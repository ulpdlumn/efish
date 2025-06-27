'''This script demonstrate how to use some automation scripts to automatically collect an energy scan of the laser '''
import seeOutside
import lc4 as lc
import PS300 as ps
import pg575v2 as pg
#import opotek2 as opo

import time
import threading
from pathlib import Path
import os, configparser


# Q-Smart keep-alive -------------------------------------------------
def _keep_alive():
    while keep_running:
        opo.laser_error_check(SYSTEM)   # lightweight ping
        time.sleep(4)                   # I think the timeout is 10 s


# ----
def oscilloscope_single(ch : int = 1, duration : float = 20, SPS : int = 100, init : bool = False):
    """Test single-shot acquisition (sequence off)."""
    max_points = SPS * duration
    t, y, =[],[]
    scope = MauiScope("192.168.8.223", debug=True)
    try:
        scope._log('[FUNC] Single acquisition ')
        scope.buzz()
        if init:
            for ii in range(4):
                if ii!=ch:
                    scope.enable_channel(ii, False)
                    scope.enable_trace(ii, False)
            scope.enable_channel(ch, True)
            scope.enable_trace(ch, True)
            scope.sequence(enable=False)
            scope.set_vdiv(ch, 1)
            scope.set_tdiv(duration/10)
            scope.set_mdepth(max_points)
        scope.single(timeout=5)
        scope.force()   # this should trigger the trigger, no matter what
        t, y = scope.get_waveform(ch, max_points=max_points, with_time=True)
        print(f"Single test: captured {len(y)} samples")
    finally:
        scope.close()
    return t, y

if False:
    import matplotlib.pyplot as plt
    fig, ax= plt.subplots()
    ax.plot(t,y, label=f'ch {ch}');
    plt.legend(); plt.draw();plt.pause(.001)

# ─── 0. Desired conditions ───────────────────────────────────────────────────

SYSTEM = 0                  # single-system setup
WAVELENGTH_NM = 580.0       # desired output
QS_DELAY_US = 90            # mid-range value (35–160 µs allowed) / this should
                            # be determined automatically from the config file


# ─── 1. Initialise ───────────────────────────────────────────────────────────
print("System init...")
opo.system_init(system_index=SYSTEM)

# ─── 2. Home all motors ──────────────────────────────────────────────────────
print("Homing motors...")
opo.motor_home(SYSTEM)      # homes OPO & UV axes

# ─── 3. Select the Signal range ──────────────────────────────────────────────
print("Figuring out which configuration to use...")
CONFIG_SIGNAL = opo.pick_config(WAVELENGTH_NM)  # figure it out from ini file
low, high = opo.system_select_config(CONFIG_SIGNAL, SYSTEM)

# ─── 4. Tune to 580 nm ───────────────────────────────────────────────────────
print(f"Tuning to {WAVELENGTH_NM} nm...")
assert low <= WAVELENGTH_NM <= high
opo.system_tune(WAVELENGTH_NM, SYSTEM)

# ─── 5. Turn the flash-lamp ON (internal trigger) ────────────────────────────
print(f"Turning flashlamps on...")
opo.laser_flash_lamp(1, 0, SYSTEM)

# ─── 6. Set output energy via Q-switch delay ─────────────────────────────────
print(f"Setting qswitch delay to {QS_DELAY_US}...")
opo.laser_qswitch_delay(QS_DELAY_US, SYSTEM)

# ─── 7.0 Wait some time before qswitch  ──────────────────────────────────────
print(f"Waiting 10 seconds...")
keep_running = True
threading.Thread(target=_keep_alive, daemon=True).start()
time.sleep(10)
keep_running = False            # stop keep-alive thread

# ─── 7.1 Enable the Q-switch (start lasing) ───────────────────────────────────
print(f"Enabling qswitch...")
opo.laser_qswitch(1, SYSTEM)

# ─── Run beam for 10 s ───────────────────────────────────────────────────────
for wavelength in range(560, 585, 5):
        print(f"Running the system for 10 seconds at {wavelength}...")
        # check if the configuration can be kept the same
        assert low <= wavelength <= high
        opo.system_tune(wavelength, SYSTEM)
        keep_running = True
        threading.Thread(target=_keep_alive, daemon=True).start()
        time.sleep(5)   # wait 5 seconds before actually starting to collet data

        # here collect data from the oscilloscope


        keep_running = False            # stop keep-alive thread    # maybe if can go one indentation less


# ─── 8. Disable the Q-switch ────────────────────────────────────────────────
print(f"Disabling qswitch...")
opo.laser_qswitch(0, SYSTEM)

# ─── 9. Turn the flash-lamp OFF ──────────────────────────────────────────────
print(f"Stopping flashlamps...")
opo.laser_flash_lamp(0, 0, SYSTEM)

# ─── 10. Park motors (reduces next-boot init time) ───────────────────────────
print(f"Parking motors...")
opo.motor_park(SYSTEM)

# ─── 11. Close ports & release resources ─────────────────────────────────────
print(f"Closing the system...")
opo.system_close(SYSTEM)

