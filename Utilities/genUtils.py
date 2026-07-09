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

import re
import maya.cmds as cmds


def clean_name(name):
    """
    Converts Maya/FBX space-imbued incomprehensible names into clean readable names.
    FBXASC032 is Maya's internal naming convention for FBX imports that
    use spaces in names. This function replaces those with FBXASC032 which is now 
    impossible to replace because the Unity system and project is FULL of characters
    with FBXASC032 in them. This is ONLY for runtime processes of THIS script and
    should not be used to rename the actual final nodes (joints, geometry, animation
    curves, etc.) in the scene.

    Example:
        |Bip001|Bip001FBXASC032LFBXASC032Hand
        ->
        Bip001_L_Hand
    """

    name = name.split("|")[-1]

    name = re.sub(
        r"FBXASC032",
        "_",
        name,
        flags=re.IGNORECASE
    )

    name = re.sub(
        r"FBXASC095",
        "_",
        name,
        flags=re.IGNORECASE
    )

    while "__" in name:
        name = name.replace("__", "_")

    return name.strip("_")


def pretty_node_name(node):
    """
    Safe display name for logs.
    Keeps scene nodes untouched.
    Only prettifies the printed output.
    """

    if not node:
        return "None"

    return clean_name(node)


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

def get_auto_transform_nodes():
    """
    Returns Maya auto-generated transform nodes:
        transform1
        transform2
        ...
        transformn
    """

    import re

    result = []

    transforms = cmds.ls(
        type="transform",
        long=False
    ) or []

    for node in transforms:

        if re.match(r"^transform\d+$", node):
            result.append(node)

    return result

def delete_transform_buffer(node):
    """
    Deletes an unwanted transform# buffer.

    If it has children, children are moved to the buffer's parent/world
    while preserving world matrices.
    """

    if not cmds.objExists(node):
        return

    # Avoid deleting transforms with shapes, just in case.
    shapes = cmds.listRelatives(
        node,
        shapes=True,
        fullPath=True
    ) or []

    if shapes:
        cmds.warning(
            "Skipping {} because it has shapes.".format(node)
        )
        return

    parent = cmds.listRelatives(
        node,
        parent=True,
        fullPath=True
    )

    parent = parent[0] if parent else None

    children = cmds.listRelatives(
        node,
        children=True,
        fullPath=True
    ) or []

    # Preserve child world matrices
    child_matrices = {}

    for child in children:
        try:
            child_matrices[child] = cmds.xform(
                child,
                q=True,
                ws=True,
                m=True
            )
        except Exception:
            pass

    # Move children out
    for child in children:

        if not cmds.objExists(child):
            continue

        try:
            if parent:
                new_child = cmds.parent(
                    child,
                    parent,
                    relative=True
                )[0]
            else:
                new_child = cmds.parent(
                    child,
                    world=True,
                    relative=True
                )[0]

            short = new_child.split("|")[-1]

            if child in child_matrices:
                cmds.xform(
                    short,
                    ws=True,
                    m=child_matrices[child]
                )

        except Exception as e:
            cmds.warning(
                "Could not reparent child {} from {}: {}".format(
                    child,
                    node,
                    e
                )
            )

    # Delete the unwanted buffer
    if cmds.objExists(node):
        try:
            cmds.delete(node)
            print("Deleted auto transform buffer: {}".format(node))
        except Exception as e:
            cmds.warning(
                "Could not delete auto transform {}: {}".format(
                    node,
                    e
                )
            )

def cleanup_auto_transform_nodes(before=None):
    """
    Deletes transform# nodes.

    If before is given, only deletes transform# nodes created after that snapshot.
    """

    current = set(get_auto_transform_nodes())

    if before is not None:
        targets = current - set(before)
    else:
        targets = current

    for node in sorted(targets):
        delete_transform_buffer(node)

    return list(targets)

def unlock_transform_attrs(obj):

    attrs = [
        "translateX", "translateY", "translateZ",
        "rotateX", "rotateY", "rotateZ",
        "scaleX", "scaleY", "scaleZ"
    ]

    for attr in attrs:

        plug = obj + "." + attr

        if not cmds.objExists(plug):
            continue

        try:
            cmds.setAttr(plug, lock=False)
            cmds.setAttr(plug, keyable=True)
        except Exception:
            pass


def clear_keys(obj, start, end):

    attrs = [
        "translateX", "translateY", "translateZ",
        "rotateX", "rotateY", "rotateZ"
    ]

    try:
        cmds.cutKey(
            obj,
            time=(start, end),
            attribute=attrs,
            option="keys"
        )
    except Exception:
        pass