import maya.cmds as cmds
import importlib
import re

import Creators.ctrlAesthetics as ctrlAes
import Utilities.genUtils as genUtils
from Utilities.Config import bipedConfig


importlib.reload(ctrlAes)
importlib.reload(genUtils)
importlib.reload(bipedConfig)

def create_ctrl_for_joint(source_joint, driver_joint=None):

    if driver_joint is None:
        driver_joint = source_joint

    clean = genUtils.clean_name(source_joint)

    ctrl_name = clean + "_FK_ctrl"
    ofs_name = clean + "_FK_ctrl_ofs"
    aut_name = clean + "_FK_ctrl_aut"

    if cmds.objExists(ofs_name):
        cmds.delete(ofs_name)

    if cmds.objExists(ctrl_name):
        cmds.delete(ctrl_name)

    ctrl = cmds.circle(
        n=ctrl_name,
        nr=(1, 0, 0),
        r=10
    )[0]

    ofs = cmds.group(
        em=True,
        n=ofs_name
    )

    aut = cmds.group(
        em=True,
        n=aut_name
    )

    aut = cmds.parent(
        aut,
        ofs
    )[0]

    ctrl = cmds.parent(
        ctrl,
        aut
    )[0]

    # Snap control to ORIGINAL animated joint,
    # not necessarily to the FK driver joint.
    tmp = cmds.parentConstraint(
        source_joint,
        ofs,
        mo=False
    )

    cmds.delete(tmp)

    return {
        "source_joint": source_joint,
        "driver_joint": driver_joint,

        # Keep this for backwards compatibility with old utilities.
        "joint": source_joint,

        "ctrl": ctrl_name,
        "ofs": ofs_name,
        "aut": aut_name
    }

def create_fk_constraints(rig, fk_links):
    """
    Creates FK behavior through constraints.

    Parent ctrl drives child aut:
        parent_ctrl -> child_ctrl_ofs

    This keeps all controls structurally flat inside family groups.
    """

    constraints = []

    for parent_slot, child_slot in fk_links:

        if parent_slot not in rig:
            continue

        if child_slot not in rig:
            continue

        parent_ctrl = genUtils.resolve_node(
            rig[parent_slot]["ctrl"]
        )

        child_ofs = genUtils.resolve_node(
            rig[child_slot]["ofs"]
        )

        pc_name = "{}_to_{}_parentConstraint".format(
            parent_slot,
            child_slot
        )

        sc_name = "{}_to_{}_scaleConstraint".format(
            parent_slot,
            child_slot
        )

        if cmds.objExists(pc_name):
            cmds.delete(pc_name)

        if cmds.objExists(sc_name):
            cmds.delete(sc_name)

        pc = cmds.parentConstraint(
            parent_ctrl,
            child_ofs,
            mo=True,
            n=pc_name
        )[0]

        sc = cmds.scaleConstraint(
            parent_ctrl,
            child_ofs,
            mo=True,
            n=sc_name
        )[0]

        constraints.append(pc)
        constraints.append(sc)

    return constraints


# BUILD FK RIG
def buildFKRig(char, fk_driver_map=None):

    if not cmds.objExists("ctrl_grp"):

        ctrl_grp = cmds.group(
            em=True,
            n="ctrl_grp"
        )

    else:

        ctrl_grp = "ctrl_grp"

    if fk_driver_map is None:
        fk_driver_map = {}
    rig = {}

    order = bipedConfig.FK_CTRL_ORDER


    for slot in order:

        source_joint = char.get(slot)

        if not source_joint:
            continue

        driver_joint = fk_driver_map.get(slot,source_joint)

        rig[slot] = create_ctrl_for_joint(source_joint,driver_joint=driver_joint)

        ctrlAes.color_ctrl_by_slot(rig[slot]["ctrl"],slot)

    # FK PARENTING

    fk_links = bipedConfig.FK_LINKS
    # FAMILY GROUPS

    family_FK_root_grp = genUtils.ensure_group(
        "FK_ctrls_grp",
        parent=ctrl_grp
    )

    family_FK_groups = {
        "c_spine_FK_ctrls_grp": genUtils.ensure_group("c_spine_FK_ctrls_grp", family_FK_root_grp),
        "l_arm_FK_ctrls_grp": genUtils.ensure_group("l_arm_FK_ctrls_grp", family_FK_root_grp),
        "r_arm_FK_ctrls_grp": genUtils.ensure_group("r_arm_FK_ctrls_grp", family_FK_root_grp),
        "l_leg_FK_ctrls_grp": genUtils.ensure_group("l_leg_FK_ctrls_grp", family_FK_root_grp),
        "r_leg_FK_ctrls_grp": genUtils.ensure_group("r_leg_FK_ctrls_grp", family_FK_root_grp),
        "misc_FK_ctrls_grp": genUtils.ensure_group("misc_FK_ctrls_grp", family_FK_root_grp),
    }

    # Parent every control OFS under its family group.
    # Controls remain structurally flat.
    for slot, data in rig.items():

        family_FK_grp_name = bipedConfig.get_family_for_slot(slot)

        family_FK_grp = family_FK_groups.get(
            family_FK_grp_name,
            family_FK_groups["misc_FK_ctrls_grp"]
        )

        try:
            ofs = genUtils.resolve_node(
                data["ofs"]
            )

            cmds.parent(
                ofs,
                family_FK_grp
            )
        except Exception:
            pass
    # FK BEHAVIOR THROUGH CONSTRAINTS
    fk_constraints = create_fk_constraints(rig,fk_links)

    FK_ctrl_count = len([
        key for key in rig.keys()
        if not key.startswith("_")
    ])

    print("Created {} FK controls.".format(FK_ctrl_count))

    return rig