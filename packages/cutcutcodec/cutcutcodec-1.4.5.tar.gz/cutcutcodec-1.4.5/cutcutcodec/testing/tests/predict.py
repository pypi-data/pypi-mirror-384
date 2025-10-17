#!/usr/bin/env python3

"""Check is the frame predictor is efficient enought."""


import pytest

from cutcutcodec.core.signal.predict import LinearPredictor


def check(sequence: list[float], memory: int):
    """Perform the prediction and verify it matches."""
    for sequence_ in (sequence[::1], sequence[::-1]):  # test in both directions
        predictor = LinearPredictor(memory=memory)
        for _ in range(memory):
            predictor.update(sequence_.pop(0))
        for item in sequence_:
            assert predictor.predict_next() == pytest.approx(item, abs=1e-9, rel=1e-9)
            predictor.update(item)


def test_afine():
    """Ensure it is able to predict an arithmetique suite."""
    sequence = [10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0]
    check(sequence, 4)
    check(sequence, 5)
    check(sequence, 6)
    check(sequence, 7)
    check(sequence, 8)
    check(sequence, 9)


def test_constant_one():
    """Ensure it is able to predict a constant suite."""
    sequence = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
    check(sequence, 2)
    check(sequence, 3)
    check(sequence, 4)
    check(sequence, 5)
    check(sequence, 6)
    check(sequence, 7)
    check(sequence, 8)
    check(sequence, 9)


def test_constant_zero():
    """Ensure it is able to predict a constant suite."""
    sequence = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    check(sequence, 2)
    check(sequence, 3)
    check(sequence, 4)
    check(sequence, 5)
    check(sequence, 6)
    check(sequence, 7)
    check(sequence, 8)
    check(sequence, 9)


def test_conv2_stride1_step1():
    """Convoltion like suite."""
    conv, stride, step = 2, 1, 1
    sequence = [float(step*a + stride*s) for a in range(5) for s in range(conv)]
    for memory in range(2*conv+2, 4*conv):
        check(sequence, memory)


def test_conv2_stride1_step2():
    """Convoltion like suite."""
    conv, stride, step = 2, 1, 2
    sequence = [float(step*a + stride*s) for a in range(5) for s in range(conv)]
    for memory in range(2*conv+2, 4*conv):
        check(sequence, memory)


def test_conv2_stride1_step3():
    """Convoltion like suite."""
    conv, stride, step = 2, 1, 3
    sequence = [float(step*a + stride*s) for a in range(5) for s in range(conv)]
    for memory in range(2*conv+2, 4*conv):
        check(sequence, memory)


def test_conv2_stride2_step1():
    """Convoltion like suite."""
    conv, stride, step = 2, 2, 1
    sequence = [float(step*a + stride*s) for a in range(5) for s in range(conv)]
    for memory in range(2*conv+2, 4*conv):
        check(sequence, memory)


def test_conv2_stride3_step1():
    """Convoltion like suite."""
    conv, stride, step = 2, 3, 1
    sequence = [float(step*a + stride*s) for a in range(5) for s in range(conv)]
    for memory in range(2*conv+2, 4*conv):
        check(sequence, memory)


def test_conv2_stride3_step2():
    """Convoltion like suite."""
    conv, stride, step = 2, 3, 2
    sequence = [float(step*a + stride*s) for a in range(5) for s in range(conv)]
    for memory in range(2*conv+2, 4*conv):
        check(sequence, memory)


def test_conv2_stride3_step3():
    """Convoltion like suite."""
    conv, stride, step = 2, 3, 3
    sequence = [float(step*a + stride*s) for a in range(5) for s in range(conv)]
    for memory in range(2*conv+2, 4*conv):
        check(sequence, memory)


def test_conv3_stride1_step1():
    """Convoltion like suite."""
    conv, stride, step = 3, 1, 1
    sequence = [float(step*a + stride*s) for a in range(5) for s in range(conv)]
    for memory in range(2*conv+2, 4*conv):
        check(sequence, memory)


def test_conv3_stride1_step2():
    """Convoltion like suite."""
    conv, stride, step = 3, 1, 2
    sequence = [float(step*a + stride*s) for a in range(5) for s in range(conv)]
    for memory in range(2*conv+2, 4*conv):
        check(sequence, memory)


def test_conv3_stride1_step3():
    """Convoltion like suite."""
    conv, stride, step = 3, 1, 3
    sequence = [float(step*a + stride*s) for a in range(5) for s in range(conv)]
    for memory in range(2*conv+2, 4*conv):
        check(sequence, memory)


def test_conv3_stride2_step1():
    """Convoltion like suite."""
    conv, stride, step = 3, 2, 1
    sequence = [float(step*a + stride*s) for a in range(5) for s in range(conv)]
    for memory in range(2*conv+2, 4*conv):
        check(sequence, memory)


def test_conv3_stride2_step2():
    """Convoltion like suite."""
    conv, stride, step = 3, 2, 2
    sequence = [float(step*a + stride*s) for a in range(5) for s in range(conv)]
    for memory in range(2*conv+2, 4*conv):
        check(sequence, memory)


def test_conv3_stride2_step3():
    """Convoltion like suite."""
    conv, stride, step = 3, 2, 3
    sequence = [float(step*a + stride*s) for a in range(5) for s in range(conv)]
    for memory in range(2*conv+2, 4*conv):
        check(sequence, memory)


def test_conv3_stride3_step1():
    """Convoltion like suite."""
    conv, stride, step = 3, 3, 1
    sequence = [float(step*a + stride*s) for a in range(5) for s in range(conv)]
    for memory in range(2*conv+2, 4*conv):
        check(sequence, memory)


def test_conv3_stride3_step2():
    """Convoltion like suite."""
    conv, stride, step = 3, 3, 2
    sequence = [float(step*a + stride*s) for a in range(5) for s in range(conv)]
    for memory in range(2*conv+2, 4*conv):
        check(sequence, memory)


def test_linear_one():
    """Ensure it is able to predict a linear suite."""
    sequence = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0]
    check(sequence, 4)
    check(sequence, 5)
    check(sequence, 6)
    check(sequence, 7)
    check(sequence, 8)
    check(sequence, 9)


def test_linear_two():
    """Ensure it is able to predict a linear suite."""
    sequence = [0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0]
    check(sequence, 4)
    check(sequence, 5)
    check(sequence, 6)
    check(sequence, 7)
    check(sequence, 8)
    check(sequence, 9)
