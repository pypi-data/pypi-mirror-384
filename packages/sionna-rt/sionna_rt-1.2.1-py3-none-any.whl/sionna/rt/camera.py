#
# SPDX-FileCopyrightText: Copyright (c) 2021-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
"""
Implements a camera for rendering of a scene.
A camera defines a viewpoint for rendering.
"""
from __future__ import annotations

import drjit as dr
import mitsuba as mi

from sionna import rt


class Camera:
    # pylint: disable=line-too-long
    r"""
    Camera defining a position and view direction for rendering a scene

    In its local coordinate system, a camera looks toward the positive X-axis
    with the positive Z-axis being the upward direction.

    :param position: Position :math:`(x,y,z)` [m] as three-dimensional vector
    :param orientation: Orientation :math:`(\alpha, \beta, \gamma)` specified
        through three angles corresponding to a 3D rotation
        as defined in :eq:`rotation`.
        This parameter is ignored if ``look_at`` is not `None`.
    :param look_at: A position or object to look at.
        If set to `None`, then ``orientation`` is used to orient the device.
    """

    # The convention of Mitsuba for camera is Y as up and look toward Z+.
    # However, Sionna uses Z as up and looks toward X+, for consistency
    # with radio devices.
    # The following transform peforms a rotation to ensure Sionna's
    # convention.
    # Note: rotation angle is specified in degrees.
    mi_to_sionna = (
          mi.Transform4f().rotate((0, 0, 1), 90.0)
        @ mi.Transform4f().rotate((1, 0, 0), 90.0)
    )

    def __init__(
        self,
        position: mi.Point3f,
        orientation: mi.Point3f = (0.,0.,0.),
        look_at: rt.RadioDevice | rt.SceneObject | mi.Poin3f | None = None):
        # Keep track of the "to world" transform.
        # Initialized to identity.
        self._to_world = mi.Transform4f()

        if look_at is not None:
            if orientation != (0., 0., 0.):
                raise ValueError("Cannot specify both `orientation` and"
                                 " `look_at`")

            # Set the position before the look_at so that the camera
            # really points to the target.
            self.position = position
            self.look_at(look_at)
        else:
            self.orientation = orientation
            # Set the position after the rotation so that it isn't affected.
            self.position = position

    @property
    def position(self):
        """
        Get/set the position

        :type: :py:class:`mi.Point3f`
        """
        return Camera.world_to_position(self._to_world)

    @position.setter
    def position(self, v):
        v = mi.Point3f(v)
        # Update transform
        c_to_world = self._to_world.matrix
        to_world = mi.Matrix4f(
            c_to_world[0].x, c_to_world[0].y, c_to_world[0].z, v.x,
            c_to_world[1].x, c_to_world[1].y, c_to_world[1].z, v.y,
            c_to_world[2].x, c_to_world[2].y, c_to_world[2].z, v.z,
            0.,                           0.,              0.,  1.)
        self._to_world = mi.Transform4f(to_world)

    @property
    def orientation(self):
        r"""
         Get/set the orientation

        :type: :py:class:`mi.Point3f`
        """
        return Camera.world_to_angles(self._to_world)

    @orientation.setter
    def orientation(self, v):
        v = mi.Point3f(v)

        # Mitsuba transform
        # Note: Mitsuba uses degrees
        v = v * 180.0 / dr.pi
        rot_x = mi.Transform4f().rotate(mi.Point3f(1, 0, 0), v.z)
        rot_y = mi.Transform4f().rotate(mi.Point3f(0, 1, 0), v.y)
        rot_z = mi.Transform4f().rotate(mi.Point3f(0, 0, 1), v.x)
        rot_mat = rot_z @ rot_y @ rot_x @ Camera.mi_to_sionna
        # Translation to keep the current position
        trs = mi.Transform4f().translate(self.position)
        to_world = trs @ rot_mat
        # Update in Mitsuba
        self._to_world = to_world

    def look_at(
        self,
        target: rt.RadioDevice | rt.SceneObject | mi.Point3f) -> None:
        r"""
        Sets the orientation so that the camera looks at a position,
        scene object, or radio device

        Given a point :math:`\mathbf{x}\in\mathbb{R}^3` with spherical angles
        :math:`\theta` and :math:`\varphi`, the orientation of the camera
        will be set equal to :math:`(\varphi, \frac{\pi}{2}-\theta, 0.0)`.

        :param target: A position or object to look at.
        """
        # Get position to look at
        if isinstance(target, (rt.RadioDevice, rt.SceneObject)):
            target = target.position
        else:
            target = mi.Point3f(target)

        # If the position and the target are on a line that is parallel to z,
        # then the look-at transform is ill-defined as z is up.
        # In this case, we add a small epsilon to x to avoid this.
        aligned = rt.isclose(self.position.x, target.x)\
            & rt.isclose(self.position.y, target.y)
        aligned = aligned.numpy()[0]
        if aligned:
            target.x = target.x + 1e-3
        # Look-at transform (recall Sionna uses Z-up)
        self._to_world = mi.Transform4f().look_at(self.position, target,
                                                  mi.Vector3f(0.0, 0.0, 1.0))

    ##############################################
    # Internal methods and class functions.
    # Should not be appear in the end user
    # documentation.
    ##############################################

    @property
    def world_transform(self):
        r"""World transform, i.e., transform from local camera frame to world
        frame

        :type: :py:class:`mi.Transform4f`
        """
        return self._to_world

    @staticmethod
    def world_to_angles(to_world: mi.Transform4f) -> mi.Point3f:
        r"""
        Extracts the orientation angles `[alpha,beta,gamma]` corresponding to a
        ``to_world`` transform

        :param to_world: Transform
        """

        # Undo the rotation to switch from Mitsuba to Sionna convention
        to_world = to_world @ Camera.mi_to_sionna.inverse()
        r_mat = to_world.matrix

        # Compute angles
        x_ang = dr.atan2(r_mat[2,1], r_mat[2,2])
        y_ang = dr.atan2(-r_mat[2,0],
                         dr.sqrt(dr.square(r_mat[2,1]) + dr.square(r_mat[2,2])))
        z_ang = dr.atan2(r_mat[1,0], r_mat[0,0])

        return mi.Point3f(z_ang, y_ang, x_ang)

    @staticmethod
    def world_to_position(to_world: mi.Transform4f) -> mi.Point3f:
        r"""
        Extracts the translation component of a ``to_world`` transform.
        If it has multiple entries, throw an exception.

        :param to_world: Transform
        """
        p = mi.Point3f(to_world.translation())
        return p
