import maya.cmds as cmds
import importlib

import Utilities.genUtils as genUtils
from Utilities.Config import bipedConfig
from Creators import ctrlAesthetics as ctrlAes

importlib.reload(genUtils)
importlib.reload(bipedConfig)
importlib.reload(ctrlAes)


def get_FKIK_switch_offset(limb_name):
    """
    Returns world-space offset for FKIK switch control placement.

    Arms:
        move upward

    Legs:
        move outward from center
    """

    # Hands / arms: place above wrist/hand
    if "arm" in limb_name:
        return [0, 15, 0]

    # Left leg: move outward to character left
    if limb_name.startswith("l_") and "leg" in limb_name:
        return [15, 0, 0]

    # Right leg: move outward to character right
    if limb_name.startswith("r_") and "leg" in limb_name:
        return [-15, 0, 0]

    # Fallback
    return [0, 15, 0]
def create_FKIK_switch_ctrl(limb_name, char, slots, radius=6):
    """
    Creates a green circular FKIK switch controller for one limb.

    The control is placed near the limb end joint.
    """

    end_slot = slots[-1]
    end_joint = char.get(end_slot)

    if not end_joint:
        cmds.warning(
            "Could not create FKIK switch ctrl for {}: missing end joint.".format(
                limb_name
            )
        )
        return None

    end_joint = genUtils.resolve_node(end_joint)

    ctrl_name = limb_name + "_FKIK_ctrl"
    ofs_name = limb_name + "_FKIK_ctrl_ofs"
    aut_name = limb_name + "_FKIK_ctrl_aut"

    if cmds.objExists(ofs_name):
        cmds.delete(ofs_name)

    if cmds.objExists(ctrl_name):
        cmds.delete(ctrl_name)

    ctrl = cmds.circle(
        n=ctrl_name,
        nr=(0, 1, 0),
        r=radius
    )[0]

    ofs = cmds.group(em=True, n=ofs_name)

    aut = cmds.group(em=True, n=aut_name)

    aut = cmds.parent(aut, ofs)[0]

    ctrl = cmds.parent(ctrl, aut)[0]

    # Snap to end joint
    tmp = cmds.parentConstraint(
        end_joint,
        ofs,
        mo=False
    )

    cmds.delete(tmp)

    # Offset slightly upward
    current_pos = cmds.xform(
        ofs,
        q=True,
        ws=True,
        t=True
    )
    offset = get_FKIK_switch_offset(limb_name)

    cmds.xform(
        ofs,
        ws=True,
        t=[
            current_pos[0] + offset[0],
            current_pos[1] + offset[1],
            current_pos[2] + offset[2]
        ]
    )

    ctrl_grp = genUtils.ensure_group(
        bipedConfig.MAIN_GROUPS["ctrl"]
    )

    FKIK_ctrls_grp = genUtils.ensure_group(
        "FKIK_ctrls_grp",
        parent=ctrl_grp
    )

    try:
        cmds.parent(ofs, FKIK_ctrls_grp)
    except Exception:
        pass

    # Green FKIK switch color
    ctrlAes.set_object_color(
        ctrl,
        viewport_rgb=(0.0, 1.0, 0.2),
        outliner_rgb=(0.0, 1.0, 0.2)
    )

    return {
        "ctrl": ctrl_name,
        "ofs": ofs_name,
        "aut": aut_name
    }

def connect_visibility_to_FKIK(
    limb_name,
    rig,
    IK_data,
    slots,
    blend_attr,
    reverse_node
):
    """
    Connects FKIK blend to FK and IK visibility.

    FKIK_blend = 0:
        FK visible
        IK hidden

    FKIK_blend = 1:
        FK hidden
        IK visible
    """

    # FK controls visibility = reverse.outputX
    for slot in slots:

        if slot not in rig:
            continue

        FK_ctrl = rig[slot].get("ctrl")

        if not FK_ctrl:
            continue

        FK_ctrl = genUtils.resolve_node(FK_ctrl)

        try:
            cmds.connectAttr(
                reverse_node + ".outputX",
                FK_ctrl + ".visibility",
                force=True
            )
        except Exception as e:
            cmds.warning(
                "Could not connect FK visibility for {}: {}".format(
                    FK_ctrl,
                    e
                )
            )

    # IK controls visibility = FKIK_blend
    if limb_name not in IK_data:
        return

    limb_IK_data = IK_data[limb_name]

    IK_ctrl_data = limb_IK_data.get("IK_ctrl")
    pv_ctrl_data = limb_IK_data.get("pv_ctrl")

    IK_ctrls = []

    if IK_ctrl_data and IK_ctrl_data.get("ctrl"):
        IK_ctrls.append(IK_ctrl_data["ctrl"])

    if pv_ctrl_data and pv_ctrl_data.get("ctrl"):
        IK_ctrls.append(pv_ctrl_data["ctrl"])

    for IK_ctrl in IK_ctrls:

        IK_ctrl = genUtils.resolve_node(IK_ctrl)

        try:
            cmds.connectAttr(
                blend_attr,
                IK_ctrl + ".visibility",
                force=True
            )
        except Exception as e:
            cmds.warning(
                "Could not connect IK visibility for {}: {}".format(
                    IK_ctrl,
                    e
                )
            )

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


def get_limb_switch_ctrl(limb_name, char, slots):
    """
    Creates and returns the dedicated FKIK switch control.
    """

    switch_data = create_FKIK_switch_ctrl(
        limb_name,
        char,
        slots
    )

    if not switch_data:
        return None, None

    return switch_data


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


# MAIN CONNECTION

def connect_FKIK_chains_to_original(
    char,
    chain_data,
    IK_data,
    rig,
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

        switch_ctrl_data = get_limb_switch_ctrl(
            limb_name,
            char,
            slots
        )
        switch_ctrl = switch_ctrl_data["ctrl"]
        if not switch_ctrl:
            cmds.warning(
                "Skipping {}: could not create FKIK switch ctrl.".format(
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
        connect_visibility_to_FKIK(
            limb_name,
            rig,
            IK_data,
            slots,
            blend_attr,
            reverse_node
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
            "switch_ctrl_data": switch_ctrl_data,
            "blend_attr": blend_attr,
            "reverse_node": reverse_node,
            "constraints": limb_constraints
        }

    print("=" * 80)
    print("FK/IK CHAIN BLEND TO ORIGINAL CONNECTION COMPLETE")
    print("Created FK/IK systems for {} limbs.".format(len(result)))
    print("=" * 80)

    return result