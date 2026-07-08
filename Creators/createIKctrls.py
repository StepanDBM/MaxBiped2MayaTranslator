import maya.cmds as cmds
import importlib
import re

from Utilities.Config import bipedConfig
import Utilities.genUtils as genUtils
import Creators.ctrlAesthetics as ctrlAes
importlib.reload(bipedConfig)


# NAMING HELPERS
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


def resolve_node(node):
    """
    Resolves short names or stale DAG paths.
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


def ensure_group(name, parent=None):

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


# --------------------------------------------------
# VECTOR HELPERS
# --------------------------------------------------

def get_world_pos(obj):

    obj = resolve_node(obj)

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


def calculate_pole_vector_position(start_obj, mid_obj, end_obj, distance_multiplier=1.5):
    """
    Calculates a pole-vector-ish position from a 3-joint chain.

    start = shoulder / thigh
    mid   = elbow / knee
    end   = wrist / foot
    """

    start = get_world_pos(start_obj)
    mid = get_world_pos(mid_obj)
    end = get_world_pos(end_obj)

    start_to_end = vec_sub(end, start)
    start_to_mid = vec_sub(mid, start)

    line_length = vec_length(start_to_end)

    projection_amount = vec_dot(
        start_to_mid,
        start_to_end
    ) / (line_length ** 2)

    projected = vec_add(
        start,
        vec_mul(
            start_to_end,
            projection_amount
        )
    )

    pole_dir = vec_sub(
        mid,
        projected
    )

    if vec_length(pole_dir) < 0.001:
        pole_dir = [0, 0, 1]

    pole_dir = vec_normalize(pole_dir)

    upper_len = vec_length(
        vec_sub(mid, start)
    )

    lower_len = vec_length(
        vec_sub(end, mid)
    )

    pole_distance = (
        upper_len + lower_len
    ) * 0.5 * distance_multiplier

    return vec_add(
        mid,
        vec_mul(
            pole_dir,
            pole_distance
        )
    )


# --------------------------------------------------
# CONTROL CREATION
# --------------------------------------------------

def create_ik_ctrl(name, source_obj, radius=12):

    ctrl_name = name + "_ik_ctrl"
    ofs_name = name + "_ik_ctrl_ofs"
    aut_name = name + "_ik_ctrl_aut"

    ctrl = cmds.circle(
        n=ctrl_name,
        nr=(0, 1, 0),
        r=radius
    )[0]

    ofs = cmds.group(
        em=True,
        n=ofs_name
    )

    aut = cmds.group(
        em=True,
        n=aut_name
    )

    cmds.parent(
        aut,
        ofs
    )

    cmds.parent(
        ctrl,
        aut
    )

    tmp = cmds.parentConstraint(
        source_obj,
        ofs,
        mo=False
    )

    cmds.delete(tmp)

    return {
        "ctrl": ctrl_name,
        "ofs": ofs_name,
        "aut": aut_name
    }


def create_pv_ctrl(name, position, radius=5):

    ctrl_name = name + "_pv_ctrl"
    ofs_name = name + "_pv_ctrl_ofs"
    aut_name = name + "_pv_ctrl_aut"

    ctrl = cmds.circle(
        n=ctrl_name,
        nr=(0, 0, 1),
        r=radius
    )[0]

    ofs = cmds.group(
        em=True,
        n=ofs_name
    )

    aut = cmds.group(
        em=True,
        n=aut_name
    )

    cmds.parent(
        aut,
        ofs
    )

    cmds.parent(
        ctrl,
        aut
    )

    cmds.xform(
        ofs,
        ws=True,
        t=position
    )

    return {
        "ctrl": ctrl_name,
        "ofs": ofs_name,
        "aut": aut_name
    }


# --------------------------------------------------
# COLORING
# --------------------------------------------------

def set_object_color(obj, viewport_rgb=(1, 1, 1), outliner_rgb=None):

    if not cmds.objExists(obj):
        return

    try:
        cmds.setAttr(obj + ".overrideEnabled", 1)
        cmds.setAttr(obj + ".overrideRGBColors", 1)
        cmds.setAttr(
            obj + ".overrideColorRGB",
            viewport_rgb[0],
            viewport_rgb[1],
            viewport_rgb[2]
        )
    except Exception:
        pass

    shapes = cmds.listRelatives(
        obj,
        shapes=True,
        fullPath=True
    ) or []

    for shape in shapes:
        try:
            cmds.setAttr(shape + ".overrideEnabled", 1)
            cmds.setAttr(shape + ".overrideRGBColors", 1)
            cmds.setAttr(
                shape + ".overrideColorRGB",
                viewport_rgb[0],
                viewport_rgb[1],
                viewport_rgb[2]
            )
        except Exception:
            pass

    if outliner_rgb is None:
        outliner_rgb = viewport_rgb

    try:
        cmds.setAttr(obj + ".useOutlinerColor", 1)
        cmds.setAttr(
            obj + ".outlinerColor",
            outliner_rgb[0],
            outliner_rgb[1],
            outliner_rgb[2]
        )
    except Exception:
        pass


def color_ik_ctrl(ctrl, side):

    if side == "l":
        color = (0.1, 0.35, 1.0)

    elif side == "r":
        color = (1.0, 0.15, 0.1)

    else:
        color = (1.0, 0.75, 0.1)

    set_object_color(
        ctrl,
        viewport_rgb=color,
        outliner_rgb=color
    )


# --------------------------------------------------
# MAIN IK CONTROL BUILDER
# --------------------------------------------------

def create_ik_controls(char, rig):
    """
    Creates IK target controls and pole-vector controls.

    This does NOT create IK handles yet.
    This only creates animator-facing IK controls and snaps them
    to the FK/end-joint positions.
    """

    ctrl_grp = genUtils.ensure_group(
        bipedConfig.MAIN_GROUPS["ctrl"]
    )

    ik_root_grp = genUtils.ensure_group(
        bipedConfig.MAIN_GROUPS["ik_ctrls"],
        parent=ctrl_grp
    )

    # --------------------------------------------------
    # CREATE IK FAMILY GROUPS
    # --------------------------------------------------

    groups = {}

    for limb_name, limb_data in bipedConfig.IK_LIMBS.items():

        groups[limb_name] = genUtils.ensure_group(
            limb_data["ik_group"],
            parent=ik_root_grp
        )

    # --------------------------------------------------
    # CREATE IK CONTROLS
    # --------------------------------------------------

    ik_data = {}

    for limb_name, limb_data in bipedConfig.IK_LIMBS.items():

        side = limb_data["side"]

        start_slot = limb_data["start"]
        mid_slot = limb_data["mid"]
        end_slot = limb_data["end"]

        ctrl_base_name = limb_data["name"]

        # Validate needed slots exist in rig
        if start_slot not in rig:
            cmds.warning(
                "Skipping {}: missing start slot in rig: {}".format(
                    limb_name,
                    start_slot
                )
            )
            continue

        if mid_slot not in rig:
            cmds.warning(
                "Skipping {}: missing mid slot in rig: {}".format(
                    limb_name,
                    mid_slot
                )
            )
            continue

        if end_slot not in rig:
            cmds.warning(
                "Skipping {}: missing end slot in rig: {}".format(
                    limb_name,
                    end_slot
                )
            )
            continue

        # FK end ctrl is used as the initial IK ctrl position/orientation
        end_fk_ctrl = genUtils.resolve_node(
            rig[end_slot]["ctrl"]
        )

        start_joint = rig[start_slot]["joint"]
        mid_joint = rig[mid_slot]["joint"]
        end_joint = rig[end_slot]["joint"]

        # --------------------------------------------------
        # CREATE IK END CONTROL
        # --------------------------------------------------

        ik_ctrl_data = create_ik_ctrl(
            ctrl_base_name,
            end_fk_ctrl,
            radius=12
        )

        # --------------------------------------------------
        # CREATE POLE VECTOR CONTROL
        # --------------------------------------------------

        pv_position = calculate_pole_vector_position(
            start_joint,
            mid_joint,
            end_joint
        )

        pv_ctrl_data = create_pv_ctrl(
            ctrl_base_name,
            pv_position,
            radius=5
        )

        # --------------------------------------------------
        # GROUP CONTROLS
        # --------------------------------------------------

        limb_grp = groups[limb_name]

        try:
            cmds.parent(
                genUtils.resolve_node(ik_ctrl_data["ofs"]),
                limb_grp
            )
        except Exception as e:
            cmds.warning(
                "Could not parent IK ctrl ofs for {}: {}".format(
                    limb_name,
                    e
                )
            )

        try:
            cmds.parent(
                genUtils.resolve_node(pv_ctrl_data["ofs"]),
                limb_grp
            )
        except Exception as e:
            cmds.warning(
                "Could not parent PV ctrl ofs for {}: {}".format(
                    limb_name,
                    e
                )
            )

        # --------------------------------------------------
        # COLOR CONTROLS
        # --------------------------------------------------

        ctrlAes.color_ctrl_by_slot(
            ik_ctrl_data["ctrl"],
            side + "_ik"
        )

        ctrlAes.color_ctrl_by_slot(
            pv_ctrl_data["ctrl"],
            side + "_ik"
        )

        # --------------------------------------------------
        # STORE DATA
        # --------------------------------------------------

        ik_data[limb_name] = {
            "side": side,

            "start": start_slot,
            "mid": mid_slot,
            "end": end_slot,

            "start_joint": start_joint,
            "mid_joint": mid_joint,
            "end_joint": end_joint,

            "ik_ctrl": ik_ctrl_data,
            "pv_ctrl": pv_ctrl_data,

            "group": limb_grp
        }

    print(
        "Created {} IK control sets.".format(
            len(ik_data)
        )
    )

    return ik_data