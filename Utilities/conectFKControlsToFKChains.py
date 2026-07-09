import maya.cmds as cmds
import importlib

import Utilities.genUtils as genUtils
from Utilities.Config import bipedConfig

importlib.reload(genUtils)
importlib.reload(bipedConfig)


def unlock_transform_attrs(obj):

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


def connect_FK_controls_to_FK_driver_chains(rig):
    """
    Connects limb FK controls to FK driver joints.

    This does NOT connect core/spine controls to the original skeleton.
    This only handles limb slots that have driver_joint data.
    """

    constraints = []

    print("=" * 80)
    print("CONNECTING FK CONTROLS TO FK DRIVER CHAINS")
    print("=" * 80)

    for slot, data in rig.items():

        if slot.startswith("_"):
            continue

        if not isinstance(data, dict):
            continue

        if not bipedConfig.is_limb_slot(slot):
            continue

        ctrl = data.get("ctrl")
        driver_joint = data.get("driver_joint")

        if not ctrl or not driver_joint:
            cmds.warning(
                "Skipping {}: missing ctrl or driver_joint.".format(slot)
            )
            continue

        ctrl = genUtils.resolve_node(ctrl)
        driver_joint = genUtils.resolve_node(driver_joint)

        unlock_transform_attrs(driver_joint)

        pc_name = slot + "_FK_ctrl_to_FK_chain_parentConstraint"

        if cmds.objExists(pc_name):
            cmds.delete(pc_name)

        pc = cmds.parentConstraint(
            ctrl,
            driver_joint,
            mo=False,
            n=pc_name
        )[0]

        constraints.append(pc)

        print(
            "Connected FK ctrl -> FK chain: {} -> {}".format(
                genUtils.pretty_node_name(ctrl),
                genUtils.pretty_node_name(driver_joint)
            )
        )

    print("=" * 80)
    print("FK CONTROL TO FK DRIVER CHAIN CONNECTION COMPLETE")
    print("Created {} constraints.".format(len(constraints)))
    print("=" * 80)

    return constraints
