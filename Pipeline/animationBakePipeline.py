# animationBakePipeline.py

import os
import importlib

import maya.cmds as cmds
import maya.mel as mel

from Inputs import bipedScanner

from Utilities.Config import bipedConfig
import Utilities.genUtils as genU
from Utilities import bakeJointsToControls
from Utilities import bakeFKtoIKctrls

importlib.reload(bipedScanner)
importlib.reload(bipedConfig)
importlib.reload(genU)
importlib.reload(bakeJointsToControls)
importlib.reload(bakeFKtoIKctrls)


ANIMATION_PIPELINE_STEP_COUNT = 8


def report_step(progress_callback, label):
    print("")
    print("=" * 80)
    print(label)
    print("=" * 80)

    if progress_callback:
        progress_callback(label)


# --------------------------------------------------
# BASIC HELPERS
# --------------------------------------------------

def safe_mel_path(path):
    path = os.path.normpath(path)
    path = path.replace("\\", "/")
    path = path.replace('"', '\\"')
    return path


def clean_base_name(node):
    """
    Converts a Maya node into the same clean base used by FK controls.

    Important:
        Imported animation FBX may have namespaces.
        Rig controls usually do not.
    """

    short = node.split("|")[-1]

    if ":" in short:
        short = short.split(":")[-1]

    return genU.clean_name(short)


def find_node(name):
    """
    Resolves a node by exact name or Maya ls fallback.
    """

    if cmds.objExists(name):
        return name

    matches = cmds.ls(name, long=False) or []

    if matches:
        return matches[0]

    matches = cmds.ls(name, long=True) or []

    if matches:
        return matches[0]

    return None


def control_data_from_base(base, suffix):
    """
    Returns a standard control dict from deterministic names.

    Example:
        base = Bip001_L_Hand
        suffix = FK_ctrl

    Creates:
        Bip001_L_Hand_FK_ctrl
        Bip001_L_Hand_FK_ctrl_ofs
        Bip001_L_Hand_FK_ctrl_aut
    """

    ctrl = find_node(base + "_" + suffix)
    ofs = find_node(base + "_" + suffix + "_ofs")
    aut = find_node(base + "_" + suffix + "_aut")

    if not ctrl:
        return None

    return {
        "ctrl": ctrl,
        "ofs": ofs,
        "aut": aut
    }


def make_dynamic_slot(base):
    slot = "anim_" + base
    slot = slot.replace(" ", "_")
    slot = slot.replace(":", "_")
    slot = slot.replace("|", "_")

    while "__" in slot:
        slot = slot.replace("__", "_")

    return slot.strip("_")


# --------------------------------------------------
# FBX ANIMATION IMPORT
# --------------------------------------------------

def import_animation_fbx(path):
    """
    Imports an animation FBX into the current rig scene.

    Returns:
        {
            "new_joints": [...],
            "top_nodes": [...]
        }

    We do not rely on namespaces here.
    Instead, we record what nodes existed before import and collect
    the newly imported skeleton nodes afterwards.
    """

    path = os.path.normpath(path)

    if not os.path.exists(path):
        raise RuntimeError(
            "Animation FBX does not exist: {}".format(path)
        )

    print("=" * 80)
    print("IMPORTING ANIMATION FBX")
    print(path)
    print("=" * 80)

    before_nodes = set(cmds.ls(long=True) or [])
    before_joints = set(cmds.ls(type="joint", long=True) or [])
    before_transforms = set(cmds.ls(type="transform", long=True) or [])

    try:
        if not cmds.pluginInfo(
            "fbxmaya",
            q=True,
            loaded=True
        ):
            cmds.loadPlugin("fbxmaya")
    except Exception as e:
        raise RuntimeError(
            "Could not load fbxmaya plugin: {}".format(e)
        )

    fbx_path = safe_mel_path(path)

    try:
        mel.eval("FBXResetImport;")
    except Exception:
        pass

    fbx_options = [
        'FBXImportMode -v "add";',
        'FBXImportCameras -v false;',
        'FBXImportLights -v false;',
        'FBXImportShapes -v true;',
        'FBXImportSkins -v true;',
        'FBXImportConstraints -v false;',
        'FBXImportSkeletonDefinitionsAs -v "HumanIK";',
        'FBXImportSetMayaFrameRate -v true;',
        'FBXImportFillTimeline -v true;',
        'FBXImportGenerateLog -v false;',
    ]

    for option in fbx_options:
        try:
            mel.eval(option)
        except Exception:
            pass

    try:
        mel.eval(
            'FBXImport -f "{}";'.format(fbx_path)
        )
    except Exception as e:
        raise RuntimeError(
            "FBXImport failed for {}: {}".format(path, e)
        )

    after_joints = set(cmds.ls(type="joint", long=True) or [])
    after_transforms = set(cmds.ls(type="transform", long=True) or [])

    new_joints = list(after_joints - before_joints)
    new_transforms = list(after_transforms - before_transforms)

    new_transform_set = set(new_transforms)
    top_nodes = []

    for node in new_transforms:
        if not cmds.objExists(node):
            continue

        parent = cmds.listRelatives(
            node,
            parent=True,
            fullPath=True
        ) or []

        if not parent or parent[0] not in new_transform_set:
            top_nodes.append(node)

    print("Imported animation joint count: {}".format(len(new_joints)))
    print("Imported animation top node count: {}".format(len(top_nodes)))

    if not new_joints:
        raise RuntimeError(
            "Animation FBX imported but no new joints were found: {}".format(
                path
            )
        )

    print("First imported animation joints:")

    for joint in new_joints[:20]:
        print("  {}".format(joint))

    print("=" * 80)

    return {
        "new_joints": new_joints,
        "top_nodes": top_nodes
    }


def delete_imported_animation(import_data):
    """
    Deletes the imported animation DTO skeleton / imported FBX nodes.
    """

    top_nodes = import_data.get("top_nodes", [])

    print("=" * 80)
    print("DELETING IMPORTED ANIMATION DTO")
    print("=" * 80)

    deleted = []

    for node in top_nodes:
        if not cmds.objExists(node):
            continue

        try:
            cmds.delete(node)
            deleted.append(node)
        except Exception as e:
            cmds.warning(
                "Could not delete imported animation node {}: {}".format(
                    node,
                    e
                )
            )

    print("Deleted {} imported top nodes.".format(len(deleted)))
    print("=" * 80)

    return deleted


# --------------------------------------------------
# CHARACTER SCAN FROM IMPORTED ANIMATION JOINTS
# --------------------------------------------------

def scan_animation_character_from_joints(joints):
    """
    Uses the existing biped scanner but restricts it to imported animation joints.
    """

    scanner = bipedScanner.BipedScanner()
    scanner.joints = joints

    char = scanner.scan()
    scanner.print_report()

    return char


# --------------------------------------------------
# RIG RECONSTRUCTION
# --------------------------------------------------

def build_animation_joint_lookup(joints):
    """
    Builds:
        clean base name -> animation joint
    """

    result = {}

    for joint in joints:
        if not cmds.objExists(joint):
            continue

        base = clean_base_name(joint)
        result[base] = joint

    return result


def reconstruct_rig_from_scene(char, animation_joints):
    """
    Reconstructs the rig dictionary expected by the existing bake utilities.

    Canonical controls:
        use bipedConfig.FK_CTRL_ORDER slots.

    Extra controls:
        any *_FK_ctrl whose base name matches an imported animation joint.
    """

    print("=" * 80)
    print("RECONSTRUCTING RIG DATA FROM EXISTING AUTO-RIG")
    print("=" * 80)

    rig = {}
    used_ctrls = set()

    animation_joint_lookup = build_animation_joint_lookup(
        animation_joints
    )

    # --------------------------------------------------
    # Canonical FK controls from bipedConfig slots
    # --------------------------------------------------

    for slot in bipedConfig.FK_CTRL_ORDER:

        joint = char.get(slot)

        if not joint:
            continue

        base = clean_base_name(joint)

        ctrl_data = control_data_from_base(
            base,
            "FK_ctrl"
        )

        if not ctrl_data:
            cmds.warning(
                "Missing FK ctrl for slot {} expected base {}".format(
                    slot,
                    base
                )
            )
            continue

        rig[slot] = {
            "source_joint": joint,
            "driver_joint": joint,
            "joint": joint,
            "ctrl": ctrl_data["ctrl"],
            "ofs": ctrl_data["ofs"],
            "aut": ctrl_data["aut"]
        }

        used_ctrls.add(ctrl_data["ctrl"])

        print(
            "Mapped canonical FK ctrl: {} -> {}".format(
                slot,
                ctrl_data["ctrl"]
            )
        )

    # --------------------------------------------------
    # Dynamic FK controls: fingers / extras
    # --------------------------------------------------

    fk_ctrls = cmds.ls(
        "*_FK_ctrl",
        type="transform",
        long=False
    ) or []

    for ctrl in fk_ctrls:

        if ctrl in used_ctrls:
            continue

        if not ctrl.endswith("_FK_ctrl"):
            continue

        base = ctrl[:-len("_FK_ctrl")]

        joint = animation_joint_lookup.get(base)

        if not joint:
            continue

        ofs = find_node(base + "_FK_ctrl_ofs")
        aut = find_node(base + "_FK_ctrl_aut")

        slot = make_dynamic_slot(base)

        if slot in rig:
            continue

        rig[slot] = {
            "source_joint": joint,
            "driver_joint": joint,
            "joint": joint,
            "ctrl": ctrl,
            "ofs": ofs,
            "aut": aut
        }

        print(
            "Mapped dynamic FK ctrl: {} -> {}".format(
                slot,
                ctrl
            )
        )

    print("Reconstructed {} FK rig controls.".format(len(rig)))
    print("=" * 80)

    return rig


def reconstruct_IK_data_from_scene():
    """
    Reconstructs the IK_data dictionary expected by bakeFKtoIKctrls.

    Uses deterministic names from bipedConfig.IK_LIMBS.
    """

    print("=" * 80)
    print("RECONSTRUCTING IK DATA FROM EXISTING AUTO-RIG")
    print("=" * 80)

    IK_data = {}

    for limb_name, data in bipedConfig.IK_LIMBS.items():

        base = data.get("name")

        if not base:
            continue

        IK_ctrl = find_node(base + "_IK_ctrl")
        IK_ofs = find_node(base + "_IK_ctrl_ofs")
        IK_aut = find_node(base + "_IK_ctrl_aut")

        pv_ctrl = find_node(base + "_pv_ctrl")
        pv_ofs = find_node(base + "_pv_ctrl_ofs")
        pv_aut = find_node(base + "_pv_ctrl_aut")

        if not IK_ctrl:
            cmds.warning(
                "Missing IK ctrl for limb {} expected {}".format(
                    limb_name,
                    base + "_IK_ctrl"
                )
            )
            continue

        if not pv_ctrl:
            cmds.warning(
                "Missing PV ctrl for limb {} expected {}".format(
                    limb_name,
                    base + "_pv_ctrl"
                )
            )

        IK_data[limb_name] = {
            "IK_ctrl": {
                "ctrl": IK_ctrl,
                "ofs": IK_ofs,
                "aut": IK_aut
            },
            "pv_ctrl": {
                "ctrl": pv_ctrl,
                "ofs": pv_ofs,
                "aut": pv_aut
            }
        }

        print(
            "Mapped IK data for {}: IK={} PV={}".format(
                limb_name,
                IK_ctrl,
                pv_ctrl
            )
        )

    print("Reconstructed {} IK systems.".format(len(IK_data)))
    print("=" * 80)

    return IK_data


# --------------------------------------------------
# MAIN PIPELINE
# --------------------------------------------------

def reconstruct_IK_data_from_scene():
    """
    Reconstructs the IK_data dictionary expected by bakeFKtoIKctrls.

    This intentionally mirrors the shape created by createIKctrls.create_IK_controls().

    Required by bakeFKtoIKctrls:
        start
        mid
        end
        slots
        IK_ctrl
        pv_ctrl
    """

    print("=" * 80)
    print("RECONSTRUCTING IK DATA FROM EXISTING AUTO-RIG")
    print("=" * 80)

    IK_data = {}

    for limb_name, config_data in bipedConfig.IK_LIMBS.items():

        base = config_data.get("name")

        if not base:
            cmds.warning(
                "Skipping IK data reconstruction for {}: missing config name.".format(
                    limb_name
                )
            )
            continue

        IK_ctrl = find_node(base + "_IK_ctrl")
        IK_ofs = find_node(base + "_IK_ctrl_ofs")
        IK_aut = find_node(base + "_IK_ctrl_aut")

        pv_ctrl = find_node(base + "_pv_ctrl")
        pv_ofs = find_node(base + "_pv_ctrl_ofs")
        pv_aut = find_node(base + "_pv_ctrl_aut")

        if not IK_ctrl:
            cmds.warning(
                "Missing IK ctrl for limb {} expected {}".format(
                    limb_name,
                    base + "_IK_ctrl"
                )
            )
            continue

        if not pv_ctrl:
            cmds.warning(
                "Missing PV ctrl for limb {} expected {}".format(
                    limb_name,
                    base + "_pv_ctrl"
                )
            )

        IK_data[limb_name] = {
            # These are the important missing fields.
            "side": config_data.get("side"),
            "family": config_data.get("family"),
            "start": config_data.get("start"),
            "mid": config_data.get("mid"),
            "end": config_data.get("end"),
            "slots": list(config_data.get("slots", [])),
            "name": base,
            "IK_group": config_data.get("IK_group"),

            # Existing controls in the loaded auto-rig scene.
            "IK_ctrl": {
                "ctrl": IK_ctrl,
                "ofs": IK_ofs,
                "aut": IK_aut
            },

            "pv_ctrl": {
                "ctrl": pv_ctrl,
                "ofs": pv_ofs,
                "aut": pv_aut
            }
        }

        print(
            "Mapped IK data for {}: start={} mid={} end={} IK={} PV={}".format(
                limb_name,
                IK_data[limb_name]["start"],
                IK_data[limb_name]["mid"],
                IK_data[limb_name]["end"],
                IK_ctrl,
                pv_ctrl
            )
        )

    print("Reconstructed {} IK systems.".format(len(IK_data)))
    print("=" * 80)

    return IK_data