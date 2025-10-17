#!/usr/bin/env python3

"""Tools for the Power Spectral Density (PSD) estimation."""

import numbers
import typing
import math

import torch

from .window import ALPHA_MIN, ALPHA_MAX, alpha_to_band, att_to_alpha, band_to_alpha, kaiser


def _find_len(s_x: float, sigma_max: float, psd_max: float, freq_res: float) -> float:
    s_w_min, s_w_max = 3.0, 65536.0
    for _ in range(16):  # dichotomy, resol = 2**-n
        s_w = 0.5*(s_w_min + s_w_max)
        eta = sigma_max * math.sqrt(s_w/s_x) / psd_max
        att = max(20.0, -20.0*math.log10(eta))  # 20 is a minimal acceptable attenuation
        value = s_w*freq_res - 2.0 * alpha_to_band(att_to_alpha(att)) - 1.0
        if value <= 0:
            s_w_min = s_w
        else:
            s_w_max = s_w
    return s_w


def intercorr(
    signal_1: torch.Tensor,
    signal_2: torch.Tensor,
    win: torch.Tensor,
    stride: int,
    return_std: bool = False,
) -> torch.Tensor:
    """Compute the average intercorrelation of 2 signal using the Welch method.

    Parameters
    ----------
    signal_1, signal_2 : torch.Tensor
        The 2 broadcastable real temporal signals.
    win : torch.Tensor
        The 1d full window used, see :py:mod:`cutcutcodec.core.signal.window`.
    stride : int
        The gap between two sliding windows, stride >= 1.
    return_std : boolean, default=False
        If True, return the standard deviation of the psd estimation.

    Returns
    -------
    psd : torch.Tensor
        The average psd of each slices.
        Complex if intercorrelation and real if autocorrelation.
    std : torch.Tensor, if return_std == True
        The unbiaised real standard deviation
        between all psd in each segment for each frequency band.
    """
    # verifiactions
    assert isinstance(signal_1, torch.Tensor), signal_1.__class__.__name__
    assert isinstance(signal_2, torch.Tensor), signal_2.__class__.__name__
    assert isinstance(win, torch.Tensor), win.__class__.__name__
    assert win.ndim == 1, win.shape
    assert torch.broadcast_shapes(signal_1.shape, signal_2.shape)[-1] >= len(win), \
        "signal to short or window to tall"
    assert isinstance(stride, int), stride.__class__.__name__
    assert stride >= 1, stride
    assert isinstance(return_std, bool), return_std.__class__.__name__

    # psd for each slice
    is_autocorr = signal_1 is signal_2  # optimisation to avoid redondant operations
    signal_1 = signal_1.contiguous()  # required for as_strides
    signal_1 = signal_1.as_strided(  # shape (..., o, m), big ram usage!
        (
            *signal_1.shape[:-1],
            (signal_1.shape[-1] - len(win)) // stride + 1,  # number of slices
            len(win),
        ),
        (*signal_1.stride()[:-1], stride, 1),
    )
    signal_1 = signal_1 * win  # not inplace because blocs was not contiguous
    signal_1 = torch.fft.rfft(signal_1, norm="ortho", dim=-1)  # norm ortho for perceval theorem
    if not is_autocorr:
        signal_2 = signal_2.contiguous()  # required for as_strides
        signal_2 = signal_2.as_strided(  # shape (..., o, m), big ram usage!
            (
                *signal_2.shape[:-1],
                (signal_2.shape[-1] - len(win)) // stride + 1,  # number of slices
                len(win),
            ),
            (*signal_2.stride()[:-1], stride, 1),
        )
        signal_2 = signal_2 * win
        signal_2 = torch.fft.rfft(signal_2, norm="ortho", dim=-1)
        psd = signal_1 * signal_2.conj()
    else:
        psd = signal_1.real*signal_1.real + signal_1.imag*signal_1.imag

    # average all psd estimations
    win_power = (win**2).mean()
    if return_std:
        std, psd = torch.std_mean(psd, dim=-2, correction=1)  # shape (..., m)
        if not is_autocorr:
            std = abs(std)  # std real
        std /= win_power
        psd /= win_power
        return psd, std
    psd = torch.mean(psd, dim=-2)  # shape (..., m)
    psd /= win_power
    return psd


def welch(
    signal_1: torch.Tensor,
    signal_2: typing.Optional[torch.Tensor] = None,
    band: typing.Optional[numbers.Real] = None,
):
    r"""Estimate the power spectral density (PSD) ie intercorrelation with the Welch method.

    .. image:: /_static/media/welch.svg
        :alt: Welch method

    It is based on :py:func:`cutcutcodec.core.signal.psd.intercorr`.

    The slices are smoothed using a Kaiser window,
    calculated with :py:func:`cutcutcodec.core.signal.window.kaiser`.

    .. math::

        \begin{cases}
            \Delta f = \frac{1 + 2 \beta}{n_w} \\
        \end{cases}

    Parameters
    ----------
    signal_1 : torch.Tensor
        A real stationary time signal.
    signal_2 : default = signal_1
        Another real stationary time signal.
        If provided, the intercorrelation is calculated.
        The returned signal is therefore a complex signal.
        If omitted (default), the autocorrelation is calculated,
        and the returned signal is therefore real positive.
    band : float, optional
        The normlised frequency resolution \(\Delta f\) in
        :math:`\left(r \in \left]0, \frac{1}{2}\right[\right)`, for a sample rate of 1.
        Higher it is, better is the frequency resolution but the greater is the variance.

    Returns
    -------
    psd : torch.Tensor
        The correlation of signals, estimated using the Welch method.
        In the case of autocorrelation, this is an estimation of the power spectral density.

    Seealso
    -------
    * `scipy <https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.welch.html>`_.

    Examples
    --------
    >>> import math
    >>> import torch
    >>> import matplotlib.pyplot as plt
    >>> from cutcutcodec.core.signal.psd import welch

    Generate a test signal, a 2 Vrms sine wave at 1234 Hz, corrupted by
    0.001 V**2/Hz of white noise sampled at 10 kHz.

    >>> fs, N, amp, freq = 10e3, 1e5, 2*math.sqrt(2), 1234.0
    >>> noise_power = 0.001 * fs / 2
    >>> time = torch.arange(N) / fs
    >>> x = amp*torch.sin(2*torch.pi*freq*time)
    >>> x += torch.randn(time.shape) * math.sqrt(noise_power)

    Compute and plot the power spectral density.

    >>> psd = welch(x, band=2/1024)
    >>> f = torch.fft.rfftfreq(2*psd.shape[-1]-1, 1/fs)
    >>> _ = plt.semilogy(f, psd)
    >>> _ = plt.xlabel('frequency [Hz]')
    >>> _ = plt.ylabel('PSD [V**2/Hz]')
    >>> # plt.show()
    """
    assert isinstance(signal_1, torch.Tensor), signal_1.__class__.__name__
    assert signal_1.ndim >= 1
    if signal_2 is not None:
        assert isinstance(signal_2, torch.Tensor), signal_2.__class__.__name__
        assert signal_2.ndim >= 1
    else:
        signal_2 = signal_1

    # find limits
    beta_limits = (alpha_to_band(ALPHA_MIN), alpha_to_band(ALPHA_MAX))
    sig_size = torch.broadcast_shapes(signal_1.shape, signal_2.shape)[-1]
    nperseg_limits = (3, sig_size)
    band_limits = (
        (1 + 2*beta_limits[1]) / nperseg_limits[1],
        (1+2*beta_limits[0]) / nperseg_limits[0],
    )

    # verification
    if band is not None:
        assert isinstance(band, numbers.Real), band.__class__.__name__
        assert band_limits[0] <= band <= band_limits[1], (
            f"for a signal with {sig_size} sample, band={band} "
            f"is not in the valid range [{band_limits[0]}, {band_limits[1]}]"
        )
        bands = [float(band)]
    else:
        # to take 10 points is totaly arbitrary
        bands = torch.logspace(
            math.log10(band_limits[0]), math.log10(band_limits[1]), 10, dtype=torch.float64
        ).tolist()

    # compute all psd
    best_psd_std: tuple[torch.Tensor, float] = (None, math.inf)
    # to take 10 is totaly arbitrary
    # for beta in torch.linspace(beta_limits[0], beta_limits[1], 10, dtype=torch.float64).tolist():
    for beta in [0.5*(beta_limits[0] + beta_limits[1])]:
        for band_ in bands:
            nperseg = round((1 + 2*beta) / band_)
            if nperseg < nperseg_limits[0] or nperseg > nperseg_limits[1]:
                continue
            win = kaiser(nperseg, band_to_alpha(beta), dtype=signal_1.dtype).to(signal_1.device)
            # to take stride=len(win)//4 is totaly arbitrary
            psd, std = intercorr(signal_1, signal_2, win, max(1, len(win)//4), return_std=True)
            std = float(std.mean())
            if best_psd_std is None or best_psd_std[1] > std:
                best_psd_std = (psd, std)
    return best_psd_std[0]
