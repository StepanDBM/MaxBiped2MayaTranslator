import maya.cmds as cmds
import importlib

import Utilities.genUtils as genUtils
from Utilities.Config import bipedConfig
importlib.reload(genUtils)
importlib.reload(bipedConfig)

# HELPERS
def connect_IK_chain_base_to_parent(
    limb_name,
    IK_root,
    rig,
    maintain_offset=True
):
    """
    Makes the base/root of the IK chain follow the appropriate core FK control.

    Example:
        l_arm IK root follows l_clavicle FK ctrl
        l_leg IK root follows pelvis FK ctrl
    """

    if limb_name not in bipedConfig.IK_BASE_PARENT_SLOTS:
        cmds.warning(
            "No IK base parent slot configured for {}".format(
                limb_name
            )
        )
        return None

    parent_slot = bipedConfig.IK_BASE_PARENT_SLOTS[limb_name]

    if parent_slot not in rig:
        cmds.warning(
            "Cannot connect IK base for {}: missing parent slot {}".format(
                limb_name,
                parent_slot
            )
        )
        return None

    parent_ctrl = rig[parent_slot].get("ctrl")

    if not parent_ctrl:
        cmds.warning(
            "Cannot connect IK base for {}: missing parent ctrl for {}".format(
                limb_name,
                parent_slot
            )
        )
        return None

    parent_ctrl = genUtils.resolve_node(parent_ctrl)
    IK_root = genUtils.resolve_node(IK_root)

    constraint_name = limb_name + "_IK_base_parentConstraint"

    if cmds.objExists(constraint_name):
        cmds.delete(constraint_name)

    constraint = cmds.parentConstraint(
        parent_ctrl,
        IK_root,
        mo=maintain_offset,
        n=constraint_name
    )[0]

    print(
        "Connected IK chain base -> parent ctrl: {} -> {}".format(
            genUtils.pretty_node_name(parent_ctrl),
            genUtils.pretty_node_name(IK_root)
        )
    )

    return constraint

def set_joint_preferred_angle(joint, angles):
    """
    Sets preferred angle attributes directly on a joint.

    angles:
        (x, y, z)
    """

    joint = genUtils.resolve_node(joint)

    attrs = [
        "preferredAngleX",
        "preferredAngleY",
        "preferredAngleZ"
    ]

    for attr, value in zip(attrs, angles):

        plug = joint + "." + attr

        if not cmds.objExists(plug):
            continue

        try:
            cmds.setAttr(plug, value)
        except Exception as e:
            cmds.warning(
                "Could not set {} to {}: {}".format(
                    plug,
                    value,
                    e
                )
            )
def apply_IK_preferred_angle(limb_name, IK_chain):
    """
    Applies preferred angle to the mid joint of an IK chain.

    Expected IK_chain:
        [upper/thigh, forearm/calf, hand/foot]
    """

    if limb_name not in bipedConfig.IK_PREFERRED_ANGLES:
        cmds.warning(
            "No IK preferred angle config found for {}".format(
                limb_name
            )
        )
        return

    data = bipedConfig.IK_PREFERRED_ANGLES[limb_name]

    angles = data.get("angles", (0, 0, 0))

    if len(IK_chain) < 3:
        cmds.warning(
            "Cannot set preferred angle for {}: IK chain too short.".format(
                limb_name
            )
        )
        return

    mid_joint = genUtils.resolve_node(IK_chain[1])

    set_joint_preferred_angle(mid_joint, angles)

    print(
        "Set IK preferred angle: {} -> {}".format(
            genUtils.pretty_node_name(mid_joint),
            angles
        )
    )

def ensure_group(name, parent=None):
    """
    Creates a group if missing.
    Parents it if parent is provided.
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
            except Exception as e:
                cmds.warning(
                    "Could not parent {} under {}: {}".format(
                        grp,
                        parent,
                        e
                    )
                )

    return grp


def delete_existing_node(node):
    """
    Deletes node if it exists.
    """

    if cmds.objExists(node):
        try:
            cmds.delete(node)
        except Exception as e:
            cmds.warning(
                "Could not delete {}: {}".format(
                    node,
                    e
                )
            )


def unlock_transform_attrs(obj):
    """
    Unlocks common transform attrs.
    """

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


def get_IK_ctrl_from_data(limb_IK_data):
    """
    Extracts IK ctrl from IK data.

    Supports:
        limb_IK_data["IK_ctrl"]["ctrl"]
        limb_IK_data["IK_ctrl"]["ctrl"]
    """

    IK_ctrl_data = limb_IK_data["IK_ctrl"]

    if not IK_ctrl_data:
        return None

    return IK_ctrl_data.get("ctrl")


def get_pv_ctrl_from_data(limb_IK_data):
    """
    Extracts pole vector ctrl from IK data.
    """

    pv_ctrl_data = limb_IK_data["pv_ctrl"]

    if not pv_ctrl_data:
        return None

    return pv_ctrl_data.get("ctrl")


# MAIN CONNECTION
def connect_IK_controls_to_IK_chains(
    IK_data,
    chain_data,
    rig,
    delete_existing=True,
    maintain_offset=False
):
    """
    Connects IK controls to IK driver chains.

    This creates:
        - IK handle on every IK chain
        - parentConstraint from IK ctrl to IK handle
        - poleVectorConstraint from PV ctrl to IK handle
        - orientConstraint from IK ctrl to IK chain end joint

    This does NOT:
        - connect anything to the original deform skeleton
        - blend FK/IK
        - delete original joint animation

    Expected input:
        IK_data[limb_name]["IK_ctrl" or "IK_ctrl"]["ctrl"]
        IK_data[limb_name]["pv_ctrl"]["ctrl"]

        chain_data[limb_name]["IK_chain"]
    """

    print("=" * 80)
    print("CONNECTING IK CONTROLS TO IK DRIVER CHAINS")
    print("=" * 80)

    rig_grp = ensure_group(
        "rig_grp"
    )

    IK_systems_grp = ensure_group(
        "IK_systems_grp",
        parent=rig_grp
    )

    result = {}

    for limb_name, limb_chain_data in chain_data.items():

        if limb_name not in IK_data:
            cmds.warning(
                "Skipping {}: no IK control data found.".format(
                    limb_name
                )
            )
            continue

        limb_IK_data = IK_data[limb_name]

        IK_chain = limb_chain_data.get("IK_chain")

        if not IK_chain or len(IK_chain) < 3:
            cmds.warning(
                "Skipping {}: IK chain missing or too short.".format(
                    limb_name
                )
            )
            continue

        IK_ctrl = get_IK_ctrl_from_data(
            limb_IK_data
        )

        pv_ctrl = get_pv_ctrl_from_data(
            limb_IK_data
        )

        if not IK_ctrl:
            cmds.warning(
                "Skipping {}: missing IK ctrl.".format(
                    limb_name
                )
            )
            continue

        if not pv_ctrl:
            cmds.warning(
                "Skipping {}: missing PV ctrl.".format(
                    limb_name
                )
            )
            continue

        IK_root = genUtils.resolve_node(IK_chain[0])
        IK_mid = genUtils.resolve_node(IK_chain[1])
        IK_end = genUtils.resolve_node(IK_chain[-1])
        IK_ctrl = genUtils.resolve_node(IK_ctrl)
        pv_ctrl = genUtils.resolve_node(pv_ctrl)
        unlock_transform_attrs(IK_root)
        unlock_transform_attrs(IK_mid)
        unlock_transform_attrs(IK_end)

        IK_base_constraint = connect_IK_chain_base_to_parent(
            limb_name,
            IK_root,
            rig,
            maintain_offset=True
        )

        limb_system_grp = ensure_group(
            limb_name + "_IK_system_grp",
            parent=IK_systems_grp
        )

        IKh_name = limb_name + "_IK_IKh"
        eff_name = limb_name + "_IK_eff"

        IK_parent_constraint_name = (
            limb_name + "_IK_ctrl_to_IK_handle_parentConstraint"
        )

        pv_constraint_name = (
            limb_name + "_pv_ctrl_to_IK_handle_poleVectorConstraint"
        )

        end_orient_constraint_name = (
            limb_name + "_IK_ctrl_to_IK_end_orientConstraint"
        )

        if delete_existing:
            delete_existing_node(IKh_name)
            delete_existing_node(eff_name)
            delete_existing_node(IK_parent_constraint_name)
            delete_existing_node(pv_constraint_name)
            delete_existing_node(end_orient_constraint_name)

            # APPLY PREFERRED ANGLE BEFORE CREATING IK HANDLE
            apply_IK_preferred_angle(limb_name,IK_chain)

            # CREATE IK HANDLE
            IKh, effector = cmds.ikHandle(
                sj=IK_root,
                ee=IK_end,
                sol="ikRPsolver",
                n=IKh_name
            )

        try:
            effector = cmds.rename(effector, eff_name)
        except Exception:
            pass

        try:
            IKh = cmds.parent(IKh, limb_system_grp)[0]
        except Exception:
            pass

        # IK CTRL DRIVES IK HANDLE
        IK_parent_constraint = cmds.parentConstraint(
            IK_ctrl,
            IKh,
            mo=maintain_offset,
            n=IK_parent_constraint_name
        )[0]

        # PV CTRL DRIVES POLE VECTOR
        pv_constraint = cmds.poleVectorConstraint(
            pv_ctrl,
            IKh,
            n=pv_constraint_name
        )[0]

        # IK CTRL ORIENTS END JOINT
        end_orient_constraint = cmds.orientConstraint(
            IK_ctrl,
            IK_end,
            mo=maintain_offset,
            n=end_orient_constraint_name
        )[0]

        result[limb_name] = {
            "IK_handle": IKh,
            "effector": effector,
            "IK_parent_constraint": IK_parent_constraint,
            "pv_constraint": pv_constraint,
            "end_orient_constraint": end_orient_constraint,
            "IK_base_constraint": IK_base_constraint,
            "IK_ctrl": IK_ctrl,
            "pv_ctrl": pv_ctrl,
            "IK_chain": IK_chain,
            "group": limb_system_grp
        }

        print("Connected IK ctrl -> IK chain: {} -> {} / {}".format(
                genUtils.pretty_node_name(IK_ctrl),
                genUtils.pretty_node_name(IK_root),
                genUtils.pretty_node_name(IK_end)
            )
        )

        print("Connected PV ctrl -> IK handle: {} -> {}".format(
                genUtils.pretty_node_name(pv_ctrl),
                genUtils.pretty_node_name(IKh)
            )
        )

    print("=" * 80)
    print("IK CONTROL TO IK CHAIN CONNECTION COMPLETE")
    print("Created {} IK systems.".format(len(result)))
    print("=" * 80)

    return result