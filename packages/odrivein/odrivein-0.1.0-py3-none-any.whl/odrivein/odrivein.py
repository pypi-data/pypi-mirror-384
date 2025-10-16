import odrive
from odrivein import motor as motor

# Motor class
class MotorDrive:
    drive: odrive
    major_rev: int
    motor0: motor.Motor
    motor1: motor.Motor

    # init
    def __init__(self, path: str = odrive.default_search_path,
             serial_number: str = None,
             cancellation_token: odrive.concurrent.futures.Future = None,
             timeout: float = None):
        # Connect to ODrive
        odrv0 = odrive.find_any(path, serial_number, cancellation_token, timeout) # find a connected ODrive (this will block until you connect one) "serial_number = ODRIVE_SERIAL_NUMBER"
        odrv0.clear_errors()
        self.motordrive = odrv0
        self.major_rev = odrv0.hw_version_major
        self.motor0 = motor.Motor(self.major_rev)
        self.motor0.odrvAxis = odrv0.axis0
        if self.major_rev == 3:
            self.motor1 = motor.Motor(self.major_rev)
            self.motor1.odrvAxis = odrv0.axis1