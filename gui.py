import tkinter as tk
from tkinter import scrolledtext
import threading
import queue
import sys
import yaml
from pathlib import Path

_CONFIG_PATH = Path(__file__).parent / 'a_config' / 'motor_config.yaml'


BG      = '#1e1e2e'
BG2     = '#181825'
SURFACE = '#313244'
FG      = '#cdd6f4'
BLUE    = '#89b4fa'
GREEN   = '#a6e3a1'
RED     = '#f38ba8'
YELLOW  = '#f9e2af'
TEAL    = '#89dceb'
GRAY    = '#6c7086'


class _LogRedirector:
    def __init__(self, q):
        self._q = q
        self._orig = sys.__stdout__

    def write(self, text):
        self._q.put(text)
        if self._orig:
            self._orig.write(text)

    def flush(self):
        pass


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Membrane Roller Control System")
        self.root.configure(bg=BG)
        self.root.resizable(True, True)
        self.root.minsize(900, 500)

        self._log_q: queue.Queue = queue.Queue()
        self.roller = None
        self._busy = False
        self._all_btns: list = []
        self._sequence_btns: list = []
        self._subsystem_btns: dict = {}  # subsystem name -> list of widgets

        sys.stdout = _LogRedirector(self._log_q)

        self._build_ui()
        self._poll_log()

    # ------------------------------------------------------------------ layout

    def _build_ui(self):
        left = tk.Frame(self.root, bg=BG, padx=12, pady=12)
        left.pack(side=tk.LEFT, fill=tk.Y)

        divider = tk.Frame(self.root, bg=SURFACE, width=1)
        divider.pack(side=tk.LEFT, fill=tk.Y)

        right = tk.Frame(self.root, bg=BG, padx=12, pady=12)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tk.Label(left, text="Membrane Roller Control",
                 bg=BG, fg=FG, font=('Segoe UI', 13, 'bold')).pack(anchor='w', pady=(0, 8))

        # ---- connection ----
        self._section(left, "Connection")
        row = self._row(left)
        self.connect_btn    = self._btn(row, "Connect",    self._do_connect,    BLUE)
        self.disconnect_btn = self._btn(row, "Disconnect", self._do_disconnect, GRAY)
        self.connect_btn.pack(side=tk.LEFT, padx=(0, 4))
        self.disconnect_btn.pack(side=tk.LEFT)
        self.status_lbl = tk.Label(left, text="● Disconnected",
                                   bg=BG, fg=RED, font=('Segoe UI', 9))
        self.status_lbl.pack(anchor='w', pady=(3, 2))

        # ---- full sequence ----
        self._section(left, "Full Sequence")
        row = self._row(left)
        self._btn(row, "Initialize", self._do_initialize, GREEN, sequence=True).pack(side=tk.LEFT, padx=(0, 4))
        self._btn(row, "Roll",       self._do_roll,       BLUE,  sequence=True).pack(side=tk.LEFT, padx=(0, 4))
        self._btn(row, "Shutdown",   self._do_off,        RED,   sequence=True).pack(side=tk.LEFT)

        row_s1 = self._row(left)
        tk.Label(row_s1, text="Stake 1 — Time (s):", bg=BG, fg=FG,
                 font=('Segoe UI', 9)).pack(side=tk.LEFT, padx=(0, 4))
        self.roll_stake1_time_var = tk.StringVar(value="3")
        tk.Entry(row_s1, textvariable=self.roll_stake1_time_var, width=5,
                 bg=SURFACE, fg=FG, insertbackground=FG,
                 relief=tk.FLAT, font=('Segoe UI', 9)).pack(side=tk.LEFT, padx=(0, 10))
        tk.Label(row_s1, text="Point:", bg=BG, fg=FG,
                 font=('Segoe UI', 9)).pack(side=tk.LEFT, padx=(0, 4))
        self.roll_stake1_point_var = tk.StringVar(value="315000")
        tk.Entry(row_s1, textvariable=self.roll_stake1_point_var, width=8,
                 bg=SURFACE, fg=FG, insertbackground=FG,
                 relief=tk.FLAT, font=('Segoe UI', 9)).pack(side=tk.LEFT)

        row_s2 = self._row(left)
        tk.Label(row_s2, text="Stake 2 — Time (s):", bg=BG, fg=FG,
                 font=('Segoe UI', 9)).pack(side=tk.LEFT, padx=(0, 4))
        self.roll_stake2_time_var = tk.StringVar(value="3")
        tk.Entry(row_s2, textvariable=self.roll_stake2_time_var, width=5,
                 bg=SURFACE, fg=FG, insertbackground=FG,
                 relief=tk.FLAT, font=('Segoe UI', 9)).pack(side=tk.LEFT, padx=(0, 10))
        tk.Label(row_s2, text="Point:", bg=BG, fg=FG,
                 font=('Segoe UI', 9)).pack(side=tk.LEFT, padx=(0, 4))
        self.roll_stake2_point_var = tk.StringVar(value="316000")
        tk.Entry(row_s2, textvariable=self.roll_stake2_point_var, width=8,
                 bg=SURFACE, fg=FG, insertbackground=FG,
                 relief=tk.FLAT, font=('Segoe UI', 9)).pack(side=tk.LEFT)

        row_rf = self._row(left)
        tk.Label(row_rf, text="Feeder — Rotations after tip:", bg=BG, fg=FG,
                 font=('Segoe UI', 9)).pack(side=tk.LEFT, padx=(0, 4))
        self.roll_rotations_after_var = tk.StringVar(value="0.218")
        tk.Entry(row_rf, textvariable=self.roll_rotations_after_var, width=5,
                 bg=SURFACE, fg=FG, insertbackground=FG,
                 relief=tk.FLAT, font=('Segoe UI', 9)).pack(side=tk.LEFT)

        # ---- heater ----
        self._section(left, "Heater")
        row = self._row(left)
        self._btn(row, "Enable",  self._do_heater_on,  YELLOW, subsystem='staker').pack(side=tk.LEFT, padx=(0, 4))
        self._btn(row, "Disable", self._do_heater_off, GRAY,   subsystem='staker').pack(side=tk.LEFT)

        # ---- clamp ----
        self._section(left, "Clamp")
        row = self._row(left)
        self._btn(row, "Home",  self._do_clamp_home,  subsystem='clamp').pack(side=tk.LEFT, padx=(0, 4))
        self._btn(row, "Clamp", self._do_clamp_clamp, subsystem='clamp').pack(side=tk.LEFT)

        # ---- staker ----
        self._section(left, "Staker")
        row = self._row(left)
        self._btn(row, "Home",    self._do_staker_home,      subsystem='staker').pack(side=tk.LEFT, padx=(0, 4))
        self._btn(row, "Stake 1", self._do_staker_stake_one, subsystem='staker').pack(side=tk.LEFT, padx=(0, 4))
        self._btn(row, "Stake 2", self._do_staker_stake_two, subsystem='staker').pack(side=tk.LEFT)

        row_s1 = self._row(left)
        tk.Label(row_s1, text="Stake 1 — Time (s):", bg=BG, fg=FG,
                 font=('Segoe UI', 9)).pack(side=tk.LEFT, padx=(0, 4))
        self.stake1_time_var = tk.StringVar(value="3")
        s1_time_entry = tk.Entry(row_s1, textvariable=self.stake1_time_var, width=5,
                                 bg=SURFACE, fg=FG, insertbackground=FG,
                                 relief=tk.FLAT, font=('Segoe UI', 9))
        s1_time_entry.pack(side=tk.LEFT, padx=(0, 10))
        self._subsystem_btns.setdefault('staker', []).append(s1_time_entry)
        tk.Label(row_s1, text="Point:", bg=BG, fg=FG,
                 font=('Segoe UI', 9)).pack(side=tk.LEFT, padx=(0, 4))
        self.stake1_point_var = tk.StringVar(value="315000")
        s1_point_entry = tk.Entry(row_s1, textvariable=self.stake1_point_var, width=8,
                                  bg=SURFACE, fg=FG, insertbackground=FG,
                                  relief=tk.FLAT, font=('Segoe UI', 9))
        s1_point_entry.pack(side=tk.LEFT)
        self._subsystem_btns.setdefault('staker', []).append(s1_point_entry)

        row_s2 = self._row(left)
        tk.Label(row_s2, text="Stake 2 — Time (s):", bg=BG, fg=FG,
                 font=('Segoe UI', 9)).pack(side=tk.LEFT, padx=(0, 4))
        self.stake2_time_var = tk.StringVar(value="5")
        s2_time_entry = tk.Entry(row_s2, textvariable=self.stake2_time_var, width=5,
                                 bg=SURFACE, fg=FG, insertbackground=FG,
                                 relief=tk.FLAT, font=('Segoe UI', 9))
        s2_time_entry.pack(side=tk.LEFT, padx=(0, 10))
        self._subsystem_btns.setdefault('staker', []).append(s2_time_entry)
        tk.Label(row_s2, text="Point:", bg=BG, fg=FG,
                 font=('Segoe UI', 9)).pack(side=tk.LEFT, padx=(0, 4))
        self.stake2_point_var = tk.StringVar(value="316000")
        s2_point_entry = tk.Entry(row_s2, textvariable=self.stake2_point_var, width=8,
                                  bg=SURFACE, fg=FG, insertbackground=FG,
                                  relief=tk.FLAT, font=('Segoe UI', 9))
        s2_point_entry.pack(side=tk.LEFT)
        self._subsystem_btns.setdefault('staker', []).append(s2_point_entry)

        # ---- spindle ----
        self._section(left, "Spindle")
        row = self._row(left)
        self._btn(row, "Home",          self._do_spindle_home,   subsystem='spindle').pack(side=tk.LEFT, padx=(0, 4))
        self._btn(row, "Full Rotation", self._do_spindle_rotate, subsystem='spindle').pack(side=tk.LEFT)

        # ---- feeder ----
        self._section(left, "Feeder")
        row = self._row(left)
        self._btn(row, "Reach Tip", self._do_feeder_tip,    subsystem='feeder').pack(side=tk.LEFT, padx=(0, 4))
        self._btn(row, "Reload",    self._do_feeder_reload, subsystem='feeder').pack(side=tk.LEFT, padx=(0, 4))
        self._btn(row, "Pull Back", self._do_feeder_pull,   subsystem='feeder').pack(side=tk.LEFT)

        row_ff = self._row(left)
        tk.Label(row_ff, text="Rotations after tip:", bg=BG, fg=FG,
                 font=('Segoe UI', 9)).pack(side=tk.LEFT, padx=(0, 4))
        self.feeder_rotations_after_var = tk.StringVar(value="0.218")
        feeder_rot_entry = tk.Entry(row_ff, textvariable=self.feeder_rotations_after_var, width=5,
                                    bg=SURFACE, fg=FG, insertbackground=FG,
                                    relief=tk.FLAT, font=('Segoe UI', 9))
        feeder_rot_entry.pack(side=tk.LEFT)
        self._subsystem_btns.setdefault('feeder', []).append(feeder_rot_entry)

        # ---- LAC cutter ----
        self._section(left, "Cutter (LAC)")
        row = self._row(left)
        self._btn(row, "Home", self._do_lac_home, subsystem='lac').pack(side=tk.LEFT, padx=(0, 4))
        self._btn(row, "Cut",  self._do_lac_cut,  subsystem='lac').pack(side=tk.LEFT)

        row2 = self._row(left)
        tk.Label(row2, text="Position:", bg=BG, fg=FG,
                 font=('Segoe UI', 9)).pack(side=tk.LEFT, padx=(0, 4))
        self.lac_pos = tk.IntVar(value=0)
        self.lac_slider = tk.Scale(row2, from_=0, to=1023, orient=tk.HORIZONTAL,
                                   variable=self.lac_pos,
                                   bg=BG, fg=FG, troughcolor=SURFACE,
                                   highlightthickness=0, length=160,
                                   font=('Segoe UI', 8))
        self.lac_slider.pack(side=tk.LEFT)
        self._subsystem_btns.setdefault('lac', []).append(self.lac_slider)
        self._btn(row2, "Set", self._do_lac_set, subsystem='lac').pack(side=tk.LEFT, padx=(4, 0))

        # ---- log panel ----
        hdr = tk.Frame(right, bg=BG)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="Output Log", bg=BG, fg=FG,
                 font=('Segoe UI', 11, 'bold')).pack(side=tk.LEFT)
        tk.Button(hdr, text="Clear", command=self._clear_log,
                  bg=SURFACE, fg=FG, font=('Segoe UI', 8),
                  relief=tk.FLAT, padx=6, pady=2).pack(side=tk.RIGHT)
        self.log_box = scrolledtext.ScrolledText(
            right, bg=BG2, fg=GREEN, font=('Consolas', 9),
            state='disabled', wrap=tk.WORD)
        self.log_box.pack(fill=tk.BOTH, expand=True, pady=(4, 0))

        self._update_conn_state()

    def _section(self, parent, title):
        tk.Frame(parent, bg=SURFACE, height=1).pack(fill=tk.X, pady=(8, 1))
        tk.Label(parent, text=title, bg=BG, fg=TEAL,
                 font=('Segoe UI', 9, 'bold')).pack(anchor='w', pady=(0, 3))

    def _row(self, parent):
        f = tk.Frame(parent, bg=BG)
        f.pack(fill=tk.X, pady=(0, 2))
        return f

    def _btn(self, parent, text, cmd, color=GRAY, subsystem=None, sequence=False):
        b = tk.Button(parent, text=text, command=cmd,
                      bg=color, fg=BG2, activebackground=FG,
                      font=('Segoe UI', 9, 'bold'),
                      relief=tk.FLAT, padx=8, pady=5, cursor='hand2')
        self._all_btns.append(b)
        if subsystem:
            self._subsystem_btns.setdefault(subsystem, []).append(b)
        if sequence:
            self._sequence_btns.append(b)
        return b

    # ------------------------------------------------------------------ state

    def _update_conn_state(self):
        live = self.roller is not None
        self.connect_btn.configure(state=tk.DISABLED if live else tk.NORMAL)
        self.disconnect_btn.configure(state=tk.NORMAL if live else tk.DISABLED)

        if not live:
            for btns in self._subsystem_btns.values():
                for w in btns:
                    w.configure(state=tk.DISABLED)
            for b in self._sequence_btns:
                b.configure(state=tk.DISABLED)
            self.status_lbl.configure(text="● Disconnected", fg=RED)
            return

        motor_map = {
            'clamp':   self.roller.clamp_motor,
            'staker':  self.roller.staker_motor,
            'spindle': self.roller.spindle_motor,
            'feeder':  self.roller.feeder_motor,
            'lac':     self.roller.lac,
        }
        for subsystem, widgets in self._subsystem_btns.items():
            state = tk.NORMAL if motor_map.get(subsystem) is not None else tk.DISABLED
            for w in widgets:
                w.configure(state=state)

        for b in self._sequence_btns:
            b.configure(state=tk.NORMAL)

        n = sum(1 for m in motor_map.values() if m is not None)
        total = len(motor_map)
        color = GREEN if n == total else YELLOW
        self.status_lbl.configure(text=f"● Connected ({n}/{total})", fg=color)

    def _lock(self):
        for b in self._all_btns:
            b.configure(state=tk.DISABLED)

    def _unlock(self):
        for b in self._all_btns:
            b.configure(state=tk.NORMAL)
        self._update_conn_state()

    # ---------------------------------------------------------------- threading

    def _run(self, fn, *args):
        if self._busy:
            self._append("⚠  Another operation is in progress.\n")
            return
        self._busy = True
        self.root.after(0, self._lock)

        def worker():
            try:
                fn(*args)
            except Exception as exc:
                sys.stdout.write(f"ERROR: {exc}\n")
            finally:
                self._busy = False
                self.root.after(0, self._unlock)

        threading.Thread(target=worker, daemon=True).start()

    # ----------------------------------------------------------------- log

    def _poll_log(self):
        while not self._log_q.empty():
            self._append(self._log_q.get_nowait())
        self.root.after(100, self._poll_log)

    def _append(self, text: str):
        self.log_box.configure(state=tk.NORMAL)
        self.log_box.insert(tk.END, text)
        self.log_box.see(tk.END)
        self.log_box.configure(state=tk.DISABLED)

    def _clear_log(self):
        self.log_box.configure(state=tk.NORMAL)
        self.log_box.delete('1.0', tk.END)
        self.log_box.configure(state=tk.DISABLED)

    # ---------------------------------------------------------------- handlers

    def _do_connect(self):
        def connect():
            from d_robot_control.membrane_roller import MembraneRoller
            with open(_CONFIG_PATH, 'r') as f:
                config = yaml.safe_load(f)
            sys.stdout.write("Connecting to motors...\n")
            self.roller = MembraneRoller(config)
            self.root.after(0, self._update_conn_state)
        self._run(connect)

    def _do_disconnect(self):
        if self.roller is not None:
            self.roller.close()
        self.roller = None
        self._update_conn_state()
        self._append("Disconnected.\n")

    def _do_initialize(self):
        self._run(self.roller.initialize)

    def _do_roll(self):
        try:
            s1_time         = float(self.roll_stake1_time_var.get())
            s1_point        = int(self.roll_stake1_point_var.get())
            s2_time         = float(self.roll_stake2_time_var.get())
            s2_point        = int(self.roll_stake2_point_var.get())
            rotations_after = float(self.roll_rotations_after_var.get())
        except ValueError:
            self._append("ERROR: Invalid stake parameter value.\n")
            return
        self._run(self.roller.roll, s1_time, s1_point, s2_time, s2_point, rotations_after)

    def _do_off(self):
        self._run(self.roller.off)

    def _do_heater_on(self):
        self._run(self.roller.staker_motor.enable_heater)

    def _do_heater_off(self):
        self._run(self.roller.staker_motor.disable_heater)

    def _do_clamp_home(self):
        self._run(self.roller.clamp_motor.home)

    def _do_clamp_clamp(self):
        self._run(self.roller.clamp_motor.clamp)

    def _do_staker_home(self):
        self._run(self.roller.staker_motor.home)

    def _do_staker_stake_one(self):
        try:
            stake_time  = float(self.stake1_time_var.get())
            stake_point = int(self.stake1_point_var.get())
        except ValueError:
            self._append("ERROR: Invalid Stake 1 time or point value.\n")
            return
        self._run(self.roller.staker_motor.stake_one, stake_time, stake_point)

    def _do_staker_stake_two(self):
        try:
            stake_time  = float(self.stake2_time_var.get())
            stake_point = int(self.stake2_point_var.get())
        except ValueError:
            self._append("ERROR: Invalid Stake 2 time or point value.\n")
            return
        self._run(self.roller.staker_motor.stake_two, stake_time, stake_point)

    def _do_spindle_home(self):
        self._run(self.roller.spindle_motor.home)

    def _do_spindle_rotate(self):
        self._run(self.roller.spindle_motor.full_rotation)

    def _do_feeder_tip(self):
        try:
            rotations_after = float(self.feeder_rotations_after_var.get())
        except ValueError:
            self._append("ERROR: Invalid rotations value.\n")
            return
        self._run(self.roller.feeder_motor.reach_tip, rotations_after)

    def _do_feeder_reload(self):
        self._run(self.roller.feeder_motor.reload)

    def _do_feeder_pull(self):
        self._run(self.roller.feeder_motor.pull_back)

    def _do_lac_home(self):
        self._run(self.roller.lac.home)

    def _do_lac_cut(self):
        self._run(self.roller.lac.cut)

    def _do_lac_set(self):
        self._run(self.roller.lac.set_position, self.lac_pos.get())


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == '__main__':
    main()
