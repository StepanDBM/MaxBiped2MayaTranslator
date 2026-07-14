import maya.cmds as cmds
import importlib

from Utilities.Config import bipedConfig
import Utilities.genUtils as genU
import Creators.ctrlAesthetics as ctrlAes
from Creators import createFKctrls

importlib.reload(bipedConfig)
importlib.reload(genU)
importlib.reload(ctrlAes)
importlib.reload(createFKctrls)


def build_known_joint_to_slot_map(char):
    """
    Builds a joint -> slot lookup from scanned/generated character data.

    Includes both resolved names and long DAG names where possible.

    This is important because:
        - scanner slots may store long names
        - later generated slots may store short names
        - Maya parenting can change DAG paths
    """

    result = {}

    skip_keys = [
        "startFrame",
        "endFrame",
        "matrices"
    ]

    for slot, node in char.items():

        if slot in skip_keys:
            continue

        if not node:
            continue

        if not cmds.objExists(node):
            continue

        try:
            resolved = genU.resolve_node(
                node
            )
        except Exception:
            continue

        result[resolved] = slot

        long_names = genU.get_long_names(
            resolved
        )

        for long_name in long_names:
            result[long_name] = slot

    return result


def collect_limb_end_fk_joints(char):
    """
    Collects joints already handled by createLimbEndFKRig.

    This prevents the generic extra FK system from duplicating
    hand/finger controls.
    """

    handled = set()

    if not hasattr(
        bipedConfig,
        "LIMB_END_FK_ROOTS"
    ):
        return handled

    for limb_end_name, data in bipedConfig.LIMB_END_FK_ROOTS.items():

        root_slot = data.get(
            "root_slot"
        )

        include_root = data.get(
            "include_root",
            False
        )

        if not root_slot:
            continue

        root_joint = char.get(
            root_slot
        )

        if not root_joint:
            continue

        if not cmds.objExists(root_joint):
            continue

        try:
            root_joint = genU.resolve_node(
                root_joint
            )
        except Exception:
            continue

        if include_root:
            handled.add(
                root_joint
            )

            for long_name in genU.get_long_names(root_joint):
                handled.add(
                    long_name
                )

        descendants = genU.get_joint_descendants(
            root_joint
        )

        for joint in descendants:
            handled.add(
                joint
            )

            for long_name in genU.get_long_names(joint):
                handled.add(
                    long_name
                )

    return handled


def collect_foot_fkik_end_joints(char):
    """
    Collects joints already handled by the foot FK/IK end system.

    Usually:
        l_toe
        r_toe
    """

    handled = set()

    if not hasattr(
        bipedConfig,
        "FOOT_FKIK_ENDS"
    ):
        return handled

    for foot_end_name, data in bipedConfig.FOOT_FKIK_ENDS.items():

        end_slot = data.get(
            "end_slot"
        )

        if not end_slot:
            continue

        joint = char.get(
            end_slot
        )

        if not joint:
            continue

        if not cmds.objExists(joint):
            continue

        try:
            joint = genU.resolve_node(
                joint
            )
        except Exception:
            continue

        handled.add(
            joint
        )

        for long_name in genU.get_long_names(joint):
            handled.add(
                long_name
            )

    return handled


def make_extra_slot(chain_name, joint):
    """
    Creates a stable internal slot name for an extra joint.
    """

    clean = genU.clean_name(
        joint
    )

    slot = "{}_{}".format(
        chain_name,
        clean
    )

    slot = slot.replace(
        " ",
        "_"
    )

    return slot


def parent_ctrl_ofs_to_group(ctrl_data, group):
    """
    Parents a control offset group under a Maya group.
    """

    if not ctrl_data:
        return

    ofs = ctrl_data.get(
        "ofs"
    )

    if not ofs:
        return

    try:
        cmds.parent(
            genU.resolve_node(ofs),
            group
        )
    except Exception:
        pass


def connect_parent_target_to_child_ofs(
    parent_target,
    child_ofs,
    constraint_base_name
):
    """
    Connects a parent target to a child control offset group.

    Used for:
        base result joint -> first extra ctrl ofs
        parent extra ctrl -> child extra ctrl ofs
    """

    constraints = []

    parent_target = genU.resolve_node(
        parent_target
    )

    child_ofs = genU.resolve_node(
        child_ofs
    )

    pc_name = constraint_base_name + "_parentConstraint"
    sc_name = constraint_base_name + "_scaleConstraint"

    if cmds.objExists(pc_name):
        cmds.delete(pc_name)

    if cmds.objExists(sc_name):
        cmds.delete(sc_name)

    pc = cmds.parentConstraint(
        parent_target,
        child_ofs,
        mo=True,
        n=pc_name
    )[0]

    constraints.append(
        pc
    )

    try:
        sc = cmds.scaleConstraint(
            parent_target,
            child_ofs,
            mo=True,
            n=sc_name
        )[0]

        constraints.append(
            sc
        )

    except Exception:
        pass

    return constraints


def find_extra_chain_roots(char):
    """
    Finds unknown joint chains whose first parent is a known slot/result joint.

    Example:

        Bip001 Head
            Ponytail_01
                Ponytail_02
                Ponytail_03

    The extra chain root is:
        Ponytail_01

    Returns:
        roots:
            [
                {
                    "root_joint": joint,
                    "base_joint": parent known joint,
                    "base_slot": parent slot
                }
            ]

        excluded_joints:
            set of joints already handled elsewhere
    """

    all_joints = genU.get_all_joints()

    known_joint_to_slot = build_known_joint_to_slot_map(
        char
    )

    known_joints = set(
        known_joint_to_slot.keys()
    )

    limb_end_joints = collect_limb_end_fk_joints(
        char
    )

    foot_end_joints = collect_foot_fkik_end_joints(
        char
    )

    excluded_joints = set()
    excluded_joints.update(
        known_joints
    )
    excluded_joints.update(
        limb_end_joints
    )
    excluded_joints.update(
        foot_end_joints
    )

    roots = []

    seen_roots = set()

    for joint in all_joints:

        if joint in excluded_joints:
            continue

        parent = genU.get_parent_joint(
            joint
        )

        if not parent:
            continue

        # The first unknown joint under a known slot/result joint
        # becomes an extra chain root.
        if parent in known_joint_to_slot:

            if joint in seen_roots:
                continue

            seen_roots.add(
                joint
            )

            roots.append(
                {
                    "root_joint": joint,
                    "base_joint": parent,
                    "base_slot": known_joint_to_slot[parent]
                }
            )

    return roots, excluded_joints


def collect_extra_chain_joints(root_joint, excluded_joints):
    """
    Collects root_joint and all its descendants except excluded joints.
    """

    result = []

    if root_joint not in excluded_joints:
        result.append(
            root_joint
        )

    descendants = genU.get_joint_descendants(
        root_joint
    )

    for joint in descendants:

        if joint in excluded_joints:
            continue

        result.append(
            joint
        )

    return result


def connect_extra_fk_behavior(
    rig,
    joint_to_slot,
    base_joint,
    base_slot
):
    """
    Creates FK behavior for one extra chain.

    First extra control:
        base/result joint -> extra root ctrl ofs

    Child extra controls:
        parent extra ctrl -> child extra ctrl ofs
    """

    constraints = []

    for joint, slot in joint_to_slot.items():

        if slot not in rig:
            continue

        child_ofs = rig[slot].get(
            "ofs"
        )

        if not child_ofs:
            continue

        parent_joint = genU.get_parent_joint(
            joint
        )

        if not parent_joint:
            continue

        if parent_joint in joint_to_slot:

            parent_slot = joint_to_slot[parent_joint]

            if parent_slot not in rig:
                continue

            parent_target = rig[parent_slot].get(
                "ctrl"
            )

            if not parent_target:
                continue

            constraint_base_name = "{}_to_{}".format(
                parent_slot,
                slot
            )

        else:

            # This is the first extra joint under the known result/base joint.
            # It follows the actual joint result, not the FK control.
            parent_target = base_joint

            constraint_base_name = "{}_resultJoint_to_{}".format(
                base_slot,
                slot
            )

        constraints.extend(
            connect_parent_target_to_child_ofs(
                parent_target,
                child_ofs,
                constraint_base_name
            )
        )

    return constraints


def create_extra_FK_controls(
    char,
    rig,
    delete_existing=True
):
    """
    Creates basic FK controls for all non-canonical extra joint chains.

    Rules:
        - known scanner slots are ignored
        - hand/finger joints already handled by LIMB_END_FK_ROOTS are ignored
        - foot/toe joints already handled by FOOT_FKIK_ENDS are ignored
        - only chains whose first parent is a known slot/result joint are created

    Behavior:
        base result joint -> first extra ctrl ofs
        parent extra ctrl -> child extra ctrl ofs

    This augments:
        char
        rig

    Then existing pipeline steps can:
        bake extra original animation to extra FK controls
        connect extra FK controls back to original extra joints
        clear original extra joint animation
    """

    auto_transform_snapshot = genU.get_auto_transform_nodes()

    print("=" * 80)
    print("CREATING EXTRA FK CONTROLS")
    print("=" * 80)

    ctrl_grp = genU.ensure_group(
        bipedConfig.MAIN_GROUPS["ctrl"]
    )

    FK_root_grp = genU.ensure_group(
        "FK_ctrls_grp",
        parent=ctrl_grp
    )

    extra_root_grp = genU.ensure_group(
        "extra_FK_ctrls_grp",
        parent=FK_root_grp
    )

    result = {
        "slots": [],
        "controls": {},
        "constraints": [],
        "chains": []
    }

    try:
        roots, excluded_joints = find_extra_chain_roots(
            char
        )

        for index, root_data in enumerate(roots, start=1):

            root_joint = root_data["root_joint"]
            base_joint = root_data["base_joint"]
            base_slot = root_data["base_slot"]

            chain_name = "extra_{:02d}_{}".format(
                index,
                genU.clean_name(root_joint)
            )

            chain_group = genU.ensure_group(
                chain_name + "_FK_ctrls_grp",
                parent=extra_root_grp
            )

            chain_joints = collect_extra_chain_joints(
                root_joint,
                excluded_joints
            )

            if not chain_joints:
                continue

            joint_to_slot = {}

            for joint in chain_joints:

                if not cmds.objExists(joint):
                    continue

                joint = genU.resolve_node(
                    joint
                )

                slot = make_extra_slot(
                    chain_name,
                    joint
                )

                if slot in rig:
                    continue

                # Make dynamic slot available to bake/connect/clear utilities.
                char[slot] = joint

                ctrl_data = createFKctrls.create_ctrl_for_joint(
                    joint,
                    driver_joint=joint,
                    size=4
                )

                rig[slot] = ctrl_data

                parent_ctrl_ofs_to_group(
                    ctrl_data,
                    chain_group
                )

                ctrlAes.color_ctrl_by_slot(
                    ctrl_data["ctrl"],
                    base_slot
                )

                joint_to_slot[joint] = slot

                result["slots"].append(
                    slot
                )

                result["controls"][slot] = ctrl_data

                print(
                    "Created extra FK ctrl: {} -> {}".format(
                        genU.pretty_node_name(joint),
                        ctrl_data["ctrl"]
                    )
                )

            constraints = connect_extra_fk_behavior(
                rig,
                joint_to_slot,
                base_joint,
                base_slot
            )

            result["constraints"].extend(
                constraints
            )

            result["chains"].append(
                {
                    "name": chain_name,
                    "root_joint": root_joint,
                    "base_joint": base_joint,
                    "base_slot": base_slot,
                    "slots": list(joint_to_slot.values())
                }
            )

            print(
                "Created extra FK chain {} under base slot {}.".format(
                    chain_name,
                    base_slot
                )
            )

    finally:
        genU.cleanup_auto_transform_nodes(
            before=auto_transform_snapshot
        )

    print("=" * 80)
    print("EXTRA FK CONTROL CREATION COMPLETE")
    print("Created {} extra FK controls.".format(len(result["slots"])))
    print("=" * 80)

    return result