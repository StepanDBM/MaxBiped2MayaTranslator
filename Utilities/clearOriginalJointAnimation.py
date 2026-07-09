import maya.cmds as cmds
import importlib

from Utilities.Config import bipedConfig
import Utilities.genUtils as genUtils

importlib.reload(bipedConfig)
importlib.reload(genUtils)


TRANSFORM_ATTRS = [
    "translateX", "translateY", "translateZ",
    "rotateX", "rotateY", "rotateZ",
    "scaleX", "scaleY", "scaleZ"
]


def get_original_animation_slots():
    """
    Slots whose original skeleton animation should be removable
    after baking to controls.
    """

    slots = list(bipedConfig.FK_CTRL_ORDER)

    # Optional toes if they exist in the scanned char.
    extra = [
        "l_toe",
        "r_toe"
    ]

    for slot in extra:
        if slot not in slots:
            slots.append(slot)

    return slots


def remove_anim_curves_from_attr(node, attr):
    """
    Deletes incoming animCurve nodes connected to node.attr.
    """

    plug = node + "." + attr

    if not cmds.objExists(plug):
        return []

    anim_curves = cmds.listConnections(
        plug,
        source=True,
        destination=False,
        type="animCurve"
    ) or []

    deleted = []

    for curve in anim_curves:

        if cmds.objExists(curve):
            try:
                cmds.delete(curve)
                deleted.append(curve)
            except Exception as e:
                cmds.warning(
                    "Could not delete animCurve {} on {}: {}".format(
                        curve,
                        plug,
                        e
                    )
                )

    return deleted


def cut_keys_on_joint(joint, start=None, end=None):
    """
    Cuts keys from transform attrs.
    """

    kwargs = {
        "attribute": TRANSFORM_ATTRS,
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


def clear_joint_animation(
    joint,
    start=None,
    end=None,
    delete_anim_curves=True
):
    """
    Removes animation from one original deform joint.
    """

    joint = genUtils.resolve_node(joint)

    cut_keys_on_joint(
        joint,
        start=start,
        end=end
    )

    deleted_curves = []

    if delete_anim_curves:

        for attr in TRANSFORM_ATTRS:

            deleted_curves.extend(
                remove_anim_curves_from_attr(
                    joint,
                    attr
                )
            )

    return deleted_curves


def clear_original_skeleton_animation(
    char,
    slots=None,
    start=None,
    end=None,
    delete_anim_curves=True
):
    """
    Clears animation from the original imported/deform skeleton.

    Run this only AFTER:
        - FK controls have been baked
        - IK controls have been baked, if they still depend on original joint motion

    This does not delete joints.
    It only removes animation curves / keys.
    """

    if slots is None:
        slots = get_original_animation_slots()

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

    print("=" * 80)
    print("CLEARING ORIGINAL SKELETON ANIMATION")
    print("Frame range: {} -> {}".format(int(start), int(end)))
    print("=" * 80)

    cleared = {}

    for slot in slots:

        joint = char.get(slot)

        if not joint:
            continue

        if not cmds.objExists(joint):
            cmds.warning(
                "Skipping {}: joint does not exist: {}".format(
                    slot,
                    joint
                )
            )
            continue

        deleted_curves = clear_joint_animation(
            joint,
            start=start,
            end=end,
            delete_anim_curves=delete_anim_curves
        )

        cleared[slot] = {
            "joint": joint,
            "deleted_anim_curves": deleted_curves
        }

        print(
            "Cleared original joint animation: {}".format(
                genUtils.pretty_node_name(joint)
            )
        )

    print("=" * 80)
    print("ORIGINAL SKELETON ANIMATION CLEANUP COMPLETE")
    print("Cleared {} joints.".format(len(cleared)))
    print("=" * 80)

    return cleared