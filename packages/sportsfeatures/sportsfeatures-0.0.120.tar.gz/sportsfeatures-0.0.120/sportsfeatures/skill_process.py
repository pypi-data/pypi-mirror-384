"""Process the current dataframe by adding skill features."""

# pylint: disable=duplicate-code,too-many-locals,too-many-statements,too-many-branches,too-many-nested-blocks

import datetime
import logging

import pandas as pd
from tqdm import tqdm

from .columns import DELIMITER
from .entity_type import EntityType
from .identifier import Identifier
from .null_check import is_null
from .windowed_rating import WindowedRating

SKILL_COLUMN_PREFIX = "skill"
SKILL_MU_COLUMN = "mu"
SKILL_SIGMA_COLUMN = "sigma"
SKILL_RANKING_COLUMN = "ranking"
SKILL_PROBABILITY_COLUMN = "probability"
TIME_SLICE_ALL = "all"


def skill_process(
    df: pd.DataFrame,
    dt_column: str,
    identifiers: list[Identifier],
    windows: list[datetime.timedelta | None],
) -> pd.DataFrame:
    """Add skill features to the dataframe."""
    logging.info("Starting skill processing")
    tqdm.pandas(desc="Skill Features")
    df_dict: dict[str, list[float | None]] = {}
    df_cols = df.columns.values.tolist()

    team_identifiers = [x for x in identifiers if x.entity_type == EntityType.TEAM]
    player_identifiers = [x for x in identifiers if x.entity_type == EntityType.PLAYER]
    coach_identifiers = [x for x in identifiers if x.entity_type == EntityType.COACH]
    rating_windows = [WindowedRating(x, dt_column) for x in windows]

    written_columns = set()
    for row in tqdm(df.itertuples(name=None), desc="Skill Processing", total=len(df)):
        row_dict = {x: row[count + 1] for count, x in enumerate(df_cols)}

        for rating_window in rating_windows:
            window_id = (
                TIME_SLICE_ALL
                if rating_window.window is None
                else f"window{rating_window.window.days}"
            )
            team_result, player_result, coach_result = rating_window.add(
                row_dict, team_identifiers, player_identifiers, coach_identifiers
            )
            for team_identifier in team_identifiers:
                if team_identifier.column not in row_dict:
                    continue
                team_id = row_dict[team_identifier.column]
                if is_null(team_id):
                    continue
                if team_id in team_result:
                    rating, ranking, prob = team_result[team_id]
                    window_prefix = DELIMITER.join(
                        [team_identifier.column_prefix, SKILL_COLUMN_PREFIX, window_id]
                    )

                    mu_col = DELIMITER.join([window_prefix, SKILL_MU_COLUMN])
                    if mu_col not in df_dict:
                        df_dict[mu_col] = [None for _ in range(len(df))]
                    df_dict[mu_col][row[0]] = rating.mu
                    written_columns.add(mu_col)

                    sigma_col = DELIMITER.join([window_prefix, SKILL_SIGMA_COLUMN])
                    if sigma_col not in df_dict:
                        df_dict[sigma_col] = [None for _ in range(len(df))]
                    df_dict[sigma_col][row[0]] = rating.sigma
                    written_columns.add(sigma_col)

                    ranking_col = DELIMITER.join([window_prefix, SKILL_RANKING_COLUMN])
                    if ranking_col not in df_dict:
                        df_dict[ranking_col] = [None for _ in range(len(df))]
                    df_dict[ranking_col][row[0]] = ranking
                    written_columns.add(ranking_col)

                    prob_col = DELIMITER.join([window_prefix, SKILL_PROBABILITY_COLUMN])
                    if prob_col not in df_dict:
                        df_dict[prob_col] = [None for _ in range(len(df))]
                    df_dict[prob_col][row[0]] = prob
                    written_columns.add(prob_col)
                for player_identifier in player_identifiers:
                    if player_identifier.column not in row_dict:
                        continue
                    player_id = row_dict[player_identifier.column]
                    if is_null(player_id):
                        continue
                    if player_id in player_result:
                        rating, ranking, prob = team_result[player_id]
                        window_prefix = DELIMITER.join(
                            [
                                player_identifier.column_prefix,
                                SKILL_COLUMN_PREFIX,
                                window_id,
                            ]
                        )

                        mu_col = DELIMITER.join([window_prefix, SKILL_MU_COLUMN])
                        if mu_col not in df_dict:
                            df_dict[mu_col] = [None for _ in range(len(df))]
                        df_dict[mu_col][row[0]] = rating.mu
                        written_columns.add(mu_col)

                        sigma_col = DELIMITER.join([window_prefix, SKILL_SIGMA_COLUMN])
                        if sigma_col not in df_dict:
                            df_dict[sigma_col] = [None for _ in range(len(df))]
                        df_dict[sigma_col][row[0]] = rating.sigma
                        written_columns.add(sigma_col)

                        ranking_col = DELIMITER.join(
                            [window_prefix, SKILL_RANKING_COLUMN]
                        )
                        if ranking_col not in df_dict:
                            df_dict[ranking_col] = [None for _ in range(len(df))]
                        df_dict[ranking_col][row[0]] = ranking
                        written_columns.add(ranking_col)

                        prob_col = DELIMITER.join(
                            [window_prefix, SKILL_PROBABILITY_COLUMN]
                        )
                        if prob_col not in df_dict:
                            df_dict[prob_col] = [None for _ in range(len(df))]
                        df_dict[prob_col][row[0]] = prob
                        written_columns.add(prob_col)

                for coach_identifier in coach_identifiers:
                    if coach_identifier.column not in row_dict:
                        continue
                    coach_id = row_dict[coach_identifier.column]
                    if is_null(coach_id):
                        continue
                    if coach_id in coach_result:
                        rating, ranking, prob = team_result[coach_id]
                        window_prefix = DELIMITER.join(
                            [
                                coach_identifier.column_prefix,
                                SKILL_COLUMN_PREFIX,
                                window_id,
                            ]
                        )

                        mu_col = DELIMITER.join([window_prefix, SKILL_MU_COLUMN])
                        if mu_col not in df_dict:
                            df_dict[mu_col] = [None for _ in range(len(df))]
                        df_dict[mu_col][row[0]] = rating.mu
                        written_columns.add(mu_col)

                        sigma_col = DELIMITER.join([window_prefix, SKILL_SIGMA_COLUMN])
                        if sigma_col not in df_dict:
                            df_dict[sigma_col] = [None for _ in range(len(df))]
                        df_dict[sigma_col][row[0]] = rating.sigma
                        written_columns.add(sigma_col)

                        ranking_col = DELIMITER.join(
                            [window_prefix, SKILL_RANKING_COLUMN]
                        )
                        if ranking_col not in df_dict:
                            df_dict[ranking_col] = [None for _ in range(len(df))]
                        df_dict[ranking_col][row[0]] = ranking
                        written_columns.add(ranking_col)

                        prob_col = DELIMITER.join(
                            [window_prefix, SKILL_PROBABILITY_COLUMN]
                        )
                        if prob_col not in df_dict:
                            df_dict[prob_col] = [None for _ in range(len(df))]
                        df_dict[prob_col][row[0]] = prob
                        written_columns.add(prob_col)

    for column in written_columns:
        df.loc[:, column] = df_dict[column]

    return df[sorted(df.columns.values.tolist())]
