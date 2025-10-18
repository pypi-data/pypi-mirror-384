from os import getenv
from time import sleep
from traceback import print_exc
from functools import wraps
from gitlab_ps_utils.logger import myLogger

log = myLogger(__name__, app_path=getenv('APP_PATH', '.'),
               log_name=getenv('APP_NAME', 'application'))


def stable_retry(original_function=None, *, ExceptionType=Exception, retries=3, delay=5, backoff=1.20):
    '''
        A decorator to assist with timing on functions. If your function uses
        this decorator and raises an error, this decorator will retry the function
        {retries} times, with a {delay} in seconds, with the delay
        time being increased by the {backoff} amount per retry.
    '''
    def _retry(function, ExceptionType=ExceptionType,
               retries=retries, delay=delay, backoff=backoff):
        @wraps(function)
        def wrapped_function(*args, **kwargs):
            mretries, mdelay = retries, delay
            while mretries >= 0:
                exception_thrown = False
                try:
                    return function(*args, **kwargs)
                except ExceptionType as e:
                    exception_thrown = True
                    log.error(print_exc())
                    log.error(
                        f"\nError: '[{ExceptionType}]{e}'\n'{function.__name__}()' from module '{function.__module__}' with arguments '{args}' and kwargs '{kwargs}' failed."
                        f"\nRetrying in {int(mdelay)} seconds..."
                    )
                finally:
                    if exception_thrown:
                        sleep(mdelay)
                        mretries -= 1
                        mdelay *= backoff
            log.error(
                f"{function.__name__} failed after '{retries}' retr{'y' if retries == 1 else 'ies'}")
        return wrapped_function
    if original_function:
        return _retry(original_function)
    return _retry


def token_rotate(function):
    """
        Decorator used to rotate token used from a list

        This decorator assumes args[0] is `self` in a class
        and the class needs to have a `token_array` instance
        attribtue and `index` class attribute
    """
    @wraps(function)
    def f_rotate(*args, **kwargs):
        tokens = args[0].token_array
        if tokens and len(tokens) > 1:
            args[0].index += 1
            index = args[0].index % len(tokens)
            log.debug(f"Rotating to token index {index}")
            args[0].token = tokens[index]
        elif not tokens:
            log.info("No tokens provided")
        return function(*args, **kwargs)
    return f_rotate
