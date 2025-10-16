def default_exception_handler(e: Exception, retry_config: dict, *args, **kwargs):
    """Base function for handling exception
    Args:
        e(Exception): the exception to raise
        retry_config(dict): the retry config from the decorator

    Raises:
        Exception: the exception supplied.
    """
    raise e
