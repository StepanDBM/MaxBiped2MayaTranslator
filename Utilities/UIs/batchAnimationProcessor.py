import os
import sys
import shutil
import traceback
from importlib import reload

import maya.cmds as cmds

from Utilities.UIs import fbxFileReader
from Utilities.UIs import UImLogger
from Pipeline import animationBakePipeline

reload(fbxFileReader)
reload(UImLogger)
reload(animationBakePipeline)


def ensure_project_root(project_root):
    project_root = os.path.normpath(project_root)

    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    return project_root


THIS_SCENE_TOKEN = "THIS SCENE"


def is_this_scene_token(path):
    if not path:
        return False

    return path.strip().upper() == THIS_SCENE_TOKEN


def get_current_scene_rig_name():
    scene_path = cmds.file(
        q=True,
        sceneName=True
    )

    if scene_path:
        return safe_folder_name_from_file(
            scene_path
        )

    return "CurrentScene"


def save_current_scene_snapshot(rig_output_dir, rig_name):
    """
    Saves the currently open scene as a reusable clean source scene.

    Every animation job should reopen this snapshot before importing/baking.
    """

    if not os.path.exists(rig_output_dir):
        os.makedirs(rig_output_dir)

    snapshot_path = os.path.join(
        rig_output_dir,
        rig_name + "_THIS_SCENE_SOURCE.ma"
    )

    cmds.file(
        rename=snapshot_path
    )

    cmds.file(
        save=True,
        type="mayaAscii"
    )

    return snapshot_path

def is_ma_file(path):
    return path.lower().endswith(".ma")


def is_fbx_file(path):
    return path.lower().endswith(".fbx")


def safe_folder_name_from_file(path):
    base = os.path.splitext(
        os.path.basename(path)
    )[0]

    bad_chars = [
        " ",
        ":",
        ";",
        ",",
        ".",
        "-",
        "(",
        ")",
        "[",
        "]",
        "{",
        "}",
    ]

    for char in bad_chars:
        base = base.replace(
            char,
            "_"
        )

    while "__" in base:
        base = base.replace(
            "__",
            "_"
        )

    return base.strip("_")


def process_animation_batch(ui_state):
    """
    Animation batch processor.

    Modes:
        Referencing ON:
            Animation scenes reference the source rig .ma.
            Original rig stays untouched.

        Referencing OFF:
            Old behavior.
            Rig scene is copied/opened, then animation is baked into that scene.

        Current Scene:
            If left/source list is empty or contains THIS SCENE,
            the current scene is saved as a source snapshot first.
    """

    source_file_list = ui_state.get("sourceFileList") or ui_state.get("fileList")
    animation_file_list = ui_state.get("animationFileList")

    output_field = ui_state["outputField"]
    project_root_field = ui_state["projectRootField"]
    progress_control = ui_state["progressControl"]
    status_label = ui_state["statusLabel"]
    logger = ui_state["logger"]

    reference_checkbox = ui_state.get(
        "referenceRigCheckBox"
    )

    reference_rig = True

    if reference_checkbox and cmds.checkBox(
        reference_checkbox,
        q=True,
        exists=True
    ):
        reference_rig = cmds.checkBox(
            reference_checkbox,
            q=True,
            value=True
        )

    source_files = fbxFileReader.get_list_items(
        source_file_list
    )

    animation_files = fbxFileReader.get_list_items(
        animation_file_list
    )

    use_current_scene = False
    rig_scene = None

    if not source_files:
        use_current_scene = True

    elif len(source_files) == 1 and is_this_scene_token(source_files[0]):
        use_current_scene = True

    elif len(source_files) == 1:
        rig_scene = source_files[0]

        if not is_ma_file(rig_scene):
            cmds.warning(
                "Animation mode requires one .ma auto-rig in the left/source list, "
                "or an empty left/source list to use the current scene."
            )
            return

    else:
        cmds.warning(
            "Animation mode requires exactly one .ma auto-rig in the left/source list, "
            "or an empty left/source list to use the current scene."
        )
        return

    if not animation_files:
        cmds.warning(
            "Animation mode requires at least one .fbx animation file on the right."
        )
        return

    non_fbx_anims = [
        path for path in animation_files
        if not is_fbx_file(path)
    ]

    if non_fbx_anims:
        cmds.warning(
            "Animation mode only accepts .fbx animation files on the right."
        )

        if logger:
            logger.append(
                "ERROR: Non-FBX animation files found:"
            )

            for path in non_fbx_anims:
                logger.append(
                    path
                )

        return

    output_dir = cmds.textField(
        output_field,
        q=True,
        text=True
    ).strip()

    if not output_dir:
        cmds.warning(
            "No output folder selected."
        )
        return

    output_dir = os.path.normpath(
        output_dir
    )

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    project_root = cmds.textField(
        project_root_field,
        q=True,
        text=True
    ).strip()

    if not project_root:
        cmds.warning(
            "No project root set."
        )
        return

    ensure_project_root(
        project_root
    )

    if use_current_scene:
        rig_name = get_current_scene_rig_name()

    else:
        rig_name = safe_folder_name_from_file(
            rig_scene
        )

    rig_output_dir = os.path.join(
        output_dir,
        rig_name
    )

    animations_output_dir = os.path.join(
        rig_output_dir,
        rig_name + "_Animations"
    )

    if not os.path.exists(rig_output_dir):
        os.makedirs(rig_output_dir)

        if logger:
            logger.append("Created missing rig output folder:")
            logger.append(rig_output_dir)

    else:
        if logger:
            logger.append("Using existing rig output folder:")
            logger.append(rig_output_dir)

    if not os.path.exists(animations_output_dir):
        os.makedirs(animations_output_dir)

        if logger:
            logger.append("Created missing animations folder:")
            logger.append(animations_output_dir)

    else:
        if logger:
            logger.append("Using existing animations folder:")
            logger.append(animations_output_dir)

    # --------------------------------------------------
    # DETERMINE RIG SOURCE PATH
    # --------------------------------------------------

    if use_current_scene:
        rig_source_path = save_current_scene_snapshot(
            rig_output_dir,
            rig_name
        )

        if logger:
            logger.append("Using current scene snapshot as rig source:")
            logger.append(rig_source_path)

    else:

        if reference_rig:
            # New behavior:
            # use the selected .ma directly as the referenced rig.
            rig_source_path = os.path.normpath(
                rig_scene
            )

            if logger:
                logger.append("Using selected .ma as referenced rig source:")
                logger.append(rig_source_path)

        else:
            # Old behavior:
            # copy selected rig into the output rig folder and open it directly.
            rig_copy_path = os.path.join(
                rig_output_dir,
                rig_name + ".ma"
            )

            try:
                source_rig_norm = os.path.normcase(
                    os.path.normpath(rig_scene)
                )

                target_rig_norm = os.path.normcase(
                    os.path.normpath(rig_copy_path)
                )

                if source_rig_norm != target_rig_norm:
                    shutil.copy2(
                        rig_scene,
                        rig_copy_path
                    )

                    if logger:
                        logger.append("Copied rig scene:")
                        logger.append(rig_copy_path)

                else:
                    if logger:
                        logger.append("Rig scene is already in the expected location:")
                        logger.append(rig_copy_path)

            except Exception:
                if logger:
                    logger.append("Warning: Could not copy rig scene to output folder.")
                    logger.append(traceback.format_exc())

                rig_copy_path = rig_scene

            rig_source_path = rig_copy_path

    total_units = (
        1 +
        len(animation_files) * animationBakePipeline.ANIMATION_PIPELINE_STEP_COUNT
    )

    current_unit = [
        0
    ]

    def advance_progress(label):
        current_unit[0] += 1

        cmds.progressBar(
            progress_control,
            e=True,
            maxValue=total_units,
            progress=current_unit[0],
            ann="{}/{} - {}".format(
                current_unit[0],
                total_units,
                label
            )
        )

        cmds.text(
            status_label,
            e=True,
            label="{}/{} - {}".format(
                current_unit[0],
                total_units,
                label
            )
        )

        if logger:
            logger.append(
                "[PROGRESS] {}/{} - {}".format(
                    current_unit[0],
                    total_units,
                    label
                )
            )

        cmds.refresh()

    cmds.progressBar(
        progress_control,
        e=True,
        maxValue=total_units,
        progress=0
    )

    cmds.text(
        status_label,
        e=True,
        label="Starting animation batch..."
    )

    logger.append("")
    logger.append("=" * 80)
    logger.append("ANIMATION BATCH START")
    logger.append("=" * 80)

    logger.append("Rig scene:")

    if use_current_scene:
        logger.append(THIS_SCENE_TOKEN)
    else:
        logger.append(rig_scene)

    logger.append("Referencing:")
    logger.append(str(reference_rig))

    logger.append("Rig output folder:")
    logger.append(rig_output_dir)

    logger.append("Rig source path:")
    logger.append(rig_source_path)

    logger.append("Animation output folder:")
    logger.append(animations_output_dir)

    logger.append("Animation file count: {}".format(len(animation_files)))
    logger.append("=" * 80)

    advance_progress(
        "Prepared rig animation output folders"
    )

    success_count = 0
    failed_count = 0

    for animation_path in animation_files:

        animation_name = safe_folder_name_from_file(
            animation_path
        )

        output_scene = os.path.join(
            animations_output_dir,
            "{}_{}.ma".format(
                rig_name,
                animation_name
            )
        )

        logger.append("")
        logger.append("-" * 80)
        logger.append("ANIMATION JOB")
        logger.append("Rig source:")
        logger.append(rig_source_path)
        logger.append("Animation FBX:")
        logger.append(animation_path)
        logger.append("Output scene:")
        logger.append(output_scene)
        logger.append("Referencing:")
        logger.append(str(reference_rig))
        logger.append("-" * 80)

        try:
            with UImLogger.capture_prints(logger):

                animationBakePipeline.run_animation_bake_pipeline(
                    rig_scene_path=rig_source_path,
                    animation_fbx_path=animation_path,
                    output_scene_path=output_scene,
                    progress_callback=advance_progress,
                    sample_by=1,
                    clear_keys=True,
                    delete_imported=True,
                    save_scene=True,
                    reference_rig=reference_rig
                )

            success_count += 1

        except Exception:

            failed_count += 1

            logger.append("")
            logger.append("=" * 80)
            logger.append("ERROR WHILE BAKING ANIMATION")
            logger.append("=" * 80)
            logger.append("Animation FBX:")
            logger.append(animation_path)
            logger.append("Output scene:")
            logger.append(output_scene)
            logger.append(traceback.format_exc())
            logger.append("=" * 80)

    cmds.text(
        status_label,
        e=True,
        label="Animation batch complete. Success: {} | Failed: {}".format(
            success_count,
            failed_count
        )
    )

    logger.append("")
    logger.append("=" * 80)
    logger.append("ANIMATION BATCH COMPLETE")
    logger.append("Success: {}".format(success_count))
    logger.append("Failed: {}".format(failed_count))
    logger.append("=" * 80)
    """
    New animation mode scaffold.

    Expected:
        left/source list:
            exactly one .ma auto-rig

        right/animation list:
            one or more .fbx animation skeleton files

    Current status:
        validates inputs
        creates output folder structure
        copies rig scene
        logs intended animation output scenes

    Actual animation baking will be added next.
    """

    source_file_list = ui_state.get("sourceFileList") or ui_state.get("fileList")
    animation_file_list = ui_state.get("animationFileList")

    output_field = ui_state["outputField"]
    project_root_field = ui_state["projectRootField"]
    progress_control = ui_state["progressControl"]
    status_label = ui_state["statusLabel"]
    logger = ui_state["logger"]

    source_files = fbxFileReader.get_list_items(source_file_list)

    animation_files = fbxFileReader.get_list_items(animation_file_list)

    use_current_scene = False
    rig_scene = None

    if not source_files:
        use_current_scene = True

    elif len(source_files) == 1 and is_this_scene_token(source_files[0]):
        use_current_scene = True

    elif len(source_files) == 1:
        rig_scene = source_files[0]

        if not is_ma_file(rig_scene):
            cmds.warning(
                "Animation mode requires one .ma auto-rig in the left/source list, "
                "or an empty left/source list to use the current scene."
            )
            return

    else:
        cmds.warning(
            "Animation mode requires exactly one .ma auto-rig in the left/source list, "
            "or an empty left/source list to use the current scene."
        )
        return

    if not animation_files:
        cmds.warning(
            "Animation mode requires at least one .fbx animation file on the right."
        )
        return

    non_fbx_anims = [
        path for path in animation_files
        if not is_fbx_file(path)
    ]

    if non_fbx_anims:
        cmds.warning(
            "Animation mode only accepts .fbx animation files on the right."
        )

        if logger:
            logger.append(
                "ERROR: Non-FBX animation files found:"
            )

            for path in non_fbx_anims:
                logger.append(
                    path
                )

        return

    output_dir = cmds.textField(
        output_field,
        q=True,
        text=True
    ).strip()

    if not output_dir:
        cmds.warning(
            "No output folder selected."
        )
        return

    output_dir = os.path.normpath(
        output_dir
    )

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    project_root = cmds.textField(
        project_root_field,
        q=True,
        text=True
    ).strip()

    if not project_root:
        cmds.warning("No project root set.")
        return

    ensure_project_root(project_root)

    if use_current_scene:
        rig_name = get_current_scene_rig_name()

    else:
        rig_name = safe_folder_name_from_file(
            rig_scene
        )

    """
    Expected structure:
       output_dir/
          RigName/
            RigName.ma or RigName_THIS_SCENE_SOURCE.ma
            RigName_Animations/
    """

    rig_output_dir = os.path.join(
        output_dir,
        rig_name
    )

    animations_output_dir = os.path.join(
        rig_output_dir,
        rig_name + "_Animations"
    )

    if not os.path.exists(rig_output_dir):
        os.makedirs(rig_output_dir)

        if logger:
            logger.append("Created missing rig output folder:")
            logger.append(rig_output_dir)

    else:
        if logger:
            logger.append("Using existing rig output folder:")
            logger.append(rig_output_dir)

    if not os.path.exists(animations_output_dir):
        os.makedirs(animations_output_dir)

        if logger:
            logger.append("Created missing animations folder:")
            logger.append(animations_output_dir)

    else:
        if logger:
            logger.append("Using existing animations folder:")
            logger.append(animations_output_dir)

    if use_current_scene:
        rig_copy_path = save_current_scene_snapshot(
            rig_output_dir,
            rig_name
        )

        if logger:
            logger.append("Using current scene snapshot:")
            logger.append(rig_copy_path)

    else:
        expected_rig_output_dir = os.path.join(
            output_dir,
            rig_name
        )

        selected_rig_dir = os.path.dirname(
            os.path.normpath(rig_scene)
        )

        selected_rig_base = os.path.basename(
            selected_rig_dir
        )

        if selected_rig_base == rig_name:
            rig_output_dir = selected_rig_dir

            animations_output_dir = os.path.join(
                rig_output_dir,
                rig_name + "_Animations"
            )

            if not os.path.exists(animations_output_dir):
                os.makedirs(animations_output_dir)

        else:
            rig_output_dir = expected_rig_output_dir

        rig_copy_path = os.path.join(
            rig_output_dir,
            rig_name + ".ma"
        )

        try:
            source_rig_norm = os.path.normcase(
                os.path.normpath(rig_scene)
            )

            target_rig_norm = os.path.normcase(
                os.path.normpath(rig_copy_path)
            )

            if source_rig_norm != target_rig_norm:
                shutil.copy2(
                    rig_scene,
                    rig_copy_path
                )

                if logger:
                    logger.append("Copied rig scene:")
                    logger.append(rig_copy_path)

            else:
                if logger:
                    logger.append("Rig scene is already in the expected location:")
                    logger.append(rig_copy_path)

        except Exception:
            if logger:
                logger.append("Warning: Could not copy rig scene to output folder.")
                logger.append(traceback.format_exc())

            rig_copy_path = rig_scene

    total_units = (
        1 +
        len(animation_files) * animationBakePipeline.ANIMATION_PIPELINE_STEP_COUNT
    )
    current_unit = [0]

    def advance_progress(label):
        current_unit[0] += 1

        cmds.progressBar(
            progress_control,
            e=True,
            maxValue=total_units,
            progress=current_unit[0],
            ann="{}/{} - {}".format(
                current_unit[0],
                total_units,
                label
            )
        )

        cmds.text(
            status_label,
            e=True,
            label="{}/{} - {}".format(
                current_unit[0],
                total_units,
                label
            )
        )

        if logger:
            logger.append(
                "[PROGRESS] {}/{} - {}".format(
                    current_unit[0],
                    total_units,
                    label
                )
            )

        cmds.refresh()

    cmds.progressBar(
        progress_control,
        e=True,
        maxValue=total_units,
        progress=0
    )

    cmds.text(
        status_label,
        e=True,
        label="Starting animation batch..."
    )

    logger.append("")
    logger.append("=" * 80)
    logger.append("ANIMATION BATCH START")
    logger.append("=" * 80)
    logger.append("Rig scene:")

    if use_current_scene:
        logger.append(THIS_SCENE_TOKEN)
    else:
        logger.append(rig_scene)
    logger.append("Rig output folder:")
    logger.append(rig_output_dir)
    logger.append("Rig copy:")
    logger.append(rig_copy_path)
    logger.append("Animation output folder:")
    logger.append(animations_output_dir)
    logger.append("Animation file count: {}".format(len(animation_files)))
    logger.append("=" * 80)

    advance_progress("Prepared rig animation output folders")

    success_count = 0
    failed_count = 0

    for animation_path in animation_files:

        animation_name = safe_folder_name_from_file(animation_path)

        output_scene = os.path.join(
            animations_output_dir,
            "{}_{}.ma".format(
                rig_name,
                animation_name
            )
        )

        logger.append("")
        logger.append("-" * 80)
        logger.append("ANIMATION JOB")
        logger.append("Rig scene:")
        logger.append(rig_copy_path)
        logger.append("Animation FBX:")
        logger.append(animation_path)
        logger.append("Output scene:")
        logger.append(output_scene)
        logger.append("-" * 80)

        try:
            with UImLogger.capture_prints(logger):

                animationBakePipeline.run_animation_bake_pipeline(
                    rig_scene_path=rig_copy_path,
                    animation_fbx_path=animation_path,
                    output_scene_path=output_scene,
                    progress_callback=advance_progress,
                    sample_by=1,
                    clear_keys=True,
                    delete_imported=True,
                    save_scene=True
                )

            success_count += 1

        except Exception:

            failed_count += 1

            logger.append("")
            logger.append("=" * 80)
            logger.append("ERROR WHILE BAKING ANIMATION")
            logger.append("=" * 80)
            logger.append("Animation FBX:")
            logger.append(animation_path)
            logger.append("Output scene:")
            logger.append(output_scene)
            logger.append(traceback.format_exc())
            logger.append("=" * 80)

    cmds.text(
        status_label,
        e=True,
        label="Animation batch complete. Success: {} | Failed: {}".format(
            success_count,
            failed_count
        )
    )

    logger.append("")
    logger.append("=" * 80)
    logger.append("ANIMATION BATCH COMPLETE")
    logger.append("Success: {}".format(success_count))
    logger.append("Failed: {}".format(failed_count))
    logger.append("=" * 80)