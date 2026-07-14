# rigBuildPipeline.py

import importlib
import maya.cmds as cmds

PIPELINE_STEP_COUNT = 16


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

TRANSFORM_ANIM_ATTRS = [
    "translateX", "translateY", "translateZ",
    "rotateX", "rotateY", "rotateZ",
    "scaleX", "scaleY", "scaleZ"
]

ROTATE_ANIM_ATTRS = [
    "rotateX",
    "rotateY",
    "rotateZ"
]


def joint_has_any_transform_keys(joint):
    """
    Returns True if a joint has any transform animation keys / animCurves.
    """
    for attr in TRANSFORM_ANIM_ATTRS:

        plug = joint + "." + attr

        key_count = cmds.keyframe(
            plug,
            q=True,
            keyframeCount=True
        )

        if key_count and key_count > 0:
            return True


        incoming_anim = cmds.listConnections(
            plug,
            source=True,
            destination=False,
            type="animCurve"
        ) or []

        if incoming_anim:
            return True
    return False


def joint_has_meaningful_rotation_keys(
    joint,
    min_rotation_degrees=1.0
):
    """
    Returns True only if a joint has rotation keys where at least one
    rotation channel changes more than min_rotation_degrees.

    This filters out static FBXs that have useless one-frame/default keys.
    """

    for attr in ROTATE_ANIM_ATTRS:

        plug = joint + "." + attr

        values = cmds.keyframe(
            plug,
            q=True,
            valueChange=True
        ) or []


        if len(values) < 2:
            continue

        min_value = min(values)
        max_value = max(values)

        delta = abs(max_value - min_value)

        if delta > min_rotation_degrees:
            print(
                "Meaningful rotation detected on {}.{} | delta: {}".format(
                    joint,
                    attr,
                    delta
                )
            )
            return True
    return False


def delete_all_joint_animation_keys(
    joints,
    start=None,
    end=None,
    delete_anim_curves=True
):
    """
    Deletes transform animation keys from all given joints.

    Used when the source FBX has keys, but they are not meaningful animation.
    """

    deleted_data = {}

    for joint in joints:

        kwargs = {
            "attribute": TRANSFORM_ANIM_ATTRS,
            "option": "keys"
        }

        if start is not None and end is not None:
            kwargs["time"] = (
                int(start),
                int(end)
            )

        try:
            cmds.cutKey(
                joint,
                **kwargs
            )

        except Exception:
            pass

        deleted_curves = []

        if delete_anim_curves:
            for attr in TRANSFORM_ANIM_ATTRS:
                plug = joint + "." + attr
                anim_curves = cmds.listConnections(
                    plug,
                    source=True,
                    destination=False,
                    type="animCurve"
                ) or []
                for curve in anim_curves:
                    cmds.delete(curve)
                    deleted_curves.append(curve)
        deleted_data[joint] = deleted_curves

    print(
        "Deleted non-meaningful joint animation from {} joints.".format(
            len(deleted_data)
        )
    )


def scene_has_joint_animation(
    char=None,
    min_rotation_degrees=1.0
):
    """
    Returns True only if the scene has meaningful joint animation.

    Meaningful animation rule:
        At least one joint must rotate more than min_rotation_degrees
        on at least one rotation channel.

    If keys exist but no joint rotates enough:
        deletes all transform keys from all joints
        returns False.
    """

    joints = cmds.ls(
        type="joint",
        long=True
    ) or []

    any_keys_found = False

    for joint in joints:

        if joint_has_any_transform_keys(joint):
            any_keys_found = True

        if joint_has_meaningful_rotation_keys(
            joint,
            min_rotation_degrees=min_rotation_degrees
        ):
            print("=" * 80)
            print("SOURCE ANIMATION CHECK")
            print("Meaningful source joint animation detected.")
            print("=" * 80)

            return True

    if any_keys_found:

        print("=" * 80)
        print("SOURCE ANIMATION CHECK")
        print(
            "Joint keys were found, but no joint rotated more than {} degree(s).".format(
                min_rotation_degrees
            )
        )
        print("Treating source as NO ANIMATION and deleting useless joint keys.")
        print("=" * 80)

        start = None
        end = None

        if char:
            start = char.get("startFrame")
            end = char.get("endFrame")

        delete_all_joint_animation_keys(
            joints,
            start=start,
            end=end,
            delete_anim_curves=True
        )

    else:

        print("=" * 80)
        print("SOURCE ANIMATION CHECK")
        print("No source joint animation keys detected.")
        print("=" * 80)

    return False

def run_backend_pipeline(progress_callback=None):
    """
    Runs the full rig conversion backend on the current Maya scene.

    This function is UI-safe:
        - It prints normal backend logs.
        - If progress_callback is provided, it reports each step to the UI.
    """
    from Utilities import genUtils as genU

    from Inputs import bipedScanner

    from Creators import createFKIKchains
    from Creators import createFKctrls
    from Creators import createIKctrls
    from Creators import createLimbEndFKRig
    from Creators import createFootFKIKchains
    from Creators import createExtraFKRig

    from Utilities import bakeJointsToControls
    from Utilities import bakeFKtoIKctrls
    from Utilities import connectControlsToJoints
    from Utilities import conectFKControlsToFKChains
    from Utilities import connectIKControlsToIKChains
    from Utilities import clearOriginalJointAnimation
    from Utilities import connectFKIKblendToOriginal
    from Utilities import connectIKFollowSpaces
    from Utilities import connectFootIKEnds
    from Utilities import connectFootFKIKEndsToOriginal

    importlib.reload(genU)

    importlib.reload(bipedScanner)

    importlib.reload(createFKIKchains)
    importlib.reload(createFKctrls)
    importlib.reload(createIKctrls)
    importlib.reload(createLimbEndFKRig)
    importlib.reload(createFootFKIKchains)
    importlib.reload(createExtraFKRig)

    importlib.reload(bakeJointsToControls)
    importlib.reload(bakeFKtoIKctrls)
    importlib.reload(connectControlsToJoints)
    importlib.reload(conectFKControlsToFKChains)
    importlib.reload(connectIKControlsToIKChains)
    importlib.reload(clearOriginalJointAnimation)
    importlib.reload(connectFKIKblendToOriginal)
    importlib.reload(connectIKFollowSpaces)
    importlib.reload(connectFootIKEnds)
    importlib.reload(connectFootFKIKEndsToOriginal)

    # --------------------------------------------------
    # STEP 1
    # --------------------------------------------------

    report_step(
        progress_callback,
        "STEP 1 - SCANNING CHARACTER"
    )

    char = bipedScanner.scanCharacter()

    # --------------------------------------------------
    # STEP 1.5
    # --------------------------------------------------
    
    source_has_animation = scene_has_joint_animation()
    print("=" * 80)
    print("SOURCE ANIMATION CHECK")
    print("Source has animation: {}".format(source_has_animation))
    print("=" * 80)

    report_step(progress_callback,
        "STEP 1 - SCANNING CHARACTER"
    )
    # --------------------------------------------------
    # STEP 2
    # --------------------------------------------------

    report_step(progress_callback,
        "STEP 2 - CREATING FK/IK DRIVER CHAINS"
    )

    chain_data = createFKIKchains.create_FKIK_driver_chains(
        char,
        delete_existing=True,
        build_at_frame=char.get("startFrame")
    )

    foot_end_chain_data = createFootFKIKchains.create_foot_FKIK_end_chains(
        char,
        chain_data,
        delete_existing=True
    )

    chain_data.update(
        foot_end_chain_data
    )

    FK_driver_map = createFKIKchains.build_FK_driver_slot_map(
        chain_data
    )

    # --------------------------------------------------
    # STEP 3
    # --------------------------------------------------

    report_step(progress_callback,
        "STEP 3 - BUILDING FK CONTROLS"
    )

    rig = createFKctrls.buildFKRig(
        char,
        fk_driver_map=FK_driver_map
    )

    # --------------------------------------------------
    # STEP 4
    # --------------------------------------------------

    report_step(progress_callback,
        "STEP 4 - CREATING LIMB-END FK CONTROLS"
    )

    limb_end_FK_data = createLimbEndFKRig.create_limb_end_FK_controls(
        char,
        rig,
        delete_existing=True
    )
    # STEP 5

    report_step(progress_callback,
        "STEP 5 - CREATING EXTRA FK CONTROLS"
    )

    extra_FK_data = createExtraFKRig.create_extra_FK_controls(
        char,
        rig,
        delete_existing=True
    )
    # --------------------------------------------------
    # STEP 6
    # --------------------------------------------------

    report_step(progress_callback,
        "STEP 6 - BAKING JOINT ANIMATION TO FK CONTROLS"
    )

    if source_has_animation:
        baked_ctrls = bakeJointsToControls.bake_joints_to_fk_controls(
            char,
            rig
        )
    else:
        print("Skipping FK bake: source FBX has no detected joint animation.")
        baked_ctrls = {}
    # --------------------------------------------------
    # STEP 7
    # --------------------------------------------------

    report_step(progress_callback,
        "STEP 7 - CONNECTING CORE FK CONTROLS TO ORIGINAL JOINTS"
    )

    driver_constraints = connectControlsToJoints.connect_fk_controls_to_joints(
        char,
        rig,
        remove_existing_joint_keys=False,
        create_scale_constraints=False,
        maintain_offset=False
    )

    # --------------------------------------------------
    # STEP 8
    # --------------------------------------------------

    report_step(progress_callback,
        "STEP 8 - CREATING IK CONTROLS"
    )

    IK_data = createIKctrls.create_IK_controls(
        char,
        rig
    )

    # --------------------------------------------------
    # STEP 9
    # --------------------------------------------------

    report_step(progress_callback,
        "STEP 9 - BAKING FK MOTION TO IK CONTROLS"
    )

    if source_has_animation:
        IK_bake_data = bakeFKtoIKctrls.bake_FK_to_IK_controls(
            char,
            rig,
            IK_data
        )

        genU.reset_time_to_start_frame(char, fallback_frame=0)
    else:
        print("Skipping IK bake: source FBX has no detected joint animation.")
        IK_bake_data = {}
    # --------------------------------------------------
    # STEP 10
    # --------------------------------------------------

    report_step(progress_callback,
        "STEP 10 - CONNECTING IK CONTROLS TO IK CHAINS"
    )

    IK_chain_connections = connectIKControlsToIKChains.connect_IK_controls_to_IK_chains(
        IK_data,
        chain_data,
        rig,
        delete_existing=True,
        maintain_offset=False
    )
    # --------------------------------------------------
    # STEP 11
    # --------------------------------------------------

    report_step(progress_callback,
        "STEP 11 - CONNECTING FOOT-END IK DRIVERS"
    )

    foot_IK_end_connections = connectFootIKEnds.connect_foot_IK_ends(
        chain_data,
        IK_data,
        maintain_offset=True
    )

    # --------------------------------------------------
    # STEP 12
    # --------------------------------------------------

    report_step(progress_callback,
        "STEP 12 - CLEARING ORIGINAL SKELETON ANIMATION"
    )

    if source_has_animation:

        clear_slots = clearOriginalJointAnimation.get_original_animation_slots()

        for slot in limb_end_FK_data.get("slots", []):
            if slot not in clear_slots:
                clear_slots.append(slot)

        for slot in extra_FK_data.get("slots", []):
            if slot not in clear_slots:
                clear_slots.append(slot)

        cleared_original_keys = clearOriginalJointAnimation.clear_original_skeleton_animation(
            char,
            slots=clear_slots
        )

    else:
        print("Skipping original skeleton animation cleanup: source FBX has no detected joint animation.")
        cleared_original_keys = {}

    # --------------------------------------------------
    # STEP 13
    # --------------------------------------------------

    report_step(progress_callback,
        "STEP 13 - CONNECTING FK CONTROLS TO FK CHAINS"
    )

    FK_chain_constraints = conectFKControlsToFKChains.connect_FK_controls_to_FK_driver_chains(
        rig
    )

    # --------------------------------------------------
    # STEP 14
    # --------------------------------------------------

    report_step(progress_callback,
        "STEP 14 - CONNECTING FK/IK CHAINS TO ORIGINAL SKELETON"
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
    # --------------------------------------------------
    # STEP 15
    # --------------------------------------------------

    report_step(progress_callback,
        "STEP 15 - CONNECTING FOOT-END FK/IK TO ORIGINAL TOE JOINTS"
    )

    foot_FKIK_end_connections = connectFootFKIKEndsToOriginal.connect_foot_FKIK_ends_to_original(
        char,
        rig,
        chain_data,
        FKIK_blend_connections,
        delete_existing=True,
        maintain_offset=False
    )

    # --------------------------------------------------
    # STEP 16
    # --------------------------------------------------

    report_step(progress_callback,
        "STEP 16 - CONNECTING IK FOLLOW SPACES"
    )

    IK_follow_connections = connectIKFollowSpaces.connect_IK_follow_spaces(
        rig,
        IK_data,
        FKIK_blend_connections,
        maintain_offset=True
    )
    genU.kick_offset_groups_with_undo(
        amount=1.0,
        patterns=[
            "*Hand*_FK_ctrl_ofs",
            "*Finger*_FK_ctrl_ofs",
            "*Thumb*_FK_ctrl_ofs",
            "*Index*_FK_ctrl_ofs",
            "*Middle*_FK_ctrl_ofs",
            "*Ring*_FK_ctrl_ofs",
            "*Pinky*_FK_ctrl_ofs"
        ]
    )
    print("\n")
    print("=" * 80)
    print("PIPELINE DONE")
    print("=" * 80)

    return {
        "character": char,
        "chain_data": chain_data,
        "foot_end_chain_data": foot_end_chain_data,
        "limb_end_FK_data": limb_end_FK_data,

        "rig": rig,
        "baked_ctrls": baked_ctrls,

        "driver_constraints": driver_constraints,
        "FK_chain_constraints": FK_chain_constraints,

        "IK_data": IK_data,
        "IK_bake_data": IK_bake_data,
        "IK_chain_connections": IK_chain_connections,

        "foot_IK_end_connections": foot_IK_end_connections,

        "cleared_original_keys": cleared_original_keys,

        "FKIK_blend_connections": FKIK_blend_connections,
        "foot_FKIK_end_connections": foot_FKIK_end_connections,

        "IK_follow_connections": IK_follow_connections
    }


def main():
    """
    Convenience function for running manually without UI.
    """

    return run_backend_pipeline(progress_callback=None)