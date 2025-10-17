"""Module containing tests for the abllib.wrapper module"""

import os
import re
from time import monotonic, sleep

import pytest

from abllib import error, log, wrapper
from abllib.pproc import WorkerThread

# pylint: disable=function-redefined, consider-using-with, unused-argument

def test_lock():
    """Ensure that Lock works as expected"""

    assert hasattr(wrapper, "Lock")
    assert callable(wrapper.Lock)

    lock = wrapper.Lock()

    assert not lock.locked()
    assert lock.acquire(blocking=True, timeout=1)
    assert lock.locked()

    assert not lock.acquire(blocking=True, timeout=1)

    lock.release()
    assert not lock.locked()

    with lock:
        assert lock.locked()
    assert not lock.locked()

    # releasing an unlocked lock should do nothing
    lock.release()

def test_lock_timeout():
    """Ensure that Lock timeouts are within expected boundaries"""

    lock = wrapper.Lock()

    lock.acquire(blocking=True, timeout=1)

    start_time = monotonic()
    assert not lock.acquire(blocking=True, timeout=0.1)

    duration = monotonic() - start_time
    assert duration > 0.05
    assert duration < 0.15

def test_lock_nested():
    """Ensure that Locks can be nested"""

    lock1 = wrapper.Lock()
    lock2 = wrapper.Lock()

    assert lock1.acquire(timeout=1)
    assert lock2.acquire(timeout=1)

    lock1.release()
    lock2.release()

def test_semaphore():
    """Ensure that Semaphore works as expected"""

    assert hasattr(wrapper, "Semaphore")
    assert callable(wrapper.Semaphore)

    sem = wrapper.Semaphore(3)

    assert not sem.locked()
    assert sem.acquire(blocking=True, timeout=1)
    assert sem.locked()
    assert sem.acquire(blocking=True, timeout=1)
    assert sem.locked()
    assert sem.acquire(blocking=True, timeout=1)
    assert sem.locked()

    # the semaphore is full
    assert not sem.acquire(blocking=True, timeout=1)

    sem.release()
    assert sem.locked()
    sem.release()
    assert sem.locked()
    sem.release()
    assert not sem.locked()

    with sem:
        assert sem.locked()
    assert not sem.locked()

    # releasing an unlocked semaphore should do nothing
    sem.release()

def test_semaphore_multi_release():
    """Ensure that semaphores can be released multiple times at once"""

    sem = wrapper.Semaphore(10)

    assert sem.acquire(blocking=True, timeout=1)
    assert sem.acquire(blocking=True, timeout=1)
    assert sem.acquire(blocking=True, timeout=1)
    sem.release(3)
    assert not sem.locked()

    assert sem.acquire(blocking=True, timeout=1)
    assert sem.acquire(blocking=True, timeout=1)
    assert sem.acquire(blocking=True, timeout=1)
    sem.release(2)
    assert sem.locked()
    sem.release()
    assert not sem.locked()

    assert sem.acquire(blocking=True, timeout=1)
    assert sem.acquire(blocking=True, timeout=1)
    assert sem.acquire(blocking=True, timeout=1)
    sem.release(4)
    assert not sem.locked()

def test_semaphore_timeout():
    """Ensure that Semaphore timeouts are within expected boundaries"""

    sem = wrapper.Semaphore(1)

    sem.acquire(blocking=True, timeout=1)

    start_time = monotonic()
    assert not sem.acquire(blocking=True, timeout=0.4)

    duration = monotonic() - start_time
    assert duration > 0.3
    assert duration < 0.5

def test_semaphore_nested():
    """Ensure that Semaphores can be nested"""

    sem1 = wrapper.Semaphore()
    sem2 = wrapper.Semaphore()

    assert sem1.acquire(timeout=1)
    assert sem2.acquire(timeout=1)

    sem1.release()
    sem2.release()

def test_namedlock():
    """Ensure that NamedLock works as expected"""

    assert hasattr(wrapper, "NamedLock")
    assert callable(wrapper.NamedLock)

    @wrapper.NamedLock("test1", timeout=0.1)
    def func1():
        return True

    assert not wrapper.NamedLock("test1").locked()
    assert func1()
    assert not wrapper.NamedLock("test1").locked()

    wrapper.NamedLock("test2").acquire()
    assert wrapper.NamedLock("test2").locked()
    assert wrapper.NamedLock("test2", timeout=1).locked()

def test_namedlock_timeout():
    """Ensure that NamedLock timeouts are within expected boundaries"""

    wrapper.NamedLock("test3").acquire()
    def func2():
        assert wrapper.NamedLock("test3").locked()
        wrapper.NamedLock("test3", timeout=0.7).acquire()

    start_time = monotonic()
    thread = WorkerThread(target=func2)
    thread.start()
    with pytest.raises(error.LockAcquisitionTimeoutError):
        thread.join(reraise=True)

    duration = monotonic() - start_time
    assert duration > 0.6
    assert duration < 0.8

def test_namedlock_nested():
    """Ensure that NamedLocks can be nested"""

    wrapper.NamedLock("test1", timeout=0.1).acquire()
    wrapper.NamedLock("test2", timeout=0.1).acquire()

    wrapper.NamedLock("test1").release()
    wrapper.NamedLock("test2").release()

def test_namedsemaphore():
    """Ensure that NamedSemaphore works as expected"""

    assert hasattr(wrapper, "NamedSemaphore")
    assert callable(wrapper.NamedSemaphore)

    @wrapper.NamedSemaphore("test1", timeout=0.1)
    def func1():
        return True

    assert not wrapper.NamedSemaphore("test1").locked()
    assert func1()
    assert not wrapper.NamedSemaphore("test1").locked()

    wrapper.NamedSemaphore("test2").acquire()
    assert wrapper.NamedSemaphore("test2").locked()
    assert wrapper.NamedSemaphore("test2", timeout=1).locked()

    wrapper.NamedSemaphore("test2").release()

def test_namedsemaphore_timeout():
    """Ensure that NamedSemaphore timeouts are within expected boundaries"""

    wrapper.NamedLock("test3").acquire()
    def func2():
        assert not wrapper.NamedSemaphore("test3").locked()
        wrapper.NamedSemaphore("test3", timeout=0.2).acquire()

    start_time = monotonic()
    thread = WorkerThread(target=func2)
    thread.start()
    with pytest.raises(error.LockAcquisitionTimeoutError):
        thread.join(reraise=True)

    duration = monotonic() - start_time
    assert duration > 0.1
    assert duration < 0.3

def test_namedsemaphore_nested():
    """Ensure that NamedSemaphores can be nested"""

    wrapper.NamedSemaphore("test1", timeout=0.1).acquire()
    wrapper.NamedSemaphore("test2", timeout=0.1).acquire()

    wrapper.NamedSemaphore("test1").release()
    wrapper.NamedSemaphore("test2").release()

def test_namedlocks_combined():
    """Ensure that NamedLock and NamedSemaphore work together correctly"""

    @wrapper.NamedLock("test1", timeout=0.1)
    def func():
        return True

    wrapper.NamedSemaphore("test1").acquire()
    with pytest.raises(error.LockAcquisitionTimeoutError):
        func()
    wrapper.NamedSemaphore("test1").release()


    @wrapper.NamedLock("test2", timeout=0.1)
    def func():
        return True

    wrapper.NamedSemaphore("test2").acquire()
    wrapper.NamedSemaphore("test2").acquire()
    wrapper.NamedSemaphore("test2").acquire()
    with pytest.raises(error.LockAcquisitionTimeoutError):
        func()
    wrapper.NamedSemaphore("test2").release()
    with pytest.raises(error.LockAcquisitionTimeoutError):
        func()
    wrapper.NamedSemaphore("test2").release()
    with pytest.raises(error.LockAcquisitionTimeoutError):
        func()
    wrapper.NamedSemaphore("test2").release()
    func()


    @wrapper.NamedSemaphore("test3", timeout=0.1)
    def func():
        return True

    wrapper.NamedLock("test3").acquire()
    with pytest.raises(error.LockAcquisitionTimeoutError):
        func()
    wrapper.NamedLock("test3").release()

def test_locks_underscore_names():
    """Ensure that named lock names can start with an underscore"""

    lock = wrapper.NamedSemaphore("_test1")
    assert not lock.locked()
    lock.acquire()
    assert lock.locked()
    assert wrapper.NamedSemaphore("_test1").locked()
    lock.release()
    assert not lock.locked()
    assert not wrapper.NamedSemaphore("_test1").locked()

    lock = wrapper.NamedLock("_test2")
    assert not lock.locked()
    lock.acquire()
    assert lock.locked()
    assert wrapper.NamedLock("_test2").locked()
    lock.release()
    assert not lock.locked()
    assert not wrapper.NamedLock("_test2").locked()

def test_singleuse():
    """Ensure that singleuse works as expected"""

    @wrapper.singleuse
    def func1():
        pass

    func1()

    with pytest.raises(error.CalledMultipleTimesError):
        func1()

    with pytest.raises(error.CalledMultipleTimesError):
        func1()

def test_singleuse_exception():
    """Ensure that raised exceptions reset singleuse flag"""

    data = [1, 2, 3]

    @wrapper.singleuse
    def func1():
        if len(data) > 0:
            data.pop(0)
            raise error.InternalCalculationError()

    with pytest.raises(error.InternalCalculationError):
        func1()
    with pytest.raises(error.InternalCalculationError):
        func1()
    with pytest.raises(error.InternalCalculationError):
        func1()

    func1()

    with pytest.raises(error.CalledMultipleTimesError):
        func1()

    with pytest.raises(error.CalledMultipleTimesError):
        func1()

def test_log_error_default(capture_logs):
    """Ensure that log_error uses the root logger by default"""

    @wrapper.log_error
    def func1():
        raise RuntimeError("my message")

    with pytest.raises(RuntimeError):
        func1()

    assert os.path.isfile("test.log")
    with open("test.log", "r", encoding="utf8") as f:
        content = f.readlines()

        # remove "pointer" lines only present in python 3.12
        content = list(filter(lambda x: x.strip().strip("^") != "", content))

        assert len(content) == 7
        assert re.match(r"\[.*\] \[ERROR   \] root: my message", content[0])
        assert re.match(r"Traceback \(most recent call last\):", content[1])
        assert re.match(r"  File \".*_log_error.py\", line \d+, in wrapper", content[2])
        assert re.match(r"    return func\(\*args, \*\*kwargs\)", content[3])
        assert re.match(r"  File \".*wrapper_test.py\", line \d+, in func1", content[4])
        assert re.match(r"    raise RuntimeError\(\"my message\"\)", content[5])
        assert re.match(r"RuntimeError: my message", content[6])

def test_log_error_loggername(capture_logs):
    """Ensure that log_error uses the provided logger name"""

    @wrapper.log_error("mycustomlogger")
    def func1():
        raise RuntimeError("my message")

    with pytest.raises(RuntimeError):
        func1()

    assert os.path.isfile("test.log")
    with open("test.log", "r", encoding="utf8") as f:
        content = f.readlines()

        # remove "pointer" lines only present in python 3.12
        content = list(filter(lambda x: x.strip().strip("^") != "", content))

        assert len(content) == 7
        assert re.match(r"\[.*\] \[ERROR   \] mycustomlogger: my message", content[0])
        assert re.match(r"Traceback \(most recent call last\):", content[1])
        assert re.match(r"  File \".*_log_error.py\", line \d+, in wrapper", content[2])
        assert re.match(r"    return func\(\*args, \*\*kwargs\)", content[3])
        assert re.match(r"  File \".*wrapper_test.py\", line \d+, in func1", content[4])
        assert re.match(r"    raise RuntimeError\(\"my message\"\)", content[5])
        assert re.match(r"RuntimeError: my message", content[6])

def test_log_error_customlogger(capture_logs):
    """Ensure that log_error uses the provided custom logger"""

    @wrapper.log_error(log.get_logger("mycustomlogger"))
    def func1():
        raise RuntimeError("my message")

    with pytest.raises(RuntimeError):
        func1()

    assert os.path.isfile("test.log")
    with open("test.log", "r", encoding="utf8") as f:
        content = f.readlines()

        # remove "pointer" lines only present in python 3.12
        content = list(filter(lambda x: x.strip().strip("^") != "", content))

        assert len(content) == 7
        assert re.match(r"\[.*\] \[ERROR   \] mycustomlogger: my message", content[0])
        assert re.match(r"Traceback \(most recent call last\):", content[1])
        assert re.match(r"  File \".*_log_error.py\", line \d+, in wrapper", content[2])
        assert re.match(r"    return func\(\*args, \*\*kwargs\)", content[3])
        assert re.match(r"  File \".*wrapper_test.py\", line \d+, in func1", content[4])
        assert re.match(r"    raise RuntimeError\(\"my message\"\)", content[5])
        assert re.match(r"RuntimeError: my message", content[6])

def test_log_error_handler():
    """Ensure that log_error uses the provided handler"""

    results = []
    def myhandler(exc_text):
        results.append(exc_text)

    @wrapper.log_error(handler=myhandler)
    def func1():
        raise RuntimeError("my message")

    with pytest.raises(RuntimeError):
        func1()

    assert len(results) == 1
    assert results[0] == "RuntimeError: my message"

def test_log_io_default(capture_logs):
    """Ensure that log_io uses the root logger by default"""

    @wrapper.log_io
    def func1(name, age, message = ""):
        return f"{name}: {message}"

    assert func1("Tom", 46) == "Tom: "
    assert func1("Anna", 77, message="no") == "Anna: no"

    assert os.path.isfile("test.log")
    with open("test.log", "r", encoding="utf8") as f:
        content = f.readlines()

        assert len(content) == 6
        assert re.match(r'\[.*\] \[DEBUG   \] root: func: func1', content[0])
        assert re.match(r'\[.*\] \[DEBUG   \] root: in  : "Tom", 46', content[1])
        assert re.match(r'\[.*\] \[DEBUG   \] root: out : "Tom: "', content[2])
        assert re.match(r'\[.*\] \[DEBUG   \] root: func: func1', content[3])
        assert re.match(r'\[.*\] \[DEBUG   \] root: in  : "Anna", 77, message="no"', content[4])
        assert re.match(r'\[.*\] \[DEBUG   \] root: out : "Anna: no"', content[5])

def test_log_io_loggername(capture_logs):
    """Ensure that log_io uses the provided logger name"""

    @wrapper.log_io("SpecialLogger")
    def func1(name, age, message = ""):
        return f"{name}: {message}"

    assert func1("Tom", 46) == "Tom: "
    assert func1("Anna", 77, "no") == "Anna: no"

    assert os.path.isfile("test.log")
    with open("test.log", "r", encoding="utf8") as f:
        content = f.readlines()

        assert len(content) == 6
        assert re.match(r'\[.*\] \[DEBUG   \] SpecialLogger: func: func1', content[0])
        assert re.match(r'\[.*\] \[DEBUG   \] SpecialLogger: in  : "Tom", 46', content[1])
        assert re.match(r'\[.*\] \[DEBUG   \] SpecialLogger: out : "Tom: "', content[2])
        assert re.match(r'\[.*\] \[DEBUG   \] SpecialLogger: func: func1', content[3])
        assert re.match(r'\[.*\] \[DEBUG   \] SpecialLogger: in  : "Anna", 77, "no"', content[4])
        assert re.match(r'\[.*\] \[DEBUG   \] SpecialLogger: out : "Anna: no"', content[5])

def test_log_io_custom_logger(capture_logs):
    """Ensure that log_io uses a custom provided logger"""

    @wrapper.log_io(log.get_logger("ExtraLogger"))
    def func1(name, age, message = ""):
        return f"{name}: {message}"

    assert func1("Tom", 46) == "Tom: "
    assert func1("Anna", 77, "no") == "Anna: no"

    assert os.path.isfile("test.log")
    with open("test.log", "r", encoding="utf8") as f:
        content = f.readlines()

        assert len(content) == 6
        assert re.match(r'\[.*\] \[DEBUG   \] ExtraLogger: func: func1', content[0])
        assert re.match(r'\[.*\] \[DEBUG   \] ExtraLogger: in  : "Tom", 46', content[1])
        assert re.match(r'\[.*\] \[DEBUG   \] ExtraLogger: out : "Tom: "', content[2])
        assert re.match(r'\[.*\] \[DEBUG   \] ExtraLogger: func: func1', content[3])
        assert re.match(r'\[.*\] \[DEBUG   \] ExtraLogger: in  : "Anna", 77, "no"', content[4])
        assert re.match(r'\[.*\] \[DEBUG   \] ExtraLogger: out : "Anna: no"', content[5])

def test_timeit_default(capture_logs):
    """Ensure that timeit uses the root logger by default"""

    @wrapper.timeit
    def func1():
        sleep(0.001)
    @wrapper.timeit
    def func2():
        sleep(0.01)
    @wrapper.timeit
    def func3():
        sleep(0.1)
    @wrapper.timeit
    def func4():
        sleep(1)
    @wrapper.timeit
    def func5():
        sleep(10)


    func1()
    func2()
    func3()
    func4()
    func5()

    assert os.path.isfile("test.log")
    with open("test.log", "r", encoding="utf8") as f:
        content = f.readlines()

        assert len(content) == 5
        assert re.match(r'\[.*\] \[DEBUG   \] root: func1: \d{1}\.\d{2} ms elapsed', content[0])
        assert re.match(r'\[.*\] \[DEBUG   \] root: func2: \d{2}\.\d{2} ms elapsed', content[1])
        assert re.match(r'\[.*\] \[DEBUG   \] root: func3: \d{3}\.\d{2} ms elapsed', content[2])
        assert re.match(r'\[.*\] \[DEBUG   \] root: func4: \d{1}\.\d{2} s elapsed', content[3])
        assert re.match(r'\[.*\] \[DEBUG   \] root: func5: \d{2}\.\d{2} s elapsed', content[4])

def test_timeit_loggername(capture_logs):
    """Ensure that timeit uses the provided logger name"""

    @wrapper.timeit("SpecialLogger")
    def func1():
        sleep(0.001)

    func1()

    assert os.path.isfile("test.log")
    with open("test.log", "r", encoding="utf8") as f:
        content = f.readlines()

        assert len(content) == 1
        assert re.match(r'\[.*\] \[DEBUG   \] SpecialLogger: func1: \d{1}\.\d{2} ms elapsed', content[0])

def test_timeit_custom_logger(capture_logs):
    """Ensure that timeit uses a custom provided logger"""

    @wrapper.timeit(log.get_logger("ExtraLogger"))
    def func1():
        sleep(0.001)

    func1()

    assert os.path.isfile("test.log")
    with open("test.log", "r", encoding="utf8") as f:
        content = f.readlines()

        assert len(content) == 1
        assert re.match(r'\[.*\] \[DEBUG   \] ExtraLogger: func1: \d{1}\.\d{2} ms elapsed', content[0])
