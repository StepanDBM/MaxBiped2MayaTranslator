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
def set_world_position(node, position):
    node = genUtils.resolve_node(
        node
    )

    cmds.xform(
        node,
        ws=True,
        t=position
    )

def get_world_matrix(node):
    node = genUtils.resolve_node(
        node
    )

    return cmds.xform(
        node,
        q=True,
        ws=True,
        m=True
    )


def set_world_matrix(node, matrix):
    node = genUtils.resolve_node(
        node
    )

    cmds.xform(
        node,
        ws=True,
        m=matrix
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


def vec_cross(a, b):
    return [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0]
    ]

def flatten_to_axis(position, axis, value):
    """
    Returns a position with one forced world axis value.
    axis:
        "x", "y", or "z"
    """

    result = list(position)

    axis = axis.lower()

    axis_indices = {
        "x": 0,
        "y": 1,
        "z": 2
    }

    if axis not in axis_indices:
        raise ValueError(
            "Invalid axis '{}'. Expected 'x', 'y', or 'z'.".format(axis)
        )

    result[axis_indices[axis]] = value

    return result