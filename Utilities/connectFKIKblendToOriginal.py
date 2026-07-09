import maya.cmds as cmds
import importlib

import Utilities.genUtils as genUtils
from Utilities.Config import bipedConfig

importlib.reload(genUtils)
importlib.reload(bipedConfig)


# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def unlock_transform_attrs(obj):
    """
    Unlocks transform attrs on original deform joints.
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


def delete_existing_constraints_on_joint(joint):
    """
    Deletes existing constraints connected to a deform joint.
    Useful before connecting FK/IK blend constraints.
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


def add_FKIK_blend_attr(ctrl, attr_name="FKIK_blend", default_value=0.0):
    """
    Adds FKIK_blend attr to a control.

    Convention:
        0 = FK
        1 = IK
    """

    ctrl = genUtils.resolve_node(ctrl)

    if not cmds.attributeQuery(
        attr_name,
        node=ctrl,
        exists=True
    ):
        cmds.addAttr(
            ctrl,
            longName=attr_name,
            attributeType="double",
            min=0.0,
            max=1.0,
            defaultValue=default_value,
            keyable=True
        )

    return ctrl + "." + attr_name


def get_limb_switch_ctrl(limb_name, IK_data):
    """
    Uses the limb IK control as the FK/IK switch holder.
    """

    if limb_name not in IK_data:
        return None

    limb_IK_data = IK_data[limb_name]

    IK_ctrl_data = limb_IK_data.get("IK_ctrl")

    if not IK_ctrl_data:
        return None

    return IK_ctrl_data.get("ctrl")


def create_reverse_node(name, input_attr):
    """
    Creates reverse node for FK weight.
    """

    if cmds.objExists(name):
        cmds.delete(name)

    reverse_node = cmds.createNode(
        "reverse",
        name=name
    )

    cmds.connectAttr(
        input_attr,
        reverse_node + ".inputX",
        force=True
    )

    return reverse_node


# --------------------------------------------------
# MAIN CONNECTION
# --------------------------------------------------

def connect_FKIK_chains_to_original(
    char,
    chain_data,
    IK_data,
    delete_existing=True,
    maintain_offset=False,
    attr_name="FKIK_blend"
):
    """
    Blends FK and IK driver chains into the original deform skeleton.

    Input:
        FK_chain + IK_chain

    Output:
        original deform limb joints

    Blend rule:
        FKIK_blend = 0 -> FK
        FKIK_blend = 1 -> IK
    """

    print("=" * 80)
    print("CONNECTING FK/IK CHAINS TO ORIGINAL DEFORM SKELETON")
    print("=" * 80)

    result = {}

    for limb_name, limb_chain_data in chain_data.items():

        slots = limb_chain_data.get("slots")
        FK_chain = limb_chain_data.get("FK_chain")
        IK_chain = limb_chain_data.get("IK_chain")

        if not slots:
            cmds.warning(
                "Skipping {}: missing slots.".format(limb_name)
            )
            continue

        if not FK_chain:
            cmds.warning(
                "Skipping {}: missing FK_chain.".format(limb_name)
            )
            continue

        if not IK_chain:
            cmds.warning(
                "Skipping {}: missing IK_chain.".format(limb_name)
            )
            continue

        if len(slots) != len(FK_chain) or len(slots) != len(IK_chain):
            cmds.warning(
                "Skipping {}: slot/FK/IK chain length mismatch.".format(
                    limb_name
                )
            )
            continue

        switch_ctrl = get_limb_switch_ctrl(
            limb_name,
            IK_data
        )

        if not switch_ctrl:
            cmds.warning(
                "Skipping {}: missing IK switch ctrl.".format(
                    limb_name
                )
            )
            continue

        switch_ctrl = genUtils.resolve_node(
            switch_ctrl
        )

        blend_attr = add_FKIK_blend_attr(
            switch_ctrl,
            attr_name=attr_name,
            default_value=0.0
        )

        reverse_node = create_reverse_node(
            limb_name + "_FKIK_reverse",
            blend_attr
        )

        limb_constraints = []

        for slot, FK_jnt, IK_jnt in zip(
            slots,
            FK_chain,
            IK_chain
        ):

            original_jnt = char.get(slot)

            if not original_jnt:
                cmds.warning(
                    "Skipping {} {}: missing original joint.".format(
                        limb_name,
                        slot
                    )
                )
                continue

            original_jnt = genUtils.resolve_node(original_jnt)
            FK_jnt = genUtils.resolve_node(FK_jnt)
            IK_jnt = genUtils.resolve_node(IK_jnt)

            unlock_transform_attrs(original_jnt)

            if delete_existing:
                delete_existing_constraints_on_joint(original_jnt)

            constraint_name = "{}_{}_FKIK_parentConstraint".format(
                limb_name,
                slot
            )

            if cmds.objExists(constraint_name):
                cmds.delete(constraint_name)

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

            if len(weights) < 2:
                cmds.warning(
                    "Could not get FK/IK weights for {}".format(
                        constraint
                    )
                )
                continue

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

            limb_constraints.append(constraint)

            print(
                "Connected FK/IK -> original: {} + {} -> {}".format(
                    genUtils.pretty_node_name(FK_jnt),
                    genUtils.pretty_node_name(IK_jnt),
                    genUtils.pretty_node_name(original_jnt)
                )
            )

        result[limb_name] = {
            "switch_ctrl": switch_ctrl,
            "blend_attr": blend_attr,
            "reverse_node": reverse_node,
            "constraints": limb_constraints
        }

    print("=" * 80)
    print("FK/IK CHAIN TO ORIGINAL CONNECTION COMPLETE")
    print("Created FK/IK systems for {} limbs.".format(len(result)))
    print("=" * 80)

    return result