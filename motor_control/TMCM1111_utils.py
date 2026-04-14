from pytrinamic.connections import ConnectionManager
from pytrinamic.modules.TMCM1111 import TMCM1111
import time

# import RPi.GPIO as GPIO


class TMCM1111Controller:
    '''Wrapper for TMCM1111 motor controller'''
    def __init__(self, config):
        self.config = config
        self.interface = ConnectionManager(f"--interface usb_tmcl --port {self.config.get('port')}").connect()
        self.module = TMCM1111(self.interface)
        self.motor = self.module.motors[0]
        self.name = self.config.get("name")
        self.AP = self.motor.AP


    def home(self):
        print(f"[{self.name}] Homing started...")

        self.motor.rotate(-self.config.get("home_search_velocity"))
        start_time = time.time()
        while True:
            not_triggered = self.motor.get_axis_parameter(self.AP.HomeSwitch) # 0: triggered, 1: not_triggered
            if not not_triggered:
                time.sleep(self.config.get("home_centering_time"))
                self.motor.stop()
                print(f"[{self.name}] Switch triggered.")
                break
            if time.time() - start_time > self.config.get("home_timeout"):
                self.motor.stop()
                raise TimeoutError(f"[{self.name}] Homing timed out")
            time.sleep(0.01)


        self.motor.set_axis_parameter(self.AP.ActualPosition, 0)
        print(f"[{self.name}] Homing complete. Position zeroed.")


    def rotate(self, velocity):
        self.motor.rotate(velocity)

    def stop(self):
        self.motor.stop()

    def close(self):
        self.interface.close()

