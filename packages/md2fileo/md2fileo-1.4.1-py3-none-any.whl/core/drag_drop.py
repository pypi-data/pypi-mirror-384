# from loguru import logger
from collections import deque
import sys

from PyQt6.QtCore import (Qt, pyqtSlot, QMimeData, QByteArray,
    QModelIndex, QDataStream, QIODevice, QCoreApplication,
    QTextStream,
)
from PyQt6.QtGui import (QDrag, QDragMoveEvent, QDropEvent, QDragEnterEvent,
)
from PyQt6.QtWidgets import QStyle

from . import app_globals as ag, low_bk, load_files, db_ut
from .dir_model import dirModel, dirItem

if sys.platform.startswith("win"):
    from . import win_menu as menu
elif sys.platform.startswith("linux"):
    from . import linux_menu as menu
else:
    raise ImportError(f"doesn't support {sys.platform} system")

dragged_dirs = set()

def get_index_path(this_index: QModelIndex) -> list[int]:
    """
    returns path as row numbers from root to this_index
    """
    idx = this_index
    path = []
    while idx.isValid():
        path.append(idx.row())
        idx = idx.parent()
    path.reverse()
    return path

def get_files_mime_data() -> QMimeData:
    """
    mimedata contains:
    - Pid of current instance
    - number of selected files
    - for each file: id, dir_id
    """
    def dir_id() -> int:
        if ag.mode is ag.appMode.DIR or ag.filter_dlg.is_single_folder():
            dir_idx = ag.dir_list.currentIndex()
            return dir_idx.data(Qt.ItemDataRole.UserRole).dir_id
        else:
            return 0

    def external_file_list() -> QMimeData:
        """
        create QMimeData to drag to another app instance
        .QtCore.QCoreApplication.applicationPid()
        """
        drag_data = QByteArray()
        data_stream = QTextStream(drag_data, QIODevice.OpenModeFlag.WriteOnly)
        low_bk._export_files(data_stream)
        return drag_data

    def internal_file_list() -> QMimeData:
        drag_data = QByteArray()
        data_stream = QDataStream(drag_data, QIODevice.OpenModeFlag.WriteOnly)
        pid = QCoreApplication.applicationPid()
        data_stream.writeInt(pid)

        data_stream.writeInt(dir_id())
        indexes = ag.file_list.selectionModel().selectedRows()
        data_stream.writeInt(len(indexes))
        model = ag.file_list.model()
        for idx in indexes:
            s_idx = model.mapToSource(idx)
            data_stream.writeInt(model.sourceModel().data(s_idx, role=Qt.ItemDataRole.UserRole))
        return drag_data

    mime_data = QMimeData()
    mime_data.setData(ag.mimeType.files_in.value, internal_file_list())
    mime_data.setData(ag.mimeType.files_out.value, external_file_list())
    return mime_data

def get_dir_mime_data() -> QMimeData:
    indexes = ag.dir_list.selectionModel().selectedRows()
    get_dragged_ids(indexes)
    return dir_mime_data(indexes)

def get_dragged_ids(indexes: QModelIndex):
    """
    collect all ids of dragged dirs with its children.
    This collection is used to avoid loop in folder tree.
    """
    model = ag.dir_list.model()
    dragged_dirs.clear()
    ids = []

    qu = deque()
    qu.extend((model.getItem(idx) for idx in indexes))
    while qu:
        item: dirItem = qu.pop()
        qu.extend(item.children)
        ids.append(item.user_data().dir_id)
    dragged_dirs.update(ids)

def dir_mime_data(indexes) -> QMimeData:
    drag_data = QByteArray()
    data_stream = QDataStream(drag_data, QIODevice.OpenModeFlag.WriteOnly)

    data_stream.writeInt(len(indexes))
    for idx in indexes:
        path = get_index_path(idx)
        data_stream.writeQString(','.join((str(x) for x in path)))

    mime_data = QMimeData()
    mime_data.setData(ag.mimeType.folders.value, drag_data)
    return mime_data

def set_drag_drop_handlers():
    ag.dir_list.startDrag = start_drag_dirs
    ag.file_list.startDrag = start_drag_files
    ag.dir_list.dragMoveEvent = drag_move_event
    ag.dir_list.dragEnterEvent = drag_enter_event
    ag.dir_list.dropEvent = drop_event

@pyqtSlot(Qt.DropAction)
def start_drag_dirs(action):
    drag = QDrag(ag.app)
    drag.setMimeData(get_dir_mime_data())
    drag.exec(Qt.DropAction.CopyAction | Qt.DropAction.MoveAction)

@pyqtSlot(Qt.DropAction)
def start_drag_files(action):
    drag = QDrag(ag.app)
    drag.setMimeData(get_files_mime_data())
    drag.exec(
        Qt.DropAction.CopyAction | Qt.DropAction.MoveAction, Qt.DropAction.CopyAction
    )

@pyqtSlot(QDragEnterEvent)
def drag_enter_event(event: QDragEnterEvent):
    menu.drop_button = event.buttons()
    event.accept()

@pyqtSlot(QDragMoveEvent)
def drag_move_event(event: QDragMoveEvent):
    if event.dropAction() is Qt.DropAction.IgnoreAction:
        event.ignore()
        return

    mime_data: QMimeData = event.mimeData()
    if mime_data.hasFormat(ag.mimeType.folders.value):
        can_drop_dir_here(event)
    else:
        can_drop_file_here(event)

def can_drop_file_here(event: QDropEvent):
    """
    file can't be dropped in the root
    """
    index = ag.dir_list.indexAt(event.position().toPoint())
    if index.isValid():
        event.accept()
    else:
        event.ignore()

def can_drop_dir_here(event: QDropEvent):
    # doesn't matter if Qt.DropAction.MoveAction
    #                or Qt.DropAction.CopyAction:
    # target can't be child of any dragged dir; to avoid loop in tree
    target = ag.dir_list.indexAt(event.position().toPoint())
    if is_descendant(target):
        event.ignore()
    else:
        event.accept()

def is_descendant(target: QModelIndex) -> bool:
    # checks if target dir or any its parent is among the dragged dirs
    target_pa = target
    while target_pa.isValid():
        p_id = target_pa.data(role=Qt.ItemDataRole.UserRole).dir_id
        if p_id in dragged_dirs:
            return True
        target_pa = target_pa.parent()
    return False

@pyqtSlot(QDropEvent)
def drop_event(e: QDropEvent):
    menu.choose_drop_action(e)
    pos = e.position().toPoint()
    target = ag.dir_list.indexAt(pos)
    data = e.mimeData()
    if drop_data(data, e.dropAction(), target):
        e.accept()
    else:
        e.setDropAction(Qt.DropAction.IgnoreAction)
        e.ignore()

def drop_data(data: QMimeData, act: Qt.DropAction, target: QModelIndex) -> bool:
    if not act & (Qt.DropAction.CopyAction | Qt.DropAction.MoveAction):
        return False
    target_id = (
        target.data(role=Qt.ItemDataRole.UserRole).dir_id
        if target.isValid() else 0
    )
    if data.hasFormat(ag.mimeType.files_uri.value):
        drop_uri_list(data, target_id)
        update_file_list(target)
        return True

    if data.hasFormat(ag.mimeType.files_in.value):
        return drop_files(data, act, target)

    if data.hasFormat(ag.mimeType.folders.value):
        res = drop_folders(data, act, target_id)
        low_bk.dirs_changed(target, sure_expand=True)
        return res

    return False

def update_file_list(target: QModelIndex):
    idx = ag.dir_list.currentIndex()
    if idx.isValid():
        if ((ag.mode is ag.appMode.DIR and idx == target) or ag.mode is ag.appMode.FILTER):
            low_bk.refresh_file_list()
        elif ag.mode is ag.appMode.DIR:
            ag.dir_list.setCurrentIndex(target)

        if ag.mode is ag.appMode.FILTER:
            ag.show_message_box(
                'Drop files',
                'Application is in Filter mode, so you may not see the dropped files.',
                icon=QStyle.StandardPixmap.SP_MessageBoxWarning
            )

def drop_uri_list(data: QMimeData, target: int) -> bool:
    load = load_files.loadFiles()
    load.set_files_iterator(
        (it.toLocalFile() for it in data.urls())
    )
    load.load_to_dir(target)

def drop_files(data: QMimeData, act: Qt.DropAction, target: QModelIndex) -> bool:
    files_data = data.data(ag.mimeType.files_in.value)
    stream = QDataStream(files_data, QIODevice.OpenModeFlag.ReadOnly)
    pid_drag_from = stream.readInt()
    if QCoreApplication.applicationPid() == pid_drag_from:   # mimeType.files_in
        target_id = target.data(role=Qt.ItemDataRole.UserRole).dir_id
        if act is Qt.DropAction.CopyAction:
            res = copy_files(stream, target_id)
            ag.dir_list.setCurrentIndex(target)
            return res
        if act is Qt.DropAction.MoveAction:
            res = move_files(stream, target_id)
            low_bk.refresh_file_list()
            return res
        return False
    else:           # mimeType.files_out
        files_data = data.data(ag.mimeType.files_out.value)
        stream = QTextStream(files_data, QIODevice.OpenModeFlag.ReadOnly)
        low_bk._import_files(stream, target)

def copy_files(stream: QDataStream, target: int) -> bool:
    _ = stream.readInt()   # source dir_id - not used here
    count = stream.readInt()

    for _ in range(count):
        id = stream.readInt()
        db_ut.copy_file(id, target)

    return True

def move_files(stream: QDataStream, target: int) -> bool:
    dir_file = dir_id = stream.readInt()   # source dir_id
    count = stream.readInt()

    for _ in range(count):
        file_id = stream.readInt()
        if not dir_id:
            dir_file = db_ut.get_dir_id_for_file(file_id)
        if dir_file:
            db_ut.move_file(target, dir_file, file_id)
        else:
            db_ut.copy_file(file_id, target)
    return True

def drop_folders(data: QMimeData, act: Qt.DropAction, target: int) -> bool:
    copy_move = (
        move_folder if act is Qt.DropAction.MoveAction
        else copy_folder
    )

    folders_data = data.data(ag.mimeType.folders.value)
    stream = QDataStream(folders_data, QIODevice.OpenModeFlag.ReadOnly)
    idx_count = stream.readInt()
    model: dirModel = ag.dir_list.model()
    for _ in range(idx_count):
        tmp_str = stream.readQString()
        path = (int(i) for i in tmp_str.split(','))
        idx = model.restore_index(path)

        if not copy_move(idx, target):
            return False
    return True

def copy_folder(index: QModelIndex, target: int) -> bool:
    dir_data: ag.DirData = index.data(Qt.ItemDataRole.UserRole)
    return db_ut.copy_dir(target, dir_data)

def move_folder(index: QModelIndex, target: int) -> bool:
    dir_data: ag.DirData = index.data(Qt.ItemDataRole.UserRole)
    return db_ut.move_dir(target, dir_data.parent, dir_data.dir_id)
