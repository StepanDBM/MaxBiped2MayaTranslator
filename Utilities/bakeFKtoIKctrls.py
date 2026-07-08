import maya.cmds as cmds
import Utilities.genUtils as genUtils

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


def clear_keys(obj, start, end):

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


def get_world_pos(obj):

    obj = genUtils.resolve_node(obj)

    return cmds.xform(
        obj,
        q=True,
        ws=True,
        t=True
    )


def vec_add(a, b):
    return [
        a[0] + b[0],
        a[1] + b[1],
        a[2] + b[2]
    ]


def vec_sub(a, b):
    return [
        a[0] - b[0],
        a[1] - b[1],
        a[2] - b[2]
    ]


def vec_mul(v, scalar):
    return [
        v[0] * scalar,
        v[1] * scalar,
        v[2] * scalar
    ]


def vec_dot(a, b):
    return (
        a[0] * b[0] +
        a[1] * b[1] +
        a[2] * b[2]
    )


def vec_length(v):
    return max(
        (
            v[0] ** 2 +
            v[1] ** 2 +
            v[2] ** 2
        ) ** 0.5,
        0.00001
    )


def vec_normalize(v):

    l = vec_length(v)

    return [
        v[0] / l,
        v[1] / l,
        v[2] / l
    ]


def calculate_pole_vector_position(start_obj, mid_obj, end_obj, distance_multiplier=1.5):

    start = get_world_pos(start_obj)
    mid = get_world_pos(mid_obj)
    end = get_world_pos(end_obj)

    start_to_end = vec_sub(end, start)
    start_to_mid = vec_sub(mid, start)

    line_length = vec_length(start_to_end)

    projection_amount = vec_dot(
        start_to_mid,
        start_to_end
    ) / (line_length ** 2)

    projected = vec_add(
        start,
        vec_mul(
            start_to_end,
            projection_amount
        )
    )

    pole_dir = vec_sub(
        mid,
        projected
    )

    if vec_length(pole_dir) < 0.001:
        pole_dir = [0, 0, 1]

    pole_dir = vec_normalize(pole_dir)

    upper_len = vec_length(
        vec_sub(mid, start)
    )

    lower_len = vec_length(
        vec_sub(end, mid)
    )

    pole_distance = (
        upper_len + lower_len
    ) * 0.5 * distance_multiplier

    return vec_add(
        mid,
        vec_mul(
            pole_dir,
            pole_distance
        )
    )


# --------------------------------------------------
# MAIN BAKE
# --------------------------------------------------

def bake_fk_to_ik_controls(
    char,
    rig,
    ik_data,
    start=None,
    end=None,
    sample_by=1,
    clear_existing_keys=True
):

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

    print("=" * 80)
    print("BAKING FK MOTION TO IK CONTROLS")
    print("Frame range: {} -> {}".format(start, end))
    print("=" * 80)

    tmp_constraints = []
    ik_end_ctrls = []
    pv_ctrls = []

    # --------------------------------------------------
    # End IK controls follow FK end controls
    # --------------------------------------------------

    for limb_name, data in ik_data.items():

        end_slot = data["end"]

        fk_end_ctrl = genUtils.resolve_node(
            rig[end_slot]["ctrl"]
        )

        ik_ctrl = genUtils.resolve_node(
            data["ik_ctrl"]["ctrl"]
        )

        unlock_transform_attrs(ik_ctrl)

        if clear_existing_keys:
            clear_keys(
                ik_ctrl,
                start,
                end
            )

        tmp_name = "TMP_{}_fk_to_ik_parentConstraint".format(
            limb_name
        )

        if cmds.objExists(tmp_name):
            cmds.delete(tmp_name)

        con = cmds.parentConstraint(
            fk_end_ctrl,
            ik_ctrl,
            mo=False,
            n=tmp_name
        )[0]

        tmp_constraints.append(con)
        ik_end_ctrls.append(ik_ctrl)

    if ik_end_ctrls:

        cmds.bakeResults(
            ik_end_ctrls,
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

    for con in tmp_constraints:
        if cmds.objExists(con):
            cmds.delete(con)

    # --------------------------------------------------
    # Pole vectors are calculated per frame
    # --------------------------------------------------

    for limb_name, data in ik_data.items():

        pv_ctrl = genUtils.resolve_node(
            data["pv_ctrl"]["ctrl"]
        )

        unlock_transform_attrs(pv_ctrl)

        if clear_existing_keys:
            clear_keys(
                pv_ctrl,
                start,
                end
            )

        start_joint = rig[data["start"]]["joint"]
        mid_joint = rig[data["mid"]]["joint"]
        end_joint = rig[data["end"]]["joint"]

        for frame in range(start, end + 1, sample_by):

            cmds.currentTime(
                frame,
                edit=True
            )

            pv_position = calculate_pole_vector_position(
                start_joint,
                mid_joint,
                end_joint
            )

            cmds.xform(
                pv_ctrl,
                ws=True,
                t=pv_position
            )

            cmds.setKeyframe(
                pv_ctrl,
                attribute=[
                    "translateX",
                    "translateY",
                    "translateZ"
                ],
                time=frame
            )

        pv_ctrls.append(pv_ctrl)

    print("=" * 80)
    print("FK TO IK BAKE COMPLETE")
    print("Baked {} IK end ctrls.".format(len(ik_end_ctrls)))
    print("Baked {} PV ctrls.".format(len(pv_ctrls)))
    print("=" * 80)

    return {
        "ik_end_ctrls": ik_end_ctrls,
        "pv_ctrls": pv_ctrls
    }