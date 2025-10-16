"""Tests for the datetimesub process function."""
import datetime
import unittest

import pandas as pd

from sportsfeatures.datetimesub_process import datetimesub_process
from sportsfeatures.identifier import Identifier
from sportsfeatures.entity_type import EntityType


class TestDatetimesubProcess(unittest.TestCase):

    def test_datetimesub_process(self):
        dt_other_column = "dt_other"
        identifier = Identifier(EntityType.TEAM, "team/0/id", [dt_other_column], "team/0/")
        dt_column = "dt"
        df = pd.DataFrame(data={
            dt_column: [datetime.datetime(2022, 1, 1), datetime.datetime(2022, 1, 2), datetime.datetime(2022, 1, 3)],
            dt_other_column: [datetime.datetime(2022, 1, 1, tzinfo=datetime.timezone.utc), datetime.datetime(2022, 1, 2, tzinfo=datetime.timezone.utc), datetime.datetime(2022, 1, 3, tzinfo=datetime.timezone.utc)],
        })
        datetimesub_process(df, dt_column, [identifier], None)
