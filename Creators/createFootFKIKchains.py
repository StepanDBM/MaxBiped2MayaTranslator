import maya.cmds as cmds
import importlib

from Utilities.Config import bipedConfig
import Utilities.genUtils as genUtils
from Creators import createFKIKchains

importlib.reload(bipedConfig)
importlib.reload(genUtils)
importlib.reload(createFKIKchains)


def parent_driver_to_existing_foot(driver_joint, parent_driver):
    """
    Parents a toe driver joint under the existing foot FK/IK driver joint.
    """

    driver_joint = genUtils.resolve_node(driver_joint)
    parent_driver = genUtils.resolve_node(parent_driver)

    driver_joint = cmds.parent(
        driver_joint,
        parent_driver,
        absolute=True
    )[0]

    return driver_joint


def create_foot_FKIK_end_chains(
    char,
    chain_data,
    delete_existing=True
):
    """
    Creates FK/IK toe driver joints for foot-end FKIK.

    This does NOT create IK handles.
    This does NOT change the main leg IK chain.

    It creates:
        l_toe_FK_jnt under l_foot_FK_jnt
        l_toe_IK_jnt under l_foot_IK_jnt
    """
    auto_transform_snapshot = genUtils.get_auto_transform_nodes()
    print("=" * 80)
    print("CREATING FOOT-END FK/IK DRIVER CHAINS")
    print("=" * 80)

    result = {}

    for foot_end_name, data in bipedConfig.FOOT_FKIK_ENDS.items():

        parent_limb = data["parent_limb"]
        root_slot = data["root_slot"]
        end_slot = data["end_slot"]

        if parent_limb not in chain_data:
            cmds.warning(
                "Skipping {}: missing parent limb chain data {}".format(
                    foot_end_name,
                    parent_limb
                )
            )
            continue

        source_toe = char.get(
            end_slot
        )

        if not source_toe:
            cmds.warning(
                "Skipping {}: missing source toe slot {}".format(
                    foot_end_name,
                    end_slot
                )
            )
            continue

        parent_FK_foot = chain_data[parent_limb]["FK_chain"][-1]
        parent_IK_foot = chain_data[parent_limb]["IK_chain"][-1]

        FK_toe = createFKIKchains.duplicate_source_joint_as_driver(
            source_toe,
            "FK"
        )

        IK_toe = createFKIKchains.duplicate_source_joint_as_driver(
            source_toe,
            "IK"
        )

        FK_toe = parent_driver_to_existing_foot(
            FK_toe,
            parent_FK_foot
        )

        IK_toe = parent_driver_to_existing_foot(
            IK_toe,
            parent_IK_foot
        )

        result[foot_end_name] = {
            "system_type": "foot_end",
            "parent_limb": parent_limb,
            "root_slot": root_slot,
            "slots": [
                end_slot
            ],
            "FK_chain": [
                FK_toe.split("|")[-1]
            ],
            "IK_chain": [
                IK_toe.split("|")[-1]
            ],
        }

        print(
            "Created foot-end FK/IK chain: {} -> {}".format(
                foot_end_name,
                end_slot
            )
        )
    genUtils.cleanup_auto_transform_nodes(before=auto_transform_snapshot)
    print("=" * 80)
    print("FOOT-END FK/IK DRIVER CHAIN CREATION COMPLETE")
    print("Created {} foot-end systems.".format(len(result)))
    print("=" * 80)

    return result