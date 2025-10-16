"""Tests for the timeseries process function."""
import datetime
import os
import tempfile
import unittest

import pandas as pd
from pandas.testing import assert_frame_equal

from sportsfeatures.timeseries_process import _extract_identifier_timeseries, _process_identifier_ts, _COLUMN_PREFIX_COLUMN
from sportsfeatures.identifier import Identifier
from sportsfeatures.entity_type import EntityType


class TestTimeseriesProcess(unittest.TestCase):

    def test_extract_identifier_timeseries(self):
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
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            _extract_identifier_timeseries(df, identifiers, dt_column, tmpdir)
            ts_dfs = {}
            for path in os.listdir(tmpdir):
                if not path.endswith(".parquet"):
                    continue
                root, _ = os.path.splitext(path)
                ts_dfs[root] = pd.read_parquet(os.path.join(tmpdir, path))
            expected_ts_dfs = {
                "_".join([EntityType.TEAM, team_0_id]): pd.DataFrame(data={
                    _COLUMN_PREFIX_COLUMN: [team_0_column_prefix, team_1_column_prefix, team_0_column_prefix],
                    dt_column: df[dt_column],
                    "/kicks": [10.0, 40.0, 30.0],
                }),
                "_".join([EntityType.TEAM, team_1_id]): pd.DataFrame(data={
                    _COLUMN_PREFIX_COLUMN: [team_1_column_prefix, team_0_column_prefix, team_1_column_prefix],
                    dt_column: df[dt_column],
                    "/kicks": [20.0, 20.0, 60.0],
                })
            }
            for key, value in expected_ts_dfs.items():
                compare_value = ts_dfs[key]
                assert_frame_equal(value, compare_value)

    def test_process_identifier_ts(self):
        dt_column = "dt"
        identifier_ts = {
            "team_0": pd.DataFrame(data={
                "/kicks": [10.0, 20.0, 30.0],
                dt_column: [datetime.datetime(2022, 1, 1), datetime.datetime(2022, 1, 2), datetime.datetime(2022, 1, 3)],
                _COLUMN_PREFIX_COLUMN: ["/teams/0", "/teams/0", "/teams/0"]
            })
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            for k, v in identifier_ts.items():
                v.to_parquet(os.path.join(tmpdir, f"{k}.parquet"))
            _process_identifier_ts([datetime.timedelta(days=20), None], dt_column, True, tmpdir)
            for k in list(identifier_ts.keys()):
                identifier_ts[k] = pd.read_parquet(os.path.join(tmpdir, f"{k}.parquet"))
            test_df = pd.DataFrame(data={
                "/kicks_transform_none_count_20days": [None, 1.0, 2.0],
                "/kicks_transform_none_count_all": [None, 1.0, 2.0],
                "/kicks_transform_none_kurt_20days": [None, None, None],
                "/kicks_transform_none_kurt_all": [None, None, None],
                "/kicks_transform_none_lag_1": [None, 10.0, 20.0],
                "/kicks_transform_none_lag_2": [None, None, 10.0],
                "/kicks_transform_none_lag_4": [None, None, None],
                "/kicks_transform_none_lag_8": [None, None, None],
                "/kicks_transform_none_max_20days": [None, 10.0, 20.0],
                "/kicks_transform_none_max_all": [None, 10.0, 20.0],
                "/kicks_transform_none_mean_20days": [None, 10.0, 15.0],
                "/kicks_transform_none_mean_all": [None, 10.0, 15.0],
                "/kicks_transform_none_median_20days": [None, 10.0, 15.0],
                "/kicks_transform_none_median_all": [None, 10.0, 15.0],
                "/kicks_transform_none_min_20days": [None, 10.0, 10.0],
                "/kicks_transform_none_min_all": [None, 10.0, 10.0],
                "/kicks_transform_none_rank_20days": [None, 1.0, 2.0],
                "/kicks_transform_none_rank_all": [None, 1.0, 2.0],
                "/kicks_transform_none_sem_20days": [None, None, 7.071068],
                "/kicks_transform_none_sem_all": [None, None, 7.071068],
                "/kicks_transform_none_skew_20days": [None, None, None],
                "/kicks_transform_none_skew_all": [None, None, None],
                "/kicks_transform_none_std_20days": [None, None, 7.071068],
                "/kicks_transform_none_std_all": [None, None, 7.071068],
                "/kicks_transform_none_sum_20days": [None, 10.0, 30.0],
                "/kicks_transform_none_sum_all": [None, 10.0, 30.0],
                "/kicks_transform_none_var_20days": [None, None, 50.0],
                "/kicks_transform_none_var_all": [None, None, 50.0],
                _COLUMN_PREFIX_COLUMN: ["/teams/0", "/teams/0", "/teams/0"],
            })
            test_df["/kicks_transform_none_skew_20days"] = test_df["/kicks_transform_none_skew_20days"].astype(float)
            test_df["/kicks_transform_none_kurt_20days"] = test_df["/kicks_transform_none_kurt_20days"].astype(float)
            test_df["/kicks_transform_none_skew_all"] = test_df["/kicks_transform_none_skew_all"].astype(float)
            test_df["/kicks_transform_none_kurt_all"] = test_df["/kicks_transform_none_kurt_all"].astype(float)
            test_df["/kicks_transform_none_lag_4"] = test_df["/kicks_transform_none_lag_4"].astype(float)
            test_df["/kicks_transform_none_lag_8"] = test_df["/kicks_transform_none_lag_8"].astype(float)
            print(test_df.columns.values.tolist())
            assert_frame_equal(identifier_ts["team_0"], test_df)

    def test_nan_in_timeseries_process(self):
        dt_column = "dt"
        identifier_ts = {
            "team_0": pd.DataFrame(data={
                _COLUMN_PREFIX_COLUMN: ["/teams/0", "/teams/0", "/teams/0", "/teams/0", "/teams/0", "/teams/0"],
                "/kicks": [10.0, 20.0, 30.0, None, None, 40.0],
                dt_column: [
                    datetime.datetime(2022, 1, 1),
                    datetime.datetime(2022, 1, 2),
                    datetime.datetime(2022, 1, 3),
                    datetime.datetime(2022, 1, 4),
                    datetime.datetime(2022, 1, 5),
                    datetime.datetime(2022, 1, 6),
                ],
            })
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            for k, v in identifier_ts.items():
                v.to_parquet(os.path.join(tmpdir, f"{k}.parquet"))
            _process_identifier_ts([datetime.timedelta(days=20), None], dt_column, True, tmpdir)
            for k in list(identifier_ts.keys()):
                identifier_ts[k] = pd.read_parquet(os.path.join(tmpdir, f"{k}.parquet"))
            print(identifier_ts)

    def test_all_nan_in_timeseries_process(self):
        dt_column = "dt"
        identifier_ts = {
            "team_0": pd.DataFrame(data={
                _COLUMN_PREFIX_COLUMN: ["/teams/0", "/teams/0", "/teams/0", "/teams/0", "/teams/0", "/teams/0"],
                "/kicks": ["all", "all", "all", "all", "all", "all"],
                dt_column: [
                    datetime.datetime(2022, 1, 1),
                    datetime.datetime(2022, 1, 2),
                    datetime.datetime(2022, 1, 3),
                    datetime.datetime(2022, 1, 4),
                    datetime.datetime(2022, 1, 5),
                    datetime.datetime(2022, 1, 6),
                ],
            })
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            for k, v in identifier_ts.items():
                v.to_parquet(os.path.join(tmpdir, f"{k}.parquet"))
            _process_identifier_ts([datetime.timedelta(days=20), None], dt_column, True, tmpdir)
            for k in list(identifier_ts.keys()):
                identifier_ts[k] = pd.read_parquet(os.path.join(tmpdir, f"{k}.parquet"))
            print(identifier_ts)
