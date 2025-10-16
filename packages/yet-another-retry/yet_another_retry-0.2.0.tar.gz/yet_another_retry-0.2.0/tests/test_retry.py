from yet_another_retry import retry


def test_retry():

    try:
        assert function_to_retry()
    except:
        assert False


@retry(tries=5)
def function_to_retry(retry_config: dict):

    attempt = retry_config["attempt"]
    if attempt == 5:
        return True

    raise Exception("This is an exception")
