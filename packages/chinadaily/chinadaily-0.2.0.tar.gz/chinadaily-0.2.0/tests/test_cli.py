import unittest
from argparse import ArgumentError
from datetime import datetime
from unittest import TestCase

from chinadaily.cli import get_parser
from chinadaily.constants import CLI_DATE_FORMAT, CLI_MONTH_FORMAT, CLI_YEAR_FORMAT


class TestParser(TestCase):

    def test_date_not_given(self):

        # test positional parameter as:
        # - default
        # - specified date

        # test date range
        args = []
        parser = get_parser()
        parsed = parser.parse_args(args)

        self.assertEqual(len(parsed.date), 0, "date argument is not empty")
        self.assertListEqual(parsed.date, [], "date is not None")

    def test_specified_date(self):
        date = "20201010"
        args = [date, ]
        parser = get_parser()
        parsed = parser.parse_args(args)

        self.assertEqual(len(parsed.date), 1, "date argument is not one")
        self.assertEqual(parsed.date,
                         [datetime.strptime(date, CLI_DATE_FORMAT)],
                         f"parsed date is not match {date}")

    def test_wrong_date(self):
        date = "asdfasdf"
        args = [date, ]
        parser = get_parser()

        with self.assertRaises(SystemExit):
            parser.parse_args(args)

    def test_multiple_date_argument(self):
        """test more than 1 date passed in"""
        date1 = "20201010"
        date2 = "20201011"
        args = [date1, date2]
        parser = get_parser()
        parsed = parser.parse_args(args)

        self.assertEqual(len(parsed.date), 2, "date argument count is not 2")
        self.assertEqual(parsed.date,
                         [datetime.strptime(date1, CLI_DATE_FORMAT), datetime.strptime(date2, CLI_DATE_FORMAT)],
                         f"parsed date is not match")

    def test_force(self):
        args = []
        parser = get_parser()
        parsed = parser.parse_args(args)
        self.assertFalse(parsed.force)

        args = ["-f"]
        parser = get_parser()
        parsed = parser.parse_args(args)
        self.assertTrue(parsed.force)

        args = ["--force"]
        parser = get_parser()
        parsed = parser.parse_args(args)
        self.assertTrue(parsed.force)

    def test_optional_m(self):
        """test -m argument"""
        args = ["-m", "202010"]
        parser = get_parser()
        parsed = parser.parse_args(args)

        self.assertEqual(parsed.month,
                         datetime.strptime("202010", CLI_MONTH_FORMAT),
                         "month is not equal")

    def test_optional_month(self):
        """test --month argument"""
        args = ["--month", "202010"]
        parser = get_parser()
        parsed = parser.parse_args(args)

        self.assertEqual(parsed.month,
                         datetime.strptime("202010", CLI_MONTH_FORMAT),
                         "month is not equal")

    def test_invalid_month_argument(self):
        """test invalid month"""
        # invalid month as str
        args = ["-m", "asjkdlfa"]
        parser = get_parser()

        with self.assertRaises(SystemExit):
            parser.parse_args(args)

        # date as month
        args = ["-m", "20201010"]
        parser = get_parser()

        with self.assertRaises(SystemExit):
            parser.parse_args(args)

    def test_optional_y(self):
        """test -y argument"""
        args = ["-y", "2020"]
        parser = get_parser()
        parsed = parser.parse_args(args)

        self.assertEqual(parsed.year,
                         datetime.strptime("2020", CLI_YEAR_FORMAT),
                         "month is not equal")

    def test_optional_year(self):
        """test --year argument"""
        args = ["--year", "2020"]
        parser = get_parser()
        parsed = parser.parse_args(args)

        self.assertEqual(parsed.year,
                         datetime.strptime("2020", CLI_YEAR_FORMAT),
                         "month is not equal")

    def test_invalid_year_argument(self):
        """test invalid year argument"""
        args = ["-y", "asjkdlfa"]
        parser = get_parser()

        with self.assertRaises(SystemExit):
            parser.parse_args(args)

        # date as month
        args = ["-y", "20201010"]
        parser = get_parser()

        with self.assertRaises(SystemExit):
            parser.parse_args(args)

    @unittest.skip("not support yet")
    def test_mutex_argumetn(self):
        """date, month, year are mutex"""
        parser = get_parser()

        # date and month mutex test
        args = ["20201010", "-m", "202010"]
        with self.assertRaises(SystemExit):
            parser.parse_args(args)
        args = ["20201010", "20201011", "-m", "202010"]
        with self.assertRaises(SystemExit):
            parser.parse_args(args)

        # date and year mutex test
        args = ["20201010", "-y", "2020"]
        with self.assertRaises(SystemExit):
            parser.parse_args(args)

        # month and year mutex test
        args = ["-m", "202010", "-y", "2020"]
        with self.assertRaises(SystemExit):
            parser.parse_args(args)


