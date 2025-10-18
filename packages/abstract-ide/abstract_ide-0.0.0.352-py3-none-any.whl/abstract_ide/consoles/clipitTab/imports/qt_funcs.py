# clipit/__init__.py
from .imports import *
from PyQt6.QtWidgets import QToolBar

def addWidget(target, widget):
    if isinstance(target, QToolBar):
        target.addWidget(widget)
        return
    if isinstance(target, (QHBoxLayout, QVBoxLayout, QGridLayout, QFormLayout)):
        target.addWidget(widget)
    elif isinstance(target, QWidget):
        lay = target.layout()
        if not lay:
            lay = QVBoxLayout(target)   # OK for normal QWidget, not QToolBar
        lay.addWidget(widget)
    else:
        raise TypeError(f"Unsupported target for addWidget: {type(target)}")
def get_argv(argv=None, system=None):
    system = system or sys
    if argv is None:
        argv = system.argv
    return argv
def create_app(argv=None, system=None):
    """
    Create and return the QApplication. Call this once in your `if __name__ == "__main__"` block.
    """
    argv = get_argv(argv=argv, system=system)
    app = QtWidgets.QApplication(argv)
    return app
def run_app(win=None,app=None,winn_args=None,win_kwargs=None,argv=None, system=None):
    winn_args = winn_args or set()
    win_kwargs = win_kwargs or {}
    app=app or create_app(argv=argv, system=system)
    window =win(*winn_args,**win_kwargs)
    run_apps(window,system=sys)
def run_apps(window,app=None,argv=None, system=None):
    argv = get_argv(argv, system)
    # build the QApplication
    app  = app or create_app(argv)
    window.show()
    sys.exit(app.exec())
def get_parent(parent=None):
    parent = parent or QtWidgets.QWidget()
    return parent

def resize_window(size=None,parent=None):
    size = size or (950, 600)
    parent.resize(*size)
    return parent
def make_main_window(parent=None,title=None, size=None) -> QtWidgets.QWidget:
    """
    Create a top‐level QWidget (or QMainWindow if you prefer), set its title and size, and return it.
    """
    title = title or "Main Window"
    parent = get_parent(parent=parent)
    size = size or (800, 600)
    parent.setWindowTitle(title)
    resize_window(size=size,parent=parent)
    return parent

def get_layout(parent=None):
    parent = get_parent(parent=parent)
    main_layout = QtWidgets.QVBoxLayout(parent)
    return main_layout

def make_toolbar(parent: QtWidgets.QWidget=None, movable: bool = False) -> QtWidgets.QToolBar:
    """
    Create a QToolBar, set whether it’s movable, and add it to the parent (if parent is a QMainWindow).
    If parent is a plain QWidget, you’ll have to insert the toolbar into a layout manually.
    """
    parent =parent or QtWidgets.QWidget
    toolbar = QtWidgets.QToolBar(parent)
    toolbar.setMovable(movable)
    return toolbar


def apply_layout(parent: QtWidgets.QWidget, layout: QtWidgets.QLayout):
    """
    Set the given layout on `parent`. This assumes parent is a QWidget (or subclass).
    """
    parent.setLayout(layout)
    return

def get_qt_index(index=None):
    index = index or QtCore.QDir.homePath()
    return index
def get_qt_rootPath(rootPath=None):
    rootPath = rootPath or QtCore.QDir.rootPath()
    return rootPath

def get_drag_and_drop(text=None,splitter=None,style=None,alignment=None,drops=True):
    text = text or "Drag files here"
    style = style or "border: 2px dashed #aaa;"
    alignment = alignment or QtCore.Qt.AlignCenter
    drops = drops or False
    drop_area = QtWidgets.QLabel(text, splitter)
    drop_area.setAlignment(alignment)
    drop_area.setStyleSheet(style)
    drop_area.setAcceptDrops(drops)
    return drop_area

def get_fs_model(index=None,root_path=None):
    index = get_qt_index(index=index)
    root_path = get_qt_rootPath(rootPath=root_path)
    fs_model = QtWidgets.QFileSystemModel()
    fs_model.setRootPath(root_path)

    fs_model.index(index)
    return fs_model

def get_tree_view(model=None,splitter=None,index=None,root_path=None,hideColumns=True):
    index = get_qt_index(index=index)
    root_path = get_qt_rootPath(rootPath=root_path)
    model = model or get_fs_model(index=index,
                                  root_path=root_path)
    
    tree_view = QtWidgets.QTreeView(splitter)
    tree_view.setModel(model)
    tree_view.setRootIndex(model.index(index))
    if hideColumns:
        column_count = model.columnCount()
        for col in range(1, ):
            tree_view.hideColumn(col)
    return tree_view

def get_splitter(parent,horizontal=None,vertical=None):
    split = QtCore.Qt.Horizontal
    if vertical is True:
        split = QtCore.Qt.Vertical
    splitter = QtWidgets.QSplitter(split, parent)
    return splitter
def add_to_splitter(splitter,*args):
    for arg in args:
       splitter.addWidget(arg)
    return splitter
def add_toolbar_action(toolbar=None,parent=None,*args):
    toolbar = toolbar or make_toolbar(parent)
    for arg in args:
       toolbar.addAction(arg)
    return toolbar

def add_widgets(parent,*args):
    for arg in args:
        kwargs = {}
        widget = arg
        if isinstance(arg,dict):
            widget = arg.get("widget",widget)
            kwargs = arg.get("kwargs",{})
        parent.addWidget(widget,**kwargs)
    return parent
def get_toggle(parent,action=None,text=None,checkable=True):
    text = text or "Toggle Logs"
    checkable = checkable or False
    toggle_logs_action = QtWidgets.QAction(text, parent)
    toggle_logs_action.setCheckable(checkable)
    toggle_logs_action.toggled.connect(action)
    return toggle_logs_action

def get_logged_text_edits(parent=None,readOnly=True,visible=True):
    # 3) Bottom: QTextEdit for logs
    log_textedit = QtWidgets.QTextEdit(parent)
    log_textedit.setReadOnly(readOnly)
    log_textedit.setVisible(visible)
    return log_textedit

def get_push_button(text=None,action=None):
    text = text or "push"
    button = QtWidgets.QPushButton(text)
    button.clicked.connect(action)
    return button
def set_visible(parent,checked: bool=None):
    if checked is not None:
        parent.setVisible(checked)
def get_log_widget(readOnly=True,style=None,hide=True):
    style = style or "background:#111; color:#eee; font-family:monospace;"
    log_widget = QtWidgets.QTextEdit()
    log_widget.setReadOnly(readOnly)
    log_widget.setStyleSheet(style)
    if hide:
        log_widget.hide()
    return log_widget
def get_toolbar():
    toolbar = QtWidgets.QToolBar()
    return toolbar

def get_window_title(title,window):
    window.setWindowTitle(title)
    


def get_orientation(splitter,horizontal=None,vertical=None):
    if horizontal==None and vertical == None:
        horizontal = True
    if horizontal:
        orientation  = QtCore.Qt.Horizontal
    else:
        orientation  = QtCore.Qt.Vertical
    splitter.setOrientation(orientation)        
