import numpy as np
import re


def extract_spad_photon_streams(data, mode):
    """
    Extract data from specific detector elements from SPAD-fcs time-tagging data

    Parameters
    ----------
    data : object
        Object with for each detector element a 2D array [t, m, F1, F2]
        - t: vector with macrotimes photon arrivals
        - m: microtimes
        - F1, F2, ... filter weights (based on microtimes).
    mode : string
        Either
        - "sum3": sum central 9 detector elements
        - "sum5": sum all detector elements
        - "C3+4+7+12" to custom sum over channels 3, 4, 7 and 12
        - int: to extract photons from a single channel
        TODO
        - a number i between -1 and -26: sum all elements except for i
        - "sum": sum over all detector element and all time points
        - "sum3_5D": sum central 9 detector elements in [z, y, x, t, c] dataset
        - "outer": sum 16 detector elements at the edge of the array
        - "chess0": sum all even numbered detector elements
        - "chess1": sum all odd numbered detector elements
        - "upper_left": sum the 12 upper left detector elements
        - "lower_right": sum the 12 lower right detector elements.

    Returns
    -------
    datasum : np.array()
        2D array with concatenated and sorted detector elements data.

    """
    
    if isinstance(mode, str):
        if mode[0] == 'C':
            # list of channels to be summed, e.g. "C1+3+12+42"
            listOfFields = ['det' + str(i) for i in re.findall(r'\d+', mode)]
        elif mode == 'central':
            # get list of detector fields
            listOfFields = [12] # [4, 5, 6, 9, 10, 11, 14, 15, 16]
            listOfFields  = ['det' + str(i) for i in listOfFields]
        elif mode == 'sum3':
            # get list of detector fields
            listOfFields = [6, 7, 8, 11, 12, 13, 16, 17, 18] # [4, 5, 6, 9, 10, 11, 14, 15, 16]
            listOfFields  = ['det' + str(i) for i in listOfFields]
        elif mode == 'sum5':
            # get list of detector fields
            listOfFields = list(data.__dict__.keys())
            listOfFields = [i for i in listOfFields if i.startswith('det')]
    else:
        # number given
        listOfFields = ['det' + str(mode)]
   
    
    # concatenate all photon streams
    for j in range(len(listOfFields)):
        if j == 0:
            datasum = getattr(data, listOfFields[j])
        else:
            datasum = np.concatenate((datasum, getattr(data, listOfFields[j])))
    
    # sort all photon streams
    datasum = datasum[datasum[:,0].argsort()]
    
    # remove photon pairs with the same macrotime
    [dummy, ind] = np.unique(datasum[:,0], return_index=True)
    datasum = datasum[ind,:]
    
    return datasum
