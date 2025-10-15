# -*- encoding: utf-8 -*-
"""
Copyright (c) 2025
The module is necessary for the MISP adapter to function.
"""
import json
import os
import signal
from datetime import datetime, timedelta
from functools import wraps


def _check_pid(pid):
    """Check For the existence of a unix pid."""
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True


def pid_handler(filepath, logger):
    """
    PIDFILE=${APP_ROOT}/store/poll.pid
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                pid = None
                if os.path.isfile(filepath):
                    with open(filepath, "r") as file:
                        pid = int(file.read())
                        if not _check_pid(pid):
                            pid = None
                        else:
                            os.kill(pid, signal.SIGKILL)
                            pid = None

                if not pid:
                    pid = str(os.getpid())
                    with open(filepath, "w") as file:
                        file.write(pid)

                return func(*args, **kwargs)

            except Exception as e:
                logger.exception("PID error.")
                raise Exception("PID error.")

        return wrapper

    return decorator


def _is_cache_expired(date, ttl):
    return datetime.now() - timedelta(days=ttl) >= datetime.strptime(
        date, "%Y-%m-%d"
    )


def cache_data(cache_dir, cache_file, ttl):
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not os.path.exists(cache_dir):
                os.mkdir(cache_dir)
            cache_file_path = os.path.join(cache_dir, cache_file)
            if os.path.exists(cache_file_path):
                with open(cache_file_path, "r") as cache_dump:
                    cache = json.load(cache_dump)
                if cache:
                    if not _is_cache_expired(cache.get("dateSaved"), ttl):
                        return cache.get("data")

            new_data = func(*args, **kwargs)
            with open(cache_file_path, "w") as cache_dump:
                cache = {
                    "dateSaved": datetime.now().strftime("%Y-%m-%d"),
                    "data": new_data,
                }
                json.dump(cache, cache_dump)

            return new_data

        return wrapper

    return decorator
