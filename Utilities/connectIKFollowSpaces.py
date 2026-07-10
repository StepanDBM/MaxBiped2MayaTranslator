import maya.cmds as cmds
import importlib

import Utilities.genUtils as genUtils
from Utilities.Config import bipedConfig

importlib.reload(genUtils)
importlib.reload(bipedConfig)


def add_follow_attr(switch_ctrl, enum_labels, attr_name="follow"):
    """
    Adds enum follow attr to FKIK switch ctrl.

    Example:
        None:Main:COG:Clavicle
    """

    switch_ctrl = genUtils.resolve_node(switch_ctrl)

    enum_string = ":".join(enum_labels)

    if not cmds.attributeQuery(
        attr_name,
        node=switch_ctrl,
        exists=True
    ):
        cmds.addAttr(
            switch_ctrl,
            longName=attr_name,
            attributeType="enum",
            enumName=enum_string,
            keyable=True
        )

    return switch_ctrl + "." + attr_name


def create_follow_remapColor(limb_name, follow_attr, follow_order):
    """
    Creates a remapColor node that converts the follow enum into
    one-hot RGB outputs.

    Convention:
        0 = None      -> R=0 G=0 B=0
        1 = Main      -> R=1 G=0 B=0
        2 = COG       -> R=0 G=1 B=0
        3 = Clavicle  -> R=0 G=0 B=1

    The enum value is connected into:
        remapColor.colorR
        remapColor.colorG
        remapColor.colorB

    Outputs:
        outColorR -> first follow target
        outColorG -> second follow target
        outColorB -> third follow target
    """

    node_name = limb_name + "_IK_follow_remapColor"

    if cmds.objExists(node_name):
        cmds.delete(node_name)

    remap = cmds.createNode("remapColor", name=node_name)

    max_index = max(len(follow_order) - 1,1)

    # Map enum range into ramp range.
    cmds.setAttr(remap + ".inputMin",0)

    cmds.setAttr(remap + ".inputMax",max_index)

    # Usually keep outputMin/outputMax at 0/1.
    cmds.setAttr(remap + ".outputMin",0)

    cmds.setAttr(remap + ".outputMax",1)

    # Connect same enum value into R/G/B ramp inputs.
    for channel in [
        "colorR",
        "colorG",
        "colorB"
    ]:
        try:
            cmds.connectAttr(
                follow_attr,
                remap + "." + channel,
                force=True
            )
        except Exception as e:
            cmds.warning(
                "Could not connect {} -> {}.{}: {}".format(
                    follow_attr,
                    remap,
                    channel,
                    e
                )
            )

    # Helper to set one ramp channel

    def set_channel_ramp(channel_name, values):
        """
        channel_name:
            red / green / blue

        values:
            list of values per enum index.
        """

        attr_prefix = channel_name

        for index, value in enumerate(values):

            position = float(index) / float(max_index)

            try:
                cmds.setAttr(
                    "{}.{}[{}].{}_Position".format(
                        remap,
                        attr_prefix,
                        index,
                        attr_prefix
                    ),
                    position
                )

                cmds.setAttr(
                    "{}.{}[{}].{}_FloatValue".format(
                        remap,
                        attr_prefix,
                        index,
                        attr_prefix
                    ),
                    value
                )

                # 0 = None / linear-ish depending on Maya,
                # but because we place exact enum values, this works.
                # If interpolation causes blends between enum values,
                # change to 1/constant if your Maya version uses that.
                cmds.setAttr(
                    "{}.{}[{}].{}_Interp".format(
                        remap,
                        attr_prefix,
                        index,
                        attr_prefix
                    ),
                    0
                )

            except Exception as e:
                cmds.warning(
                    "Could not set {} ramp index {} on {}: {}".format(
                        channel_name,
                        index,
                        remap,
                        e
                    )
                )

    # Build per-channel one-hot values

    red_values = []
    green_values = []
    blue_values = []

    for index, item in enumerate(follow_order):

        # 0 = None
        if index == 0:
            red_values.append(0)
            green_values.append(0)
            blue_values.append(0)

        # 1 = Main
        elif index == 1:
            red_values.append(1)
            green_values.append(0)
            blue_values.append(0)

        # 2 = COG
        elif index == 2:
            red_values.append(0)
            green_values.append(1)
            blue_values.append(0)

        # 3 = Clavicle / extra
        elif index == 3:
            red_values.append(0)
            green_values.append(0)
            blue_values.append(1)

        else:
            cmds.warning(
                "{} has more than 3 follow targets. remapColor RGB supports only 3 target weights.".format(
                    limb_name
                )
            )

            red_values.append(0)
            green_values.append(0)
            blue_values.append(0)

    set_channel_ramp("red",red_values)
    set_channel_ramp("green",green_values)
    set_channel_ramp("blue",blue_values)

    return remap


def get_follow_target_ctrls(limb_name, rig):
    """
    Resolves follow target controls from bipedConfig.IK_FOLLOW_ORDERS.

    Returns:
        labels
        target_ctrls
    """

    if limb_name not in bipedConfig.IK_FOLLOW_ORDERS:
        cmds.warning(
            "No IK follow order configured for {}".format(
                limb_name
            )
        )
        return [], []

    follow_order = bipedConfig.IK_FOLLOW_ORDERS[limb_name]

    labels = []
    target_ctrls = []

    for label, slot in follow_order:

        labels.append(label)

        if slot is None:
            continue

        if slot not in rig:
            cmds.warning(
                "Follow target slot {} not found in rig for {}".format(
                    slot,
                    limb_name
                )
            )
            continue

        ctrl = rig[slot].get("ctrl")

        if not ctrl:
            cmds.warning(
                "Follow target slot {} has no ctrl for {}".format(
                    slot,
                    limb_name
                )
            )
            continue

        target_ctrls.append(
            genUtils.resolve_node(ctrl)
        )

    return labels, target_ctrls


def get_IK_ctrl_aut(limb_name, IK_data):
    """
    Returns the IK ctrl AUT group for the limb.
    """

    if limb_name not in IK_data:
        return None

    limb_IK_data = IK_data[limb_name]

    IK_ctrl_data = limb_IK_data.get("IK_ctrl")

    if not IK_ctrl_data:
        return None

    aut = IK_ctrl_data.get("aut")

    if not aut:
        return None

    return genUtils.resolve_node(aut)


def connect_follow_weights(remap, constraint, target_count):
    """
    Connects remapColor RGB channels to parentConstraint weights.
    """

    weights = cmds.parentConstraint(
        constraint,
        query=True,
        weightAliasList=True
    )

    outputs = [
        remap + ".outColorR",
        remap + ".outColorG",
        remap + ".outColorB",
    ]

    for index in range(
        min(target_count, len(weights), len(outputs))
    ):

        cmds.connectAttr(
            outputs[index],
            constraint + "." + weights[index],
            force=True
        )


def connect_IK_follow_spaces(
    rig,
    IK_data,
    FKIK_blend_data,
    maintain_offset=True
):
    """
    Creates IK follow-space switching for every limb.

    Uses:
        switch_ctrl.follow enum
        remapColor RGB outputs
        parentConstraint weights on IK_ctrl_aut

    Enum examples:
        Arms: None/Main/COG/Clavicle
        Legs: None/Main/COG
    """

    print("=" * 80)
    print("CONNECTING IK FOLLOW SPACES")
    print("=" * 80)

    result = {}

    for limb_name, blend_data in FKIK_blend_data.items():

        if limb_name not in bipedConfig.IK_FOLLOW_ORDERS:
            continue

        switch_ctrl_data = blend_data.get("switch_ctrl_data")

        if not switch_ctrl_data:
            cmds.warning(
                "Skipping {}: missing switch_ctrl_data.".format(
                    limb_name
                )
            )
            continue

        switch_ctrl = switch_ctrl_data.get("ctrl")

        if not switch_ctrl:
            cmds.warning(
                "Skipping {}: missing switch ctrl.".format(
                    limb_name
                )
            )
            continue

        switch_ctrl = genUtils.resolve_node(switch_ctrl)

        IK_aut = get_IK_ctrl_aut(
            limb_name,
            IK_data
        )

        if not IK_aut:
            cmds.warning(
                "Skipping {}: missing IK ctrl aut group.".format(
                    limb_name
                )
            )
            continue

        follow_order = bipedConfig.IK_FOLLOW_ORDERS[limb_name]

        enum_labels, target_ctrls = get_follow_target_ctrls(
            limb_name,
            rig
        )

        if not target_ctrls:
            cmds.warning(
                "Skipping {}: no follow targets resolved.".format(
                    limb_name
                )
            )
            continue

        follow_attr = add_follow_attr(
            switch_ctrl,
            enum_labels,
            attr_name="follow"
        )

        remap = create_follow_remapColor(
            limb_name,
            follow_attr,
            follow_order
        )

        constraint_name = limb_name + "_IK_follow_parentConstraint"

        if cmds.objExists(constraint_name):
            cmds.delete(constraint_name)

        constraint = cmds.parentConstraint(
            target_ctrls,
            IK_aut,
            maintainOffset=maintain_offset,
            name=constraint_name
        )[0]

        connect_follow_weights(
            remap,
            constraint,
            len(target_ctrls)
        )

        result[limb_name] = {
            "switch_ctrl": switch_ctrl,
            "follow_attr": follow_attr,
            "remapColor": remap,
            "constraint": constraint,
            "IK_aut": IK_aut,
            "targets": target_ctrls
        }

        print(
            "Connected IK follow spaces for {} -> {}".format(
                limb_name,
                genUtils.pretty_node_name(IK_aut)
            )
        )

    print("=" * 80)
    print("IK FOLLOW SPACE CONNECTION COMPLETE")
    print("Created {} follow systems.".format(len(result)))
    print("=" * 80)

    return result