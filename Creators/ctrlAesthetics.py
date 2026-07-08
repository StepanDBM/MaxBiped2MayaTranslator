import maya.cmds as cmds
def color_ctrl_by_slot(ctrl, slot):
    """
    Colors controls based on scanner slot name.
    Example slots:
        l_upperarm
        r_hand
        pelvis
    """

    # Left side = blue
    if slot.startswith("l_"):
        set_object_color(
            ctrl,
            viewport_rgb=(0.1, 0.35, 1.0),
            outliner_rgb=(0.1, 0.35, 1.0)
        )

    # Right side = red
    elif slot.startswith("r_"):
        set_object_color(
            ctrl,
            viewport_rgb=(1.0, 0.15, 0.1),
            outliner_rgb=(1.0, 0.15, 0.1)
        )

    # Center = yellow/orange neutral
    else:
        set_object_color(
            ctrl,
            viewport_rgb=(1.0, 0.75, 0.1),
            outliner_rgb=(1.0, 0.75, 0.1)
        )

def set_object_color(obj, viewport_rgb=(1, 1, 1), outliner_rgb=None):
    """
    Colors an object in both viewport and outliner.
    Works on transform and its shape nodes.
    """

    if not cmds.objExists(obj):
        cmds.warning("Object does not exist: {}".format(obj))
        return

    # Viewport color on transform
    try:
        cmds.setAttr(obj + ".overrideEnabled", 1)
        cmds.setAttr(obj + ".overrideRGBColors", 1)
        cmds.setAttr(
            obj + ".overrideColorRGB",
            viewport_rgb[0],
            viewport_rgb[1],
            viewport_rgb[2]
        )
    except Exception:
        pass

    # Viewport color on shapes
    shapes = cmds.listRelatives(
        obj,
        shapes=True,
        fullPath=True
    ) or []

    for shape in shapes:
        try:
            cmds.setAttr(shape + ".overrideEnabled", 1)
            cmds.setAttr(shape + ".overrideRGBColors", 1)
            cmds.setAttr(
                shape + ".overrideColorRGB",
                viewport_rgb[0],
                viewport_rgb[1],
                viewport_rgb[2]
            )
        except Exception:
            pass

    # Outliner color
    if outliner_rgb is None:
        outliner_rgb = viewport_rgb

    try:
        cmds.setAttr(obj + ".useOutlinerColor", 1)
        cmds.setAttr(
            obj + ".outlinerColor",
            outliner_rgb[0],
            outliner_rgb[1],
            outliner_rgb[2]
        )
    except Exception:
        pass