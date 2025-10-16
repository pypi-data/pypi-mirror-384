"""Tests for the players process function."""
import datetime
import os
import unittest

import pandas as pd
from pandas.testing import assert_frame_equal

from sportsfeatures.players_process import players_process
from sportsfeatures.identifier import Identifier
from sportsfeatures.entity_type import EntityType


class TestPlayersProcess(unittest.TestCase):

    def setUp(self):
        self.dir = os.path.dirname(__file__)

    def test_players_process(self):
        team_0_column_prefix = "teams/0"
        team_1_column_prefix = "teams/1"
        dt_column = "dt"
        team_0_id_column = team_0_column_prefix + "/id"
        team_0_kicks = team_0_column_prefix + "/kicks"
        team_0_id = "0"
        team_1_id_column = team_1_column_prefix + "/id"
        team_1_kicks = team_1_column_prefix + "/kicks"
        team_1_id = "1"
        df = pd.DataFrame(data={
            dt_column: [datetime.datetime(2022, 1, 1), datetime.datetime(2022, 1, 2), datetime.datetime(2022, 1, 3)],
            team_0_id_column: [team_0_id, team_1_id, team_0_id],
            team_0_kicks: [10.0, 20.0, 30.0],
            team_1_id_column: [team_1_id, team_0_id, team_1_id],
            team_1_kicks: [20.0, 40.0, 60.0],
            team_0_column_prefix + "/players/0/identifier": ["a", "a", "a"],
            team_0_column_prefix + "/players/1/identifier": ["b", "b", "b"],
            team_1_column_prefix + "/players/0/identifier": ["c", "c", "c"],
            team_1_column_prefix + "/players/1/identifier": ["d", "d", "d"],
            team_0_column_prefix + "/players/0/feature": [0.0, 1.0, 2.0],
            team_0_column_prefix + "/players/1/feature": [1.0, 2.0, 3.0],
            team_1_column_prefix + "/players/0/feature": [2.0, 3.0, 4.0],
            team_1_column_prefix + "/players/1/feature": [3.0, 4.0, 5.0],
        })
        identifiers = [
            Identifier(
                EntityType.TEAM,
                team_0_id_column,
                [team_0_kicks],
                team_0_column_prefix,
            ),
            Identifier(
                EntityType.TEAM,
                team_1_id_column,
                [team_1_kicks],
                team_1_column_prefix,
            ),
            Identifier(
                EntityType.PLAYER,
                team_0_column_prefix + "/players/0/identifier",
                [team_0_column_prefix + "/players/0/feature"],
                team_0_column_prefix + "/players/0",
                team_identifier_column=team_0_id_column,
            ),
            Identifier(
                EntityType.PLAYER,
                team_0_column_prefix + "/players/1/identifier",
                [team_0_column_prefix + "/players/1/feature"],
                team_0_column_prefix + "/players/1",
                team_identifier_column=team_0_id_column,
            ),
            Identifier(
                EntityType.PLAYER,
                team_1_column_prefix + "/players/0/identifier",
                [team_1_column_prefix + "/players/0/feature"],
                team_1_column_prefix + "/players/0",
                team_identifier_column=team_1_id_column,
            ),
            Identifier(
                EntityType.PLAYER,
                team_1_column_prefix + "/players/1/identifier",
                [team_1_column_prefix + "/players/1/feature"],
                team_1_column_prefix + "/players/1",
                team_identifier_column=team_1_id_column,
            ),
        ]
        players_df = players_process(df, identifiers)
        #players_df.to_parquet("players_df.parquet")
        expected_df = pd.read_parquet(os.path.join(self.dir, "players_df.parquet"))
        assert_frame_equal(players_df, expected_df)
