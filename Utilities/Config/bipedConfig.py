# Config/bipedConfig.py


# --------------------------------------------------
# MAIN GROUP NAMES
# --------------------------------------------------

MAIN_GROUPS = {
    "ctrl": "ctrl_grp",
    "family_ctrls": "family_ctrls_grp",
    "IK_ctrls": "IK_ctrls_grp",
    "rig": "rig_grp",
    "chains": "chains_grp",
    "FK_chains": "FK_chains_grp",
    "IK_chains": "IK_chains_grp",
    "FKIK_chains": "FKIK_chains_grp",
}


# --------------------------------------------------
# LIMB-END DIRECT FK SYSTEMS
# --------------------------------------------------
# These are direct FK descendant systems.
# Current intended use:
#     hands / fingers
#
# Do NOT put feet here if we are making feet FK/IK.
# Feet/toes are handled by FOOT_FKIK_ENDS below.

LIMB_END_FK_ROOTS = {
    "l_hand_end": {
        "root_slot": "l_hand",
        "family_group": "l_arm_FK_ctrls_grp",
        "include_root": False
    },

    "r_hand_end": {
        "root_slot": "r_hand",
        "family_group": "r_arm_FK_ctrls_grp",
        "include_root": False
    },
}


# --------------------------------------------------
# FOOT FK/IK END SYSTEMS
# --------------------------------------------------
# These are foot extension systems.
#
# Main leg FK/IK limb remains:
#     thigh -> calf -> foot
#
# Foot end FK/IK creates:
#     toe_FK_jnt under foot_FK_jnt
#     toe_IK_jnt under foot_IK_jnt
#
# Then toe FK/IK drivers are blended into the original toe
# using the parent leg FKIK_blend attr.

FOOT_FKIK_ENDS = {
    "l_foot_end": {
        "side": "l",
        "parent_limb": "l_leg",
        "root_slot": "l_foot",
        "end_slot": "l_toe",
        "FK_chain_group": "l_foot_end_FK_chain_grp",
        "IK_chain_group": "l_foot_end_IK_chain_grp",
    },

    "r_foot_end": {
        "side": "r",
        "parent_limb": "r_leg",
        "root_slot": "r_foot",
        "end_slot": "r_toe",
        "FK_chain_group": "r_foot_end_FK_chain_grp",
        "IK_chain_group": "r_foot_end_IK_chain_grp",
    },
}


# --------------------------------------------------
# CORE / LIMB SLOT DEFINITIONS
# --------------------------------------------------

CORE_FK_SLOTS = [
    "pelvis",
    "spine",
    "spine1",
    "spine2",
    "neck",
    "head",

    # Kept as direct/core controls for now.
    "l_clavicle",
    "r_clavicle",
]


LIMB_FK_SLOTS = [
    # left arm
    "l_upperarm",
    "l_forearm",
    "l_hand",

    # right arm
    "r_upperarm",
    "r_forearm",
    "r_hand",

    # left leg
    "l_thigh",
    "l_calf",
    "l_foot",
    "l_toe",

    # right leg
    "r_thigh",
    "r_calf",
    "r_foot",
    "r_toe",
]


FK_CTRL_ORDER = CORE_FK_SLOTS + LIMB_FK_SLOTS


# --------------------------------------------------
# FK RELATIONSHIPS
# --------------------------------------------------

FK_LINKS = [
    # spine
    ("pelvis", "spine"),
    ("spine", "spine1"),
    ("spine1", "spine2"),
    ("spine2", "neck"),
    ("neck", "head"),

    # left arm
    ("spine2", "l_clavicle"),
    ("l_clavicle", "l_upperarm"),
    ("l_upperarm", "l_forearm"),
    ("l_forearm", "l_hand"),

    # right arm
    ("spine2", "r_clavicle"),
    ("r_clavicle", "r_upperarm"),
    ("r_upperarm", "r_forearm"),
    ("r_forearm", "r_hand"),

    # left leg
    ("pelvis", "l_thigh"),
    ("l_thigh", "l_calf"),
    ("l_calf", "l_foot"),
    ("l_foot", "l_toe"),

    # right leg
    ("pelvis", "r_thigh"),
    ("r_thigh", "r_calf"),
    ("r_calf", "r_foot"),
    ("r_foot", "r_toe"),
]


# --------------------------------------------------
# FAMILY GROUPS
# --------------------------------------------------

CONTROL_FAMILIES = {
    "c_spine": {
        "group": "c_spine_FK_ctrls_grp",
        "slots": [
            "pelvis",
            "spine",
            "spine1",
            "spine2",
            "neck",
            "head",
        ],
    },

    "l_arm": {
        "group": "l_arm_FK_ctrls_grp",
        "slots": [
            "l_clavicle",
            "l_upperarm",
            "l_forearm",
            "l_hand",
        ],
    },

    "r_arm": {
        "group": "r_arm_FK_ctrls_grp",
        "slots": [
            "r_clavicle",
            "r_upperarm",
            "r_forearm",
            "r_hand",
        ],
    },

    "l_leg": {
        "group": "l_leg_FK_ctrls_grp",
        "slots": [
            "l_thigh",
            "l_calf",
            "l_foot",
            "l_toe",
        ],
    },

    "r_leg": {
        "group": "r_leg_FK_ctrls_grp",
        "slots": [
            "r_thigh",
            "r_calf",
            "r_foot",
            "r_toe",
        ],
    },

    "misc": {
        "group": "misc_FK_ctrls_grp",
        "slots": [],
    },
}


# --------------------------------------------------
# IK LIMB DEFINITIONS
# --------------------------------------------------
# Keep legs ending at foot, NOT toe.
# Reverse foot / toe IK happens separately.

IK_LIMBS = {
    "l_arm": {
        "side": "l",
        "family": "l_arm",
        "start": "l_upperarm",
        "mid": "l_forearm",
        "end": "l_hand",
        "slots": [
            "l_upperarm",
            "l_forearm",
            "l_hand",
        ],
        "name": "bip001_l_arm",
        "IK_group": "l_arm_IK_ctrls_grp",
    },

    "r_arm": {
        "side": "r",
        "family": "r_arm",
        "start": "r_upperarm",
        "mid": "r_forearm",
        "end": "r_hand",
        "slots": [
            "r_upperarm",
            "r_forearm",
            "r_hand",
        ],
        "name": "bip001_r_arm",
        "IK_group": "r_arm_IK_ctrls_grp",
    },

    "l_leg": {
        "side": "l",
        "family": "l_leg",
        "start": "l_thigh",
        "mid": "l_calf",
        "end": "l_foot",
        "slots": [
            "l_thigh",
            "l_calf",
            "l_foot",
        ],
        "name": "bip001_l_leg",
        "IK_group": "l_leg_IK_ctrls_grp",
    },

    "r_leg": {
        "side": "r",
        "family": "r_leg",
        "start": "r_thigh",
        "mid": "r_calf",
        "end": "r_foot",
        "slots": [
            "r_thigh",
            "r_calf",
            "r_foot",
        ],
        "name": "bip001_r_leg",
        "IK_group": "r_leg_IK_ctrls_grp",
    },
}


# --------------------------------------------------
# MAIN FK/IK CHAIN DEFINITIONS
# --------------------------------------------------
# Do NOT include toes here.
# Main leg FK/IK chain remains thigh -> calf -> foot.

FKIK_LIMBS = {
    "l_arm": {
        "slots": [
            "l_upperarm",
            "l_forearm",
            "l_hand",
        ],
        "IK_data": "l_arm",
        "FK_chain_group": "l_arm_FK_chain_grp",
        "IK_chain_group": "l_arm_IK_chain_grp",
        "FKIK_group": "l_arm_FKIK_grp",
    },

    "r_arm": {
        "slots": [
            "r_upperarm",
            "r_forearm",
            "r_hand",
        ],
        "IK_data": "r_arm",
        "FK_chain_group": "r_arm_FK_chain_grp",
        "IK_chain_group": "r_arm_IK_chain_grp",
        "FKIK_group": "r_arm_FKIK_grp",
    },

    "l_leg": {
        "slots": [
            "l_thigh",
            "l_calf",
            "l_foot",
        ],
        "IK_data": "l_leg",
        "FK_chain_group": "l_leg_FK_chain_grp",
        "IK_chain_group": "l_leg_IK_chain_grp",
        "FKIK_group": "l_leg_FKIK_grp",
    },

    "r_leg": {
        "slots": [
            "r_thigh",
            "r_calf",
            "r_foot",
        ],
        "IK_data": "r_leg",
        "FK_chain_group": "r_leg_FK_chain_grp",
        "IK_chain_group": "r_leg_IK_chain_grp",
        "FKIK_group": "r_leg_FKIK_grp",
    },
}


# --------------------------------------------------
# IK PREFERRED ANGLES
# --------------------------------------------------

IK_PREFERRED_ANGLES = {
    "l_arm": {
        "mid_slot": "l_forearm",
        "angles": (0, 0, -10)
    },

    "r_arm": {
        "mid_slot": "r_forearm",
        "angles": (0, 0, -10)
    },

    "l_leg": {
        "mid_slot": "l_calf",
        "angles": (0, 0, -10)
    },

    "r_leg": {
        "mid_slot": "r_calf",
        "angles": (0, 0, -10)
    },
}


# --------------------------------------------------
# IK BASE PARENTING
# --------------------------------------------------

IK_BASE_PARENT_SLOTS = {
    "l_arm": "l_clavicle",
    "r_arm": "r_clavicle",
    "l_leg": "pelvis",
    "r_leg": "pelvis",
}


# --------------------------------------------------
# IK FOLLOW SPACES
# --------------------------------------------------

IK_FOLLOW_ORDERS = {
    "l_arm": [
        ("None", None),
        ("Main", "pelvis"),
        ("COG", "spine2"),
        ("Clavicle", "l_clavicle"),
    ],

    "r_arm": [
        ("None", None),
        ("Main", "pelvis"),
        ("COG", "spine2"),
        ("Clavicle", "r_clavicle"),
    ],

    "l_leg": [
        ("None", None),
        ("Main", "pelvis"),
        ("COG", "spine2"),
    ],

    "r_leg": [
        ("None", None),
        ("Main", "pelvis"),
        ("COG", "spine2"),
    ],
}


# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------

def get_family_key_for_slot(slot):
    """
    Returns family key:
        c_spine
        l_arm
        r_arm
        l_leg
        r_leg
        misc
    """

    for family_key, data in CONTROL_FAMILIES.items():

        if slot in data["slots"]:
            return family_key

    return "misc"


def get_family_for_slot(slot):
    """
    Returns actual Maya group name for a slot.
    """

    family_key = get_family_key_for_slot(
        slot
    )

    return CONTROL_FAMILIES[family_key]["group"]


def get_all_family_groups():
    """
    Returns all family group names.
    """

    return [
        data["group"]
        for data in CONTROL_FAMILIES.values()
    ]


def get_all_IK_groups():
    """
    Returns all IK control group names.
    """

    return [
        data["IK_group"]
        for data in IK_LIMBS.values()
    ]


def is_limb_slot(slot):
    return slot in LIMB_FK_SLOTS


def is_core_slot(slot):
    return slot in CORE_FK_SLOTS


def is_foot_end_slot(slot):
    """
    Returns True if slot belongs to a foot FK/IK end system.
    """

    for data in FOOT_FKIK_ENDS.values():

        if slot == data.get("end_slot"):
            return True

    return False