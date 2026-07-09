import sys
import importlib

PROJECT_ROOT = r"E:\Work\3D\my_3D\KANEDA\Projects\Scripting\MaxMayaRigTranslator"

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

    
# IMPORTS

from Inputs import bipedScanner
from Creators import createFKIKchains
from Creators import createFKctrls
from Utilities import bakeJointsToControls
from Utilities import connectControlsToJoints
from Creators import createIKctrls
from Utilities import bakeFKtoIKctrls


importlib.reload(bipedScanner)
importlib.reload(createFKIKchains)
importlib.reload(createFKctrls)
importlib.reload(bakeJointsToControls)
importlib.reload(connectControlsToJoints)
importlib.reload(createIKctrls)
importlib.reload(bakeFKtoIKctrls)


def main():

    print("=" * 80)
    print("STEP 1 - SCANNING CHARACTER")
    print("=" * 80)

    char = bipedScanner.scanCharacter()

    print("\n")
    print("=" * 80)
    print("STEP 2 - CREATING FK/IK DRIVER CHAINS")
    print("=" * 80)

    chain_data = createFKIKchains.create_FKIK_driver_chains(
        char,
        delete_existing=True,
        build_at_frame=char.get("startFrame")
    )

    print("\n")
    print("=" * 80)
    print("STEP 3 - BUILDING FK CONTROLS")
    print("=" * 80)

    rig = createFKctrls.buildFKRig(char)

    print("\n")
    print("=" * 80)
    print("STEP 4 - BAKING JOINT ANIMATION TO FK CONTROLS")
    print("=" * 80)

    baked_ctrls = bakeJointsToControls.bake_joints_to_fk_controls(
        char,
        rig
    )

    print("\n")
    print("=" * 80)
    print("STEP 5 - CONNECTING FK CONTROLS TO JOINTS")
    print("=" * 80)

    driver_constraints = connectControlsToJoints.connect_fk_controls_to_joints(
        char,
        rig,
        remove_existing_joint_keys=True,
        create_scale_constraints=False,
        maintain_offset=False
    )

    print("\n")
    print("=" * 80)
    print("STEP 6 - CREATING IK CONTROLS")
    print("=" * 80)

    ik_data = createIKctrls.create_IK_controls(
        char,
        rig
    )

    print("\n")
    print("=" * 80)
    print("STEP 7 - BAKING FK MOTION TO IK CONTROLS")
    print("=" * 80)

    ik_bake_data = bakeFKtoIKctrls.bake_FK_to_IK_controls(
        char,
        rig,
        ik_data
    )

    print("\n")
    print("=" * 80)
    print("DONE")
    print("=" * 80)

    return {
        "character": char,
        "rig": rig,
        "baked_ctrls": baked_ctrls,
        "driver_constraints": driver_constraints,
        "ik_data": ik_data,
        "ik_bake_data": ik_bake_data
    }


result = main()