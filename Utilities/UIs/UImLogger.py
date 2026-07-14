# UImLogger.py

import sys
import html
import contextlib

import maya.cmds as cmds
from maya import OpenMayaUI as omui

try:
    from PySide2 import QtWidgets, QtGui, QtCore
    import shiboken2
except ImportError:
    from PySide6 import QtWidgets, QtGui, QtCore
    import shiboken6 as shiboken2


def maya_layout_to_qwidget(layout_name):
    """
    Converts a Maya cmds layout/control into a Qt widget.
    """

    ptr = omui.MQtUtil.findLayout(layout_name)

    if ptr is None:
        ptr = omui.MQtUtil.findControl(layout_name)

    if ptr is None:
        raise RuntimeError(
            "Could not find Maya UI layout/control: {}".format(
                layout_name
            )
        )

    return shiboken2.wrapInstance(
        int(ptr),
        QtWidgets.QWidget
    )
class _ResizeToParentFilter(QtCore.QObject):
    """
    Forces a Qt widget to always fill its parent widget.
    """

    def __init__(self, child_widget):
        super(_ResizeToParentFilter, self).__init__()

        self.child_widget = child_widget

    def eventFilter(self, parent_widget, event):

        if event.type() == QtCore.QEvent.Resize:

            self.child_widget.setGeometry(
                parent_widget.rect()
            )

        return False


class UILogger(object):
    """
    Rich Qt logger.

    Supports:
        - white normal text
        - green larger step lines
        - red larger error lines
        - auto-scroll to bottom
        - stdout/stderr capture
    """

    def __init__(self, text_edit):
        self.text_edit = text_edit
        self.buffer = ""

    @classmethod
    def from_maya_layout(cls, maya_layout):
        """
        Creates a QTextEdit inside a Maya cmds layout and forces it
        to fill the entire layout area.
        """

        parent_widget = maya_layout_to_qwidget(maya_layout)

        text_edit = QtWidgets.QTextEdit(parent_widget)

        text_edit.setReadOnly(True)

        text_edit.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)

        text_edit.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding
        )

        font = QtGui.QFont("Consolas", 10)

        text_edit.setFont(font)

        text_edit.setStyleSheet(
            """
            QTextEdit {
                background-color: #141414;
                color: #eeeeee;
                border: 1px solid #333333;
            }
            """
        )

        # Force it to fill the host immediately
        text_edit.setGeometry(parent_widget.rect())

        # Force it to keep filling the host when Maya resizes
        resize_filter = _ResizeToParentFilter(text_edit)

        parent_widget.installEventFilter(resize_filter)

        # Keep reference alive, otherwise Python may garbage collect it
        text_edit._resize_filter = resize_filter

        text_edit.show()

        return cls(text_edit)

    def clear(self):
        self.text_edit.clear()

    def classify_line(self, message):
        """
        Returns style information for a log line.
        """

        clean = message.strip()

        upper = clean.upper()

        if (
            upper.startswith("STEP ")
            or "PIPELINE DONE" in upper
            or "BATCH START" in upper
            or "BATCH COMPLETE" in upper
            or upper.startswith("[PROGRESS]")
        ):
            return {
                "color": "#55ff88",
                "size": "13px",
                "weight": "bold"
            }

        if (
            "ERROR" in upper
            or "TRACEBACK" in upper
            or "EXCEPTION" in upper
            or "RUNTIMEERROR" in upper
            or "IMPORTERROR" in upper
            or "VALUEERROR" in upper
            or "SYNTAXERROR" in upper
        ):
            return {
                "color": "#ff5555",
                "size": "13px",
                "weight": "bold"
            }

        if upper.startswith("=" * 10) or upper.startswith("#" * 10):
            return {
                "color": "#888888",
                "size": "10px",
                "weight": "normal"
            }

        return {
            "color": "#eeeeee",
            "size": "11px",
            "weight": "normal"
        }

    def append(self, message):
        if message is None:
            return

        message = str(message)

        style = self.classify_line(message)

        safe_message = html.escape(message)

        html_line = (
            '<div style="'
            'color:{color}; '
            'font-size:{size}; '
            'font-weight:{weight}; '
            'font-family:Consolas, monospace;'
            '">{message}</div>'
        ).format(
            color=style["color"],
            size=style["size"],
            weight=style["weight"],
            message=safe_message
        )

        self.text_edit.moveCursor(QtGui.QTextCursor.End)

        self.text_edit.insertHtml(html_line)

        self.text_edit.insertPlainText("\n")

        self.scroll_to_bottom()

        cmds.refresh()

    def scroll_to_bottom(self):
        scrollbar = self.text_edit.verticalScrollBar()

        scrollbar.setValue(scrollbar.maximum())

    def write(self, text):
        """
        Used by sys.stdout / sys.stderr redirection.
        """

        if not text:
            return

        self.buffer += text

        while "\n" in self.buffer:
            line, self.buffer = self.buffer.split(
                "\n",
                1
            )

            self.append(
                line
            )

    def flush(self):
        if self.buffer:
            self.append(
                self.buffer
            )

            self.buffer = ""


@contextlib.contextmanager
def capture_prints(logger):
    """
    Redirects stdout/stderr to the UI logger.
    """

    old_stdout = sys.stdout
    old_stderr = sys.stderr

    sys.stdout = logger
    sys.stderr = logger

    try:
        yield

    finally:
        logger.flush()
        sys.stdout = old_stdout
        sys.stderr = old_stderr