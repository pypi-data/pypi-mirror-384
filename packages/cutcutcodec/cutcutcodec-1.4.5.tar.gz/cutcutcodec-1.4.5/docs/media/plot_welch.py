#!/usr/bin/env python3

"""Plot an illustration of the Welch method."""

import matplotlib.pyplot as plt
import torch

from cutcutcodec.core.signal.psd import intercorr
from cutcutcodec.core.signal.window import kaiser
from style import COLORS

DURATION = 5.0  # in s
SAMPLE_RATE = 8000  # in Hz
NBR = 1025  # nbr of samples per slice


def main():
    # figure context
    fig = plt.figure(layout="constrained", figsize=(8, 8))
    fig.suptitle("Estimation of PSD with the Welch method")
    fig_signal, fig_slices_t, fig_slices_f, fig_psd = fig.subfigures(nrows=4, ncols=1)

    # temporal signal
    time = torch.arange(0.0, DURATION, 1.0/SAMPLE_RATE)  # time sample in (s)
    tot = len(time)
    signal = torch.randn(tot) + torch.sin(2*torch.pi*440*time)

    fig_signal.supylabel("Magnitude")
    fig_signal.supxlabel("Time (s)")
    axe = fig_signal.subplots()
    axe.plot(time, signal, color=COLORS[0], label="$n + \\sin(2 \\pi 440 t)$")
    for i, pos in enumerate(range(tot//4, tot, tot//4)):
        axe.plot(time[pos-NBR//2:pos+NBR//2+1], signal[pos-NBR//2:pos+NBR//2+1], color=COLORS[i+1])
    axe.legend()

    # temporal slices
    fig_slices_t.supylabel("Magnitude")
    fig_slices_t.supxlabel("Time (s)")
    axes_t = fig_slices_t.subplots(ncols=3, sharey=True)

    fig_slices_f.supylabel("$\\Gamma$")
    fig_slices_f.supxlabel("Frequency (Hz)")
    axes_f = fig_slices_f.subplots(ncols=3, sharey=True)

    win = kaiser(NBR, alpha=2.0)
    win_power = (win**2).mean()

    for i, pos in enumerate(range(tot//4, tot, tot//4)):
        time_slice = time[pos-NBR//2:pos+NBR//2+1]
        signal_slice = signal[pos-NBR//2:pos+NBR//2+1]
        signal_slice = signal_slice * win
        axes_t[i].plot(time_slice, signal_slice, color=COLORS[i+1], label="slice * window")
        axes_t[i].legend()

        psd = abs(torch.fft.rfft(signal_slice, norm="ortho", dim=-1))**2
        freq = torch.fft.rfftfreq(2*psd.shape[-1]-1, 1.0/SAMPLE_RATE)
        axes_f[i].plot(freq, psd, color=COLORS[i+1], label="local psd")
        axes_f[i].set_yscale("log", base=10)
        axes_f[i].legend()

    # full intercorr
    psd = intercorr(signal, signal, win, stride=NBR//4)
    freq = torch.fft.rfftfreq(2*psd.shape[-1]-1, 1.0/SAMPLE_RATE)

    fig_psd.supylabel("$\\Gamma$")
    fig_psd.supxlabel("Frequency (Hz)")
    axe = fig_psd.subplots()
    axe.plot(freq, psd, color=COLORS[0], label="average psd")
    axe.legend()
    axe.set_yscale("log", base=10)

    # save
    plt.savefig("welch.svg", format="svg")
    plt.show()


if __name__ == "__main__":
    main()
