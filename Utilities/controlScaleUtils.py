import importlib

import Utilities.vectorMath as vMath

importlib.reload(vMath)


def distance_between(char, slot_a, slot_b):
    """
    Returns world-space distance between two char slots.
    """

    node_a = char.get(slot_a)
    node_b = char.get(slot_b)

    if not node_a or not node_b:
        return None

    try:
        return vMath.vec_length(
            vMath.vec_sub(
                vMath.get_world_pos(node_b),
                vMath.get_world_pos(node_a)
            )
        )

    except Exception:
        return None


def average_valid(values):
    """
    Returns average of valid distances.
    """

    values = [
        value for value in values
        if value is not None and value > 0.001
    ]

    if not values:
        return None

    return sum(values) / float(len(values))


def clamp(value, min_value, max_value):
    return max(
        min_value,
        min(
            value,
            max_value
        )
    )


def get_character_measurements(char):
    """
    Computes reusable proportional rig measurements.
    """

    l_arm_len = average_valid([
        distance_between(char, "l_clavicle", "l_hand"),
        distance_between(char, "l_upperarm", "l_hand")
    ])

    r_arm_len = average_valid([
        distance_between(char, "r_clavicle", "r_hand"),
        distance_between(char, "r_upperarm", "r_hand")
    ])

    l_leg_len = average_valid([
        distance_between(char, "l_thigh", "l_foot"),
        distance_between(char, "l_thigh", "l_toe")
    ])

    r_leg_len = average_valid([
        distance_between(char, "r_thigh", "r_foot"),
        distance_between(char, "r_thigh", "r_toe")
    ])

    shoulder_width = average_valid([
        distance_between(char, "l_clavicle", "r_clavicle"),
        distance_between(char, "l_upperarm", "r_upperarm")
    ])

    spine_len = average_valid([
        distance_between(char, "pelvis", "head"),
        distance_between(char, "pelvis", "spine2")
    ])

    arm_len = average_valid([
        l_arm_len,
        r_arm_len
    ])

    leg_len = average_valid([
        l_leg_len,
        r_leg_len
    ])

    torso_len = average_valid([
        shoulder_width,
        spine_len
    ])

    global_len = average_valid([
        distance_between(char, "l_foot", "head"),
        distance_between(char, "r_foot", "head"),
        distance_between(char, "pelvis", "head"),
        arm_len,
        leg_len,
        torso_len
    ]) or 100.0

    size_data = {
        "l_arm_len": l_arm_len or global_len * 0.35,
        "r_arm_len": r_arm_len or global_len * 0.35,
        "arm_len": arm_len or global_len * 0.35,

        "l_leg_len": l_leg_len or global_len * 0.45,
        "r_leg_len": r_leg_len or global_len * 0.45,
        "leg_len": leg_len or global_len * 0.45,

        "shoulder_width": shoulder_width or global_len * 0.25,
        "spine_len": spine_len or global_len * 0.35,
        "torso_len": torso_len or global_len * 0.30,

        "global_len": global_len
    }
    return size_data


def get_fk_control_size(slot, char, measurements=None):
    """
    Returns proportional FK control size.
    """

    if measurements is None:
        measurements = get_character_measurements(char)

    global_len = measurements["global_len"]

    size = global_len * 0.045

    if slot in [
        "root",
        "pelvis"
    ]:
        size = measurements["torso_len"] * 0.65

    elif slot in [
        "spine",
        "spine1",
        "spine2",
        "neck",
        "head"
    ]:
        size = measurements["torso_len"] * 0.45

    elif slot in [
        "l_clavicle",
        "r_clavicle"
    ]:
        size = measurements["shoulder_width"] * 0.16

    elif slot in [
        "l_upperarm",
        "l_forearm",
        "l_hand"
    ]:
        size = measurements["l_arm_len"] * 0.2

    elif slot in [
        "r_upperarm",
        "r_forearm",
        "r_hand"
    ]:
        size = measurements["r_arm_len"] * 0.2

    elif slot in [
        "l_thigh",
        "l_calf",
        "l_foot",
        "l_toe"
    ]:
        size = measurements["l_leg_len"] * 0.18

    elif slot in [
        "r_thigh",
        "r_calf",
        "r_foot",
        "r_toe"
    ]:
        size = measurements["r_leg_len"] * 0.18

    elif any(
        token in slot.lower()
        for token in [
            "thumb",
            "index",
            "middle",
            "ring",
            "pinky",
            "finger"
        ]
    ):
        size = measurements["arm_len"] * 0.1

    return clamp(
        size,
        global_len * .02,
        global_len * .6
    )


def get_ik_control_size(limb_name, char, measurements=None):
    """
    Returns proportional IK control size.
    """

    if measurements is None:
        measurements = get_character_measurements(char)

    if limb_name.startswith("l_arm"):
        return measurements["l_arm_len"] * 0.25

    if limb_name.startswith("r_arm"):
        return measurements["r_arm_len"] * 0.25

    if limb_name.startswith("l_leg"):
        return measurements["l_leg_len"] * 0.2

    if limb_name.startswith("r_leg"):
        return measurements["r_leg_len"] * 0.2

    return measurements["global_len"] * 0.08


def get_pv_control_size(limb_name, char, measurements=None):
    """
    Returns proportional pole-vector control size.
    """

    return get_ik_control_size(
        limb_name,
        char,
        measurements=measurements
    ) * 0.45