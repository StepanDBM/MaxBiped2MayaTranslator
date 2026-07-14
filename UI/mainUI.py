# mainUI.py

import os
import importlib

import maya.cmds as cmds

from Utilities.UIs import UImLogger
from Utilities.UIs import fbxFileReader
from Utilities.UIs import sceneProcessor
from Utilities.UIs import batchAnimationProcessor as batchAnimProc
from Utilities.UIs import batchConversionProcessor as batchConvProc

from Pipeline import rigBuildPipeline

importlib.reload(UImLogger)
importlib.reload(fbxFileReader)
importlib.reload(sceneProcessor)
importlib.reload(batchAnimProc)
importlib.reload(batchConvProc)
importlib.reload(rigBuildPipeline)


WINDOW = "MaxMayaRigTranslator_UI"


def build_ui(project_root):
    global projectRootField
    global outputField

    global sourceFileList
    global animationFileList

    # Backwards compatibility if some old code still reads fileList.
    global fileList

    global logHost
    global progressControl
    global statusLabel
    global logger
    global ui_state

    if cmds.window(WINDOW, exists=True):
        cmds.deleteUI(WINDOW)

    cmds.window(
        WINDOW,
        title="Max Maya Rig Translator",
        sizeable=True,
        widthHeight=(1000, 700)
    )

    # Main resizable form
    mainForm = cmds.formLayout()

    # Top fixed-area column
    topColumn = cmds.columnLayout(
        adjustableColumn=True,
        rowSpacing=6,
        parent=mainForm
    )

    # --------------------------------------------------
    # CURRENT SCENE RUN BUTTON
    # --------------------------------------------------

    cmds.button(
        label="Run Pipeline On Current Scene",
        height=38,
        command=lambda *args: sceneProcessor.process_current_scene(
            ui_state,
            rigBuildPipeline.run_backend_pipeline
        )
    )

    cmds.separator(height=8)

    # --------------------------------------------------
    # PROJECT ROOT
    # --------------------------------------------------

    cmds.text(label="Project Root")

    cmds.rowLayout(
        numberOfColumns=2,
        adjustableColumn=1
    )

    projectRootField = cmds.textField(
        text=project_root
    )

    cmds.button(
        label="Browse",
        width=90,
        command=lambda *args: fbxFileReader.browse_folder_into_text_field(
            projectRootField,
            "Select Project Root"
        )
    )

    cmds.setParent("..")

    cmds.separator(height=8)
    # --------------------------------------------------
    # DUAL FILE LISTS
    # --------------------------------------------------

    listsForm = cmds.formLayout(
        parent=topColumn
    )

    # --------------------------------------------------
    # LEFT LIST - SOURCE / RIG FILES
    # --------------------------------------------------

    leftColumn = cmds.columnLayout(
        adjustableColumn=True,
        rowSpacing=4,
        parent=listsForm
    )

    cmds.text(
        label="Selected Source / Rig Files",
        align="left"
    )

    cmds.text(
        label="Build mode: .fbx / .max    |    Animation mode: one .ma auto-rig",
        align="left"
    )

    sourceFileList = cmds.textScrollList(
        allowMultiSelection=True,
        height=150
    )

    cmds.rowLayout(
        numberOfColumns=4,
        adjustableColumn=1,
        columnWidth4=(120, 120, 120, 120)
    )

    cmds.button(
        label="Add Files",
        command=lambda *args: fbxFileReader.browse_source_files(
            sourceFileList,
            logger
        )
    )

    cmds.button(
        label="Add Folder",
        command=lambda *args: fbxFileReader.browse_source_folder(
            sourceFileList,
            logger
        )
    )

    cmds.button(
        label="Remove",
        command=lambda *args: fbxFileReader.remove_selected_files(
            sourceFileList,
            logger
        )
    )

    cmds.button(
        label="Clear",
        command=lambda *args: fbxFileReader.clear_files(
            sourceFileList,
            logger
        )
    )

    cmds.setParent("..")        # leave left button row
    cmds.setParent(listsForm)   # leave left column / return to form


    # --------------------------------------------------
    # RIGHT LIST - ANIMATION FILES
    # --------------------------------------------------

    rightColumn = cmds.columnLayout(
        adjustableColumn=True,
        rowSpacing=4,
        parent=listsForm
    )

    cmds.text(
        label="Selected Animation Files",
        align="left"
    )

    cmds.text(
        label="Animation mode only: baked skeleton animation .fbx files",
        align="left"
    )

    animationFileList = cmds.textScrollList(
        allowMultiSelection=True,
        height=150
    )

    cmds.rowLayout(
        numberOfColumns=4,
        adjustableColumn=1,
        columnWidth4=(120, 120, 120, 120)
    )

    cmds.button(
        label="Add Anim FBXs",
        command=lambda *args: fbxFileReader.browse_animation_files(
            animationFileList,
            logger
        )
    )

    cmds.button(
        label="Add Folder",
        command=lambda *args: fbxFileReader.browse_animation_folder(
            animationFileList,
            logger
        )
    )

    cmds.button(
        label="Remove",
        command=lambda *args: fbxFileReader.remove_selected_files(
            animationFileList,
            logger
        )
    )

    cmds.button(
        label="Clear",
        command=lambda *args: fbxFileReader.clear_files(
            animationFileList,
            logger
        )
    )

    cmds.setParent("..")        # leave right button row
    cmds.setParent(listsForm)   # return to form


    # --------------------------------------------------
    # MAKE BOTH SIDES 50/50
    # --------------------------------------------------

    cmds.formLayout(
        listsForm,
        e=True,
        attachForm=[
            (leftColumn, "top", 0),
            (leftColumn, "left", 0),
            (leftColumn, "bottom", 0),

            (rightColumn, "top", 0),
            (rightColumn, "right", 0),
            (rightColumn, "bottom", 0),
        ],
        attachPosition=[
            (leftColumn, "right", 4, 50),
            (rightColumn, "left", 4, 50),
        ]
    )

    cmds.setParent(topColumn)

    cmds.separator(height=8)

    # --------------------------------------------------
    # OUTPUT FOLDER
    # --------------------------------------------------

    cmds.text(label="Output Folder")

    cmds.rowLayout(
        numberOfColumns=2,
        adjustableColumn=1
    )

    outputField = cmds.textField(
        text=os.path.join(
            project_root,
            "ConvertedScenes"
        )
    )

    cmds.button(
        label="Browse",
        width=90,
        command=lambda *args: fbxFileReader.browse_folder_into_text_field(
            outputField,
            "Select Output Folder"
        )
    )

    cmds.setParent("..")

    cmds.separator(height=8)

    # --------------------------------------------------
    # RUN BUTTON
    # --------------------------------------------------

    buttonForm = cmds.formLayout()

    buildRigButton = cmds.button(
        label="Batch Build Rigs From Source Files",
        height=45,
        command=lambda *args: batchConvProc.process_conversion_batch(
            ui_state,
            rigBuildPipeline.run_backend_pipeline
        )
    )

    bakeAnimButton = cmds.button(
        label="Batch Bake Animations Onto Auto-Rig",
        height=45,
        command=lambda *args: batchAnimProc.process_animation_batch(
            ui_state
        )
    )

    cmds.formLayout(
        buttonForm,
        e=True,
        attachForm=[
            (buildRigButton, "top", 0),
            (buildRigButton, "left", 0),
            (buildRigButton, "bottom", 0),

            (bakeAnimButton, "top", 0),
            (bakeAnimButton, "right", 0),
            (bakeAnimButton, "bottom", 0),
        ],
        attachPosition=[
            (buildRigButton, "right", 4, 50),
            (bakeAnimButton, "left", 4, 50),
        ]
    )

    cmds.setParent("..")

    cmds.separator(height=8)

    # --------------------------------------------------
    # PROGRESS BAR
    # --------------------------------------------------

    cmds.rowLayout(
        numberOfColumns=2,
        adjustableColumn=1
    )

    progressControl = cmds.progressBar(
        maxValue=100,
        width=650
    )

    statusLabel = cmds.text(
        label=""
    )

    cmds.setParent("..")

    cmds.separator(height=8)

    # --------------------------------------------------
    # DEBUG LOG HEADER
    # --------------------------------------------------

    cmds.setParent(mainForm)

    debugHeader = cmds.rowLayout(
        numberOfColumns=2,
        adjustableColumn=1,
        parent=mainForm
    )

    cmds.text(
        label="Debug Log"
    )

    cmds.button(
        label="Clear Log",
        width=100,
        command=lambda *args: logger.clear()
    )

    cmds.setParent(mainForm)

    # --------------------------------------------------
    # RESIZABLE DEBUG LOG HOST
    # --------------------------------------------------

    logHost = cmds.formLayout(
        parent=mainForm
    )

    # --------------------------------------------------
    # FORM ATTACHMENTS
    # --------------------------------------------------

    cmds.formLayout(
        mainForm,
        e=True,
        attachForm=[
            (topColumn, "top", 6),
            (topColumn, "left", 6),
            (topColumn, "right", 6),

            (debugHeader, "left", 6),
            (debugHeader, "right", 6),

            (logHost, "left", 6),
            (logHost, "right", 6),
            (logHost, "bottom", 6),
        ],
        attachControl=[
            (debugHeader, "top", 8, topColumn),
            (logHost, "top", 4, debugHeader),
        ]
    )

    # --------------------------------------------------
    # RUNTIME UI STATE
    # --------------------------------------------------

    logger = UImLogger.UILogger.from_maya_layout(
        logHost
    )

    # Backwards compatibility:
    # old batchProcessor code may still look for "fileList".
    fileList = sourceFileList

    ui_state = {
        "projectRootField": projectRootField,
        "outputField": outputField,

        "sourceFileList": sourceFileList,
        "animationFileList": animationFileList,

        # temporary old key
        "fileList": sourceFileList,

        "progressControl": progressControl,
        "statusLabel": statusLabel,
        "logger": logger
    }

    cmds.showWindow(WINDOW)