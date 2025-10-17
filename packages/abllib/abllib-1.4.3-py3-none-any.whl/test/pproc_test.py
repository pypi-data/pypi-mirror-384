"""Module containing tests for abllib.thread"""

from multiprocessing import Process
from threading import Thread
from time import sleep

import pytest

from abllib import pproc, wrapper

# pylint: disable=missing-class-docstring

def test_workerthread_inheritance():
    """Ensure that WorkerThread inherits from Thread"""

    assert hasattr(pproc, "WorkerThread")
    assert issubclass(pproc.WorkerThread, Thread)

def test_workerthread_func_execution():
    """Ensure that WorkerThread executes its target and then exits"""

    out = [False]
    def func1():
        out[0] = True

    t = pproc.WorkerThread(target=func1)
    t.start()

    c = 0
    while c < 10 and not out[0] and t.is_alive():
        sleep(0.1)
        c += 1

    if c >= 10:
        pytest.fail("thread did not complete in time")

    # is_alive stays True for a short time after thread completes
    sleep(0.1)
    assert not t.is_alive()

    assert out[0]

def test_workerthread_value_return():
    """Ensure that WorkerThread returns values"""

    def func1():
        return None

    t = pproc.WorkerThread(target=func1)
    t.start()

    r = t.join()
    assert r is None
    r = t.join(reraise=True)
    assert r is None

    def func2():
        return ("val1", 25)

    t = pproc.WorkerThread(target=func2)
    t.start()

    r = t.join()
    assert not t.is_alive()
    assert not t.failed()
    assert r == ("val1", 25)
    assert isinstance(r[0], str)
    assert isinstance(r[1], int)

    r = t.join(reraise=True)
    assert not t.is_alive()
    assert not t.failed()
    assert r == ("val1", 25)
    assert isinstance(r[0], str)
    assert isinstance(r[1], int)


def test_workerthread_exception_return():
    """Ensure that WorkerThread returns exceptions"""

    def func1():
        raise AssertionError("This is a test message")

    t = pproc.WorkerThread(target=func1)
    t.start()

    r = t.join()
    assert t.failed()
    assert isinstance(r, BaseException)
    assert str(r) == "This is a test message"

def test_workerthread_exception_reraise():
    """Ensure that WorkerThread reraises exceptions if flag is set"""

    def func1():
        raise AssertionError("This is a test message")

    t = pproc.WorkerThread(target=func1)
    t.start()

    try:
        t.join(reraise=True)
    except AssertionError as e:
        assert str(e) == "This is a test message"
    else:
        pytest.fail("no exception raised")

def test_workerprocess_inheritance():
    """Ensure that WorkerProcess inherits from Process"""

    assert hasattr(pproc, "WorkerProcess")
    assert issubclass(pproc.WorkerProcess, Process)

def test_workerprocess_value_return():
    """Ensure that WorkerProcess returns values"""

    def func1():
        return None

    p = pproc.WorkerProcess(target=func1)
    p.start()

    r = p.join()
    assert r is None
    r = p.join(reraise=True)
    assert r is None

    def func2():
        return ("val1", 25)

    p = pproc.WorkerProcess(target=func2)
    p.start()

    r = p.join()
    assert not p.failed()
    assert r == ("val1", 25)
    assert isinstance(r[0], str)
    assert isinstance(r[1], int)

    r = p.join(reraise=True)
    assert not p.failed()
    assert r == ("val1", 25)
    assert isinstance(r[0], str)
    assert isinstance(r[1], int)

def test_workerprocess_exception_return():
    """Ensure that WorkerProcess returns exceptions"""

    def func1():
        raise AssertionError("This is a test message")

    p = pproc.WorkerProcess(target=func1)
    p.start()

    r = p.join()
    assert p.failed()
    assert isinstance(r, BaseException)
    assert str(r) == "This is a test message"

def test_workerprocess_exception_reraise():
    """Ensure that WorkerProcess reraises exceptions if flag is set"""

    def func1():
        raise AssertionError("This is a test message")

    t = pproc.WorkerProcess(target=func1)
    t.start()

    try:
        t.join(reraise=True)
    except AssertionError as e:
        assert str(e) == "This is a test message"
    else:
        pytest.fail("no exception raised")

def test_lock():
    """Ensure that Lock is imported correctly"""

    assert hasattr(wrapper, "Lock")
    assert pproc.Lock == wrapper.Lock

def test_semaphore():
    """Ensure that Semaphore is imported correctly"""

    assert hasattr(wrapper, "Semaphore")
    assert pproc.Semaphore == wrapper.Semaphore
