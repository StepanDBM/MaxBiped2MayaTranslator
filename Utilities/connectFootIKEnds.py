import maya.cmds as cmds
import importlib

import Utilities.genUtils as genUtils
import Utilities.vectorMath as vMath

importlib.reload(genUtils)
importlib.reload(vMath)

# --------------------------------------------------
# POLE VECTOR RECUPERATION AFTER REVERSE FOOT CONTROLS
# --------------------------------------------------
def get_pv_ctrl_from_limb_IK_data(parent_limb, limb_IK_data=None):
    """
    Finds the pole vector control for this limb.

    Preferred:
        limb_IK_data["pv_ctrl"]["ctrl"]

    Fallback:
        bip001_l_leg_pv_ctrl
        bip001_r_leg_pv_ctrl
    """

    if limb_IK_data:
        pv_ctrl_data = limb_IK_data.get("pv_ctrl")

        if pv_ctrl_data:
            pv_ctrl = pv_ctrl_data.get("ctrl")

            if pv_ctrl and cmds.objExists(pv_ctrl):
                return genUtils.resolve_node(pv_ctrl)

    fallback_name = "bip001_" + parent_limb + "_pv_ctrl"

    if cmds.objExists(fallback_name):
        return genUtils.resolve_node(fallback_name)

    cmds.warning(
        "Could not find PV ctrl for limb: {}".format(
            parent_limb
        )
    )

    return None


def delete_pole_vector_constraints_on_handle(ik_handle):
    """
    Deletes poleVectorConstraints connected to this IK handle only.
    """

    if not ik_handle or not cmds.objExists(ik_handle):
        return []

    constraints = cmds.listConnections(
        ik_handle,
        source=True,
        destination=False,
        type="poleVectorConstraint"
    ) or []

    deleted = []

    for constraint in constraints:
        if not cmds.objExists(constraint):
            continue

        try:
            cmds.delete(constraint)
            deleted.append(constraint)
        except Exception:
            pass

    return deleted


def ensure_original_leg_pole_vector_constraint(
    parent_limb,
    limb_IK_data,
    leg_handle
):
    """
    Ensures the original leg IK handle has a live PV constraint.

    Example:
        parent_limb = "l_leg"
        pv ctrl     = "bip001_l_leg_pv_ctrl"
        ik handle   = "l_leg_IK_IKh"
        constraint  = "l_leg_pv_ctrl_to_IK_handle_poleVectorConstraint"
    """

    if not leg_handle or not cmds.objExists(leg_handle):
        cmds.warning(
            "Cannot create PV constraint. Missing leg handle for {}".format(
                parent_limb
            )
        )
        return None

    pv_ctrl = get_pv_ctrl_from_limb_IK_data(
        parent_limb,
        limb_IK_data=limb_IK_data
    )

    if not pv_ctrl:
        cmds.warning(
            "Cannot create PV constraint. Missing PV ctrl for {}".format(
                parent_limb
            )
        )
        return None

    constraint_name = parent_limb + "_pv_ctrl_to_IK_handle_poleVectorConstraint"

    delete_pole_vector_constraints_on_handle(
        leg_handle
    )

    if cmds.objExists(constraint_name):
        try:
            cmds.delete(constraint_name)
        except Exception:
            pass

    constraint = cmds.poleVectorConstraint(
        pv_ctrl,
        leg_handle,
        n=constraint_name
    )[0]

    print(
        "Rebuilt original leg PV: {} -> {}".format(
            pv_ctrl,
            leg_handle
        )
    )

    return constraint




# --------------------------------------------------
# BASIC HELPERS
# --------------------------------------------------

def get_flat_foot_direction(foot_pos, toe_pos):
    """
    Gets foot direction projected onto world XZ.

    This keeps reverse-foot controls from caring about the foot's vertical tilt.
    """

    direction = [
        toe_pos[0] - foot_pos[0],
        0,
        toe_pos[2] - foot_pos[2]
    ]

    return vMath.vec_normalize(direction)


def get_world_x_side_axis(foot_end_name):
    """
    Returns world X side direction for outer/inner controls.

    We intentionally do not derive this from foot orientation.
    """

    side = side_from_foot_end_name(foot_end_name)

    if side == "r":
        return [-1, 0, 0]

    return [1, 0, 0]

def parent_preserve_world(child, parent=None):
    """
    Parents child while preserving world matrix.
    """

    child = genUtils.resolve_node(child)

    matrix = vMath.get_world_matrix(child)

    if parent:
        parent = genUtils.resolve_node(parent)

        child = cmds.parent(child, parent)[0]

    else:
        child = cmds.parent(child, world=True)[0]

    vMath.set_world_matrix(child, matrix)

    return child


def side_from_foot_end_name(foot_end_name):
    """
    l_foot_end -> l
    r_foot_end -> r
    """

    return foot_end_name.split("_")[0]


def get_control_prefix(foot_end_name):
    """
    Matches reference scene naming:
        l_IK_outter_ctrl
        l_IK_inner_ctrl
        l_IK_heel_ctrl
        ...
    """

    side = side_from_foot_end_name(foot_end_name)

    return side + "_IK"


def get_original_leg_ik_handle(parent_limb):
    """
    Gets the original leg IK handle created by the OG IK system.

    Example:
        parent_limb = "l_leg"
        returns:
            "l_leg_IK_IKh"

    This is the handle that already has the correct poleVectorConstraint.
    """

    handle_name = parent_limb + "_IK_IKh"

    if cmds.objExists(handle_name):
        return genUtils.resolve_node(handle_name)

    cmds.warning(
        "Original leg IK handle not found: {}".format(
            handle_name
        )
    )

    return None

# --------------------------------------------------
# CUBE CONTROL CREATION
# --------------------------------------------------

def set_control_color(ctrl, rgb=(1.0, 0.8, 0.1)):
    """
    Colors transform and shapes.
    """

    if not cmds.objExists(ctrl):
        return

    try:
        cmds.setAttr(ctrl + ".overrideEnabled", 1)
        cmds.setAttr(ctrl + ".overrideRGBColors", 1)
        cmds.setAttr(
            ctrl + ".overrideColorRGB",
            rgb[0],
            rgb[1],
            rgb[2]
        )

    except Exception:
        pass

    shapes = cmds.listRelatives(
        ctrl,
        shapes=True,
        fullPath=True
    ) or []

    for shape in shapes:
        try:
            cmds.setAttr(shape + ".overrideEnabled", 1)
            cmds.setAttr(shape + ".overrideRGBColors", 1)
            cmds.setAttr(
                shape + ".overrideColorRGB",
                rgb[0],
                rgb[1],
                rgb[2]
            )

        except Exception:
            pass


def create_cube_curve_ctrl(name, size=1.0, componentOffset=(0.0, 0.0, 0.0)):
    """
    Creates a cube-shaped curve control.

    This is intentionally a curve, not mesh geometry.

    componentOffset:
        Moves the curve components/points relative to the transform pivot.
        The transform stays at origin until positioned later, but the cube shape
        is offset in local/component space.

        Example:
            componentOffset=(0, 2, 0)
            moves all cube points upward from the control pivot.
    """

    if cmds.objExists(name):
        cmds.delete(name)

    half = size * 0.5

    ox = componentOffset[0]
    oy = componentOffset[1]
    oz = componentOffset[2]

    points = [
        [-half, -half, -half],
        [ half, -half, -half],
        [ half,  half, -half],
        [-half,  half, -half],
        [-half, -half, -half],

        [-half, -half,  half],
        [ half, -half,  half],
        [ half,  half,  half],
        [-half,  half,  half],
        [-half, -half,  half],

        [ half, -half,  half],
        [ half, -half, -half],

        [ half,  half, -half],
        [ half,  half,  half],

        [-half,  half,  half],
        [-half,  half, -half],
    ]

    offset_points = []

    for point in points:
        offset_points.append(
            [
                point[0] + ox,
                point[1] + oy,
                point[2] + oz
            ]
        )

    ctrl = cmds.curve(
        d=1,
        p=offset_points,
        n=name
    )

    set_control_color(ctrl)

    return ctrl


def create_cube_ctrl_at(name, position, size=1.0, componentOffset=(0.0,0.0,0.0), parent=None):
    """
    Creates a curve cube control at world-space position.
    """

    ctrl = create_cube_curve_ctrl(
        name,
        size=size,
        componentOffset = componentOffset
    )

    vMath.set_world_position(ctrl, position)

    if parent:
        ctrl = parent_preserve_world(ctrl, parent)

    return ctrl


# --------------------------------------------------
# IK JOINT / IK HANDLE HELPERS
# --------------------------------------------------

def unlock_transform_attrs(node):
    attrs = [
        "translateX", "translateY", "translateZ",
        "rotateX", "rotateY", "rotateZ",
        "scaleX", "scaleY", "scaleZ"
    ]

    for attr in attrs:
        plug = node + "." + attr

        if not cmds.objExists(plug):
            continue

        try:
            cmds.setAttr(plug, lock=False)

            cmds.setAttr(plug, keyable=True)

        except Exception:
            pass


def delete_constraints_on_node(node):
    """
    Deletes normal transform constraints on an IK handle/target.

    Does not delete poleVectorConstraint.
    """

    if not node or not cmds.objExists(node):
        return []

    deleted = []

    constraint_types = [
        "parentConstraint",
        "pointConstraint",
        "orientConstraint",
        "scaleConstraint"
    ]

    for constraint_type in constraint_types:
        constraints = cmds.listConnections(
            node,
            source=True,
            destination=False,
            type=constraint_type
        ) or []

        for constraint in constraints:
            if not cmds.objExists(constraint):
                continue

            try:
                cmds.delete(constraint)
                deleted.append(constraint)

            except Exception:
                pass

    return deleted


def get_ik_handle_end_joint(handle):
    """
    Returns the end joint of an IK handle by checking the parent of its effector.
    """

    try:
        effector = cmds.ikHandle(
            handle,
            q=True,
            ee=True
        )

    except Exception:
        return None

    if not effector or not cmds.objExists(effector):
        return None

    parents = cmds.listRelatives(
        effector,
        parent=True,
        type="joint",
        fullPath=True
    ) or []

    if not parents:
        return None

    return parents[0]


def find_ik_handle_between(start_joint, end_joint):
    """
    Finds an existing IK handle from start_joint to end_joint.
    """

    start_joint = genUtils.resolve_node(start_joint)
    end_joint = genUtils.resolve_node(end_joint)

    handles = cmds.ls(type="ikHandle") or []

    for handle in handles:

        try:
            sj = cmds.ikHandle(
                handle,
                q=True,
                sj=True
            )

        except Exception:
            continue

        if not sj:
            continue

        try:
            sj = genUtils.resolve_node(sj)

        except Exception:
            continue

        ee_joint = get_ik_handle_end_joint(handle)

        if not ee_joint:
            continue

        try:
            ee_joint = genUtils.resolve_node(ee_joint)

        except Exception:
            continue

        if sj == start_joint and ee_joint == end_joint:
            return handle

    return None


def get_ik_handle_solver(handle):
    """
    Returns IK handle solver name if possible.
    """

    try:
        return cmds.ikHandle(
            handle,
            q=True,
            solver=True
        )
    except Exception:
        return None


def create_or_reuse_ik_handle(
    name,
    start_joint,
    end_joint,
    solver="ikRPsolver",
    recreate_if_solver_mismatch=False
):
    """
    Creates or reuses an IK handle between start_joint and end_joint.

    For reverse foot:
        leg handle  -> ikRPsolver
        foot handle -> ikSCsolver
        toe handle  -> ikSCsolver
    """

    start_joint = genUtils.resolve_node(start_joint)
    end_joint = genUtils.resolve_node(end_joint)
    existing = find_ik_handle_between(start_joint, end_joint)

    if existing:
        existing_solver = get_ik_handle_solver(existing)

        if (
            recreate_if_solver_mismatch and
            existing_solver and
            existing_solver != solver
        ):
            try:
                cmds.delete(existing)
                existing = None
            except Exception:
                pass

        else:
            if existing != name and not cmds.objExists(name):
                try:
                    existing = cmds.rename(existing, name)
                except Exception:
                    pass

            return existing

    if cmds.objExists(name):
        cmds.delete(
            name
        )

    handle, effector = cmds.ikHandle(
        sj=start_joint,
        ee=end_joint,
        sol=solver,
        n=name
    )

    try:
        cmds.setAttr(effector + ".visibility", 0)
    except Exception:
        pass

    return handle


def ensure_tip_toe_IK_joint(
    foot_end_name,
    foot_IK_jnt,
    toe_IK_jnt
):
    """
    Creates the IK-only tip toe joint.

    Important:
        This does NOT create an FK tip joint.
        This does NOT create a result/original tip joint.
        This exists only to be the final joint of the toe IK handle.
    """

    prefix = get_control_prefix(foot_end_name)

    tip_joint_name = prefix + "_tipToe_IK_jnt"

    if cmds.objExists(tip_joint_name):
        return genUtils.resolve_node(tip_joint_name)
    foot_IK_jnt = genUtils.resolve_node(foot_IK_jnt)
    toe_IK_jnt = genUtils.resolve_node(toe_IK_jnt)

    foot_pos = vMath.get_world_pos(foot_IK_jnt)
    toe_pos = vMath.get_world_pos(toe_IK_jnt)

    foot_dir = get_flat_foot_direction(foot_pos, toe_pos)

    foot_length = vMath.vec_length(
        [
            toe_pos[0] - foot_pos[0],
            0,
            toe_pos[2] - foot_pos[2]
        ]
    )

    tip_pos = vMath.vec_add(
        toe_pos,
        vMath.vec_mul(
            foot_dir,
            foot_length * 0.75
        )
    )

    old_selection = cmds.ls(
        selection=True,
        long=True
    ) or []

    cmds.select(
        clear=True
    )

    tip_joint = cmds.joint(
        n=tip_joint_name,
        p=tip_pos
    )

    try:
        cmds.setAttr(
            tip_joint + ".radius",
            cmds.getAttr(toe_IK_jnt + ".radius")
        )
    except Exception:
        pass

    tip_joint = parent_preserve_world(tip_joint, toe_IK_jnt)

    try:
        if old_selection:
            cmds.select(old_selection, replace=True)
        else:
            cmds.select(clear=True)
    except Exception:
        pass

    print(
        "Created IK-only tip toe joint: {}".format(
            tip_joint
        )
    )

    return tip_joint


# --------------------------------------------------
# REVERSE FOOT CONTROL CLEANUP
# --------------------------------------------------

def delete_existing_reverse_foot_controls(foot_end_name):
    """
    Deletes old reverse-foot controls if rebuilding.
    """

    prefix = get_control_prefix(foot_end_name)

    names = [
        prefix + "_outter_ctrl",
        prefix + "_outer_ctrl",
        prefix + "_inner_ctrl",
        prefix + "_heel_ctrl",
        prefix + "_tip_ctrl",
        prefix + "_toe_ctrl",
        prefix + "_foot_ctrl"
    ]

    for name in names:
        if cmds.objExists(name):
            try:
                cmds.delete(name)
            except Exception:
                pass


# --------------------------------------------------
# REVERSE FOOT BUILD
# --------------------------------------------------

def build_reverse_foot_controls(
    foot_end_name,
    IK_ctrl,
    parent_limb,
    parent_IK_chain,
    foot_end_IK_chain,
    limb_IK_data
):
    """
    Creates the reverse foot system.

    Reference hierarchy:
        IK_ctrl
            outter_ctrl
                inner_ctrl
                    heel_ctrl
                        tip_ctrl
                            toe_ctrl
                                IK_toe_handle
                            foot_ctrl
                                IK_foot_handle
                                IK_leg_handle
    """

    prefix = get_control_prefix(foot_end_name)
    IK_ctrl = genUtils.resolve_node(IK_ctrl)
    thigh_IK_jnt = genUtils.resolve_node(parent_IK_chain[0])
    foot_IK_jnt = genUtils.resolve_node(parent_IK_chain[-1])
    toe_IK_jnt = genUtils.resolve_node(foot_end_IK_chain[0])
    tip_toe_IK_jnt = ensure_tip_toe_IK_joint(
        foot_end_name,
        foot_IK_jnt,
        toe_IK_jnt
    )

    delete_existing_reverse_foot_controls(foot_end_name)
    foot_pos = vMath.get_world_pos(foot_IK_jnt)
    toe_pos = vMath.get_world_pos(toe_IK_jnt)
    tip_pos = vMath.get_world_pos(tip_toe_IK_jnt)

    # All reverse-foot controls live on the same world Y level.
    # This matches the reference scene behavior and avoids caring about foot tilt.
    control_y = toe_pos[1]

    foot_dir = get_flat_foot_direction(foot_pos, toe_pos)

    side_dir = get_world_x_side_axis(foot_end_name)

    flat_foot_pos = vMath.flatten_to_axis(foot_pos, "y", control_y)
    flat_toe_pos = vMath.flatten_to_axis(toe_pos, "y", control_y)
    flat_tip_pos = vMath.flatten_to_axis(tip_pos, "y", control_y)

    foot_length = vMath.vec_length(
        [
            toe_pos[0] - foot_pos[0],
            0,
            toe_pos[2] - foot_pos[2]
        ]
    )

    side_offset = foot_length * 0.35

    heel_pos = vMath.vec_add(
        flat_foot_pos,
        vMath.vec_mul(
            foot_dir,
            -foot_length * 0.5
        )
    )

    outter_pos = vMath.vec_add(
        flat_foot_pos,
        vMath.vec_mul(
            side_dir,
            side_offset
        )
    )

    inner_pos = vMath.vec_add(
        flat_foot_pos,
        vMath.vec_mul(
            side_dir,
            -side_offset
        )
    )

    outter_ctrl = create_cube_ctrl_at(
        prefix + "_outter_ctrl",
        outter_pos,
        size=3,
        parent=IK_ctrl
    )

    inner_ctrl = create_cube_ctrl_at(
        prefix + "_inner_ctrl",
        inner_pos,
        size=3,
        parent=outter_ctrl
    )

    heel_ctrl = create_cube_ctrl_at(
        prefix + "_heel_ctrl",
        heel_pos,
        size=3,
        parent=inner_ctrl
    )

    tip_ctrl = create_cube_ctrl_at(
        prefix + "_tip_ctrl",
        flat_tip_pos,
        size=3,
        parent=heel_ctrl
    )

    toe_ctrl = create_cube_ctrl_at(
        prefix + "_toe_ctrl",
        flat_toe_pos,
        size=5,
        parent=tip_ctrl,
        componentOffset=(0.0,8.0,0.0)
    )

    toe_to_foot_distance = vMath.vec_length(
        vMath.vec_sub(
            toe_pos,
            foot_pos
        )
    )

    foot_ctrl = create_cube_ctrl_at(
        prefix + "_foot_ctrl",
        flat_foot_pos,
        size=10,
        parent=tip_ctrl,
        componentOffset=(0.0,toe_to_foot_distance,0.0)
    )

    leg_handle_name = parent_limb + "_IK_IKh"
    foot_handle_name = prefix + "_foot_hdl"
    toe_handle_name = prefix + "_toe_hdl"

    # Use the original leg IK handle.
    # This is the one that already has the poleVectorConstraint connected.
    leg_handle = get_original_leg_ik_handle(parent_limb)

    if not leg_handle:
        raise RuntimeError(
            "Cannot build reverse foot: missing original leg IK handle {}".format(
                leg_handle_name
            )
        )

    # Remove the old parentConstraint from IK ctrl -> IK handle.
    # Reverse foot hierarchy will drive the handle now.
    # IMPORTANT: delete_constraints_on_node does NOT delete poleVectorConstraint.
    delete_constraints_on_node(
        leg_handle
    )

    foot_handle = create_or_reuse_ik_handle(
        foot_handle_name,
        foot_IK_jnt,
        toe_IK_jnt,
        solver="ikSCsolver",
        recreate_if_solver_mismatch=True
    )

    toe_handle = create_or_reuse_ik_handle(
        toe_handle_name,
        toe_IK_jnt,
        tip_toe_IK_jnt,
        solver="ikSCsolver",
        recreate_if_solver_mismatch=True
    )

    for handle in [
        leg_handle,
        foot_handle,
        toe_handle
    ]:
        unlock_transform_attrs(
            handle
        )

        delete_constraints_on_node(
            handle
        )

    parent_preserve_world(
        toe_handle,
        toe_ctrl
    )

    parent_preserve_world(
        foot_handle,
        foot_ctrl
    )

    parent_preserve_world(
        leg_handle,
        foot_ctrl
    )
    leg_pv_constraint = ensure_original_leg_pole_vector_constraint(
        parent_limb,
        limb_IK_data,
        leg_handle
    )

    print(
        "Created reverse-foot IK setup for {}".format(
            foot_end_name
        )
    )

    return {
        "outter_ctrl": outter_ctrl,
        "inner_ctrl": inner_ctrl,
        "heel_ctrl": heel_ctrl,
        "tip_ctrl": tip_ctrl,
        "toe_ctrl": toe_ctrl,
        "foot_ctrl": foot_ctrl,

        "leg_handle": leg_handle,
        "foot_handle": foot_handle,
        "toe_handle": toe_handle,

        "foot_IK_jnt": foot_IK_jnt,
        "toe_IK_jnt": toe_IK_jnt,
        "tip_toe_IK_jnt": tip_toe_IK_jnt,
        "leg_pv_constraint": leg_pv_constraint
    }


# --------------------------------------------------
# MAIN
# --------------------------------------------------

def connect_foot_IK_ends(
    chain_data,
    IK_data,
    maintain_offset=True
):
    """
    Builds foot-end IK reverse-foot control hierarchy.

    It creates:
        - IK-only tip toe joint
        - IK leg handle
        - IK foot handle
        - IK toe handle
        - cube reverse-foot controls

    Control / handle hierarchy:
        IK_ctrl
            outter_ctrl
                inner_ctrl
                    heel_ctrl
                        tip_ctrl
                            toe_ctrl
                                toe IK handle
                            foot_ctrl
                                foot IK handle
                                leg IK handle
    """

    print("=" * 80)
    print("CONNECTING FOOT-END IK DRIVERS / REVERSE FOOT CONTROLS")
    print("=" * 80)

    result = {}

    for foot_end_name, data in chain_data.items():

        if data.get("system_type") != "foot_end":
            continue

        parent_limb = data.get(
            "parent_limb"
        )

        if parent_limb not in IK_data:
            cmds.warning(
                "Skipping {}: missing parent IK data {}".format(
                    foot_end_name,
                    parent_limb
                )
            )
            continue

        if parent_limb not in chain_data:
            cmds.warning(
                "Skipping {}: missing parent limb chain data {}".format(
                    foot_end_name,
                    parent_limb
                )
            )
            continue

        limb_IK_data = IK_data[parent_limb]

        IK_ctrl_data = limb_IK_data.get("IK_ctrl")

        if not IK_ctrl_data:
            cmds.warning(
                "Skipping {}: missing IK ctrl data for {}".format(
                    foot_end_name,
                    parent_limb
                )
            )
            continue

        IK_ctrl = IK_ctrl_data.get("ctrl")

        if not IK_ctrl:
            cmds.warning(
                "Skipping {}: missing IK ctrl.".format(
                    foot_end_name
                )
            )
            continue

        parent_IK_chain = chain_data[parent_limb].get("IK_chain", [])

        foot_end_IK_chain = data.get("IK_chain", [])

        if len(parent_IK_chain) < 3:
            cmds.warning(
                "Skipping {}: parent limb IK chain is too short.".format(
                    foot_end_name
                )
            )
            continue

        if not foot_end_IK_chain:
            cmds.warning(
                "Skipping {}: foot end has no IK chain.".format(
                    foot_end_name
                )
            )
            continue

        reverse_foot_data = build_reverse_foot_controls(
            foot_end_name,
            IK_ctrl,
            parent_limb,
            parent_IK_chain,
            foot_end_IK_chain,
            limb_IK_data
        )

        result[foot_end_name] = {
            "parent_limb": parent_limb,
            "IK_chain": foot_end_IK_chain,
            "constraints": [],
            "reverse_foot": reverse_foot_data
        }

        print(
            "Foot-end IK reverse-foot prepared: {} under parent limb {}".format(
                foot_end_name,
                parent_limb
            )
        )

    print("=" * 80)
    print("FOOT-END IK / REVERSE FOOT CONTROL COMPLETE")
    print("Created {} systems.".format(len(result)))
    print("=" * 80)

    return result