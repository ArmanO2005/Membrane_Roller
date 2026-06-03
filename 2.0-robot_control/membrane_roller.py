from motor_control.TMC4671_utils import TMC4671Controller
from motor_control.TMCM1111_utils import TMCM1111Controller
from motor_control.Clamp_utils import ClampController
from motor_control.Staker_utils import StakerController
from motor_control.Feeder_utils import FeederController
from motor_control.Spindle_utils import SpindleController
import time
import yaml


class MembraneRoller:
    def __init__(self, config):
        self.clamp_motor = ClampController(config['clamp'])
        self.staker_motor = StakerController(config['staker'])
        self.spindle_motor = SpindleController(config['spindle'])
        self.feeder_motor = FeederController(config['feeder'])
        

    def initialize(self):
        self.staker_motor.enable_heater()
        self.clamp_motor.home()
        self.staker_motor.home()
        self.spindle_motor.home()

    def roll(self):
        self.clamp_motor.clamp()
        self.feeder_motor.reach_tip()
        self.staker_motor.stake()
        self.spindle_motor.full_rotation()
        # self.staker_motor.go_to_stake()
        # self.feeder_motor.pull_back()
        # self.staker_motor.exit_stake()
        self.staker_motor.stake()
        self.clamp_motor.home()
        self.feeder_motor.pull_back()

    def off(self):
        self.staker_motor.disable_heater()
        self.clamp_motor.home()
        self.staker_motor.home()
        self.spindle_motor.home()