'''
Quick TEMPORARY script to plot some debugging results.
This file can be deleted later
'''
import numpy as np
import pickle
import glob
import matplotlib.pyplot as plt

saveloc = '__media__/'

def reduce_median(y, segments):
    y = y.reshape(segments, len(y)//segments)
    return np.median(y, axis=1)

def calculate_length(tdiv, mdepth, segments=1):
    # calculate sampling frequency
    sampling_period = tdiv*10/mdepth if tdiv*10/mdepth > 4e-10 else 4e-10
    samples_one_segment = np.round( tdiv*10/sampling_period ) #TODO check this rounding operation
    return int(samples_one_segment * segments)

def get_matrix(y,tdiv, mdepth, segments):
    y = np.array(y).reshape(segments, len(y)//segments)
    return y[:, :calculate_length(tdiv, mdepth, segments)//segments]

if True:
    fn = '/home/user/PESANTE/UM3/250702/wavelength_scan__first_test_1751473795.2466938.pkl'
    fn = '/home/user/PESANTE/UM3/250702/wavelength_scan__first_test_1751476180.844844.pkl'
    with open(fn, 'rb') as fi:
        datacollection = pickle.load(fi)

    PMT, PD, PRE, WL = [],[],[],[]
    for data in datacollection:
        [aqt, QS_DELAY_US, tdiv, segments, mdepth, wavelength,y1,y2,y4] = data
        M = np.array( [ get_matrix(y, tdiv, mdepth, segments) for y in [y1, y2, y4] ] )
        PD.append( np.sum(M[0]) / segments )
        PMT.append( np.sum(M[1]) / segments )
        PRE.append( np.mean(M[1]) )
        WL.append(wavelength)

        if False:
            fig, ax= plt.subplots(3, 1, sharex=True)
            for ii, y in enumerate([y1,y2,y4]):
                ax[ii].plot(M[ii].transpose(), alpha=.2, linewidth=3, color='rgb'[ii])
            ax.set_title(f'{wavelength} nm')
            plt.draw();plt.pause(.001)

    fig, ax= plt.subplots(sharex=True)
    ax.plot(WL, PMT)
    ax.set_xlabel('Wavelength [nm]')
    ax.set_ylabel('PMT intensity [arb]')
    plt.legend(frameon=False)
    plt.tight_layout()
    plt.draw();plt.pause(.001)
    plt.savefig(f'{saveloc}longscan.png')


fig, axg= plt.subplots(sharex=True)
fn1 = '/home/user/PESANTE/UM3/250702/wavelength_scan__ND30pc_g.304_1751485678.659286.pkl'
fn2 = '/home/user/PESANTE/UM3/250702/wavelength_scan__ND30pc_g_FGL.304_1751486127.0670846.pkl'
fn3 = '/home/user/PESANTE/UM3/250702/wavelength_scan__shortrange_s1_g290_1751488877.199153.pkl'
fn4 = '/home/user/PESANTE/UM3/250702/wavelength_scan__shortrange_s1_g290_FGL_1751489057.2398999.pkl'

# enabele either block
# title = 'UNrealSH'
# for fn, label in zip( [fn1, fn2], ['ND30%','ND30% + FGL']):
title = 'realSH'
for fn, label in zip( [fn3, fn4], ['1G', '1G+FGL']):
    with open(fn, 'rb') as fi:
        datacollection = pickle.load(fi)

    PMT = []
    PD  = []
    PRE = []
    WL  = []

    for kk, data in enumerate( datacollection ):
        [aqt, QS_DELAY_US, tdiv, segments, mdepth, wavelength,y1,y2,y4] = data
        M = np.array( [ get_matrix(y, tdiv, mdepth, segments) for y in [y1, y2, y4] ] )

        if kk== 0:
            PMTNOISE = np.mean(M[1], axis=0)
        M[1] = M[1] - PMTNOISE
        PD.append( np.sum(M[0]) / segments )
        PMT.append( ( np.mean( M[1][:, 85:130] ) ) / segments )
        PRE.append( np.mean(M[1]) )
        WL.append(wavelength)

        print(wavelength-571)
        if True and np.abs(wavelength-571) < .01 and not('GL' in label):
            fig, ax= plt.subplots( sharex=True)
            ax.plot(np.sum(M[0], axis=1), np.sum(M[1][:, 85:130], axis=1) , 's')
            fig.suptitle(f'{wavelength:0.1f} nm')
            ax.set_xlabel('Photodiode (~fundamental) [arb.]')
            ax.set_ylabel('PMT (~SH) [arb.]')
            plt.draw();plt.pause(.001)
            plt.savefig(f'{saveloc}{title}_shreally.png')

            fig, ax= plt.subplots( sharex=True)
            ax.plot(np.max(M[0], axis=1), np.mean(M[1][:, 85:130], axis=1) , 's')
            fig.suptitle(f'{wavelength:0.1f} nm')
            ax.set_xlabel('Photodiode (~fundamental) [arb.]')
            ax.set_ylabel('PMT (~SH) [arb.]')
            plt.draw();plt.pause(.001)
            plt.savefig(f'{saveloc}{title}_shreally_alt.png')

            fig, ax= plt.subplots(3, 1, sharex=True)
            for ii, y in enumerate([y1,y2,y4]):
                ax[ii].plot(M[ii].transpose(), alpha=.2, linewidth=3, color='rgb'[ii])
            fig.suptitle(f'{wavelength} nm')
            plt.draw();plt.pause(.001)
            plt.savefig(f'{saveloc}{title}_waveforms.png')

    axg.plot(WL, PMT, 's-', label=label)
axg.set_xlabel('Wavelength [nm]')
axg.set_ylabel('PMT intensity [arb]')
plt.legend(frameon=False)
plt.tight_layout()
plt.draw();plt.pause(.001)
plt.savefig(f'{saveloc}{title}.png')

