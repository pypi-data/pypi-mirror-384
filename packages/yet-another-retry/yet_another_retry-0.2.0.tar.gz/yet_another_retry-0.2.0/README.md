# yet-another-retry
This package is inspired by other retry-packages.  
It takes a slightly different approach to certain things however to allow the decorated function to know it is being retried and take action based on a retry_config.    
The package uses only python standard library and has no external dependencies.  
  
It allows for custom handlers to be created for retry and exception handling.  
Handlers can log or do anything user wants them to do and will also recieve the retry_config.

# Install
```bash
python -m pip install yet-another-retry
```
then import with:
```python
from yet-another-retry import retry
```

# Usage
### Basic usage
This is not much different from other retry packages.  
Uses the decorator with all default values  
tries=5  
retry_delay_seconds=0  

```python
from yet_another_retry import retry

@retry()
def my_function():
  ...

```
### Changing number of tries
Since we have to know in advance how many tries to do, this is a parameter directly to the decorator
```python
from yet_another_retry import retry

@retry(tries=5)
def my_function():
  ...
```

### Changing number of seconds to sleep in default retry handler 
The default retry handler has a parameter "retry_delay_seconds" that can be modified as an extra_kwarg.

```python
from yet_another_retry import retry

@retry(extra_kwargs={"retry_delay_seconds": 10})
def my_function():
  ...

```

# Handlers
The decorator uses a concept of handlers for retries and exceptions.  
A handler is just a function with some requirements.  
The handler will be called on retries and final exception.  
Both types of handlers must have the following parameters:
- e: Exception
- retry_config: dict
- *args
- **kwargs

It can also contain extra parameters that can be submitted as extra_kwargs dict to the decorator.


## Retry handlers
A retry handler is expected to return a float or integer that the retry function will sleep for before the next attempt.  
The default retry_handler has a parameter `retry_delay_seconds` that can be sent as an extra_kwarg to the decorator to modify the nr of seconds it sleeps for.

See examples in the examples folder

To use a custom retry handler:
```python
from yet_another_retry import retry

def custom_retry_handler(e: Exception, retry_config: dict, *args, **kwargs):
    sleep_time = 1
    return sleeptime
    
    
@retry(retry_handler=custom_retry_handler)
def my_function():
  ...

```

## Exception handlers
A exception handler triggers on raising exception.
Works the same way as retry_handler except is not expected to return anything.
The default raise_exception handler just raises the exception.
If no exception is raised by a custom exception_handler the decorator will raise the error after the function.

See examples in the examples folder

To use a custom exception handler:
```python
from yet_another_retry import retry

def custom_exception_handler(e: Exception, retry_config: dict, *args, **kwargs):
    ... do things 
    raise e
    
    
@retry(exception_handler=custom_exception_handler)
def my_function():
  ...

```