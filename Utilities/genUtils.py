import maya.cmds as cmds
import re

def clean_name(name):

    name = name.split("|")[-1]

    name = re.sub(
        r"FBXASC032",
        "_",
        name,
        flags=re.IGNORECASE
    )

    while "__" in name:
        name = name.replace("__", "_")

    return name

def ensure_group(name, parent=None):
    """
    Creates a group if it does not exist.
    Optionally parents it under another group.
    """

    if cmds.objExists(name):
        grp = name
    else:
        grp = cmds.group(
            em=True,
            n=name
        )

    if parent and cmds.objExists(parent):
        current_parent = cmds.listRelatives(
            grp,
            parent=True,
            fullPath=False
        )

        if not current_parent or current_parent[0] != parent:
            try:
                grp = cmds.parent(
                    grp,
                    parent
                )[0]
            except Exception:
                pass

    return grp


def resolve_node(node):
    """
    Resolves a Maya node name even if an old full DAG path was stored.
    Returns a valid node name.
    """

    if cmds.objExists(node):
        return node

    short = node.split("|")[-1]

    matches = cmds.ls(
        short,
        long=False
    ) or []

    if matches:
        return matches[0]

    matches = cmds.ls(
        short,
        long=True
    ) or []

    if matches:
        return matches[0]

    raise RuntimeError(
        "Could not resolve node: {}".format(node)
    )