from microEye.hardware.cams.camera_calibration import dark_calibration
from microEye.hardware.cams.camera_list import CameraList, CameraManager
from microEye.hardware.cams.camera_panel import Camera_Panel, CamParams
from microEye.hardware.cams.jobs import AcquisitionJob
from microEye.hardware.cams.linescan.IR_Cam import (
    DemoLineScanner,
    IR_Cam,
    ParallaxLineScanner,
)
from microEye.hardware.cams.micam import miCamera, miDummy
from microEye.hardware.cams.thorlabs.thorlabs import CMD, thorlabs_camera
from microEye.hardware.cams.thorlabs.thorlabs_panel import Thorlabs_Panel

try:
    from pyueye import ueye

    from microEye.hardware.cams.ueye.ueye_camera import IDS_Camera
    from microEye.hardware.cams.ueye.ueye_panel import IDS_Panel
except Exception:
    ueye = None
    IDS_Camera = None
    IDS_Panel = None
try:
    from microEye.hardware.cams.vimba import INSTANCE, vb
    from microEye.hardware.cams.vimba.vimba_cam import vimba_cam
    from microEye.hardware.cams.vimba.vimba_panel import Vimba_Panel
except Exception:
    vb = None
