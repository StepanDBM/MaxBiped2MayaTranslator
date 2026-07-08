import maya.cmds as cmds

# BASIC HELPERS
def unlock_transform_attrs(obj):
    """
    Makes sure transform attributes are keyable/unlocked
    before baking animation onto the control.
    """

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


def clear_existing_keys(obj, start, end):
    """
    Removes previous keys from the control inside the bake range.
    Useful while testing repeatedly.
    """

    attrs = [
        "translateX", "translateY", "translateZ",
        "rotateX", "rotateY", "rotateZ"
    ]

    try:
        cmds.cutKey(
            obj,
            time=(start, end),
            attribute=attrs,
            option="keys"
        )
    except Exception:
        pass


# MAIN BAKE FUNCTION
def bake_joints_to_fk_controls(
    char,
    rig,
    start=None,
    end=None,
    sample_by=1,
    clear_keys=True
):
    """
    Bakes existing skeleton/joint animation onto FK controls.

    Source:
        legacy animated joints

    Target:
        FK controls

    This does NOT make controls drive the joints yet, only
    copies/bakes animation to the controls.
    """

    if start is None:
        start = char.get(
            "startFrame",
            cmds.playbackOptions(q=True, min=True)
        )

    if end is None:
        end = char.get(
            "endFrame",
            cmds.playbackOptions(q=True, max=True)
        )

    start = int(start)
    end = int(end)

    """
    print("=" * 80)
    print("BAKING JOINT ANIMATION TO FK CONTROLS")
    print("Frame range: {} -> {}".format(start, end))
    print("=" * 80)
    """

    tmp_constraints = []
    baked_ctrls = []

    # Create temporary constraints:
    # joint drives ctrl
    for slot, data in rig.items():
    
        # Skip metadata / non-control entries
        if slot.startswith("_"):
            continue

        if not isinstance(data, dict):
            continue

        joint = data.get("joint")
        ctrl = data.get("ctrl")

        if not joint or not ctrl:
            cmds.warning("Skipping {}: missing joint or ctrl.".format(slot))
            continue

        if not cmds.objExists(joint):
            cmds.warning("Skipping {}: joint does not exist: {}".format(slot, joint))
            continue

        if not cmds.objExists(ctrl):
            cmds.warning("Skipping {}: ctrl does not exist: {}".format(slot, ctrl))
            continue

        unlock_transform_attrs(ctrl)

        if clear_keys:
            clear_existing_keys(
                ctrl,
                start,
                end
            )

        tmp_name = "TMP_{}_joint_to_ctrl_PC".format(slot)

        if cmds.objExists(tmp_name):
            cmds.delete(tmp_name)

        constraint = cmds.parentConstraint(
            joint,
            ctrl,
            mo=False,
            n=tmp_name
        )[0]

        tmp_constraints.append(constraint)
        baked_ctrls.append(ctrl)

        print("Constrained joint -> ctrl: {} -> {}".format(joint, ctrl))

    if not baked_ctrls:
        raise RuntimeError("No FK controls found to bake.")

    # Bake controls
    cmds.bakeResults(
        baked_ctrls,
        time=(start, end),
        simulation=True,
        sampleBy=sample_by,
        disableImplicitControl=True,
        preserveOutsideKeys=True,
        sparseAnimCurveBake=False,
        removeBakedAttributeFromLayer=False,
        removeBakedAnimFromLayer=False,
        bakeOnOverrideLayer=False,
        minimizeRotation=True,
        attribute=[
            "translateX", "translateY", "translateZ",
            "rotateX", "rotateY", "rotateZ"
        ]
    )

    # Delete temporary constraints
    for constraint in tmp_constraints:
        if cmds.objExists(constraint):
            cmds.delete(constraint)

    print("=" * 80)
    print("BAKE COMPLETE")
    print("Baked {} FK controls.".format(len(baked_ctrls)))
    print("=" * 80)

    return baked_ctrls