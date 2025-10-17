# tstring-logger
Python logging with template strings with support for conditional (lazy) execution of functions in log messages. 

Provides **TStringLogger(logging.Logger)** and sets it as the default logger class upon `import tstring_logger`

A **Template String** may embed function calls with a *!fn* format specifier. They will only be executed if the logger is active.

## Example ##
```
import logging
import tstring_logger

def expensive_function(x):
    time.sleep(1)
    return 2 * x

logging.basicConfig()
lg = logging.getLogger("demo")
hour = datetime.datetime.now().hour
print(1)
lg.debug(test := t"The thing happened with {expensive_function:!fn} {7} at hour {hour}.")
print(2)
lg.setLevel(logging.DEBUG)
lg.debug(test)
print(3)
```

will quickly print 1 and 2, then pause a second before 3 appears after *DEBUG:demo:The thing happened with 14 at hour 16.*
Since *expensive_function* takes a single argument, the 7 is passed to the function while *hour* renders in the usual way.

The logger uses the *embed* function of [tstring-util](https://pypi.org/project/tstring-util/). 

