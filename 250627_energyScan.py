'''This script demonstrate how to use some automation scripts to automatically collect an energy scan of the laser '''
import seeOutside
from lc4 import *
import PS300 as ps
import pg575v2 as pg
import opotek2 as opo

import pickle
import numpy as np


import time
import threading
from pathlib import Path
import os, configparser
import matplotlib.pyplot as plt

allowedMDepth = [25e6, 12.5e6, 5e6, 1.25e6, 5e5, 125e3, 5e4, 125e2, 5e3, 1250]
allowedtdiv   = [100, 200, 500]  


notes = "_em570_sensormoved"    # additional notes
EMCorrFac = 1/5 # energy meter correction factor [V/W]
LaserFreq = 10  # [Hz]
waitingtime = 3 # time after tuning before starting the acquisition
aqtime = 5  # acquisition time for each condition 
wstep = 5   # wavelength scan step 
reps = 3
wavelengthsBase = np.arange(560, 592.5, wstep)
wavelengths = []
for r in range(reps):
    wavelengths = np.array([*wavelengths, *wavelengthsBase])

saveloc = "__media__/"  # location where to save files 
QS_DELAY_US = 50    # (35–160 µs allowed)


# Q-Smart keep-alive -------------------------------------------------
def _keep_alive():
    while keep_running:
        opo.laser_error_check(SYSTEM)   # lightweight ping
        time.sleep(4)                   # I think the timeout is 10 s


# ----
def oscilloscope_single(ch : int = 1, tdiv : float = 1, max_points : int = allowedMDepth[-1], init : bool = False):
    """Test single-shot acquisition (sequence off)."""
    duration = tdiv * 10
    SPS = max_points / duration
    t, y, =[],[]
    scope = MauiScope("192.168.8.223", debug=True)
    try:
        scope._log('[FUNC] Single acquisition ')
        scope.buzz()
        if init:
            for ii in range(1, 5):
                if ii!=ch:
                    scope.enable_channel(ii, False)
                    scope.enable_trace(ii, False)
            scope.enable_channel(ch, True)
            scope.enable_trace(ch, True)
            
            scope.sequence(enable=False)
            scope.set_vdiv(ch, .01) # sets vdiv to 10 mv
            scope.set_tdiv(tdiv)
            scope.set_mdepth(max_points)
            scope._log('INIT COMPLETED...')
        
        scope.single(timeout=5, forceTr=True)
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

if False:
        t, y = oscilloscope_single(ch =4, tdiv = 1, init = 0==0)
        import matplotlib.pyplot as plt
        fig, ax= plt.subplots()
        ax.plot(t,y)
        plt.draw();plt.pause(.001)


        input(aaaa)
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
collection = []
for ii, wavelength in enumerate( wavelengths ):
        print(f"Running the system for 10 seconds at {wavelength}...")
        # check if the configuration can be kept the same
        assert low <= wavelength <= high
        opo.system_tune(wavelength, SYSTEM)
        keep_running = True
        threading.Thread(target=_keep_alive, daemon=True).start()
        time.sleep(waitingtime)   # wait some seconds before actually starting to collet data

#.        if ii==0: input("check scope")
        # here collect data from the oscilloscope
        t, y = oscilloscope_single(ch =4, tdiv = aqtime/10, init = ii==0)
        collection.append([QS_DELAY_US, wavelength,  y.mean(), (y.max() - y.min()) ])

        print(f"Average energy at {wavelength} n: {y.mean()}")

keep_running = False            # stop keep-alive thread    # maybe if can go one indentation less

collection = np.array(collection)
## saving the results
with open(f'{saveloc}energy_scan_QS{QS_DELAY_US}{notes}.pkl', 'wb') as fi:
    pickle.dump(collection, fi)


# ─── 8. Disable the Q-switch ────────────────────────────────────────────────
print(f"Disabling qswitch...")
keep_running = False            # stop keep-alive thread    # maybe if can go one indentation less
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


## plot the reuslts
if True:
    fig, ax= plt.subplots()
    ax.plot(collection[:,1], collection[:,2] / EMCorrFac / LaserFreq, 'sr', label=f'Energy');
    ax.set_xlabel("Wavelength [nm]")
    ax.set_ylabel("Average pulse energy [J]")
    ax.set_title(f"Average pulse energy vs wavelength\nat QS delay: {QS_DELAY_US} us")
    plt.legend(frameon=False); 
    ax.grid()
    plt.draw();plt.pause(.001)
    plt.savefig( f'{saveloc}energy_scan_QS{QS_DELAY_US}{notes}.png')
    
    