# rigBuildPipeline.py

import importlib


PIPELINE_STEP_COUNT = 12


def report_step(progress_callback, label):
    """
    Prints a nice backend separator and reports progress to the UI.
    """

    print("\n")
    print("=" * 80)
    print(label)
    print("=" * 80)

    if progress_callback:
        progress_callback(label)


def run_backend_pipeline(progress_callback=None):
    """
    Runs the full rig conversion backend on the current Maya scene.

    This function is UI-safe:
        - It prints normal backend logs.
        - If progress_callback is provided, it reports each step to the UI.
    """

    from Inputs import bipedScanner

    from Creators import createFKIKchains
    from Creators import createFKctrls
    from Creators import createIKctrls

    from Utilities import bakeJointsToControls
    from Utilities import bakeFKtoIKctrls
    from Utilities import connectControlsToJoints
    from Utilities import conectFKControlsToFKChains
    from Utilities import connectIKControlsToIKChains
    from Utilities import clearOriginalJointAnimation
    from Utilities import connectFKIKblendToOriginal
    from Utilities import connectIKFollowSpaces

    importlib.reload(bipedScanner)

    importlib.reload(createFKIKchains)
    importlib.reload(createFKctrls)
    importlib.reload(createIKctrls)

    importlib.reload(bakeJointsToControls)
    importlib.reload(bakeFKtoIKctrls)
    importlib.reload(connectControlsToJoints)
    importlib.reload(conectFKControlsToFKChains)
    importlib.reload(connectIKControlsToIKChains)
    importlib.reload(clearOriginalJointAnimation)
    importlib.reload(connectFKIKblendToOriginal)
    importlib.reload(connectIKFollowSpaces)

    # STEP 1

    report_step(
        progress_callback,
        "STEP 1 - SCANNING CHARACTER"
    )

    char = bipedScanner.scanCharacter()

    # STEP 2

    report_step(
        progress_callback,
        "STEP 2 - CREATING FK/IK DRIVER CHAINS"
    )

    chain_data = createFKIKchains.create_FKIK_driver_chains(
        char,
        delete_existing=True,
        build_at_frame=char.get("startFrame")
    )

    FK_driver_map = createFKIKchains.build_FK_driver_slot_map(
        chain_data
    )

    # STEP 3

    report_step(
        progress_callback,
        "STEP 3 - BUILDING FK CONTROLS"
    )

    rig = createFKctrls.buildFKRig(
        char,
        fk_driver_map=FK_driver_map
    )

    # STEP 4

    report_step(
        progress_callback,
        "STEP 4 - BAKING JOINT ANIMATION TO FK CONTROLS"
    )

    baked_ctrls = bakeJointsToControls.bake_joints_to_fk_controls(
        char,
        rig
    )

    # STEP 5

    report_step(
        progress_callback,
        "STEP 5 - CONNECTING CORE FK CONTROLS TO ORIGINAL JOINTS"
    )

    driver_constraints = connectControlsToJoints.connect_fk_controls_to_joints(
        char,
        rig,
        remove_existing_joint_keys=False,
        create_scale_constraints=False,
        maintain_offset=False
    )

    # STEP 6

    report_step(
        progress_callback,
        "STEP 6 - CREATING IK CONTROLS"
    )

    IK_data = createIKctrls.create_IK_controls(
        char,
        rig
    )

    # STEP 7

    report_step(
        progress_callback,
        "STEP 7 - BAKING FK MOTION TO IK CONTROLS"
    )

    IK_bake_data = bakeFKtoIKctrls.bake_FK_to_IK_controls(
        char,
        rig,
        IK_data
    )

    # STEP 8

    report_step(
        progress_callback,
        "STEP 8 - CONNECTING IK CONTROLS TO IK CHAINS"
    )

    IK_chain_connections = connectIKControlsToIKChains.connect_IK_controls_to_IK_chains(
        IK_data,
        chain_data,
        rig,
        delete_existing=True,
        maintain_offset=False
    )

    # STEP 9

    report_step(
        progress_callback,
        "STEP 9 - CLEARING ORIGINAL SKELETON ANIMATION"
    )

    cleared_original_keys = clearOriginalJointAnimation.clear_original_skeleton_animation(
        char
    )

    # STEP 10

    report_step(
        progress_callback,
        "STEP 10 - CONNECTING FK CONTROLS TO FK CHAINS"
    )

    FK_chain_constraints = conectFKControlsToFKChains.connect_FK_controls_to_FK_driver_chains(
        rig
    )

    # STEP 11

    report_step(
        progress_callback,
        "STEP 11 - CONNECTING FK/IK CHAINS TO ORIGINAL SKELETON"
    )

    FKIK_blend_connections = connectFKIKblendToOriginal.connect_FKIK_chains_to_original(
        char,
        chain_data,
        IK_data,
        rig,
        delete_existing=True,
        maintain_offset=False,
        attr_name="FKIK_blend"
    )

    # STEP 12

    report_step(
        progress_callback,
        "STEP 12 - CONNECTING IK FOLLOW SPACES"
    )

    IK_follow_connections = connectIKFollowSpaces.connect_IK_follow_spaces(
        rig,
        IK_data,
        FKIK_blend_connections,
        maintain_offset=True
    )

    print("\n")
    print("=" * 80)
    print("PIPELINE DONE")
    print("=" * 80)

    return {
        "character": char,
        "chain_data": chain_data,
        "rig": rig,
        "baked_ctrls": baked_ctrls,
        "driver_constraints": driver_constraints,
        "FK_chain_constraints": FK_chain_constraints,
        "IK_data": IK_data,
        "IK_bake_data": IK_bake_data,
        "IK_chain_connections": IK_chain_connections,
        "cleared_original_keys": cleared_original_keys,
        "FKIK_blend_connections": FKIK_blend_connections,
        "IK_follow_connections": IK_follow_connections
    }


def main():
    """
    Convenience function for running manually without UI.
    """

    return run_backend_pipeline(
        progress_callback=None
    )