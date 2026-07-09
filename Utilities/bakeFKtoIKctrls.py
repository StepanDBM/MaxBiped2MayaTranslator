import maya.cmds as cmds
import Utilities.genUtils as genUtils
import Utilities.vectorMath as vecMath
import importlib
importlib.reload(genUtils)
importlib.reload(vecMath)


def calculate_pole_vector_position(start_obj, mid_obj, end_obj, distance_multiplier=1.5):

    start = vecMath.get_world_pos(start_obj)
    mid = vecMath.get_world_pos(mid_obj)
    end = vecMath.get_world_pos(end_obj)

    start_to_end = vecMath.vec_sub(end, start)
    start_to_mid = vecMath.vec_sub(mid, start)

    line_length = vecMath.vec_length(start_to_end)

    projection_amount = vecMath.vec_dot(
        start_to_mid,
        start_to_end
    ) / (line_length ** 2)

    projected = vecMath.vec_add(
        start,
        vecMath.vec_mul(
            start_to_end,
            projection_amount
        )
    )

    pole_dir = vecMath. vec_sub(
        mid,
        projected
    )

    if vecMath.vec_length(pole_dir) < 0.001:
        pole_dir = [0, 0, 1]

    pole_dir = vecMath.vec_normalize(pole_dir)

    upper_len = vecMath.vec_length(
        vecMath.vec_sub(mid, start)
    )

    lower_len = vecMath.vec_length(
        vecMath.vec_sub(end, mid)
    )

    pole_distance = (
        upper_len + lower_len
    ) * 0.5 * distance_multiplier

    return vecMath.vec_add(
        mid,
        vecMath.vec_mul(
            pole_dir,
            pole_distance
        )
    )


# MAIN BAKE

def bake_FK_to_IK_controls(
    char,
    rig,
    IK_data,
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
    IK_end_ctrls = []
    pv_ctrls = []

    # End IK controls follow FK end controls

    for limb_name, data in IK_data.items():

        end_slot = data["end"]

        FK_end_ctrl = genUtils.resolve_node(
            rig[end_slot]["ctrl"]
        )

        IK_ctrl = genUtils.resolve_node(
            data["IK_ctrl"]["ctrl"]
        )

        genUtils.unlock_transform_attrs(IK_ctrl)

        if clear_existing_keys:
            genUtils.clear_keys(
                IK_ctrl,
                start,
                end
            )

        tmp_name = "TMP_{}_FK_to_IK_parentConstraint".format(
            limb_name
        )

        if cmds.objExists(tmp_name):
            cmds.delete(tmp_name)

        con = cmds.parentConstraint(
            FK_end_ctrl,
            IK_ctrl,
            mo=False,
            n=tmp_name
        )[0]

        tmp_constraints.append(con)
        IK_end_ctrls.append(IK_ctrl)

    if IK_end_ctrls:

        cmds.bakeResults(
            IK_end_ctrls,
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

    # Pole vectors are calculated per frame

    for limb_name, data in IK_data.items():

        pv_ctrl = genUtils.resolve_node(
            data["pv_ctrl"]["ctrl"]
        )

        genUtils.unlock_transform_attrs(pv_ctrl)

        if clear_existing_keys:
            genUtils.clear_keys(
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
    print("Baked {} IK end ctrls.".format(len(IK_end_ctrls)))
    print("Baked {} PV ctrls.".format(len(pv_ctrls)))
    print("=" * 80)

    return {
        "IK_end_ctrls": IK_end_ctrls,
        "pv_ctrls": pv_ctrls
    }