"""Tests for the bet process function."""
import datetime
import unittest
import os

import pandas as pd
from pandas.testing import assert_frame_equal

from sportsfeatures.bets_process import bet_process
from sportsfeatures.identifier import Identifier
from sportsfeatures.entity_type import EntityType
from sportsfeatures.bet import Bet


class TestBetProcess(unittest.TestCase):

    def setUp(self):
        self.dir = os.path.dirname(__file__)

    def test_bet_process(self):
        df = pd.read_csv(os.path.join(self.dir, "bets.csv"))
        identifiers = [
            Identifier(
                EntityType.TEAM,
                "teams/0/identifier",
                [],
                "teams/0",
                points_column="teams/0/points",
                bets=[Bet(
                    odds_column=f"teams/0/odds/{x}/odds",
                    bookie_id_column=f"teams/0/odds/{x}/bookie/name",
                    dt_column=f"teams/0/odds/{x}/dt",
                    canonical_column=f"teams/0/odds/{x}/canonical",
                    bookie_name_column=f"teams/0/odds/{x}/bookie/realname",
                    bet_type_column=f"teams/0/odds/{x}/bet_type",
                ) for x in range(28)],
            ),
            Identifier(
                EntityType.TEAM,
                "teams/1/identifier",
                [],
                "teams/1",
                points_column="teams/1/points",
                bets=[Bet(
                    odds_column=f"teams/1/odds/{x}/odds",
                    bookie_id_column=f"teams/1/odds/{x}/bookie/name",
                    dt_column=f"teams/1/odds/{x}/dt",
                    canonical_column=f"teams/1/odds/{x}/canonical",
                    bookie_name_column=f"teams/1/odds/{x}/bookie/realname",
                    bet_type_column=f"teams/0/odds/{x}/bet_type",
                ) for x in range(28)],
            ),
        ]
        new_df = bet_process(df, identifiers, "dt", True)
        odds = new_df["teams/0_odds"].to_list()
        self.assertListEqual(odds, [
            4.0,
            8.0,
            1.3333333333333333,
            2.203333333333333,
            1.3050000000000002,
            1.4849999999999999,
            2.675,
            1.47,
            2.25,
            1.03,
            1.51,
            2.05,
            2.65,
            3.35,
            2.1500000000000004,
            1.705,
            2.05,
            1.5150000000000001,
            1.49,
            5.5,
        ])
        odds = new_df["teams/1_odds"].to_list()
        self.assertListEqual(odds, [
            2.29,
            1.03,
            3.266666666666667,
            1.6266666666666667,
            3.2,
            2.425,
            1.41,
            2.4749999999999996,
            1.5550000000000002,
            8.25,
            2.375,
            1.68,
            1.435,
            1.28,
            1.62,
            2.0,
            1.68,
            2.375,
            2.425,
            1.105,
        ])
