from pytrinamic.connections import ConnectionManager
from pytrinamic.evalboards import TMC4671_eval
from pytrinamic.ic.TMC4671 import TMC4671
import time


class TMC4671Controller:
    def __init__(self, config):
        self.config = config
        self.interface = ConnectionManager(
            f"--interface serial_tmcl --port {self.config.get('port')} --data-rate 9600"
        ).connect()
        self.module = TMC4671_eval(self.interface, module_id=1)  # module 1, id1
        self.ic = self.module.ics[0]
        self.name = self.config.get("name")

    def _write(self, reg, value):
        self.module.write_register(reg, value)

    def _read(self, reg):
        return self.module.read_register(reg)

    def check_chip(self):
        val = self._read(TMC4671.REG.CHIPINFO_ADDR)
        print(f"[{self.name}] CHIPINFO: 0x{val:08X}")

    def initialize(self):
        REG = TMC4671.REG

        # Motor type & PWM configuration
        self._write(REG.MOTOR_TYPE_N_POLE_PAIRS, 0x00020032)  # BLDC, 50 pole pairs
        self._write(REG.PWM_POLARITIES,          0x00000000)
        self._write(REG.PWM_MAXCNT,              0x00000F9F)  # ~4000 counts → ~25 kHz
        self._write(REG.PWM_BBM_H_BBM_L,         0x00000A0A)  # 10 clk break-before-make
        self._write(REG.PWM_SV_CHOP,             0x00000007)  # space-vector, all phases

        # ADC configuration
        self._write(REG.ADC_I_SELECT,        0x18000100)
        self._write(REG.dsADC_MCFG_B_MCFG_A, 0x00100010)
        self._write(REG.dsADC_MCLK_A,        0x20000000)
        self._write(REG.dsADC_MCLK_B,        0x20000000)
        self._write(REG.dsADC_MDEC_B_MDEC_A, 0x014E014E)
        self._write(REG.ADC_I0_SCALE_OFFSET,  0x010082DC)  # scale=1, offset=33500
        self._write(REG.ADC_I1_SCALE_OFFSET,  0x010080E8)  # scale=1, offset=33000

        # Open-loop settings
        self._write(REG.OPENLOOP_MODE,            0x00000000)
        self._write(REG.OPENLOOP_ACCELERATION,    0x0000003C)  # 60
        self._write(REG.OPENLOOP_VELOCITY_TARGET, 0xFFFFFFFB)  # −5 (initial stopped state)

        # Feedback selection — open loop (PHI_E_SELECTION = 2)
        self._write(REG.PHI_E_SELECTION, 0x00000002)
        self._write(REG.UQ_UD_EXT,       0x00000E17)  # UD=3607 drive voltage

        print(f"[{self.name}] Initialized.")

    # ------------------------------------------------------------------
    # Open-loop test drive — mirrors the test sequence in the config
    # ------------------------------------------------------------------

    def open_loop_test(self):
        """
        Replicates the open-loop test drive from the TMCL config:
          rotate right 2 s → rotate left 4 s → stop 2 s → cut drive voltage
        """
        REG = TMC4671.REG

        # Switch to open-loop velocity mode (MODE_RAMP_MODE_MOTION = 8)
        self._write(REG.MODE_RAMP_MODE_MOTION, 0x00000008)

        # Rotate right
        self._write(REG.OPENLOOP_VELOCITY_TARGET, 0x0000003C)  # +60
        time.sleep(2.0)

        # Rotate left
        self._write(REG.OPENLOOP_VELOCITY_TARGET, 0xFFFFFFC4)  # −60
        time.sleep(4.0)

        # Stop
        self._write(REG.OPENLOOP_VELOCITY_TARGET, 0x00000000)
        time.sleep(2.0)

        # Remove drive voltage
        self._write(REG.UQ_UD_EXT, 0x00000000)
        print(f"[{self.name}] Open-loop test complete.")


    def rotate(self, velocity):
        self._write(TMC4671.REG.OPENLOOP_VELOCITY_TARGET, velocity)

    def stop(self):
        self._write(TMC4671.REG.OPENLOOP_VELOCITY_TARGET, 0)