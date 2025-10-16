"""Tests for the process function."""
import datetime
import os
import tempfile
import unittest

import pandas as pd

from sportsfeatures.process import process
from sportsfeatures.identifier import Identifier
from sportsfeatures.entity_type import EntityType
from sportsfeatures.bet import Bet
from sportsfeatures.news import News


class TestProcess(unittest.TestCase):

    def test_process(self):
        current_dir = os.getcwd()
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                os.chdir(tmpdir)
                team_0_column_prefix = "teams/0"
                team_1_column_prefix = "teams/1"
                dt_column = "dt"
                team_0_id_column = team_0_column_prefix + "/id"
                team_0_kicks = team_0_column_prefix + "/kicks"
                team_0_points_column = team_0_column_prefix + "/points"
                team_0_field_goals_column = team_0_column_prefix + "/field_goals"
                team_0_assists_column = team_0_column_prefix + "/assists"
                team_0_field_goals_attempted_column = team_0_column_prefix + "/field_goals_attempted"
                team_0_offensive_rebounds_column = team_0_column_prefix + "/offensive_rebounds"
                team_0_turnovers_column = team_0_column_prefix + "/turnovers"
                team_0_odds_column = team_0_column_prefix + "/odds/odds"
                team_0_bookie_column = team_0_column_prefix + "/odds/bookie"
                team_0_dt_column = team_0_column_prefix + "/odds/dt"
                team_0_canonical_column = team_0_column_prefix + "/odds/canonical"
                team_0_bookie_name_column = team_0_column_prefix + "/odds/bookie_name"
                team_0_bet_type_column = team_0_column_prefix + "/odds/bet_type"
                team_0_news_title_column = team_0_column_prefix + "/news/0/title"
                team_0_news_published_column = team_0_column_prefix + "/news/0/published"
                team_0_news_summary_column = team_0_column_prefix + "/news/0/summary"
                team_0_news_source_column = team_0_column_prefix + "/news/0/source"
                team_1_id_column = team_1_column_prefix + "/id"
                team_1_kicks = team_1_column_prefix + "/kicks"
                team_1_points_column = team_1_column_prefix + "/points"
                team_1_field_goals_column = team_1_column_prefix + "/field_goals"
                team_1_assists_column = team_1_column_prefix + "/assists"
                team_1_field_goals_attempted_column = team_1_column_prefix + "/field_goals_attempted"
                team_1_offensive_rebounds_column = team_1_column_prefix + "/offensive_rebounds"
                team_1_turnovers_column = team_1_column_prefix + "/turnovers"
                team_1_odds_column = team_1_column_prefix + "/odds/odds"
                team_1_bookie_column = team_1_column_prefix + "/odds/bookie"
                team_1_dt_column = team_1_column_prefix + "/odds/dt"
                team_1_canonical_column = team_1_column_prefix + "/odds/canonical"
                team_1_bookie_name_column = team_1_column_prefix + "/odds/bookie_name"
                team_1_bet_type_column = team_1_column_prefix + "/odds/bet_type"
                team_1_news_title_column = team_0_column_prefix + "/news/1/title"
                team_1_news_published_column = team_0_column_prefix + "/news/1/published"
                team_1_news_summary_column = team_0_column_prefix + "/news/1/summary"
                team_1_news_source_column = team_0_column_prefix + "/news/1/source"
                df = pd.DataFrame(data={
                    dt_column: [datetime.datetime(2022, 1, 1), datetime.datetime(2022, 1, 2), datetime.datetime(2022, 1, 3)],
                    team_0_id_column: ["0", "1", "0"],
                    team_0_kicks: [10, 20, 30],
                    team_0_points_column: [50, 100, 150],
                    team_0_field_goals_column: [12, 24, 36],
                    team_0_assists_column: [10, 20, 30],
                    team_0_field_goals_attempted_column: [20, 40, 60],
                    team_0_offensive_rebounds_column: [30, 60, 90],
                    team_0_turnovers_column: [10.0, 20.0, 30.0],
                    team_0_odds_column: [1.1, 1.2, 1.3],
                    team_0_bookie_column: ["a", "a", "a"],
                    team_0_dt_column: [datetime.datetime(2022, 1, 1) - datetime.timedelta(hours=1), datetime.datetime(2022, 1, 2) - datetime.timedelta(hours=1), datetime.datetime(2022, 1, 3) - datetime.timedelta(hours=1)],
                    team_0_canonical_column: [False, False, False],
                    team_0_bookie_name_column: ["a", "a", "a"],
                    team_0_bet_type_column: ["win", "win", "win"],
                    team_0_news_title_column: ["Team 0 Article", "Team 1 Article", "Team 0 Article"],
                    team_0_news_published_column: [datetime.datetime(2022, 1, 1) - datetime.timedelta(hours=10), datetime.datetime(2022, 1, 2) - datetime.timedelta(hours=10), datetime.datetime(2022, 1, 3) - datetime.timedelta(hours=10)],
                    team_0_news_summary_column: ["Team 0 is great", "Team 1 is great", "Team 0 is great"],
                    team_0_news_source_column: ["Newspaper A", "Newspaper A", "Newspaper A"],
                    team_1_id_column: ["1", "0", "1"],
                    team_1_kicks: [20, 40, 60],
                    team_1_points_column: [60, 120, 180],
                    team_1_field_goals_column: [30, 60, 90],
                    team_1_assists_column: [20, 40, 60],
                    team_1_field_goals_attempted_column: [80, 160, 240],
                    team_1_offensive_rebounds_column: [90, 180, 270],
                    team_1_turnovers_column: [10.0, 20.0, 30.0],
                    team_1_odds_column: [2.1, 2.2, 2.3],
                    team_1_bookie_column: ["a", "a", "a"],
                    team_1_dt_column: [datetime.datetime(2022, 1, 1) - datetime.timedelta(hours=1), datetime.datetime(2022, 1, 2) - datetime.timedelta(hours=1), datetime.datetime(2022, 1, 3) - datetime.timedelta(hours=1)],
                    team_1_canonical_column: [False, False, False],
                    team_1_bookie_name_column: ["a", "a", "a"],
                    team_1_bet_type_column: ["win", "win", "win"],
                    team_1_news_title_column: ["Team 1 Article", "Team 0 Article", "Team 1 Article"],
                    team_1_news_published_column: [datetime.datetime(2022, 1, 1) - datetime.timedelta(hours=10), datetime.datetime(2022, 1, 2) - datetime.timedelta(hours=10), datetime.datetime(2022, 1, 3) - datetime.timedelta(hours=10)],
                    team_1_news_summary_column: ["Team 1 is great", "Team 0 is great", "Team 1 is great"],
                    team_1_news_source_column: ["Newspaper A", "Newspaper A", "Newspaper A"],
                })
                identifiers = [
                    Identifier(
                        EntityType.TEAM,
                        team_0_id_column,
                        [team_0_kicks],
                        team_0_column_prefix,
                        points_column=team_0_points_column,
                        field_goals_column=team_0_field_goals_column,
                        assists_column=team_0_assists_column,
                        field_goals_attempted_column=team_0_field_goals_attempted_column,
                        offensive_rebounds_column=team_0_offensive_rebounds_column,
                        turnovers_column=team_0_turnovers_column,
                        bets=[Bet(
                            odds_column=team_0_odds_column,
                            bookie_id_column=team_0_bookie_column,
                            dt_column=team_0_dt_column,
                            canonical_column=team_0_canonical_column,
                            bookie_name_column=team_0_bookie_name_column,
                            bet_type_column=team_0_bet_type_column,
                        )],
                        news=[News(
                            title_column=team_0_news_title_column,
                            published_column=team_0_news_published_column,
                            summary_column=team_0_news_summary_column,
                            source_column=team_0_news_source_column,
                        )],
                    ),
                    Identifier(
                        EntityType.TEAM,
                        team_1_id_column,
                        [team_1_kicks],
                        team_1_column_prefix,
                        points_column=team_1_points_column,
                        field_goals_column=team_1_field_goals_column,
                        assists_column=team_1_assists_column,
                        field_goals_attempted_column=team_1_field_goals_attempted_column,
                        offensive_rebounds_column=team_1_offensive_rebounds_column,
                        turnovers_column=team_1_turnovers_column,
                        bets=[Bet(
                            odds_column=team_1_odds_column,
                            bookie_id_column=team_1_bookie_column,
                            dt_column=team_1_dt_column,
                            canonical_column=team_1_canonical_column,
                            bookie_name_column=team_1_bookie_name_column,
                            bet_type_column=team_1_bet_type_column,
                        )],
                        news=[News(
                            title_column=team_1_news_title_column,
                            published_column=team_1_news_published_column,
                            summary_column=team_1_news_summary_column,
                            source_column=team_1_news_source_column,
                        )],
                    ),
                ]
                df = process(df, dt_column, identifiers, [datetime.timedelta(days=365), None], set())
                with pd.option_context('display.max_rows', None, 'display.max_columns', None):
                    print(df)
                print(df.columns.values)
        finally:
            os.chdir(current_dir)
