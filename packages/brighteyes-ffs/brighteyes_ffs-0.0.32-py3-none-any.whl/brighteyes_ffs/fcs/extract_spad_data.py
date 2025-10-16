import numpy as np
import re


def extract_spad_data(data, mode):
    """
    Extract data from specific detector elements from SPAD-fcs data

    Parameters
    ----------
    data : 2D numpy array
        [Nt x 25] array with fcs data as a function of time assuming a 
        5x5 array detector
        if 26 columns: last one is assumed to be the sum over all channels.
    mode : scalar or string
        Either
        - a number i between 0-25: extract data detector element i
        - a number i between -1 and -26: sum all elements except for i
        - "sum": sum over all detector elements and all time points
        - "sum3": sum central 9 detector elements
        - "sum3_5D": sum central 9 detector elements in [z, y, x, t, c] dataset
        - "sum5": sum all detector elements (= last column)
        - "outer": sum 16 detector elements at the edge of the array
        - "chess0": sum all even numbered detector elements
        - "chess1": sum all odd numbered detector elements
        - "upper_left": sum the 12 upper left detector elements
        - "lower_right": sum the 12 lower right detector elements
        - "sum5left": sum pixels 6, 10, 11, 12, 16
        - "sum5right", "sum5top", "sum5bottom"
        - "C3+7+8+125": C followed by a custom list of channel numbers
            of which the sum is returned.

    Returns
    -------
    array : numpy array
        Nx1 element vector with N the number of time points
        The vector contains the extracted and/or summed data.

    """
    
    # Check data type
    if isinstance(mode, str):
        if mode[0] == 'C':
            # list of channels to be summed, e.g. "C1+3+12+42"
            channels = [int(i) for i in re.findall(r'\d+', mode)]
            return np.sum(data[:, channels], axis=1)
        else:
            return switch_mode_string(data, mode)
    else:
        # number given
        if mode >= 0:
            return data[:, mode]
        else:
            return np.subtract(data[:, 25], data[:,np.mod(-mode, 25)])
   

def sum_all(data):
    # return total photon counts over all bins over all detector elements
    return np.sum(data[:, 25])
 
def central(data):
    # return central detector element data
    return data[:, 12]

def sum3(data):
    # sum detector elements 6, 7, 8, 11, 12, 13, 16, 17, 18
    datasum = np.sum(data[:, [6, 7, 8, 11, 12, 13, 16, 17, 18]], 1)
    return datasum

def sum5left(data):
    # sum detector elements 6, 10, 11, 12, 16
    datasum = np.sum(data[:, [6, 10, 11, 12, 16]], 1)
    return datasum

def sum5right(data):
    # sum detector elements 8, 12, 13, 14, 18
    datasum = np.sum(data[:, [8, 12, 13, 14, 18]], 1)
    return datasum

def sum5top(data):
    # sum detector elements 2, 6, 7, 8, 12
    datasum = np.sum(data[:, [2, 6, 7, 8, 12]], 1)
    return datasum

def sum5bottom(data):
    # sum detector elements 12, 16, 17, 18, 22
    datasum = np.sum(data[:, [12, 16, 17, 18, 22]], 1)
    return datasum

def sum3_5D(data):
    # sum over all time bins
    datasum = np.sum(data, 3)
    # sum detector elements 6, 7, 8, 11, 12, 13, 16, 17, 18
    datasum = np.sum(datasum[:, :, :, [6, 7, 8, 11, 12, 13, 16, 17, 18]], 3)
    return datasum

def allbuthot(data):
    # sum detector elements all but 1
    print("Not pixel 1")
    datasum = np.sum(data[:, [x for x in range(25) if x != 1]], 1)
    return datasum

def sum5(data):
    # sum all detector elements
    # datasum = data[:, 25]
    datasum = np.sum(data, 1)
    return datasum

def allbuthot_5D(data):
    # sum over all time bins
    datasum = np.sum(data, 3)
    # sum over all detector elements except hot
    datasum = np.sum(datasum[:, :, :, [0, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 18, 19, 20, 21, 22, 23, 24]], 3)
    return datasum

def outer(data):
    # smn 16 detector elements at the edge of the detector
    datasum = np.sum(data[:, [0, 1, 2, 3, 4, 5, 9, 10, 14, 15, 19, 20, 21, 22, 23, 24]], 1)
    return datasum
 
def chess0(data):
    # sum over all even numbered detector elements
    datasum = np.sum(data[:, 0:25:2], 1)
    return datasum

def chess1(data):
    # sum over all odd numbered detector elements
    datasum = np.sum(data[:, 1:25:2], 1)
    return datasum

def chess3a(data):
    # sum over all even numbered detector elements in the central 3x3 matrix
    datasum = np.sum(data[:, [6, 8, 12, 16, 18]], 1)
    return datasum

def chess3b(data):
    # sum over all odd numbered detector elements in the central 3x3 matrix
    datasum = np.sum(data[:, [7, 11, 13, 17]], 1)
    return datasum

def upper_left(data):
    # sum over detector elements 0, 1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 15
    datasum = np.sum(data[:, [0, 1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 15]], 1)
    return datasum

def lower_right(data):
    # sum over detector elements 9, 13, 14, 16, 17, 18, 19, 20, 21, 22, 23, 24
    datasum = np.sum(data[:, [9, 13, 14, 16, 17, 18, 19, 20, 21, 22, 23, 24]], 1)
    return datasum

def switch_mode_string(data, mode):
    switcher = {
        "central": central,
        "center": central,
        "sum3": sum3,
        "sum3_5D": sum3_5D,
        "allbuthot": allbuthot,
        "allbuthot_5D": allbuthot_5D,
        "sum5": sum5,
        "sum": sum_all,
        "outer": outer,
        "chess0": chess0,
        "chess1": chess1,
        "chess3a": chess3a,
        "chess3b": chess3b,
        "upper_left": upper_left,
        "lower_right": lower_right,
        "sum5left": sum5left,
        "sum5right": sum5right,
        "sum5top": sum5top,
        "sum5bottom": sum5bottom
    }
    # Get the function from switcher dictionary
    func = switcher.get(mode, "Invalid mode")
    # Execute the function
    return func(data)