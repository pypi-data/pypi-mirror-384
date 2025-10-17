import os
import sys
from enum import Enum
from typing import Optional

from pyqtgraph.parametertree import Parameter

from microEye.qt import QApplication, QtWidgets, Signal
from microEye.utils.parameter_tree import Tree


class CamParams(Enum):
    '''
    Enum class defining Camera parameters.
    '''

    ACQUISITION = 'Acquisition'
    EXPERIMENT_NAME = 'Acquisition.Experiment Name'
    FRAMES = 'Acquisition.Number of Frames'
    SAVE_DATA = 'Acquisition.Save Data'
    ACQ_SETTINGS = 'Acquisition Settings'
    CAMERA_GPIO = 'GPIOs'
    CAMERA_TIMERS = 'Timers'
    EXPOSURE = 'Acquisition Settings.Exposure Time'
    EXPORTS = 'Exports'
    SAVE_DIRECTORY = 'Exports.Save Directory'
    DARK_CALIBRATION = 'Exports.Dark Calibration'
    IMAGE_FORMAT = 'Exports.Image Format'
    TIFF_FORMAT = 'Exports.Tiff Format'
    ZARR_FORMAT = 'Exports.Zarr Format'
    BIGG_TIFF_FORMAT = 'Exports.BiggTiff Format'
    FULL_METADATA = 'Exports.Full Metadata'
    STATS = 'Stats'
    CAPTURE_STATS = 'Stats.Capture'
    DISPLAY_STATS = 'Stats.Display'
    SAVE_STATS = 'Stats.Save'
    TEMPERATURE = 'Stats.Temperature'
    ROI = 'Region of Interest (ROI)'
    ROI_X = 'Region of Interest (ROI).X'
    ROI_Y = 'Region of Interest (ROI).Y'
    ROI_WIDTH = 'Region of Interest (ROI).Width'
    ROI_HEIGHT = 'Region of Interest (ROI).Height'
    SET_ROI = 'Region of Interest (ROI).Set ROI'
    RESET_ROI = 'Region of Interest (ROI).Reset ROI'
    CENTER_ROI = 'Region of Interest (ROI).Center ROI'
    SELECT_ROI = 'Region of Interest (ROI).Select ROI'
    EXPORT_ROIS = 'Region of Interest (ROI).Export ROIs'
    SELECT_EXPORT_ROIS = 'Region of Interest (ROI).Export ROIs.Select ROIs'
    EXPORTED_ROIS = 'Region of Interest (ROI).Export ROIs.ROIs'
    EXPORT_ROIS_SEPERATE = 'Region of Interest (ROI).Export ROIs.Seperate Files'
    EXPORT_ROIS_FLIPPED = 'Region of Interest (ROI).Export ROIs.Flip Horizontally'
    DISPLAY = 'Display'
    PREVIEW = 'Display.Preview'
    DISPLAY_STATS_OPTION = 'Display.Display Stats'
    AUTO_STRETCH = 'Display.Auto Stretch'
    PLOT_TYPE = 'Display.Plot Type'
    VIEW_OPTIONS = 'Display.View Options'
    SINGLE_VIEW = 'Display.View Options.Single View'
    DUAL_VIEW = 'Display.View Options.Dual Channel'
    DUAL_OVERLAID = 'Display.View Options.Dual Channel (Overlaid)'
    ROIS_VIEW = 'Display.View Options.Export ROIs'
    ROIS_VIEW_OVERLAID = 'Display.View Options.Export ROIs (Overlaid)'
    # add colors for dual view RG, GB, GR, BR, BG, etc.
    DUAL_VIEW_COLORS = 'Display.Dual View Colors'
    LINE_PROFILER = 'Display.Line Profiler'
    LUT = 'Display.LUT'
    LUT_NUMPY = 'Display.LUT Numpy (12bit)'
    LUT_OPENCV = 'Display.LUT Opencv (8bit)'
    RESIZE_DISPLAY = 'Display.Resize Display'

    EXPORT_STATE = 'Export State'
    IMPORT_STATE = 'Import State'

    def __str__(self):
        '''
        Return the last part of the enum value (Param name).
        '''
        return self.value.split('.')[-1]

    def get_path(self):
        '''
        Return the full parameter path.
        '''
        return self.value.split('.')


class CameraOptions(Tree):
    '''
    Tree widget for editing camera parameters.

    Attributes
    ----------
    paramsChanged : Signal
        Signal for parameter changed event.
    '''

    PARAMS = CamParams

    setROI: Signal = Signal()
    resetROI: Signal = Signal()
    centerROI: Signal = Signal()
    selectROI: Signal = Signal()
    selectROIs: Signal = Signal()
    directoryChanged: Signal = Signal(str)
    viewOptionChanged: Signal = Signal()

    def __init__(self, parent: Optional['QtWidgets.QWidget'] = None):
        '''
        Initialize the CameraOptions.

        Parameters
        ----------
        parent : QWidget, optional
            The parent widget, by default None.
        '''
        super().__init__(parent=parent)

    @classmethod
    def combine_params(name, extra_params: Enum):
        combined_members = {}
        enum_classes: list[Enum] = [CameraOptions.PARAMS, extra_params]
        for enum_class in enum_classes:
            for member in enum_class:
                combined_members[member.name] = member.value

        sorted_members = dict(
            sorted(combined_members.items(), key=lambda item: item[1].split('.')[0])
        )
        CameraOptions.PARAMS = Enum('CamParams', sorted_members)

    def create_parameters(self):
        '''
        Create the parameter tree structure.
        '''
        params = [
            {
                'name': str(CamParams.ACQUISITION),
                'type': 'group',
                'expanded': True,
                'children': [
                    {
                        'name': str(CamParams.EXPERIMENT_NAME),
                        'type': 'str',
                        'value': '001_Experiment',
                    },
                    {
                        'name': str(CamParams.FRAMES),
                        'type': 'int',
                        'value': int(1e6),
                        'limits': [1, int(1e9)],
                    },
                    {'name': str(CamParams.SAVE_DATA), 'type': 'bool', 'value': False},
                ],
            },
            {
                'name': str(CamParams.ACQ_SETTINGS),
                'type': 'group',
                'expanded': False,
                'children': [
                    {
                        'name': str(CamParams.EXPOSURE),
                        'type': 'float',
                        'value': 100.0,
                        'dec': False,
                        'decimals': 6,
                        'suffixes': [' ns', ' us', ' ms', ' s'],
                    },
                ],
            },
            {
                'name': str(CamParams.EXPORTS),
                'type': 'group',
                'children': [
                    {
                        'name': str(CamParams.SAVE_DIRECTORY),
                        'type': 'file',
                        'directory': os.path.join(os.path.expanduser('~'), 'Desktop'),
                        'fileMode': 'Directory',
                    },
                    {
                        'name': str(CamParams.DARK_CALIBRATION),
                        'type': 'bool',
                        'value': False,
                    },
                    {
                        'name': str(CamParams.IMAGE_FORMAT),
                        'type': 'list',
                        'limits': [
                            str(CamParams.BIGG_TIFF_FORMAT),
                            str(CamParams.TIFF_FORMAT),
                            str(CamParams.ZARR_FORMAT),
                        ],
                    },
                    {
                        'name': str(CamParams.FULL_METADATA),
                        'type': 'bool',
                        'value': True,
                    },
                ],
            },
            {
                'name': str(CamParams.DISPLAY),
                'type': 'group',
                'expanded': False,
                'children': [
                    {'name': str(CamParams.PREVIEW), 'type': 'bool', 'value': True},
                    {
                        'name': str(CamParams.DISPLAY_STATS_OPTION),
                        'type': 'bool',
                        'value': True,
                    },
                    {
                        'name': str(CamParams.AUTO_STRETCH),
                        'type': 'bool',
                        'value': True,
                    },
                    {
                        'name': str(CamParams.PLOT_TYPE),
                        'type': 'list',
                        'limits': ['Histogram', 'Cumulative'],
                    },
                    {
                        'name': str(CamParams.VIEW_OPTIONS),
                        'type': 'list',
                        'limits': [
                            str(CamParams.SINGLE_VIEW),
                            str(CamParams.DUAL_VIEW),
                            str(CamParams.DUAL_OVERLAID),
                            str(CamParams.ROIS_VIEW),
                            str(CamParams.ROIS_VIEW_OVERLAID),
                        ],
                    },
                    {
                        'name': str(CamParams.DUAL_VIEW_COLORS),
                        'type': 'list',
                        'limits': [
                            'RG',
                            'GB',
                            'GR',
                            'BR',
                            'BG',
                            'RB',
                            'GB',
                            'RG',
                        ],
                        'value': 'GB',
                    },
                    {
                        'name': str(CamParams.LINE_PROFILER),
                        'type': 'bool',
                        'value': False,
                    },
                    {
                        'name': str(CamParams.RESIZE_DISPLAY),
                        'type': 'float',
                        'value': 0.5,
                        'limits': [0.1, 4.0],
                        'step': 0.02,
                        'dec': False,
                    },
                ],
            },
            {
                'name': str(CamParams.STATS),
                'type': 'group',
                'expanded': False,
                'children': [
                    {
                        'name': str(CamParams.CAPTURE_STATS),
                        'type': 'str',
                        'value': '0 | 0.00 ms',
                        'readonly': True,
                    },
                    {
                        'name': str(CamParams.DISPLAY_STATS),
                        'type': 'str',
                        'value': '0 | 0.00 ms',
                        'readonly': True,
                    },
                    {
                        'name': str(CamParams.SAVE_STATS),
                        'type': 'str',
                        'value': '0 | 0.00 ms',
                        'readonly': True,
                    },
                    {
                        'name': str(CamParams.TEMPERATURE),
                        'type': 'str',
                        'value': ' T -127.00 °C',
                        'readonly': True,
                    },
                ],
            },
            {
                'name': str(CamParams.ROI),
                'type': 'group',
                'expanded': False,
                'children': [
                    {'name': str(CamParams.ROI_X), 'type': 'int', 'value': 0},
                    {'name': str(CamParams.ROI_Y), 'type': 'int', 'value': 0},
                    {'name': str(CamParams.ROI_WIDTH), 'type': 'int', 'value': 0},
                    {'name': str(CamParams.ROI_HEIGHT), 'type': 'int', 'value': 0},
                    {'name': str(CamParams.SET_ROI), 'type': 'action'},
                    {'name': str(CamParams.RESET_ROI), 'type': 'action'},
                    {'name': str(CamParams.CENTER_ROI), 'type': 'action'},
                    {'name': str(CamParams.SELECT_ROI), 'type': 'action'},
                    {
                        'name': str(CamParams.EXPORT_ROIS),
                        'type': 'group',
                        'children': [
                            {
                                'name': str(CamParams.SELECT_EXPORT_ROIS),
                                'type': 'action',
                            },
                            {
                                'name': str(CamParams.EXPORTED_ROIS),
                                'type': 'group',
                                'children': [],
                            },
                            {
                                'name': str(CamParams.EXPORT_ROIS_SEPERATE),
                                'type': 'bool',
                                'value': True,
                                'tip': 'Export each ROI a Tiff file. (Not for Zarr)',
                            },
                            {
                                'name': str(CamParams.EXPORT_ROIS_FLIPPED),
                                'type': 'bool',
                                'value': True,
                                'tip': 'Flip n-th ROIs horizontally for n > 1.',
                            },
                        ],
                    },
                ],
            },
            {
                'name': str(CamParams.CAMERA_GPIO),
                'type': 'group',
                'expanded': False,
                'children': [],
            },
            {
                'name': str(CamParams.CAMERA_TIMERS),
                'type': 'group',
                'expanded': False,
                'children': [],
            },
            {'name': str(CamParams.EXPORT_STATE), 'type': 'action'},
            {'name': str(CamParams.IMPORT_STATE), 'type': 'action'},
        ]

        self.param_tree = Parameter.create(name='', type='group', children=params)
        self.param_tree.sigTreeStateChanged.connect(self.change)
        self.header().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)

        self.get_param(CamParams.SAVE_DIRECTORY).sigValueChanged.connect(
            lambda: self.directoryChanged.emit(
                self.get_param_value(CamParams.SAVE_DIRECTORY)
            )
        )

        self.get_param(CamParams.SET_ROI).sigActivated.connect(
            lambda: self.setROI.emit()
        )
        self.get_param(CamParams.RESET_ROI).sigActivated.connect(
            lambda: self.resetROI.emit()
        )
        self.get_param(CamParams.CENTER_ROI).sigActivated.connect(
            lambda: self.centerROI.emit()
        )
        self.get_param(CamParams.SELECT_ROI).sigActivated.connect(
            lambda: self.selectROI.emit()
        )
        self.get_param(CamParams.SELECT_EXPORT_ROIS).sigActivated.connect(
            lambda: self.selectROIs.emit()
        )
        self.get_param(CamParams.VIEW_OPTIONS).sigValueChanged.connect(
            lambda: self.viewOptionChanged.emit()
        )

        self.get_param(CamParams.IMPORT_STATE).sigActivated.connect(self.load_json)
        self.get_param(CamParams.EXPORT_STATE).sigActivated.connect(self.export_json)

    def get_roi_info(self):
        '''
        Get the region of interest (ROI) information.

        Returns
        -------
        tuple
            Tuple containing ROI X, ROI Y, ROI width, and ROI height.
        '''
        info = [
            self.get_param_value(CamParams.ROI_X),
            self.get_param_value(CamParams.ROI_Y),
            self.get_param_value(CamParams.ROI_WIDTH),
            self.get_param_value(CamParams.ROI_HEIGHT),
        ]
        return info

    def set_roi_info(self, x: int, y: int, w: int, h: int):
        '''
        Set the region of interest (ROI) information.

        Parameters
        ----------
        x : int
            X-coordinate of the ROI.
        y : int
            Y-coordinate of the ROI.
        w : int
            Width of the ROI.
        h : int
            Height of the ROI.

        Returns
        -------
        None
        '''
        self.set_param_value(CamParams.ROI_X, x)
        self.set_param_value(CamParams.ROI_Y, y)
        self.set_param_value(CamParams.ROI_WIDTH, w)
        self.set_param_value(CamParams.ROI_HEIGHT, h)

    def set_roi_limits(
        self,
        x: tuple[int, int],
        y: tuple[int, int],
        w: tuple[int, int],
        h: tuple[int, int],
    ):
        '''
        Set limits for the Region of Interest (ROI) parameters.

        This function sets limits for the X-coordinate, Y-coordinate, width,
        and height parameters of the Region of Interest (ROI).

        Parameters
        ----------
        x : tuple[int, int]
            Tuple representing the minimum and maximum limits for the X-coordinate.
        y : tuple[int, int]
            Tuple representing the minimum and maximum limits for the Y-coordinate.
        w : tuple[int, int]
            Tuple representing the minimum and maximum limits for the width.
        h : tuple[int, int]
            Tuple representing the minimum and maximum limits for the height.

        Returns
        -------
        None
        '''
        self.get_param(CamParams.ROI_X).setLimits(x)
        self.get_param(CamParams.ROI_Y).setLimits(y)
        self.get_param(CamParams.ROI_WIDTH).setLimits(w)
        self.get_param(CamParams.ROI_WIDTH).setDefault(w[1])
        self.get_param(CamParams.ROI_WIDTH).setValue(w[1])
        self.get_param(CamParams.ROI_HEIGHT).setLimits(h)
        self.get_param(CamParams.ROI_HEIGHT).setDefault(h[1])
        self.get_param(CamParams.ROI_HEIGHT).setValue(h[1])

    def get_export_rois(self):
        '''
        Get the export regions of interest (ROIs) information.

        Returns
        -------
        list[list[int]]
            list or ROIs with each being a list[int] of [x, y, w, h].
        '''
        rois_param = self.get_param(CamParams.EXPORTED_ROIS)
        rois = []

        if len(rois_param.children()) > 0:
            for child in rois_param.children():
                rois.append(list(map(int, child.value().split(', '))))
        return rois

    def setZoom(self, value: float):
        '''
        Set the zoom value.
        '''
        param = self.get_param(CamParams.RESIZE_DISPLAY)

        if param and param.opts['enabled']:
            param.setValue(value)

    def change(self, param: Parameter, changes: list):
        '''
        Handle parameter changes as needed.

        This method handles the changes made to the parameters in the parameter
        tree.

        Parameters
        ----------
        param : Parameter
            The parameter that triggered the change.
        changes : list
            List of changes.

        Returns
        -------
        None
        '''
        # Handle parameter changes as needed
        for p, _, data in changes:
            path = self.param_tree.childPath(p)

            self.paramsChanged.emit(p, data)

    @property
    def isTiff(self):
        '''
        Check if the image format is TIFF.

        Returns
        -------
        bool
            True if the image format is TIFF, False otherwise.
        '''
        return self.get_param_value(CamParams.IMAGE_FORMAT) in [
            str(CamParams.TIFF_FORMAT),
            str(CamParams.BIGG_TIFF_FORMAT),
        ]

    @property
    def isBiggTiff(self):
        '''
        Check if the image format is BigTIFF.

        Returns
        -------
        bool
            True if the image format is BigTIFF, False otherwise.
        '''
        return self.get_param_value(CamParams.IMAGE_FORMAT) in [
            str(CamParams.BIGG_TIFF_FORMAT)
        ]

    @property
    def isSingleView(self):
        '''
        Check if the view option is set to single view.

        Returns
        -------
        bool
            True if the view option is set to single view, False otherwise.
        '''
        return self.get_param_value(CamParams.VIEW_OPTIONS) in [
            str(CamParams.SINGLE_VIEW)
        ]

    @property
    def isROIsView(self):
        '''
        Check if the view option is set to export ROIs view.

        Returns
        -------
        bool
            True if the view option is set to export ROIs view, False otherwise.
        '''
        return self.get_param_value(CamParams.VIEW_OPTIONS) in [
            str(CamParams.ROIS_VIEW),
            str(CamParams.ROIS_VIEW_OVERLAID),
        ]

    @property
    def isFlippedROIsView(self) -> bool:
        '''
        Check if the view option is set to export ROIs view with flipped ROIs.
        '''
        return self.get_param_value(CamParams.EXPORT_ROIS_FLIPPED)

    @property
    def isOverlaidView(self):
        '''
        Check if the view option is set to overlaid view.

        Returns
        -------
        bool
            True if the view option is set to overlaid view, False otherwise.
        '''
        return self.get_param_value(CamParams.VIEW_OPTIONS) in [
            str(CamParams.DUAL_OVERLAID),
            str(CamParams.ROIS_VIEW_OVERLAID),
        ]

    @property
    def isFullMetadata(self):
        '''
        Check if the metadata option is set to full.

        Returns
        -------
        bool
            True if the full metadata option is set, False otherwise.
        '''
        return self.get_param_value(CamParams.FULL_METADATA)

    @property
    def isDarkCalibration(self):
        '''
        Check if the dark calibration option is set.

        Returns
        -------
        bool
            True if the dark calibration option is set, False otherwise.
        '''
        return self.get_param_value(CamParams.DARK_CALIBRATION)

    @property
    def isSaveData(self):
        '''
        Check if the save data option is set.

        Returns
        -------
        bool
            True if the save data option is set, False otherwise.
        '''
        return self.get_param_value(CamParams.SAVE_DATA)

    def toggleSaveData(self):
        param = self.get_param(CamParams.SAVE_DATA)
        if param:
            param.setValue(not param.value())

    @property
    def isPreview(self):
        '''
        Check if the preview option is set.

        Returns
        -------
        bool
            True if the preview option is set, False otherwise.
        '''
        return self.get_param_value(CamParams.PREVIEW)

    def togglePreview(self):
        param = self.get_param(CamParams.PREVIEW)
        if param:
            param.setValue(not param.value())

    @property
    def isAutostretch(self):
        '''
        Check if the auto-stretch option is set.

        Returns
        -------
        bool
            True if the auto-stretch option is set, False otherwise.
        '''
        return self.get_param_value(CamParams.AUTO_STRETCH)

    def toggleAutostretch(self):
        param = self.get_param(CamParams.AUTO_STRETCH)
        if param:
            param.setValue(not param.value())

    @property
    def isDisplayStats(self):
        '''
        Check if the display stats option is set.

        Returns
        -------
        bool
            True if the display stats option is set, False otherwise.
        '''
        return self.get_param_value(CamParams.DISPLAY_STATS_OPTION)

    def toggleDisplayStats(self):
        param = self.get_param(CamParams.DISPLAY_STATS_OPTION)
        if param:
            param.setValue(not param.value())

    @property
    def isLineProfiler(self):
        '''
        Check if the line profiler option is set.

        Returns
        -------
        bool
            True if the line profiler option is set, False otherwise.
        '''
        return self.get_param_value(CamParams.LINE_PROFILER)

    @property
    def isHistogramPlot(self):
        '''
        Check if the LUT option is set to numpy lut.

        Returns
        -------
        bool
            True if the LUT option is set to numpy lut, False otherwise.
        '''
        return self.get_param_value(CamParams.PLOT_TYPE) == 'Histogram'

    @property
    def dualViewColors(self):
        '''
        Get the dual view colors as channel indices.

        Returns
        -------
        str
            The selected dual view colors.
        '''
        # get the selected dual view colors from the parameter tree e.g. 'RG', 'GB', etc
        scheme = self.get_param_value(CamParams.DUAL_VIEW_COLORS)

        indices = {'R': 0, 'G': 1, 'B': 2}

        return [indices[c] for c in scheme]


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = CameraOptions()
    window.show()
    sys.exit(app.exec())
