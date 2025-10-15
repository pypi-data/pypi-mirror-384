#!/usr/bin/env python

"""Tests for `chinadaily` package."""
import os
import unittest
from datetime import datetime

from chinadaily.chinadaily import download


class TestChinadaily(unittest.TestCase):
    """Tests for `chinadaily` package."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_000_something(self):
        """Test something."""

    # todo(@yarving): implement test trigger
    @unittest.skipUnless(os.getenv('download'), "skip download due to network slowing")
    def test_download(self):
        """Test download"""
        now = datetime.now()
        filename = download(now)

        print(f'{filename} download successfully.')
        self.assertTrue(os.path.exists(filename))
        self.assertTrue(os.path.isfile(filename))

        os.remove(filename)
        self.assertFalse(os.path.exists(filename))
