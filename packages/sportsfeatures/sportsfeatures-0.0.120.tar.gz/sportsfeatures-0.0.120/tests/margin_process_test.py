"""Tests for the margin process function."""
import datetime
import os
import unittest

import pandas as pd
from pandas.testing import assert_frame_equal

from sportsfeatures.margin_process import margin_process
from sportsfeatures.identifier import Identifier
from sportsfeatures.entity_type import EntityType


class TestMarginProcess(unittest.TestCase):

    def setUp(self):
        self.dir = os.path.dirname(__file__)

    def test_margin_process(self):
        team_0_column_prefix = "teams/0"
        team_1_column_prefix = "teams/1"
        dt_column = "dt"
        team_0_id_column = team_0_column_prefix + "/id"
        team_0_points_column = team_0_column_prefix + "/points"
        team_0_id = "0"
        team_1_id_column = team_1_column_prefix + "/id"
        team_1_points_column = team_1_column_prefix + "/points"
        team_1_id = "1"
        df = pd.DataFrame(data={
            dt_column: [datetime.datetime(2022, 1, 1), datetime.datetime(2022, 1, 2), datetime.datetime(2022, 1, 3)],
            team_0_id_column: [team_0_id, team_1_id, team_0_id],
            team_0_points_column: [10.0, 20.0, 30.0],
            team_1_id_column: [team_1_id, team_0_id, team_1_id],
            team_1_points_column: [20.0, 40.0, 60.0],
        })
        identifiers = [
            Identifier(
                EntityType.TEAM,
                team_0_id_column,
                [],
                team_0_column_prefix,
                points_column=team_0_points_column,
            ),
            Identifier(
                EntityType.TEAM,
                team_1_id_column,
                [],
                team_1_column_prefix,
                points_column=team_1_points_column,
            ),
        ]
        new_df = margin_process(df, identifiers)
        expected_df = pd.read_parquet(os.path.join(self.dir, "margin.parquet"))
        assert_frame_equal(new_df, expected_df)
