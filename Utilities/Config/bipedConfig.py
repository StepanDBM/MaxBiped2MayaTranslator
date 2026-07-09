# Config/bipedConfig.py

# MAIN GROUP NAMES

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


# CANONICAL SLOT ORDER

FK_CTRL_ORDER = [
    # spine
    "pelvis",
    "spine",
    "spine1",
    "spine2",
    "neck",
    "head",

    # left arm
    "l_clavicle",
    "l_upperarm",
    "l_forearm",
    "l_hand",

    # right arm
    "r_clavicle",
    "r_upperarm",
    "r_forearm",
    "r_hand",

    # left leg
    "l_thigh",
    "l_calf",
    "l_foot",

    # right leg
    "r_thigh",
    "r_calf",
    "r_foot",
]


# --------------------------------------------------
# FK RELATIONSHIPS
# --------------------------------------------------

FK_LINKS = [
    ("pelvis", "spine"),
    ("spine", "spine1"),
    ("spine1", "spine2"),
    ("spine2", "neck"),
    ("neck", "head"),

    ("spine2", "l_clavicle"),
    ("l_clavicle", "l_upperarm"),
    ("l_upperarm", "l_forearm"),
    ("l_forearm", "l_hand"),

    ("spine2", "r_clavicle"),
    ("r_clavicle", "r_upperarm"),
    ("r_upperarm", "r_forearm"),
    ("r_forearm", "r_hand"),

    ("pelvis", "l_thigh"),
    ("l_thigh", "l_calf"),
    ("l_calf", "l_foot"),

    ("pelvis", "r_thigh"),
    ("r_thigh", "r_calf"),
    ("r_calf", "r_foot"),
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
        ],
    },

    "r_leg": {
        "group": "r_leg_FK_ctrls_grp",
        "slots": [
            "r_thigh",
            "r_calf",
            "r_foot",
        ],
    },

    "misc": {
        "group": "misc_FK_ctrls_grp",
        "slots": [],
    },
}

CORE_FK_SLOTS = [
    "pelvis",
    "spine",
    "spine1",
    "spine2",
    "neck",
    "head",

    # I will keep clavicles as core/direct for now.
    "l_clavicle",
    "r_clavicle",
]


LIMB_FK_SLOTS = [
    "l_upperarm",
    "l_forearm",
    "l_hand",

    "r_upperarm",
    "r_forearm",
    "r_hand",

    "l_thigh",
    "l_calf",
    "l_foot",

    "r_thigh",
    "r_calf",
    "r_foot",
]


FK_CTRL_ORDER = CORE_FK_SLOTS + LIMB_FK_SLOTS

# IK LIMB DEFINITIONS

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


# FK/IK CHAIN DEFINITIONS

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
IK_PREFERRED_ANGLES = {
    # Values are XYZ preferred angle values in degrees.
    # These may need tweaking depending on Biped joint orientation.

    "l_arm": {
        "mid_slot": "l_forearm",
        "angles": (00, 0, -10)
    },

    "r_arm": {
        "mid_slot": "r_forearm",
        "angles": (0, 0, 10)
    },

    "l_leg": {
        "mid_slot": "l_calf",
        "angles": (0, 0, 10)
    },

    "r_leg": {
        "mid_slot": "r_calf",
        "angles": (0, 0, -10)
    },
}

IK_BASE_PARENT_SLOTS = {
    "l_arm": "l_clavicle",
    "r_arm": "r_clavicle",
    "l_leg": "pelvis",
    "r_leg": "pelvis",
}

# HELPER FUNCTIONS

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

    family_key = get_family_key_for_slot(slot)

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