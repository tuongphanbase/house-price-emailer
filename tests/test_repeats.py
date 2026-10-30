"""Run: python -m unittest discover tests

A listing already emailed must not go out again for REPEAT_AFTER_DAYS days
(across runs and days), and the state file written before that rule existed
must still be read.
"""
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_settings import load  # noqa: E402

emailer = load()


class RecentlySent(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.dir.name, "last_price.json")
        self.today = date.fromisoformat(emailer._today_str())

    def tearDown(self):
        self.dir.cleanup()

    def day(self, n):
        return (self.today - timedelta(days=n)).isoformat()

    def test_keeps_listings_sent_in_the_last_days_only(self):
        sent = {"a": self.day(0), "b": self.day(6), "c": self.day(7), "d": self.day(30)}
        emailer.save_last_hash("h", sent=sent, path=self.path)
        self.assertEqual(emailer.load_last_hash(self.path), "h")
        self.assertEqual(emailer.load_recently_sent(self.path, days=7), {"a": self.day(0), "b": self.day(6)})

    def test_reads_the_old_one_day_format(self):
        with open(self.path, "w") as f:
            json.dump({"hash": "h", "date": self.day(1), "sent_ids": ["x", "y"]}, f)
        self.assertEqual(emailer.load_recently_sent(self.path, days=7), {"x": self.day(1), "y": self.day(1)})

    def test_missing_or_unreadable_state_means_nothing_was_sent(self):
        self.assertEqual(emailer.load_recently_sent(os.path.join(self.dir.name, "missing.json")), {})
        with open(self.path, "w") as f:
            f.write("{not json")
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(emailer.load_recently_sent(self.path), {})


if __name__ == "__main__":
    unittest.main()
