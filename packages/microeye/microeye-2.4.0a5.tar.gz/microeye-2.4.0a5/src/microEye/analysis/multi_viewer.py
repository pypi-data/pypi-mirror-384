import json
import os
import re
import webbrowser
from enum import Enum
from typing import Optional, Union
from weakref import ref

import cv2

from microEye import __version__
from microEye.analysis.fitting.results import FittingResults
from microEye.analysis.tools.registration import RegistrationWidget
from microEye.analysis.viewer import LocalizationsView, PSFView, StackView
from microEye.qt import (
    QT_API,
    QAction,
    QApplication,
    QDateTime,
    QFileSystemModel,
    QIcon,
    QMainWindow,
    Qt,
    QtCore,
    QtWidgets,
    Slot,
)
from microEye.utils import StartGUI


class DockKeys(Enum):
    FILE_SYSTEM = 'File System'
    FILES_LIST = 'Files List'
    SMLM_ANALYSIS = 'SMLM Analysis'
    DATA_FILTERS = 'Data Filters'


class CustomFileSystemModel(QFileSystemModel):
    def __init__(self, parent=None):
        super().__init__(parent)

    def filterAcceptsRow(self, source_row, source_parent):
        index = self.index(source_row, 0, source_parent)
        if not index.isValid():
            return False

        # Get the file/folder name and path
        file_info = self.fileInfo(index)
        file_name = file_info.fileName()
        parent_path = file_info.absolutePath()

        # Check if the parent directory is a .zarr folder
        if parent_path.endswith('.zarr'):
            return False  # Do not show any files within a .zarr folder

        # Check if the current directory is a .zarr folder
        if file_name.endswith('.zarr'):
            return True  # Always accept .zarr folders themselves

        # Use the default filtering behavior for other files/folders
        return super().filterAcceptsRow(source_row, source_parent)

    def isDir(self, index):
        # Override the isDir method to treat .zarr folders as files
        file_info = self.fileInfo(index)
        if file_info.isDir() and file_info.fileName().endswith('.zarr'):
            return False  # Treat .zarr folders as files
        return super().isDir(index)

    def data(self, index, role):
        # Optionally, customize the display role to show the .zarr folders as files
        file_info = self.fileInfo(index)
        if (
            role == QFileSystemModel.Roles.FileIconRole
            and file_info.fileName().endswith('.zarr')
        ):
            # Get the icon for a ZIP file (or any compressed file)
            zip_icon = QIcon.fromTheme('application-zip')  # On Linux
            if zip_icon.isNull():
                zip_icon = self.iconProvider().icon(
                    QtCore.QFileInfo('dummy.zip')
                )  # Fallback for Windows/Mac
            return zip_icon  # Return ZIP icon for .zarr folders

        return super().data(index, role)

    def hasChildren(self, index):
        # Ensure that .zarr folders don't expand by showing no children
        file_info = self.fileInfo(index)
        if file_info.isDir() and file_info.fileName().endswith('.zarr'):
            return False  # Treat .zarr folders as files with no children
        return super().hasChildren(index)


class multi_viewer(QMainWindow):
    def __init__(self, path=None):
        super().__init__()
        # Set window properties
        self.title = f'Multi Viewer Module v{__version__}'
        self.left = 0
        self.top = 0
        self._width = 1600
        self._height = 950

        # {path: {'type': str, 'widget': QWidget}}
        self._opened_files: dict[str, dict[str, QtWidgets.QWidget]] = {}

        # Threading
        self._threadpool = QtCore.QThreadPool.globalInstance()
        print(
            f'Multithreading with maximum {self._threadpool.maxThreadCount()} threads'
        )

        # Set the path
        if path is None:
            path = os.path.dirname(os.path.abspath(__package__))
        self.initialize(path)

        # Set up the status bar
        self.status()

        # Status Bar Timer
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.status)
        self.timer.start(200)

        # Set main window properties
        self.setStatusBar(self.statusBar())

    def initialize(self, path):
        # Set Title / Dimensions / Center Window
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self._width, self._height)

        # Define main window layout
        self.setupMainWindowLayout()

        # Initialize the file system model / tree
        self.setupFileSystemTab(path)

        # Setup opened files list
        self.setup_files_list()

        # Tabify docks
        self.tabifyDocks()

        # Set tab positions
        self.setTabPositions()

        # Raise docks
        self.raiseDocks()

        # Create menu bar
        self.createMenuBar()

        self.show()
        self.center()

    def setupMainWindowLayout(self):
        # # Create the MDI area
        self.mdi_area = QtWidgets.QMdiArea()
        self.mdi_area.setViewMode(QtWidgets.QMdiArea.ViewMode.TabbedView)
        self.mdi_area.setTabsClosable(True)
        self.mdi_area.setTabsMovable(True)
        self.mdi_area.setBackground(Qt.GlobalColor.transparent)
        tabs = self.mdi_area.findChild(QtWidgets.QTabBar)
        tabs.setExpanding(False)

        self.setCentralWidget(self.mdi_area)

        self.docks: dict[
            str, QtWidgets.QDockWidget
        ] = {}  # Dictionary to store created docks
        self.layouts = {}

    def setup_files_list(self):
        self.opened_files_list = QtWidgets.QListWidget(self)
        self.opened_files_list.setWindowTitle('Opened Files')
        self.opened_files_list.itemClicked.connect(self._focus_opened_file)
        self.create_tab(
            DockKeys.FILES_LIST,
            QtWidgets.QVBoxLayout,
            'LeftDockWidgetArea',
            widget=None,
            visible=True,
        ).addWidget(self.opened_files_list)

    def setupFileSystemTab(self, path):
        # Tiff File system tree viewer tab layout
        self.file_tree_layout = self.create_tab(
            DockKeys.FILE_SYSTEM,
            QtWidgets.QVBoxLayout,
            'LeftDockWidgetArea',
            widget=None,
        )

        self.path = path

        # Create QFileSystemModel
        self.model = CustomFileSystemModel()
        self.model.setRootPath(path)
        self.model.setFilter(
            QtCore.QDir.Filter.AllDirs
            | QtCore.QDir.Filter.Files
            | QtCore.QDir.Filter.NoDotAndDotDot
        )
        self.model.setNameFilters(['*.tif', '*.tiff', '*.tsv', '*.h5', '*.zarr'])
        self.model.setNameFilterDisables(False)

        # Create QTreeView
        self.tree = QtWidgets.QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(path))
        self.tree.setAnimated(False)
        self.tree.setIndentation(20)
        self.tree.setSortingEnabled(False)
        self.tree.hideColumn(1)
        self.tree.hideColumn(2)
        self.tree.hideColumn(3)
        self.tree.setWindowTitle('Dir View')
        self.tree.setMinimumWidth(400)
        self.tree.resize(512, 256)

        # Connect double-click signal to a method that uses QTimer
        self.tree.doubleClicked.connect(self._open_file)

        # Create Tree view context menu
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_tree_context_menu)

        # Add the File system tab contents
        self.imsq_pattern = QtWidgets.QLineEdit('/image_0*.ome.tif')

        self.file_tree_layout.addWidget(QtWidgets.QLabel('Image Sequence pattern:'))
        self.file_tree_layout.addWidget(self.imsq_pattern)
        self.file_tree_layout.addWidget(self.tree)

    def _show_tree_context_menu(self, position):
        index = self.tree.indexAt(position)
        if not index.isValid():
            return

        menu = QtWidgets.QMenu()
        reveal_action = menu.addAction('Reveal in Explorer')
        new_folder_action = menu.addAction('New Folder')
        menu.addSeparator()

        # Root path shortcuts
        root_action = menu.addAction('This PC (Root Path)')
        home_action = menu.addAction('Home (User Directory)')
        desktop_action = menu.addAction('Desktop')
        initial_action = menu.addAction('Initial Path')
        working_dir_action = menu.addAction('Working Directory')

        action = menu.exec(self.tree.viewport().mapToGlobal(position))
        if action == reveal_action:
            path = self.model.filePath(index)
            folder = path if os.path.isdir(path) else os.path.dirname(path)
            os.startfile(folder)
        elif action == new_folder_action:
            self._create_new_folder()
        elif action == home_action:
            home = os.path.expanduser('~')
            self.tree.setRootIndex(self.model.index(home))
        elif action == desktop_action:
            desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
            self.tree.setRootIndex(self.model.index(desktop))
        elif action == root_action:
            self.tree.setRootIndex(self.model.index(''))
        elif action == initial_action:
            self.tree.setRootIndex(self.model.index(self.path))
        elif action == working_dir_action:
            self.tree.setRootIndex(
                self.model.index(os.path.dirname(os.path.abspath(__package__)))
            )

    def _create_new_folder(self):
        index = self.tree.currentIndex()
        if not index.isValid():
            return

        path = self.model.filePath(index)
        if not os.path.isdir(path):
            path = os.path.dirname(path)

        new_folder_name, ok = QtWidgets.QInputDialog.getText(
            self, 'New Folder', 'Enter folder name:'
        )
        if ok and new_folder_name:
            new_folder_path = os.path.join(path, new_folder_name)
            try:
                os.makedirs(new_folder_path)
            except OSError as e:
                QtWidgets.QMessageBox.critical(
                    self, 'Error', f'Could not create folder: {e}'
                )

    def tabifyDocks(self):
        # Tabify docks
        if len(self.docks) > 1:
            first_dock = next(iter(self.docks.values()))
            for dock in list(self.docks.values())[1:]:
                self.tabifyDockWidget(first_dock, dock)

    def setTabPositions(self):
        self.setTabPosition(
            Qt.DockWidgetArea.LeftDockWidgetArea, QtWidgets.QTabWidget.TabPosition.North
        )
        self.setTabPosition(
            Qt.DockWidgetArea.RightDockWidgetArea,
            QtWidgets.QTabWidget.TabPosition.North,
        )

    def raiseDocks(self):
        # Raise docks
        self.docks[DockKeys.FILE_SYSTEM].raise_()

    def createMenuBar(self):
        menu_bar = self.menuBar()

        # Create file menu
        file_menu = menu_bar.addMenu('File')
        view_menu = menu_bar.addMenu('View')
        tools_menu = menu_bar.addMenu('Tools')
        help_menu = menu_bar.addMenu('Help')

        # Create exit action
        save_config = QAction('Save Config.', self)
        save_config.triggered.connect(lambda: saveConfig(self))
        load_config = QAction('Load Config.', self)
        load_config.triggered.connect(lambda: loadConfig(self))

        github = QAction('microEye Github', self)
        github.triggered.connect(
            lambda: webbrowser.open('https://github.com/samhitech/microEye')
        )
        pypi = QAction('microEye PYPI', self)
        pypi.triggered.connect(
            lambda: webbrowser.open('https://pypi.org/project/microEye/')
        )

        # Add exit action to file menu
        file_menu.addAction(save_config)
        file_menu.addAction(load_config)

        def connect(action: QAction, dock: QtWidgets.QDockWidget):
            action.triggered.connect(lambda: dock.setVisible(action.isChecked()))

        # Create toggle view actions for each dock
        dock_toggle_actions = {}
        for key, dock in self.docks.items():
            toggle_action = dock.toggleViewAction()
            toggle_action.setEnabled(True)
            dock_toggle_actions[key] = toggle_action
            view_menu.addAction(toggle_action)
            if '6' in QT_API:
                connect(toggle_action, dock)

        # Add tools menu actions
        self.reg_window = None

        def show_registration_tool():
            if self.reg_window is not None:
                self.reg_window.close()
                self.reg_window = None

            stacks = {}
            for path, info in self._opened_files.items():
                widget = info['widget']()
                if info['type'] in ('TIFF', 'ZARR', 'ImageSeq') and isinstance(
                    widget, StackView
                ):
                    channels = widget.stack_handler.shapeTCZYX()[1]
                    for c in range(channels):
                        key = (
                            self._compact_display_name(path, info['type']) + f' (C{c})'
                        )
                        stacks[key.replace('\n', ' ')] = ref(widget.stack_handler)
            self.reg_window = RegistrationWidget(stacks=stacks)
            self.reg_window.show()

        # Add tools menu actions
        registration_tool = QAction('Registration Tool', self)
        registration_tool.triggered.connect(show_registration_tool)
        tools_menu.addAction(registration_tool)

        help_menu.addAction(github)
        help_menu.addAction(pypi)

    def create_tab(
        self,
        key: DockKeys,
        layout_type: Optional[
            type[Union[QtWidgets.QVBoxLayout, QtWidgets.QFormLayout]]
        ] = None,
        dock_area: str = 'LeftDockWidgetArea',
        widget: Optional[QtWidgets.QWidget] = None,
        visible: bool = True,
    ) -> Optional[type[Union[QtWidgets.QVBoxLayout, QtWidgets.QFormLayout]]]:
        '''
        Create a tab with a dock widget.

        Parameters
        ----------
        key : DockKeys
            The unique identifier for the tab.
        layout_type : Optional[Type[Union[QVBoxLayout, QFormLayout]]], optional
            The layout type for the group in the dock. If provided,
            widget should be None.
        dock_area : str, optional
            The dock area where the tab will be added.
        widget : Optional[QWidget], optional
            The widget to be placed in the dock. If provided,
            layout_type should be None.
        visible : bool, optional
            Whether the dock widget should be visible.

        Returns
        -------
        Optional[Type[Union[QVBoxLayout, QFormLayout]]]
            The layout if layout_type is provided, otherwise None.
        '''
        if widget:
            group = widget
        else:
            group = QtWidgets.QWidget()
            group_layout = layout_type() if layout_type else QtWidgets.QVBoxLayout()
            group.setLayout(group_layout)
            self.layouts[key] = group_layout

        dock = QtWidgets.QDockWidget(str(key.value), self)
        dock.setFeatures(
            QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetFloatable
            | QtWidgets.QDockWidget.DockWidgetFeature.DockWidgetMovable
        )
        dock.setWidget(group)
        dock.setVisible(visible)
        self.addDockWidget(getattr(Qt.DockWidgetArea, dock_area), dock)

        # Store the dock in the dictionary
        self.docks[key] = dock

        # Return the layout if layout_type is provided, otherwise None
        return None if widget else group_layout

    def center(self):
        '''Centers the window within the screen using setGeometry.'''
        # Get the screen geometry
        screen_geometry = QApplication.primaryScreen().availableGeometry()

        # Calculate the center point
        center_point = screen_geometry.center()

        # Set the window geometry
        self.setGeometry(
            center_point.x() - self.width() // 2,
            center_point.y() - self.height() // 2,
            self.width(),
            self.height(),
        )

    def status(self):
        # Statusbar time
        self.statusBar().showMessage(
            f'{QT_API} | '
            + 'Time: '
            + QDateTime.currentDateTime().toString('hh:mm:ss,zzz')
        )

    def _focus_opened_file(self, item):
        if isinstance(item, str):
            path = item
        elif isinstance(item, QtWidgets.QListWidgetItem):
            path = item.data(QtCore.Qt.ItemDataRole.UserRole)

        widget = self._opened_files[path]['widget']()
        for subwin in self.mdi_area.subWindowList():
            if subwin.widget() is widget:
                # subwin.raise_()
                subwin.showMaximized()
                break

    @staticmethod
    def _compact_display_name(path, type):
        # extract drive if on windows
        if os.name == 'nt':
            drive, tail = os.path.splitdrive(path)
            parts = tail.strip('/').split('/')
            drive = f'[💻{drive}]'
        else:
            drive = '[💻ROOT]'
            parts = path.strip('/').split('/')

        parent = '' if len(parts) < 2 else f'\n[📁{parts[-2]}]'
        basename = parts[-1]

        # file name pattern 00__image_00000_roi_00.ome.tif
        # extrat roi if exists regex
        match = re.search(r'.*?(\d+)__image_(\d+)_roi_(\d+)', basename)
        if match:
            prefix = match.group(1)
            image_num = match.group(2)
            roi_num = match.group(3)
            return (
                f'{drive} [{type}]'
                f'\n[{prefix}] [Image {image_num}] [ROI {roi_num}]{parent}'
            )
        elif len(basename) > 20:
            return f'{drive} [{type}]\n...{basename[-20:]}{parent}'
        else:
            return f'{drive} [{type}]\n{basename}{parent}'

    def _update_opened_files_list(self):
        self.opened_files_list.clear()
        for path, info in self._opened_files.items():
            display_name = self._compact_display_name(path, type=info['type'])
            item = QtWidgets.QListWidgetItem(f'{display_name}')
            item.setData(QtCore.Qt.ItemDataRole.UserRole, path)
            self.opened_files_list.addItem(item)

    @Slot(QtCore.QModelIndex)
    def _open_file(self, index: QtCore.QModelIndex):
        # Set the Qt.WindowFlags for making the subwindow resizable
        view = None

        path = self.model.filePath(index)

        if path in self._opened_files:
            self._focus_opened_file(path)
            return

        if not os.path.isdir(path):
            if path.endswith('.tif') or path.endswith('.tiff'):
                view = StackView(path, None)
                view.localizedData.connect(self.localizedData)
                file_type = 'TIFF'
            elif path.endswith('.zarr'):
                view = StackView(path)
                view.localizedData.connect(self.localizedData)
                file_type = 'ZARR'
            elif (
                path.endswith('.h5') and not path.endswith('.psf.h5')
            ) or path.endswith('.tsv'):
                results = FittingResults.fromFile(path, 1)
                if results is not None:
                    view = LocalizationsView(results)
                    file_type = 'HDF5' if path.endswith('.h5') else 'TSV'
                    print('Done importing results.')
                else:
                    print('Error importing results.')
            elif path.endswith('.psf.h5'):
                view = PSFView(path)
                file_type = 'PSF'
        else:
            if path.endswith('.zarr'):
                view = StackView(path)
                file_type = 'ZARR'
            else:
                try:
                    view = StackView(path, self.imsq_pattern.text())
                    file_type = 'ImageSeq'
                except Exception as e:
                    print(f'Error opening image sequence: {e}')
                    return

            view.localizedData.connect(self.localizedData)

        if view:
            self._opened_files[path] = {'type': file_type, 'widget': ref(view)}
            window = self.mdi_area.addSubWindow(view)
            # Install event filter
            window.destroyed.connect(lambda _, p=path: self._on_subwindow_close(p))
            window.show()

        self._update_opened_files_list()

    def _on_subwindow_close(self, path):
        # Remove file from opened files when subwindow closes
        if path in self._opened_files:
            del self._opened_files[path]
            self._update_opened_files_list()

    def localizedData(self, path):
        index = self.model.index(path)
        self._open_file(index)

    def StartGUI(path=None):
        '''
        Initializes a new QApplication and multi_viewer.

        Parameters
        ----------
        path : str, optional
            The path to a file to be loaded initially.

        Returns
        -------
        tuple of QApplication and multi_viewer
            Returns a tuple with QApplication and multi_viewer main window.
        '''
        return StartGUI(multi_viewer, path)


def get_dock_config(dock: QtWidgets.QDockWidget):
    '''
    Get the configuration dictionary for a QDockWidget.

    Parameters
    ----------
    dock : QDockWidget
        The QDockWidget to get the configuration for.

    Returns
    -------
    dict
        The configuration dictionary containing isFloating,
        position, size, and isVisible.
    '''
    if dock:
        return {
            'isFloating': dock.isFloating(),
            'position': (
                dock.mapToGlobal(QtCore.QPoint(0, 0)).x(),
                dock.mapToGlobal(QtCore.QPoint(0, 0)).y(),
            ),
            'size': (dock.geometry().width(), dock.geometry().height()),
            'isVisible': dock.isVisible(),
        }


def get_widget_config(widget: QtWidgets.QWidget):
    '''
    Get the configuration dictionary for a QWidget.

    Parameters
    ----------
    widget : QWidget
        The QWidget to get the configuration for.

    Returns
    -------
    dict
        The configuration dictionary containing position, size, and isMaximized.
    '''
    if widget:
        return {
            'position': (
                widget.mapToGlobal(QtCore.QPoint(0, 0)).x(),
                widget.mapToGlobal(QtCore.QPoint(0, 0)).y(),
            ),
            'size': (widget.geometry().width(), widget.geometry().height()),
            'isMaximized': widget.isMaximized(),
        }


def saveConfig(window: multi_viewer, filename: str = 'config_tiff.json'):
    """
    Save the configuration for the multi_viewer application.

    Parameters
    ----------
    window : multi_viewer
        The main application window.
    filename : str, optional
        The filename of the configuration file, by default 'config_tiff.json'.
    """
    config = dict()

    # Save multi_viewer widget config
    config['multi_viewer'] = get_widget_config(window)

    # Save docks config
    for key in DockKeys:
        dock = window.docks.get(key)
        if dock:
            config[key.value] = get_dock_config(dock)

    with open(filename, 'w') as file:
        json.dump(config, file, indent=2)

    print(f'{filename} file generated!')


def load_widget_config(widget: QtWidgets.QWidget, widget_config):
    '''
    Load configuration for a QWidget.

    Parameters
    ----------
    widget : QWidget
        The QWidget to apply the configuration to.
    widget_config : dict
        The configuration dictionary containing position, size, and maximized status.

    Returns
    -------
    None
    '''
    widget.setGeometry(
        widget_config['position'][0],
        widget_config['position'][1],
        widget_config['size'][0],
        widget_config['size'][1],
    )
    if bool(widget_config['isMaximized']):
        widget.showMaximized()


def loadConfig(window: multi_viewer, filename: str = 'config_tiff.json'):
    """
    Load the configuration for the multi_viewer application.

    Parameters
    ----------
    window : multi_viewer
        The main application window.
    filename : str, optional
        The filename of the configuration file, by default 'config_tiff.json'.
    """
    if not os.path.exists(filename):
        print(f'{filename} not found!')
        return

    config: dict = None

    with open(filename) as file:
        config = json.load(file)

    # Loading multi_viewer widget config
    if 'multi_viewer' in config:
        load_widget_config(window, config['multi_viewer'])

    # Loading docks
    for dock_key, dock_config in config.items():
        dock_enum_key = None
        try:
            dock_enum_key = DockKeys(dock_key)
        except ValueError:
            # Skip processing if dock_key is not a valid DockKeys enum
            continue

        if dock_enum_key in window.docks:
            dock = window.docks[dock_enum_key]
            dock.setVisible(bool(dock_config.get('isVisible', False)))
            if bool(dock_config.get('isFloating', False)):
                dock.setFloating(True)
                dock.setGeometry(
                    dock_config.get('position', (0, 0))[0],
                    dock_config.get('position', (0, 0))[1],
                    dock_config.get('size', (0, 0))[0],
                    dock_config.get('size', (0, 0))[1],
                )
            else:
                dock.setFloating(False)

    print(f'{filename} file loaded!')


if __name__ == '__main__':
    app, window = multi_viewer.StartGUI('')
    app.exec()
