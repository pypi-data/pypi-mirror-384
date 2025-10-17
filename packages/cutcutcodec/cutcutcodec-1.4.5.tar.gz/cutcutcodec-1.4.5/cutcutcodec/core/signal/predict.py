#!/usr/bin/env python3

r"""Sequence prediction tools.

Terminology
-----------
* :math:`n_o` is the number of observations used by the predictor.
* :math:`o_i` are the past observation, with :math:`i \in [\![1,n_o]\!]`.
* :math:`\hat{o}_{n+1}` is the prediction of the next observation.
"""

import abc
import copy
import math
import numbers
import typing

import numpy as np


class Predictor(abc.ABC):
    """Basic structuring class for predicting a sequence of reels.

    Attributes
    ----------
    memory : int
        The number of memorized samples (readonly).
    obs : list[float]
        Past observations, more recent first (readonly).
    """

    def __init__(self, memory: numbers.Integral | float = math.inf):
        """Initialize the memory.

        Parameters
        ----------
        memory : int, default=inf
            The number of samples to be memorised.
        """
        assert isinstance(memory, numbers.Integral | float), memory.__class__.__name__
        if isinstance(memory, float):
            assert math.isinf(memory), memory
            self._memory: int | float = math.inf
            self._obs: list[float] = []
        else:
            assert memory >= 2, memory
            self._memory: int | float = int(memory)
            self._obs: list[float] = [0.0 for _ in range(self._memory)]

    @abc.abstractmethod
    def _update(self):
        """Update the internal step, to be ready for the next prediction."""
        raise NotImplementedError

    @property
    def memory(self) -> int | float:
        """Return the number of memorized samples."""
        return self._memory

    @property
    def obs(self) -> list[float]:
        """Return the past observations."""
        return self._obs.copy()  # copy to be user safe

    def predict(self, nbr: numbers.Integral = 1) -> list[float]:
        r"""Predict the next samples :math:`\hat{o}_{n+1}`.

        Parameters
        ----------
        nbr : int, default=1
            The number of sample to predict.

        Returns
        -------
        samples : list[float]
            The predicted sample, the last predicted in first position.
        """
        assert isinstance(nbr, numbers.Integral), nbr.__class__.__name__
        assert nbr >= 1, nbr

        predicted: list[float] = []
        self_ = self.__class__.__new__(self.__class__)
        self_.__dict__ = copy.deepcopy(self.__dict__)
        for _ in range(nbr-1):
            predicted.insert(0, self_.predict_next())
            self_.update(predicted[0])
        predicted.insert(0, self_.predict_next())
        return predicted

    @abc.abstractmethod
    def predict_next(self) -> float:
        r"""Predict the next sample :math:`\hat{o}_{n+1}`."""
        raise NotImplementedError

    def update(self, obs: numbers.Real | typing.Iterable[numbers.Real]):
        """Update the state of the predictor using the new samples.

        Parameters
        ----------
        obs : float or list[float]
            The new observation(s).
        """
        if isinstance(obs, numbers.Real):
            self.update([obs])
        else:
            assert hasattr(obs, "__iter__"), obs.__class__.__name__
            obs = list(obs)
            assert all(isinstance(o, numbers.Real) for o in obs), obs
            for i in range(min(self._memory, len(obs))-1, -1, -1):
                self._obs.insert(0, float(obs[i]))
            if not math.isinf(self._memory):
                del self._obs[self._memory:]
            self._update()


class LinearPredictor(Predictor):
    r"""Prediction by linear combination of observations.

    The prediction of the next observation is defined as follow:

    .. math::

        \hat{o}_{n+1} = \sum_{k=1}^{n_\alpha} \alpha_k o_{n+1-k}

    Notation:

    .. math::

        \begin{align}
            \begin{pmatrix} \hat{o}_n \\ \vdots \\ \hat{o}_{n-h} \end{pmatrix}
            &= \begin{pmatrix}
                o_{n-1} & \ldots & o_{n-1-n_\alpha} \\
                \vdots & \ddots & \vdots \\
                o_{n-1-h} & \ldots & o_{n-1-h-n_\alpha} \\
            \end{pmatrix}
            \begin{pmatrix} \alpha_1 \\ \vdots \\ \alpha_{n_\alpha} \end{pmatrix} \\
            \Leftrightarrow \boldsymbol{\hat{o}} &= \boldsymbol{X} \boldsymbol{\alpha}
        \end{align}

    The :math:`\alpha_k` scalars are founded to minimise the mse:

    .. math::

        \begin{align}
            &\boldsymbol{\alpha} = \underset{\boldsymbol{\alpha}}{\operatorname{argmin}}\left(
                \left\|
                    \begin{pmatrix} \hat{o}_n \\ \vdots \\ \hat{o}_{n-h} \end{pmatrix}
                    - \begin{pmatrix} o_n \\ \vdots \\ o_{n-h} \end{pmatrix}
                \right\|^2
            \right) \\
            \Leftrightarrow &\boldsymbol{\alpha}
            = \underset{\boldsymbol{\alpha}}{\operatorname{argmin}}\left(
                \left\| \boldsymbol{\hat{o}} - \boldsymbol{o} \right\|^2
            \right) \\
            \Leftrightarrow &\boldsymbol{\alpha}
            = \underset{\boldsymbol{\alpha}}{\operatorname{argmin}}\left(
                \left( \boldsymbol{X} \boldsymbol{\alpha} - \boldsymbol{o} \right)^\intercal
                \left( \boldsymbol{X} \boldsymbol{\alpha} - \boldsymbol{o} \right)
            \right) \\
            \Leftrightarrow &\frac{
                \partial \left(
                    \left( \boldsymbol{X} \boldsymbol{\alpha} - \boldsymbol{o} \right)^\intercal
                    \left( \boldsymbol{X} \boldsymbol{\alpha} - \boldsymbol{o} \right)
                \right)
            }{\partial \boldsymbol{\alpha}} = \boldsymbol{0} \\
            \Leftrightarrow &\boldsymbol{\alpha}
            = \left( \boldsymbol{X}^\intercal \boldsymbol{X} \right)^{-1}
            \boldsymbol{X}^\intercal \boldsymbol{o} \\
        \end{align}

    Examples
    --------
    >>> from cutcutcodec.core.signal.predict import LinearPredictor
    >>> # simple case
    >>> predictor = LinearPredictor(memory=4)
    >>> predictor.update([4.0, 3.0, 2.0, 1.0])  # arithmetic sequence (more recent first)
    >>> round(predictor.predict_next(), 6)
    5.0
    >>> # complicated case
    >>> predictor = LinearPredictor(memory=6)
    >>> predictor.update([4.0, 2.0, 3.0, 1.0, 2.0, 0.0])  # less trivial sequence
    >>> [round(p, 6) for p in predictor.predict(4)]
    [6.0, 4.0, 5.0, 3.0]
    >>>
    """

    def __init__(self, *args, n_alpha: typing.Optional[numbers.Integral] = None, **kwargs):
        r"""Initialise the predictor.

        Parameters
        ----------
        *args, **kwargs
            Transmitted to :py:class:`Predictor`
        n_alpha : int, optional
            The number of internal coefficients :math:`n_\alpha`.
            By default :math:`n_\alpha = \lfloor \frac{n_{obs}+1}{2} \rfloor`.
        """
        super().__init__(*args, **kwargs)
        if n_alpha is None:
            if math.isinf(self._memory):
                n_alpha = 3  # default value
            else:
                n_alpha = (self._memory + 1) // 2
        else:
            assert isinstance(n_alpha, numbers.Integral), n_alpha.__class__.__name__
            assert n_alpha >= 1, n_alpha
            if not math.isinf(self._memory):
                assert n_alpha <= (self._memory + 1) // 2, (
                    f"with an history of size {self._memory}, "
                    f"alpha has to be <= {(self._memory + 1) // 2}"
                )
        self._alpha = [1.0] + [0.0 for _ in range(n_alpha-1)]

    def _update(self):
        """Recompute the best alpha."""
        for n_alpha in range(len(self._alpha), 0, -1):
            # first check
            if (h_size := len(self._obs) - n_alpha) <= 0:
                if n_alpha == 1:
                    raise RuntimeError("please provide more observations")
                continue

            # creation of the vector and matrix
            o_vec = np.asarray(self._obs[:h_size], dtype=np.float64)[:, None]
            x_mat = np.asarray(
                [self._obs[i+1:i+1+n_alpha] for i in range(h_size)],
                dtype=np.float64,
            )

            # try to resolve
            xtx_inv = np.linalg.linalg.pinv(x_mat.mT @ x_mat, hermitian=True)

            # set result
            alpha = xtx_inv @ x_mat.mT @ o_vec
            alpha = alpha[:, 0].tolist()
            alpha.extend([0.0 for _ in range(len(self._alpha) - n_alpha)])
            self._alpha = alpha
            break

    def predict_next(self) -> float:
        r"""Compute :math:`\sum_{k=1}^{n_\alpha} \alpha_k o_{n+1-k}`."""
        return sum(a*o for a, o in zip(self._alpha, self._obs))
