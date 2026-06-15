from c_motor_control.TMC4671_utils import TMC4671Controller
from pytrinamic.ic.TMC4671 import TMC4671
import time

class FeederController(TMC4671Controller):
    def __init__(self, config):
        super().__init__(config)

    def detect_membrane(self):
        not_triggered = self.module.read_register_field(TMC4671.FIELD.REF_SW_L_RAW)
        return not not_triggered

    def reach_tip(self):
        self.rotate(-self.config.get("velocity"))
        start_time = time.time()
        while True:
            not_triggered = self.module.read_register_field(TMC4671.FIELD.REF_SW_H_RAW)
            if not not_triggered:
                time.sleep(1)
                self.stop()
                break
            if time.time() - start_time > self.config.get("tip_timeout"):
                self.stop()
                raise TimeoutError(f"[{self.name}] Tip detection timed out")
            time.sleep(0.01)

    def reload(self):
        self.rotate(-self.config.get("velocity"))
        time.sleep(0.2)
        self.stop()

    def pull_back(self):
        self.rotate(3 * self.config.get("velocity"))
        start_time = time.time()

        while True:
            not_triggered = self.module.read_register_field(TMC4671.FIELD.REF_SW_H_RAW)         
            if not_triggered:
                self.stop()
                break
            if time.time() - start_time > self.config.get("tip_timeout"):
                self.stop()
                raise TimeoutError(f"[{self.name}] Tip detection timed out")
            time.sleep(0.01)