import sys
import importlib

PROJECT_ROOT = r"E:\Work\3D\my_3D\KANEDA\Projects\Scripting\MaxMayaRigTranslator"

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

    
# IMPORTS

from Inputs import bipedScanner
from Creators import createFKIKchains
from Creators import createFKctrls
from Utilities import conectFKControlsToFKChains
from Utilities import bakeJointsToControls
from Utilities import connectControlsToJoints
from Creators import createIKctrls
from Utilities import bakeFKtoIKctrls
from Utilities import connectIKControlsToIKChains
from Utilities import connectFKIKblendToOriginal
from Utilities import clearOriginalJointAnimation



importlib.reload(bipedScanner)
importlib.reload(createFKIKchains)
importlib.reload(createFKctrls)
importlib.reload(bakeJointsToControls)
importlib.reload(connectControlsToJoints)
importlib.reload(conectFKControlsToFKChains)
importlib.reload(createIKctrls)
importlib.reload(bakeFKtoIKctrls)
importlib.reload(connectIKControlsToIKChains)

importlib.reload(connectFKIKblendToOriginal)

importlib.reload(clearOriginalJointAnimation)

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

    fk_driver_map = createFKIKchains.build_FK_driver_slot_map(chain_data)

    print("\n")
    print("=" * 80)
    print("STEP 3 - BUILDING FK CONTROLS")
    print("=" * 80)

    rig = createFKctrls.buildFKRig(
        char,
        fk_driver_map = fk_driver_map
    )

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
        remove_existing_joint_keys=False,
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
    print("STEP 8 - CONNECTING IK CONTROLS TO IK CHAINS")
    print("=" * 80)

    ik_chain_connections = connectIKControlsToIKChains.connect_IK_controls_to_IK_chains(
        ik_data,
        chain_data,
        rig,
        delete_existing=True,
        maintain_offset=False
    )
    cleared_original_keys = clearOriginalJointAnimation.clear_original_skeleton_animation(
        char
    )
    fk_chain_constraints = conectFKControlsToFKChains.connect_FK_controls_to_FK_driver_chains(rig)
    print("\n")
    print("=" * 80)
    print("STEP 9 - CONNECTING FK/IK CHAINS TO ORIGINAL SKELETON")
    print("=" * 80)

    FKIK_blend_connections = connectFKIKblendToOriginal.connect_FKIK_chains_to_original(
        char,
        chain_data,
        ik_data,
        rig,
        delete_existing=True,
        maintain_offset=False,
        attr_name="FKIK_blend"
    )

    print("\n")
    print("=" * 80)
    print("DONE")
    print("=" * 80)

    return {
        "character": char,
        "chain_data": chain_data,
        "rig": rig,
        "baked_ctrls": baked_ctrls,
        "driver_constraints": driver_constraints,
        "fk_chain_constraints": fk_chain_constraints,
        "ik_data": ik_data,
        "ik_bake_data": ik_bake_data,
        "ik_chain_connections": ik_chain_connections,
        "FKIK_blend_connections": FKIK_blend_connections
    }

result = main()