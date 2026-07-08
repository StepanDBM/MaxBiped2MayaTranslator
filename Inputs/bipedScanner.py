import maya.cmds as cmds
import re

def clean_name(name):

    name = name.split("|")[-1]

    name = re.sub(
        r"FBXASC032",
        "_",
        name,
        flags=re.IGNORECASE
    )

    while "__" in name:
        name = name.replace("__", "_")

    return name

class BipedScanner:

    REQUIRED_JOINTS = [
        "pelvis",
        "head",
        "l_upperarm",
        "r_upperarm",
        "l_thigh",
        "r_thigh",
    ]

    JOINT_PATTERNS = {

        # Core

        "root": ["bip001"],

        "pelvis": ["pelvis"],

        "spine": ["spine"],

        "spine1": ["spine1"],

        "spine2": ["spine2"],

        "neck": ["neck"],

        "head": ["head"],

        # Left Arm

        "l_clavicle": ["l clavicle"],

        "l_upperarm": ["l upperarm"],

        "l_forearm": ["l forearm"],

        "l_hand": ["l hand"],

        # Right Arm
        "r_clavicle": ["r clavicle"],

        "r_upperarm": ["r upperarm"],

        "r_forearm": ["r forearm"],

        "r_hand": ["r hand"],

        # Left Leg

        "l_thigh": ["l thigh"],

        "l_calf": ["l calf"],

        "l_foot": ["l foot"],

        "l_toe": ["l toe0","l toe"],

        # Right Leg

        "r_thigh": ["r thigh"],

        "r_calf": ["r calf"],

        "r_foot": ["r foot"],

        "r_toe": ["r toe0", "r toe"],
    }

    def __init__(self):

        self.joints = cmds.ls(
            type="joint",
            long=True
        )

        self.data = {}

    # NAME NORMALIZATION
    def normalize_name(self, name):

        # short name only
        name = name.split("|")[-1]

        # FBX ASCII spaces
        name = re.sub(
            r"FBXASC032",
            " ",
            name,
            flags=re.IGNORECASE
        )

        # FBX ASCII underscore
        name = re.sub(
            r"FBXASC095",
            "_",
            name,
            flags=re.IGNORECASE
        )

        # namespaces
        name = name.replace(":", " ")

        # underscores
        name = name.replace("_", " ")

        # multiple spaces
        name = " ".join(name.split())

        return name.lower()

    # FINDING
    def find_joint(self, pattern_list):

        # exact match pass

        for joint in self.joints:

            normalized = self.normalize_name(joint)

            for pattern in pattern_list:

                if normalized == pattern.lower():

                    return joint

        # partial match pass

        for joint in self.joints:

            normalized = self.normalize_name(joint)

            for pattern in pattern_list:

                if pattern.lower() in normalized:

                    return joint

        return None

    # MATRICES
    def get_world_matrix(self, obj):

        return cmds.xform(
            obj,
            q=True,
            ws=True,
            m=True
        )

    # SCAN
    def scan(self):

        character = {}

        for slot, patterns in self.JOINT_PATTERNS.items():

            character[slot] = self.find_joint(patterns)

        character["startFrame"] = cmds.playbackOptions(
            q=True,
            min=True
        )

        character["endFrame"] = cmds.playbackOptions(
            q=True,
            max=True
        )

        character["matrices"] = {}

        for key, value in character.items():

            if key in [
                "startFrame",
                "endFrame",
                "matrices"
            ]:
                continue

            if value and cmds.objExists(value):

                character["matrices"][key] = (
                    self.get_world_matrix(value)
                )

        self.validate(character)

        self.data = character

        return character

    # VALIDATION
    def validate(self, character):

        missing = []

        for joint in self.REQUIRED_JOINTS:

            if not character.get(joint):

                missing.append(joint)

        if missing:

            raise RuntimeError(
                "\nMissing required joints:\n\n{}".format(
                    "\n".join(missing)
                )
            )

    # DEBUG
    def debug_joint_names(self):

        print("\n========== JOINT NAMES ==========\n")

        for joint in self.joints:

            print(
                "{:<80} -> {}".format(
                    joint.split("|")[-1],
                    self.normalize_name(joint)
                )
            )

    def print_report(self):

        print("\n")
        print("=" * 160)
        print("BIPED SCAN REPORT")
        print("=" * 160)

        for key, value in self.data.items():

            if key == "matrices":
                continue

            print(
                "{:<15} {}".format(
                    key,
                    value
                )
            )

        print("=" * 160)


# PUBLIC FUNCTION
def scanCharacter():

    scanner = BipedScanner()

    data = scanner.scan()

    scanner.print_report()

    return data