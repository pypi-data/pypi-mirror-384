import multiprocessing
import re
from joblib import Parallel, delayed
from .atimes2corr import atimes_2_corr
from .fcs2corr import Correlations
import numpy as np
from .extract_spad_photon_streams import extract_spad_photon_streams


def atimes_2_corrs_parallel(data, list_of_g, accuracy=50, taumax="auto", root=0, averaging=None, perform_coarsening=True, logtau=True, split=10, list_of_g_out=None):
    """
    Calculate correlations between several photon streams with arrival times
    stored in macrotimes, using parallel computing to speed up the process

    Parameters
    ----------
    data : TYPE
        Object having fields det0, det1, ..., det24 which contain
        the macrotimes of the photon arrivals [in a.u.].
        In addition, the object must have a field "data.macrotime" containing
        the macrotime unit in s (e.g. 1e-12 for ps)
    list_of_g : list
        List of correlations to calculate
        e.g. [4, 12, 'sum3', 'sum5', 'x1011'] or ['crossAll']
    accuracy : float, optional
        Accuracy with which to calculate G. The default is 50.
    taumax : float or string, optional
        Maximum tau value for which to calculate G. The default is "auto".
    root : int, optional
        used for GUI only to pass progress. The default is 0.
    averaging : list of strings
        used to average cross correlations, e.g.
        averaging = ['14x12+15x3', '10x12+9x3', '12x14+3x15']
        averages the xcorr between ch14x12 and ch15x13 and saves them
        in a field with name from "list_of_g_out". THe length of averaging list
        and list_of_g_out must be the same
    perform_coarsening : Boolean, optional
        Perform coarsening. The default is True.
    logtau : Boolean, optional
        Use log spaced tau values. The default is True.
    split : float, optional
        Chunks size with which to split the data. The default is 10.
    list_of_g_out : list of strings, optional
        used for GUI only. The default is None.

    Returns
    -------
    G : object
        object with [N x 2] matrices with tau and G values

    """
    
    n_ch = len([attr for attr in dir(data) if attr.startswith('det')])
    if n_ch < 1:
        return None
    
    if taumax == "auto":
        taumax = 1e12 # ps
    
    calc_all_xcorr = False
    if "crossAll" in list_of_g:
        list_of_g = convert_crossall_to_list_of_g(n_ch)
        calc_all_xcorr = True
    
    G = Correlations()
    
    calcAv = False
    if 'av' in list_of_g:
        # calculate the correlations of all channels and calculate average
        list_of_g.remove('av')
        list_of_g += list(range(n_ch))
        calcAv = True
    
    for idx_corr, corr in enumerate(list_of_g):
        if root != 0:
            root.progress = idx_corr / len(list_of_g)
        print("Calculating correlation " + str(corr))
        
        # EXTRACT DATA
        crossCorr = False
        if type(corr) == int:
            dataExtr = getattr(data, 'det' + str(corr))
            t0 = dataExtr[:, 0]
            corrname = 'det' + str(corr)
        elif corr[0] == 'x':
            c0 = corr[1:3] # first channel
            c1 = corr[3:5] # second channel
            print("Extracting photons channels " + c0 + " and " + c1)
            dataExtr = getattr(data, 'det' + str(int(c0)))
            t0 = dataExtr[:, 0]
            dataExtr1 = getattr(data, 'det' + str(int(c1)))
            t1 = dataExtr1[:, 0]
            corrname = corr
            crossCorr = True
        else:
            print("Extracting and sorting photons")
            dataExtr = extract_spad_photon_streams(data, corr)
            t0 = dataExtr[:, 0]
            corrname = corr
        
        # CALCULATE CORRELATIONS
        duration = t0[-1] * data.macrotime
        Nchunks = int(np.floor(duration / split))
        # go over all filters
        num_filters = np.shape(dataExtr)[1] - 1
        for j in range(num_filters):
            print("   Filter " + str(j))
            if crossCorr == False:
                if j == 0:
                    Processed_list = Parallel(n_jobs=multiprocessing.cpu_count() - 1)(delayed(parallel_g)(t0, [1], data.macrotime, j, split, accuracy, taumax, perform_coarsening, logtau, chunk) for chunk in list(range(Nchunks)))
                else:
                    w0 = dataExtr[:, j+1]
                    Processed_list = Parallel(n_jobs=multiprocessing.cpu_count() - 1)(delayed(parallel_g)(t0, w0, data.macrotime, j, split, accuracy, taumax, perform_coarsening, logtau, chunk) for chunk in list(range(Nchunks)))
            else:
                if j == 0:
                    Processed_list = Parallel(n_jobs=multiprocessing.cpu_count() - 1)(delayed(parallel_gx)(t0, [1], t1, [1], data.macrotime, j, split, accuracy, taumax, perform_coarsening, logtau, chunk) for chunk in list(range(Nchunks)))
                else:
                    w0 = dataExtr[:, j+1]
                    w1 = dataExtr1[:, j+1]
                    Processed_list = Parallel(n_jobs=multiprocessing.cpu_count() - 1)(delayed(parallel_gx)(t0, w0, t1, w1, data.macrotime, j, split, accuracy, taumax, perform_coarsening, logtau, chunk) for chunk in list(range(Nchunks)))
            
            if calc_all_xcorr:
                if idx_corr == 0:
                    n_times = len(Processed_list[0][:,0])
                    g_cross_all = np.zeros((num_filters, Nchunks, n_times, n_ch, n_ch))
                for chunk in range(Nchunks):
                    g_temp = Processed_list[chunk]
                    g_times = g_temp[:,0]
                    g_cross_all[j, chunk, :, int(c0), int(c1)] = g_temp[:,1]
            else:
                for chunk in range(Nchunks):
                    if list_of_g_out is None:
                        corrname_out = corrname + "F" + str(j)
                    else:
                        corrname_out = list_of_g_out[idx_corr]
                        if j > 0:
                            corrname_out += "F" + str(j)
                    setattr(G, corrname_out + '_chunk' + str(chunk), Processed_list[chunk])
           
                # average over all chunks
                listOfFields = list(G.__dict__.keys())
                listOfFields = [i for i in listOfFields if i.startswith(corrname_out + "_chunk")]
                Gav = sum(getattr(G, i) for i in listOfFields) / len(listOfFields)
                setattr(G, corrname_out + '_average', Gav)
    
    if calc_all_xcorr:
        g_temp = np.zeros((len(g_times), 2))
        g_temp[:,0] = np.squeeze(g_times)
        if averaging is None:
            for j in range(n_ch):
                for k in range(n_ch):
                    for l in range(Nchunks):
                        g_temp[:,1] = g_cross_all[0,l,:,j,k]
                        setattr(G, 'det' + str(j) + 'x' + str(k) + '_chunk' + str(l), g_temp)
        else:
            # average over multiple cross-correlations
            avs = averaging
            els = list_of_g_out
            for l in range(Nchunks):
                for el, av in enumerate(avs):
                    singleAv = [int(ch_nr) for ch_nr in re.findall(r'\d+', av)]
                    Nav = int(len(singleAv) / 2)
                    g_temp = np.zeros((len(g_times), 2))
                    g_temp[:,0] = np.squeeze(g_times)
                    for ind_av in range(Nav):
                        g_temp[:,1] += g_cross_all[0, l, :, singleAv[2*ind_av], singleAv[2*ind_av+1]]
                    g_temp[:,1] /= Nav
                    setattr(G, els[el] + '_chunk' + str(l), g_temp)
    
    # ---------- CALCULATE AVERAGE CORRELATION OF ALL CHUNKS ----------
    print("Calculating average correlations")
    if calc_all_xcorr:
        G = calc_average_correlation(G)
    
    if calcAv:
        # calculate average correlation of all detector elements
        for f in range(num_filters):
            # start with correlation of detector 20 (last one)
            Gav = getattr(G, 'det' + str(n_ch-1) + 'F' + str(f) + '_average')
            # add correlations detector elements 0-19
            for det in range(n_ch - 1):
                Gav += getattr(G, 'det' + str(det) + 'F' + str(f) + '_average')
            # divide by the number of detector elements to get the average
            Gav = Gav / n_ch
            # store average in G
            setattr(G, 'F' + str(f) + '_average', Gav)
    
    return G


def parallel_g(t0, w0, macrotime, filter_number, split, accuracy, taumax, perform_coarsening, logtau, chunk):
    tstart = chunk * split / macrotime
    tstop = (chunk + 1) * split / macrotime
    tchunk = t0[(t0 >= tstart) & (t0 < tstop)]
    tchunkN = tchunk - tchunk[0]
    if filter_number == 0:
        # no filter
        Gtemp = atimes_2_corr(tchunkN, tchunkN, [1], [1], macrotime, accuracy, taumax, perform_coarsening, logtau)
    else:
        # filters
        wchunk = w0[(t0 >= tstart) & (t0 < tstop)].copy()
        Gtemp = atimes_2_corr(tchunkN, tchunkN, wchunk, wchunk, macrotime, accuracy, taumax, perform_coarsening, logtau)
    return(Gtemp)


def parallel_gx(t0, w0, t1, w1, macrotime, filter_number, split, accuracy, taumax, perform_coarsening, logtau, chunk):
    tstart = chunk * split / macrotime
    tstop = (chunk + 1) * split / macrotime
    tchunk0 = t0[(t0 >= tstart) & (t0 < tstop)]
    tchunk1 = t1[(t1 >= tstart) & (t1 < tstop)]
    # normalize time by sutracting first number
    tN = np.min([tchunk0[0], tchunk1[0]])
    tchunk0 = tchunk0 - tN
    tchunk1 = tchunk1 - tN
    if filter_number == 0:
        # no filter
        Gtemp = atimes_2_corr(tchunk0, tchunk1, [1], [1], macrotime, accuracy, taumax, perform_coarsening, logtau)
    else:
        # filters
        wchunk0 = w0[(t0 >= tstart) & (t0 < tstop)].copy()
        wchunk1 = w1[(t1 >= tstart) & (t1 < tstop)].copy()
        Gtemp = atimes_2_corr(tchunk0, tchunk1, wchunk0, wchunk1, macrotime, accuracy, taumax, perform_coarsening, logtau)
    return(Gtemp)


def convert_crossall_to_list_of_g(n_ch):
    """
    Convert the string "crossAll" to a list of all crosscorrelations to calculate

    Parameters
    ----------
    n_ch : int
        Number of channels.

    Returns
    -------
    list_of_g : list of strings
        ["x0000", "x0001", ..., "x2525"].

    """
    list_of_g = []
    for i in range(n_ch):
        str_i = ""
        if i < 10:
            str_i += "0"
        str_i += str(i)
        for j in range(n_ch):
            str_j = ""
            if j < 10:
                str_j += "0"
            str_j += str(j)
            list_of_g.append("x" + str_i + str_j)
    return list_of_g


def calc_average_correlation(G):
    # Get list of "root" names, i.e. without "_chunk"
    Gfields = list(G.__dict__.keys())
    t = [Gfields[i].split("_chunk")[0] for i in range(len(Gfields))]
    t = list(dict.fromkeys(t))
    for field in t:
        avList = [i for i in Gfields if i.startswith(field + '_chunk')]
        # check if all elements have same dimension
        Ntau = [len(getattr(G, i)) for i in avList]
        avList2 = [avList[i] for i in range(len(avList)) if Ntau[i] == Ntau[0]]
        
        Gtemp = getattr(G, avList2[0]) * 0
        GtempSquared = getattr(G, avList2[0])**2 * 0
        for chunk in avList2:
            Gtemp += getattr(G, chunk)
            GtempSquared += getattr(G, chunk)**2
        
        Gtemp /= len(avList2)
        Gstd = np.sqrt(np.clip(GtempSquared / len(avList2) - Gtemp**2, 0, None))
        
        Gtot = np.zeros((np.shape(Gtemp)[0], np.shape(Gtemp)[1] + 1))
        Gtot[:, 0:-1] = Gtemp # [time, average]
        Gtot[:, -1] = Gstd[:,1] # standard deviation
        
        setattr(G, str(field) + '_average', Gtot)
        
    return G