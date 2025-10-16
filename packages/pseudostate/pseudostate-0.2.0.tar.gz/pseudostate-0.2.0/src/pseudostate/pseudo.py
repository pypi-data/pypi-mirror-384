import polars as pl
from polarstate import prepare_event_table, predict_aj_estimates


def calculate_pseudostates(
    times_and_reals: pl.DataFrame, fixed_time_horizon: int
) -> pl.DataFrame:
    pseudo_states: list[pl.DataFrame] = []

    for i in range(times_and_reals.height):
        sub_data = times_and_reals.slice(0, i).vstack(
            times_and_reals.slice(i + 1, times_and_reals.height - i)
        )

        sub_event_table = prepare_event_table(sub_data)

        pseudo_state = predict_aj_estimates(
            sub_event_table, fixed_time_horizons=pl.Series([fixed_time_horizon])
        )

        pseudo_states.append(pseudo_state)

    return pl.concat(pseudo_states, how="vertical")
