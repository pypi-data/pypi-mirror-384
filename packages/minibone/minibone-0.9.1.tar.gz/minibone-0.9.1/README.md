# minibone

[![Check](https://github.com/erromu/minibone/actions/workflows/python-check.yml/badge.svg)](https://github.com/erromu/minibone/actions/workflows/python-check.yml)  [![Deploy](https://github.com/erromu/minibone/actions/workflows/python-publish.yml/badge.svg)](https://github.com/erromu/minibone/actions/workflows/python-publish.yml) [![PyPI version](https://badge.fury.io/py/minibone.svg)](https://pypi.org/project/minibone)

minibone is an easy to use yet powerful boiler plate for multithreading, multiprocessing and others:

- __Config__: To handle configuration settings
- __Daemon__: To run a periodical task in another thread
- __Emailer__: To send emails in concurrent threads
- __HTMLBase__: To render html using snippets and toml configuration file in async mode
- __HTTPt__: HTTP client to do concurrent requests in threads
- __Logging__: To setup a logger friendly with filerotation
- __IOThreads__: To run concurrent tasks in threads
- __PARProcesses__: To run parallel CPU-bound tasks
- __Storing__: To queue and store files periodically in a thread (queue and forget)

It will be deployed to PyPi when a new release is created

## Installation

```shell
pip install minibone
```

## Config

Handle configuration settings in memory and/or persist them into toml/yaml/json formats

```python
from minibone.config import Config

# Create a new set of settings and persist them
cfg = Config(settings={"listen": "localhost", "port": 80}, filepath="config.toml")	
cfg.add("debug", True)	
cfg.to_toml()

# Load settings from a file. Defaults can be set. More information: help(Config.from_toml)
cfg2 = Config.from_toml("config.toml")

# also there are async counter part methods
import asyncio

cfg3 = asyncio.run(Config.aiofrom_toml("config.toml"))
```

Usually config files are editted externaly then loaded as read only on your code, so in such case, you may want to subclass Config for easier usage

```python
from minibone.config import Config

class MyConfig(Config):

    def __init__(self):
        defaults = {"main": {"listen": "localhost", "port": 80}}
        settings = Config.from_toml(filepath="config.toml", defaults=defaults)
        super().__init__(settings=settings)

    @property
    def listen(self) -> str:
        return self["main"]["listen"]

    @property
    def port(self) -> int:
        return self["main"]["port"]

if __name__ == "__main__":
    cfg = MyConfig()
    print(cfg.port)
    # it will print the default port value if not port setting was defined in config.toml
```

## Daemon

It is just another python class to run a periodical task in another thread. It can be used in two modes: subclasing and callback

### Usage as SubClass mode

- Subclass Daemon
- call super().__init__() in yours
- Overwrite on_process method with yours
- Add logic you want to run inside on_process
- Be sure your methods are safe-thread to avoid race condition
- self.lock is available for lock.acquire / your_logic / lock.release
- call start() method to keep running on_process in a new thread
- call stop() to finish the thread

Check [sample_clock.py](https://github.com/erromu/minibone/blob/main/samples/sample_clock.py) for a sample

### Usage as callback mode

- Instance Daemon by passing a callable
- Add logic to your callable method
- Be sure your callable is safe-thread to avoid race condition
- call start() method to keep running callable in a new thread
- call stop() to finish the thread

Check [sample_clock_callback.py](https://github.com/erromu/minibone/blob/main/samples/sample_clock_callback.py) for a sample

## AsyncDaemon

It is just another python class to run a periodical task using asyncio instead of threads. It can be used in two modes: subclasing and callback

### Usage as SubClass mode

- Subclass AsyncDaemon
- call super().__init__() in yours
- Overwrite on_process method with yours (must be async)
- Add logic you want to run inside on_process
- Be sure your methods are async-safe to avoid race condition
- self.lock is available for async with self.lock context manager
- call await start() method to keep running on_process as a task
- call await stop() to finish the task

Check [sample_async_clock.py](https://github.com/erromu/minibone/blob/main/samples/sample_async_clock.py) for a sample

### Usage as callback mode

- Instance AsyncDaemon by passing an async callable
- Add logic to your callable method (must be async)
- Be sure your callable is async-safe to avoid race condition
- call await start() method to keep running callable as a task
- call await stop() to finish the task

Check [sample_async_clock_callback.py](https://github.com/erromu/minibone/blob/main/samples/sample_async_clock_callback.py) for a sample

## Logging

Setup a logger using UTC time that outputs logs to stdin or to a file.
It is friendly to filerotation (when setting output to a file)

```python
import logging

from minibone.logging import setup_log

if __name__ == "__main__":

    # setup_log must be called only once in your code.
    # So you have to choice if logging to stdin or to a file when calling it

    setup_log(level="INFO")
    logging.info('This is a log to the stdin')

    # or call the next lines instead if you want to log into a file
    # setup_log(file="sample.log", level="INFO")
    # logging.info('yay!')
```

## Contribution

- Feel free to clone this repository and send any pull requests.
- Add issues if something is not working as expected.
