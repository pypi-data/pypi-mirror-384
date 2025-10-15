import glob
import hashlib
import os
import re
import time
from datetime import timedelta

from openmodule.utils.schedule import Scheduler

from openmodule.config import settings


def _file_cleanup(file_pattern: str, retention_time: timedelta, exclude_regex: re.Pattern | None = None):
    """
    removes files matching file_mask and older than retention_time and not matching exclude_regex if given
    """
    min_keep_time = time.time() - retention_time.total_seconds()
    fns = glob.glob(file_pattern, recursive=True)
    for fn in fns:
        if os.path.getmtime(fn) < min_keep_time and os.path.isfile(fn) \
                and not (exclude_regex and exclude_regex.match(fn)):
            os.remove(fn)


def schedule_file_cleanup(scheduler: Scheduler, file_pattern: str, retention_time: timedelta,
                          exclude_regex: re.Pattern | None = None):
    """
    schedules cleanup of files matching file_mask and older than retention_time at every day at 02:xx
    where xx is a service name dependent offset
    :param scheduler: scheduler where file cleanup is scheduled
    :param file_pattern: pattern for files (glob syntax) that files must match to be deleted
    :param retention_time: minimum age of file before its deleted
    :param exclude_regex: files matching exclude_regex are excluded even if they match file_pattern
    """
    service_name_hash = hashlib.sha256(settings.NAME.encode("utf-8")).hexdigest()
    random_offset = int(service_name_hash, 16) % 60

    scheduler.every().day.at(f"02:{random_offset:02}", settings.TIMEZONE).do(_file_cleanup, file_pattern,
                                                                             retention_time, exclude_regex)
