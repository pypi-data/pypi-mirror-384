"""Calculate bet features."""

import datetime
import functools

import pandas as pd
from sklearn.metrics import mean_squared_error  # type: ignore
from tqdm import tqdm

from .columns import DELIMITER
from .identifier import Identifier
from .null_check import is_null


def _force_utc_aware(series, timezone="UTC"):
    series = pd.to_datetime(series, errors="coerce")

    if series.dt.tz is None:
        return series.dt.tz_localize(timezone, ambiguous="NaT", nonexistent="NaT")
    return series.dt.tz_convert(timezone)


def bet_process(
    df: pd.DataFrame,
    identifiers: list[Identifier],
    dt_column: str,
    use_bets_features: bool,
) -> pd.DataFrame:
    """Process bets."""
    # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    tqdm.pandas(desc="Bets Features")
    bookie_odds: list[float] = []
    wins: list[float] = []

    def apply_bets(
        row: pd.Series, identifiers: list[Identifier], dt_column: str
    ) -> pd.Series:
        nonlocal bookie_odds
        nonlocal wins

        try:
            game_dt = pd.Timestamp(row[dt_column]).tz_localize("UTC")
        except TypeError:
            game_dt = pd.Timestamp(row[dt_column]).tz_convert("UTC")

        price_efficiency = (
            None if not bookie_odds else mean_squared_error(bookie_odds, wins)
        )
        local_bookie_odds = []
        local_points = []
        for identifier in identifiers:
            if identifier.points_column is None:
                continue
            if identifier.points_column not in row:
                continue

            odds_data = []
            bookies_data = []
            dts_data = []
            final_odds = None
            for bet in identifier.bets:
                if bet.odds_column not in row or bet.bookie_id_column not in row:
                    continue
                odds = row[bet.odds_column]
                if is_null(odds):
                    continue
                bookie_id = row[bet.bookie_id_column]
                if is_null(bookie_id):
                    continue
                if bet.dt_column is None or bet.dt_column not in row:
                    dt = game_dt - datetime.timedelta(hours=1)
                else:
                    dt = pd.to_datetime(row[bet.dt_column])
                    if is_null(dt):
                        dt = game_dt - datetime.timedelta(hours=1)
                try:
                    dt = pd.Timestamp(dt).tz_localize("UTC")
                except TypeError:
                    dt = pd.Timestamp(dt).tz_convert("UTC")
                if dt > game_dt - datetime.timedelta(hours=1):
                    continue
                if bet.canonical_column in row:
                    canonical = row[bet.canonical_column]
                    if not is_null(canonical) and canonical:
                        final_odds = odds
                odds_data.append(odds)
                bookies_data.append(bookie_id)
                dts_data.append(dt)
            bet_df = pd.DataFrame(
                data={
                    "odds": odds_data,
                    "bookie": bookies_data,
                    "dt": dts_data,
                }
            )
            if bet_df.empty:
                continue
            bet_df[dt_column] = _force_utc_aware(bet_df[dt_column])
            bet_df = bet_df.sort_values(by=dt_column)
            odds_max = bet_df["odds"].max()
            odds_min = bet_df["odds"].min()
            earliest_odds = bet_df["odds"].iloc[0]
            latest_odds = bet_df["odds"].iloc[-1]
            earliest_dt = bet_df[dt_column].iloc[0]
            latest_dt = bet_df[dt_column].iloc[-1]

            direction_changes = 0
            big_shifts = 0
            consensus_flips = 0
            resampled_df = pd.DataFrame()
            for bookie in bet_df["bookie"].unique():
                bookie_df = bet_df[bet_df["bookie"] == bookie]
                bookies_odds = bookie_df["odds"].to_list()
                current_odds = None
                current_direction = None
                for odd in bookies_odds:
                    if current_odds is None:
                        current_odds = odd
                        continue
                    if current_direction is None:
                        current_direction = 1 if odd >= current_odds else -1
                        current_odds = odd
                        continue
                    new_direction = 1 if odd >= current_odds else -1
                    if new_direction != current_direction:
                        direction_changes += 1
                    if max(current_odds, odd) / min(current_odds, odd) > 1.1:
                        big_shifts += 1
                    if min(current_odds, odd) < 2.0 < max(current_odds, odd):
                        consensus_flips += 1
                    current_odds = odd
                    current_direction = new_direction
                resampled_df = pd.concat(
                    [
                        resampled_df,
                        pd.DataFrame(
                            data={
                                bookie + "_odds": bookies_odds,
                            },
                            index=bookie_df["dt"],
                        ),
                    ]
                )
            resampled_df = resampled_df.resample("5T").last()
            resampled_df = resampled_df.ffill()

            ffill_df = bet_df.set_index("dt").ffill()
            oneday_df = ffill_df[ffill_df.index > game_dt - datetime.timedelta(days=1)]
            if final_odds is None:
                final_odds = resampled_df.mean(axis=1).to_list()[-1]

            if use_bets_features:
                row[DELIMITER.join([identifier.column_prefix, "odds", "max"])] = (
                    odds_max
                )
                row[DELIMITER.join([identifier.column_prefix, "odds", "min"])] = (
                    odds_min
                )
                row[DELIMITER.join([identifier.column_prefix, "odds", "mean"])] = (
                    bet_df["odds"].mean()
                )
                row[DELIMITER.join([identifier.column_prefix, "odds", "median"])] = (
                    bet_df["odds"].median()
                )
                row[DELIMITER.join([identifier.column_prefix, "odds", "spread"])] = (
                    odds_max - odds_min
                )
                row[DELIMITER.join([identifier.column_prefix, "odds", "bookies"])] = (
                    bet_df["bookie"].nunique()
                )
                row[DELIMITER.join([identifier.column_prefix, "odds", "roc"])] = (
                    latest_odds - earliest_odds
                ) / (latest_dt - earliest_dt).total_seconds()
                row[DELIMITER.join([identifier.column_prefix, "odds", "mom"])] = (
                    latest_odds - earliest_odds
                )
                row[
                    DELIMITER.join([identifier.column_prefix, "odds", "directchanges"])
                ] = direction_changes
                row[DELIMITER.join([identifier.column_prefix, "odds", "samples"])] = (
                    len(bet_df)
                )
                # row[DELIMITER.join([identifier.column_prefix, "odds", "ewm"])] = (
                #    resampled_df.mean(axis=1).ewm(alpha=0.2, adjust=False).mean()
                # )
                row[DELIMITER.join([identifier.column_prefix, "odds", "bigshifts"])] = (
                    big_shifts
                )
                row[
                    DELIMITER.join([identifier.column_prefix, "odds", "consensusflips"])
                ] = consensus_flips
                if len(oneday_df) > 1:
                    row[
                        DELIMITER.join([identifier.column_prefix, "odds", "roc1day"])
                    ] = (
                        oneday_df["odds"].iloc[-1] - oneday_df["odds"].iloc[0]
                    ) / datetime.timedelta(days=1).total_seconds()
                else:
                    row[
                        DELIMITER.join([identifier.column_prefix, "odds", "roc1day"])
                    ] = 0.0
                row[
                    DELIMITER.join(
                        [identifier.column_prefix, "odds", "priceefficiency"]
                    )
                ] = price_efficiency
            row[DELIMITER.join([identifier.column_prefix, "odds"])] = final_odds

            local_bookie_odds.append(1.0 / final_odds)

            points = row[identifier.points_column]
            if is_null(points):
                continue
            local_points.append(points)

        if local_points:
            bookie_odds.extend(local_bookie_odds)
            wins.extend([float(x == max(local_points)) for x in local_points])

        return row

    return df.progress_apply(
        functools.partial(
            apply_bets,
            identifiers=identifiers,
            dt_column=dt_column,
        ),
        axis=1,
    )  # type: ignore
