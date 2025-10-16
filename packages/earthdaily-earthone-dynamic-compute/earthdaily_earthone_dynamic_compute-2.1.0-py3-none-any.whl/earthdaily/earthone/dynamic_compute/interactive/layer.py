# flake8: noqa

import contextlib
import hashlib
import json
import logging
import threading
import uuid
import warnings
from datetime import date, datetime
from importlib.metadata import version
from urllib.parse import urlencode

import earthdaily.earthone as eo
import earthdaily.earthone.dynamic_compute as dc
import geopandas as gpd
import ipyleaflet
import ipywidgets as widgets
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import requests
import traitlets
from earthdaily.earthone.core.vector.tiles import create_layer
from pandas.api.types import is_numeric_dtype

from ..datetime_utils import normalize_datetime_or_none
from ..operations import (
    API_HOST,
    UnauthorizedUserError,
    _python_major_minor_version,
    set_cache_id,
)
from .clearable import ClearableOutput
from .tile_url import validate_scales


class ScaleFloat(traitlets.CFloat):
    "Casting Float traitlet that also considers the empty string as None"

    def validate(self, obj, value):
        if value == "" and self.allow_none:
            return None
        return super(ScaleFloat, self).validate(obj, value)


class VectorTileLayer(ipyleaflet.VectorTileLayer):
    """VectorTileLayer wrapper with handling for Authentication and advanced styling.

    Attributes
    ----------
    product_id : str
        Vector product to display
    vector_tile_layer_styles : dict
        Style dictionary. For advanced styling, this will be a JS block.
        property_coloring = traitlets.Bool()
    property_coloring : bool
        If True, enable coloring by property.
    chosen_prop: str
        Property to color by, if property_coloring is True.
    """

    colors = [
        "#5781F6",
        "#EC5C56",
        "#87FA6B",
        "#ED6F2D",
        "#4C56F6",
        "#EC62F8",
        "#85FBFD",
        "#F29D39",
        "#F19FCA",
        "#429697",
        "#C49A6D",
        "#8D3915",
        "#8C43F5",
        "#000C82",
        "#D9E859",
        "#989BF8",
    ]
    idx = 0
    color = traitlets.Unicode()
    fill_color = traitlets.Unicode()
    radius = traitlets.Int()
    weight = traitlets.Float()
    fill_opacity = traitlets.Float()
    property_coloring = traitlets.Bool()
    chosen_prop = traitlets.Unicode()
    colorbar = traitlets.Unicode()
    color_min = traitlets.Float()
    color_max = traitlets.Float()
    prop_description = traitlets.Unicode()

    fetch_options = traitlets.Dict({"credentials": "include"}).tag(sync=True, o=True)

    def __init__(self, product_id, **kwargs):

        # Get the layer URL from Platform
        product_name = eo.vector.Table.get(product_id).name
        lyr = create_layer(product_id, product_name)
        super().__init__(name=product_name, url=lyr.url, **kwargs)

        self.product_id = product_id
        style_dict = {}

        # Set some style defaults
        if "vector_tile_layer_styles" in kwargs:
            style_dict = list(kwargs["vector_tile_layer_styles"].values())[0]
        elif "saved_styles" in kwargs:
            style_dict = kwargs["saved_styles"]
        self.color = (
            VectorTileLayer.colors[VectorTileLayer.idx % len(VectorTileLayer.colors)]
            if "color" not in style_dict
            else style_dict["color"]
        )
        self.fill_color = (
            self.color if "fill_color" not in style_dict else style_dict["fill_color"]
        )
        self.opacity = 1 if "opacity" not in style_dict else style_dict["opacity"]
        self.weight = 1.9 if "weight" not in style_dict else style_dict["weight"]
        self.fill_opacity = (
            0.1 if "fill_opacity" not in style_dict else style_dict["fill_opacity"]
        )
        self.radius = 3 if "radius" not in style_dict else style_dict["radius"]

        VectorTileLayer.idx += 1

        self.observe(
            self.reset_style,
            names=[
                "color",
                "fill_color",
                "opacity",
                "weight",
                "fill_opacity",
                "radius",
            ],
        )

        # Property coloring
        self.df = gpd.GeoDataFrame()
        self.property_coloring = (
            False
            if "property_coloring" not in style_dict
            else style_dict["property_coloring"]
        )
        self.properties = [
            col
            for col in eo.vector.Table.get(self.product_id).columns
            if col not in ["geometry", "uuid"]
        ]
        self.chosen_prop = (
            "" if "chosen_prop" not in style_dict else style_dict["chosen_prop"]
        )
        self.colorbar = (
            "jet" if "colorbar" not in style_dict else style_dict["colorbar"]
        )
        self.color_min = 0 if "color_min" not in style_dict else style_dict["color_min"]
        self.color_max = 0 if "color_max" not in style_dict else style_dict["color_max"]
        self.categories = (
            {} if "categories" not in style_dict else style_dict["categories"]
        )
        self.prop_description = (
            ""
            if "prop_description" not in style_dict
            else style_dict["prop_description"]
        )
        self.observe(
            self._color_by_property,
            [
                "property_coloring",
                "chosen_prop",
                "colorbar",
                "color_min",
                "color_max",
            ],
        )

        self.reset_style(None)

    def reset_style(self, change):
        # Create the styles as a dictionary for simple coloring
        if self.property_coloring:
            self._color_by_property(change)
        else:
            self._update_style_simple(change)

    def _update_style_simple(self, change):
        # Create the styles as a dictionary for simple coloring
        prime_dict = {
            "fill": "true",
            "fillColor": f"{self.fill_color}",
            "color": f"{self.color}",
            "opacity": self.opacity,
            "fillOpacity": self.fill_opacity,
            "weight": self.weight,
            "radius": self.radius,
        }
        if self.product_id.split(":")[0] == "earthdaily":
            dl_name = ":".join(["descarteslabs"] + self.product_id.split(":")[1:])
            self.vector_tile_layer_styles = {
                self.product_id: prime_dict,
                dl_name: prime_dict,
            }
        else:
            self.vector_tile_layer_styles = {self.product_id: prime_dict}

    def _color_by_property(self, change):
        if not self.property_coloring:
            self.categories = {}
            self.chosen_prop = ""
            self.color_min, self.color_max = 0, 0
            self._update_style_simple(change)
            return
        if self.df.empty:
            # Create a dataframe (if we haven't already) and convert the types as best as we can
            # (so we don't have numerical data coming in as strings mainly)
            self.df = eo.vecTable.get(
                self.product_id, aoi=dc.map.geocontext()
            ).collect()
            self.df = self.df.convert_dtypes()
            for col in self.df.columns:
                if gpd.pd.api.types.is_datetime64_any_dtype(self.df[col]):
                    self.df[col] = self.df[col].astype(str)
        if not self.chosen_prop:
            # Don't try to do anything if a property hasn't been set yet
            return
        # Create the JS string for styles
        if is_numeric_dtype(self.df[self.chosen_prop]):
            cmap = mpl.colormaps[self.colorbar]
            thresholds = np.linspace(self.color_min, self.color_max, 100)
            colors = [
                mpl.colors.to_hex(
                    cmap((v - self.color_min) / (self.color_max - self.color_min))
                )
                for v in thresholds
            ]
            js_color_stops = ",\n        ".join(
                f"{{ threshold: {v:.6f}, color: '{c}' }}"
                for v, c in zip(thresholds, colors)
            )
            if self.product_id.split(":")[0] == "earthdaily":
                dl_name = ":".join(["descarteslabs"] + self.product_id.split(":")[1:])
                jstyle = f"""{{
                    "{self.product_id}": function(properties, zoom) {{
                    var value = properties.{self.chosen_prop};
                    var color = '#999';

                    var colorStops = [
                        {js_color_stops}
                    ];

                    for (var i = 0; i < colorStops.length - 1; i++) {{
                        if (value >= colorStops[i].threshold && value < colorStops[i + 1].threshold) {{
                            color = colorStops[i].color;
                            break;
                        }}
                    }}
                    if (value < colorStops[0].threshold) {{
                        color = colorStops[0].color;
                    }}
                    if (value >= colorStops[colorStops.length - 1].threshold) {{
                        color = colorStops[colorStops.length - 1].color;
                    }}

                    return {{ color: color,
                            fill: true,
                            fillColor: color,
                            opacity: {self.opacity},
                            fillOpacity: {self.fill_opacity},
                            weight: {self.weight},
                            radius: {self.radius} }};
                    }},
                    "{dl_name}": function(properties, zoom) {{
                    var value = properties.{self.chosen_prop};
                    var color = '#999';

                    var colorStops = [
                        {js_color_stops}
                    ];

                    for (var i = 0; i < colorStops.length - 1; i++) {{
                        if (value >= colorStops[i].threshold && value < colorStops[i + 1].threshold) {{
                            color = colorStops[i].color;
                            break;
                        }}
                    }}
                    if (value < colorStops[0].threshold) {{
                        color = colorStops[0].color;
                    }}
                    if (value >= colorStops[colorStops.length - 1].threshold) {{
                        color = colorStops[colorStops.length - 1].color;
                    }}
                    return {{ color: color,
                            fill: true,
                            fillColor: color,
                            opacity: {self.opacity},
                            fillOpacity: {self.fill_opacity},
                            weight: {self.weight},
                            radius: {self.radius} }};
                }} }}"""
            else:
                jstyle = f"""{{"{self.product_id}": function(properties, zoom) {{
                    var value = properties.{self.chosen_prop};
                    var color = '#999';

                    var colorStops = [
                        {js_color_stops}
                    ];

                    for (var i = 0; i < colorStops.length - 1; i++) {{
                        if (value >= colorStops[i].threshold && value < colorStops[i + 1].threshold) {{
                            color = colorStops[i].color;
                            break;
                        }}
                    }}
                    if (value < colorStops[0].threshold) {{
                        color = colorStops[0].color;
                    }}
                    if (value >= colorStops[colorStops.length - 1].threshold) {{
                        color = colorStops[colorStops.length - 1].color;
                    }}

                    return {{ color: color,
                            fill: true,
                            fillColor: color,
                            opacity: {self.opacity},
                            fillOpacity: {self.fill_opacity},
                            weight: {self.weight},
                            radius: {self.radius} }};
                    }} }}"""
        else:
            self.color_min, self.color_max = 0, 0
            num_cats = len(self.df[self.chosen_prop].unique())
            self.prop_description = f"String/Category data. {num_cats} unique values."
            if change and change["name"] == "chosen_prop":
                self._set_categories()
            js_color_stops = ",\n        ".join(
                f"{{ cat: '{v}', color: '{c}' }}" for v, c in self.categories.items()
            )
            if self.product_id.split(":")[0] == "earthdaily":
                dl_name = ":".join(["descarteslabs"] + self.product_id.split(":")[1:])
                jstyle = f"""{{
                    "{self.product_id}": function(properties, zoom) {{
                    var value = properties.{self.chosen_prop};
                    var color = '#999';

                    var colorStops = [
                        {js_color_stops}
                    ];

                    for (var i = 0; i < colorStops.length - 1; i++) {{
                        if (value === colorStops[i].cat) {{
                            color = colorStops[i].color;
                            break;
                        }}
                    }}

                    return {{ color: color,
                            fill: true,
                            fillColor: color,
                            opacity: {self.opacity},
                            fillOpacity: {self.fill_opacity},
                            weight: {self.weight},
                            radius: {self.radius} }};
                    }},
                    "{dl_name}": function(properties, zoom) {{
                    var value = properties.{self.chosen_prop};
                    var color = '#999';

                    var colorStops = [
                        {js_color_stops}
                    ];

                    for (var i = 0; i < colorStops.length - 1; i++) {{
                        if (value === colorStops[i].cat) {{
                            color = colorStops[i].color;
                            break;
                        }}
                    }}

                    return {{ color: color,
                            fill: true,
                            fillColor: color,
                            opacity: {self.opacity},
                            fillOpacity: {self.fill_opacity},
                            weight: {self.weight},
                            radius: {self.radius} }};
                }} }}"""
            else:
                jstyle = f"""{{"{self.product_id}": function(properties, zoom) {{
                    var value = properties.{self.chosen_prop};
                    var color = '#999';

                    var colorStops = [{js_color_stops}];

                    for (var i = 0; i < colorStops.length - 1; i++) {{
                        if (value == colorStops[i].cat) {{
                            color = colorStops[i].color;
                            break;
                        }}
                    }}

                    return {{ color: color,
                            fill: true,
                            fillColor: color,
                            opacity: {self.opacity},
                            fillOpacity: {self.fill_opacity},
                            weight: {self.weight},
                            radius: {self.radius} }};
                    }} }}"""
        self.vector_tile_layer_styles = jstyle

    def _set_categories(self):
        """Populate the dialog for categorical data"""
        self.categories = {}
        colors = self.colors
        for i, cat in enumerate(self.df[self.chosen_prop].dropna().unique()):
            color = colors[i % len(colors)]
            self.categories[cat] = color

    def set_category_color(self, cat, color):
        self.categories[cat] = color
        self.reset_style(None)


class DynamicComputeLayer(ipyleaflet.TileLayer):
    """
    Subclass of ``ipyleaflet.TileLayer`` for displaying a dynamic compute
    `Mosaic`

    Attributes
    ----------
    imagery: ~.Mosaic or ~.ImageStack
        Read-only: the `~.Mosaic` or `~.ImageStack` to use.
        Change it with `set_imagery`.
    value: ~.Mosaic or ~.ImageStack
        Read-only: a parametrized version of `imagery`, with all the values of `parameters`
        embedded in it.
    image_value: ~.Mosaic
        Read-only: a parametrized version of `imagery` as a `~.Mosaic`,
        with any `reduction` applied and all the values of `parameters` embedded in it
    parameters: dict
        Parameters to use while computing; modify attributes under ``.parameters``
        (like ``layer.update_parameters(foo = "bar")``) to cause the layer to recompute
        and update under those new parameters. This trait is read-only in that you
        can't do ``layer.parameters = a_new_parameter_set``, but you can change the attributes
        *within* ``layer.parameters``.
    clear_on_update: bool, default True
        Whether to clear all tiles from the map as soon as the layer changes, or leave out-of-date
        tiles visible until new ones have loaded. True (default) makes it easier to tell whether
        the layer is done loading and up-to-date or not. False prevents fast-loading layers from
        appearing to "flicker" as you interact with them.
    session_id: str
        Read-only: Unique ID that logs will be stored under, generated automatically.
    checkerboard: bool, default True
        Whether to display a checkerboarded background for missing or masked data.
    classes: list, default None
        Whether or not there are classes in the layer, indicating it is classified
    colormap: str, optional, default None
        Name of the colormap to use.
        If set, `imagery` must have 1 band.
    alpha: ~.Mosaic, optional, default to None
        The optional Mosaic to use to control transparency, e.g.
        an actual alpha channel that will be applied to tiles. It is up to
        the user to create a reasonable alpha channel, we do no checks about the values
    reduction: {"min", "max", "mean", "median", "mosaic", "sum", "std", "count"}
        If displaying a `~.Mosaic`, this method is used to reduce it
        into an `~.ImageStack`. Reduction is performed before applying a colormap or scaling.
    r_min: float, optional, default None
        Min value for scaling the red band. Along with r_max,
        controls scaling when a colormap is enabled.
    r_max: float, optional, default None
        Max value for scaling the red band. Along with r_min, controls scaling
        when a colormap is enabled.
    g_min: float, optional, default None
        Min value for scaling the green band.
    g_max: float, optional, default None
        Max value for scaling the green band.
    b_min: float, optional, default None
        Min value for scaling the blue band.
    b_max: float, optional, default None
        Max value for scaling the blue band.
    log_output: ipywidgets.Output, optional, default None
        If set, write unique log records from tiles computation to this output area
        from a background thread. Setting to None stops the listener thread.
    log_level: int, default logging.DEBUG
        Only listen for log records at or above this log level during tile computation.
        See https://docs.python.org/3/library/logging.html#logging-levels for valid
        log levels.

    Example
    -------
    >>> import earthdaily.earthone.dynamic_compute as dc
    >>> m = dc.map # doctest: +SKIP
    >>> m
    >>> # ^ display interactive map
    >>> opt_rgb = dc.Mosaic.from_product_bands("hi_res_optical:v2", # doctest: +SKIP
                                                "blue", # doctest: +SKIP
                                                start_datetime="20210101", # doctest: +SKIP
                                                end_datetime="2022101",)/ 256 # doctest: +SKIP
    >>> sigma0_vv = dc.ImageStack.from_product_bands("sentinel-1:sar:sigma0v:v1", # doctest: +SKIP
                                                    "vv", # doctest: +SKIP
                                                    "20230101", # doctest: +SKIP
                                                    "20230401") # doctest: +SKIP
    >>> water_mask = sigma0_vv.min(axis="images") > -20 # doctest: +SKIP
    >>> water = opt_rgb.mask(water_mask) # doctest: +SKIP
    >>> water_layer = water.visualize("Water", m, scales=[[0, 1]], colormap="viridis") # doctest: +SKIP
    >>> water_layer.colormap = "plasma" # doctest: +SKIP
    >>> # ^ change colormap (this will update the layer on the map)
    >>> water_layer.checkerboard = False # doctest: +SKIP
    >>> # ^ adjust parameters (this also updates the layer)
    >>> water_layer.set_scales((0.01, 0.3)) # doctest: +SKIP
    >>> # ^ adjust scaling (this also updates the layer)
    """

    attribution = traitlets.Unicode("EarthDaily Analytics").tag(sync=True, o=True)
    min_zoom = traitlets.Int(5).tag(sync=True, o=True)
    url = traitlets.Unicode(read_only=True).tag(sync=True)
    layer_id = traitlets.Unicode(read_only=True).tag(sync=True)
    clear_on_update = traitlets.Bool(default_value=True)

    imagery = traitlets.Instance(dict, read_only=True)

    value = traitlets.Instance(dict, read_only=True)

    image_value = traitlets.Instance(dict, read_only=True, allow_none=True)

    parameters = traitlets.Instance(dict, allow_none=True)

    session_id = traitlets.Unicode(read_only=True)
    log_level = traitlets.Int(logging.DEBUG)

    checkerboard = traitlets.Bool(True, allow_none=True)
    classes = traitlets.Instance(list, allow_none=True)
    val_range = traitlets.Bool(False, allow_none=True)
    reduction = traitlets.Unicode("mosaic")
    colormap = traitlets.Unicode(None, allow_none=True)
    alpha = traitlets.Instance(dict, allow_none=True)

    r_min = ScaleFloat(None, allow_none=True)
    r_max = ScaleFloat(None, allow_none=True)
    g_min = ScaleFloat(None, allow_none=True)
    g_max = ScaleFloat(None, allow_none=True)
    b_min = ScaleFloat(None, allow_none=True)
    b_max = ScaleFloat(None, allow_none=True)

    log_output = traitlets.Instance(widgets.Output, allow_none=True)
    autoscale_progress = traitlets.Instance(ClearableOutput)

    def __init__(
        self,
        imagery,
        scales=None,
        colormap=None,
        checkerboard=None,
        reduction=None,
        classes=None,
        val_range=None,
        alpha=None,
        log_level=logging.DEBUG,
        parameter_overrides=None,
        **kwargs,
    ):

        if classes and scales:
            warnings.warn("Classes are provided, scales will be ignored")

        if classes and len(imagery.bands.split(" ")) > 1:
            warnings.warn(
                "Classes can only be used with single-band images, classes will be ignored"
            )

        if val_range and not classes:
            warnings.warn(
                "val_range is set to True but classes are not provided; val_range will be ignored"
            )

        if alpha is not None:
            assert isinstance(alpha, dc.mosaic.Mosaic), "Alpha must be a Mosaic layer"

        if parameter_overrides is None:
            parameter_overrides = {}

        self._url_updates_blocked = False
        super().__init__(**kwargs)

        with self.hold_url_updates():
            self.parameters = parameter_overrides
            self.set_scales(scales, new_colormap=colormap)
            if reduction is not None:
                self.reduction = reduction
            self.checkerboard = checkerboard
            self.classes = classes
            self._set_class_colors()
            self.alpha = alpha
            self.log_level = log_level
            self.set_imagery(imagery, **parameter_overrides)

            self.set_trait("session_id", uuid.uuid4().hex)
            self.set_trait(
                "autoscale_progress",
                ClearableOutput(
                    widgets.Output(),
                    layout=widgets.Layout(max_height="10rem", flex="1 0 auto"),
                ),
            )

        self._log_listener = None
        self._known_logs = set()
        self._known_logs_lock = threading.Lock()

    def set_imagery(self, imagery: dict, **parameter_overrides):
        """
        Set a new `Mosaic` object for this layer to use.
        You can set/override the values of any parameters the imagery depends on
        by passing them as kwargs.

        Parameters
        ----------
        **parameter_overrides: JSON-serializable value, Proxytype, or ipywidgets.Widget
            Parameter names to values. Values can be Python types,
            `Proxytype` instances, or ``ipywidgets.Widget`` instances.
            Names must correspond to parameters that ``imagery`` depends on.

        """

        # Combine the parameter dependencies from `imagery` with any overrides
        # and raise an error for any missing or unexpected parameter overrides.
        # We don't do any typechecking of parameter values here; that'll be dealt with
        # later (within `ParameterSet` when trying to actually assign the trait values).
        merged_params = {}
        for name, value in self.parameters.items():
            try:
                merged_params[name] = parameter_overrides.pop(name)
                # TODO when you override the value of a widget-based parameter, you'd like to keep
                # the same type of widget (but a new instance in case it's linked to other stuff)
            except KeyError:
                raise ValueError(
                    f"Missing required parameter {name!r} for layer {self.name!r}"
                ) from None
        if parameter_overrides:
            raise ValueError(
                f"Unexpected parameters {tuple(parameter_overrides)}. This layer only "
                f"accepts the parameters {tuple(p for p in self.parameters)}."
            )

        with self.hold_url_updates():
            if not self.trait_has_value("imagery") or imagery is not self.imagery:
                self.set_trait("imagery", imagery)

            self.parameters.update(**merged_params)

    def update_parameters(self, **kwargs):
        self.set_imagery(self.imagery, **kwargs)

    def trait_has_value(self, name):
        # Backport for traitlets < 5.0, to maintain py3.6 support.
        # Remove after support for py3.6 is dropped.
        # Copied from
        # https://github.com/ipython/traitlets/blob/2bb2597224ca5ae485761781b11c06141770f110/traitlets/traitlets.py#L1496-L1516

        return name in self._trait_values

    def make_url(self):
        """
        Generate the URL for this layer.

        This is called automatically as the attributes (`imagery`, `colormap`, scales, etc.) are changed.

        Example
        -------
        >>> import earthdaily.earthone.dynamic_compute as dc
        >>> img = dc.Mosaic.from_product_bands(
                "usda:naip:v1",
                "red green blue",
                start_datetime="20210101",
                end_datetime="20220101",
            )
        >>> layer = img.visualize("sample", m) # doctest: +SKIP
        >>> layer.make_url() # doctest: +SKIP
        'https://"https://dynamic-compute.appsci-production.earthone.earthdaily.com/layers/9ec70d0e99db7f50c856c774809ae454ffd8475816e05c5c/tile/{z}/{x}/{y}?scales=%5B%5B0.0%2C+1.0%5D%5D&colormap=viridis&checkerboard=False'
        """
        if not self.visible:
            # workaround for the fact that Leaflet still loads tiles from inactive layers,
            # which is expensive computation users don't want
            return ""

        if self.colormap is not None:
            scales = [[self.r_min, self.r_max]]
        else:
            scales = [
                [self.r_min, self.r_max],
                [self.g_min, self.g_max],
                [self.b_min, self.b_max],
            ]

        scales = [scale for scale in scales if scale != [None, None]]

        parameters = self.parameters
        for key, value in self.parameters.items():
            if type(value) in [datetime, date]:
                parameters[key] = normalize_datetime_or_none(value)

        # assume a None parameter value means the value is missing
        # and we can't render the layer.
        # primarily for the `LayerPicker` widget, which can have no layer selected.
        if any(v is None for v in parameters.values()):
            return ""

        # Make the layer cacheable
        set_cache_id(self.imagery)

        # Create a layer from the graft
        response = requests.post(
            f"{API_HOST}/layers/",
            headers={"Authorization": eo.auth.Auth.get_default_auth().token},
            json={
                "graft": self.imagery,
                "python_version": _python_major_minor_version,
                "dynamic_compute_version": version(
                    "earthdaily-earthone-dynamic-compute"
                ),
            },
        )
        try:
            response.raise_for_status()
        except Exception as e:
            if e.response.status_code == 403:
                raise UnauthorizedUserError(
                    "User does not have access to dynamic-compute. "
                    "If you believe this to be an error, contact support@earthdaily.com"
                )
            else:
                raise e

        if self.alpha:
            # Create an alpha layer from the graft
            alpha_response = requests.post(
                f"{API_HOST}/layers/",
                headers={"Authorization": eo.auth.Auth.get_default_auth().token},
                json={
                    "graft": self.alpha,
                    "python_version": _python_major_minor_version,
                    "dynamic_compute_version": version(
                        "earthdaily-earthone-dynamic-compute"
                    ),
                },
            )
            alpha = json.loads(alpha_response.content.decode("utf-8"))["layer_id"]

        layer_id = json.loads(response.content.decode("utf-8"))["layer_id"]
        self.set_trait("layer_id", layer_id)
        # URL encode query parameters
        params = {}
        params["python_version"] = _python_major_minor_version
        if scales is not None:
            params["scales"] = json.dumps(scales)
        if self.colormap is not None:
            params["colormap"] = self.colormap
        if self.checkerboard is not None:
            params["checkerboard"] = self.checkerboard
        if self.classes is not None:
            self._set_class_colors()
            params["classes"] = json.dumps(self.classes)
        if self.val_range is not None:
            params["val_range"] = json.dumps(self.val_range)
        if self.alpha is not None:
            params["alpha"] = alpha
        if parameters is not None:
            params["parameters"] = json.dumps(parameters)
            param_id = hashlib.sha256(
                bytes(json.dumps(parameters), "utf-8")
            ).hexdigest()
            params["param_id"] = param_id
        # if vector_tile_layer_styles is None:
        #     vector_tile_layer_styles = {}
        query_params = urlencode(params)

        # Construct a URL to request tiles with
        url = f"{API_HOST}/layers/{layer_id}/tile/{{z}}/{{x}}/{{y}}?{query_params}"
        return url

    def _set_class_colors(self):
        """Set the class dictionary properly"""
        if self.classes is None:
            # Nothing to do if classes don't exist
            return
        if self.colormap:
            # If a colormap is defined, use it to define colors. This will override user defined colors.
            cmap = plt.get_cmap(self.colormap, len(self.classes) + 1)
        elif "color" not in self.classes[0].keys():
            # Colormap is not defined, but colors are not either
            cmap = plt.get_cmap("viridis", len(self.classes) + 1)
        else:
            # User provided colors with no map, use them.
            return
        for i, cls_ in enumerate(self.classes):
            cls_["color"] = mpl.colors.rgb2hex(cmap(i))

    @contextlib.contextmanager
    def hold_url_updates(self):
        """
        Context manager to prevent the layer URL from being updated multiple times.

        When leaving the context manager, the URL is always updated exactly once.

        Also applies ``hold_trait_notifications``.

        Example
        -------
        >>> import earthdaily.earthone.dynamic_compute as dc
        >>> naip = dc.Mosaic.from_product_bands("usda:naip:rgbn:v1", "nir") # doctest: +SKIP
        >>> naip_layer = naip.visualize("NAIP", m, colormap="viridis") # doctest: +SKIP
        >>> with naip_layer.hold_url_updates(): # doctest: +SKIP
                naip_layer.set_scales([[0.2, 1]]) # doctest: +SKIP
                naip_layer.colormap="plasma" # doctest: +SKIP
                naip_layer.set_scales([[0.2, 0.7176]]) # doctest: +SKIP
        >>> # ^ the layer will now update only once, instead of 3 times.
        """
        if self._url_updates_blocked:
            yield
        else:
            try:
                self._url_updates_blocked = True
                with self.hold_trait_notifications():
                    yield
            finally:
                self._url_updates_blocked = False
            self._update_url({})

    @traitlets.observe("xyz_obj", "parameters", type=traitlets.All)
    def _update_value(self, change):
        self.set_trait("value", self.imagery)

    @traitlets.observe("value", "reduction")
    def _update_image_value(self, change):
        value = self.value

        self.set_trait("image_value", value)

    @traitlets.observe(
        "visible",
        "checkerboard",
        "colormap",
        "reduction",
        "r_min",
        "r_max",
        "g_min",
        "g_max",
        "b_min",
        "b_max",
        "session_id",
        "parameters",
        "classes",
        "alpha",
    )
    def _update_url(self, change):
        if self._url_updates_blocked:
            return
        try:
            self.set_trait("url", self.make_url())

        except ValueError as e:
            if "Invalid scales passed" not in str(e):
                raise e
        self.clear_logs()
        if self.clear_on_update:
            self.redraw()

    @traitlets.observe("parameters", type="delete")
    # traitlets is dumb and decorator stacking doesn't work so we have to repeat this
    def _update_url_on_param_delete(self, change):
        if self._url_updates_blocked:
            return
        try:
            self.set_trait("url", self.make_url())
        except ValueError as e:
            if "Invalid scales passed" not in str(e):
                raise e
        self.clear_logs()
        if self.clear_on_update:
            self.redraw()

    def _log(self, message: str, level: int = 2):
        "Log a message to the error output (if there is one), without duplicates"
        if self.log_output is None:
            return

        with self._known_logs_lock:
            if message in self._known_logs:
                return
            else:
                self._known_logs.add(message)

        log_level = "WARNING"
        msg = "{}: {} - {}\n".format(self.name, log_level, message)
        self.log_output.append_stdout(msg)

    def _stop_logger(self):
        if self._log_listener is not None:
            self._log_listener.stop(timeout=1)
            self._log_listener = None

    @traitlets.observe("log_output")
    def _toggle_log_listener_if_output(self, change):
        if change["new"] is None:
            self._stop_logger()

    def __del__(self):
        self._stop_logger()
        self.clear_logs()
        super(DynamicComputeLayer, self).__del__()

    def forget_logs(self):
        """
        Clear the set of known log records, so they are re-displayed if they occur again

        """
        with self._known_logs_lock:
            self._known_logs.clear()

    def clear_logs(self):
        """
        Clear any logs currently displayed for this layer
        """
        if self.log_output is None:
            return

        self.forget_logs()
        new_logs = []
        for error in self.log_output.outputs:
            if not error["text"].startswith(self.name + ": "):
                new_logs.append(error)
        self.log_output.outputs = tuple(new_logs)

    def set_scales(self, scales, new_colormap=False, new_classes=False):
        """
        Update the scales for this layer by giving a list of scales

        Parameters
        ----------
        scales: list of lists, default None
            The scaling to apply to each band in the `Mosaic` or `ImageStack`.
            If displaying an `ImageStack`, it is reduced into a `Mosaic`
            before applying scaling.

            If `Mosaic` or `ImageStack` contains 3 bands,
            ``scales`` must be a list like ``[(0, 1), (0, 1), (-1, 1)]``.

            If `Mosaic` or `ImageStack` contains 1 band, ``scales`` must be a list like ``[(0, 1)]``,
            or just ``(0, 1)`` for convenience

            If None, each 256x256 tile will be scaled independently
            based on the min and max values of its data.
        new_colormap: str, None, or False, optional, default False
            A new colormap to set at the same time, or False to use the current colormap.
        new_classes: list of dicts, or False, or None, default False
            New classes to use for the layer. If False, current classes will be used if available

        Example
        -------
        >>> import earthdaily.earthone.dynamic_compute as dc
        >>> dc.map # doctest: +SKIP
        >>> naip = dc.Mosaic.from_product_bands("usda:naip:rgbn:v1", "nir") # doctest: +SKIP
        >>> naip_layer = naip.visualize("NAIP", m, colormap="viridis") # doctest: +SKIP
        >>> naip_layer.set_scales((0.08, 0.3), new_colormap="plasma") # doctest: +SKIP
        >>> # ^ optionally set new colormap
        """
        colormap = self.colormap if new_colormap is False else new_colormap
        classes = self.classes if new_classes is False else new_classes

        if scales is not None:
            scales = validate_scales(scales)

            if len(scales) == 1 and colormap is None and classes is None:
                msg = "When displaying a 1-band image, either classes or a colormap must be defined."
                raise ValueError(msg)
            elif len(scales) == 3 and colormap is not None and classes is None:
                msg = "Colormaps can only be used with 3-band images if classes are also defined."
                raise ValueError(msg)

            with self.hold_url_updates():
                if colormap is None and classes is None:
                    self.r_min = scales[0][0]
                    self.r_max = scales[0][1]
                    self.g_min = scales[1][0]
                    self.g_max = scales[1][1]
                    self.b_min = scales[2][0]
                    self.b_max = scales[2][1]
                else:
                    self.r_min = scales[0][0]
                    self.r_max = scales[0][1]
                if new_colormap is not False:
                    self.colormap = new_colormap
                if new_classes is not False:
                    self.classes = new_classes
        else:
            # scales is None
            with self.hold_url_updates():
                if colormap is None and classes is None:
                    self.r_min = None
                    self.r_max = None
                    self.g_min = None
                    self.g_max = None
                    self.b_min = None
                    self.b_max = None
                else:
                    self.r_min = None
                    self.r_max = None
                if new_colormap is not False:
                    self.colormap = new_colormap
                if new_classes is not False:
                    self.classes = new_classes

    def get_scales(self):
        """
        Get scales for a layer.

        Returns
        -------
        scales: List[List[int]] or None
            A list containing a list of scales for each band in the layer or None if the layer has no scales set.


        Example
        -------
        >>> import earthdaily.earthone.dynamic_compute as dc
        >>> dc.map # doctest: +SKIP
        >>> naip = dc.Mosaic.from_product_bands("usda:naip:rgbn:v1", "nir") # doctest: +SKIP
        >>> naip_layer = naip.visualize("NAIP", m, colormap="viridis") # doctest: +SKIP
        >>> naip_layer.set_scales((0.08, 0.3), new_colormap="plasma") # doctest: +SKIP
        >>> layer.get_scales() # doctest: +SKIP
        [[0.08, 0.3]]
        """
        if self.r_min is None:
            return None
        if self.colormap:
            return [[self.r_min, self.r_max]]
        else:
            return [
                [self.r_min, self.r_max],
                [self.g_min, self.g_max],
                [self.b_min, self.b_max],
            ]

    def _ipython_display_(self):
        param_set = self.parameters
        if param_set:
            widget = param_set.widget
            if widget and len(widget.children) > 0:
                widget._ipython_display_()


class VectorRasterLayer(DynamicComputeLayer):
    """
    Subclass of ``DynamicComputeLayer`` for displaying a dynamic compute
    `Mosaic` that is derived from a vector product.
    """

    def __init__(
        self,
        imagery,
        scales=None,
        colormap=None,
        checkerboard=None,
        log_level=logging.DEBUG,
        **kwargs,
    ):
        self._url_updates_blocked = False
        super(DynamicComputeLayer, self).__init__(**kwargs)
        with self.hold_url_updates():
            self.set_scales(scales, new_colormap=colormap)
            self.checkerboard = checkerboard
            self.log_level = log_level
            self.parameters = {}
            self.set_imagery(imagery, **self.parameters)
            self.set_trait("session_id", uuid.uuid4().hex)
            self.set_trait(
                "autoscale_progress",
                ClearableOutput(
                    widgets.Output(),
                    layout=widgets.Layout(max_height="10rem", flex="1 0 auto"),
                ),
            )

        self._log_listener = None
        self._known_logs = set()
        self._known_logs_lock = threading.Lock()

    def make_url(self):
        """
        Generate the URL for this layer.

        This is called automatically as the attributes (`imagery`, `colormap`, scales, etc.) are changed.

        Example
        -------
        >>> import earthdaily.earthone.dynamic_compute as dc
        >>> img = dc.Mosaic.from_product_bands(
                "usda:naip:v1",
                "red green blue",
                start_datetime="20210101",
                end_datetime="20220101",
            )
        >>> layer = img.visualize("sample", m) # doctest: +SKIP
        >>> layer.make_url() # doctest: +SKIP
        'https://"https://dynamic-compute.appsci-production.earthone.earthdaily.com/layers/9ec70d0e99db7f50c856c774809ae454ffd8475816e05c5c/tile/{z}/{x}/{y}?scales=%5B%5B0.0%2C+1.0%5D%5D&colormap=viridis&checkerboard=False'
        """
        if not self.visible:
            # workaround for the fact that Leaflet still loads tiles from inactive layers,
            # which is expensive computation users don't want
            return ""

        if self.colormap is not None:
            scales = [[self.r_min, self.r_max]]
        else:
            scales = [
                [self.r_min, self.r_max],
                [self.g_min, self.g_max],
                [self.b_min, self.b_max],
            ]

        scales = [scale for scale in scales if scale != [None, None]]

        # Make the layer cacheable
        set_cache_id(self.imagery)

        # Create a layer from the graft
        response = requests.post(
            f"{API_HOST}/layers/",
            headers={"Authorization": eo.auth.Auth.get_default_auth().token},
            json={
                "graft": self.imagery,
                "python_version": _python_major_minor_version,
                "dynamic_compute_version": version(
                    "earthdaily-earthone-dynamic-compute"
                ),
            },
        )
        try:
            response.raise_for_status()
        except Exception as e:
            if e.response.status_code == 403:
                raise UnauthorizedUserError(
                    "User does not have access to dynamic-compute. "
                    "If you believe this to be an error, contact support@earthdaily.com"
                )
            else:
                raise e

        layer_id = json.loads(response.content.decode("utf-8"))["layer_id"]
        self.set_trait("layer_id", layer_id)
        # URL encode query parameters
        params = {}
        params["python_version"] = _python_major_minor_version
        if scales is not None:
            params["scales"] = json.dumps(scales)
        if self.colormap is not None:
            params["colormap"] = self.colormap
        if self.checkerboard is not None:
            params["checkerboard"] = self.checkerboard

        query_params = urlencode(params)

        # Construct a URL to request tiles with
        url = f"{API_HOST}/layers/{self.layer_id}/rasterize/{{z}}/{{x}}/{{y}}?{query_params}"
        return url
