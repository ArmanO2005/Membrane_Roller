# from pytrinamic.connections import ConnectionManager
# from pytrinamic.evalboards.TMC4671_eval import TMC4671_eval
# from pytrinamic.ic import TMC4671




from motor_control.TMC4671_utils import TMC4671Controller
from motor_control.TMCM1111_utils import TMCM1111Controller
from motor_control.Clamp_utils import ClampController
import time
import yaml

with open('config/motor_config.yaml', 'r') as file:
    motor_config = yaml.safe_load(file)

# 4 to 1 USB Adaptor
PORT0 = "COM3"
PORT1 = "COM13"  # Clamp
PORT2 = "COM14"  # Staker
PORT3 = "COM15"  # Spindle


clamp_motor = ClampController(motor_config['clamp'])
staker_motor = TMCM1111Controller(motor_config['staker'])
spindle_motor = TMCM1111Controller(motor_config['spindle'])
feeder_motor = TMC4671Controller(motor_config['feeder'])

feeder_motor.initialize()
feeder_motor.rotate(-1)
time.sleep(5)
feeder_motor.stop()

