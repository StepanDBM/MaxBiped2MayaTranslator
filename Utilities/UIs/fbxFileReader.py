import os

import maya.cmds as cmds


# --------------------------------------------------
# BASIC LIST HELPERS
# --------------------------------------------------

def get_list_items(file_list):
    items = cmds.textScrollList(
        file_list,
        q=True,
        allItems=True
    )

    return items or []


def add_file_to_list(file_list, path):
    path = os.path.normpath(path)

    current = get_list_items(
        file_list
    )

    if path not in current:
        cmds.textScrollList(
            file_list,
            e=True,
            append=path
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


# --------------------------------------------------
# SOURCE / RIG FILE LIST
# --------------------------------------------------
# Left list.
#
# Allowed:
#   .fbx
#   .max
#   .ma
#
# Usage:
#   old conversion mode:
#       .fbx / .max
#
#   new animation mode:
#       exactly one .ma auto-rig


def is_source_file(path):
    lower = path.lower()

    return (
        lower.endswith(".fbx") or
        lower.endswith(".max") or
        lower.endswith(".ma")
    )


def browse_source_files(file_list, logger=None):
    paths = cmds.fileDialog2(
        fileMode=4,
        caption="Select Source / Rig Files",
        fileFilter=(
            "Source / Rig Files (*.fbx *.max *.max.txt *.ma);;"
            "FBX Files (*.fbx);;"
            "3ds Max Files (*.max *.max.txt);;"
            "Maya ASCII Rig Files (*.ma);;"
            "All Files (*.*)"
        )
    )

    if not paths:
        return

    count = 0

    for path in paths:

        if not is_source_file(path):
            continue

        add_file_to_list(
            file_list,
            path
        )

        count += 1

    if logger:
        logger.append(
            "Added {} source / rig file(s).".format(
                count
            )
        )


def browse_source_folder(file_list, logger=None):
    folders = cmds.fileDialog2(
        fileMode=3,
        caption="Select Folder Containing Source / Rig Files"
    )

    if not folders:
        return

    folder = folders[0]
    count = 0

    for name in os.listdir(folder):

        path = os.path.join(
            folder,
            name
        )

        if not os.path.isfile(path):
            continue

        if not is_source_file(path):
            continue

        add_file_to_list(
            file_list,
            path
        )

        count += 1

    if logger:
        logger.append(
            "Added {} source / rig file(s) from folder.".format(
                count
            )
        )


# --------------------------------------------------
# ANIMATION FILE LIST
# --------------------------------------------------
# Right list.
#
# Allowed:
#   .fbx only


def is_animation_file(path):
    lower = path.lower()

    return lower.endswith(".fbx")


def browse_animation_files(file_list, logger=None):
    paths = cmds.fileDialog2(
        fileMode=4,
        caption="Select Animation FBX Files",
        fileFilter=(
            "Animation FBX Files (*.fbx);;"
            "FBX Files (*.fbx);;"
            "All Files (*.*)"
        )
    )

    if not paths:
        return

    count = 0

    for path in paths:

        if not is_animation_file(path):
            continue

        add_file_to_list(
            file_list,
            path
        )

        count += 1

    if logger:
        logger.append(
            "Added {} animation FBX file(s).".format(
                count
            )
        )


def browse_animation_folder(file_list, logger=None):
    folders = cmds.fileDialog2(
        fileMode=3,
        caption="Select Folder Containing Animation FBXs"
    )

    if not folders:
        return

    folder = folders[0]
    count = 0

    for name in os.listdir(folder):

        path = os.path.join(
            folder,
            name
        )

        if not os.path.isfile(path):
            continue

        if not is_animation_file(path):
            continue

        add_file_to_list(
            file_list,
            path
        )

        count += 1

    if logger:
        logger.append(
            "Added {} animation FBX file(s) from folder.".format(
                count
            )
        )


# --------------------------------------------------
# BACKWARDS COMPATIBILITY WRAPPERS
# --------------------------------------------------
# Old UI/code used these names.
# I'll keep pointing to the source-list behavior for now.


def browse_files(file_list, logger=None):
    browse_source_files(
        file_list,
        logger
    )


def browse_folder_for_fbx(file_list, logger=None):
    browse_source_folder(
        file_list,
        logger
    )