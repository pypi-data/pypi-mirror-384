#
# SPDX-FileCopyrightText: Copyright (c) 2021-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""
Scene class, utilities, and example scenes
"""

from __future__ import annotations

import os
from importlib_resources import files
from typing import List
import contextlib

import drjit as dr
import matplotlib
import matplotlib.pyplot as plt
import mitsuba as mi
import numpy as np
from scipy.constants import speed_of_light, Boltzmann

import sionna
from .constants import DEFAULT_FREQUENCY, DEFAULT_BANDWIDTH, \
                       DEFAULT_TEMPERATURE, \
                       DEFAULT_PREVIEW_BACKGROUND_COLOR
from .radio_materials import RadioMaterialBase
from .antenna_array import AntennaArray
from .camera import Camera
from .preview import Previewer
from .radio_devices import Transmitter, Receiver
from .renderer import render
from .scene_utils import edit_scene_shapes, process_xml
from .utils import radio_map_color_mapping
from . import scenes


class Scene:
    # pylint: disable=line-too-long
    r"""
    A scene contains everything that is needed for radio propagation simulation
    and rendering.

    A scene is a collection of multiple instances of
    :class:`~sionna.rt.SceneObject` which define the geometry and materials of
    the objects in the scene. It also includes transmitters
    (:class:`~sionna.rt.Transmitter`) and
    receivers (:class:`~sionna.rt.Receiver`).

    A scene is instantiated by calling :func:`~sionna.rt.load_scene()`.

    `Example scenes <https://nvlabs.github.io/sionna/rt/api/scene.html#examples>`_ can be loaded as follows:

    .. code-block:: python

        from sionna.rt import load_scene
        scene = load_scene(sionna.rt.scene.munich)
        scene.preview()

    .. figure:: ../figures/scene_preview.png
        :align: center

    :param mi_scene: A Mitsuba scene
    """

    def __init__(self, mi_scene: mi.Scene | None = None,
                 remove_duplicate_vertices: bool = False):

        # Transmitter antenna array
        self._tx_array = None
        # Receiver antenna array
        self._rx_array = None

        # Radio materials
        self._radio_materials = {}

        # Scene objects
        self._scene_objects = {}

        # Radio devices
        self._transmitters = {}
        self._receivers = {}

        # Preview widget
        self._preview_widget = None

        # Set the frequency to the default value
        self.frequency = DEFAULT_FREQUENCY

        # Set the bandwidth to the default value
        self.bandwidth = DEFAULT_BANDWIDTH

        # Set the temperature to the default value
        self.temperature = DEFAULT_TEMPERATURE

        # If no scene is loaded, then load the empty scene
        if mi_scene is None:
            self._scene = mi.load_dict({ "type": "scene" })
        else:
            assert isinstance(mi_scene, mi.Scene)
            self._scene = mi_scene
        self._scene_params = mi.traverse(self._scene)

        # Load the scene objects.
        # The radio material is a Mitsuba BSDF, and as so were already
        # instantiated when loading the Mitsuba scene.
        # Note that when the radio material is instantiated, it is added
        # to the this scene.
        self._load_scene_objects(remove_duplicate_vertices)

    @property
    def frequency(self):
        """
        :py:class:`mi.Float`: Get/set the carrier frequency [Hz]
        """
        return self._frequency

    @frequency.setter
    def frequency(self, f):
        if f <= 0.0:
            raise ValueError("Frequency must be positive")
        self._frequency = mi.Float(f)
        # Update radio materials
        for mat in self.radio_materials.values():
            mat.frequency_update()

    @property
    def wavelength(self):
        """
         :py:class:`mi.Float`:  Wavelength [m]
        """
        return speed_of_light / self.frequency

    @property
    def wavenumber(self):
        """
        :py:class:`mi.Float` : Wavenumber [rad/m]
        """
        return dr.two_pi / self.wavelength

    @property
    def temperature(self):
        """
        :py:class:`mi.Float`: Get/set the environment temperature [K].
            Used for the computation of
            :attr:`~sionna.rt.Scene.thermal_noise_power`.
        """
        return self._temperature

    @temperature.setter
    def temperature(self, v):
        if v<0:
            raise ValueError("temperature must be positive")
        self._temperature = mi.Float(v)

    @property
    def bandwidth(self):
        """
        :py:class:`mi.Float`: Get/set the transmission bandwidth [Hz].
            Used for the computation of
            :attr:`~sionna.rt.Scene.thermal_noise_power`.
        """
        return self._bandwidth

    @bandwidth.setter
    def bandwidth(self, v):
        if v<0:
            raise ValueError("bandwidth must be positive")
        self._bandwidth = mi.Float(v)

    @property
    def thermal_noise_power(self):
        """
        :py:class:`mi.Float`: Thermal noise power [W]
        """
        return self.temperature * Boltzmann * self.bandwidth

    @property
    def angular_frequency(self):
        """
        :py:class:`mi.Float`: Angular frequency [rad/s]
        """
        return dr.two_pi*self.frequency

    @property
    def tx_array(self):
        """
        :class:`~rt.AntennaArray`: Get/set the antenna array used by
            all transmitters in the scene
        """
        return self._tx_array

    @tx_array.setter
    def tx_array(self, array):
        if not isinstance(array, AntennaArray):
            raise TypeError("`array` must be an instance of ``AntennaArray``")
        self._tx_array = array

    @property
    def rx_array(self):
        """
        :class:`~rt.AntennaArray`: Get/set the antenna array used by
            all receivers in the scene
        """
        return self._rx_array

    @rx_array.setter
    def rx_array(self, array):
        if not isinstance(array, AntennaArray):
            raise TypeError("`array` must be an instance of ``AntennaArray``")
        self._rx_array = array

    @property
    def radio_materials(self):
        """
        :py:class:`dict`, { "name", :class:`~rt.RadioMaterialBase`} :
            Dictionary of radio materials
        """
        return dict(self._radio_materials)

    @property
    def objects(self):
        """
        :py:class:`dict`, { "name", :class:`~rt.SceneObject`}: Dictionary
            of scene objects
        """
        return dict(self._scene_objects)

    @property
    def transmitters(self):
        """
        :py:class:`dict`, { "name", :class:`~rt.Transmitter`}: Dictionary
            of transmitters
        """
        return dict(self._transmitters)

    @property
    def receivers(self):
        """
        :py:class:`dict`, { "name", :class:`~rt.Receiver`}: Dictionary
            of receivers
        """
        return dict(self._receivers)

    @property
    def paths_solver(self):
        """
        :class:`rt.PathSolverBase`: Get/set the path solver
        """
        return self._paths_solver

    @paths_solver.setter
    def paths_solver(self, solver):
        self._paths_solver = solver

    def get(self, name: str) -> (
        None |
        sionna.rt.RadioDevice |
        RadioMaterialBase
    ) :
        # pylint: disable=line-too-long
        r"""
        Returns a scene object, radio device, or radio material

        :param name: Name of the item to retrieve
        """
        if name in self._radio_materials:
            return self._radio_materials[name]
        if name in self._scene_objects:
            return self._scene_objects[name]
        if name in self._transmitters:
            return self._transmitters[name]
        if name in self._receivers:
            return self._receivers[name]
        return None

    def add(self,
            item: (sionna.rt.RadioDevice |
                   RadioMaterialBase)
    ) -> None:
        # pylint: disable=line-too-long
        r"""
        Adds a radio device or radio material to the scene

        If a different item with the same name as ``item`` is part of
        the scene, an error is raised.

        :param item: Item to be added to the scene
        """
        name = item.name
        s_item = self.get(name)
        if s_item is not None:
            if s_item is not item:
                raise ValueError(f"Name '{name}' is already used by another item"
                                 " of the scene")

            # This exact item was already added, skip it.
            return

        if isinstance(item, RadioMaterialBase):
            item.scene = self
            self._radio_materials[name] = item
        elif isinstance(item, Transmitter):
            self._transmitters[name] = item
        elif isinstance(item, Receiver):
            self._receivers[name] = item
        else:
            raise ValueError(
                f"Cannot add object of type {type(item)} to the scene."
                " The input must be a Transmitter, Receiver,"
                " or RadioMaterialBase.")

    def remove(self, name: str) -> None:
        # pylint: disable=line-too-long
        """
        Removes a radio device or radio material from the scene

        In the case of a radio material, it must not be used by any object of
        the scene.

        :param name: Name of the item to be removed
        """
        if not isinstance(name, str):
            raise ValueError("The input should be a string")
        item = self.get(name)

        if item is None:
            pass
        elif isinstance(item, RadioMaterialBase):
            if item.is_used:
                raise ValueError(f"Cannot remove the radio material '{name}'"
                                  " because it is still used by at least one"
                                  " object")
            del self._radio_materials[name]
        elif isinstance(item, Transmitter):
            del self._transmitters[name]
        elif isinstance(item, Receiver):
            del self._receivers[name]
        else:
            raise TypeError("Only Transmitters, Receivers, or RadioMaterials"
                            " can be removed")

    def edit(self,
             add: (sionna.rt.SceneObject |
                   list[sionna.rt.SceneObject] |
                   dict |
                   None)=None,
             remove: (str |
                      sionna.rt.SceneObject |
                      list[sionna.rt.SceneObject | str] |
                      None)=None
    ) -> None:
        r"""
        Add and/or remove a list of objects to/from the scene

        To optimize performance and reduce processing time, it is recommended
        to use a single call to this function with a list of objects to add
        and/or remove, rather than making multiple individual calls to edit
        scene objects.

        :param add: Object, or list /dictionary of objects to be added

        :param remove: Name or object, or list/dictionary of objects or names
            to be added
        """

        # Set the Mitsuba scene to the edited scene
        self._scene = edit_scene_shapes(self, add=add, remove=remove)

        # Reset the scene params
        self._scene_params = mi.traverse(self._scene)

        # Update the scene objects.
        # Scene objects are not re-instantiated to keep the instances held by
        # the users valid.
        scene_objects = dict(self._scene_objects)
        if add is not None:
            if isinstance(add, sionna.rt.SceneObject):
                add = [add]
            scene_objects.update({o.name: o for o in add})

        self._scene_objects = {}
        for s in self._scene.shapes():
            name = sionna.rt.SceneObject.shape_id_to_name(s.id())
            obj = scene_objects.get(name)
            assert obj
            obj.mi_mesh = s
            self._add_scene_object(obj)

        # Reset the preview widget to ensure the preview is redraw
        self.scene_geometry_updated()

    def preview(self, *,
        background: str = DEFAULT_PREVIEW_BACKGROUND_COLOR,
        clip_at: float | None = None,
        clip_plane_orientation: tuple[float, float, float] = (0,0,-1),
        fov: float = 45.,
        paths: sionna.rt.Paths | None = None,
        radio_map: sionna.rt.PlanarRadioMap | sionna.rt.MeshRadioMap | None = None,
        resolution: tuple[int, int] = (655, 500),
        rm_db_scale: bool = True,
        rm_metric : str  = "path_gain",
        rm_tx: int | str | None = None,
        rm_vmax: float | None = None,
        rm_vmin: float | None = None,
        rm_cmap: callable | str | None = None,
        show_devices: bool = True,
        show_orientations: bool = False,
        point_picker: bool = True
    ) -> None:
        # pylint: disable=line-too-long
        r"""In an interactive notebook environment, opens an interactive 3D viewer of the scene.

        Default color coding:

        * Green: Receiver
        * Blue: Transmitter

        Controls:

        * Mouse left: Rotate
        * Scroll wheel: Zoom
        * Mouse right: Move

        :param background: Background color in hex format prefixed by "#"

        :param clip_at: If not `None`, the scene preview will be clipped (cut)
            by a plane with normal orientation ``clip_plane_orientation`` and
            offset ``clip_at``.
            That means that everything *behind* the plane becomes invisible.
            This allows visualizing the interior of meshes, such as buildings.

        :param clip_plane_orientation: Normal vector of the clipping plane

        :param fov: Field of view [deg]

        :param paths: Optional propagation paths to be shown

        :param radio_map: Optional radio map to be shown

        :param resolution: Size of the viewer figure

        :param rm_db_scale: Use logarithmic scale for radio map
            visualization, i.e. the radio map values are mapped to:
            :math:`y = 10 \cdot \log_{10}(x)`.

        :param rm_metric: Metric of the radio map to be displayed
        :type rm_metric: "path_gain" | "rss" | "sinr"

        :param rm_tx: When ``radio_map`` is specified, controls for which of
            the transmitters the radio map is shown. Either the
            transmitter's name or index can be given. If `None`, the maximum
            metric over all transmitters is shown.

        :param rm_vmax: For radio map visualization, defines the maximum
            value that the colormap covers.
            It should be provided in dB if ``rm_db_scale`` is
            set to `True`, or in linear scale otherwise.

        :param rm_vmin: For radio map visualization, defines the minimum
            value that the colormap covers.
            It should be provided in dB if ``rm_db_scale`` is
            set to `True`, or in linear scale otherwise.

        :param rm_cmap: For coverage map visualization, defines the colormap to use.
            If set to None, then the default colormap is used.
            If a string is given, it is interpreted as a Matplotlib colormap name.
            If a callable is given, it is used as a custom colormap function with
            the same interface as a Matplotlib colormap.
            Defaults to `None`.

        :param show_devices: Show radio devices

        :param show_orientations: Show orientation of radio devices

        :param point_picker: Enable picking a point in the scene with
            alt + click in order to display its coordinates.
        """
        if (self._preview_widget is not None) and (resolution is not None):
            assert isinstance(resolution, (tuple, list)) and len(resolution) == 2
            if tuple(resolution) != self._preview_widget.resolution:
                # User requested a different rendering resolution, create
                # a new viewer from scratch to match it.
                self._preview_widget = None

        # Cache the render widget so that we don't need to re-create it
        # every time
        widget = self._preview_widget
        needs_reset = widget is not None
        show_paths = paths is not None
        if needs_reset:
            widget.reset()
        else:
            widget = Previewer(scene=self,
                               resolution=resolution,
                               fov=fov,
                               background=background)
            self._preview_widget = widget

        # Show paths and devices, if required
        if show_paths:
            widget.plot_paths(paths)
        if show_devices:
            widget.plot_radio_devices(show_orientations=show_orientations)
        if radio_map is not None:
            if isinstance(radio_map, sionna.rt.MeshRadioMap):
                widget.plot_mesh_radio_map(
                    radio_map, tx=rm_tx, db_scale=rm_db_scale,
                    vmin=rm_vmin, vmax=rm_vmax, metric=rm_metric,
                    cmap=rm_cmap)
            else:
                widget.plot_planar_radio_map(
                    radio_map, tx=rm_tx, db_scale=rm_db_scale,
                    vmin=rm_vmin, vmax=rm_vmax, metric=rm_metric,
                    cmap=rm_cmap)

        # Clipping
        widget.set_clipping_plane(offset=clip_at,
                                  orientation=clip_plane_orientation)

        if point_picker:
            widget.setup_point_picker()

        # Update the camera state
        if not needs_reset:
            widget.center_view()

        # Display the previewer and its companion widgets
        widget.display()


    def render(self, *,
        camera: Camera | str,
        clip_at: float | None = None,
        clip_plane_orientation: tuple[float, float, float] = (0,0,-1),
        envmap: str | None = None,
        fov: float | None = None,
        lighting_scale: float = 1.0,
        num_samples: int = 128,
        paths: sionna.rt.Paths | None = None,
        radio_map: sionna.rt.RadioMap | None = None,
        resolution: tuple[int, int] = (655, 500),
        return_bitmap: bool = False,
        rm_db_scale: bool = True,
        rm_metric: str = "path_gain",
        rm_show_color_bar: bool = False,
        rm_tx: int | str | None = None,
        rm_vmax: float | None = None,
        rm_vmin: float | None = None,
        rm_cmap: str | callable | None = None,
        show_devices: bool = True,
        show_orientations: bool = False
    ) -> plt.Figure | mi.Bitmap:
        # pylint: disable=line-too-long
        r"""Renders the scene from the viewpoint of a camera or the interactive viewer

        :param camera: Camera to be used for rendering the scene.
            If an interactive viewer was opened with
            :meth:`~sionna.rt.Scene.preview()`, `"preview"` can be to used
            to render the scene from its viewpoint.

        :param clip_at: If not `None`, the scene preview will be clipped (cut)
            by a plane with normal orientation ``clip_plane_orientation`` and
            offset ``clip_at``.
            That means that everything *behind* the plane becomes invisible.
            This allows visualizing the interior of meshes, such as buildings.

        :param clip_plane_orientation: Normal vector of the clipping plane

        :param envmap: Path to an environment map image file
            (e.g. in EXR format) to use for scene lighting

        :param fov: Field of view [deg]. If `None`, the field of view will
            default to 45 degrees, unless `camera` is set to `"preview"`, in
            which case the field of view of the preview camera is used.

        :param lighting_scale: Scale to apply to the lighting in the scene
            (e.g., from a constant uniform emitter or a given environment map)

        :param num_samples: Number of rays thrown per pixel

        :param paths: Optional propagation paths to be shown

        :param radio_map: Optional radio map to be shown

        :param resolution: Size of the viewer figure

        :param return_bitmap: If `True`, directly return the rendered image

        :param rm_db_scale: Use logarithmic scale for radio map
            visualization, i.e. the radio map values are mapped to:
            :math:`y = 10 \cdot \log_{10}(x)`.

        :param rm_metric: Metric of the radio map to be displayed
        :type rm_metric: "path_gain" | "rss" | "sinr"

        :param rm_show_color_bar: Show color bar

        :param rm_tx: When ``radio_map`` is specified, controls for which of
            the transmitters the radio map is shown. Either the
            transmitter's name or index can be given. If `None`, the maximum
            metric over all transmitters is shown.

        :param rm_vmax: For radio map visualization, defines the maximum
            value that the colormap covers.
            It should be provided in dB if ``rm_db_scale`` is
            set to `True`, or in linear scale otherwise.

        :param rm_vmin: For radio map visualization, defines the minimum
            value that the colormap covers.
            It should be provided in dB if ``rm_db_scale`` is
            set to `True`, or in linear scale otherwise.

        :param rm_cmap: For coverage map visualization, defines the colormap to use.
            If set to None, then the default colormap is used.
            If a string is given, it is interpreted as a Matplotlib colormap name.
            If a callable is given, it is used as a custom colormap function with
            the same interface as a Matplotlib colormap.
            Defaults to `None`.

        :param show_devices: Show radio devices

        :param show_orientations: Show orientation of radio devices
        """
        image = render(
            scene=self,
            camera=camera,
            paths=paths,
            show_devices=show_devices,
            show_orientations=show_orientations,
            clip_at=clip_at,
            clip_plane_orientation=clip_plane_orientation,
            radio_map=radio_map,
            rm_tx=rm_tx,
            rm_db_scale=rm_db_scale,
            rm_cmap=rm_cmap,
            rm_vmin=rm_vmin,
            rm_vmax=rm_vmax,
            rm_metric=rm_metric,
            num_samples=num_samples,
            resolution=resolution,
            fov=fov,
            envmap=envmap,
            lighting_scale=lighting_scale
        )
        if return_bitmap:
            return image

        to_show = image.convert(component_format=mi.Struct.Type.UInt8,
                                srgb_gamma=True)

        show_color_bar = (radio_map is not None) and rm_show_color_bar

        if show_color_bar:
            aspect = image.width()*1.06 / image.height()
            fig, ax = plt.subplots(1, 2,
                                   gridspec_kw={'width_ratios': [0.97, 0.03]},
                                   figsize=(aspect * 6, 6))
            im_ax = ax[0]
        else:
            aspect = image.width() / image.height()
            fig, ax = plt.subplots(1, 1, figsize=(aspect * 6, 6))
            im_ax = ax

        im_ax.imshow(to_show)

        if show_color_bar:
            cm = getattr(radio_map, rm_metric).numpy()
            if rm_tx is None:
                cm = np.max(cm, axis=0)
            else:
                cm = cm[rm_tx]
                # Ensure that dBm is correctly computed for RSS
            if rm_metric=="rss" and rm_db_scale:
                cm *= 1000
            _, normalizer, color_map = radio_map_color_mapping(
                cm, db_scale=rm_db_scale,
                vmin=rm_vmin, vmax=rm_vmax)
            mappable = matplotlib.cm.ScalarMappable(
                norm=normalizer, cmap=color_map)

            cax = ax[1]
            if rm_metric=="rss" and rm_db_scale:
                cax.set_title("dBm")
            else:
                cax.set_title('dB')
            fig.colorbar(mappable, cax=cax)

        # Remove axes and margins
        im_ax.axis('off')
        fig.tight_layout()
        return fig

    def render_to_file(self, *,
        camera: Camera | str,
        filename: str,
        clip_at: float | None=None,
        clip_plane_orientation: tuple[float, float, float]=(0,0,-1),
        envmap: str | None = None,
        fov: float | None = None,
        lighting_scale: float = 1.0,
        num_samples: int = 512,
        paths: sionna.rt.Paths | None = None,
        radio_map: sionna.rt.RadioMap | None = None,
        resolution: tuple[int, int] = (655, 500),
        rm_db_scale: bool=True,
        rm_metric: str ="path_gain",
        rm_tx: int | str | None=None,
        rm_vmin: float | None=None,
        rm_vmax: float | None=None,
        show_devices: bool=True,
        show_orientations: bool=True
    ) -> mi.Bitmap:
        # pylint: disable=line-too-long
        r"""Renders the scene from the viewpoint of a camera or the interactive
        viewer, and saves the resulting image

        :param camera: Camera to be used for rendering the scene.
            If an interactive viewer was opened with
            :meth:`~sionna.rt.Scene.preview()`, `"preview"` can be to used
            to render the scene from its viewpoint.

        :param filename: Filename for saving the rendered image,
            e.g., "my_scene.png"

        :param clip_at: If not `None`, the scene preview will be clipped (cut)
            by a plane with normal orientation ``clip_plane_orientation`` and
            offset ``clip_at``.
            That means that everything *behind* the plane becomes invisible.
            This allows visualizing the interior of meshes, such as buildings.

        :param clip_plane_orientation: Normal vector of the clipping plane

        :param envmap: Path to an environment map image file
            (e.g. in EXR format) to use for scene lighting

        :param fov: Field of view [deg]. If `None`, the field of view will
            default to 45 degrees, unless `camera` is set to `"preview"`, in
            which case the field of view of the preview camera is used.

        :param lighting_scale: Scale to apply to the lighting in the scene
            (e.g., from a constant uniform emitter or a given environment map)

        :param num_samples: Number of rays thrown per pixel

        :param paths: Optional propagation paths to be shown

        :param radio_map: Optional radio map to be shown

        :param resolution: Size of the viewer figure

        :param rm_db_scale: Use logarithmic scale for radio map
            visualization, i.e. the radio map values are mapped to:
            :math:`y = 10 \cdot \log_{10}(x)`.

        :param rm_metric: Metric of the radio map to be displayed
        :type rm_metric: "path_gain" | "rss" | "sinr"

        :param rm_tx: When ``radio_map`` is specified, controls for which of
            the transmitters the radio map is shown. Either the
            transmitter's name or index can be given. If `None`, the maximum
            metric over all transmitters is shown.

        :param rm_vmax: For radio map visualization, defines the maximum
            value that the colormap covers.
            It should be provided in dB if ``rm_db_scale`` is
            set to `True`, or in linear scale otherwise.

        :param rm_vmin: For radio map visualization, defines the minimum
            value that the colormap covers.
            It should be provided in dB if ``rm_db_scale`` is
            set to `True`, or in linear scale otherwise.

        :param show_devices: Show radio devices

        :param show_orientations: Show orientation of radio devices
        """
        image = render(
            scene=self,
            camera=camera,
            paths=paths,
            show_devices=show_devices,
            show_orientations=show_orientations,
            clip_at=clip_at,
            clip_plane_orientation=clip_plane_orientation,
            radio_map=radio_map,
            rm_tx=rm_tx,
            rm_db_scale=rm_db_scale,
            rm_vmin=rm_vmin,
            rm_vmax=rm_vmax,
            rm_metric=rm_metric,
            num_samples=num_samples,
            resolution=resolution,
            fov=fov,
            envmap=envmap,
            lighting_scale=lighting_scale
        )

        ext = os.path.splitext(filename)[1].lower()
        if ext in ('.jpg', '.jpeg', '.ppm',):
            image = image.convert(component_format=mi.Struct.Type.UInt8,
                                  pixel_format=mi.Bitmap.PixelFormat.RGB,
                                  srgb_gamma=True)
        elif ext in ('.png', '.tga' '.bmp'):
            image = image.convert(component_format=mi.Struct.Type.UInt8,
                                  srgb_gamma=True)
        image.write(filename)
        return image

    @property
    def mi_scene_params(self):
        r"""
        :py:class:`mi.SceneParameters`: Mitsuba scene parameters
        """
        return self._scene_params

    @property
    def mi_scene(self):
        r"""
        :py:class:`mi.Scene`: Mitsuba scene
        """
        return self._scene

    # pylint: disable=line-too-long
    def sources(self,
                synthetic_array: bool,
                return_velocities: bool
                ) -> tuple[mi.Point3f, mi.Point3f, mi.Point3f | None, mi.Vector3f | None]:
        r"""
        Builds arrays containing the positions and orientations of the
        sources

        If synthetic arrays are not used, then every transmit antenna is modeled
        as a source of paths. Otherwise, transmitters are modelled as if they
        had a single antenna located at their :attr:`~sionna.rt.RadioDevice.position`.

        :return: Positions of the sources
        :return: Orientations of the sources
        :return: Positions of the antenna elements relative to the transmitters
            positions. `None` is returned if ``synthetic_array`` is `True`.
        :return: Velocities of the transmitters. `None` is returned if
            `return_velocities` is set to `False`.
        """

        return self._endpoints(self.transmitters.values(),
                               self.tx_array,
                               synthetic_array,
                               return_velocities)

    # pylint: disable=line-too-long
    def targets(self,
                synthetic_array: bool,
                return_velocities: bool,
                ) -> tuple[mi.Point3f, mi.Point3f, mi.Point3f | None, mi.Vector3f | None]:
        r"""
        Builds arrays containing the positions and orientations of the targets

        If synthetic arrays are not used, then every receiver antenna is modeled
        as a source of paths. Otherwise, receivers are modelled as if they
        had a single antenna located at their :attr:`~sionna.rt.RadioDevice.position`.

        :return: Positions of the targets
        :return: Orientations of the targets
        :return: Positions of the antenna elements relative to the receivers.
            Only returned if ``synthetic_array`` is `True`.
        :return: Velocities of the transmitters. `None` is returned if
            `return_velocities` is set to `False`.
        """

        return self._endpoints(self.receivers.values(),
                               self.rx_array,
                               synthetic_array,
                               return_velocities)

    def scene_geometry_updated(self) -> None:
        """
        Callback to trigger when the scene geometry is updated
        """
        # Update the scene geometry in the preview
        if self._preview_widget:
            self._preview_widget.redraw_scene_geometry()

    def all_set(self, radio_map: bool) -> None:
        # pylint: disable=line-too-long
        r"""
        Raises an exception if the scene is not all set for simulations

        :param radio_map: Set to `True` if checking for radio map computation. Set to `False` otherwise.
        """

        if self.tx_array is None:
            raise ValueError("Transmitter array not set")

        if len(self.transmitters) == 0:
            raise ValueError("Scene has no transmitters")

        if not radio_map:
            if self.rx_array is None:
                raise ValueError("Receiver array not set")
            if len(self.receivers) == 0:
                raise ValueError("Scene has no receivers")

    ##################################################
    # Internal methods
    ##################################################

    @contextlib.contextmanager
    def use_mi_scene(self, scene: mi.Scene):
        old_scene = self._scene
        self._scene = scene
        yield
        self._scene = old_scene

    def _load_scene_objects(self, remove_duplicate_vertices: bool):
        """
        Builds Sionna SceneObject instances from the Mistuba scene
        """

        # List of shapes
        shapes = self._scene.shapes()

        # Parse all shapes in the scene
        for s in shapes:

            # Only meshes are supported
            if not isinstance(s, mi.Mesh):
                raise TypeError('Only triangle meshes are supported')

            # Instantiate the scene object
            scene_object = sionna.rt.SceneObject(mi_mesh=s,
                                                 remove_duplicate_vertices=remove_duplicate_vertices)

            # Add a scene object to the scene
            self._add_scene_object(scene_object)

    def _add_scene_object(self, scene_object: sionna.rt.SceneObject) -> None:
        r"""
        Add `scene_object` to the scene. Note that this function does not
        add the object to the Mitsuba scene, just to the Sionna wrapper.

        :param scene_object: Object to add
        """

        if not isinstance(scene_object, sionna.rt.SceneObject):
            raise ValueError("The input must be a SceneObject")

        name = scene_object.name
        s_item = self.get(name)
        if s_item is not None:
            if s_item is not scene_object:
                raise ValueError(f"Name '{name}' is already used by another item"
                                 " of the scene")
            else:
                # This item was already added.
                return

        # Add the scene object and its material

        # Check if the scene object is a measurement surface
        if not scene_object.radio_material:
            raise ValueError(f"Object {scene_object.name} has no radio"
                             " material assigned to it")
        scene_object.scene = self
        self._scene_objects[scene_object.name] = scene_object
        # Add the scene object radio material as well
        self.add(scene_object.radio_material)

    def _is_name_used(self, name: str) -> bool:
        """
        Returns `True` if ``name`` is used by a scene object, a transmitter,
        a receiver, or a radio material. Returns `False` otherwise.

        :param name: Name
        """
        used = ((name in self._radio_materials)
             or (name in self._scene_objects)
             or (name in self._transmitters)
             or (name in self._receivers))
        return used

    def _endpoints(self,
                   radio_devices: List[mi.Transmitter | mi.Receiver],
                   array: AntennaArray,
                   synthetic_array: bool,
                   return_velocities: bool
                  ) -> tuple[mi.Point3f, mi.Point3f, mi.Point3f | None, mi.Vector3f | None]:
        r"""
        Builds arrays containing the positions and orientations of the
        endpoints (sources or targets)

        If synthetic arrays are not used, then every antenna is modeled
        as an endpoint of paths. Otherwise, radio devices are modelled as if
        they had a single antenna located at their
        :attr:`~sionna.rt.RadioDevice.position`.

        :param radio_devices: List of radio devices, i.e., transmitters or
            receivers
        :param array: Antenna array used by the radio devices
        :param synthetic_array: Flag indicating if a synthetic array is used
        :param return_velocities: If set to `True`, then the velocities of the
            radio devices are returned

        :return: Positions of the endpoints
        :return: Orientations of the endpoints
        :return: Positions of the antenna elements relative to the endpoints
            positions. `None` is returned if ``synthetic_array`` is `True`.
        :return: Velocities of the radio devices. `None` is returned
            if `return_velocities` is set to `False`.
        """

        n_dev = len(radio_devices)
        if synthetic_array or (array is None):
            n_ep = n_dev
            eff_array_size_src = 1
        else:
            n_ep = n_dev*array.array_size
            eff_array_size_src = array.array_size

        positions = dr.zeros(mi.Point3f, n_ep)
        orientations = dr.zeros(mi.Point3f, n_ep)
        if synthetic_array:
            rel_ant_positions = dr.zeros(mi.Point3f,
                                         n_ep*array.array_size)
            rel_and_ind = dr.arange(mi.UInt, array.array_size)
        else:
            rel_ant_positions = None

        if return_velocities:
            velocities = dr.zeros(mi.Vector3f, n_dev)
        else:
            velocities = None

        s = dr.arange(mi.UInt, eff_array_size_src)
        for i,dev in enumerate(radio_devices):
            p = dev.position
            o = dev.orientation
            v = dev.velocity
            if synthetic_array:
                p_ant = array.rotate(self.wavelength, o)
                ind = rel_and_ind+i*array.array_size
                dr.scatter(rel_ant_positions.x, p_ant.x, ind)
                dr.scatter(rel_ant_positions.y, p_ant.y, ind)
                dr.scatter(rel_ant_positions.z, p_ant.z, ind)
            else:
                p = array.rotate(self.wavelength, o) + p
            ind = s+i*eff_array_size_src
            dr.scatter(positions.x, p.x, ind)
            dr.scatter(positions.y, p.y, ind)
            dr.scatter(positions.z, p.z, ind)
            #
            dr.scatter(orientations.x, o.x, ind)
            dr.scatter(orientations.y, o.y, ind)
            dr.scatter(orientations.z, o.z, ind)
            #
            if return_velocities:
                dr.scatter(velocities.x, v.x, i)
                dr.scatter(velocities.y, v.y, i)
                dr.scatter(velocities.z, v.z, i)

        return positions, orientations, rel_ant_positions, velocities

def load_scene(filename: str | None = None,
               merge_shapes: bool = True,
               merge_shapes_exclude_regex: str | None = None,
               remove_duplicate_vertices: bool = False) -> Scene:
    # pylint: disable=line-too-long
    r"""
    Loads a scene from file

    :param filename: Name of a valid scene file.
        Sionna uses the simple XML-based format
        from `Mitsuba 3 <https://mitsuba.readthedocs.io/en/stable/src/key_topics/scene_format.html>`_.
        For `None`, an empty scene is created.

    :param merge_shapes: If set to `True`, shapes that share
        the same radio material are merged.

    :param merge_shapes_exclude_regex: Optional regex to exclude shapes from
        merging. Only used if ``merge_shapes`` is set to `True`.

    :param remove_duplicate_vertices: If set to `True`, duplicate vertices are
        removed from the scene objects.
    """
    if filename is None:
        return Scene()

    with open(filename, "r") as f: # pylint: disable=unspecified-encoding
        xml_string = f.read()

    # Since we will be loading directly from a string, we have to make sure
    # the directory containing the scene is part of the search path.
    fres_old = mi.file_resolver()
    fres = mi.FileResolver(fres_old)
    fres.append(os.path.dirname(filename))

    try:
        mi.set_file_resolver(fres)
        loaded = load_scene_from_string(
            xml_string, merge_shapes=merge_shapes,
            merge_shapes_exclude_regex=merge_shapes_exclude_regex,
            remove_duplicate_vertices=remove_duplicate_vertices
        )
    finally:
        mi.set_file_resolver(fres_old)

    return loaded


def load_scene_from_string(
    xml_string: str, merge_shapes: bool = True,
    merge_shapes_exclude_regex: str | None = None,
    remove_duplicate_vertices: bool = False
) -> Scene:
    r"""
    Loads a scene from an XML string.

    :param scene_string: XML string containing the scene.
    :param merge_shapes: If set to `True`, shapes that share
        the same radio material are merged.
    :param merge_shapes_exclude_regex: Optional regex to exclude shapes from
        merging. Only used if ``merge_shapes`` is set to `True`.
    :param remove_duplicate_vertices: If set to `True`, duplicate vertices are
        removed from the scene objects.
    """
    processed = process_xml(xml_string, merge_shapes=merge_shapes,
                        merge_shapes_exclude_regex=merge_shapes_exclude_regex)
    mi_scene = mi.load_string(processed, optimize=False)

    return Scene(mi_scene=mi_scene,
                 remove_duplicate_vertices=remove_duplicate_vertices)


#
# Module variables for example scene files
#

box = str(files(scenes).joinpath("box/box.xml"))
# pylint: disable=C0301
"""
Example scene containing a metallic box

.. figure:: ../figures/box.png
   :align: center
"""

simple_reflector = str(files(scenes).joinpath("simple_reflector/simple_reflector.xml"))
# pylint: disable=C0301
"""
Example scene containing a metallic reflector

.. figure:: ../figures/simple_reflector.png
   :align: center
"""

simple_wedge = str(files(scenes).joinpath("simple_wedge/simple_wedge.xml"))
# pylint: disable=C0301
r"""
Example scene containing a wedge with a :math:`90^{\circ}` opening angle

.. figure:: ../figures/simple_wedge.png
   :align: center
"""

box_one_screen = str(files(scenes).joinpath("box_one_screen/box_one_screen.xml"))
# pylint: disable=C0301
"""
Example scene containing a metallic box and a screen made of glass

Note: In the figure below, the upper face of the box has been removed for
visualization purposes. In the actual scene, the box is closed on all sides.

.. figure:: ../figures/box_one_screen.png
   :align: center
"""

box_two_screens = str(files(scenes).joinpath("box_two_screens/box_two_screens.xml"))
# pylint: disable=C0301
"""
Example scene containing a metallic box and two screens made of glass

Note: In the figure below, the upper face of the box has been removed for
visualization purposes. In the actual scene, the box is closed on all sides.

.. figure:: ../figures/box_two_screens.png
   :align: center
"""

box_knife = str(files(scenes).joinpath("box_knife/box_knife.xml"))
# pylint: disable=C0301
"""
Example scene containing a metallic box and a knife made of glass

.. figure:: ../figures/box_knife.png
   :align: center
"""

etoile = str(files(scenes).joinpath("etoile/etoile.xml"))
# pylint: disable=C0301
"""
Example scene containing the area around the Arc de Triomphe in Paris
The scene was created with data downloaded from `OpenStreetMap <https://www.openstreetmap.org>`_ and
the help of `Blender <https://www.blender.org>`_ and the `Blender-OSM <https://github.com/vvoovv/blender-osm>`_
and `Mitsuba Blender <https://github.com/mitsuba-renderer/mitsuba-blender>`_ add-ons.
The data is licensed under the `Open Data Commons Open Database License (ODbL) <https://openstreetmap.org/copyright>`_.

.. figure:: ../figures/etoile.png
   :align: center
"""

munich = str(files(scenes).joinpath("munich/munich.xml"))
# pylint: disable=C0301
"""
Example scene containing the area around the Frauenkirche in Munich
The scene was created with data downloaded from `OpenStreetMap <https://www.openstreetmap.org>`_ and
the help of `Blender <https://www.blender.org>`_ and the `Blender-OSM <https://github.com/vvoovv/blender-osm>`_
and `Mitsuba Blender <https://github.com/mitsuba-renderer/mitsuba-blender>`_ add-ons.
The data is licensed under the `Open Data Commons Open Database License (ODbL) <https://openstreetmap.org/copyright>`_.

.. figure:: ../figures/munich.png
   :align: center
"""

florence = str(files(scenes).joinpath("florence/florence.xml"))
# pylint: disable=C0301
"""
Example scene containing the area around the Florence Cathedral in Florence
The scene was created with data downloaded from `OpenStreetMap <https://www.openstreetmap.org>`_ and
the help of `Blender <https://www.blender.org>`_ and the `Blender-OSM <https://github.com/vvoovv/blender-osm>`_
and `Mitsuba Blender <https://github.com/mitsuba-renderer/mitsuba-blender>`_ add-ons.
The data is licensed under the `Open Data Commons Open Database License (ODbL) <https://openstreetmap.org/copyright>`_.

.. figure:: ../figures/florence.png
   :align: center
"""

san_francisco = str(files(scenes).joinpath("san_francisco/san_francisco.xml"))
# pylint: disable=C0301
"""
Example scene containing a portion of San Francisco.
The scene was created with data downloaded from `OpenStreetMap <https://www.openstreetmap.org>`_ and
the help of `Blender <https://www.blender.org>`_ and the `Blender-OSM <https://github.com/vvoovv/blender-osm>`_
and `Mitsuba Blender <https://github.com/mitsuba-renderer/mitsuba-blender>`_ add-ons.
The data is licensed under the `Open Data Commons Open Database License (ODbL) <https://openstreetmap.org/copyright>`_.

.. figure:: ../figures/san_francisco.png
   :align: center
"""

low_poly_car = str(files(scenes).joinpath("low_poly_car.ply"))
# pylint: disable=C0301
"""
Simple mesh of a car

.. figure:: ../figures/low_poly_car.png
   :align: center
   :width: 50%
"""

sphere = str(files(scenes).joinpath("sphere.ply"))
# pylint: disable=C0301
"""
Mesh of a sphere

.. figure:: ../figures/sphere.png
   :align: center
   :width: 50%
"""

floor_wall = str(files(scenes).joinpath("floor_wall/floor_wall.xml"))
# pylint: disable=C0301
"""
Example scene containing a ground plane and a vertical wall

.. figure:: ../figures/floor_wall.png
   :align: center
"""

# pylint: disable=C0301
simple_street_canyon = str(files(scenes).joinpath("simple_street_canyon/simple_street_canyon.xml"))
"""
Example scene containing a few rectangular building blocks and a ground plane

.. figure:: ../figures/street_canyon.png
   :align: center
"""

# pylint: disable=C0301
simple_street_canyon_with_cars = str(files(scenes).joinpath("simple_street_canyon_with_cars/simple_street_canyon_with_cars.xml"))
"""
Example scene containing a few rectangular building blocks and a ground plane as well as some cars

.. figure:: ../figures/street_canyon_with_cars.png
   :align: center
"""

double_reflector = str(files(scenes).joinpath("double_reflector/double_reflector.xml"))
# pylint: disable=C0301
r"""
Example scene containing two metallic squares

.. figure:: ../figures/double_reflector.png
   :align: center
"""

triple_reflector = str(files(scenes).joinpath("triple_reflector/triple_reflector.xml"))
# pylint: disable=C0301
r"""
Example scene containing three metallic rectangles

.. figure:: ../figures/triple_reflector.png
   :align: center
"""
