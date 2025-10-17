#!/usr/bin/env python3

"""Plot some examples of the dpss window."""

import matplotlib.pyplot as plt
import torch

from cutcutcodec.core.signal.window import find_win_law, kaiser
from style import COLORS


NBR = 129


def main():
    # figure context
    fig = plt.figure(layout="constrained", figsize=(12, 6))
    axe_t, axe_f = fig.subplots(nrows=1, ncols=2)
    axe_t.set_title("Kaiser window in temporal domain")
    axe_t.set_xlabel("Time (s)")
    axe_t.set_ylabel("Magnitude")
    axe_f.set_title("Kaiser window in spectral domain")
    axe_f.set_xlabel("Normalized frequency")
    axe_f.set_ylabel("Gain (dB)")

    # fill plots
    for i, alpha in enumerate((1.0, 2.2, 4.7, 10.0)):
        # legend
        axe_t.scatter([], [], label=f"$\\alpha = {alpha}$", color=COLORS[i])

        # get windows
        win = kaiser(NBR, alpha)
        gain = 20*torch.log10(abs(torch.fft.rfft(win, 100000)))
        gain -= torch.max(gain)

        # plot
        axe_t.plot(
            torch.linspace(-1, 1, len(win)), win,
            color=COLORS[i],
        )
        axe_f.plot(
            torch.linspace(0, 0.5, 50001), gain,
            color=COLORS[i],
        )

    # add regression
    alphas, atts, bands = find_win_law(NBR, win="kaiser")
    axe_f.plot(bands/NBR, -atts, color="black", label="attenuation = $f(\\alpha)$")
    axe_f.legend()
    axe_f.set_xlim(0.0, 2.0*bands.max()/NBR)

    # legend
    lines, labels = axe_t.get_legend_handles_labels()
    fig.legend(lines, labels, loc="outside upper center", ncols=4)

    # save
    plt.savefig("kaiser.svg", format="svg")
    plt.show()


if __name__ == "__main__":
    main()
