from typing import Callable
import time
import inspect
from yet_another_retry.retry_handlers import default_retry_handler
from yet_another_retry.exception_handlers import default_exception_handler


def retry(
    retry_exceptions: Exception | tuple[Exception] = (Exception),
    fail_on_exceptions: Exception | tuple[Exception] = (),
    tries: int = 3,
    retry_handler: Callable = default_retry_handler,
    exception_handler: Callable = default_exception_handler,
    extra_kwargs: dict = {},
    raise_error: bool = True,
) -> Callable:
    """Decorator for retrying a function

    If the decorated function contains parameter named "retry_config" the decorator will pass the following dict as a parameter to the function:

    ```python
        retry_config = {
            "retry_exceptions": retry_exceptions,
            "fail_on_exceptions": fail_on_exception,
            "tries": tries,
            "op_kwargs": op_kwargs,
            "retry_handler": retry_handler,
            "exception_handler": exception_handler,
            "extra_kwargs": extra_kwargs,
            "raise_error": raise_error,
            "attempt": 1    # which attempt number currently running
        }

    ```

    Args:
        retry_exceptions(tuple[Exception]): An Exception or tuple of exceptions to retry. All other exceptions will fail. Defaults to (Exception) meaning all exceptions are retried unless this value is modified.
        fail_on_exceptions(tuple[Exception]): An Exception or tuple of exception to not retry but instead raise error if it occures. Defaults to ()
        tries(int): Maximum number of retries to attempt. Defaults to 3
        retry_handler(Callable): Callable function to run in case of retries. Defaults to default retry_handler function
        exception_handler(Callable): Callable function to run in case of erroring out, either by reaching max tries +1 or hitting a fail_on_exception exception. Defaults to default exception_handler function.
        extra_kwargs(dict): A dict of extra parameters to pass to the handlers.
                            If supplied will be passed to the handler as normal parameters as well as in the retry_config as "extra_kwargs".
        raise_error(bool): If set to false the decorator itself will not raise the error but expect the handler to do it. Default is True
    """

    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            retry_config = {
                "retry_exceptions": retry_exceptions,
                "fail_on_exceptions": fail_on_exceptions,
                "tries": tries,
                "retry_handler": retry_handler,
                "exception_handler": exception_handler,
                "extra_kwargs": extra_kwargs,
                "raise_error": raise_error,
                "attempt": 0,
            }
            # parameters from the decorated function
            # used to check if the decorated function has a "retry_config" parameter
            send_config = (
                True if "retry_config" in inspect.signature(func).parameters else False
            )

            for i in range(1, tries + 1):
                try:
                    if send_config:
                        kwargs["retry_config"] = retry_config
                        kwargs["retry_config"]["attempt"] = i
                    return func(*args, **kwargs)

                except fail_on_exceptions as e:
                    if exception_handler:
                        exception_handler(e, retry_config=retry_config, **extra_kwargs)
                    if raise_error:
                        raise e

                except retry_exceptions as e:
                    if i == tries:
                        if exception_handler:
                            exception_handler(
                                e, retry_config=retry_config, **extra_kwargs
                            )
                        if raise_error:
                            raise e
                    delay_seconds = retry_handler(
                        e, retry_config=retry_config, **extra_kwargs
                    )

                    # the return from the retry handler must be an int or a float
                    if not isinstance(delay_seconds, (int, float)):
                        raise TypeError(
                            f"The retry_handler did not return an int or float. Can not use {type(delay_seconds)} as input to sleep"
                        )
                    time.sleep(delay_seconds)

        return wrapper

    return decorator
