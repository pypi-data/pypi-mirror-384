import glob
import os
import re
import shutil
from datetime import datetime, timedelta
from unittest import TestCase

import freezegun
import openmodule.utils.schedule as schedule
from dateutil.tz import UTC, gettz, tzlocal

from openmodule.config import settings
from openmodule.utils.cleanup import _file_cleanup, schedule_file_cleanup
from openmodule.utils.misc_functions import utcnow


class CleanupTest(TestCase):
    test_dir = "/tmp/cleanup_test/"

    def setUp(self):
        super().setUp()
        try:
            shutil.rmtree(self.test_dir)
        except OSError:
            pass
        os.makedirs(self.test_dir)

    def test_cleanup_file_pattern_and_retention_time(self):
        open(os.path.join(self.test_dir, "a.png"), 'w').close()
        open(os.path.join(self.test_dir, "a2.png"), 'w').close()
        open(os.path.join(self.test_dir, "b.png"), 'w').close()
        current_time = utcnow()

        # 1 minute less than retention time old -> no delete
        delta = timedelta(days=3)
        with freezegun.freeze_time(current_time + delta - timedelta(minutes=1)):
            _file_cleanup("/tmp/cleanup_test/a*.png", delta)
            self.assertEqual(3, len(glob.glob("/tmp/cleanup_test/*.png")))

        # older than retention time old -> delete according to pattern -> only b.png left
        with freezegun.freeze_time(current_time + delta + timedelta(minutes=1)):
            _file_cleanup("/tmp/cleanup_test/a*.png", delta)
            self.assertEqual(["/tmp/cleanup_test/b.png"], glob.glob("/tmp/cleanup_test/*.png"))

    def test_recursive(self):
        os.makedirs("/tmp/cleanup_test/d1/d2/d3/d4")
        open(os.path.join(self.test_dir, "/tmp/cleanup_test/a.png"), 'w').close()
        open(os.path.join(self.test_dir, "/tmp/cleanup_test/d1/a.png"), 'w').close()
        open(os.path.join(self.test_dir, "/tmp/cleanup_test/d1/d2/a.png"), 'w').close()
        open(os.path.join(self.test_dir, "/tmp/cleanup_test/d1/d2/d3/a.png"), 'w').close()
        open(os.path.join(self.test_dir, "/tmp/cleanup_test/d1/d2/d3/d4/a.png"), 'w').close()

        self.assertEqual(5, len(glob.glob("/tmp/cleanup_test/**/*.png", recursive=True)))
        with freezegun.freeze_time(utcnow() + timedelta(days=2)):
            _file_cleanup("/tmp/cleanup_test/*/a.png", timedelta(days=1))  # delete only .../d1/a.png
            self.assertEqual(4, len(glob.glob("/tmp/cleanup_test/**/*.png", recursive=True)))

            _file_cleanup("/tmp/cleanup_test/**/a.png", timedelta(days=1))  # delete all
            self.assertEqual(0, len(glob.glob("/tmp/cleanup_test/**/*.png", recursive=True)))

    def test_exclude_regex(self):
        os.makedirs("/tmp/cleanup_test/vehicle_images/")
        os.makedirs("/tmp/cleanup_test/vehicle_loop/")
        os.makedirs("/tmp/cleanup_test/new_track/")
        open(os.path.join(self.test_dir, "/tmp/cleanup_test/vehicle_images/a.jpg"), 'w').close()
        open(os.path.join(self.test_dir, "/tmp/cleanup_test/vehicle_loop/b.jpg"), 'w').close()
        open(os.path.join(self.test_dir, "/tmp/cleanup_test/new_track/c.jpg"), 'w').close()

        with freezegun.freeze_time(utcnow() + timedelta(days=2)):
            _file_cleanup("/tmp/cleanup_test/*/*.jpg", timedelta(days=1), re.compile('.*/vehicle_images/.*'))
            self.assertEqual(["/tmp/cleanup_test/vehicle_images/a.jpg"],
                             glob.glob("/tmp/cleanup_test/*/*.jpg", recursive=True))

    def test_scheduling(self):
        scheduler = schedule.Scheduler()
        open(os.path.join(self.test_dir, "1.png"), 'w').close()
        open(os.path.join(self.test_dir, "2.png"), 'w').close()

        # 2 days to ensure we delete even if we hit an unlucky race condition when testcase is run
        base_time = (utcnow() + timedelta(days=2))\
            .replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=gettz(settings.TIMEZONE))\
            .astimezone(UTC)
        with freezegun.freeze_time(base_time, tz_offset=datetime.now(tz=tzlocal()).utcoffset()):
            settings.NAME = "om_service_test_1"  # offset 17 minutes
            schedule_file_cleanup(scheduler, "/tmp/cleanup_test/1.png", timedelta(0))
            settings.NAME = "om_service_test_2"  # offset 1 minute
            schedule_file_cleanup(scheduler, "/tmp/cleanup_test/2.png", timedelta(0))

        # 2:00 -> no job should be run -> 2 files present
        with freezegun.freeze_time(base_time + timedelta(hours=2),
                                   tz_offset=datetime.now(tz=tzlocal()).utcoffset()):
            scheduler.run_pending()
            self.assertEqual(2, len(glob.glob("/tmp/cleanup_test/*.png")))
        # 2:01 -> 2.png should be deleted because job ran
        with freezegun.freeze_time(base_time + timedelta(hours=2, minutes=1),
                                   tz_offset=datetime.now(tz=tzlocal()).utcoffset()):
            scheduler.run_pending()
            self.assertEqual(["/tmp/cleanup_test/1.png"], glob.glob("/tmp/cleanup_test/*.png"))
        # 2:16 -> no more deletions
        with freezegun.freeze_time(base_time + timedelta(hours=2, minutes=16),
                                   tz_offset=datetime.now(tz=tzlocal()).utcoffset()):
            scheduler.run_pending()
            self.assertEqual(["/tmp/cleanup_test/1.png"], glob.glob("/tmp/cleanup_test/*.png"))
        # 2:17 -> 1.png should be deleted because job ran
        with freezegun.freeze_time(base_time + timedelta(hours=2, minutes=17),
                                   tz_offset=datetime.now(tz=tzlocal()).utcoffset()):
            scheduler.run_pending()
            self.assertEqual([], glob.glob("/tmp/cleanup_test/*.png"))
