from numpy import *
from itertools import izip

from .data import RawSparseData

__all__ = ['load_fet_fmask_to_raw']


def load_fet_fmask_to_raw(fname, shank):
    fet_fname = fname+'.fet.'+str(shank)
    fmask_fname = fname+'.fmask.'+str(shank)
    # read files
    fet_file = open(fet_fname, 'r')
    fmask_file = open(fmask_fname, 'r')
    # read first line of fmask file
    num_features = int(fmask_file.readline())
    # Stage 1: read min/max of fet values for normalisation
    # and count total number of unmasked features
    fet_file.readline() # skip first line (num channels)
    # we normalise channel-by-channel
    vmin = ones(num_features)*inf
    vmax = ones(num_features)*-inf
    total_unmasked_features = 0
    num_spikes = 0
    for fetline, fmaskline in izip(fet_file, fmask_file):
        vals = fromstring(fetline, dtype=float, sep=' ')
        fmaskvals = fromstring(fmaskline, dtype=float, sep=' ')
        inds, = (fmaskvals>0).nonzero()
        total_unmasked_features += len(inds)
        vmin = minimum(vals, vmin)
        vmax = maximum(vals, vmax)
        num_spikes += 1
    # Stage 2: read data line by line, normalising
    fet_file.close()
    fet_file = open(fet_fname, 'r')
    fet_file.readline()
    fmask_file.close()
    fmask_file = open(fmask_fname, 'r')
    fmask_file.readline()
    vdiff = vmax-vmin
    vdiff[vdiff==0] = 1
    fetsum = zeros(num_features)
    fet2sum = zeros(num_features)
    nsum = zeros(num_features)
    all_features = zeros(total_unmasked_features)
    all_fmasks = zeros(total_unmasked_features)
    all_unmasked = zeros(total_unmasked_features, dtype=int)
    offsets = zeros(num_spikes+1, dtype=int)
    curoff = 0
    for i, (fetline, fmaskline) in enumerate(izip(fet_file, fmask_file)):
        fetvals = (fromstring(fetline, dtype=float, sep=' ')-vmin)/vdiff
        fmaskvals = fromstring(fmaskline, dtype=float, sep=' ')
        inds, = (fmaskvals>0).nonzero()
        all_features[curoff:curoff+len(inds)] = fetvals[inds]
        all_fmasks[curoff:curoff+len(inds)] = fmaskvals[inds]
        all_unmasked[curoff:curoff+len(inds)] = inds
        offsets[i] = curoff
        curoff += len(inds)
        fetsum += fetvals
        fet2sum += fetvals**2
        nsum += 1        
    offsets[-1] = curoff
    
    nsum[nsum==0] = 1
    noise_mean = fetsum/nsum
    noise_variance = fet2sum/nsum-noise_mean**2
    
    return RawSparseData(noise_mean, noise_variance, all_features, all_fmasks, all_unmasked, offsets)
