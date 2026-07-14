import traceback

import maya.cmds as cmds

from Utilities.UIs import UImLogger


def process_current_scene(ui_state, backend_runner):
    """
    Runs the rig pipeline on the currently open Maya scene.

    This does NOT:
        - import an FBX
        - export from MAX
        - create a new Maya scene
        - save the scene automatically

    It only runs the backend pipeline on whatever is already open.
    """

    progress_control = ui_state["progressControl"]
    status_label = ui_state["statusLabel"]
    logger = ui_state["logger"]

    pipeline_step_count = 16

    total_units = pipeline_step_count
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
        label="Running pipeline on current scene..."
    )

    logger.append("")
    logger.append("=" * 80)
    logger.append("CURRENT SCENE PIPELINE START")
    logger.append("=" * 80)

    try:
        with UImLogger.capture_prints(logger):

            backend_runner(
                progress_callback=advance_progress
            )

        cmds.text(
            status_label,
            e=True,
            label="Current scene pipeline complete."
        )

        logger.append("")
        logger.append("=" * 80)
        logger.append("CURRENT SCENE PIPELINE COMPLETE")
        logger.append("=" * 80)

    except Exception:

        cmds.text(
            status_label,
            e=True,
            label="Current scene pipeline failed."
        )

        logger.append("")
        logger.append("=" * 80)
        logger.append("CURRENT SCENE PIPELINE ERROR")
        logger.append("=" * 80)
        logger.append(
            traceback.format_exc()
        )
        logger.append("=" * 80)