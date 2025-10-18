import string

import altair as alt
from babel.numbers import get_currency_symbol
import pandas as pd
import numpy as np
from typing import Callable, Any, Literal

from .triangle import Triangle, Cell
from .base import metadata_diff

alt.renderers.enable("browser")

SLICE_TITLE_KWARGS = {
    "anchor": "middle",
    "font": "sans-serif",
    "fontWeight": "normal",
    "fontSize": 12,
}

BASE_HEIGHT = 600
BASE_WIDTH = "container"

BASE_AXIS_LABEL_FONT_SIZE = 16
BASE_AXIS_TITLE_FONT_SIZE = 18
FONT_SIZE_DECAY_FACTOR = 0.2

CellArgs = Cell | Cell, Cell, Cell
MetricFunc = Callable[[CellArgs], float | int | np.ndarray]
MetricFuncDict = dict[str, MetricFunc]

COMMON_METRIC_DICT: MetricFuncDict = {
    "Paid Loss Ratio": lambda cell: 100 * cell["paid_loss"] / cell["earned_premium"],
    "Reported Loss Ratio": lambda cell: 100
    * cell["reported_loss"]
    / cell["earned_premium"],
    "Incurred Loss Ratio": lambda cell: 100
    * cell["incurred_loss"]
    / cell["earned_premium"],
    "Paid Loss": lambda cell: cell["paid_loss"],
    "Reported Loss": lambda cell: cell["reported_loss"],
    "Incurred Loss": lambda cell: cell["incurred_loss"],
    "Paid ATA": lambda cell, prev_cell: cell["paid_loss"] / prev_cell["paid_loss"],
    "Reported ATA": lambda cell, prev_cell: cell["reported_loss"]
    / prev_cell["reported_loss"],
    "Paid Incremental ATA": lambda cell, prev_cell: cell["paid_loss"]
    / prev_cell["paid_loss"]
    - 1,
    "Reported Incremental ATA": lambda cell, prev_cell: cell["reported_loss"]
    / prev_cell["reported_loss"]
    - 1,
}

MetricFuncSpec = MetricFuncDict | str | list[str]


def _resolve_metric_spec(metric_spec: MetricFuncSpec) -> MetricFuncDict:
    if isinstance(metric_spec, str):
        metric_spec = [metric_spec]
    if isinstance(metric_spec, list):
        result = {}
        for ref in metric_spec:
            if not isinstance(ref, str):
                raise ValueError("Supplied metric references must be strings")
            elif ref not in COMMON_METRIC_DICT:
                raise ValueError(f"Don't know the definition of metric {ref}")
            else:
                result[ref] = COMMON_METRIC_DICT[ref]
        return result
    else:
        return metric_spec


@alt.theme.register("bermuda_plot_theme", enable=True)
def bermuda_plot_theme() -> alt.theme.ThemeConfig:
    return {
        "autosize": {"contains": "content", "resize": True},
        "config": {
            "style": {
                "group-title": {"fontSize": 24},
                "group-subtitle": {"fontSize": 18},
                "guide-label": {
                    "fontSize": BASE_AXIS_LABEL_FONT_SIZE,
                    "font": "sans-serif",
                },
                "guide-title": {
                    "fontSize": BASE_AXIS_TITLE_FONT_SIZE,
                    "font": "sans-serif",
                },
            },
            "mark": {"color": "black"},
            "title": {"anchor": "start", "offset": 20},
            "axis": {"labelOverlap": True},
            "legend": {
                "orient": "right",
                "titleAnchor": "start",
                "layout": {
                    "direction": "vertical",
                },
            },
        },
    }


def _remove_triangle_samples(triangle: Triangle) -> Triangle:
    """Removes cells that contain samples. The primary use-case
    of this method is to remove future predictions from a triangle to make
    investigating observed data in combined triangles easier."""
    if triangle.num_samples == 1:
        return triangle

    int_cells = []
    for cell in triangle:
        if not any(
            isinstance(v, np.ndarray) and v.size > 1 for v in cell.values.values()
        ):
            int_cells.append(cell)
    return Triangle(int_cells)


def plot_right_edge(
    triangle: Triangle,
    hide_samples: bool = False,
    uncertainty: bool = True,
    uncertainty_type: Literal["ribbon", "segments"] = "ribbon",
    width: int = 400,
    height: int = 200,
    ncols: int | None = None,
    facet_titles: list[str] | None = None,
) -> alt.Chart:
    main_title = alt.Title(
        "Latest Loss Ratio", subtitle="The most recent loss ratio diagonal"
    )
    n_slices = len(triangle.slices)
    max_cols = ncols or _determine_facet_cols(n_slices)
    fig = _build_metric_slice_charts(
        _remove_triangle_samples(triangle) if hide_samples else triangle,
        plot_func=_plot_right_edge,
        title=main_title,
        facet_titles=facet_titles,
        uncertainty=uncertainty,
        uncertainty_type=uncertainty_type,
        width=width,
        height=height,
        mark_scaler=max_cols,
        ncols=max_cols,
    ).configure_axis(**_compute_font_sizes(max_cols))
    return fig


def _plot_right_edge(
    triangle: Triangle,
    title: alt.Title,
    mark_scaler: int,
    uncertainty: bool = True,
    uncertainty_type: Literal["ribbon", "segments"] = "ribbon",
) -> alt.Chart:
    if "earned_premium" not in triangle.fields:
        raise ValueError(
            "Triangle must contain `earned_premium` to plot its right edge. "
            f"This triangle contains {triangle.fields}"
        )

    loss_fields = [field for field in triangle.right_edge.fields if "_loss" in field]

    loss_data = alt.Data(
        values=[
            *[
                {
                    **_core_plot_data(cell),
                    **_calculate_field_summary(
                        cell=cell,
                        prev_cell=None,
                        func=lambda ob: ob[field] / ob["earned_premium"],
                        name="loss_ratio",
                    ),
                    "Field": field.replace("_loss", "").title() + " LR",
                }
                for cell in triangle.right_edge
                for field in loss_fields
                if "earned_premium" in cell
            ]
        ]
    )

    premium_data = alt.Data(
        values=[
            *[
                {
                    "period_start": pd.to_datetime(cell.period_start),
                    "period_end": pd.to_datetime(cell.period_end),
                    "evaluation_date": pd.to_datetime(cell.evaluation_date),
                    "dev_lag": cell.dev_lag(),
                    "Earned Premium": cell["earned_premium"],
                    "Field": "Earned Premium",
                }
                for cell in triangle.right_edge
                if "earned_premium" in cell
            ]
        ]
    )

    currency = _currency_symbol(triangle)

    bar = (
        alt.Chart(premium_data, title=title)
        .mark_bar()
        .encode(
            x=alt.X("yearmonth(period_start):O"),
            y=alt.Y("Earned Premium:Q").axis(format="$.2s"),
            color=alt.Color("Field:N").scale(range=["lightgray"]),
            tooltip=[
                alt.Tooltip("period_start:T", title="Period Start"),
                alt.Tooltip("period_end:T", title="Period End"),
                alt.Tooltip("dev_lag:O", title="Dev Lag"),
                alt.Tooltip("evaluation_date:T", title="Evaluation Date"),
                alt.Tooltip("Earned Premium:Q", format=f"{currency},.0f"),
            ],
        )
    )

    if uncertainty and uncertainty_type == "ribbon":
        loss_error = (
            alt.Chart(loss_data)
            .mark_area(
                opacity=0.5,
            )
            .encode(
                x=alt.X("yearmonth(period_start):T"),
                y=alt.Y("loss_ratio_lower_ci:Q").axis(title="Loss Ratio %", format="%"),
                y2=alt.Y2("loss_ratio_upper_ci:Q"),
                color=alt.Color("Field:N"),
            )
        )
    elif uncertainty and uncertainty_type == "segments":
        loss_error = (
            alt.Chart(loss_data)
            .mark_errorbar(thickness=3)
            .encode(
                x=alt.X("yearmonth(period_start):T").title("Period Start"),
                y=alt.Y("loss_ratio_lower_ci:Q").axis(title="Loss Ratio %", format="%"),
                y2=alt.Y2("loss_ratio_upper_ci:Q"),
                color=alt.Color("Field:N"),
            )
        )
    else:
        loss_error = alt.LayerChart()

    lines = (
        alt.Chart(loss_data)
        .mark_line(
            size=1,
        )
        .encode(
            x=alt.X("yearmonth(period_start):T", axis=alt.Axis(labelAngle=0)).title(
                "Period Start"
            ),
            y=alt.Y(
                "loss_ratio:Q", scale=alt.Scale(zero=True), axis=alt.Axis(format="%")
            ).title("Loss Ratio %"),
            color=alt.Color("Field:N"),
        )
    ).interactive()

    points = (
        alt.Chart(loss_data)
        .mark_point(
            size=max(20, 100 / mark_scaler),
            filled=True,
            opacity=1,
        )
        .encode(
            x=alt.X("yearmonth(period_start):T", axis=alt.Axis(labelAngle=0)).title(
                "Period Start"
            ),
            y=alt.Y(
                "loss_ratio:Q", scale=alt.Scale(zero=True), axis=alt.Axis(format="%")
            ),
            color=alt.Color("Field:N").legend(title=None),
            tooltip=[
                alt.Tooltip("period_start:T", title="Period Start"),
                alt.Tooltip("period_end:T", title="Period End"),
                alt.Tooltip("dev_lag:O", title="Dev Lag"),
                alt.Tooltip("evaluation_date:T", title="Evaluation Date"),
                alt.Tooltip("loss_ratio:Q", title="Loss Ratio (%)", format=".2%"),
            ],
        )
    )

    fig = alt.layer(bar, loss_error + lines + points).resolve_scale(
        y="independent",
        color="independent",
    )

    return fig.interactive()


def plot_data_completeness(
    triangle: Triangle,
    hide_samples: bool = False,
    width: int = 400,
    height: int = 300,
    ncols: int | None = None,
    facet_titles: list[str] | None = None,
) -> alt.Chart:
    main_title = alt.Title(
        "Triangle Completeness",
        subtitle="The number of data fields available per cell",
    )
    n_slices = len(triangle.slices)
    max_cols = ncols or _determine_facet_cols(n_slices)
    fig = _build_metric_slice_charts(
        _remove_triangle_samples(triangle) if hide_samples else triangle,
        plot_func=_plot_data_completeness,
        title=main_title,
        facet_titles=facet_titles,
        width=width,
        height=height,
        mark_scaler=max_cols,
        ncols=max_cols,
    ).configure_axis(**_compute_font_sizes(max_cols))
    return fig


def _plot_data_completeness(
    triangle: Triangle, title: alt.Title, mark_scaler: int
) -> alt.Chart:
    if not triangle.is_disjoint:
        raise Exception(
            "This triangle isn't disjoint! You probably don't want to use it"
        )
    if not triangle.is_semi_regular:
        raise Exception(
            "This triangle isn't semi-regular! You probably don't want to use it"
        )

    currency = _currency_symbol(triangle)

    selection = alt.selection_point()

    cell_data = alt.Data(
        values=[
            *[
                {
                    "period_start": pd.to_datetime(cell.period_start),
                    "period_end": pd.to_datetime(cell.period_end),
                    "evaluation_date": pd.to_datetime(cell.evaluation_date),
                    "dev_lag": cell.dev_lag(),
                    "Number of Fields": len(cell.values),
                    "Fields": ", ".join(
                        [
                            field.replace("_", " ").title()
                            + f" ({currency}{np.mean(cell[field]):,.0f})"
                            for field in cell.values
                        ]
                    ),
                }
                for cell in triangle.cells
            ]
        ]
    )

    fig = (
        alt.Chart(
            cell_data,
            title=title,
        )
        .mark_circle(size=500 * 1 / mark_scaler, opacity=1)
        .encode(
            alt.X(
                "dev_lag:N", axis=alt.Axis(labelAngle=0), scale=alt.Scale(zero=True)
            ).title("Dev Lag (months)"),
            alt.Y(
                "yearmonth(period_start):T", scale=alt.Scale(padding=15, reverse=True)
            ).title("Period Start"),
            color=alt.condition(
                selection,
                alt.Color("Number of Fields:N").scale(scheme="dark2"),
                alt.value("lightgray"),
            ),
            tooltip=[
                alt.Tooltip("period_start:T", title="Period Start"),
                alt.Tooltip("period_end:T", title="Period End"),
                alt.Tooltip("evaluation_date:T", title="Evaluation Date"),
                alt.Tooltip("dev_lag:N", title="Dev Lag (months)"),
                alt.Tooltip("Fields:N"),
            ],
        )
        .add_params(selection)
    )

    return fig.interactive()


def plot_heatmap(
    triangle: Triangle,
    metric_spec: MetricFuncSpec = ["Paid Loss Ratio"],
    hide_samples: bool = False,
    show_values: bool = True,
    width: int = 400,
    height: int = 200,
    ncols: int | None = None,
    facet_titles: list[str] | None = None,
) -> alt.Chart:
    """Plot triangle metrics as a heatmap."""
    main_title = alt.Title(
        "Triangle Heatmap",
    )
    metric_dict = _resolve_metric_spec(metric_spec)
    n_metrics = len(metric_dict)
    n_slices = len(triangle.slices)
    max_cols = ncols or _determine_facet_cols(n_slices * n_metrics)
    fig = (
        _build_metric_slice_charts(
            _remove_triangle_samples(triangle) if hide_samples else triangle,
            plot_func=_plot_heatmap,
            metric_dict=metric_dict,
            title=main_title,
            facet_titles=facet_titles,
            width=width,
            height=height,
            mark_scaler=max_cols,
            ncols=max_cols,
            show_values=show_values,
        )
        .resolve_scale(color="independent")
        .resolve_legend(color="independent")
    )
    return fig


def _plot_heatmap(
    triangle: Triangle,
    metric: MetricFunc,
    name: str,
    show_values: bool,
    title: alt.Title,
    mark_scaler: int,
) -> alt.Chart:
    metric_data = alt.Data(
        values=[
            {
                **_core_plot_data(cell),
                **_calculate_field_summary(cell, prev_cell, metric, "metric"),
                "Field": name,
            }
            for cell, prev_cell in zip(triangle, [None, *triangle[:-1]])
        ]
    )

    base = alt.Chart(metric_data, title=title).encode(
        x=alt.X("dev_lag:N", axis=alt.Axis(labelAngle=0)).title("Dev Lag (months)"),
        y=alt.X("yearmonth(period_start):O", scale=alt.Scale(reverse=False)).title(
            "Period Start"
        ),
    )

    stroke_predicate = alt.datum.metric_sd / alt.datum.metric > 0
    selection = alt.selection_interval()
    heatmap = (
        base.mark_rect()
        .encode(
            color=alt.when(selection)
            .then(
                alt.Color(
                    "metric:Q",
                    scale=alt.Scale(scheme="blueorange"),
                    legend=alt.Legend(title=name, format=".2s"),
                ).title(name)
            )
            .otherwise(
                alt.value("gray"),
            ),
            tooltip=[
                alt.Tooltip("period_start:T", title="Period Start"),
                alt.Tooltip("period_end:T", title="Period End"),
                alt.Tooltip("evaluation_date:T", title="Evaluation Date"),
                alt.Tooltip("dev_lag:O", title="Dev Lag (months)"),
                alt.Tooltip("metric:Q", title=name),
            ],
            stroke=alt.when(stroke_predicate).then(alt.value("black")),
            strokeWidth=alt.when(stroke_predicate)
            .then(alt.value(3))
            .otherwise(alt.value(0)),
        )
        .add_params(selection)
    )

    if show_values:
        text = base.mark_text(
            fontSize=BASE_AXIS_TITLE_FONT_SIZE
            * np.exp(-FONT_SIZE_DECAY_FACTOR * mark_scaler),
            font="monospace",
        ).encode(text=alt.Text("metric:Q", format=".2s"))

        return heatmap + text
    return heatmap.resolve_scale(color="independent")


def plot_atas(
    triangle: Triangle,
    metric_spec: MetricFuncSpec = ["Paid ATA"],
    hide_samples: bool = False,
    ncols: int | None = None,
    width: int = 400,
    height: int = 200,
    facet_titles: list[str] | None = None,
) -> alt.Chart:
    """Plot triangle ATAs."""
    main_title = alt.Title(
        "Triangle ATAs",
    )
    metric_dict = _resolve_metric_spec(metric_spec)
    n_metrics = len(metric_dict)
    n_slices = len(triangle.slices)
    max_cols = ncols or _determine_facet_cols(n_slices * n_metrics)
    fig = (
        _build_metric_slice_charts(
            _remove_triangle_samples(triangle) if hide_samples else triangle,
            plot_func=_plot_atas,
            metric_dict=metric_dict,
            title=main_title,
            facet_titles=facet_titles,
            width=width,
            height=height,
            ncols=max_cols,
        )
        .configure_axis(**_compute_font_sizes(max_cols))
        .configure_legend(**_compute_font_sizes(max_cols))
        .resolve_scale(color="independent")
    )
    return fig


def _plot_atas(
    triangle: Triangle, metric: MetricFunc, name: str, title: alt.Title
) -> alt.Chart:
    metric_data = alt.Data(
        values=[
            {
                **_core_plot_data(cell),
                **_calculate_field_summary(cell, prev_cell, metric, "metric"),
                "Field": name,
            }
            for cell, prev_cell in zip(triangle, [None, *triangle[:-1]])
        ]
    )

    tooltip = [
        alt.Tooltip("period_start:T", title="Period Start"),
        alt.Tooltip("period_end:T", title="Period End"),
        alt.Tooltip("evaluation_date:T", title="Evaluation Date"),
        alt.Tooltip("dev_lag:Q", title="Dev Lag (months)"),
        alt.Tooltip("metric:Q", title=name, format=".2f"),
    ]

    base = alt.Chart(metric_data, title=title).encode(
        x=alt.X("dev_lag:Q").title("Dev Lag (months)").scale(padding=10),
        y=alt.X("metric:Q").title(name).scale(zero=False, padding=10),
        tooltip=tooltip,
    )

    points = base.mark_point(color="black", filled=True)
    boxplot = base.mark_boxplot(
        opacity=0.7,
        color="skyblue",
        median=alt.MarkConfig(stroke="black"),
        rule=alt.MarkConfig(stroke="black"),
        box=alt.MarkConfig(stroke="black"),
    )
    errors = base.mark_errorbar(thickness=1).encode(
        y=alt.Y("metric_lower_ci:Q").axis(title=name),
        y2=alt.Y2("metric_upper_ci:Q"),
        color=alt.value("black"),
        opacity=alt.value(0.7),
    )

    return (points + errors + boxplot).interactive()


def plot_growth_curve(
    triangle: Triangle,
    metric_spec: MetricFuncSpec = ["Paid Loss Ratio"],
    hide_samples: bool = False,
    uncertainty: bool = True,
    uncertainty_type: Literal["ribbon", "segments", "spaghetti"] = "ribbon",
    n_lines: int = 100,
    seed: int | None = None,
    width: int = 400,
    height: int = 300,
    ncols: int | None = None,
    facet_titles: list[str] | None = None,
) -> alt.Chart:
    """Plot triangle metrics as a growth curve."""
    main_title = alt.Title(
        "Triangle Growth Curve",
    )
    metric_dict = _resolve_metric_spec(metric_spec)
    n_metrics = len(metric_dict)
    n_slices = len(triangle.slices)
    max_cols = ncols or _determine_facet_cols(n_slices * n_metrics)
    fig = (
        _build_metric_slice_charts(
            _remove_triangle_samples(triangle) if hide_samples else triangle,
            plot_func=_plot_growth_curve,
            metric_dict=metric_dict,
            uncertainty=uncertainty,
            uncertainty_type=uncertainty_type,
            n_lines=n_lines,
            seed=seed,
            mark_scaler=max_cols,
            title=main_title,
            facet_titles=facet_titles,
            width=width,
            height=height,
            ncols=max_cols,
        )
        .configure_axis(**_compute_font_sizes(max_cols))
        .configure_legend(**_compute_font_sizes(max_cols))
    )
    return fig


def _plot_growth_curve(
    triangle: Triangle,
    metric: MetricFunc,
    name: str,
    title: alt.Title,
    uncertainty: bool,
    uncertainty_type: Literal["ribbon", "segments", "spaghetti"],
    mark_scaler: int,
    n_lines: int = 100,
    seed: int | None = None,
) -> alt.Chart:
    if uncertainty_type == "spaghetti":
        triangle_thinned = triangle.thin(num_samples=n_lines)
        spaghetti_data = alt.Data(
            values=[
                {
                    **_core_plot_data(cell),
                    "metric_sample": value,
                    "iteration": i,
                }
                for cell, prev_cell in zip(
                    triangle_thinned, [None, *triangle_thinned[:-1]]
                )
                for i, value in enumerate(
                    _scalar_or_array_to_iter(
                        _safe_apply_metric(cell, prev_cell, metric)
                    )
                )
            ]
        )

    metric_data = alt.Data(
        values=[
            {
                **_core_plot_data(cell),
                "last_lag": max(
                    triangle.filter(lambda ob: ob.period == cell.period).dev_lags()
                ),
                **_calculate_field_summary(cell, prev_cell, metric, "metric"),
            }
            for cell, prev_cell in zip(triangle, [None, *triangle[:-1]])
        ]
    )

    color = (
        alt.Color("yearmonth(period_start):Q")
        .scale(scheme="blueorange", reverse=True)
        .legend(title="Period Start")
    )
    color_none = color.legend(None)

    selector = alt.selection_point(fields=["period_start"])
    color_conditional = alt.when(selector).then(color).otherwise(alt.value("lightgray"))
    color_conditional_no_legend = (
        alt.when(selector).then(color_none).otherwise(alt.value("lightgray"))
    )
    opacity_conditional = (
        alt.when(selector).then(alt.OpacityValue(1)).otherwise(alt.OpacityValue(0.2))
    )

    base = alt.Chart(metric_data, title=title).encode(
        x=alt.X(
            "dev_lag:Q",
            axis=alt.Axis(grid=True, labelAngle=0),
            scale=alt.Scale(padding=5),
        ).title("Dev Lag (months)"),
        y=alt.Y("metric:Q", axis=alt.Axis(format=".2s")).title(name),
        tooltip=[
            alt.Tooltip("period_start:T", title="Period Start"),
            alt.Tooltip("period_end:T", title="Period End"),
            alt.Tooltip("evaluation_date:T", title="Evaluation Date"),
            alt.Tooltip("dev_lag:Q", title="Dev Lag (months)"),
            alt.Tooltip("metric:Q", format=",.1f", title=name),
        ],
    )

    lines = base.mark_line(opacity=0.2).encode(color=color_conditional_no_legend)

    points = base.mark_point(stroke=None, filled=True).encode(
        color=color_conditional_no_legend,
        opacity=opacity_conditional,
    )

    ultimates = (
        base.mark_point(size=300 / mark_scaler, filled=True, stroke=None)
        .encode(
            color=color_conditional,
            opacity=opacity_conditional,
            strokeOpacity=opacity_conditional,
        )
        .transform_filter(alt.datum.last_lag == alt.datum.dev_lag)
    )

    if uncertainty and uncertainty_type == "ribbon":
        ribbon_opacity_conditional = (
            alt.when(selector)
            .then(alt.OpacityValue(0.5))
            .otherwise(alt.OpacityValue(0.2))
        )
        errors = base.mark_area(
            opacity=0.5,
        ).encode(
            y=alt.Y("metric_lower_ci:Q"),
            y2=alt.Y2("metric_upper_ci:Q"),
            color=color_conditional_no_legend,
            opacity=ribbon_opacity_conditional,
        )
    elif uncertainty and uncertainty_type == "segments":
        errors = base.mark_errorbar(thickness=5).encode(
            y=alt.Y("metric_lower_ci:Q").axis(title=name),
            y2=alt.Y2("metric_upper_ci:Q"),
            color=color_conditional_no_legend,
            opacity=opacity_conditional,
        )
    elif uncertainty and uncertainty_type == "spaghetti":
        errors = (
            alt.Chart(spaghetti_data)
            .mark_line(opacity=0.2)
            .encode(
                x=alt.X("dev_lag:Q"),
                y=alt.X("metric_sample:Q"),
                detail="iteration:N",
                color=color_conditional_no_legend,
            )
        )
    else:
        errors = alt.LayerChart()

    if len(triangle.periods) == 1:
        scale_color = "shared"
    else:
        scale_color = "independent"

    return (
        alt.layer(errors + lines + points, ultimates.add_params(selector))
        .resolve_scale(color=scale_color)
        .interactive()
    )


def plot_sunset(
    triangle: Triangle,
    metric_spec: MetricFuncSpec = ["Paid Incremental ATA"],
    hide_samples: bool = False,
    uncertainty: bool = True,
    uncertainty_type: Literal["ribbon", "segments"] = "ribbon",
    width: int = 400,
    height: int = 200,
    ncols: int | None = None,
    facet_titles: list[str] | None = None,
) -> alt.Chart:
    """Plot triangle metrics as a sunset."""
    main_title = alt.Title(
        "Triangle Sunset",
    )
    metric_dict = _resolve_metric_spec(metric_spec)
    n_metrics = len(metric_dict)
    n_slices = len(triangle.slices)
    max_cols = ncols or _determine_facet_cols(n_slices * n_metrics)
    fig = (
        _build_metric_slice_charts(
            _remove_triangle_samples(triangle) if hide_samples else triangle,
            plot_func=_plot_sunset,
            metric_dict=metric_dict,
            uncertainty=uncertainty,
            uncertainty_type=uncertainty_type,
            mark_scaler=max_cols,
            title=main_title,
            facet_titles=facet_titles,
            width=width,
            height=height,
            ncols=max_cols,
        )
        .configure_axis(**_compute_font_sizes(max_cols))
        .configure_legend(**_compute_font_sizes(max_cols))
    )
    return fig.interactive()


def _plot_sunset(
    triangle: Triangle,
    metric: MetricFunc,
    name: str,
    title: alt.Title,
    mark_scaler: int,
    uncertainty: bool,
    uncertainty_type: Literal["ribbon", "segments"],
) -> alt.Chart:
    metric_data = alt.Data(
        values=[
            *[
                {
                    **_core_plot_data(cell),
                    **_calculate_field_summary(cell, prev_cell, metric, name),
                }
                for cell, prev_cell in zip(triangle, [None, *triangle[:-1]])
            ]
        ]
    )

    color = (
        alt.Color("dev_lag:Q")
        .scale(scheme="blueorange")
        .legend(title="Development Lag")
    )
    color_none = color.legend(None)

    selector = alt.selection_point(fields=["dev_lag"])
    opacity_conditional = (
        alt.when(selector).then(alt.OpacityValue(1)).otherwise(alt.OpacityValue(0.2))
    )
    color_conditional = alt.when(selector).then(color).otherwise(alt.value("lightgray"))
    color_conditional_no_legend = (
        alt.when(selector).then(color_none).otherwise(alt.value("lightgray"))
    )

    base = alt.Chart(metric_data, title=title).encode(
        x=alt.X(
            "yearmonth(evaluation_date):O", axis=alt.Axis(grid=True, labelAngle=0)
        ).title("Calendar Year"),
        y=alt.X(f"{name}:Q").title(name).scale(type="pow", exponent=0.3),
        tooltip=[
            alt.Tooltip("period_start:T", title="Period Start"),
            alt.Tooltip("period_end:T", title="Period End"),
            alt.Tooltip("evaluation_date:T", title="Evaluation Date"),
            alt.Tooltip("dev_lag:Q", title="Dev Lag (months)"),
            alt.Tooltip(f"{name}:Q", format=",.1f", title=name),
        ],
    )

    points = base.mark_point(stroke=None, size=30 / mark_scaler, filled=True).encode(
        color=color_conditional,
        opacity=opacity_conditional,
        strokeOpacity=opacity_conditional,
    )
    regression = (
        base.transform_loess(
            "evaluation_date", f"{name}", groupby=["dev_lag"], bandwidth=0.6
        )
        .mark_line(strokeWidth=2)
        .encode(color=color_conditional_no_legend, opacity=opacity_conditional)
    )

    if uncertainty and uncertainty_type == "ribbon":
        ribbon_conditional = (
            alt.when(selector)
            .then(alt.OpacityValue(0.5))
            .otherwise(alt.OpacityValue(0.2))
        )
        errors = base.mark_area().encode(
            y=alt.Y(f"{name}_lower_ci:Q").axis(title=name),
            y2=alt.Y2(f"{name}_upper_ci:Q"),
            color=color_conditional_no_legend,
            opacity=ribbon_conditional,
        )
    elif uncertainty and uncertainty_type == "segments":
        errors = base.mark_errorbar(thickness=5).encode(
            y=alt.Y(f"{name}_lower_ci:Q").axis(title=name),
            y2=alt.Y2(f"{name}_upper_ci:Q"),
            color=color_conditional_no_legend,
            opacity=opacity_conditional,
        )
    else:
        errors = alt.LayerChart()

    return (
        alt.layer(errors, regression, points)
        .add_params(selector)
        .resolve_scale(color="independent")
    )


def plot_mountain(
    triangle: Triangle,
    metric_spec: MetricFuncSpec = ["Paid Loss Ratio"],
    hide_samples: bool = False,
    uncertainty: bool = True,
    uncertainty_type: Literal["ribbon", "segments"] = "ribbon",
    width: int = 400,
    height: int = 200,
    ncols: int | None = None,
    facet_titles: list[str] | None = None,
    highlight_ultimates: bool = True,
) -> alt.Chart:
    """Plot triangle metrics as a mountain."""
    main_title = alt.Title(
        "Triangle Mountain Plot",
    )
    metric_dict = _resolve_metric_spec(metric_spec)
    n_metrics = len(metric_dict)
    n_slices = len(triangle.slices)
    max_cols = ncols or _determine_facet_cols(n_slices * n_metrics)
    legend_direction = "horizontal" if highlight_ultimates else "vertical"
    fig = (
        _build_metric_slice_charts(
            _remove_triangle_samples(triangle) if hide_samples else triangle,
            plot_func=_plot_mountain,
            metric_dict=metric_dict,
            uncertainty=uncertainty,
            uncertainty_type=uncertainty_type,
            highlight_ultimates=highlight_ultimates,
            mark_scaler=max_cols,
            title=main_title,
            facet_titles=facet_titles,
            width=width,
            height=height,
            ncols=max_cols,
        )
        .configure_axis(**_compute_font_sizes(max_cols))
        .configure_legend(**_compute_font_sizes(max_cols), direction=legend_direction)
    )
    return fig.interactive()


def _plot_mountain(
    triangle: Triangle,
    metric: MetricFunc,
    name: str,
    title: alt.Title,
    mark_scaler: int,
    uncertainty: bool,
    uncertainty_type: Literal["ribbon", "segments"],
    highlight_ultimates: bool = True,
) -> alt.Chart:
    metric_triangle = (
        triangle.clip(max_dev=triangle.dev_lags()[-2])
        if highlight_ultimates
        else triangle
    )
    metric_data = alt.Data(
        values=[
            {
                **_core_plot_data(cell),
                "last_lag": max(
                    triangle.filter(lambda ob: ob.period == cell.period).dev_lags()
                ),
                **_calculate_field_summary(cell, prev_cell, metric, "metric"),
                "Field": name,
            }
            for cell, prev_cell in zip(metric_triangle, [None, *metric_triangle[:-1]])
        ]
    )

    if highlight_ultimates:
        ultimate_triangle = triangle.right_edge
        ultimate_data = alt.Data(
            values=[
                {
                    **_core_plot_data(cell),
                    **_calculate_field_summary(cell, prev_cell, metric, "metric"),
                    "Field": name,
                }
                for cell, prev_cell in zip(
                    ultimate_triangle, [None, *ultimate_triangle[:-1]]
                )
            ]
        )

    color = (
        alt.Color("dev_lag:Q")
        .scale(scheme="blueorange")
        .legend(title="Development Lag")
    )
    color_none = color.legend(None)

    selector = alt.selection_point(fields=["dev_lag"])
    opacity_conditional = (
        alt.when(selector).then(alt.OpacityValue(1)).otherwise(alt.OpacityValue(0.2))
    )

    tooltip = [
        alt.Tooltip("period_start:T", title="Period Start"),
        alt.Tooltip("period_end:T", title="Period End"),
        alt.Tooltip("evaluation_date:T", title="Evaluation Date"),
        alt.Tooltip("dev_lag:Q", title="Dev Lag (months)"),
        alt.Tooltip("metric:Q", format=",.1f", title=name),
    ]

    base = alt.Chart(metric_data, title=title).encode(
        x=alt.X(
            "yearmonth(period_start):O", axis=alt.Axis(grid=True, labelAngle=0)
        ).title("Period Start"),
        y=alt.Y("metric:Q", axis=alt.Axis(format=".2s")).title(name),
        tooltip=tooltip,
    )

    lines = base.mark_line().encode(color=color_none, opacity=opacity_conditional)
    points = base.mark_point(filled=True, stroke=None).encode(
        color=color,
        opacity=opacity_conditional,
    )

    if uncertainty and uncertainty_type == "ribbon":
        ribbon_conditional = (
            alt.when(selector)
            .then(alt.OpacityValue(0.5))
            .otherwise(alt.OpacityValue(0.2))
        )
        errors = base.mark_area().encode(
            y=alt.Y("metric_lower_ci:Q"),
            y2=alt.Y2("metric_upper_ci:Q"),
            color=color_none,
            opacity=ribbon_conditional,
        )
    elif uncertainty and uncertainty_type == "segments":
        errors = base.mark_errorbar(thickness=5).encode(
            y=alt.Y("metric_lower_ci:Q").axis(title=name),
            y2=alt.Y2("metric_upper_ci:Q"),
            color=color_none,
            opacity=opacity_conditional,
        )
    else:
        errors = alt.LayerChart()

    if highlight_ultimates:
        ultimate_color = alt.Color("dev_lag:Q").scale(scheme="greys")
        ultimate_base = alt.Chart(ultimate_data).encode(
            x=alt.X(
                "yearmonth(period_start):O", axis=alt.Axis(grid=True, labelAngle=0)
            ).title("Period Start"),
            y=alt.X("metric:Q").title(name),
            tooltip=tooltip,
            order=alt.value(1),
        )
        ultimates = ultimate_base.mark_line().encode(
            color=ultimate_color.legend(title="Ultimate Lag")
        )
        ultimates += ultimate_base.mark_point(filled=True).encode(
            color=ultimate_color,
        )

        if uncertainty and uncertainty_type == "ribbon":
            ultimates += ultimate_base.mark_area().encode(
                y=alt.Y("metric_lower_ci:Q"),
                y2=alt.Y2("metric_upper_ci:Q"),
                color=ultimate_color,
                opacity=ribbon_conditional,
            )
        if uncertainty and uncertainty_type == "segments":
            ultimates += ultimate_base.mark_errorbar(thickness=5).encode(
                y=alt.Y("metric_lower_ci:Q").axis(title=name),
                y2=alt.Y2("metric_upper_ci:Q"),
                color=ultimate_color,
                opacity=opacity_conditional,
            )
    else:
        ultimates = alt.LayerChart()

    return alt.layer(
        lines + errors,
        points.add_params(selector),
        ultimates,
    ).resolve_scale(color="independent")


def plot_ballistic(
    triangle: Triangle,
    axis_metrics: MetricFuncDict = {
        "Paid Loss Ratio": lambda cell: 100
        * cell["paid_loss"]
        / cell["earned_premium"],
        "Reported Loss Ratio": lambda cell: 100
        * cell["reported_loss"]
        / cell["earned_premium"],
    },
    hide_samples: bool = False,
    uncertainty: bool = True,
    width: int = 400,
    height: int = 200,
    ncols: int | None = None,
    facet_titles: list[str] | None = None,
) -> alt.Chart:
    """Plot triangle metrics as a ballistic."""
    main_title = alt.Title(
        "Triangle Ballistic Plot",
    )
    n_slices = len(triangle.slices)
    max_cols = ncols or _determine_facet_cols(n_slices)
    fig = _build_metric_slice_charts(
        _remove_triangle_samples(triangle) if hide_samples else triangle,
        plot_func=_plot_ballistic,
        axis_metrics=axis_metrics,
        title=main_title,
        facet_titles=facet_titles,
        uncertainty=uncertainty,
        width=width,
        height=height,
        mark_scaler=max_cols,
        ncols=max_cols,
    ).configure_axis(**_compute_font_sizes(max_cols))
    return fig


def _plot_ballistic(
    triangle: Triangle,
    axis_metrics: MetricFuncDict,
    title: alt.Title,
    mark_scaler: int,
    uncertainty: bool,
) -> alt.Chart:
    (name_x, name_y), (func_x, func_y) = zip(*axis_metrics.items())

    metric_data = alt.Data(
        values=[
            *[
                {
                    **_core_plot_data(cell),
                    "last_lag": max(
                        triangle.filter(lambda ob: ob.period == cell.period).dev_lags()
                    ),
                    **_calculate_field_summary(cell, prev_cell, func_x, name_x),
                    **_calculate_field_summary(cell, prev_cell, func_y, name_y),
                }
                for cell, prev_cell in zip(triangle, [None, *triangle[:-1]])
            ]
        ]
    )

    color = (
        alt.Color("dev_lag:Q")
        .scale(scheme="blueorange")
        .legend(title="Development Lag (months)")
    )
    color_none = color.legend(None)

    selector = alt.selection_point(fields=["period_start"])
    opacity_conditional = (
        alt.when(selector).then(alt.OpacityValue(1)).otherwise(alt.OpacityValue(0.2))
    )
    color_conditional = alt.when(selector).then(color).otherwise(alt.value("lightgray"))
    color_conditional_no_legend = (
        alt.when(selector).then(color_none).otherwise(alt.value("lightgray"))
    )

    base = alt.Chart(metric_data, title=title).encode(
        x=alt.X(f"{name_x}:Q").title(name_x).axis(grid=True),
        y=alt.X(f"{name_y}:Q").title(name_y).axis(grid=True),
        tooltip=[
            alt.Tooltip("period_start:T", title="Period Start"),
            alt.Tooltip("period_end:T", title="Period End"),
            alt.Tooltip("evaluation_date:T", title="Evaluation Date"),
            alt.Tooltip("dev_lag:Q", title="Dev Lag (months)"),
            alt.Tooltip(f"{name_x}:Q", format=".1f"),
            alt.Tooltip(f"{name_y}:Q", format=".1f"),
        ],
    )

    diagonal = (
        alt.Chart(metric_data)
        .mark_line(color="black", strokeDash=[5, 5])
        .encode(
            x=f"{name_x}:Q",
            y=f"{name_x}:Q",
        )
    )

    lines = base.mark_line(color="black", strokeWidth=0.5).encode(
        detail="period_start:N", opacity=opacity_conditional
    )
    points = base.mark_point(filled=True, size=100 / mark_scaler, stroke=None).encode(
        color=color_conditional, opacity=opacity_conditional
    )
    ultimates = (
        base.mark_point(size=200 / mark_scaler, filled=True, stroke=None)
        .encode(color=color_conditional, opacity=opacity_conditional)
        .transform_filter(alt.datum.last_lag == alt.datum.dev_lag)
    )

    if uncertainty:
        errors = base.mark_errorbar(thickness=5).encode(
            y=alt.Y(f"{name_y}_lower_ci:Q").axis(title=name_y),
            y2=alt.Y2(f"{name_y}_upper_ci:Q"),
            color=color_conditional_no_legend,
        )
    else:
        errors = alt.LayerChart()

    return (
        alt.layer(diagonal, errors + lines, (points + ultimates).add_params(selector))
        .resolve_scale(color="independent")
        .interactive()
    )


def plot_broom(
    triangle: Triangle,
    axis_metrics: MetricFuncDict = {
        "Paid/Reported Ratio": lambda cell: cell["paid_loss"] / cell["reported_loss"],
        "Paid Loss Ratio": lambda cell: 100
        * cell["paid_loss"]
        / cell["earned_premium"],
    },
    hide_samples: bool = False,
    rule: int | None = 1,
    uncertainty: bool = True,
    width: int = 400,
    height: int = 200,
    ncols: int | None = None,
    facet_titles: list[str] | None = None,
) -> alt.Chart:
    """Plot triangle metrics as a broom."""
    main_title = alt.Title(
        "Triangle Broom Plot",
    )
    n_slices = len(triangle.slices)
    max_cols = ncols or _determine_facet_cols(n_slices)
    fig = _build_metric_slice_charts(
        _remove_triangle_samples(triangle) if hide_samples else triangle,
        plot_func=_plot_broom,
        axis_metrics=axis_metrics,
        title=main_title,
        facet_titles=facet_titles,
        uncertainty=uncertainty,
        rule=rule,
        width=width,
        height=height,
        mark_scaler=max_cols,
        ncols=max_cols,
    ).configure_axis(**_compute_font_sizes(max_cols))
    return fig.interactive()


def _plot_broom(
    triangle: Triangle,
    axis_metrics: MetricFuncDict,
    title: alt.Title,
    mark_scaler: int,
    uncertainty: bool,
    rule: int | None,
) -> alt.Chart:
    (name_x, name_y), (func_x, func_y) = zip(*axis_metrics.items())

    metric_data = alt.Data(
        values=[
            *[
                {
                    **_core_plot_data(cell),
                    "last_lag": max(
                        triangle.filter(lambda ob: ob.period == cell.period).dev_lags()
                    ),
                    **_calculate_field_summary(cell, prev_cell, func_x, name_x),
                    **_calculate_field_summary(cell, prev_cell, func_y, name_y),
                }
                for cell, prev_cell in zip(triangle, [None, *triangle[:-1]])
            ]
        ]
    )

    color = (
        alt.Color("dev_lag:Q")
        .scale(scheme="blueorange")
        .legend(title="Development Lag (months)")
    )
    color_none = color.legend(None)

    selector = alt.selection_point(fields=["period_start"])
    opacity_conditional = (
        alt.when(selector).then(alt.OpacityValue(1)).otherwise(alt.OpacityValue(0.2))
    )
    color_conditional = alt.when(selector).then(color).otherwise(alt.value("lightgray"))
    color_conditional_no_legend = (
        alt.when(selector).then(color_none).otherwise(alt.value("lightgray"))
    )

    base = alt.Chart(metric_data, title=title).encode(
        x=alt.X(f"{name_x}:Q").scale(padding=10, nice=False).title(name_x),
        y=alt.Y(f"{name_y}:Q").title(name_y),
        tooltip=[
            alt.Tooltip("period_start:T", title="Period Start"),
            alt.Tooltip("period_end:T", title="Period End"),
            alt.Tooltip("evaluation_date:T", title="Evaluation Date"),
            alt.Tooltip("dev_lag:Q", title="Dev Lag (months)"),
            alt.Tooltip(f"{name_x}:Q", format=".1f"),
            alt.Tooltip(f"{name_y}:Q", format=".1f"),
        ],
    )

    wall = (
        alt.Chart().mark_rule(strokeDash=[12, 5], opacity=0.5, strokeWidth=2)
    ).encode()
    if rule is not None:
        wall = wall.encode(x=alt.datum(rule))

    lines = base.mark_line(color="black", strokeWidth=0.5).encode(
        detail="period_start:N", opacity=opacity_conditional
    )
    points = base.mark_point(filled=True, size=100 / mark_scaler, stroke=None).encode(
        color=color_conditional,
        opacity=opacity_conditional,
        strokeOpacity=opacity_conditional,
    )
    ultimates = (
        base.mark_point(size=300 / mark_scaler, filled=True, stroke=None)
        .encode(
            color=color_conditional,
            opacity=opacity_conditional,
            strokeOpacity=opacity_conditional,
        )
        .transform_filter(alt.datum.last_lag == alt.datum.dev_lag)
    )

    if uncertainty:
        errors = base.mark_errorbar(thickness=5).encode(
            x=alt.X(f"{name_x}_lower_ci:Q").axis(title=name_x),
            x2=alt.X2(f"{name_x}_upper_ci:Q"),
            color=color_conditional_no_legend,
        )
    else:
        errors = alt.LayerChart()

    return alt.layer(
        errors + lines + wall, (points + ultimates).add_params(selector)
    ).resolve_scale(color="independent")


def plot_drip(
    triangle: Triangle,
    axis_metrics: MetricFuncDict = {
        "Reported Loss Ratio": lambda cell: 100
        * cell["reported_loss"]
        / cell["earned_premium"],
        "Open Claim Share": lambda cell: 100
        * cell["open_claims"]
        / cell["reported_claims"],
    },
    hide_samples: bool = False,
    uncertainty: bool = True,
    width: int = 400,
    height: int = 300,
    ncols: int | None = None,
    facet_titles: list[str] | None = None,
) -> alt.Chart:
    """Plot triangle metrics as a drip."""
    main_title = alt.Title(
        "Triangle Drip Plot",
    )
    n_slices = len(triangle.slices)
    max_cols = ncols or _determine_facet_cols(n_slices)
    fig = (
        _build_metric_slice_charts(
            _remove_triangle_samples(triangle) if hide_samples else triangle,
            plot_func=_plot_drip,
            axis_metrics=axis_metrics,
            title=main_title,
            facet_titles=facet_titles,
            uncertainty=uncertainty,
            width=width,
            height=height,
            mark_scaler=max_cols,
            ncols=max_cols,
        )
        .configure_axis(**_compute_font_sizes(max_cols))
        .resolve_scale(color="independent")
    )
    return fig.interactive()


def _plot_drip(
    triangle: Triangle,
    axis_metrics: MetricFuncDict,
    title: alt.Title,
    uncertainty: bool,
    mark_scaler: int,
) -> alt.Chart:
    (name_x, name_y), (func_x, func_y) = zip(*axis_metrics.items())

    metric_data = alt.Data(
        values=[
            *[
                {
                    **_core_plot_data(cell),
                    "last_lag": max(
                        triangle.filter(lambda ob: ob.period == cell.period).dev_lags()
                    ),
                    **_calculate_field_summary(cell, prev_cell, func_x, name_x),
                    **_calculate_field_summary(cell, prev_cell, func_y, name_y),
                }
                for cell, prev_cell in zip(triangle, [None, *triangle[:-1]])
            ]
        ]
    )

    color = (
        alt.Color("dev_lag:Q")
        .scale(scheme="blueorange")
        .legend(title="Development Lag (months)")
    )
    color_none = color.legend(None)

    selector = alt.selection_point(fields=["period_start"])
    opacity_conditional = (
        alt.when(selector).then(alt.OpacityValue(1)).otherwise(alt.OpacityValue(0.2))
    )
    color_conditional = alt.when(selector).then(color).otherwise(alt.value("lightgray"))
    color_conditional_no_legend = (
        alt.when(selector).then(color_none).otherwise(alt.value("lightgray"))
    )

    base = alt.Chart(metric_data, title=title).encode(
        x=alt.X(f"{name_x}:Q").title(name_x, padding=10),
        y=alt.Y(f"{name_y}:Q").title(name_y).scale(nice=False, padding=10),
        tooltip=[
            alt.Tooltip("period_start:T", title="Period Start"),
            alt.Tooltip("period_end:T", title="Period End"),
            alt.Tooltip("evaluation_date:T", title="Evaluation Date"),
            alt.Tooltip("dev_lag:Q", title="Dev Lag (months)"),
            alt.Tooltip(f"{name_x}:Q", format=".1f"),
            alt.Tooltip(f"{name_y}:Q", format=".1f"),
        ],
    )

    lines = base.mark_line(color="black", strokeWidth=0.5).encode(
        detail="period_start:N", opacity=opacity_conditional
    )
    points = base.mark_point(filled=True, size=100 / mark_scaler, stroke=None).encode(
        color=color_conditional, opacity=opacity_conditional
    )
    ultimates = (
        base.mark_point(size=300 / mark_scaler, filled=True, stroke=None)
        .encode(color=color_conditional, opacity=opacity_conditional)
        .transform_filter(alt.datum.last_lag == alt.datum.dev_lag)
    )

    if uncertainty:
        errors = base.mark_errorbar(thickness=5).encode(
            y=alt.Y(f"{name_y}_lower_ci:Q").title(name_y),
            y2=alt.Y2(f"{name_y}_upper_ci:Q"),
            color=color_conditional_no_legend,
        )
    else:
        errors = alt.LayerChart()

    return alt.layer(
        errors + lines, (points + ultimates).add_params(selector)
    ).resolve_scale(color="independent")


def plot_hose(
    triangle: Triangle,
    axis_metrics: MetricFuncDict = {
        "Paid Loss Ratio": lambda cell: 100
        * cell["paid_loss"]
        / cell["earned_premium"],
        "Incremental Paid Loss Ratio": lambda cell, prev_cell: 100
        * (
            cell["paid_loss"] / cell["earned_premium"]
            - prev_cell["paid_loss"] / prev_cell["earned_premium"]
        ),
    },
    hide_samples: bool = False,
    uncertainty: bool = True,
    width: int = 400,
    height: int = 300,
    ncols: int | None = None,
    facet_titles: list[str] | None = None,
) -> alt.Chart:
    return plot_drip(
        triangle,
        axis_metrics,
        hide_samples,
        uncertainty,
        width,
        height,
        ncols,
        facet_titles,
    ).properties(title="Triangle Hose Plot")


def plot_histogram(
    triangle: Triangle,
    metric_spec: MetricFuncSpec = "Paid Loss",
    right_edge: bool = True,
    hide_samples: bool = False,
    width: int = 400,
    height: int = 200,
    ncols: int | None = None,
    facet_titles: list[str] | None = None,
) -> alt.Chart:
    main_title = alt.Title("Triangle Histogram")
    metric_dict = _resolve_metric_spec(metric_spec)
    n_slices = len(triangle.slices)
    n_metrics = len(metric_spec)
    max_cols = ncols or _determine_facet_cols(n_slices * n_metrics)
    fig = _build_metric_slice_charts(
        _remove_triangle_samples(triangle) if hide_samples else triangle,
        plot_func=_plot_histogram,
        metric_dict=metric_dict,
        title=main_title,
        right_edge=right_edge,
        facet_titles=facet_titles,
        width=width,
        height=height,
        ncols=max_cols,
    ).configure_axis(**_compute_font_sizes(max_cols))
    return fig


def _plot_histogram(
    triangle: Triangle,
    metric: MetricFunc,
    name: str,
    right_edge: bool,
    title: alt.Title,
) -> alt.Chart:
    if right_edge:
        triangle = triangle.right_edge

    metric_data = alt.Data(
        values=[
            {
                name: value,
                "iteration": i,
            }
            for cell in triangle
            for i, value in enumerate(_scalar_or_array_to_iter(metric(cell)))
        ]
    )

    histogram = (
        alt.Chart(metric_data, title=title)
        .mark_bar()
        .encode(
            x=alt.X(f"{name}:Q", axis=alt.Axis(format=".2s"))
            .bin({"maxbins": 50})
            .title(name),
            y=alt.Y("count()").title("Count"),
        )
    )

    return histogram


def _build_metric_slice_charts(
    triangle, plot_func, title, facet_titles, width, height, ncols, **plot_kwargs
):
    charts = []
    n_slices = len(triangle.slices)
    for i, (_, triangle_slice) in enumerate(triangle.slices.items()):
        if facet_titles is None:
            slice_title = _slice_label(triangle_slice, triangle)
        else:
            slice_title = facet_titles[i]
        if plot_kwargs.get("metric_dict") is not None:
            for name, metric in plot_kwargs["metric_dict"].items():
                metric_title = (
                    (n_slices > 1) * (slice_title + ": ") + name
                    if facet_titles is None
                    else slice_title
                )
                charts.append(
                    plot_func(
                        triangle=triangle_slice,
                        metric=metric,
                        name=name,
                        title=alt.Title(metric_title, **SLICE_TITLE_KWARGS),
                        **{k: v for k, v in plot_kwargs.items() if k != "metric_dict"},
                    ).properties(width=width, height=height)
                )
        else:
            charts.append(
                plot_func(
                    triangle=triangle_slice,
                    title=alt.Title(slice_title, **SLICE_TITLE_KWARGS),
                    **plot_kwargs,
                ).properties(width=width, height=height)
            )
    fig = (
        _concat_charts(charts, title=title, ncols=ncols)
        .configure_axis(**_compute_font_sizes(ncols))
        .configure_legend(**_compute_font_sizes(ncols))
        .configure_mark(color="#1f8fff")
    )
    return fig


def _core_plot_data(cell: Cell) -> dict[str, Any]:
    return {
        "period_start": pd.to_datetime(cell.period_start),
        "period_end": pd.to_datetime(cell.period_end),
        "evaluation_date": pd.to_datetime(cell.evaluation_date),
        "dev_lag": cell.dev_lag(),
    }


def _calculate_field_summary(
    cell: Cell,
    prev_cell: Cell | None,
    func: MetricFunc,
    name: str,
    probs: tuple[float, float] = (0.05, 0.95),
):
    metric = _safe_apply_metric(cell, prev_cell, func)

    if metric is None:
        return {
            f"{name}": None,
            f"{name}_sd": None,
            f"{name}_lower_ci": None,
            f"{name}_upper_ci": None,
        }

    if np.isscalar(metric) or len(metric) == 1:
        return {
            f"{name}": metric,
            f"{name}_sd": 0,
            f"{name}_lower_ci": None,
            f"{name}_upper_ci": None,
        }

    point = np.mean(metric)
    lower, upper = np.quantile(metric, probs)
    return {
        f"{name}": point,
        f"{name}_sd": metric.std(),
        f"{name}_lower_ci": lower,
        f"{name}_upper_ci": upper,
    }


def _safe_apply_metric(cell: Cell, prev_cell: Cell | None, func: MetricFunc):
    try:
        if prev_cell.period != cell.period:
            raise IndexError
        return func(cell, prev_cell)
    except Exception:
        try:
            return func(cell)
        except Exception:
            return None


def _compute_font_sizes(mark_scaler: int) -> dict[str, float | int]:
    return {
        "titleFontSize": BASE_AXIS_TITLE_FONT_SIZE
        * np.exp(-FONT_SIZE_DECAY_FACTOR * (mark_scaler - 1)),
        "labelFontSize": BASE_AXIS_LABEL_FONT_SIZE
        * np.exp(-FONT_SIZE_DECAY_FACTOR * (mark_scaler - 1)),
    }


def _currency_symbol(triangle: Triangle) -> str:
    code = triangle.metadata[0].currency
    return get_currency_symbol(code, locale="en_US") or "$"


def _concat_charts(charts: list[alt.Chart], ncols: int, **kwargs) -> alt.Chart:
    if len(charts) == 1:
        return charts[0].properties(**kwargs)

    fig = alt.concat(*charts, columns=ncols, **kwargs)
    return fig


def _determine_facet_cols(n: int):
    """This is a replication of grDevices::n2mfrow in R"""
    return int(min(n, np.ceil(n / np.sqrt(n))))


def _slice_label(slice_tri: Triangle, base_tri: Triangle):
    slice_metadata = metadata_diff(base_tri.common_metadata, slice_tri.common_metadata)

    # Custom elements
    custom_elems = []
    for label, value in {
        **slice_metadata.details,
        **slice_metadata.loss_details,
    }.items():
        custom_elems.append(f"{string.capwords(label)}: {value}")

    # Bare elements
    bare_elems = []
    if slice_metadata.country is not None:
        bare_elems.append(slice_metadata.country)
    if slice_metadata.reinsurance_basis is not None:
        bare_elems.append(slice_metadata.reinsurance_basis)
    if slice_metadata.loss_definition is not None:
        bare_elems.append(slice_metadata.loss_definition)

    # Decorated elements
    decorated_elems = []
    if slice_metadata.per_occurrence_limit is not None:
        decorated_elems.append(f"limit {slice_metadata.per_occurrence_limit}")
    if slice_metadata.risk_basis is not None:
        decorated_elems.append(f"{slice_metadata.risk_basis} Basis")
    if slice_metadata.currency is not None:
        decorated_elems.append(f"in {slice_metadata.currency}")

    custom_label = ", ".join(custom_elems)
    bare_label = " ".join(bare_elems)
    decorated_label = "(" + ", ".join(decorated_elems) + ")"

    label = ""
    if custom_label:
        label += custom_label
    if label and bare_label:
        label += "; "
    if bare_label:
        label += bare_label
    if label and len(decorated_label) > 2:
        label += " "
    if len(decorated_label) > 2:
        label += decorated_label

    return label


def _scalar_or_array_to_iter(x: float | int | list | np.ndarray) -> np.ndarray:
    if np.isscalar(x) or x is None:
        return np.array([x])
    return x
