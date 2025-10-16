import numpy as np
from .checkfname import checkfname
from tifffile import imwrite, imread
from matplotlib import cm

def array2tiff(data, fname, pxsize=1, dim="yxz", transpose3=True):
    """
    Write 2D or 3D array to tiff image file

    Parameters
    ----------
    data : np.array
        2D or 3D array with data (integer numbers int16)
        order: TZCYXS
        with    t   time
                c   channel.
    fname : string
        Name of the file to write to.
    pxsize : float, optional
        Pixel size [µm]. The default is 1.
    dim : TYPE, optional
        String with dimensions in image
        e.g. z stack of planar images: dim = "yxz"
        The order must be "tzcyxs". The same order must be used for data
        E.g. for a xy time series: dim="tyx" and 'data' is a 3D
        array with time, y, and x as 1st, 2nd, and 3r dimension
        The only exception is that for a 3D array also "yxz" is ok
        in combination with transpose3=True
        (which moves the 3rd dimension to the first to correct the
         order). The default is "yxz".
    transpose3 : boolean, optional
        Transpose array. The default is True.

    Returns
    -------
    Tiff image.

    """
    
    # check file extension
    fname = checkfname(fname, "tiff")
    
    # check number of images in data
    ndim = data.ndim
    if ndim >= 3 and transpose3:
        # transpose data to make 3rd dimension first
        data = np.transpose(data, (2, 0, 1))
    
        # order of dimensions is now TZCYXS
        dimAll = "tzcyxs"
        N = [1, 1, 1, 1, 1, 1]
        d = 0
        Ishape = np.shape(data)
        for i in range(6):
            if dimAll[i] in dim:
                N[i] = Ishape[d]
                d += 1
        
        data.shape = N  # dimensions in TZCYXS order
        
    data = data.astype('int16')
    imwrite(fname, data, imagej=True, resolution=(1./pxsize, 1./pxsize), metadata={'unit': 'um'})
    
    # add every image to same tiff file    
    #imsave(fname, data)
    
    print("Done.")
    

def array2rgbtiff(data, fname, cmap=cm.hot):
    """
    Write 2D array to tiff image file

    Parameters
    ----------
    data : np.array
        2D array with data (integer values).
    fname : string
        Name of the file to write to.
    cmap : matplotlib color map, optional
        color map. The default is cm.hot.

    Returns
    -------
    tiff image.

    Example:
        array2rgbtiff(data, "data_rgb.tiff", cmap=cm.viridis)
    """
    
    # check file extension
    fname = checkfname(fname, "tiff")
    
    # color map
    data = data.astype(int)
    dataMin = np.min(data)
    data -= dataMin
    dataMax = np.max(data)
    dataRange = dataMax + 1
    colors = cmap
    colorTable = colors(np.linspace(0, 1, int(dataRange)))
    colorTable = colorTable[:, 0:3]
    
    # image
    Ny = np.shape(data)[0]
    Nx = np.shape(data)[1]
    image = np.zeros((Ny, Nx, 3), dtype='uint8')
    for y in range(Ny):
        for x in range(Nx):
            image[y, x, :] = 255 * colorTable[data[y, x], :]
    
    #image = image.astype(uint8)
    imwrite(fname, image, photometric='rgb')
    
    print("Done.")
    
def tiff2array(fileList, Nx, Ny):
    """
    Read .tiff images and return 3D numpy array

    Parameters
    ----------
    fileList : list
        List of .tiff filenames to read.
    Nx : int
        Dimensions of the images.
    Ny : int
        Dimensions of the images.

    Returns
    -------
    imarray : np.array
        3D numpy array (Nf x Ny x Nx) with Nf the number of files.

    """
    
    Nf = len(fileList)
    imarray = np.zeros((Nf, Ny, Nx))
    for i in range(Nf):
        fname = fileList[i]
        im = imread(fname)
        imarray[i,:,:] = np.array(im)
    return imarray