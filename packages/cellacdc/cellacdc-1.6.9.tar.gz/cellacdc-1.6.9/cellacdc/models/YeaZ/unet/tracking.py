import os
import sys
import time
import numpy as np
import pandas as pd
from sklearn.preprocessing import scale
from sklearn.metrics.pairwise import euclidean_distances
from scipy.optimize import linear_sum_assignment
from tqdm import tqdm
from skimage.measure import regionprops
from math import sqrt

try:
    from munkres import Munkres
except ModuleNotFoundError as e:
    pass

def correspondence(prev, curr, use_scipy=True, use_modified_yeaz=True):
    """
    source: YeaZ modified by Cell-ACDC developers
    scipy.optimize.linear_sum_assignment instead of munkres library
    Corrects correspondence between previous and current mask, returns current
    mask with corrected cell values. New cells are given the unique identifier
    starting at max(prev)+1.

    This is done by embedding every cell into a feature space consisting of
    the center of mass and the area. The pairwise euclidean distance is
    calculated between the cells of the previous and current frame. This is
    then used as a cost for the bipartite matching problem which is in turn
    solved by the Hungarian algorithm as implemented in the munkres package.
    """
    newcell = np.max(prev) + 1
    if use_scipy:
        hu_dict = scipy_align(prev, curr, acdc_yeaz=use_modified_yeaz)
    else:
        hu_dict = hungarian_align(prev, curr, acdc_yeaz=use_modified_yeaz)
    new = curr.copy()
    for key, val in hu_dict.items():
        # If new cell
        if val == -1:
            val = newcell
            newcell += 1

        new[curr==key] = val

    return new

def scipy_align(m1, m2, acdc_yeaz=True):
    """
    source: YeaZ modified by Cell-ACDC
    Aligns the cells using the hungarian algorithm using the euclidean distance as
    cost.
    Returns dictionary of cells in m2 to cells in m1. If a cell is new, the dictionary
    value is -1.
    """
    dist, ix1, ix2 = cell_distance(m1, m2, acdc_yeaz=acdc_yeaz)

    # If dist couldn't be calculated, return dictionary from cells to themselves
    if dist is None:
        unique_m2 = np.unique(m2)
        return dict(zip(unique_m2, unique_m2))

    row_ind, col_ind = linear_sum_assignment(dist)

    # Create dictionary of cell indicies
    d = dict([(ix2.get(i2, -1), ix1.get(i1, -1)) for i1, i2 in zip(row_ind, col_ind)])
    d.pop(-1, None)
    return d

def correspondence_stack(stack, signals=None):
    """
    source: YeaZ
    corrects correspondence of a stack of segmented and labeled masks, by
    fitting the hungarian iteratively on the stack
    """
    corrected_stack = np.empty(stack.shape, dtype=np.uint32)
    corrected_stack[0] = stack[0]
    for idx in range(len(stack)):
        try:
            curr = stack[idx+1]
            prev = corrected_stack[idx]
        except IndexError:
            continue
        corrected_stack[idx+1] = correspondence(prev, curr)
        if signals is not None:
            signals.progressBar.emit(1)
    return corrected_stack

def hungarian_align(m1, m2, acdc_yeaz=True):
    """
    source: YeaZ
    Aligns the cells using the hungarian algorithm using the euclidean distance as
    cost.
    Returns dictionary of cells in m2 to cells in m1. If a cell is new, the dictionary
    value is -1.
    """
    dist, ix1, ix2 = cell_distance(m1, m2, acdc_yeaz=acdc_yeaz)

    # If dist couldn't be calculated, return dictionary from cells to themselves
    if dist is None:
        unique_m2 = np.unique(m2)
        return dict(zip(unique_m2, unique_m2))

    solver = Munkres()
    indexes = solver.compute(make_square(dist))

    # Create dictionary of cell indicies
    d = dict([(ix2.get(i2, -1), ix1.get(i1, -1)) for i1, i2 in indexes])
    d.pop(-1, None)
    return d

def cell_to_features(im, c, nsamples=None, time=None):
    """
    source: YeaZ
    Embeds cell c in image im into feature space
    """
    coord = np.argwhere(im==c)
    area = coord.shape[0]

    if nsamples is not None:
        samples = np.random.choice(area, min(nsamples, area), replace=False)
        sampled = coord[samples,:]
    else:
        sampled = coord

    com = sampled.mean(axis=0)

    return {'cell': c,
            'time': time,
            'sqrtarea': np.sqrt(area),
            'area': area,
            'com_x': com[0],
            'com_y': com[1]}

def get_features_acdc(m, t):
    rp = regionprops(m)
    features = {
        'cell': [],
        'time': [],
        'sqrtarea': [],
        'area': [],
        'com_x': [],
        'com_y': []
    }
    for obj in rp:
        area = obj.area
        y, x = obj.centroid
        features['cell'].append(obj.label)
        features['time'].append(t)
        features['sqrtarea'].append(sqrt(area))
        features['area'].append(area)
        features['com_x'].append(y)
        features['com_y'].append(x)
    df = pd.DataFrame(features)
    return df, dict(enumerate(features['cell']))


def get_features(m, t):
    cells = list(np.unique(m))
    if 0 in cells:
        cells.remove(0)
    features = [cell_to_features(m, c, time=t) for c in cells]
    return pd.DataFrame(features), dict(enumerate(cells))

def cell_distance(m1, m2, weight_com=3, acdc_yeaz=True):
    """
    source: YeaZ
    Gives distance matrix between cells in first and second frame, by embedding
    all cells into the feature space. Currently uses center of mass and area
    as features, with center of mass weighted with factor weight_com (to
    make it more important).
    """
    # Modify to compute use more computed features
    #cols = ['com_x', 'com_y', 'roundness', 'sqrtarea']
    cols = ['com_x', 'com_y', 'area']

    get_features_func = get_features_acdc if acdc_yeaz else get_features

    # Create df, rescale
    feat1, ix_to_cell1 = get_features_func(m1, 1)
    feat2, ix_to_cell2 = get_features_func(m2, 2)

    # feat1_acdc, ix_to_cell1_acdc = get_features_acdc(m1, 1)

    # Check if one of matrices doesn't contain cells
    if len(feat1)==0 or len(feat2)==0:
        return None, None, None

    df = pd.concat((feat1, feat2))
    df[cols] = scale(df[cols])

    # give more importance to center of mass
    df[['com_x', 'com_y']] = df[['com_x', 'com_y']] * weight_com

    # pairwise euclidean dist
    dist = euclidean_distances(
        df.loc[df['time']==1][cols],
        df.loc[df['time']==2][cols]
    )
    return dist, ix_to_cell1, ix_to_cell2


def zero_pad(m, shape):
    """
    source: YeaZ
    Pads matrix with zeros to be of desired shape
    """
    out = np.zeros(shape)
    nrow, ncol = m.shape
    out[0:nrow, 0:ncol] = m
    return out


def make_square(m):
    """
    source: YeaZ
    Turns matrix into square matrix, as required by Munkres algorithm
    """
    r,c = m.shape
    if r==c:
        return m
    elif r>c:
        return zero_pad(m, (r,r))
    else:
        return zero_pad(m, (c,c))
