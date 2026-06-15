from c_motor_control.TMC4671_utils import TMC4671Controller
from c_motor_control.TMCM1111_utils import TMCM1111Controller
from c_motor_control.Clamp_utils import ClampController
from c_motor_control.Staker_utils import StakerController
from c_motor_control.Feeder_utils import FeederController
from c_motor_control.Spindle_utils import SpindleController
from c_motor_control.Actuonix_LAC_utils import LAC
import time
import yaml


class MembraneRoller:
    def __init__(self, config):
        self.clamp_motor  = self._try("Clamp",   ClampController,   config['clamp'])
        self.staker_motor = self._try("Staker",  StakerController,  config['staker'])
        self.spindle_motor= self._try("Spindle", SpindleController, config['spindle'])
        self.feeder_motor = self._try("Feeder",  FeederController,  config['feeder'])
        self.lac          = self._try_lac()

    def _try(self, name, cls, config):
        try:
            return cls(config)
        except Exception as e:
            print(f"[{name}] Connection failed: {e}")
            return None

    def _try_lac(self):
        try:
            return LAC()
        except Exception as e:
            print(f"[LAC] Connection failed: {e}")
            return None

    def close(self):
        for motor in (self.clamp_motor, self.staker_motor, self.spindle_motor, self.feeder_motor):
            if motor is not None:
                try:
                    motor.close()
                except Exception:
                    pass

    def initialize(self):
        if self.staker_motor:  self.staker_motor.enable_heater()
        if self.clamp_motor:   self.clamp_motor.home()
        if self.staker_motor:  self.staker_motor.home()
        if self.spindle_motor: self.spindle_motor.home()
        if self.lac:           self.lac.home()

    def roll(self, stake1_time=3, stake1_point=310000, stake2_time=5, stake2_point=310000):
        if self.clamp_motor:   self.clamp_motor.clamp()
        if self.feeder_motor:  self.feeder_motor.reach_tip()
        if self.staker_motor:  self.staker_motor.stake(stake1_time, stake1_point)
        if self.spindle_motor: self.spindle_motor.full_rotation()
        if self.staker_motor:  self.staker_motor.stake(stake2_time, stake2_point)
        if self.lac:           self.lac.cut()
        if self.clamp_motor:   self.clamp_motor.home()
        if self.feeder_motor:  self.feeder_motor.pull_back()

    def off(self):
        if self.staker_motor:  self.staker_motor.disable_heater()
        if self.clamp_motor:   self.clamp_motor.home()
        if self.staker_motor:  self.staker_motor.home()
        if self.spindle_motor: self.spindle_motor.home()
        if self.lac:           self.lac.home()
