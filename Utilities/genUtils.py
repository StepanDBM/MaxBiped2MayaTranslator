import maya.cmds as cmds
import re


def get_all_joints():
    """
    Returns all scene joints as long names.
    """

    return cmds.ls(
        type="joint",
        long=True
    ) or []


def get_parent_joint(joint):
    """
    Returns the parent joint of a joint, or None.
    """

    joint = resolve_node(joint)

    parents = cmds.listRelatives(
        joint,
        parent=True,
        type="joint",
        fullPath=True
    ) or []

    if not parents:
        return None

    return parents[0]


def get_joint_descendants(joint):
    """
    Returns all joint descendants in parent-first order.
    """

    joint = resolve_node(
        joint
    )

    descendants = cmds.listRelatives(
        joint,
        ad=True,
        type="joint",
        fullPath=True
    ) or []

    # Maya returns deepest-first with ad=True.
    # Reverse to get parent-first.
    descendants.reverse()

    return descendants


def get_long_names(node):
    """
    Returns all long DAG names for a node.
    """

    if not node:
        return []

    if not cmds.objExists(node):
        return []

    try:
        node = resolve_node(
            node
        )
    except Exception:
        return []

    return cmds.ls(
        node,
        long=True
    ) or []

def clean_name(name):

    name = name.split("|")[-1]

    name = re.sub(
        r"FBXASC032",
        "_",
        name,
        flags=re.IGNORECASE
    )

    while "__" in name:
        name = name.replace("__", "_")

    return name

def clean_name(name):
    """
    Converts Maya/FBX space-imbued incomprehensible names into clean readable names.
    FBXASC032 is Maya's internal naming convention for FBX imports that
    use spaces in names. This function replaces those with FBXASC032 which is now 
    impossible to replace because the Unity system and project is FULL of characters
    with FBXASC032 in them. This is ONLY for runtime processes of THIS script and
    should not be used to rename the actual final nodes (joints, geometry, animation
    curves, etc.) in the scene.

    Example:
        |Bip001|Bip001FBXASC032LFBXASC032Hand
        ->
        Bip001_L_Hand
    """

    name = name.split("|")[-1]

    name = re.sub(
        r"FBXASC032",
        "_",
        name,
        flags=re.IGNORECASE
    )

    name = re.sub(
        r"FBXASC095",
        "_",
        name,
        flags=re.IGNORECASE
    )

    while "__" in name:
        name = name.replace("__", "_")

    return name.strip("_")


def pretty_node_name(node):
    """
    Safe display name for logs.
    Keeps scene nodes untouched.
    Only prettifies the printed output.
    """

    if not node:
        return "None"

    return clean_name(node)


def ensure_group(name, parent=None):
    """
    Creates a group if it does not exist.
    Optionally parents it under another group.
    """

    if cmds.objExists(name):
        grp = name
    else:
        grp = cmds.group(
            em=True,
            n=name
        )

    if parent and cmds.objExists(parent):
        current_parent = cmds.listRelatives(
            grp,
            parent=True,
            fullPath=False
        )

        if not current_parent or current_parent[0] != parent:
            try:
                grp = cmds.parent(
                    grp,
                    parent
                )[0]
            except Exception:
                pass

    return grp


def resolve_node(node):
    """
    Resolves a Maya node name even if an old full DAG path was stored.
    Returns a valid node name.
    """

    if cmds.objExists(node):
        return node

    short = node.split("|")[-1]

    matches = cmds.ls(
        short,
        long=False
    ) or []

    if matches:
        return matches[0]

    matches = cmds.ls(
        short,
        long=True
    ) or []

    if matches:
        return matches[0]

    raise RuntimeError(
        "Could not resolve node: {}".format(node)
    )

def get_auto_transform_nodes():
    """
    Returns Maya auto-generated transform nodes:
        transform1
        transform2
        ...
        transformn
    """

    import re

    result = []

    transforms = cmds.ls(
        type="transform",
        long=False
    ) or []

    for node in transforms:

        if re.match(r"^transform\d+$", node):
            result.append(node)

    return result

def delete_transform_buffer(node):
    """
    Deletes an unwanted transform# buffer.

    If it has children, children are moved to the buffer's parent/world
    while preserving world matrices.
    """

    if not cmds.objExists(node):
        return

    # Avoid deleting transforms with shapes, just in case.
    shapes = cmds.listRelatives(
        node,
        shapes=True,
        fullPath=True
    ) or []

    if shapes:
        cmds.warning(
            "Skipping {} because it has shapes.".format(node)
        )
        return

    parent = cmds.listRelatives(
        node,
        parent=True,
        fullPath=True
    )

    parent = parent[0] if parent else None

    children = cmds.listRelatives(
        node,
        children=True,
        fullPath=True
    ) or []

    # Preserve child world matrices
    child_matrices = {}

    for child in children:
        try:
            child_matrices[child] = cmds.xform(
                child,
                q=True,
                ws=True,
                m=True
            )
        except Exception:
            pass

    # Move children out
    for child in children:

        if not cmds.objExists(child):
            continue

        try:
            if parent:
                new_child = cmds.parent(
                    child,
                    parent,
                    relative=True
                )[0]
            else:
                new_child = cmds.parent(
                    child,
                    world=True,
                    relative=True
                )[0]

            short = new_child.split("|")[-1]

            if child in child_matrices:
                cmds.xform(
                    short,
                    ws=True,
                    m=child_matrices[child]
                )

        except Exception as e:
            cmds.warning(
                "Could not reparent child {} from {}: {}".format(
                    child,
                    node,
                    e
                )
            )

    # Delete the unwanted buffer
    if cmds.objExists(node):
        try:
            cmds.delete(node)
            print("Deleted auto transform buffer: {}".format(node))
        except Exception as e:
            cmds.warning(
                "Could not delete auto transform {}: {}".format(
                    node,
                    e
                )
            )

def cleanup_auto_transform_nodes(before=None):
    """
    Deletes transform# nodes.

    If before is given, only deletes transform# nodes created after that snapshot.
    """

    current = set(get_auto_transform_nodes())

    if before is not None:
        targets = current - set(before)
    else:
        targets = current

    for node in sorted(targets):
        delete_transform_buffer(node)

    return list(targets)

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

def force_dg_evaluation(label=None):
    """
    Forces Maya to dirty and evaluate the dependency graph.

    Useful after creating/deleting many constraints, IK handles,
    blend connections, or animation curves in one scripted pass.

    This helps avoid stale transforms that only update after
    user interaction, selection, moving a control, or undo.
    """
    if label:
        print("=" * 80)
        print("FORCING DG EVALUATION: {}".format(label))
        print("=" * 80)

    current_time = cmds.currentTime(q=True)

    min_time = cmds.playbackOptions(q=True, min=True)

    max_time = cmds.playbackOptions(q=True, max=True)

    # Dirty the graph if Maya supports it.
    try:
        cmds.dgdirty(allPlugs=True)
    except Exception:
        pass

    # Force timeline evaluation by stepping away and back.
    probe_time = current_time

    if current_time < max_time:
        probe_time = current_time + 1

    elif current_time > min_time:
        probe_time = current_time - 1

    if probe_time != current_time:
        try:
            cmds.currentTime(
                probe_time,
                edit=True
            )
        except Exception:
            pass

    try:
        cmds.currentTime(
            current_time,
            edit=True
        )
    except Exception:
        pass

    try:
        cmds.refresh(force=True)
    except Exception:
        pass

    if label:
        print("DG evaluation forced.")

def kick_aut_groups(
    amount=0.01,
    patterns=None
):
    """
    Tiny transform nudge for AUT groups.

    This is a Maya evaluation hack.

    Some newly-created constraint / IK / FKIK graphs do not update
    correctly until the user manually moves a control or presses undo.

    This function simulates that harmlessly by:
        - moving AUT groups by a tiny amount
        - forcing a refresh
        - moving them back

    It should not visually change the rig.
    """

    if patterns is None:
        patterns = [
            "*_FK_ctrl_aut",
            "*_IK_ctrl_aut",
            "*_pv_ctrl_aut",
            "*_ctrl_aut",
            "*_aut",
            "*_FK_ctrl_ofs",
            "*_IK_ctrl_ofs",
            "*_pv_ctrl_ofs",
            "*_ctrl_ofs",
            "*_ofs"
        ]

    nodes = []

    for pattern in patterns:
        found = cmds.ls(
            pattern,
            type="transform",
            long=False
        ) or []

        for node in found:
            if node not in nodes:
                nodes.append(node)

    if not nodes:
        print("No AUT groups found to kick.")
        return []

    print("=" * 80)
    print("KICKING AUT GROUPS FOR MAYA EVALUATION")
    print("Found {} AUT groups.".format(len(nodes)))
    print("=" * 80)

    # Avoid accidentally keying the nudge if Auto Key is enabled.
    auto_key_state = False

    try:
        auto_key_state = cmds.autoKeyframe(q=True, state=True)
        cmds.autoKeyframe(state=False)
    except Exception:
        pass

    kicked = []
    for node in nodes:
        if not cmds.objExists(node):
            continue
        try:
            pos = cmds.xform(
                node,
                q=True,
                ws=True,
                t=True
            )
            cmds.xform(
                node,
                ws=True,
                t=[
                    pos[0] + amount,
                    pos[1],
                    pos[2]
                ]
            )
            cmds.xform(
                node,
                ws=True,
                t=pos
            )
            kicked.append(node)

        except Exception:
            pass

    try:
        cmds.refresh(force=True)
    except Exception:
        pass

    try:
        cmds.dgdirty(allPlugs=True)
    except Exception:
        pass

    try:
        cmds.currentTime(
            cmds.currentTime(q=True),
            edit=True
        )
    except Exception:
        pass

    try:
        cmds.refresh(force=True)
    except Exception:
        pass

    try:
        cmds.autoKeyframe(state=auto_key_state)
    except Exception:
        pass

    print("Kicked {} AUT groups.".format(len(kicked)))

    print("=" * 80)

    return kicked
def kick_offset_groups_with_undo(
    amount=1.0,
    patterns=None
):
    """
    Forces Maya to evaluate the rig by doing a real undoable transform edit.

    This mimics:
        1. User moves an offset group.
        2. User presses Ctrl-Z.
        3. Maya finally updates the rig graph.

    Unlike a silent xform-to-position-and-back, this creates a real undo queue
    operation, then immediately undoes only that operation.

    This should leave the rig visually unchanged.
    """

    import maya.cmds as cmds

    if patterns is None:
        patterns = [
            "*_FK_ctrl_ofs",
            "*_IK_ctrl_ofs",
            "*_pv_ctrl_ofs",
            "*_ctrl_ofs",
            "*_ofs"
        ]

    nodes = []

    for pattern in patterns:
        found = cmds.ls(
            pattern,
            type="transform",
            long=False
        ) or []

        for node in found:
            if node not in nodes:
                nodes.append(node)

    if not nodes:
        print("No offset groups found to kick.")
        return []

    print("=" * 80)
    print("KICKING OFFSET GROUPS WITH UNDO")
    print("Found {} offset groups.".format(len(nodes)))
    print("=" * 80)

    # Store selection so the user's scene selection is restored.
    old_selection = cmds.ls(
        selection=True,
        long=True
    ) or []

    # Avoid creating accidental animation keys if Auto Key is enabled.
    auto_key_state = False

    try:
        auto_key_state = cmds.autoKeyframe(
            q=True,
            state=True
        )

        cmds.autoKeyframe(
            state=False
        )

    except Exception:
        pass

    # Make sure undo is enabled.
    undo_was_enabled = True

    try:
        undo_was_enabled = cmds.undoInfo(
            q=True,
            state=True
        )

        if not undo_was_enabled:
            cmds.undoInfo(
                state=True
            )

    except Exception:
        pass

    kicked = []

    try:
        cmds.undoInfo(
            openChunk=True,
            chunkName="MaxBiped2MayaTranslator_EvaluationKick"
        )

        for node in nodes:

            if not cmds.objExists(node):
                continue

            try:
                # Use cmds.move instead of xform.
                # This is closer to what Maya does during manual interaction.
                cmds.move(
                    amount,
                    0,
                    0,
                    node,
                    relative=True,
                    worldSpace=True
                )

                kicked.append(node)

            except Exception:
                pass

        cmds.undoInfo(
            closeChunk=True
        )

        # Force Maya to process the move.
        try:
            cmds.refresh(
                force=True
            )
        except Exception:
            pass

        # Undo ONLY the artificial nudge chunk.
        try:
            cmds.undo()
        except Exception as e:
            cmds.warning(
                "Could not undo evaluation kick: {}".format(e)
            )

    except Exception as e:

        try:
            cmds.undoInfo(
                closeChunk=True
            )
        except Exception:
            pass

        cmds.warning(
            "Evaluation kick failed: {}".format(e)
        )

    # Restore auto key.
    try:
        cmds.autoKeyframe(
            state=auto_key_state
        )
    except Exception:
        pass

    # Restore undo state if it was disabled before.
    try:
        if not undo_was_enabled:
            cmds.undoInfo(
                state=False
            )
    except Exception:
        pass

    # Restore previous selection.
    try:
        if old_selection:
            cmds.select(
                old_selection,
                replace=True
            )
        else:
            cmds.select(
                clear=True
            )

    except Exception:
        try:
            cmds.select(
                clear=True
            )
        except Exception:
            pass

    # Force final evaluation.
    try:
        cmds.dgdirty(
            allPlugs=True
        )
    except Exception:
        pass

    try:
        current_time = cmds.currentTime(
            q=True
        )

        cmds.currentTime(
            current_time,
            edit=True
        )
    except Exception:
        pass

    try:
        cmds.refresh(
            force=True
        )
    except Exception:
        pass

    print(
        "Kicked and undone {} offset groups.".format(
            len(kicked)
        )
    )

    print("=" * 80)

    return kicked

def printPrettyMatrix(node):
    """
    Prints a Maya node world matrix in a readable 4x4 format.

    Shows:
        - input node name
        - resolved node name
        - short node name
        - long node name
        - pretty node name
        - world matrix
    """
    if not node:
        print("printPrettyMatrix: No node provided.")
        return

    if not cmds.objExists(node):
        try:
            node = resolve_node(node)
        except Exception:
            print(
                "printPrettyMatrix: Node does not exist or cannot be resolved: {}".format(
                    node
                )
            )
            return

    resolved = resolve_node(node)

    short_name = resolved.split("|")[-1]
    long_names = cmds.ls(resolved, long=True) or []

    if long_names:
        long_name = long_names[0]
    else:
        long_name = resolved

    pretty_name = pretty_node_name(resolved)

    matrix = cmds.xform(resolved, q=True, ws=True, m=True)

    print("")
    print("=" * 80)
    print("PRETTY MATRIX")
    print("=" * 80)
    print("Input node:    {}".format(node))
    print("Resolved node: {}".format(resolved))
    print("Short name:    {}".format(short_name))
    print("Long name:     {}".format(long_name))
    print("Pretty name:   {}".format(pretty_name))
    print("-" * 80)

    for row in range(4):
        values = matrix[row * 4:row * 4 + 4]

        print(
            "[ {:>12.6f}  {:>12.6f}  {:>12.6f}  {:>12.6f} ]".format(
                values[0],
                values[1],
                values[2],
                values[3]
            )
        )

    print("=" * 80)
    print("")

def reset_time_to_start_frame(char=None, fallback_frame=0):
    """
    Resets Maya timeline/current frame to the character start frame.

    If char has startFrame, uses that.
    Otherwise uses fallback_frame, default 0.
    """

    frame = fallback_frame

    if char:
        frame = char.get(
            "startFrame",
            fallback_frame
        )

    frame = int(frame)

    cmds.currentTime(
        frame,
        edit=True
    )

    try:
        cmds.refresh(
            force=True
        )
    except Exception:
        pass

    print(
        "Timeline reset to frame: {}".format(
            frame
        )
    )

    return frame