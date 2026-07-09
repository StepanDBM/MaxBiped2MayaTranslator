import Utilities.genUtils as genUtils
import maya.cmds as cmds
import importlib
importlib.reload(genUtils)

def get_world_pos(obj):

    obj = genUtils.resolve_node(obj)

    return cmds.xform(
        obj,
        q=True,
        ws=True,
        t=True
    )


def vec_add(a, b):
    return [
        a[0] + b[0],
        a[1] + b[1],
        a[2] + b[2]
    ]


def vec_sub(a, b):
    return [
        a[0] - b[0],
        a[1] - b[1],
        a[2] - b[2]
    ]


def vec_mul(v, scalar):
    return [
        v[0] * scalar,
        v[1] * scalar,
        v[2] * scalar
    ]


def vec_dot(a, b):
    return (
        a[0] * b[0] +
        a[1] * b[1] +
        a[2] * b[2]
    )


def vec_length(v):
    return max(
        (
            v[0] ** 2 +
            v[1] ** 2 +
            v[2] ** 2
        ) ** 0.5,
        0.00001
    )

def vec_normalize(v):

    length = vec_length(v)

    return [
        v[0] / length,
        v[1] / length,
        v[2] / length
    ]