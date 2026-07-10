import os

import maya.cmds as cmds


def get_list_items(file_list):
    items = cmds.textScrollList(
        file_list,
        q=True,
        allItems=True
    )

    return items or []


def add_file_to_list(file_list, path):
    path = os.path.normpath(path)

    current = get_list_items(file_list)

    if path not in current:
        cmds.textScrollList(
            file_list,
            e=True,
            append=path
        )


def browse_files(file_list, logger=None):
    paths = cmds.fileDialog2(
        fileMode=4,
        caption="Select FBX Files",
        fileFilter="FBX Files (*.fbx);;All Files (*.*)"
    )

    if not paths:
        return

    for path in paths:
        add_file_to_list(
            file_list,
            path
        )

    if logger:
        logger.append(
            "Added {} file(s).".format(
                len(paths)
            )
        )


def browse_folder_for_fbx(file_list, logger=None):
    folders = cmds.fileDialog2(
        fileMode=3,
        caption="Select Folder Containing FBXs"
    )

    if not folders:
        return

    folder = folders[0]

    count = 0

    for name in os.listdir(folder):

        if not name.lower().endswith(".fbx"):
            continue

        add_file_to_list(
            file_list,
            os.path.join(
                folder,
                name
            )
        )

        count += 1

    if logger:
        logger.append(
            "Added {} FBX file(s) from folder.".format(
                count
            )
        )


def remove_selected_files(file_list, logger=None):
    selected = cmds.textScrollList(
        file_list,
        q=True,
        selectItem=True
    ) or []

    for item in selected:
        cmds.textScrollList(
            file_list,
            e=True,
            removeItem=item
        )

    if logger:
        logger.append(
            "Removed {} selected file(s).".format(
                len(selected)
            )
        )


def clear_files(file_list, logger=None):
    cmds.textScrollList(
        file_list,
        e=True,
        removeAll=True
    )

    if logger:
        logger.append(
            "Cleared file list."
        )


def browse_folder_into_text_field(text_field, caption):
    folders = cmds.fileDialog2(
        fileMode=3,
        caption=caption
    )

    if not folders:
        return

    cmds.textField(
        text_field,
        e=True,
        text=folders[0]
    )