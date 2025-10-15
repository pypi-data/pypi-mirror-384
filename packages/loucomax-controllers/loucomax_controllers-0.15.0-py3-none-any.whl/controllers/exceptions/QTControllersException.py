#!/usr/bin/env python3
# =============================================================================
#  ControllersException.py
#
#  Description : Custom exception classes for controller hardware errors and warnings.
#
#  Author      : Antoine BLASIAK <antoineblasiak66@gmail.com>
#  Copyright   : (c) 2025 Antoine BLASIAK
#  License     : MIT License
#  Repository  : https://github.com/abpydev/LouCOMAX_Controllers
#
#  This file is part of the LouCOMAX Controllers project from LAB-BC research unit of CNRS.
#  See the LICENSE file for more details.
# =============================================================================

# PyQT imports
from PyQt5.QtWidgets import QMessageBox

class ControllerNotConnected(Exception):

    def __init__(self, name="Unknown controller") -> None:
        text = f"{name} not connected"

        dlg = QMessageBox()
        dlg.setWindowTitle("Controller Connection ERROR")
        dlg.setIcon(QMessageBox.Icon.Critical)
        dlg.setText(text)
        dlg.exec()

class ControllerWarningMsg(Exception):

    def __init__(self, text:str) -> None:

        dlg = QMessageBox()
        dlg.setWindowTitle("Controller WARNING message")
        dlg.setIcon(QMessageBox.Icon.Warning)
        dlg.setText(text)
        dlg.exec()

class ControllerErrorMsg(Exception):

    def __init__(self, text:str) -> None:

        dlg = QMessageBox()
        dlg.setWindowTitle("Controller ERROR message")
        dlg.setIcon(QMessageBox.Icon.Warning)
        dlg.setText(text)
        dlg.exec()

class ZaberNotConnected(ControllerNotConnected):
    def __init__(self, *args: object) -> None:
        super().__init__(name="Zaber positionning stages")

class AmptekMaxrfNotConnected(ControllerNotConnected):
    def __init__(self, *args: object) -> None:
        super().__init__(name="Amptek MAXRF sensor")

class AmptekCxrfNotConnected(ControllerNotConnected):
    def __init__(self, *args: object) -> None:
        super().__init__(name="Amptek CXRF sensor")

class LaserNotConnected(ControllerNotConnected):
    def __init__(self, *args: object) -> None:
        super().__init__(name="Telemetry Laser Sensor")

class CSUNotConnected(ControllerNotConnected):
    def __init__(self, *args: object) -> None:
        super().__init__(name="CSU for RX control")

class CSUCantOpenShutterError(ControllerWarningMsg):
    def __init__(self, *args: object) -> None:
        csu_error = args[0]
        super().__init__(text=f"Could not open the RX Shutter.\nCheck CSU control panel for Errors or retart the CSU hardware\n{csu_error}")

class CSURxNotWarmedUp(ControllerWarningMsg):
    def __init__(self, *args: object) -> None:
        super().__init__(text="RX Tube was not warmed up yet.\nPlease power ON the RX Tube's High Voltage and wait for warmup")

class LaserOutOfRangeWarning(ControllerWarningMsg):
    def __init__(self, *args: object) -> None:
        text = "Can't start Z auto control :\
\n\
\n\
- The distance LASER is OFF\
\nor\n\
- The Distance LASER is disconnected\
\nor\n\
- No Z distance target, reach manualy the wanted distance then click on 'save Z'\
\nor\n\
- The distance LASER is out of bounds.\
Please reach manualy inside the working range before activating Z control.\
\nor\n\
- The current Z distance is too far from the target 'saved z'.\
Please reach manualy closer to the target before activating Z control."
        super().__init__(text)

class MappingOutOfBoundsError(ControllerErrorMsg):

    def __init__(self, text:str) -> None:

        super().__init__(text)