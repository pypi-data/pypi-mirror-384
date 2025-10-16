from yet_another_retry import retry


@retry()
def my_function(retry_config: dict):
    print(f"This is attempt number: {retry_config['attempt']}")
    raise Exception("This is an exception")


my_function()
