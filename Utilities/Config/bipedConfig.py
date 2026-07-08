# Config/bipedConfig.py

# MAIN GROUP NAMES

MAIN_GROUPS = {
    "ctrl": "ctrl_grp",
    "family_ctrls": "family_ctrls_grp",
    "ik_ctrls": "ik_ctrls_grp",
    "rig": "rig_grp",
    "chains": "chains_grp",
    "fk_chains": "fk_chains_grp",
    "ik_chains": "ik_chains_grp",
    "fkik_chains": "fkik_chains_grp",
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
        "group": "c_spine_ctrls_grp",
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
        "group": "l_arm_ctrls_grp",
        "slots": [
            "l_clavicle",
            "l_upperarm",
            "l_forearm",
            "l_hand",
        ],
    },

    "r_arm": {
        "group": "r_arm_ctrls_grp",
        "slots": [
            "r_clavicle",
            "r_upperarm",
            "r_forearm",
            "r_hand",
        ],
    },

    "l_leg": {
        "group": "l_leg_ctrls_grp",
        "slots": [
            "l_thigh",
            "l_calf",
            "l_foot",
        ],
    },

    "r_leg": {
        "group": "r_leg_ctrls_grp",
        "slots": [
            "r_thigh",
            "r_calf",
            "r_foot",
        ],
    },

    "misc": {
        "group": "misc_ctrls_grp",
        "slots": [],
    },
}


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
        "ik_group": "l_arm_ik_ctrls_grp",
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
        "ik_group": "r_arm_ik_ctrls_grp",
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
        "ik_group": "l_leg_ik_ctrls_grp",
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
        "ik_group": "r_leg_ik_ctrls_grp",
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
        "ik_data": "l_arm",
        "fk_chain_group": "l_arm_fk_chain_grp",
        "ik_chain_group": "l_arm_ik_chain_grp",
        "fkik_group": "l_arm_fkik_grp",
    },

    "r_arm": {
        "slots": [
            "r_upperarm",
            "r_forearm",
            "r_hand",
        ],
        "ik_data": "r_arm",
        "fk_chain_group": "r_arm_fk_chain_grp",
        "ik_chain_group": "r_arm_ik_chain_grp",
        "fkik_group": "r_arm_fkik_grp",
    },

    "l_leg": {
        "slots": [
            "l_thigh",
            "l_calf",
            "l_foot",
        ],
        "ik_data": "l_leg",
        "fk_chain_group": "l_leg_fk_chain_grp",
        "ik_chain_group": "l_leg_ik_chain_grp",
        "fkik_group": "l_leg_fkik_grp",
    },

    "r_leg": {
        "slots": [
            "r_thigh",
            "r_calf",
            "r_foot",
        ],
        "ik_data": "r_leg",
        "fk_chain_group": "r_leg_fk_chain_grp",
        "ik_chain_group": "r_leg_ik_chain_grp",
        "fkik_group": "r_leg_fkik_grp",
    },
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


def get_all_ik_groups():
    """
    Returns all IK control group names.
    """

    return [
        data["ik_group"]
        for data in IK_LIMBS.values()
    ]