import maya.cmds as cmds
import importlib
import re

import Utilities.genUtils as genUtils
from Utilities.Config import bipedConfig

importlib.reload(genUtils)
importlib.reload(bipedConfig)


# LOCAL NAME HELPER

def clean_name(name):
    """
    Uses genUtils.clean_name if present.
    Falls back to local cleaner otherwise.
    """

    if hasattr(genUtils, "clean_name"):
        return genUtils.clean_name(name)

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


# DRIVER JOINT CREATION
def duplicate_source_joint_as_driver(source_joint, suffix):
    """
    Duplicates one source joint as a clean FK or IK driver joint.

    Example:
        Bip001FBXASC032LFBXASC032UpperArm
        ->
        Bip001_L_UpperArm_fk_jnt
        Bip001_L_UpperArm_ik_jnt
    """

    source_joint = genUtils.resolve_node(source_joint)

    clean = clean_name(source_joint)

    driver_name = clean + "_" + suffix + "_jnt"

    if cmds.objExists(driver_name):
        cmds.delete(driver_name)

    source_matrix = cmds.xform(
        source_joint,
        q=True,
        ws=True,
        m=True
    )

    driver_joint = cmds.duplicate(
        source_joint,
        parentOnly=True,
        n=driver_name
    )[0]

    parent = cmds.listRelatives(
        driver_joint,
        parent=True,
        fullPath=False
    )

    if parent:
        driver_joint = cmds.parent(
            driver_joint,
            world=True
        )[0]

    cmds.xform(
        driver_joint,
        ws=True,
        m=source_matrix
    )

    try:
        cmds.setAttr(driver_joint + ".radius", 2)
    except Exception:
        pass

    return driver_joint


def create_driver_chain_from_slots(char, slots, suffix, parent_grp):
    """
    Creates one FK or IK driver chain from canonical scanner slots.

    Example:
        slots = ["l_upperarm", "l_forearm", "l_hand"]
        suffix = "fk"

    Result:
        Bip001_L_UpperArm_fk_jnt
            └── Bip001_L_Forearm_fk_jnt
                └── Bip001_L_Hand_fk_jnt
    """
    auto_transform_snapshot = genUtils.get_auto_transform_nodes()
    chain = []
    source_matrices = {}

    # Create joints flat first
    for slot in slots:

        source_joint = char.get(slot)

        if not source_joint:
            raise RuntimeError(
                "Missing source joint for slot: {}".format(slot)
            )

        source_joint = genUtils.resolve_node(source_joint)

        source_matrices[slot] = cmds.xform(
            source_joint,
            q=True,
            ws=True,
            m=True
        )

        driver_joint = duplicate_source_joint_as_driver(
            source_joint,
            suffix
        )

        chain.append(driver_joint)

    # Parent joints into proper hierarchy
    for i in range(1, len(chain)):

        child = chain[i]
        parent = chain[i - 1]

        child = cmds.parent(
            child,
            parent,
            absolute=True
        )[0]

        chain[i] = child

    # Re-apply source matrices after parenting
    # This protects world-space position/orientation.
    for slot, driver_joint in zip(slots, chain):

        driver_joint = genUtils.resolve_node(driver_joint)

        cmds.xform(
            driver_joint,
            ws=True,
            m=source_matrices[slot]
        )

    # Parent chain root under limb group
    chain[0] = cmds.parent(
        chain[0],
        parent_grp,
        absolute=True
    )[0]

    # Store short names where possible
    clean_chain = []

    for jnt in chain:

        short = jnt.split("|")[-1]
        clean_chain.append(short)
    """
    Delete Maya's unwanted transform1, transform2, etc. Those are
    created to preserve child's matrices when creating chains or
    remapping positions but it's easier to delete them rather than
    to make sure they do not exist jssjsjsjjs
    """
    genUtils.cleanup_auto_transform_nodes(
        before=auto_transform_snapshot
    )
    return clean_chain


# MAIN BUILDER

def create_FKIK_driver_chains(
    char,
    delete_existing=True,
    build_at_frame=None
):
    """
    Creates FK and IK duplicate driver chains for every configured limb.

    This only creates chains.

    It does NOT:
        - connect FK controls to FK chains
        - create IK handles
        - connect IK controls
        - blend chains into original skeleton

    Expected config:
        bipedConfig.FKIK_LIMBS
    """

    if build_at_frame is not None:
        cmds.currentTime(
            build_at_frame,
            edit=True
        )

    rig_grp = genUtils.ensure_group(
        "rig_grp"
    )

    chains_grp = genUtils.ensure_group(
        "chains_grp",
        parent=rig_grp
    )

    # Development rebuild behavior
    if delete_existing:

        if cmds.objExists("fk_chains_grp"):
            cmds.delete("fk_chains_grp")

        if cmds.objExists("ik_chains_grp"):
            cmds.delete("ik_chains_grp")

    fk_chains_grp = genUtils.ensure_group(
        "fk_chains_grp",
        parent=chains_grp
    )

    ik_chains_grp = genUtils.ensure_group(
        "ik_chains_grp",
        parent=chains_grp
    )

    chain_data = {}

    for limb_name, limb_data in bipedConfig.FKIK_LIMBS.items():

        slots = limb_data["slots"]

        fk_group_name = limb_data.get(
            "fk_chain_group",
            limb_name + "_fk_chain_grp"
        )

        ik_group_name = limb_data.get(
            "ik_chain_group",
            limb_name + "_ik_chain_grp"
        )

        fk_limb_grp = genUtils.ensure_group(
            fk_group_name,
            parent=fk_chains_grp
        )

        ik_limb_grp = genUtils.ensure_group(
            ik_group_name,
            parent=ik_chains_grp
        )

        fk_chain = create_driver_chain_from_slots(
            char,
            slots,
            "fk",
            fk_limb_grp
        )

        ik_chain = create_driver_chain_from_slots(
            char,
            slots,
            "ik",
            ik_limb_grp
        )

        chain_data[limb_name] = {
            "slots": slots,

            "fk_chain": fk_chain,
            "ik_chain": ik_chain,

            "fk_group": fk_limb_grp,
            "ik_group": ik_limb_grp,
        }

        print(
            "Created FK/IK chains for {}: {}".format(
                limb_name,
                slots
            )
        )

    print(
        "Created FK/IK driver chains for {} limbs.".format(
            len(chain_data)
        )
    )

    return chain_data