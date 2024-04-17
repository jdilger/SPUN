import pandas as pd
import altair as alt


def add_row_column_for_facets(
    row: int, column: int, df: pd.DataFrame, column_name: str
) -> tuple[pd.DataFrame, int, int]:
    keys = df[column_name].unique()
    _range = range(len(keys))
    row_vals = [i % row + 1 for i in _range]
    col_vals = [i % column + 1 for i in _range]
    row_map = dict(zip(keys, row_vals))
    col_map = dict(zip(keys, col_vals))

    df["chart_row"] = df[column_name].map(lambda x: row_map.get(x))
    df["chart_col"] = df[column_name].map(lambda x: col_map.get(x))
    return df, min(max(row_vals), row), min(max(col_vals), column)


def apply_style(
    chart: alt.Chart,
    title: str | None = None,
    subtitle: str | None = None,
) -> alt.Chart:
    title = title.upper() if isinstance(title, str) else ""
    subtitle = subtitle.upper() if isinstance(subtitle, str) else ""
    title = alt.TitleParams(title, subtitle=[subtitle])
    chart = (
        chart.properties(title=title)
        .configure_axis(
            labelFont="Neue Haas Unica, sans-serif",
            titleFont="Neue Haas Unica, sans-serif",
            titleFontSize=15,  # Adjust the font size if needed
            labelFontSize=12,  # Adjust the font size if needed
            titleFontWeight=400,
            titleLineHeight=90,
        )
        .configure_title(
            fontSize=40,  # Adjust the font size of the title
            font="Girott, sans-serif",  # Set the font of the title
            subtitleFont="Neue Haas Unica, sans-serif",
            subtitleFontSize=25,
            subtitleLineHeight=130,
        )
        .configure_legend(
            labelFont="Neue Haas Unica, sans-serif",
            titleFont="Neue Haas Unica, sans-serif",
            labelFontSize=12,
            titleFontSize=15,
        )
        .configure_header(
            labelFontSize=0,
        )
    )

    return chart
