from pytrinamic.connections import ConnectionManager
from pytrinamic.evalboards import TMC4671_eval
from pytrinamic.ic.TMC4671 import TMC4671
import time


class TMC4671Controller:
    # Derived from initialize() hardware config:
    # PWM_FREQ = 100 MHz / (PWM_MAXCNT + 1) = 100e6 / 4000 = 25000 Hz
    # POLE_PAIRS = lower 16 bits of MOTOR_TYPE_N_POLE_PAIRS = 0x0032 = 50
    _PWM_FREQ   = 100_000_000 // (0x00000F9F + 1)  # 25 000 Hz
    _POLE_PAIRS = 0x00020032 & 0xFFFF               # 50

    def __init__(self, config):
        self.config = config
        self.name = self.config.get("name")
        self.interface = ConnectionManager(
            f"--interface serial_tmcl --port {self.config.get('port')} --data-rate 115200"
        ).connect()
        self.module = TMC4671_eval(self.interface, module_id=1)
        self.ic = self.module.ics[0]
        self.motor = self.module.motors[0]
        self.AP = self.motor.AP
        self.check_chip()
        self.initialize()
        print(f"[{self.name}] Connected.")

    def _write(self, reg, value):
        self.module.write_register(reg, value)

    def _read(self, reg):
        return self.module.read_register(reg)

    def check_chip(self):
        self._write(TMC4671.REG.CHIPINFO_ADDR, 0)
        chip_type = self._read(TMC4671.REG.CHIPINFO_DATA)
        if chip_type != 0x34363731:
            raise RuntimeError(
                f"[{self.name}] TMC4671 not responding correctly "
                f"(expected chip type 0x34363731, got 0x{chip_type:08X})"
            )
        print(f"[{self.name}] CHIPINFO: 0x{chip_type:08X} (\"4671\") — connection OK")

    def initialize(self):
        REG = TMC4671.REG

        # Motor type & PWM configuration
        self._write(REG.MOTOR_TYPE_N_POLE_PAIRS, 0x00020032)
        self._write(REG.PWM_POLARITIES,          0x00000000)
        self._write(REG.PWM_MAXCNT,              0x00000F9F)
        self._write(REG.PWM_BBM_H_BBM_L,         0x00000A0A)
        self._write(REG.PWM_SV_CHOP,             0x00000007)

        # ADC configuration
        self._write(REG.ADC_I_SELECT,        0x18000100)
        self._write(REG.dsADC_MCFG_B_MCFG_A, 0x00100010)
        self._write(REG.dsADC_MCLK_A,        0x20000000)
        self._write(REG.dsADC_MCLK_B,        0x20000000)
        self._write(REG.dsADC_MDEC_B_MDEC_A, 0x014E014E)
        self._write(REG.ADC_I0_SCALE_OFFSET,  0x010082DC)
        self._write(REG.ADC_I1_SCALE_OFFSET,  0x010080E8)

        # Open-loop settings
        self._write(REG.OPENLOOP_MODE,            0x00000000)
        self._write(REG.OPENLOOP_ACCELERATION,    0x0000003C)
        self._write(REG.OPENLOOP_VELOCITY_TARGET, 0xFFFFFFFB)

        # Feedback selection — open loop
        self._write(REG.PHI_E_SELECTION, 0x00000002)
        self._write(REG.UQ_UD_EXT,       0x00000E17)

        print(f"[{self.name}] Initialized.")
        self.stop()

    def open_loop_test(self):
        REG = TMC4671.REG

        self._write(REG.MODE_RAMP_MODE_MOTION, 0x00000008)

        self._write(REG.OPENLOOP_VELOCITY_TARGET, 0x0000003C)
        time.sleep(2.0)

        self._write(REG.OPENLOOP_VELOCITY_TARGET, 0xFFFFFFC4)
        time.sleep(4.0)

        self._write(REG.OPENLOOP_VELOCITY_TARGET, 0x00000000)
        time.sleep(2.0)

        self._write(REG.UQ_UD_EXT, 0x00000000)
        print(f"[{self.name}] Open-loop test complete.")

    def rotate(self, velocity):
        self._write(TMC4671.REG.OPENLOOP_VELOCITY_TARGET, velocity)

    def move_by(self, rotations, velocity=None):
        """Rotate by a given number of revolutions (open-loop, time-based).

        rotations: positive = forward, negative = reverse
        velocity:  register magnitude; defaults to config 'velocity'
        """
        if velocity is None:
            velocity = self.config.get("velocity")
        speed = abs(int(velocity))
        mech_rps = speed * self._PWM_FREQ / (65536 * self._POLE_PAIRS)
        duration = abs(rotations) / mech_rps
        direction = 1 if rotations >= 0 else -1
        self.rotate(direction * speed)
        time.sleep(duration)
        self.stop()

    def stop(self):
        self._write(TMC4671.REG.OPENLOOP_VELOCITY_TARGET, 0)

    def close(self):
        self.interface.close()