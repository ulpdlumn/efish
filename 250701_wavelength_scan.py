'''
First EFISH laser wavelngth scan!

'''
USELASER = True#False
import seeOutside
from lc4 import *
import PS300 as ps
import pg575v2 as pg
if USELASER: import opotek2 as opo

import pickle
import numpy as np


import time
import threading
from pathlib import Path
import os, configparser
import matplotlib.pyplot as plt

### TODO:
# pressure sensor channel #4: just get the average, not the waveform


allowedMDepth = [25e6, 12.5e6, 5e6, 1.25e6, 5e5, 125e3, 5e4, 125e2, 5e3, 1250]
allowedtdiv   = [100, 200, 500]  


notes = "_first_test"    # additional notes
LaserFreq = 10  # [Hz]
waitingtime = 3 # time after tuning before starting the acquisition

wavelengths = np.array([
    *np.arange(560, 568, 1),
    *np.arange(568, 574, .1),
    *np.arange(574, 577, 1),
    *np.arange(577, 582, .1),
    *np.arange(582, 586, 1),
    ])

wavelengths = np.arange(561, 591, 5)

tdiv = 10e-9
mdepth = 1250
segments = 100
saveCollection = False
# saveloc = "__media__/"  # location where to save files
saveloc = r"C:\\\\Users\\L136-ULPDL\\Desktop\\SharedDataAccess\\"  # location where to save files
QS_DELAY_US = 35    # (35–160 µs allowed)


# Q-Smart keep-alive -------------------------------------------------
if USELASER:
    def _keep_alive():
        while keep_running:
            opo.laser_error_check(SYSTEM)   # lightweight ping
            time.sleep(4)                   # I think the timeout is 10 s


# ----
def test_sequence(mdepth = 1_000, segments = 1000, tdiv=50e-9, init=False):
    """Test sequence acquisition of 3 segments."""
    scope = MauiScope("192.168.8.223", debug=True)
    try:
        scope.buzz()
        if init:
            scope.enable_channel(1, True)
            scope.enable_channel(2, True)
            scope.enable_channel(3, False)
            scope.enable_channel(4, True)
            scope.enable_trace(1, True)
            scope.enable_trace(2, True)
            scope.enable_trace(3, False)
            scope.enable_trace(4, True)

            # scope.set_vdiv(1, 2)
            scope.set_tdiv(tdiv)
            scope.set_mdepth(mdepth)
            scope.sequence(enable=True, segments=segments)

        scope.single(timeout=10)

        t0  = time.time()
        y1 = scope.get_waveform(1, max_points=mdepth*segments, with_time=False)
        y2    = scope.get_waveform(2, max_points=mdepth*segments)
        y3    = scope.get_waveform(4, max_points=mdepth*segments)
        print(f'\t\tTIME REQUIRED: {time.time()-t0}')
    finally:
        scope.close()

    return y1, y2, y3

# ─── 0. Desired conditions ───────────────────────────────────────────────────

SYSTEM = 0                  # single-system setup
WAVELENGTH_NM = 580.0       # desired output

if False:
    t, y1,y2,y3 = test_sequence(segments=10, mdepth = 1250, tdiv=10e-9)
    # fig, ax= plt.subplots(3, 1, sharex=True)
    # for ii, y in enumerate([y1,y2,y3]):
    # ax[ii].plot(y)
    # ax[ii].set_title(len(y))
    # plt.draw();plt.pause(.001)

def reduce_median(y, segments):
    y = y.reshape(segments, len(y)//segments)
    return np.median(y, axis=1)

if USELASER:
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
try:
    collection = []
    for ii, wavelength in enumerate( wavelengths ):
            print(f"Running the system at {wavelength}...")
            # check if the configuration can be kept the same
            # assert low <= wavelength <= high
            if USELASER:
                opo.system_tune(wavelength, SYSTEM)
                keep_running = True
                threading.Thread(target=_keep_alive, daemon=True).start()
            time.sleep(waitingtime)   # wait some seconds before actually starting to collet data
            y1,y2,y4 = test_sequence(segments=segments, mdepth = mdepth, tdiv=tdiv, init=ii==0)
            data = [time.time(), QS_DELAY_US, tdiv, segments, mdepth, wavelength,y1,y2,y4]
            collection.append(data)
# finally:
            if not(saveCollection):
                try:
                    ## saving the results
                    filename = f'{saveloc}{wavelength}_wavelength_scan_{notes}_{time.time()}.pkl'
                    print(f'Saving data on file {filename}')
                    with open(filename, 'wb') as fi:
                        pickle.dump(data, fi)
                except:
                    print('Saving failed')
except:
    print('Acquisition failed :( ')
finally:
    if saveCollection:
        ## saving the results
        filename = f'{saveloc}wavelength_scan_{notes}_{time.time()}.pkl'
        print(f'Saving data on file {filename}')
        with open(filename, 'wb') as fi:
            pickle.dump(data, fi)


if USELASER:
    keep_running = False            # stop keep-alive thread    # maybe if can go one indentation less
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


