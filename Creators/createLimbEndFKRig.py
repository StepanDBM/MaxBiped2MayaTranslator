import maya.cmds as cmds
import importlib

from Utilities.Config import bipedConfig
import Utilities.genUtils as genUtils
import Creators.ctrlAesthetics as ctrlAes
from Creators import createFKctrls

importlib.reload(bipedConfig)
importlib.reload(genUtils)
importlib.reload(ctrlAes)
importlib.reload(createFKctrls)


def get_joint_descendants(root_joint, include_root=False):
    """
    Returns joint descendants under root_joint.
    """

    root_joint = genUtils.resolve_node(root_joint)

    result = []

    if include_root:
        result.append(root_joint)

    descendants = cmds.listRelatives(
        root_joint,
        ad=True,
        type="joint",
        fullPath=True
    ) or []

    # Maya returns descendants deepest-first with ad=True.
    # Reverse so parents come before children.
    descendants.reverse()

    result.extend(descendants)

    return result


def make_limb_end_slot(limb_end_name, joint):
    """
    Creates a stable virtual slot name for dynamic limb-end joints.
    """

    clean = genUtils.clean_name(joint)

    slot = "{}_{}".format(limb_end_name, clean)

    slot = slot.replace(" ", "_")

    return slot


def parent_ctrl_ofs_to_group(ctrl_data, group):
    """
    Parents a control offset group under a family group.
    """

    if not ctrl_data:
        return

    ofs = ctrl_data.get("ofs")

    if not ofs:
        return

    try:
        cmds.parent(genUtils.resolve_node(ofs), group)
    except Exception:
        pass


def connect_parent_ctrl_to_child_aut(parent_ctrl, child_aut, name):
    """
    Parent/scale constraints parent ctrl to child ctrl offset.
    """

    constraints = []

    parent_ctrl = genUtils.resolve_node(parent_ctrl)

    child_aut = genUtils.resolve_node(child_aut)

    pc_name = name + "_parentConstraint"
    sc_name = name + "_scaleConstraint"

    if cmds.objExists(pc_name):
        cmds.delete(pc_name)

    if cmds.objExists(sc_name):
        cmds.delete(sc_name)

    pc = cmds.parentConstraint(
        parent_ctrl,
        child_aut,
        mo=True,
        n=pc_name
    )[0]

    constraints.append(pc)

    try:
        sc = cmds.scaleConstraint(
            parent_ctrl,
            child_aut,
            mo=True,
            n=sc_name
        )[0]

        constraints.append(sc)

    except Exception:
        pass

    return constraints


def connect_limb_end_fk_behavior(char, rig, joint_to_slot, root_slot):
    """
    Creates FK hierarchy behavior for dynamic limb-end controls.

    Important rule:

        First-level limb-end controls follow the final/result root joint,
        not the FK root control.

    Example:

        Bip001 L Hand -> first left finger ctrl ofs
        Bip001 R Hand -> first right finger ctrl ofs

    This makes fingers follow the final FK/IK blended wrist result.

    Deeper descendants still follow their parent finger controls:

        index_01_ctrl -> index_02_ctrl_ofs
        index_02_ctrl -> index_03_ctrl_ofs
    """

    constraints = []

    root_result_joint = char.get(
        root_slot
    )

    if not root_result_joint:
        cmds.warning(
            "Cannot connect limb-end FK behavior: missing root result joint for {}".format(
                root_slot
            )
        )
        return constraints

    root_result_joint = genUtils.resolve_node(
        root_result_joint
    )

    for joint, slot in joint_to_slot.items():

        if slot not in rig:
            continue

        parent_joint = cmds.listRelatives(
            genUtils.resolve_node(joint),
            parent=True,
            fullPath=True
        )

        if not parent_joint:
            continue

        parent_joint = parent_joint[0]

        child_aut = rig[slot].get(
            "aut"
        )

        if not child_aut:
            continue

        # --------------------------------------------------
        # Case A:
        # Parent is another dynamic finger joint.
        # Use parent finger FK ctrl.
        # --------------------------------------------------

        if parent_joint in joint_to_slot:

            parent_slot = joint_to_slot[parent_joint]

            if parent_slot not in rig:
                continue

            parent_target = rig[parent_slot].get(
                "ctrl"
            )

            if not parent_target:
                continue

            constraint_name = "{}_to_{}".format(
                parent_slot,
                slot
            )

        # --------------------------------------------------
        # Case B:
        # Parent is the hand/wrist root joint.
        # Use the final/result hand joint, not the FK hand ctrl.
        # --------------------------------------------------

        else:

            parent_target = root_result_joint

            constraint_name = "{}_resultJoint_to_{}".format(
                root_slot,
                slot
            )

        constraints.extend(
            connect_parent_ctrl_to_child_aut(
                parent_target,
                child_aut,
                constraint_name
            )
        )

    return constraints


def create_limb_end_FK_controls(
    char,
    rig,
    delete_existing=True
):
    """
    Creates direct FK controls for limb-end descendant joints.

    Current intended use:
        - fingers / hand joint descendants

    This does NOT:
        - create FK/IK chains
        - create IK handles
        - create FKIK blends

    It directly augments:
        char
        rig
    """

    print("=" * 80)
    print("CREATING LIMB-END FK CONTROLS")
    print("=" * 80)

    ctrl_grp = genUtils.ensure_group(bipedConfig.MAIN_GROUPS["ctrl"])

    FK_root_grp = genUtils.ensure_group("FK_ctrls_grp", parent=ctrl_grp)

    result = {
        "slots": [],
        "controls": {},
        "constraints": []
    }

    for limb_end_name, data in bipedConfig.LIMB_END_FK_ROOTS.items():

        root_slot = data["root_slot"]
        family_group_name = data["family_group"]
        include_root = data.get(
            "include_root",
            False
        )

        root_joint = char.get(root_slot)

        if not root_joint:
            cmds.warning(
                "Skipping {}: missing root slot {}".format(
                    limb_end_name,
                    root_slot
                )
            )
            continue

        if root_slot not in rig:
            cmds.warning(
                "Skipping {}: root slot {} has no FK ctrl in rig.".format(
                    limb_end_name,
                    root_slot
                )
            )
            continue

        family_group = genUtils.ensure_group(
            family_group_name,
            parent=FK_root_grp
        )

        joints = get_joint_descendants(
            root_joint,
            include_root=include_root
        )

        joint_to_slot = {}

        for joint in joints:

            joint = genUtils.resolve_node(joint)

            # Avoid duplicating canonical joints if any were found again.
            if joint in char.values():
                continue

            slot = make_limb_end_slot(limb_end_name, joint)

            if slot in rig:
                continue

            # Make dynamic slot visible to the rest of the pipeline.
            char[slot] = joint

            ctrl_data = createFKctrls.create_ctrl_for_joint(joint, driver_joint=joint, size=3)

            rig[slot] = ctrl_data

            parent_ctrl_ofs_to_group(ctrl_data, family_group)

            ctrlAes.color_ctrl_by_slot(
                ctrl_data["ctrl"],
                root_slot
            )

            joint_to_slot[joint] = slot

            result["slots"].append(slot)

            result["controls"][slot] = ctrl_data

            print(
                "Created limb-end FK ctrl: {} -> {}".format(
                    genUtils.pretty_node_name(joint),
                    ctrl_data["ctrl"]
                )
            )

        constraints = connect_limb_end_fk_behavior(
            char,
            rig,
            joint_to_slot,
            root_slot
        )

        result["constraints"].extend(constraints)

    print("=" * 80)
    print("LIMB-END FK CONTROL CREATION COMPLETE")
    print("Created {} limb-end FK controls.".format(len(result["slots"])))
    print("=" * 80)

    return result