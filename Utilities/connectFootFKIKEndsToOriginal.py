import maya.cmds as cmds
import importlib

import Utilities.genUtils as genUtils
from Utilities.Config import bipedConfig

importlib.reload(genUtils)
importlib.reload(bipedConfig)


def delete_existing_constraints_on_joint(joint):
    """
    Deletes existing constraints connected to a deform joint.
    """

    constraint_types = [
        "parentConstraint",
        "orientConstraint",
        "pointConstraint",
        "scaleConstraint"
    ]

    for ctype in constraint_types:

        constraints = cmds.listConnections(
            joint,
            source=True,
            destination=False,
            type=ctype
        ) or []

        for constraint in constraints:
            if cmds.objExists(constraint):
                try:
                    cmds.delete(constraint)
                except Exception:
                    pass

def connect_foot_end_visibility(
    slot,
    rig,
    reverse_node
):
    """
    Connects toe/foot-end FK control visibility to the parent leg FKIK switch.

    FKIK_blend = 0:
        FK toe visible

    FKIK_blend = 1:
        FK toe hidden
    """

    if slot not in rig:
        return

    ctrl = rig[slot].get("ctrl")

    if not ctrl:
        return

    ctrl = genUtils.resolve_node(ctrl)

    try:
        cmds.connectAttr(
            reverse_node + ".outputX",
            ctrl + ".visibility",
            force=True
        )
    except Exception as e:
        cmds.warning(
            "Could not connect foot-end FK visibility for {}: {}".format(
                ctrl,
                e
            )
        )

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


def connect_foot_FKIK_ends_to_original(
    char,
    rig,
    chain_data,
    FKIK_blend_connections,
    delete_existing=True,
    maintain_offset=False
):
    """
    Blends FK/IK foot-end driver joints into original toe joints.

    Uses the parent leg FKIK blend attr.
    """

    print("=" * 80)
    print("CONNECTING FOOT-END FK/IK TO ORIGINAL TOE JOINTS")
    print("=" * 80)

    result = {}

    for foot_end_name, data in chain_data.items():

        if data.get("system_type") != "foot_end":
            continue

        parent_limb = data["parent_limb"]

        if parent_limb not in FKIK_blend_connections:
            cmds.warning(
                "Skipping {}: missing FKIK blend data for parent limb {}".format(
                    foot_end_name,
                    parent_limb
                )
            )
            continue

        parent_blend_data = FKIK_blend_connections[parent_limb]

        blend_attr = parent_blend_data.get("blend_attr")
        reverse_node = parent_blend_data.get("reverse_node")

        if not blend_attr or not reverse_node:
            cmds.warning(
                "Skipping {}: missing parent blend attr or reverse node.".format(
                    foot_end_name
                )
            )
            continue

        slots = data["slots"]
        FK_chain = data["FK_chain"]
        IK_chain = data["IK_chain"]

        constraints = []

        for slot, FK_jnt, IK_jnt in zip(
            slots,
            FK_chain,
            IK_chain
        ):

            original_jnt = char.get(slot)

            if not original_jnt:
                cmds.warning(
                    "Skipping {} {}: missing original joint.".format(
                        foot_end_name,
                        slot
                    )
                )
                continue

            original_jnt = genUtils.resolve_node(original_jnt)
            FK_jnt = genUtils.resolve_node(FK_jnt)
            IK_jnt = genUtils.resolve_node(IK_jnt)

            unlock_transform_attrs(original_jnt)

            constraint_name = "{}_{}_FKIK_parentConstraint".format(
                foot_end_name,
                slot
            )

            if delete_existing:
                delete_existing_constraints_on_joint(
                    original_jnt
                )

            constraint = cmds.parentConstraint(
                FK_jnt,
                IK_jnt,
                original_jnt,
                maintainOffset=maintain_offset,
                name=constraint_name
            )[0]

            weights = cmds.parentConstraint(
                constraint,
                query=True,
                weightAliasList=True
            )

            FK_weight = weights[0]
            IK_weight = weights[1]

            cmds.connectAttr(
                reverse_node + ".outputX",
                constraint + "." + FK_weight,
                force=True
            )

            cmds.connectAttr(
                blend_attr,
                constraint + "." + IK_weight,
                force=True
            )

            connect_foot_end_visibility(
                slot,
                rig,
                reverse_node
            )

            constraints.append(constraint)

            print(
                "Connected foot-end FK/IK -> original: {} + {} -> {}".format(
                    genUtils.pretty_node_name(FK_jnt),
                    genUtils.pretty_node_name(IK_jnt),
                    genUtils.pretty_node_name(original_jnt)
                )
            )

        result[foot_end_name] = {
            "parent_limb": parent_limb,
            "blend_attr": blend_attr,
            "reverse_node": reverse_node,
            "constraints": constraints
        }

    print("=" * 80)
    print("FOOT-END FK/IK TO ORIGINAL CONNECTION COMPLETE")
    print("Created {} foot-end blend systems.".format(len(result)))
    print("=" * 80)

    return result