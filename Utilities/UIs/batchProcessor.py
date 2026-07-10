import os
import sys
import traceback

import maya.cmds as cmds

from Utilities.UIs import fbxFileReader
from Utilities.UIs import UImLogger


def ensure_project_root(project_root):
    """
    Adds project root to sys.path.
    """

    project_root = os.path.normpath(project_root)

    if project_root not in sys.path:
        sys.path.insert(
            0,
            project_root
        )

    return project_root


def import_fbx(path):
    """
    Imports an FBX into a fresh Maya scene.
    """

    path = os.path.normpath(path)

    if not os.path.exists(path):
        raise RuntimeError(
            "FBX does not exist: {}".format(path)
        )

    cmds.file(
        new=True,
        force=True
    )

    cmds.file(
        path,
        i=True,
        type="FBX",
        ignoreVersion=True,
        mergeNamespacesOnClash=False,
        options="fbx",
        preserveReferences=True
    )


def safe_scene_name_from_file(path):
    """
    Converts an FBX filename into a clean Maya scene filename.
    """

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


def save_output_scene(input_fbx, output_dir):
    """
    Saves the converted rig scene.
    """

    scene_name = safe_scene_name_from_file(
        input_fbx
    )

    save_path = os.path.join(
        output_dir,
        scene_name + "_animRig.ma"
    )

    cmds.file(
        rename=save_path
    )

    cmds.file(
        save=True,
        type="mayaAscii"
    )

    return save_path


def process_files(ui_state, backend_runner):
    """
    Batch process all listed FBXs.

    backend_runner:
        function that runs your rig pipeline on the current scene.
    """

    file_list = ui_state["fileList"]
    output_field = ui_state["outputField"]
    project_root_field = ui_state["projectRootField"]
    progress_control = ui_state["progressControl"]
    status_label = ui_state["statusLabel"]
    logger = ui_state["logger"]

    files = fbxFileReader.get_list_items(
        file_list
    )

    if not files:
        cmds.warning(
            "No FBX files selected."
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

    total = len(files)

    # Your backend currently has 12 reported steps.
    # Plus:
    #   1 import step
    #   1 save step
    pipeline_step_count = 12

    units_per_file = pipeline_step_count + 2

    total_units = len(files) * units_per_file
    current_unit = [0]


    def advance_progress(label):
        current_unit[0] += 1

        cmds.progressBar(
            progress_control,
            e=True,
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
        label="Starting..."
    )

    logger.append("=" * 80)
    logger.append("BATCH START")
    logger.append("Files: {}".format(total))
    logger.append("Output: {}".format(output_dir))
    logger.append("=" * 80)

    success_count = 0
    failed_count = 0

    for index, fbx_path in enumerate(files, start=1):

        logger.append("")
        logger.append("#" * 80)
        logger.append(
            "PROCESSING {}/{}".format(
                index,
                total
            )
        )
        logger.append(fbx_path)
        logger.append("#" * 80)

        cmds.text(
            status_label,
            e=True,
            label="Processing {}/{}".format(
                index,
                total
            )
        )

        try:
            with UImLogger.capture_prints(logger):

                advance_progress(
                    "Importing FBX"
                )

                import_fbx(
                    fbx_path
                )

                backend_runner(
                    progress_callback=advance_progress
                )

                advance_progress(
                    "Saving Maya scene"
                )

                saved_path = save_output_scene(
                    fbx_path,
                    output_dir
                )

                print("")
                print("Saved scene:")
                print(saved_path)

            success_count += 1

        except Exception:

            failed_count += 1

            logger.append(
                "ERROR while processing:"
            )

            logger.append(
                fbx_path
            )

            logger.append(
                traceback.format_exc()
            )
        cmds.refresh()

    cmds.text(
        status_label,
        e=True,
        label="Done. Success: {} | Failed: {}".format(
            success_count,
            failed_count
        )
    )

    logger.append("")
    logger.append("=" * 80)
    logger.append("BATCH COMPLETE")
    logger.append("Success: {}".format(success_count))
    logger.append("Failed: {}".format(failed_count))
    logger.append("=" * 80)