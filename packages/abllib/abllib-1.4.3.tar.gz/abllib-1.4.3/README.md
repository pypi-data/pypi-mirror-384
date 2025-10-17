# abllib

Ableytners' general-purpose python library.

Supports Python versions 3.11 - 3.14.

## Overview

This project is a collection of many small helper modules that can be used for all kinds of projects.

It is structured into small submodules, which are all optional and not dependent on each other. Feel free to only use the ones you need.

The following submodules are available:
1. Algorithms (`abllib.alg`)
2. Errors (`abllib.error`)
3. File system operations (`abllib.fs`)
4. Fuzzy matching (`abllib.fuzzy`)
5. General (`abllib.general`)
6. Logging (`abllib.log`)
7. Cleanup on exit (`abllib.onexit`)
8. Parallel processing (`abllib.pproc`)
9. Storages (`abllib.storage`)
10. Function wrappers (`abllib.wrapper`)

## Installation

### PyPI

All stable versions get released on [PyPI](https://pypi.org/project/abllib). To download the newest version, run the following command:
```bash
pip install abllib
```
This will automatically install all other dependencies.

Alternatively, a specific version can be installed as follows:
```bash
pip install abllib==1.3.6
```
where 1.3.6 is the version you want to install.

### Github

To install the latest development version directly from Github, run the following command:
```bash
pip install git+https://github.com/Ableytner/abllib
```

Additionally, a [wheel](https://peps.python.org/pep-0427/) is added to every [stable release](https://github.com/Ableytner/abllib/releases), which can be manually downloaded and installed.

### requirements.txt

If you want to include this library as a dependency in your requirements.txt, the syntax is as follows:
```text
abllib==1.3.6
```
where 1.3.6 is the version that you want to install.

To always use the latest stable version:
```text
abllib
```

To always install the latest development version:
```text
abllib @ git+https://github.com/Ableytner/abllib
```

### Optional dependencies

Some modules have optional dependencies which bring various improvements.
All of them are optional and listed below.

| name | needed in | improvement |
|------|-----------|-------------|
| pykakasi | fs.filename | needed to correctly translate japanese kanji |
| levenshtein | alg.levenshtein_distance | provides a 10x speedup by using the C implementation |

## Documentation

### 1. Algorithms (`abllib.alg`)

This module contains general-purpose algorithms.

#### Levenshtein distance (`abllib.alg.levenshtein_distance`)

Calculate the [edit distance](https://en.wikipedia.org/wiki/Levenshtein_distance) between two words.

Example usage:
```py
>> from abllib.alg import levenshtein_distance
>> levenshtein_distance("house", "houses")
1
>> levenshtein_distance("mice", "mouse")
3
>> levenshtein_distance("thomas", "anna")
5
```

If the optional package 'Levenshtein' is installed (`pip install Levenshtein`), its C implementation is used instead.
This provides a 10x speedup, but requires an extra package.

### 2. Errors (`abllib.error`)

This module contains a custom exception system, which supports default messages for different errors.

#### CustomException (`abllib.error.CustomException`)

The base class to all custom exceptions. This class cannot be invoked on its own, but should be subclassed to create your own error classes.

Note that all deriving classes' names should end with 'Error', not 'Exception', to stay consistent with the python naming scheme.

Example usage:
```py
>> from abllib.error import CustomException
>> class MySpecialError(CustomException):
..     default_messages = {0: "This error shows a default message!", 1: "This error shows {0}!"}
>> raise MySpecialError()
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
    raise MySpecialError()
MySpecialError: This error shows a default message!
>> raise MySpecialError.with_values("a customizable message")
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
    raise MySpecialError.with_values("a customizable message")
MySpecialError: This error shows a customizable message!
```

Note that custom error classes need to define the class member `default_messages`, which contains the default error messages.
The keys (0 in this example) refer to the number of arguments that will be auto-filled.

A default message for 0 arguments is mandatory.

#### General purpose errors

This module also contains some premade general-purpose error classes, which all derive from `CustomException`. The following classes are provided:
* CalledMultipleTimesError
* DeprecatedError
* DirNotFoundError
* InternalCalculationError
* InternalFunctionUsedError
* InvalidKeyError
* KeyNotFoundError
* LockAcquisitionTimeoutError
* MissingDefaultMessageError
* MissingInheritanceError
* NameNotFoundError
* NoneTypeError
* NotInitializedError
* ReadonlyError
* RegisteredMultipleTimesError
* SingletonInstantiationError
* UninitializedFieldError
* WrongTypeError

### 3. File system (`abllib.fs`)

This module contains various file system-related functionality. All provided functions are tested and work correctly on Linux and Windows systems.

#### Absolute path (`abllib.fs.absolute`)

A function which accepts filenames / paths and makes them absolute, also resolving all symlinks and '..'-calls. If a relative path is provided, the current working directory is prepended.

Example usage:
```py
>> from abllib.fs import absolute
>> absolute("image.png")
'C:\\MyUser\\Some\\sub\\dir\\image.png'
>> absolute("../../image.png")
'C:\\MyUser\\Some\\image.png'
>> absolute("C:\\MyUser\\Some\\image.png")
'C:\\MyUser\\Some\\image.png'
```

#### Filename sanitization (`abllib.fs.sanitize`)

A function which accepts any text and sanitizes it for use as a file name / folder name.
The resulting text only contains ascii characters.

Example usage:
```py
>> from abllib.fs import sanitize
>> sanitize("myfilename.txt")
'myfilename.txt'
>> sanitize("This sentence gets converted..txt")
'This_sentence_gets_converted.txt'
>> sanitize("special' char/act\\ers ar|e i*gnor;ed")
'special_char_act_ers_ar_e_ignor_ed'
>> sanitize("Die grüne Böschung")
'Die_grune_Boschung'
>> sanitize("ハウルの動く城")
'hauru_no_ugoku_shiro'
```

Currently supported language-specific text transliterations:
| language   | supported | additional notes                                                                                                                           |
| ---------- | :-------: | ------------------------------------------------------------------------------------------------------------------------------------------ |
| english    | yes       |                                                                                                                                            |
| german     | yes       |                                                                                                                                            |
| japanese   | partial   | needs optional library [pykakasi](https://pypi.org/project/pykakasi/) (`pip install pykakasi`), otherwise removes japanese characters      |

Special characters from unsupported languages and any other non-ascii will be removed from the resulting text.

### 4. Fuzzy matching (`abllib.fuzzy`)

This module contains functions to search for strings within a list of strings, while applying [fuzzy searching logic](https://en.wikipedia.org/wiki/Approximate_string_matching).

> [!TIP]
> If the performance seems poor, the optional levenshtein package can be installed for a 10x speedup (`pip install levenshtein`).

The source code and documentation use a few words which might be confusing, so they are explained here:
* target: the word that we want to find.
* candidate: a word that could match with target.
* score: the similarity score, which is a float value between 0 and 1, rounded down to two digits.

Note that target and candidate can be a single word, multiple words separated by ' ', or a sentence.

Furthermore, it is possible to pass an [iterable](https://docs.python.org/3/glossary.html#term-iterable) as the candidate.
This will try to match the target against all of its items.

#### Results packaged in MatchResult (`abllib.fuzzy.MatchResult`)

Using the primary matching functions will return MatchResult objects, which encapsulate the functions results.

MatchResult is a simple dataclass with the following fields:
* value: the candidate that was the closest match.
* index: the index of the candidate that was the closest match.
This index corresponds to the original candidates list.
* inner_index: None if candidate is a string, or the index of the matching sub-candidate.
This index corresponds to the sub-candidate within the matching iterable candidate.
* score: the 'similarity' between the target and closest matching candidate.

Example usage, assuming that result was received from a match function:
```py
>> result
MatchResult(score=np.float64(1.0), value=['book', 'libro', 'Buch'], index=1, inner_index=2)
>> result.score
np.float64(1.0)
>> result.value
['book', 'libro', 'Buch']
```

Example for using the inner_index:
```py
>> from abllib.fuzzy import match_closest
>> candidates = [["house", "casa", "Haus"], ["book", "libro", "Buch"]]
>> result = match_closest("Buch", candidates)
>> result
MatchResult(score=np.float64(1.0), value=['book', 'libro', 'Buch'], index=1, inner_index=2)
>> result.value[result.inner_index]
Buch
>> candidates[result.index][result.inner_index]
Buch
```
This means that 'Buch' was the closest-matching candidate.

#### Find closest-matching candidate (`abllib.fuzzy.match_closest`)

A function which returns the closest-matching candidate out of a list of candidates.

To achieve this, two different strategies are used:
* calculate the edit distance between the whole target and candidate.
* split target / candidate at ' ' and calculate the edit distance between each word.

After that, a MatchResult with the closest-matching candidate will be returned.

Example usage:
```py
>> from abllib.fuzzy import match_closest
>> match_closest("cat", ["dog", "car"])
MatchResult(score=np.float64(0.67), value='car', index=1, inner_index=None)
>> match_closest("Buch", [["house", "casa", "Haus"], ["book", "libro", "Buch"]])
MatchResult(score=np.float64(1.0), value=['book', 'libro', 'Buch'], index=1, inner_index=2)
```

#### Find all matching candidates (`abllib.fuzzy.match_all`)

A function which returns all matching candidates out of a list of candidates.

To achieve this, two different strategies are used:
* calculate the edit distance between the whole target and candidate.
* split target / candidate at ' ' and calculate the edit distance between each word.

After that, a list of MatchResults which are within a certain threshold are returned.

Example usage:
```py
>> from abllib.fuzzy import match_all
>> results = match_all("cat", ["dog", "car", "card", "horse", "mouse", "cat"])
>> results
[MatchResult(score=np.float64(0.67), value='car', index=1, inner_index=None), MatchResult(score=np.float64(0.5), value='card', index=2, inner_index=None), MatchResult(score=np.float64(1.0), value='cat', index=5, inner_index=None)]
>> len(results)
3
```

#### Calculate the similartity score between two targets (`abllib.fuzzy.similarity`)

A function which returns the similarity score between two targets.
The targets can be a single word or a whole sentence.

To achieve this, two different strategies are used:
* calculate the edit distance between the whole target and candidate.
* split target / candidate at ' ' and calculate the edit distance between each word.

The score is returned as a simple float value, rounded down to two digits.

Example usage:
```py
>> from abllib.fuzzy import similarity
>> similarity("cat", "dog")
0.0
>> similarity("cat", "car")
0.67
>> similarity("cat", "cat")
1.0
```

### 5. General (`abllib.general`)

This module contains different general-purpose functions that don't warrant an own module.

#### Try to import a module (`abllib.general.try_import_module`)

This function tries to import and return a given module.

```py
>> from abllib.general import try_import_module
>> sys = try_import_module("sys")
>> sys.modules
{'sys': <module 'sys' (built-in)>, ...}
>> non_existent = try_import_module("non_existent")
>> non_existent
None
```

If the optional argument `error_msg` is given and the import fails, the message will be logged.
```py
>> from abllib.general import try_import_module
>> non_existent = try_import_module("non_existent", "The module 'non_existent' doesn't exist")
[2025-08-20 10:58:07] [WARNING ] general: The module 'non_existent' doesn't exist
>> non_existent
None
```

If the optional argument `enforce` is given and the import fails, an error is thrown.
```py
>> from abllib.general import try_import_module
>> non_existent = try_import_module("non_existent", enforce=True)
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
abllib.error._general.MissingRequiredModuleError: "The required module 'non_existent' is not installed."
>> non_existent = try_import_module("non_existent", error_msg="The error message", enforce=True)
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
abllib.error._general.MissingRequiredModuleError: "The error message"
```

### 6. Logging (`abllib.log`)

This module contains functions to easily log to the console or specified log files.
It can be used without initialization, or customized.
If it isn't initialized, the currently set `logging` modules settings are used.

Example usage without setup:
```py
>> from abllib import log
>> logger = log.get_logger()
>> logger.info("this is a test log")
this is a test log
```
In this example, the returned logger is a `logging.Logger` object from the Python standard library.

The module can be customized as follows:
```py
>> from abllib import log
>> log.initialize(log.LogLevel.INFO)
>> log.add_console_handler()
>> logger = log.get_logger()
>> logger.debug("this call will do nothing")
>> logger.info("this is a test log")
[2025-04-08 23:03:08] [INFO    ] root: this is a test log
>> logger = log.get_logger("mymodule")
>> logger.info("we can set custom logger names")
[2025-04-08 23:04:13] [INFO    ] mymodule: we can set custom logger names
```

Logging to a file is supported as follows:
```py
>> from abllib import log
>> log.initialize(log.LogLevel.INFO)
>> log.add_file_handler("mylogfile.txt")
>> logger = log.get_logger()
>> logger.info("this is written to the file")
```
The logfile will be created once the first message with a high enough log level is logged.
The file is closed at program exit or handler removal.

`log.add_file_handler` also supports an optional filemode parameter, which specifies how the logfile should be opened, with the following options:
* w : overwrite
* a : append

Multiple handlers can also be added simultaneously.
In this case, the logged message is sent to all of them.
```py
>> from abllib import log
>> log.initialize(log.LogLevel.INFO)
>> log.add_console_handler()
>> log.add_file_handler("mylogfile.txt")
>> log.add_file_handler("/logs/anotherfile.txt")
>> logger = log.get_logger()
>> logger.info("this is written to both files")
[2025-04-08 23:09:31] [INFO    ] root: this is written to both files
```

#### Parsing the log level from a string

The libaries' LogLevel enum also contains a convenience function for parsing a log level.

Example code:
```py
>> from abllib import log
>> log.LogLevel.from_str("DEBUG")
LogLevel.DEBUG
>> log.LogLevel.from_str("critical")
LogLevel.CRITICAL
>> log.LogLevel.from_str("NONEXISTENT")
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
abllib.error._general.NameNotFoundError: "'NONEXISTENT' isn't a known log level"
```

#### Using the logging module in another library

This module can also be used in other libraries without having to worry about the final applications.
Calling `log.initialize` resets all previous configurations, so the application simply needs to do that.

Code in the library:
```py
>> from abllib import log
>> log.initialize(log.LogLevel.INFO)
>> log.add_console_handler()
```

Code in the application which runs later:
```py
>> from abllib import log
>> log.initialize(log.LogLevel.WARNING)
>> log.add_file_handler("mylogfile.txt")
```

This results in a final setup which writes to mylogfile.txt and doesn't produce console output.

### 7. Cleanup on exit (`abllib.onexit`)

This module contains functions to register callbacks which run on application exit.

The registered functions are called if the application:
* exits without an exception
* exits with an exception
* is killed by a SIGINT signal (the user pressed CTRL+C)
* is killed by a SIGTERM signal (the program is asked to shut down, e.g. when used in a docker container)
* calls sys.exit

The registered functions are NOT called if the application:
* is killed by a SIGKILL signal (cannot be handled by the program)
* calls os._exit
* encounters an unrecoverable interpreter exception

Note that this module can only be used from the main thread, as that is what the `signal` module demants.

Example usage:
```py
>> from abllib import onexit
>> def my_function():
..   print("we are exiting")
>> onexit.register("myfunc", my_function)
>> exit()
we are exiting
```

Already registered callbacks can also be deregistered:
```py
>> from abllib import onexit
>> def my_function():
..   print("we are exiting")
>> onexit.register("myfunc", my_function)
>> onexit.deregister("myfunc")
>> exit()
```

### 8. Parallel processing (`abllib.pproc`)

This module contains parallel processing-related functionality, both thread-based and process-based.

#### Thread vs Process

The parallel processing module contains both thread-based and process-based methods with overlapping functionality.
To help decide which solution to use, the key differences are outlined below:

You should use thread-based processing if the parallel task:
* is not CPU-intensive
* modifies local variables
* doesn't need to be killable

Alternatively, you should use process-based processing if the parallel task:
* is doing CPU-intensive calculations
* needs to be killable

The reason as to why CPU-intensive tasks in python should run in different processes is due to the [GIL](https://realpython.com/python-gil/) (global interpreter lock), which is further explained in the linked article. This effectively makes multiple threads run as fast as one thread if the bottleneck is the CPU.

Another thing to consider is that thread-based processing is simple and straightforward, whereas process-based functionality can be pretty complex.
Arguments passed to another process, for example, lose the reference to its original object.
This means that passing a list to a different process and adding an element in that process doesn't add anything in the original list.

TLDR: If you are not sure what to use, use thread-based processing.

#### WorkerThread (`abllib.pproc.WorkerThread`)

This class represents a separate thread that runs a given function until completion.
If .join() is called, the functions return value or any occurred exception is returned.
If .join() is called with reraise=True, any caught exception will be reraised.

Example usage:

```py
>> from abllib.pproc import WorkerThread
>> def the_answer():
..     return 42
>> wt = WorkerThread(target=the_answer)
>> wt.start()
>> wt.join()
42
```

Exceptions that occur are caught and returned. The exception object can be reraised manually.

Optionally, if reraise is provided, any caught exception will be raised automatically.
```py
>> from abllib.pproc import WorkerThread
>> def not_the_answer():
..     raise ValueError("The answer is not yet calculated!")
>> wt = WorkerThread(target=not_the_answer)
>> wt.start()
>> wt.join()
ValueError('The answer is not yet calculated!')
>> isinstance(wt.join(), BaseException)
True
>> raise wt.join()
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
ValueError: The answer is not yet calculated!
>> wt.join(reraise=True)
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
ValueError: The answer is not yet calculated!
```

#### WorkerProcess (`abllib.pproc.WorkerProcess`)

This class represents a separate process that runs a given function until completion.
If .join() is called, the functions return value or any occurred exception is returned.
If .join() is called with reraise=True, any caught exception will be reraised.

Example usage:

```py
>> from abllib.pproc import WorkerProcess
>> def the_answer():
..     return 42
>> wp = WorkerProcess(target=the_answer)
>> wp.start()
>> wp.join()
42
```

Exceptions that occur are caught and returned. The exception object can be reraised manually.

Optionally, if reraise is provided, any caught exception will be raised automatically.
```py
>> from abllib.pproc import WorkerProcess
>> def not_the_answer():
..     raise ValueError("The answer is not yet calculated!")
>> wp = WorkerProcess(target=not_the_answer)
>> wp.start()
>> wp.join()
ValueError('The answer is not yet calculated!')
>> isinstance(wp.join(), BaseException)
True
>> raise wp.join()
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
ValueError: The answer is not yet calculated!
>> wp.join(reraise=True)
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
ValueError: The answer is not yet calculated!
```

### 9. Storages (`abllib.storage`)

This module contains multiple storage types.
All data stored in these storages is accessible from anywhere within the program, as each storage is a global [singleton](https://en.wikipedia.org/wiki/Singleton_pattern).
Multithreaded access is also allowed.

The data is stored as key:value pairs. The key needs to be of type `<class 'str'>`, the allowed value types are storage-specific.

#### Initialize storages

The storages can be initialized (enabled) in two different ways:

Enable all storages:
```py
>> from abllib import storage
>> storage.initialize()
```

Alternatively, only the needed storages can be enabled:
```py
>> from abllib import VolatileStorage, PersistentStorage
>> VolatileStorage.initialize()
>> PersistentStorage.initialize()
```

#### VolatileStorage (`abllib.VolatileStorage`)

This storage can hold any type of value. The stored data is reset after each program restart.

Example usage:

First the storage needs to be imported and initialized:
```py
>> from abllib import VolatileStorage
>> VolatileStorage.initialize()
```

Items can be assigned in multiple ways:
```py
>> VolatileStorage["mykey"] = "myvalue"
>> VolatileStorage["toplevelkey.sublevelkey"] = "another value"
>> VolatileStorage["specialvalue"] = threading.Lock()
```

Presence of keys can be checked in multiple ways:
```py
>> "toplevelkey" in VolatileStorage
True
>> "toplevelkey.sublevelkey" in VolatileStorage
True
>> VolatileStorage.contains("toplevelkey")
True
>> in VolatileStorage.contains("toplevelkey.sublevelkey")
True
```

Items can be retrieved in multiple ways:
```py
>> VolatileStorage["mykey"]
'myvalue'
>> VolatileStorage.get("mykey")
'myvalue'
>> VolatileStorage["toplevelkey"]["sublevelkey"]
'another value'
>> VolatileStorage.get("toplevelkey")["sublevelkey"]
'another value'
>> VolatileStorage["toplevelkey.sublevelkey"]
'another value'
>> VolatileStorage.get("toplevelkey.sublevelkey")
'another value'
>> type(VolatileStorage["specialvalue"])
<class '_thread.lock'>
>> VolatileStorage.get("nonexistent.key", default=42)
42
```

Multiple items can also be retrieved at once:
```py
>> VolatileStorage.keys()
dict_keys(['mykey', 'toplevelkey', 'specialvalue'])
>> VolatileStorage.values()
dict_values(['myvalue', {'sublevelkey': 'another value'}, <unlocked _thread.lock object at 0x000002831830E980>])
>> VolatileStorage.items()
dict_items([('mykey', 'myvalue'), ('toplevelkey', {'sublevelkey': 'another value'}), ('specialvalue', <unlocked _thread.lock object at 0x000002831830E980>)])
```

There also exists a way to check whether an item and a key matches a certain value:
```py
>> VolatileStorage.contains_item("toplevelkey.sublevelkey", "another value")
True
>> # is equal to:
>> VolatileStorage["toplevelkey.sublevelkey"] == "another value"
True
```

Items can be deleted in multiple ways:
```py
>> del VolatileStorage["mykey"]
>> VolatileStorage.pop("mykey")
'myvalue'
>> del VolatileStorage["toplevelkey"]["sublevelkey"]
>> del VolatileStorage["toplevelkey.sublevelkey"]
>> VolatileStorage.pop("toplevelkey.sublevelkey")
'another value'
```
Trying to delete non-existent items raises a KeyNotFoundError.

#### PersistentStorage (`abllib.PersistentStorage`)

This storage automatically loads saved data on program start.
It can also save its data on program exit, if desired.

It can only hold values of the following types:
* bool
* int
* float
* str
* list
* dict
* tuple
* None

Example usage:

First the storage needs to be imported and initialized:
```py
>> from abllib import PersistentStorage
>> PersistentStorage.initialize(save_on_exit=True)
```

Items can be assigned in multiple ways:
```py
>> PersistentStorage["mykey"] = "myvalue"
>> PersistentStorage["toplevelkey.sublevelkey"] = "another value"
```

Presence of keys can be checked in multiple ways:
```py
>> "toplevelkey" in PersistentStorage
True
>> "toplevelkey.sublevelkey" in PersistentStorage
True
>> PersistentStorage.contains("toplevelkey")
True
>> in PersistentStorage.contains("toplevelkey.sublevelkey")
True
```

Items can be retrieved in multiple ways:
```py
>> PersistentStorage["mykey"]
'myvalue'
>> PersistentStorage.get("mykey")
'myvalue'
>> PersistentStorage["toplevelkey"]["sublevelkey"]
'another value'
>> PersistentStorage.get("toplevelkey")["sublevelkey"]
'another value'
>> PersistentStorage["toplevelkey.sublevelkey"]
'another value'
>> PersistentStorage.get("toplevelkey.sublevelkey")
'another value'
>> PersistentStorage.get("nonexistent.key", default=42)
42
```

Multiple items can also be retrieved at once:
```py
>> PersistentStorage.keys()
dict_keys(['mykey', 'toplevelkey'])
>> PersistentStorage.values()
dict_values(['myvalue', {'sublevelkey': 'another value'}])
>> PersistentStorage.items()
dict_items([('mykey', 'myvalue'), ('toplevelkey', {'sublevelkey': 'another value'})])
```

There also exists a way to check whether an item and a key matches a certain value:
```py
>> PersistentStorage.contains_item("toplevelkey.sublevelkey", "another value")
True
>> # is equal to:
>> PersistentStorage["toplevelkey.sublevelkey"] == "another value"
True
```

Items can be deleted in multiple ways:
```py
>> del PersistentStorage["mykey"]
>> PersistentStorage.pop("mykey")
'myvalue'
>> del PersistentStorage["toplevelkey"]["sublevelkey"]
>> del PersistentStorage["toplevelkey.sublevelkey"]
>> PersistentStorage.pop("toplevelkey.sublevelkey")
'another value'
```
Trying to delete non-existent items raises an KeyNotFoundError.

All storage data can be loaded and saved manually:
```py
>> PersistentStorage.load_from_disk()
>> PersistentStorage.save_to_disk()
```

#### CacheStorage (`abllib.CacheStorage`)

This storage is specialized for caching things. It can hold any type of value. The stored data is reset after each program restart.

Important: All stored data could be lost at any time, if a cache reset is forced.

Example usage:

First the storage needs to be imported:
```py
>> from abllib import CacheStorage
```
Initialization is not needed.

Items can be assigned in multiple ways:
```py
>> CacheStorage["mykey"] = "myvalue"
>> CacheStorage["toplevelkey.sublevelkey"] = "another value"
>> CacheStorage["specialvalue"] = threading.Lock()
```

Presence of keys can be checked in multiple ways:
```py
>> "toplevelkey" in CacheStorage
True
>> "toplevelkey.sublevelkey" in CacheStorage
True
>> CacheStorage.contains("toplevelkey")
True
>> in CacheStorage.contains("toplevelkey.sublevelkey")
True
```

Items can be retrieved in multiple ways:
```py
>> CacheStorage["mykey"]
'myvalue'
>> CacheStorage.get("mykey")
'myvalue'
>> CacheStorage["toplevelkey"]["sublevelkey"]
'another value'
>> CacheStorage.get("toplevelkey")["sublevelkey"]
'another value'
>> CacheStorage["toplevelkey.sublevelkey"]
'another value'
>> CacheStorage.get("toplevelkey.sublevelkey")
'another value'
>> type(CacheStorage["specialvalue"])
<class '_thread.lock'>
>> CacheStorage.get("nonexistent.key", default=42)
42
```

Multiple items can also be retrieved at once:
```py
>> CacheStorage.keys()
dict_keys(['mykey', 'toplevelkey', 'specialvalue'])
>> CacheStorage.values()
dict_values(['myvalue', {'sublevelkey': 'another value'}, <unlocked _thread.lock object at 0x000002831830E980>])
>> CacheStorage.items()
dict_items([('mykey', 'myvalue'), ('toplevelkey', {'sublevelkey': 'another value'}), ('specialvalue', <unlocked _thread.lock object at 0x000002831830E980>)])
```

There also exists a way to check whether an item and a key matches a certain value:
```py
>> CacheStorage.contains_item("toplevelkey.sublevelkey", "another value")
True
>> # is equal to:
>> CacheStorage["toplevelkey.sublevelkey"] == "another value"
True
```

Items can be deleted in multiple ways:
```py
>> del CacheStorage["mykey"]
>> CacheStorage.pop("mykey")
'myvalue'
>> del CacheStorage["toplevelkey"]["sublevelkey"]
>> del CacheStorage["toplevelkey.sublevelkey"]
>> CacheStorage.pop("toplevelkey.sublevelkey")
'another value'
```
Trying to delete non-existent items raises a KeyNotFoundError.

#### StorageView (`abllib.StorageView`)

Implements a read-only view on any loaded storage. It is useful to check whether a key exists in any of the storages.

The StorageView checks storages in the order in which they were initialized.

Example usage:

First the view needs to be imported:
```py
>> from abllib import StorageView
```

Presence of keys can be checked in multiple ways:
```py
>> "toplevelkey" in StorageView
True
>> "toplevelkey.sublevelkey" in StorageView
True
>> StorageView.contains("toplevelkey")
True
>> in StorageView.contains("toplevelkey.sublevelkey")
True
```

Items can be retrieved in multiple ways:
```py
>> StorageView["mykey"]
'myvalue'
>> StorageView.get("mykey")
'myvalue'
>> StorageView["toplevelkey"]["sublevelkey"]
'another value'
>> StorageView["toplevelkey.sublevelkey"]
'another value'
>> StorageView.get("toplevelkey.sublevelkey")
'another value'
>> StorageView.get("nonexistent.key", default=42)
42
```

Multiple items can also be retrieved at once:
```py
>> StorageView.keys()
['mykey', 'toplevelkey', 'specialvalue']
>> StorageView.values()
['myvalue', {'sublevelkey': 'another value'}, <unlocked _thread.lock object at 0x000002831830E980>]
>> StorageView.items()
[('mykey', 'myvalue'), ('toplevelkey', {'sublevelkey': 'another value'}), ('specialvalue', <unlocked _thread.lock object at 0x000002831830E980>)]
```

There also exists a way to check whether an item and a key matches a certain value:
```py
>> StorageView.contains_item("toplevelkey.sublevelkey", "another value")
True
>> # is equal to:
>> StorageView["toplevelkey.sublevelkey"] == "another value"
True
```

### 10. Function wrappers (`abllib.wrapper`)

This module contains general-purpose [wrappers](https://www.geeksforgeeks.org/function-wrappers-in-python/).

#### Singleuse functions (`abllib.wrapper.singleuse`)

The singleuse wrapper can be applied to functions to make them single-useable.
If an already called function is called again, an CalledMultipleTimesError is raised.

Example usage:
```py
>> from abllib.wrapper import singleuse
>> @singleuse
.. def my_func(arg):
    print(arg)
>> my_func("hello world")
hello world
>> my_func("hello world")
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
abllib.error._general.CalledMultipleTimesError: The function can only be called once
```

If an error occurred during function execution, the function can be called again.
```py
>> from abllib.wrapper import singleuse
>> @singleuse
.. def my_func(arg):
    raise FileNotFoundError()
>> my_func("hello world")
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
    raise FileNotFoundError()
>> my_func("hello world")
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
    raise FileNotFoundError()
```

#### Custom lock (`abllib.wrapper.Lock`)

The wrapper module contains a modified version of threading.Lock.
The .acquire method now accepts None for a timeout.

Additionally, releasing the lock while it is not locked does not raise an error.

#### Custom Semaphore (`abllib.wrapper.Semaphore`)

The wrapper module also contains a custom Semaphore class based on threading.BoundedSemaphore.
It now contains a .locked method which returns whether it is held at least once.

The semaphore is initialized with the maximum number of times it can be acquired simultaneously.
After that, future acquisitions result in an LockAcquisitionTimeoutError.
Releasing the semaphore while it is not locked does not raise an error.

The semaphore can be blocked, which halts all new acquisitions.

#### Lock wrappers

There are two classes which help with multi-threaded synchronisation:
* NamedLock
* namedSemaphore

NamedLock works like a normal [lock](https://en.wikipedia.org/wiki/Lock_(computer_science)), while NamedSemaphore works like a [semaphore](https://en.wikipedia.org/wiki/Semaphore_(programming)).

Creating a NamedLock and NamedSemaphore with the same name links them.
If the NamedLock is acquired and after that the NamedSemaphore gets acquired, it has to wait until the NamedLock is released.

Multiple NamedLock or NamedSemaphore can also be created with the same name.
This lets them share the same global state, so if one of them is acquired, all the others are acquired too.

If a NamedLock or NamedSemaphore is applied to a function, its lock is acquired before the function executes and is released afterwards.

Example usage:
```py
>> from time import sleep
>> from abllib.wrapper import NamedLock
>> @NamedLock("MyLockName")
.. def do_something(duration):
..     sleep(duration)
>> do_something(10) #this holds the "MyLockName"-lock for ten seconds
```

The default behaviour is to wait until the lock can be acquired. If a timeout parameter is provided, an LockAcquisitionTimeoutError is raised if the acquisition takes too long. The timeout is specified in seconds.
```py
>> from time import sleep
>> from abllib.wrapper import NamedLock
>> @NamedLock("MyLockName", timeout=5)
.. def do_something(duration):
..     sleep(duration)
>> NamedLock("MyLockName").acquire() #this holds the "MyLockName"-lock
>> do_something(10) #the "MyLockName"-lock is already held
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
abllib.error._general.LockAcquisitionTimeoutError: The requested lock could not be acquired in time
```

#### Deprecated marker (`abllib.wrapper.deprecated`)

The deprecate wrapper marks a function or class as deprecated.
If a deprecated function is called, a deprecation warning is logged using the current root logger.

```py
>> from abllib.wrapper import deprecated
>> @deprecated
.. def my_func(arg):
    print(arg)
>> my_func("hello world")
The functionality my_func is deprecated but used here: File "c:\Users\youruser\abllib\src\main.py",
line 27, in <module>
hello world
```

It can also be applied explicitly as a warning or error:
```py
>> from abllib.wrapper import deprecated
>> @deprecated.warning
.. def my_func(arg):
    print(arg)
>> my_func("hello world")
The functionality my_func is deprecated but used here: File "c:\Users\youruser\abllib\src\main.py",
line 27, in <module>
hello world
>> @deprecated.error
.. def my_func(arg):
    print(arg)
>> my_func("hello world")
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
abllib.error._general.DeprecatedError: The functionality 'my_func' is deprecated but used here: File "c:\Users\youruser\abllib\src\main.py", line 27, in <module>
```

A custom deprecation message can also be supplied:
```py
>> from abllib.wrapper import deprecated
>> @deprecated.warning("my_func is deprecated, use my_other_func instead")
.. def my_func(arg):
    print(arg)
>> my_func("hello world")
my_func is deprecated, use my_other_func instead
hello world
>> @deprecated.error("my_func is deprecated, use my_other_func instead")
.. def my_func(arg):
    print(arg)
>> my_func("hello world")
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
abllib.error._general.DeprecatedError: my_func is deprecated, use my_other_func instead
```

#### Log function error (`abllib.wrapper.log_error`)

The log_error wrapper can be applied to functions to send any occurred exception to the default logger.

First, logging needs to be setup. In this example, this librarys' logging is used.
```py
>> from abllib import log
>> log.initialize()
>> log.add_console_handler()
```

Example usage:
```py
>> from abllib.wrapper import log_error
>> @log_error
.. def my_func(arg):
..   raise RuntimeError("my message")
>> try:
..   my_func("hello world")
.. except:
..   pass
[2025-07-29 11:58:54] [ERROR   ] root: my message
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
RuntimeError: my message
```

A custom logger can also be specified by either passing the name or logging.Logger object.
```py
>> logger = log.get_logger("mymodulelogger")
>> from abllib.wrapper import log_error
>> @log_error(logger)
.. def my_func(arg):
..   raise RuntimeError("my message")
>> try:
..   my_func("hello world")
.. except:
..   pass
[2025-07-29 11:58:54] [ERROR   ] mymodulelogger: my message
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
RuntimeError: my message
```

Instead of logging, a custom handler function can be provided, which will be passed the error message.
```py
>> from abllib.wrapper import log_error
>> @log_error(handler=lambda exc: print(exc))
.. def my_func(arg):
..   raise RuntimeError("my message")
>> try:
..   my_func("hello world")
.. except:
..   pass
RuntimeError: my message
```

#### Log function arguments and return value (`abllib.wrapper.log_io`)

The log_io wrapper can be applied to functions to send all arguments, keyword arguments and return values to the default logger.

First, logging needs to be setup. In this example, this librarys' logging is used.
```py
>> from abllib import log
>> log.initialize()
>> log.add_console_handler()
```

Example usage:
```py
>> from abllib.wrapper import log_io
>> @log_io
.. def my_func(arg):
..   return False
>> _ = my_func("hello world")
[2025-07-29 11:58:54] [ERROR   ] root: func: my_func
[2025-07-29 11:58:54] [ERROR   ] root: in  : "hello world"
[2025-07-29 11:58:54] [ERROR   ] root: out : False
```

A custom logger can also be specified by either passing the name or logging.Logger object.
```py
>> logger = log.get_logger("mymodulelogger")
>> from abllib.wrapper import log_io
>> @log_io(logger)
.. def my_func(arg):
..   return False
>> _ = my_func(arg="Test")
[2025-07-29 11:58:54] [ERROR   ] mymodulelogger: func: my_func
[2025-07-29 11:58:54] [ERROR   ] mymodulelogger: in  : arg="hello world"
[2025-07-29 11:58:54] [ERROR   ] mymodulelogger: out : False
>> @log_io("CustomLogger")
.. def my_func(arg):
..   return False
>> _ = my_func(111)
[2025-07-29 11:58:54] [ERROR   ] CustomLogger: func: my_func
[2025-07-29 11:58:54] [ERROR   ] CustomLogger: in  : 111
[2025-07-29 11:58:54] [ERROR   ] CustomLogger: out : False
```

#### Log function execution time (`abllib.wrapper.timeit`)

The timeit wrapper can be applied to functions to log the functions' execution time.

First, logging needs to be setup. In this example, this librarys' logging is used.
We'll also import the sleep function.
```py
>> from abllib import log
>> log.initialize(log.LogLevel.DEBUG)
>> log.add_console_handler()
>> from time import sleep
```

Example usage using the root logger:
```py
>> from abllib.wrapper import timeit
>> @timeit
.. def my_func(delay):
..   sleep(delay)
>> my_func(0.001)
[2025-07-30 12:33:49] [DEBUG   ] root: myfunc: 1.44 ms elapsed
>> my_func(0.37)
[2025-07-30 12:33:50] [DEBUG   ] root: myfunc: 370.71 ms elapsed
>> my_func(5)
[2025-07-30 12:33:55] [DEBUG   ] root: myfunc: 5.00 s elapsed
```

A custom logger can also be specified by either passing the name or logging.Logger object.
```py
>> logger = log.get_logger("mymodulelogger")
>> from abllib.wrapper import timeit
>> @timeit(logger)
.. def my_func(delay):
..   sleep(delay)
>> my_func(0.002)
[2025-07-30 12:33:49] [DEBUG   ] root: myfunc: 2.25 ms elapsed
>> @timeit("CustomLogger")
.. def my_func(delay):
..   sleep(delay)
>> my_func(0.002)
[2025-07-30 12:33:49] [DEBUG   ] root: myfunc: 2.28 ms elapsed
```

## Development environment setup

If you want to contribute to this project, you need to set up your local environment.

### Clone the repository

Run the command
```bash
git clone https://github.com/Ableytner/abllib
cd abllib
```
in your terminal.

### Install pip packages

To install all optional as well as development python packages, run the following commands in the project root.

Windows:
```bash
py -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
```

Linux:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Git pre-commit hooks

Pre-commit hooks are used to check and autofix formatting issues and typos before you commit your changes.
Once installed, they run automatically if you run `git commit ...`.

Using these is optional, but encouraged.

```bash
pip install pre-commit
pre-commit install
```

To verify the installation and run all checks:
```bash
pre-commit run --all-files
```
