"""This module contains the class(es) for control of the PANASONIC 
Laser : HG-C1100-P with a specific setup on a Arduino"""

# Standard imports
import serial
import serial.tools.list_ports
import time
import configparser
import logging

# project sub-modules imports
from .abstractcontroller import AbsController
from .threads.control_threads import CyclicJob

# logger configuration
logger = logging.getLogger(f'core.{__name__}')

class LaserController(AbsController):
    """
    LaserController is a controller class for managing a laser distance sensor via serial communication.

    This controller handles connection management and distance measurement.

    It supports periodic distance polling (Threaded).

    This class only works on a specific harware setup (Telemetry Laser + Arduino UNO with specific connections)
    please refer to the documentation for further info

    Args:
        - controllers_config (configparser.ConfigParser): Configuration object containing sensor and connection parameters.
        - parent (QWidget, optional): Parent widget.
    """

    def __init__(self, controllers_config:configparser.ConfigParser, parent=None) -> None:
        super().__init__()

        self.controllers_config = controllers_config

        self.com_port = controllers_config.get('Distance_sensor', 'COM_PORT')
        self.offset_mm = int(controllers_config.get('Distance_sensor', 'MEASURING_CENTER_DISTANCE_MM'))
        self.laser_range_mm = int(controllers_config.get('Distance_sensor', 'MEASURING_RANGE_MM'))
        self.min_distance_for_safety = float(controllers_config.get('Distance_sensor', 'MIN_SAFE_DISTANCE_MM')) * 1000

        self.measured_distance = 0.

        self.last_valid_value = self.offset_mm * 1000

        self.unit = "µm"
        self.port_tuple_repr = None
        self.out_of_range_flag = True
        self.serial_port = None
        self.connexion_established = False

    # Threaded method
    def _read_serial(self, range_points_num=1024, sampling_rate_secs=.1):
        """Reads the serial port to update the laser value"""

        if not self.serial_port.is_open :
            return

        # Flush the buffer
        self.serial_port.read_all()
        self.serial_port.readline()
        time.sleep(sampling_rate_secs)

        # Read one line from buffer
        str_val = str(self.serial_port.readline()[:-2])

        if not str_val == "b''":
            str_val = str_val.lstrip("b").strip("'")
            if int(str_val) > 1022 :
                # Out of range of the sensor (100mm +-35mm)
                self.out_of_range_flag = True
            else:
                # In range of the sensor (100mm +-35mm)
                self.out_of_range_flag = False
                raw_measure_mm = int(str_val) * self.laser_range_mm / range_points_num
                self.measured_distance = (self.offset_mm + (self.laser_range_mm / 2) - raw_measure_mm)*1000

    def get_measured_dist(self) -> float:
        """
        Retrieves the measured distance (with the applied offset).

        Returns:
            float: The measured distance with the offset applied.
        """
        return self.measured_distance - self.offset_mm

    def query_can_move_closer(self) -> bool:
        """
        @Returns:
            -   True if the minimal safety distance has not yet been reached,
                False otherwise
            - Always True if the laser is not connected or out of range or OFF
        """

        if not self.is_connected() or self.is_out_of_range() :
            return True

        return self.measured_distance >= self.min_distance_for_safety

    def get_remaining_safe_distance(self) -> float:
        """Get the remaining distance that the move forward allows
            
            (Depends on MIN_SAFE_DISTANCE_MM from .cfg file)
        """
        if self.is_out_of_range() :
            return float("-inf")

        remaining_distance = self.measured_distance - self.min_distance_for_safety
        
        return 0 if remaining_distance <= 0 else remaining_distance

    def can_move_forward_by(self, distance:float) -> bool:
        """Returns a bool indicating whether or not the given distance
        can be moved forward (towards object) without collision"""

        if not self.is_connected() or self.is_out_of_range() :
            return True

        return distance < self.get_remaining_safe_distance()

    def start_update_distance_job(self, sampling_freq=.1, feed_to_csv=False, csv_filepath=None) -> None:
        """Create and start the Job for distance update 
        (Cyclicaly interogates the laser device for distance)"""

        logger.info('Starting laser distance updating')
        self.update_dist_timer = CyclicJob(target=self._read_serial,
                                        interval=sampling_freq)
        self.update_dist_timer.name = 'LaserDistance-position-update-Job'
        self.update_dist_timer.start()

    def stop_update_distance_job(self):
        """Stops the Job for distance update"""
        if hasattr(self, "update_dist_timer"):
            self.update_dist_timer.stop()

    def is_connected(self) -> bool:
        
        return self.connexion_established

    def is_out_of_range(self) -> bool:
        return self.out_of_range_flag

    def start_connection(self) -> None:

        if self.serial_port is None or not self.serial_port.is_open:
            try :
                logger.debug(f'...Attempting connection to ARDUINO at {self.com_port}')
                self.serial_port = serial.Serial(self.com_port, 9600, timeout=1)

                # Save tuple representation of the COM port connection for later connection checking
                connected_com_ports = [tuple(p) for p in list(serial.tools.list_ports.comports())]
                self.port_tuple_repr = [port for port in connected_com_ports if self.com_port in port ][0]

            except serial.SerialException as ser_err:
                connerr_msg = f'ARDUINO for Distance Laser control not found at COM port : {self.com_port}'
                logger.error(connerr_msg)
                self.connexion_established = False
                raise ConnectionError(connerr_msg)

            self.connexion_established = True
            logger.info(f'ARDUINO for Distance Laser control connected on serial port : {self.com_port}')
            self.start_update_distance_job(sampling_freq=0.01)

        else :
            pass

    def stop_connection(self) -> None:
        if not self.is_connected():
            return
        self.stop_update_distance_job()
        self.serial_port.close()
        self.connexion_established = False

    def laser_on(self) -> None:
        """Turn the laser on"""
        if not self.is_connected():
            return

        if self.serial_port is not None and self.serial_port.is_open:
            self.serial_port.write(b'0')
            logger.debug('Laser turned ON')

    def laser_off(self) -> None:
        """Turn the laser off"""
        if not self.is_connected():
            return

        if self.serial_port is not None and self.serial_port.is_open:
            self.serial_port.write(b'1')
            logger.debug('Laser turned OFF')

    def get_value_and_unit(self):
        """Returns the last read value of the distance and a string representing the unit"""
        return self.get_measured_dist(), self.unit

    def __repr__(self):
        return (f"<LaserController("
                f"COM_PORT={self.com_port!r}, "
                f"Offset_mm={self.offset_mm}, "
                f"Range_mm={self.laser_range_mm}, "
                f"MinSafeDist_um={self.min_distance_for_safety}, "
                f"Connected={self.connexion_established}, "
                f"OutOfRange={self.out_of_range_flag}, "
                f"LastValue={self.measured_distance}, "
                f"Unit={self.unit})>")

    def __str__(self):
        return (f"<LaserController("
                f"COM_PORT={self.com_port!r}, \n"
                f"Offset_mm={self.offset_mm}, \n"
                f"Range_mm={self.laser_range_mm}, \n"
                f"MinSafeDist_um={self.min_distance_for_safety}, \n"
                f"Connected={self.connexion_established}, \n"
                f"OutOfRange={self.out_of_range_flag}, \n"
                f"LastValue={self.measured_distance}, \n"
                f"Unit={self.unit})>\n")

def test_LaserController_init():

    # Typical configuration
    config = configparser.ConfigParser()
    config.add_section('Distance_sensor')
    config.set('Distance_sensor', 'com_port', 'COM3')
    config.set('Distance_sensor', 'measuring_center_distance_mm', '100')
    config.set('Distance_sensor', 'measuring_range_mm', '70')
    config.set('Distance_sensor', 'min_safe_distance_mm', '97.250')
    config.set('Distance_sensor', 'focus_distance_mm', '1.383')

    laser_controller = LaserController(config)
    print(laser_controller)

    assert True

def test_LaserController_start_connection():

    # Typical configuration
    config = configparser.ConfigParser()
    config.add_section('Distance_sensor')
    config.set('Distance_sensor', 'com_port', 'COM3')
    config.set('Distance_sensor', 'measuring_center_distance_mm', '100')
    config.set('Distance_sensor', 'measuring_range_mm', '70')
    config.set('Distance_sensor', 'min_safe_distance_mm', '97.250')
    config.set('Distance_sensor', 'focus_distance_mm', '1.383')

    laser_controller = LaserController(config)

    laser_controller.start_connection()
    time.sleep(1)
    assert laser_controller.is_connected()

    laser_controller.stop_connection()
    time.sleep(1)

def test_LaserController_stop_connection():

    # Typical configuration
    config = configparser.ConfigParser()
    config.add_section('Distance_sensor')
    config.set('Distance_sensor', 'com_port', 'COM3')
    config.set('Distance_sensor', 'measuring_center_distance_mm', '100')
    config.set('Distance_sensor', 'measuring_range_mm', '70')
    config.set('Distance_sensor', 'min_safe_distance_mm', '97.250')
    config.set('Distance_sensor', 'focus_distance_mm', '1.383')

    laser_controller = LaserController(config)

    laser_controller.start_connection()
    time.sleep(1)
    assert laser_controller.is_connected()

    laser_controller.stop_connection()
    time.sleep(1)
    assert not laser_controller.is_connected()

def test_LaserController_Laser_On_Off():
    
    # Typical configuration
    config = configparser.ConfigParser()
    config.add_section('Distance_sensor')
    config.set('Distance_sensor', 'com_port', 'COM3')
    config.set('Distance_sensor', 'measuring_center_distance_mm', '100')
    config.set('Distance_sensor', 'measuring_range_mm', '70')
    config.set('Distance_sensor', 'min_safe_distance_mm', '97.250')
    config.set('Distance_sensor', 'focus_distance_mm', '1.383')

    laser_controller = LaserController(config)
    laser_controller.start_connection()
    time.sleep(1)
    laser_controller.laser_on()
    time.sleep(1)
    laser_controller.laser_on()
    time.sleep(10)
    laser_controller.laser_off()
    time.sleep(1)

    assert True

    laser_controller.stop_connection()

if __name__ == "__main__":

    # test_LaserController_init()
    # test_LaserController_start_connection()
    # test_LaserController_stop_connection()
    test_LaserController_Laser_On_Off()