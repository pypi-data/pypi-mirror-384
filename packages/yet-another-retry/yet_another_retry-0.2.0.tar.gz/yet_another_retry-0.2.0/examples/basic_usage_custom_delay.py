from yet_another_retry import retry


@retry(tries=10, extra_kwargs={"retry_delay_seconds": 5})
def my_function():
    """This function will delay for 5 seconds and retry 10 as per config"""

    print("Raising an error")
    raise Exception("Raising an error")


my_function()
