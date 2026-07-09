import maya.cmds as cmds
import importlib

from Utilities.Config import bipedConfig
import Utilities.genUtils as genUtils
import Utilities.vectorMath as vMath
import Creators.ctrlAesthetics as ctrlAes

importlib.reload(bipedConfig)
importlib.reload(genUtils)
importlib.reload(vMath)
importlib.reload(ctrlAes)


def calculate_pole_vector_position(start_obj, mid_obj, end_obj, distance_multiplier=1.5):
    """
    Calculates a pole-vector-ish position from a 3-joint chain.

    start = shoulder / thigh
    mid   = elbow / knee
    end   = wrist / foot
    """

    start = vMath.get_world_pos(start_obj)
    mid = vMath.get_world_pos(mid_obj)
    end = vMath.get_world_pos(end_obj)

    start_to_end = vMath.vec_sub(end, start)
    start_to_mid = vMath.vec_sub(mid, start)

    line_length = vMath.vec_length(start_to_end)

    projection_amount = vMath.vec_dot(
        start_to_mid,
        start_to_end
    ) / (line_length ** 2)

    projected = vMath.vec_add(
        start,
        vMath.vec_mul(
            start_to_end,
            projection_amount
        )
    )

    pole_dir = vMath.vec_sub(
        mid,
        projected
    )

    if vMath.vec_length(pole_dir) < 0.001:
        pole_dir = [0, 0, 1]

    pole_dir = vMath.vec_normalize(pole_dir)

    upper_len = vMath.vec_length(
        vMath.vec_sub(mid, start)
    )

    lower_len = vMath.vec_length(
        vMath.vec_sub(end, mid)
    )

    pole_distance = (
        upper_len + lower_len
    ) * 0.5 * distance_multiplier

    return vMath.vec_add(
        mid,
        vMath.vec_mul(
            pole_dir,
            pole_distance
        )
    )


# CONTROL CREATION

def create_IK_ctrl(name, source_obj, radius=12):

    ctrl_name = name + "_IK_ctrl"
    ofs_name = name + "_IK_ctrl_ofs"
    aut_name = name + "_IK_ctrl_aut"

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


# COLORING
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


def color_IK_ctrl(ctrl, side):

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


# MAIN IK CONTROL BUILDER
def create_IK_controls(char, rig):
    """
    Creates IK target controls and pole-vector controls.

    This does NOT create IK handles yet.
    This only creates animator-facing IK controls and snaps them
    to the FK/end-joint positions.
    """

    ctrl_grp = genUtils.ensure_group(
        bipedConfig.MAIN_GROUPS["ctrl"]
    )

    IK_root_grp = genUtils.ensure_group(
        bipedConfig.MAIN_GROUPS["IK_ctrls"],
        parent=ctrl_grp
    )

    # CREATE IK FAMILY GROUPS
    groups = {}

    for limb_name, limb_data in bipedConfig.IK_LIMBS.items():

        groups[limb_name] = genUtils.ensure_group(
            limb_data["IK_group"],
            parent=IK_root_grp
        )

    # CREATE IK CONTROLS
    IK_data = {}

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

        # CREATE IK END CONTROL
        IK_ctrl_data = create_IK_ctrl(
            ctrl_base_name,
            end_fk_ctrl,
            radius=12
        )

        # CREATE POLE VECTOR CONTROL
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

        # GROUP CONTROLS
        limb_grp = groups[limb_name]

        try:
            cmds.parent(
                genUtils.resolve_node(IK_ctrl_data["ofs"]),
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

        # COLOR CONTROLS
        ctrlAes.color_ctrl_by_slot(
            IK_ctrl_data["ctrl"],
            side + "_IK"
        )

        ctrlAes.color_ctrl_by_slot(
            pv_ctrl_data["ctrl"],
            side + "_IK"
        )

        # STORE DATA
        IK_data[limb_name] = {
            "side": side,

            "start": start_slot,
            "mid": mid_slot,
            "end": end_slot,

            "start_joint": start_joint,
            "mid_joint": mid_joint,
            "end_joint": end_joint,

            "IK_ctrl": IK_ctrl_data,
            "pv_ctrl": pv_ctrl_data,

            "group": limb_grp
        }

    print(
        "Created {} IK control sets.".format(
            len(IK_data)
        )
    )

    return IK_data