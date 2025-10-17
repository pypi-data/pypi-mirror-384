import numpy as np

def CV(
        signal: np.ndarray, 
        autoBkgr: float, 
        dataPrepBkgr: float, 
        objectRp, 
        correct_with_bkgr=False, 
        which_bkgr='auto'
    ):
    """Function used to calculate coefficient of variation.

    NOTE: Make sure to name the function with the same name as the Python file
    containing this function (e.g., this file is named CV.py and the function
    is named CV)

    Parameters
    ----------
    signal : numpy 1D array
        This is a numpy array with all the intensities of the signal
        from each single segmented object.
    autoBkgr : single numeric value
        Median of all the background pixels (i.e. pixels with value 0 in the
        segmentation mask). Pass None if background correction with
        this value is not needed.
    dataPrepBkgr : single numeric value
        Median of all the pixels inside the background ROIs added during the
        data prep step (Cell-ACDC module 1).
        Pass None if background correction with this vaue is not needed.
    objectRp: skimage.measure.RegionProperties class
        Region properties for the single object. 
        Refer to `skimage.measure.regionprops` for more information
        on the available region properties.
    correct_with_bkgr : boolean
        Pass True if you need background correction.
    which_bkgr : string
        which_bkgr='auto' for correction with autoBkgr or
        which_bkgr='dataPrep' for correction with dataPrepBkgr

    Returns
    -------
    float
        Coefficient of Variation

    """
    
    if correct_with_bkgr:
        if which_bkgr=='auto':
            signal = signal - autoBkgr
        elif dataPrepBkgr is not None:
            signal = signal - dataPrepBkgr

    # Here goes your custom metric computation
    CV = np.std(signal)/np.mean(signal)

    return CV
