#!/usr/bin/env python3

"""Window a signal to control gibbs effects.

The optimal dpss window is implemented here, but it is not very stable computationally.
All functions are based on the Kaiser window,
which is a good compromise between stability and optimality.
"""

import logging
import math
import numbers

import torch
import tqdm

ALPHA_MIN = 1e-3
ALPHA_MAX = 12.0


def _regression(x_data: torch.Tensor, y_data: torch.Tensor) -> torch.Tensor:
    """Fit the model y = a*x + b + c*tanh(d*x)."""
    # initialisation
    cst = torch.tensor(
        # [8.4e-2, 2.5e1, 1.3e1, -1.8e1, 9.9e-1],  # alpha_to_att
        [0.0e0, 9.8e-1, 8.1e-1, -5.6e-1, 1.6e0],  # alpha_to_band
        dtype=torch.float64,
        requires_grad=True,
    )
    # cst = torch.tensor(, dtype=torch.float64, requires_grad=True)
    optim = torch.optim.SGD([cst], lr=1e-4)
    prec_loss = torch.inf
    # gradient decrease fit
    for i in range(10_000_000):
        y_pred = (
            cst[0] * x_data * x_data + cst[1] * x_data + cst[2]
            + cst[3] * torch.tanh(cst[4]*x_data)
        )
        loss = torch.mean((y_data - y_pred)**2)
        optim.zero_grad()
        loss.backward()
        optim.step()
        if i % 100 == 0:
            print(f"{loss:.4g}: {cst.tolist()}")
        if loss >= prec_loss:
            break
        prec_loss = loss
    return cst.tolist()


def alpha_to_att(alpha: numbers.Real) -> float:
    r"""Empirical estimation based on regression.

    The fitted model is :math:`\eta = a*\alpha^2 + b*\alpha + c + d*\tanh(e*\alpha)`.

    This function is strictly increasing.

    Bijection of :py:func:`att_to_alpha`.

    Examples
    --------
    >>> import torch
    >>> from cutcutcodec.core.signal.window import alpha_to_att, find_win_law
    >>> alphas, atts, _ = find_win_law()
    >>> pred = [alpha_to_att(a) for a in alphas.tolist()]
    >>> # import matplotlib.pyplot as plt
    >>> # _ = plt.plot(alphas.numpy(force=True), atts.numpy(force=True))
    >>> # _ = plt.plot(alphas.numpy(force=True), pred)
    >>> # plt.show()
    >>>
    """
    assert isinstance(alpha, numbers.Real), alpha.__class__.__name__
    if not ALPHA_MIN <= alpha <= ALPHA_MAX:
        logging.warning("alpha=%f is not in the valid range[%f, %f]", alpha, ALPHA_MIN, ALPHA_MAX)
    # mse = 0.1760
    cst_a = 0.0843565615460276
    cst_b = 24.6451250759085
    cst_c = 13.006908816901474
    cst_d = -18.03549549878431
    cst_e = 0.9853208856137512
    return cst_a*alpha*alpha + cst_b*alpha + cst_c + cst_d*math.tanh(cst_e*alpha)


def alpha_to_band(alpha: numbers.Real) -> float:
    r"""Empirical estimation based on regression.

    The fitted model is :math:`band = a*\alpha^2 + b*\alpha + c + d*tanh(e*\alpha)`.

    This function is strictly increasing.

    Bijection of :py:func:`band_to_alpha`.

    Examples
    --------
    >>> import torch
    >>> from cutcutcodec.core.signal.window import alpha_to_band, find_win_law
    >>> alphas, _, bands = find_win_law()
    >>> pred = [alpha_to_band(a) for a in alphas.tolist()]
    >>> # import matplotlib.pyplot as plt
    >>> # _ = plt.plot(alphas.numpy(force=True), bands.numpy(force=True))
    >>> # _ = plt.plot(alphas.numpy(force=True), pred)
    >>> # plt.show()
    >>>
    """
    assert isinstance(alpha, numbers.Real), alpha.__class__.__name__
    if not ALPHA_MIN <= alpha <= ALPHA_MAX:
        logging.warning("alpha=%f is not in the valid range[%f, %f]", alpha, ALPHA_MIN, ALPHA_MAX)
    # mse 0.0008983
    cst_a = 0.0002108558177947993
    cst_b = 0.977822030619533
    cst_c = 0.8107202793747393
    cst_d = -0.5605637717096734
    cst_e = 1.5997332801630457
    return cst_a*alpha*alpha + cst_b*alpha + cst_c + cst_d*math.tanh(cst_e*alpha)


def att_to_alpha(att: numbers.Real) -> float:
    """Inverse of the empirical estimation based on regression.

    Bijection of :py:func:`alpha_to_att`.

    As there is no closed form for this function, it is approximated using the tangent method.

    Examples
    --------
    >>> from cutcutcodec.core.signal.window import alpha_to_att, att_to_alpha
    >>> round(alpha_to_att(att_to_alpha(20.0)), 6)
    20.0
    >>> round(alpha_to_att(att_to_alpha(40.0)), 6)
    40.0
    >>> round(alpha_to_att(att_to_alpha(80.0)), 6)
    80.0
    >>> round(alpha_to_att(att_to_alpha(120.0)), 6)
    120.0
    >>> round(alpha_to_att(att_to_alpha(160.0)), 6)
    160.0
    >>>
    """
    assert isinstance(att, numbers.Real), att.__class__.__name__
    alpha_min, alpha_max = ALPHA_MIN, ALPHA_MAX
    att_min, att_max = alpha_to_att(alpha_min), alpha_to_att(alpha_max)
    assert att_min <= att <= att_max, f"att={att} is not in the valid range[{att_min}, {att_max}]"
    while alpha_max - alpha_min > 1e-10:
        alpha = alpha_min + (att - att_min) * (alpha_max - alpha_min) / (att_max - att_min)
        new_att = alpha_to_att(alpha)
        if new_att < att:
            alpha_min, att_min = alpha, new_att
        else:
            alpha_max, att_max = alpha, new_att
    return 0.5 * (alpha_min + alpha_max)


def band_to_alpha(band: numbers.Real) -> float:
    """Inverse of the empirical estimation based on regression.

    Bijection of :py:func:`alpha_to_band`.

    As there is no closed form for this function, it is approximated using the tangent method.

    Examples
    --------
    >>> from cutcutcodec.core.signal.window import alpha_to_band, band_to_alpha
    >>> round(alpha_to_band(band_to_alpha(0.9)), 6)
    0.9
    >>> round(alpha_to_band(band_to_alpha(1.8)), 6)
    1.8
    >>> round(alpha_to_band(band_to_alpha(3.4)), 6)
    3.4
    >>> round(alpha_to_band(band_to_alpha(4.9)), 6)
    4.9
    >>> round(alpha_to_band(band_to_alpha(6.4)), 6)
    6.4
    >>>
    """
    assert isinstance(band, numbers.Real), band.__class__.__name__
    alpha_min, alpha_max = ALPHA_MIN, ALPHA_MAX
    band_min, band_max = alpha_to_band(alpha_min), alpha_to_band(alpha_max)
    assert band_min <= band <= band_max, \
        f"band={band} is not in the valid range[{band_min}, {band_max}]"
    while alpha_max - alpha_min > 1e-10:
        alpha = alpha_min + (band - band_min) * (alpha_max - alpha_min) / (band_max - band_min)
        new_band = alpha_to_band(alpha)
        if new_band < band:
            alpha_min, band_min = alpha, new_band
        else:
            alpha_max, band_max = alpha, new_band
    return 0.5 * (alpha_min + alpha_max)


def dpss(nb_samples: numbers.Integral, alpha: numbers.Real, dtype=torch.float64) -> torch.Tensor:
    """Compute the Discrete Prolate Spheroidal Sequences (DPSS).

    It is similar to the scipy function ``scipy.signal.windows.dpss``.

    .. image:: /_static/media/dpss.svg
        :alt: DPSS windows

    Parameters
    ----------
    nb_samples : int
        The window size, it has to be >= 3.
    alpha : float
        Standardized half bandwidth.
    dtype : torch.dtype, default=float64
        The data type of the window samples: torch.float64 or torch.float32.

    Returns
    -------
    window : torch.Tensor
        The 1d symetric window, normalized with the maximum value at 1.

    Examples
    --------
    >>> import torch
    >>> from cutcutcodec.core.signal.window import dpss
    >>> dpss(1024, 2.0)
    tensor([0.0158, 0.0163, 0.0169,  ..., 0.0169, 0.0163, 0.0158],
           dtype=torch.float64)
    >>>
    >>> # comparison with kaiser
    >>> alpha, nbr = 5.0, 129
    >>> win_dpss = dpss(nbr, alpha)
    >>> win_kaiser = torch.kaiser_window(
    ...     nbr, periodic=False, beta=alpha*torch.pi, dtype=torch.float64
    ... )
    >>> gain_dpss = 20*torch.log10(abs(torch.fft.rfft(win_dpss, 100000)))
    >>> gain_dpss -= torch.max(gain_dpss)
    >>> gain_kaiser = 20*torch.log10(abs(torch.fft.rfft(win_kaiser, 100000)))
    >>> gain_kaiser -= torch.max(gain_kaiser)
    >>>
    >>> # import matplotlib.pyplot as plt
    >>> # fig, (ax1, ax2) = plt.subplots(2)
    >>> # _ = ax1.plot(win_dpss, label="dpss")
    >>> # _ = ax1.plot(win_kaiser, label="kaiser")
    >>> # _ = ax1.legend()
    >>> # _ = ax2.plot(torch.linspace(0, 0.5, 50001), gain_dpss, label="dpss")
    >>> # _ = ax2.plot(torch.linspace(0, 0.5, 50001), gain_kaiser, label="kaiser")
    >>> # _ = ax2.axvline(x=alpha/nbr)
    >>> # _ = ax2.legend()
    >>> # plt.show()
    >>>
    """
    assert isinstance(nb_samples, numbers.Integral), nb_samples.__class__.__name__
    assert nb_samples >= 3, nb_samples
    assert isinstance(alpha, numbers.Real), alpha.__class__.__name__
    assert alpha > 0, alpha
    assert dtype in {torch.float32, torch.float64}, dtype

    # Based on scipy: https://github.com/scipy/scipy/blob/v1.15.0/scipy/signal/windows/_windows.py
    # The window is the eigenvector affiliated with the largest eigenvalue
    # of the symmetrical tridiagonal matrix defined below.
    n_idx = torch.arange(nb_samples, dtype=dtype)
    diag = (0.5*(nb_samples - 2*n_idx - 1))**2 * math.cos(2 * math.pi * float(alpha) / nb_samples)
    off_diag = 0.5 * n_idx[1:] * (nb_samples - n_idx[1:])

    # Find the eigen vector.
    # The function `window = torch.linalg.eigh(matrix)[1][:, nb_samples-1]` is not stable.
    # As the kaiser window is an approximation of the dpss window, it's a very good starting point.
    win = kaiser(nb_samples, alpha)
    if nb_samples**2 * diag.dtype.itemsize > 104857600:  # if more than 100 Mio of ram is required
        return win  # we only keep an approximation
    # Create the matrix.
    matrix = torch.diag(diag)
    matrix[range(0, nb_samples-1), range(1, nb_samples)] = off_diag
    matrix[range(1, nb_samples), range(0, nb_samples-1)] = off_diag
    _, win = torch.lobpcg(matrix, X=win[:, None], largest=True, niter=-1)
    win = win[:, 0]

    # normalisation
    win /= float(win[nb_samples//2])  # the extremum is on the middle

    return win


def find_win_law(
    nb_samples: numbers.Integral = 129,
    nb_alphas: numbers.Integral = 1000,
    alpha_min: numbers.Real = ALPHA_MIN,
    alpha_max: numbers.Real = 15.0,
    win: str = "kaiser"
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """For each beta parameter, associate the frequency properties.

    Parameters
    ----------
    nb_samples : int, default=129
        The window size, it has to be >= 3.
    nb_alphas : int, default=1000
        The number of alpha points.
    alpha_min : float, default=ALPHA_MIN
        The minimal inclusive alpha value.
    alpha_max : float, default=15.0
        The maximal inclusive alpha value.
    win : str, default="kaiser"
        The windows type, "kaiser" or "dpss"

    Returns
    -------
    alphas : torch.Tensor
        The apha values.
    atts : torch.Tensor
        The real positive attenuation of the secondaries lobs in dB.
    bands : torch.Tensor
        The normalised size of the main lob.

    Examples
    --------
    >>> import torch
    >>> from cutcutcodec.core.signal.window import find_win_law
    >>> alphas, atts, bands = find_win_law()
    >>>
    >>> # import matplotlib.pyplot as plt
    >>> # _ = plt.plot(alphas.numpy(force=True), atts.numpy(force=True), label="attenuation")
    >>> # _ = plt.plot(alphas.numpy(force=True), bands.numpy(force=True), label="band")
    >>> # _ = plt.legend()
    >>> # plt.show()
    >>>
    """
    assert isinstance(nb_samples, numbers.Integral), nb_samples.__class__.__name__
    assert nb_samples >= 3, nb_samples
    assert isinstance(nb_alphas, numbers.Integral), nb_alphas.__class__.__name__
    assert nb_alphas >= 1, nb_alphas
    assert isinstance(win, str), win.__class__.__name__
    assert win in {"dpss", "kaiser"}, win
    assert isinstance(alpha_min, numbers.Real), alpha_min.__class__.__name__
    assert isinstance(alpha_max, numbers.Real), alpha_max.__class__.__name__
    assert 0.0 < alpha_min <= alpha_max, (alpha_min, alpha_max)

    alphas = torch.logspace(
        math.log10(alpha_min), math.log10(alpha_max), nb_alphas, base=10.0
    ).tolist()
    atts = []  # attenuation in db
    bands = []  # band * nb_samples

    for alpha in tqdm.tqdm(alphas):
        win_values = {"dpss": dpss, "kaiser": kaiser}[win](nb_samples, alpha)
        gain = 20*torch.log10(abs(torch.fft.rfft(win_values, 200*nb_samples)))
        gain -= gain.max()
        idx = torch.argmax((gain[1:] > gain[:-1]).view(torch.uint8))
        att = -torch.max(gain[idx:])  # positive value
        band = torch.argmin(abs(gain[:idx] + att)) / 200
        atts.append(float(att))
        bands.append(float(band))

        # import matplotlib.pyplot as plt
        # plt.title(f"for alpha={alpha:.2g}")
        # plt.xlabel("freq")
        # plt.ylabel("gain")
        # plt.plot(torch.linspace(0, 0.5, len(gain)), gain)
        # plt.axhline(y=-att)
        # plt.axvline(x=band/nb_samples)
        # plt.show()

    return torch.asarray(alphas), torch.asarray(atts), torch.asarray(bands)


def kaiser(nb_samples: numbers.Integral, alpha: numbers.Real, dtype=torch.float64) -> torch.Tensor:
    """Compute the Kaiser–Bessel window.

    It is an approximation of :py:func:`cutcutcodec.core.signal.window.dpss`.

    .. image:: /_static/media/kaiser.svg
        :alt: Kaiser windows

    Parameters
    ----------
    nb_samples : int
        The window size, it has to be >= 3.
    alpha : float
        Standardized half bandwidth.
    dtype : torch.dtype, default=float64
        The data type of the window samples: torch.float64 or torch.float32.

    Returns
    -------
    window : torch.Tensor
        The 1d symetric window, normalized with the maximum value at 1.
    """
    assert isinstance(nb_samples, numbers.Integral), nb_samples.__class__.__name__
    assert nb_samples >= 3, nb_samples
    assert isinstance(alpha, numbers.Real), alpha.__class__.__name__
    assert alpha > 0, alpha
    assert dtype in {torch.float32, torch.float64}, dtype

    return torch.kaiser_window(nb_samples, beta=math.pi*alpha, dtype=dtype, periodic=False)
