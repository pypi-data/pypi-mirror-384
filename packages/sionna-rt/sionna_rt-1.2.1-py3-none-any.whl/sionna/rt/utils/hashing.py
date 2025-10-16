#
# SPDX-FileCopyrightText: Copyright (c) 2021-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
"""Hashing utilities for path solvers."""

import mitsuba as mi
import drjit as dr
from typing import Literal


def hash_fnv1a(x: mi.UInt32 | mi.UInt64,
               h: mi.UInt64 =
                   mi.UInt64(14695981039346656037)) -> mi.UInt64:
    """
    FNV-1a hash function for a floating-point number.
    http://www.isthe.com/chongo/tech/comp/fnv/#FNV-1a

    :param x: Input value to hash
    :param h: Current hash value (default is the 64-bit FNV-1a offset basis)
    """
    if isinstance(x, mi.UInt32):
        num_bytes = 4
    elif isinstance(x, mi.UInt64):
        num_bytes = 8
    else:
        raise TypeError("Input must be either mi.UInt32 or mi.UInt64.")

    prime = mi.UInt64(1099511628211)
    for _ in range(num_bytes):
        h = (h ^ (x & 0xFF)) * prime
        x = x >> 8

    return h

class GeometricElementHasher:
    """
    Abstract class for hashing geometric elements
    """
    def __init__(self, op: Literal['round', 'floor'] = 'round'):
        self.op = getattr(dr, op)
        if op == 'round':
            self.offset = 0.04281
        else:
            self.offset = 0.06284

    def quantize(self, x: mi.Float, eps: float = 1e-5) -> mi.UInt32:
        """
        Quantizes a floating-point value to a 32-bit unsigned integer.
        It is first rounded to the nearest multiple of `eps` to
        ensure a consistent hashing despite floating-point precision issues.

        :param x: Input value to quantize
        :param eps: Desired precision

        :return: Quantized value as a 32-bit unsigned integer
        """
        x = dr.select(dr.abs(x) < eps, 0.0, x)
        x = self.op((x + self.offset*eps) / eps)
        return dr.reinterpret_array(mi.UInt32, x)

    def __call__(self, *args, **kwargs):
        raise NotImplementedError("This is an abstract class.")


class PlaneHasher(GeometricElementHasher):
    """
    Hash function for planes. Relies on the FNV-1a hash function.
    """

    def __call__(self,
                 n : mi.Normal3f,
                 p : mi.Point3f) -> mi.UInt64:
        n = dr.normalize(n)
        # Enforce a consistent orientation of the normal vector
        flip_eps = 1e-4
        flip_n = (n.z < -flip_eps) \
                 | ((dr.abs(n.z) < flip_eps) & (n.y < -flip_eps)) \
                 | ((dr.abs(n.z) < flip_eps) & (dr.abs(n.y) < flip_eps)
                    & (n.x < -flip_eps))
        n = dr.select(flip_n, -n, n)
        d = dr.dot(n, p)

        h = hash_fnv1a(self.quantize(n.x))
        h = hash_fnv1a(self.quantize(n.y), h=h)
        h = hash_fnv1a(self.quantize(n.z), h=h)
        h = hash_fnv1a(self.quantize(d, eps=1e-3), h=h)
        return h


class EdgeHasher(GeometricElementHasher):
    """
    Hash function for edges. Relies on the FNV-1a hash function.
    """

    def __call__(self,
                 p1 : mi.Point3f,
                 p2 : mi.Point3f) -> mi.UInt64:
        # Enforce a consistent order of endpoints
        flip_eps = 1e-4
        flip_points = (p2.z < p1.z + flip_eps) | \
                    ( (dr.abs(p1.z - p2.z) < flip_eps)\
                        & (p2.y < p1.y + flip_eps) ) | \
                    ( (dr.abs(p1.z - p2.z) < flip_eps)\
                        & (dr.abs(p1.y - p2.y) < flip_eps)\
                        & (p2.x < p1.x + flip_eps) )
        p1_ = dr.select(flip_points, p2, p1)
        p2_ = dr.select(flip_points, p1, p2)

        # Hash the sequence of float (p1.x, p1.y, p1.z, p2.x, p2.y, p2.z)
        h = hash_fnv1a(self.quantize(p1_.x))
        h = hash_fnv1a(self.quantize(p1_.y), h=h)
        h = hash_fnv1a(self.quantize(p1_.z), h=h)
        h = hash_fnv1a(self.quantize(p2_.x), h=h)
        h = hash_fnv1a(self.quantize(p2_.y), h=h)
        h = hash_fnv1a(self.quantize(p2_.z), h=h)
        return h
