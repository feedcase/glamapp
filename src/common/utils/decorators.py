import asyncio
from functools import wraps
from types import CoroutineType
from typing import Optional


def waiter_wrapper(top_attempts: int = 10,
                   sleep_time: int = 1,
                   exp_exc: Optional[list] = None):
    """
    Tries to get result for top_attempts times

    :param top_attempts: max count of tries
    :param sleep_time: waiting time between attempts
    :param exp_exc: error to be ignored

    :returns:
    """
    exp_exc = exp_exc or []

    def wrapper(func):
        @wraps(func)
        async def inner(*args, **kwargs):
            attempts = 0
            while True:
                attempts += 1
                try:
                    result = func(*args, **kwargs)
                    if isinstance(result, CoroutineType):
                        result = await result
                except Exception as e:
                    if attempts >= top_attempts or type(e) in exp_exc:
                        raise e
                    await asyncio.sleep(sleep_time)
                    continue
                else:
                    return result
        return inner

    return wrapper
