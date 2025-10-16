# parallel_functions.py

import numpy as np
from numpy.linalg import norm, eigh
from numpy.fft import fft, ifft


def zscore(a, axis=0, ddof=0):
    a = np.asanyarray(a)
    mns = a.mean(axis=axis)
    sstd = a.std(axis=axis, ddof=ddof)

    if axis and mns.ndim < a.ndim:
        res = (a - np.expand_dims(mns, axis=axis)) / np.expand_dims(sstd, axis=axis)
    else:
        res = (a - mns) / sstd

    return np.nan_to_num(res)


def roll_zeropad(a, shift, axis=None):
    a = np.asanyarray(a)
    if shift == 0:
        return a

    if axis is None:
        n = a.size
        reshape = True
    else:
        n = a.shape[axis]
        reshape = False

    if np.abs(shift) > n:
        res = np.zeros_like(a)
    elif shift < 0:
        shift += n
        zeros = np.zeros_like(a.take(np.arange(n - shift), axis))
        res = np.concatenate((a.take(np.arange(n - shift, n), axis), zeros), axis)
    else:
        zeros = np.zeros_like(a.take(np.arange(n - shift, n), axis))
        res = np.concatenate((zeros, a.take(np.arange(n - shift), axis)), axis)

    if reshape:
        return res.reshape(a.shape)
    else:
        return res


def _ncc_c_3dim(data):
    x, y = data[0], data[1]
    den = norm(x, axis=(0, 1)) * norm(y, axis=(0, 1))

    if den < 1e-9:
        den = np.inf

    x_len = x.shape[0]
    fft_size = 1 << (2 * x_len - 1).bit_length()

    cc = ifft(fft(x, fft_size, axis=0) * np.conj(fft(y, fft_size, axis=0)), axis=0)
    cc = np.concatenate((cc[-(x_len - 1) :], cc[:x_len]), axis=0)

    return np.real(cc).sum(axis=-1) / den


def _sbd(x, y):
    ncc = _ncc_c_3dim([x, y])
    idx = np.argmax(ncc)
    yshift = roll_zeropad(y, (idx + 1) - max(len(x), len(y)))

    return yshift


def collect_shift(data):
    x, cur_center = data[0], data[1]
    if np.all(cur_center == 0):
        return x
    else:
        return _sbd(cur_center, x)


def _extract_shape(idx, x, j, cur_center):
    _a = []
    for i in range(len(idx)):
        if idx[i] == j:
            _a.append(collect_shift([x[i], cur_center]))

    a = np.array(_a)
    if len(a) == 0:
        indices = np.random.choice(x.shape[0], 1)
        return np.squeeze(x[indices].copy())

    columns = a.shape[1]
    y = zscore(a, axis=1, ddof=1)

    s = np.dot(y[:, :, 0].transpose(), y[:, :, 0])
    p = np.empty((columns, columns))
    p.fill(1.0 / columns)
    p = np.eye(columns) - p
    m = np.dot(np.dot(p, s), p)

    _, vec = eigh(m)
    centroid = vec[:, -1]

    finddistance1 = np.sum(
        np.linalg.norm(a - centroid.reshape((x.shape[1], 1)), axis=(1, 2))
    )
    finddistance2 = np.sum(
        np.linalg.norm(a + centroid.reshape((x.shape[1], 1)), axis=(1, 2))
    )

    if finddistance1 >= finddistance2:
        centroid *= -1

    return zscore(centroid, ddof=1)
