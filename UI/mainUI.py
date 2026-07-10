# mainUI.py

import os
import importlib

import maya.cmds as cmds

from Utilities.UIs import UImLogger
from Utilities.UIs import fbxFileReader
from Utilities.UIs import batchProcessor

from Pipeline import rigBuildPipeline

importlib.reload(UImLogger)
importlib.reload(fbxFileReader)
importlib.reload(batchProcessor)
importlib.reload(rigBuildPipeline)


WINDOW = "MaxMayaRigTranslator_UI"


def get_default_project_root():
    """
    Returns the project root.

    If this file is imported from disk, __file__ exists.
    Since this file lives inside /UI, we go one folder up.
    """

    if "__file__" in globals():
        return os.path.dirname(
            os.path.dirname(
                os.path.abspath(__file__)
            )
        )

    return r"E:\Work\3D\my_3D\KANEDA\Projects\Scripting\MaxMayaRigTranslator"


def build_ui():
    global projectRootField
    global outputField
    global fileList
    global logHost
    global progressControl
    global statusLabel
    global logger
    global ui_state

    if cmds.window(
        WINDOW,
        exists=True
    ):
        cmds.deleteUI(WINDOW)

    cmds.window(
        WINDOW,
        title="Max Maya Rig Translator",
        sizeable=True,
        widthHeight=(850, 650)
    )

    # Main resizable form
    mainForm = cmds.formLayout()

    # Top fixed-area column
    topColumn = cmds.columnLayout(
        adjustableColumn=True,
        rowSpacing=6,
        parent=mainForm
    )

    # Project Root
    cmds.text(
        label="Project Root"
    )

    cmds.rowLayout(
        numberOfColumns=2,
        adjustableColumn=1
    )

    projectRootField = cmds.textField(
        text=get_default_project_root()
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

    cmds.separator(
        height=8
    )

    # FBX File Selection

    cmds.text(
        label="FBX Files To Convert"
    )

    fileList = cmds.textScrollList(
        allowMultiSelection=True,
        height=150
    )

    cmds.rowLayout(
        numberOfColumns=4,
        adjustableColumn=1,
        columnWidth4=(180, 180, 180, 180)
    )

    cmds.button(
        label="Add FBX Files",
        command=lambda *args: fbxFileReader.browse_files(
            fileList,
            logger
        )
    )

    cmds.button(
        label="Add Folder FBXs",
        command=lambda *args: fbxFileReader.browse_folder_for_fbx(
            fileList,
            logger
        )
    )

    cmds.button(
        label="Remove Selected",
        command=lambda *args: fbxFileReader.remove_selected_files(
            fileList,
            logger
        )
    )

    cmds.button(
        label="Clear List",
        command=lambda *args: fbxFileReader.clear_files(
            fileList,
            logger
        )
    )

    cmds.setParent("..")

    cmds.separator(
        height=8
    )

    # Output Folder
    cmds.text(
        label="Output Folder"
    )

    cmds.rowLayout(
        numberOfColumns=2,
        adjustableColumn=1
    )

    outputField = cmds.textField(
        text=os.path.join(
            get_default_project_root(),
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

    cmds.separator(
        height=8
    )

    # Run Button

    cmds.button(
        label="Batch Create Animator Scenes",
        height=45,
        command=lambda *args: batchProcessor.process_files(
            ui_state,
            rigBuildPipeline.run_backend_pipeline
        )
    )

    cmds.separator(
        height=8
    )

    # Progress Bar

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

    cmds.separator(
        height=8
    )

    # Debug Log Header
    # This is outside topColumn so the log can resize.

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

    """
    Resizable Debug Log Host
    This Maya layout will contain the Qt QTextEdit logger.
    No fixed height here.
    """
    logHost = cmds.formLayout(
        parent=mainForm
    )

    # Attach layout pieces

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

    # Runtime UI State
    logger = UImLogger.UILogger.from_maya_layout(
        logHost
    )

    ui_state = {
        "projectRootField": projectRootField,
        "outputField": outputField,
        "fileList": fileList,
        "progressControl": progressControl,
        "statusLabel": statusLabel,
        "logger": logger
    }

    cmds.showWindow(
        WINDOW
    )