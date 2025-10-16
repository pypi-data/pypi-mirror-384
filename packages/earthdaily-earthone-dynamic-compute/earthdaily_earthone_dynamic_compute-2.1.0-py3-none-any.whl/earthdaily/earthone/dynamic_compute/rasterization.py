# noqa

from __future__ import annotations

import dataclasses
import logging
from copy import deepcopy
from typing import Dict, List, Optional, Union

import ipyleaflet

from .compute_map import ComputeMap
from .eo_utils import verify_vector_product
from .interactive.tile_url import validate_scales
from .operations import (
    create_rasterization,
    format_bands,
    op_args,
    reset_graft,
    set_cache_id,
)
from .serialization import BaseSerializationModel

# The ground sample distance at the highest resolution.
MIN_GSD = 0.5971642732620239


@dataclasses.dataclass
class RasterizationSerializationModel(BaseSerializationModel):
    """State representation of a Rasterization instance"""

    graft: Dict
    product_id: str
    columns: Union[str, List[str]]

    @classmethod
    def from_json(cls, data: str) -> RasterizationSerializationModel:
        base_obj = super().from_json(data)
        base_obj.graft = reset_graft(base_obj.graft)
        return base_obj


RAST_METHODS = ["IDW", "fishnet"]


class Rasterization(
    ComputeMap,  # Base class
):
    """
    Class wrapper around rasterization operations
    """

    _RETURN_PRECEDENCE = 1

    def __init__(
        self,
        graft: Dict,
        columns: Optional[Union[str, List[str]]] = None,
        product_id: Optional[str] = None,
    ):
        """
        Initialize a new instance of Rasterization. Users should rely on
        from_product_columns

        Parameters
        ----------
        graft: Dict
            Graft, which when evaluated will generate a bands x rows x cols array
        columns: Union[str, List[str]]
            Columns either as space separated names in a single string or a list
            of column names
        product_id: str
            Product id
        """

        set_cache_id(graft)
        super().__init__(graft)
        self.columns = columns
        self.product_id = product_id

    def tile_layer(
        self,
        name=None,
        scales=None,
        colormap=None,
        checkerboard=True,
        log_level=logging.DEBUG,
    ):
        """
        A `.VectorRasterLayer` for this `Rasterization`.

        Generally, use `Rasterization.visualize` for displaying on map.
        Only use this method if you're managing your own ipyleaflet Map instances,
        and creating more custom visualizations.

        An empty `Rasterization` will be rendered as a checkerboard (default) or blank tile.

        Parameters
        ----------
        name: str
            The name of the layer.
        scales: list of lists, default None
            The scaling to apply to each column in the `Rasterization`.

            If `Rasterization` contains 3 bands, ``scales`` must be a list like
            ``[(0, 1), (0, 1), (-1, 1)]``.

            If `Rasterization` contains 1 band, ``scales`` must be a list like ``[(0, 1)]``,
            or just ``(0, 1)`` for convenience

            If None, each 256x256 tile will be scaled independently
            based on the min and max values of its data.
        colormap: str, default None
            The name of the colormap to apply to the `Rasterization`. Only valid if the
             `Rasterization` has a single band.
        checkerboard: bool, default True
            Whether to display a checkerboarded background for missing or masked data.
        log_level: int, default logging.DEBUG
            Only listen for log records at or above this log level during tile
            computation. See https://docs.python.org/3/library/logging.html#logging-levels
             for valid log levels.

        Returns
        -------
        layer: `.DynamicComputeLayer`
        """
        from earthdaily.earthone.dynamic_compute.interactive.layer import (
            VectorRasterLayer,
        )

        return VectorRasterLayer(
            self,
            name=name,
            scales=scales,
            colormap=colormap,
            checkerboard=checkerboard,
            log_level=log_level,
        )

    @classmethod
    def from_product_columns(
        cls,
        product_id: str,
        columns: Union[str, List[str]],
        method: str,
        **kwargs,
    ) -> Rasterization:
        """
        Create a new Rasterization object

        Parameters
        ----------
        product_id: str
            ID of the product from which we want to access data
        columns: Union[str, List[str]]
            A space-separated list of columns within the product, or a list of strings.
        method: str
            Method to use for rasterization.

        Returns
        -------
        m: Rasterization
            New rasterization object.
        """
        if method not in RAST_METHODS:
            raise NotImplementedError(
                f"Method `{method}` not implemented for Rasterizations."
            )
        if method == "fishnet":
            assert "statistic" in kwargs, (
                "statistic is required to rasterize with fishnet method. Valid options"
                " are one of 'min', 'max', 'mean', 'count', or 'count-bdl'."
            )
        columns = format_bands(columns)

        verify_vector_product(product_id, columns)

        columns = " ".join(columns)

        graft = create_rasterization(product_id, columns, method, **kwargs)

        return cls(graft, columns, product_id)

    def pick_columns(self, columns: Union[str, List[str]]) -> Rasterization:
        """
        Create a new Rasterization object with the specified columns and
        the product-id of this Rasterization object

        Parameters
        ----------
        columns: str
            A space-separated list of columns within the product, or a list
            of columns as strings

        Returns
        -------
        r: Rasterization
            New rasterization object.
        """

        columns = format_bands(columns)

        return_key = self["returns"]
        return_value = self[return_key]

        args = op_args(return_value)

        product_id = self[args[0]]
        original_columns = format_bands(self[args[1]])
        method = self[args[2]]
        options = deepcopy(args[3])

        for key in options:
            options[key] = self[options[key]]
        options.pop("cache_id", None)

        if set(columns) > set(original_columns):
            raise Exception(
                f"selected bands {columns} are not a subset of the mosaic bands {original_columns}"
            )

        return Rasterization.from_product_columns(
            product_id, columns, method, **options
        )

    def visualize(
        self,
        name: str,
        map: ipyleaflet.leaflet.Map,
        colormap: Optional[str] = None,
        scales: Optional[List[List]] = None,
        checkerboard=True,
        **parameter_overrides,
    ) -> ipyleaflet.leaflet.TileLayer:
        """
        Visualize this Mosaic instance on a map. This call does not
        mutate `this`
        Parameters
        ----------
        name: str
            Name of this layer on the map
        map: ipyleaflet.leaflet.Map
            IPyleaflet map on which to add this mosaic as a layer
        colormap: str
            Optional colormap to use
        scales: list
            List of lists where each sub-list is a lower and upper bound. There must be
            as many sub-lists as bands in the mosaic
        classes: list, default None
            Whether or not there are classes in the layer, indicating it is classified

        Returns
        -------
        layer: lyr
            IPyleaflet tile layer on the map.
        """

        if scales is not None:
            scales = validate_scales(scales)
            if not isinstance(scales, list):
                raise Exception("Scales must be a list")
            for scale in scales:
                if len(scale) != 2:
                    raise Exception("Each entry in scales must have a min and max")

        for layer in map.layers:
            if layer.name == name:
                with layer.hold_url_updates():
                    layer.set_imagery(self, **parameter_overrides)
                    layer.set_scales(scales, new_colormap=colormap)
                    layer.checkerboard = checkerboard
                return layer
        else:
            layer = self.tile_layer(
                name=name,
                scales=scales,
                colormap=colormap,
                checkerboard=checkerboard,
                **parameter_overrides,
            )
            map.add_layer(layer)
            return layer

    def serialize(self):
        """Serializes this object into a json representation"""

        return RasterizationSerializationModel(
            graft=dict(self),
            product_id=self.product_id,
            bands=self.bands,
        ).json()

    @classmethod
    def deserialize(cls, data: str) -> Rasterization:
        """Deserializes into this object from json

        Parameters
        ----------
        data : str
            The json representation of the object state

        Returns
        -------
        Mosaic
            An instance of this object with the state stored in data
        """

        return cls(**RasterizationSerializationModel.from_json(data).dict())
