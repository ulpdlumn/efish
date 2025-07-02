import numpy as np
import pickle
import glob
import matplotlib.pyplot as plt


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
    # fns = glob.glob('__media__/*')
    fn = '/home/user/PESANTE/UM3/250702/wavelength_scan__first_test_1751473795.2466938.pkl'
    fn = '/home/user/PESANTE/UM3/250702/wavelength_scan__first_test_1751476180.844844.pkl'
    with open(fn, 'rb') as fi:
        datacollection = pickle.load(fi)

    PMT = []
    PD  = []
    PRE = []
    WL  = []

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
    ax.plot(WL, PD)
    ax.plot(WL, PRE)
    plt.draw();plt.pause(.001)

    fig, ax= plt.subplots(sharex=True)
    ax.plot(PD, PMT)
    plt.draw();plt.pause(.001)

