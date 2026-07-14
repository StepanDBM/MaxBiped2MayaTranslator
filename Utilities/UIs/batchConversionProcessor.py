import os
import sys
import traceback
from importlib import reload

import maya.cmds as cmds

from Utilities.UIs import fbxFileReader
from Utilities.UIs import UImLogger
from Utilities import hdls3DsMaxHdl

reload(fbxFileReader)
reload(UImLogger)
reload(hdls3DsMaxHdl)


def ensure_project_root(project_root):
    project_root = os.path.normpath(project_root)

    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    return project_root


def is_ma_file(path):
    return path.lower().endswith(".ma")


def safe_scene_name_from_file(path):
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
        base = base.replace( char, "_" )

    while "__" in base:
        base = base.replace( "__", "_" )

    return base.strip("_")


def save_output_scene(input_fbx, output_dir):
    """
    Saves the converted auto-rig scene using the rig folder hierarchy.

    Output structure:
        output_dir/
            RigName/
                RigName.ma
                RigName_Animations/
    """

    rig_name = safe_scene_name_from_file(input_fbx)

    rig_folder = os.path.join(output_dir, rig_name)

    animations_folder = os.path.join(rig_folder, rig_name + "_Animations")

    if not os.path.exists(rig_folder):
        os.makedirs(rig_folder)

    if not os.path.exists(animations_folder):
        os.makedirs(animations_folder)

    save_path = os.path.join(rig_folder, rig_name + ".ma")

    cmds.file(rename=save_path)

    cmds.file(save=True, type="mayaAscii")

    return save_path


def import_fbx(path):
    """
    Imports an FBX into a fresh Maya scene.

    Uses MEL FBXImport because cmds.file was triggering the Game Importer /
    bad batch import behavior.
    """

    import maya.mel as mel

    path = os.path.normpath(path)

    if not os.path.exists(path):
        raise RuntimeError(
            "FBX does not exist: {}".format(path)
        )

    print("=" * 80)
    print("IMPORTING FBX")
    print(path)
    print("=" * 80)

    cmds.file(new=True, force=True)

    try:
        if not cmds.pluginInfo(
            "fbxmaya",
            q=True,
            loaded=True
        ):
            cmds.loadPlugin("fbxmaya")
    except Exception as e:
        raise RuntimeError(
            "Could not load fbxmaya plugin: {}".format(e)
        )

    fbx_path = path.replace( "\\", "/" )

    fbx_path = fbx_path.replace( '"', '\\"' )

    try:
        mel.eval("FBXResetImport;")
    except Exception:
        pass

    fbx_options = [
        'FBXImportMode -v "add";',
        'FBXImportCameras -v false;',
        'FBXImportLights -v false;',
        'FBXImportShapes -v true;',
        'FBXImportSkins -v true;',
        'FBXImportConstraints -v false;',
        'FBXImportSkeletonDefinitionsAs -v "HumanIK";',
        'FBXImportSetMayaFrameRate -v true;',
        'FBXImportFillTimeline -v true;',
        'FBXImportGenerateLog -v false;',
    ]

    for option in fbx_options:
        try:
            mel.eval(option)
        except Exception:
            pass

    try:
        mel.eval(
            'FBXImport -f "{}";'.format(
                fbx_path
            )
        )
    except Exception as e:
        raise RuntimeError(
            "FBXImport failed for {}: {}".format(
                path,
                e
            )
        )

    joints = cmds.ls(
        type="joint",
        long=True
    ) or []

    print(
        "Imported joint count: {}".format(
            len(joints)
        )
    )

    if not joints:
        raise RuntimeError(
            "FBX imported but no Maya joints were found: {}".format(
                path
            )
        )

    print("First imported joints:")

    for joint in joints[:20]:
        print(
            "  {}".format(joint)
        )

    print("=" * 80)


def process_conversion_batch(
    ui_state,
    backend_runner
):
    """
    Old batch mode.

    Input:
        left/source list:
            .fbx
            .max
            .max.txt

        right/animation list:
            must be empty / ignored by UI

    Behavior:
        .max files are exported to FBX first.
        FBXs are imported into Maya.
        Full rigBuildPipeline runs.
        Output .ma scene is saved.
    """

    source_file_list = ui_state.get("sourceFileList") or ui_state.get("fileList")

    output_field = ui_state["outputField"]
    project_root_field = ui_state["projectRootField"]
    progress_control = ui_state["progressControl"]
    status_label = ui_state["statusLabel"]
    logger = ui_state["logger"]

    files = fbxFileReader.get_list_items(source_file_list)

    if not files:
        cmds.warning("No source files selected.")
        return

    ma_files = [
        path for path in files
        if is_ma_file(path)
    ]

    if ma_files:
        cmds.warning(
            "Conversion mode does not accept .ma files. Use the animation batch system."
        )

        if logger:
            logger.append(
                "ERROR: Conversion mode does not accept .ma files."
            )
            logger.append(
                "Use the animation bake system for .ma auto-rigs."
            )

        return

    output_dir = cmds.textField(
        output_field,
        q=True,
        text=True
    ).strip()

    if not output_dir:
        cmds.warning("No output folder selected.")
        return

    output_dir = os.path.normpath(output_dir)

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

    max_files = []
    fbx_files = []

    for path in files:
        if hdls3DsMaxHdl.is_max_file(path):
            max_files.append(path)
        else:
            fbx_files.append(path)

    pipeline_step_count = 16
    units_per_source = pipeline_step_count + 2
    max_export_units = 1 if max_files else 0

    estimated_source_count = len(fbx_files) + len(max_files)

    total_units = (
        max_export_units +
        estimated_source_count * units_per_source
    )

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
        maxValue=max(total_units, 1),
        progress=0
    )

    cmds.text(
        status_label,
        e=True,
        label="Starting conversion batch..."
    )

    logger.append("=" * 80)
    logger.append("CONVERSION BATCH START")
    logger.append("Input files: {}".format(len(files)))
    logger.append("MAX files: {}".format(len(max_files)))
    logger.append("FBX files: {}".format(len(fbx_files)))
    logger.append("Output: {}".format(output_dir))
    logger.append("=" * 80)

    success_count = 0
    failed_count = 0

    exported_from_max = []

    if max_files:
        try:
            with UImLogger.capture_prints(logger):

                advance_progress(
                    "Exporting MAX files to FBX"
                )

                max_export_dir = os.path.join(
                    output_dir,
                    "_exported_from_max"
                )

                exported_from_max = hdls3DsMaxHdl.export_many_max_to_fbx(
                    max_files,
                    max_export_dir,
                    logger=logger
                )

        except Exception:
            failed_count += len(max_files)

            logger.append("")
            logger.append("=" * 80)
            logger.append("ERROR WHILE EXPORTING MAX FILES")
            logger.append("=" * 80)
            logger.append(
                traceback.format_exc()
            )
            logger.append("=" * 80)

            exported_from_max = []

        missing_max_exports = max(
            0,
            len(max_files) - len(exported_from_max)
        )

        if missing_max_exports:
            failed_count += missing_max_exports

            logger.append(
                "Warning: {} MAX file(s) did not produce FBX output.".format(
                    missing_max_exports
                )
            )

    source_files = []
    source_files.extend(fbx_files)
    source_files.extend(exported_from_max)

    total_units = (
        current_unit[0] +
        len(source_files) * units_per_source
    )

    cmds.progressBar(
        progress_control,
        e=True,
        maxValue=max(total_units, 1)
    )

    if not source_files:
        cmds.text(
            status_label,
            e=True,
            label="Done. No FBX files to process."
        )

        logger.append("")
        logger.append("=" * 80)
        logger.append("CONVERSION BATCH COMPLETE")
        logger.append("Success: {}".format(success_count))
        logger.append("Failed: {}".format(failed_count))
        logger.append("No FBX files were available for Maya processing.")
        logger.append("=" * 80)

        return

    logger.append("")
    logger.append("=" * 80)
    logger.append("MAYA CONVERSION PROCESSING START")
    logger.append("Source FBX files: {}".format(len(source_files)))
    logger.append("=" * 80)

    total_sources = len(source_files)

    for index, source_path in enumerate(source_files, start=1):

        logger.append("")
        logger.append("#" * 80)
        logger.append(
            "PROCESSING {}/{}".format(
                index,
                total_sources
            )
        )
        logger.append(source_path)
        logger.append("#" * 80)

        cmds.text(
            status_label,
            e=True,
            label="Processing {}/{}".format(
                index,
                total_sources
            )
        )

        try:
            with UImLogger.capture_prints(logger):
                advance_progress("Importing FBX")
                import_fbx(source_path)
                backend_runner(progress_callback=advance_progress)
                advance_progress("Saving Maya scene")
                saved_path = save_output_scene(source_path, output_dir)

                print("")
                print("Saved scene:")
                print(saved_path)

            success_count += 1

        except Exception:
            failed_count += 1
            logger.append("ERROR while processing:")
            logger.append(source_path)
            logger.append(traceback.format_exc())

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
    logger.append("CONVERSION BATCH COMPLETE")
    logger.append("Success: {}".format(success_count))
    logger.append("Failed: {}".format(failed_count))
    logger.append("=" * 80)