from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, Input, Output, State, dcc, html


# ---------- Load data ----------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "sales_dashboard.csv"

df = pd.read_csv(
    DATA_PATH,
    encoding="utf-8-sig",
    parse_dates=["OrderDate"],
)

MIN_DATE = df["OrderDate"].min().date().isoformat()
MAX_DATE = df["OrderDate"].max().date().isoformat()

playback_months = pd.date_range(
    df["OrderDate"].min().to_period("M").start_time,
    df["OrderDate"].max().to_period("M").start_time,
    freq="MS",
)

playback_labels = [
    month.strftime("%b %Y") for month in playback_months
]

# Prepare playback data once instead of regrouping all sales every tick.
playback_data = (
    df.assign(
        Month=df["OrderDate"].dt.to_period("M").dt.to_timestamp()
    )
    .groupby(
        ["Month", "Channel", "Country", "Product"],
        as_index=False,
    )
    .agg(Revenue=("Sales Amount", "sum"))
)


# ---------- App and styles ----------
app = Dash(__name__)
app.title = "AdventureWorks Sales Dashboard"

BLUE = "#2563eb"
GREEN = "#16a34a"
RED = "#dc2626"
TEXT = "#0f172a"
MUTED = "#64748b"

PANEL = {
    "backgroundColor": "white",
    "border": "1px solid #e2e8f0",
    "borderRadius": "16px",
    "padding": "24px",
    "marginBottom": "24px",
    "boxShadow": "0 4px 16px rgba(15, 23, 42, 0.04)",
    "minWidth": "0",
}

BUTTON = {
    "backgroundColor": BLUE,
    "color": "white",
    "border": "none",
    "borderRadius": "8px",
    "padding": "12px 20px",
    "fontWeight": "600",
    "cursor": "pointer",
}

LABEL = {
    "display": "block",
    "fontSize": "14px",
    "fontWeight": "600",
    "marginBottom": "10px",
    "color": "#475569",
}

GRAPH_CONFIG = {"displaylogo": False}


# ---------- Helpers ----------
def filter_sales(channel, country, start_date=None, end_date=None):
    mask = pd.Series(True, index=df.index)

    if channel != "All":
        mask &= df["Channel"].eq(channel)

    if country != "All":
        mask &= df["Country"].eq(country)

    if start_date:
        mask &= df["OrderDate"].ge(pd.Timestamp(start_date))

    if end_date:
        mask &= df["OrderDate"].lt(
            pd.Timestamp(end_date) + pd.Timedelta(days=1)
        )

    return df.loc[mask]


def kpi_card(label, value):
    return html.Div(
        [
            html.P(label, style={"color": MUTED, "margin": "0"}),
            html.H2(
                value,
                style={
                    "margin": "12px 0 0",
                    "fontSize": "clamp(22px, 2.2vw, 30px)",
                    "overflowWrap": "anywhere",
                },
            ),
        ],
        style={
            "backgroundColor": "white",
            "padding": "24px",
            "borderRadius": "12px",
            "border": "1px solid #e2e8f0",
            "borderTop": f"4px solid {BLUE}",
            "flex": "1 1 200px",
            "minWidth": "0",
        },
    )


def style_chart(fig, height=450):
    fig.update_layout(
        template="plotly_white",
        height=height,
        autosize=True,
        font={"family": "Arial, sans-serif", "color": TEXT, "size": 13},
        title={"x": 0.02, "font": {"size": 18}},
        margin={"l": 35, "r": 40, "t": 85, "b": 55},
        paper_bgcolor="white",
        plot_bgcolor="white",
    )
    fig.update_xaxes(automargin=True)
    fig.update_yaxes(automargin=True)
    return fig


def empty_chart(
    title,
    message="No sales found for the selected filters",
    height=450,
):
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
        font={"size": 17, "color": MUTED},
    )
    style_chart(fig, height)
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return fig


# ---------- Layout ----------
app.layout = html.Div(
    [
        html.Div(
            [
                # Header
                html.Div(
                    [
                        html.Div(
                            [
                                html.P(
                                    "ADVENTUREWORKS • SALES ANALYTICS",
                                    style={
                                        "color": BLUE,
                                        "fontSize": "12px",
                                        "fontWeight": "700",
                                        "letterSpacing": "2px",
                                    },
                                ),
                                html.H1(
                                    "Sales & Profitability",
                                    style={
                                        "margin": "8px 0",
                                        "fontSize": "clamp(26px, 4vw, 38px)",
                                    },
                                ),
                                html.P(
                                    f"Available sales: "
                                    f"{df['OrderDate'].min():%d %b %Y}"
                                    f" – {df['OrderDate'].max():%d %b %Y}",
                                    style={"color": MUTED},
                                ),
                            ]
                        ),
                        html.Button(
                            "Reset analysis filters",
                            id="reset-filters",
                            n_clicks=0,
                            style=BUTTON,
                        ),
                    ],
                    style={
                        "display": "flex",
                        "justifyContent": "space-between",
                        "alignItems": "center",
                        "flexWrap": "wrap",
                        "gap": "16px",
                        "marginBottom": "24px",
                    },
                ),

                # Filters
                html.Div(
                    [
                        html.Div(
                            [
                                html.Label("Sales channel", style=LABEL),
                                dcc.Dropdown(
                                    id="channel-filter",
                                    options=[
                                        {"label": "All channels", "value": "All"},
                                        {"label": "Internet", "value": "Internet"},
                                        {"label": "Reseller", "value": "Reseller"},
                                    ],
                                    value="All",
                                    clearable=False,
                                ),
                            ],
                            style={"flex": "1 1 220px", "minWidth": "0"},
                        ),
                        html.Div(
                            [
                                html.Label("Country", style=LABEL),
                                dcc.Dropdown(
                                    id="country-filter",
                                    options=[
                                        {"label": "All countries", "value": "All"},
                                        *[
                                            {"label": name, "value": name}
                                            for name in sorted(
                                                df["Country"].dropna().unique()
                                            )
                                        ],
                                    ],
                                    value="All",
                                    clearable=False,
                                ),
                            ],
                            style={"flex": "1 1 220px", "minWidth": "0"},
                        ),
                        html.Div(
                            [
                                html.Label("Order date range", style=LABEL),
                                dcc.DatePickerRange(
                                    id="date-filter",
                                    min_date_allowed=MIN_DATE,
                                    max_date_allowed=MAX_DATE,
                                    start_date=MIN_DATE,
                                    end_date=MAX_DATE,
                                    display_format="DD MMM YYYY",
                                    minimum_nights=0,
                                    clearable=False,
                                    number_of_months_shown=1,
                                ),
                            ],
                            style={
                                "flex": "2 1 320px",
                                "minWidth": "0",
                                "overflowX": "auto",
                            },
                        ),
                    ],
                    style={
                        **PANEL,
                        "display": "flex",
                        "flexWrap": "wrap",
                        "gap": "24px",
                        "alignItems": "flex-start",
                    },
                ),

                html.Div(
                    id="kpi-cards",
                    style={
                        "display": "flex",
                        "flexWrap": "wrap",
                        "gap": "16px",
                        "marginBottom": "16px",
                    },
                ),

                html.P(
                    "Gross profit = revenue − product cost; it is not net profit. "
                    "June 2020 contains partial-month data. "
                    "Currency has not been verified; amounts use source-data units.",
                    style={
                        "fontSize": "13px",
                        "color": MUTED,
                        "lineHeight": "1.7",
                        "marginBottom": "24px",
                    },
                ),

                html.Div(
                    dcc.Graph(
                        id="monthly-chart",
                        config=GRAPH_CONFIG,
                        responsive=True,
                        style={"height": "500px"},
                    ),
                    style=PANEL,
                ),

                html.Div(
                    dcc.Graph(
                        id="category-profit-chart",
                        config=GRAPH_CONFIG,
                        responsive=True,
                        style={"height": "420px"},
                    ),
                    style=PANEL,
                ),

                html.Div(
                    [
                        html.Label("Product ranking", style=LABEL),
                        dcc.Dropdown(
                            id="product-ranking",
                            options=[
                                {
                                    "label": "Top 10 profitable products",
                                    "value": "profit",
                                },
                                {
                                    "label": "Top 10 loss-making products",
                                    "value": "loss",
                                },
                            ],
                            value="profit",
                            clearable=False,
                            style={"maxWidth": "360px"},
                        ),
                        dcc.Graph(
                            id="product-profit-chart",
                            config=GRAPH_CONFIG,
                            responsive=True,
                            style={"height": "600px"},
                        ),
                    ],
                    style=PANEL,
                ),

                # Playback: controls, slider, then a fixed-height chart.
                html.Div(
                    [
                        html.P(
                            "EXPLORE THROUGH TIME",
                            style={
                                "color": BLUE,
                                "fontSize": "12px",
                                "fontWeight": "700",
                                "letterSpacing": "2px",
                            },
                        ),
                        html.H2("Monthly product playback"),
                        html.P(
                            "Historical monthly revenue, not live sales. "
                            "Uses Channel and Country filters above. "
                            "The analysis date range and product ranking "
                            "do not apply here.",
                            style={
                                "color": MUTED,
                                "fontSize": "14px",
                                "lineHeight": "1.7",
                            },
                        ),
                        html.Div(
                            [
                                html.Button(
                                    "▶ Play",
                                    id="playback-button",
                                    n_clicks=0,
                                    style=BUTTON,
                                ),
                                html.H3(
                                    id="playback-month-label",
                                    style={"margin": "0", "color": BLUE},
                                ),
                            ],
                            style={
                                "display": "flex",
                                "alignItems": "center",
                                "flexWrap": "wrap",
                                "gap": "20px",
                                "minHeight": "60px",
                                "margin": "16px 0",
                            },
                        ),
                        html.H3(
    "Monthly revenue of the overall top 10 products",
    style={"marginBottom": "8px"},
),

html.P(
    "Products are selected by total revenue across the available period "
    "for the chosen Channel and Country. "
    "Their order and revenue scale stay fixed during playback.",
    style={"color": MUTED, "fontSize": "13px", "lineHeight": "1.7"},
),

html.Div(
    id="animated-product-bars",
    className="animated-products",
),

                        html.Div(
                            dcc.Slider(
                                id="playback-slider",
                                min=0,
                                max=len(playback_months) - 1,
                                step=1,
                                value=0,
                                marks={
                                    i: label
                                    for i, label in enumerate(playback_labels)
                                    if i % 6 == 0
                                    or i == len(playback_labels) - 1
                                },
                            ),
                            style={
                                "padding": "12px 16px 40px",
                                "minHeight": "95px",
                                "boxSizing": "border-box",
                                "position": "relative",
                                "flexShrink": "0",
                            },
                        ),

                        html.Div(
                            dcc.Graph(
                                id="playback-product-chart",
                                config=GRAPH_CONFIG,
                                responsive=True,
                                style={
                                    "height": "550px",
                                    "width": "100%",
                                },
                            ),
                            style={
                                "height": "550px",
                                "minHeight": "550px",
                                "position": "relative",
                                "flexShrink": "0",
                            },
                        ),

                        dcc.Interval(
                            id="playback-timer",
                            interval=1500,
                            n_intervals=0,
                            disabled=True,
                        ),
                    ],
                    style={
                        **PANEL,
                        "display": "flex",
                        "flexDirection": "column",
                    },
                ),

                html.P(
                    "AdventureWorks portfolio project • "
                    "Built by Md Abdul Wahid Raju • Python / Dash / Plotly",
                    style={
                        "textAlign": "center",
                        "color": MUTED,
                        "fontSize": "12px",
                        "padding": "12px 0",
                    },
                ),
            ],
            style={"maxWidth": "1400px", "margin": "0 auto"},
        )
    ],
    style={
        "fontFamily": "Arial, sans-serif",
        "backgroundColor": "#f1f5f9",
        "color": TEXT,
        "minHeight": "100vh",
        "padding": "24px",
        "boxSizing": "border-box",
    },
)


# ---------- KPI and monthly chart ----------
@app.callback(
    Output("kpi-cards", "children"),
    Output("monthly-chart", "figure"),
    Input("channel-filter", "value"),
    Input("country-filter", "value"),
    Input("date-filter", "start_date"),
    Input("date-filter", "end_date"),
)
def update_dashboard(channel, country, start_date, end_date):
    filtered = filter_sales(channel, country, start_date, end_date)

    revenue = filtered["Sales Amount"].sum()
    profit = filtered["GrossProfit"].sum()
    orders = filtered["Sales Order"].nunique()
    margin_text = f"{profit / revenue * 100:.2f}%" if revenue else "N/A"

    cards = [
        kpi_card("Revenue", f"{revenue:,.2f}"),
        kpi_card("Gross profit", f"{profit:,.2f}"),
        kpi_card("Gross margin", margin_text),
        kpi_card("Orders", f"{orders:,}"),
    ]

    if filtered.empty:
        return cards, empty_chart(
            "Monthly revenue and gross profit", height=500
        )

    monthly = (
        filtered.groupby(pd.Grouper(key="OrderDate", freq="MS"))
        .agg(
            Revenue=("Sales Amount", "sum"),
            GrossProfit=("GrossProfit", "sum"),
        )
        .reset_index()
        .rename(columns={"GrossProfit": "Gross profit"})
    )

    channel_label = "All channels" if channel == "All" else channel
    country_label = "All countries" if country == "All" else country

    fig = px.line(
        monthly,
        x="OrderDate",
        y=["Revenue", "Gross profit"],
        markers=True,
        title=(
            f"Monthly revenue and gross profit"
            f"<br><sup>{channel_label} | {country_label}</sup>"
        ),
        labels={
            "OrderDate": "Month",
            "value": "Amount",
            "variable": "Metric",
        },
        color_discrete_map={
            "Revenue": BLUE,
            "Gross profit": GREEN,
        },
    )

    style_chart(fig, 500)
    fig.update_layout(
        hovermode="x unified",
        legend_title_text="",
        legend={"orientation": "h", "y": 1.02, "x": 0},
    )
    fig.update_traces(hovertemplate="%{y:,.2f}")
    fig.update_xaxes(rangeslider_visible=True)
    fig.update_yaxes(zeroline=True, zerolinecolor="#94a3b8")

    return cards, fig


# ---------- Category chart ----------
@app.callback(
    Output("category-profit-chart", "figure"),
    Input("channel-filter", "value"),
    Input("country-filter", "value"),
    Input("date-filter", "start_date"),
    Input("date-filter", "end_date"),
)
def update_category_profit(channel, country, start_date, end_date):
    filtered = filter_sales(channel, country, start_date, end_date)

    if filtered.empty:
        return empty_chart("Gross profit by category", height=420)

    category = (
        filtered.groupby("Category", as_index=False)
        .agg(
            Revenue=("Sales Amount", "sum"),
            GrossProfit=("GrossProfit", "sum"),
        )
        .sort_values("GrossProfit")
    )

    fig = px.bar(
        category,
        x="GrossProfit",
        y="Category",
        orientation="h",
        text="GrossProfit",
        hover_data={"Revenue": ":,.2f"},
        title="Gross profit by category",
        labels={"GrossProfit": "Gross profit"},
    )

    fig.update_traces(
        marker_color=[
            RED if value < 0 else GREEN
            for value in category["GrossProfit"]
        ],
        texttemplate="%{x:,.0f}",
        textposition="auto",
    )

    style_chart(fig, 420)
    fig.update_yaxes(
        categoryorder="array",
        categoryarray=category["Category"].tolist(),
    )
    fig.update_xaxes(
        zeroline=True,
        zerolinewidth=2,
        zerolinecolor=MUTED,
    )
    return fig


# ---------- Product ranking ----------
@app.callback(
    Output("product-profit-chart", "figure"),
    Input("channel-filter", "value"),
    Input("country-filter", "value"),
    Input("date-filter", "start_date"),
    Input("date-filter", "end_date"),
    Input("product-ranking", "value"),
)
def update_product_chart(channel, country, start_date, end_date, ranking):
    filtered = filter_sales(channel, country, start_date, end_date)

    if filtered.empty:
        return empty_chart("Product profitability", height=600)

    products = (
        filtered.groupby("Product", as_index=False)
        .agg(
            Revenue=("Sales Amount", "sum"),
            GrossProfit=("GrossProfit", "sum"),
            UnitsSold=("Order Quantity", "sum"),
        )
    )

    if ranking == "profit":
        selected = products.loc[
            products["GrossProfit"] > 0
        ].nlargest(10, "GrossProfit")
        title = "Top 10 profitable products"
        color = GREEN
        no_results = "No profitable products for the selected filters"
    else:
        selected = products.loc[
            products["GrossProfit"] < 0
        ].nsmallest(10, "GrossProfit")
        title = "Top 10 loss-making products"
        color = RED
        no_results = "No loss-making products for the selected filters"

    if selected.empty:
        return empty_chart(title, no_results, height=600)

    fig = px.bar(
        selected,
        x="GrossProfit",
        y="Product",
        orientation="h",
        text="GrossProfit",
        hover_data={
            "Revenue": ":,.2f",
            "UnitsSold": ":,",
            "GrossProfit": ":,.2f",
        },
        labels={
            "GrossProfit": "Gross profit",
            "UnitsSold": "Units sold",
        },
        title=title,
    )

    fig.update_traces(
        marker_color=color,
        texttemplate="%{x:,.0f}",
        textposition="auto",
    )
    style_chart(fig, 600)
    fig.update_yaxes(
        categoryorder="array",
        categoryarray=selected["Product"].tolist(),
        autorange="reversed",
    )
    fig.update_xaxes(
        zeroline=True,
        zerolinewidth=2,
        zerolinecolor=MUTED,
    )
    return fig


# ---------- Reset analysis filters ----------
@app.callback(
    Output("channel-filter", "value"),
    Output("country-filter", "value"),
    Output("date-filter", "start_date"),
    Output("date-filter", "end_date"),
    Output("product-ranking", "value"),
    Input("reset-filters", "n_clicks"),
    prevent_initial_call=True,
)
def reset_filters(n_clicks):
    return "All", "All", MIN_DATE, MAX_DATE, "profit"


# ---------- Playback controls ----------
@app.callback(
    Output("playback-timer", "disabled"),
    Output("playback-button", "children"),
    Input("playback-button", "n_clicks"),
)
def toggle_playback(n_clicks):
    playing = (n_clicks or 0) % 2 == 1
    return not playing, "⏸ Pause" if playing else "▶ Play"


@app.callback(
    Output("playback-slider", "value"),
    Input("playback-timer", "n_intervals"),
    State("playback-slider", "value"),
    prevent_initial_call=True,
)
def advance_playback(n_intervals, current_month):
    return (int(current_month or 0) + 1) % len(playback_months)


@app.callback(
    Output("playback-month-label", "children"),
    Input("playback-slider", "value"),
)
def show_playback_month(month_index):
    month_index = int(month_index or 0)
    label = playback_labels[month_index]

    if month_index == len(playback_months) - 1:
        label += " — partial month"

    return label


# ---------- Playback chart ----------
@app.callback(
    Output("playback-product-chart", "figure"),
    Input("playback-slider", "value"),
    Input("channel-filter", "value"),
    Input("country-filter", "value"),
)
def update_playback_products(month_index, channel, country):
    month_index = int(month_index or 0)
    selected_month = playback_months[month_index]
    month_label = playback_labels[month_index]

    if month_index == len(playback_months) - 1:
        month_label += " (partial month)"

    filtered = playback_data

    if channel != "All":
        filtered = filtered.loc[filtered["Channel"] == channel]

    if country != "All":
        filtered = filtered.loc[filtered["Country"] == country]

    monthly_products = (
        filtered.groupby(["Month", "Product"], as_index=False)
        .agg(Revenue=("Revenue", "sum"))
    )

    selected = (
        monthly_products.loc[
            monthly_products["Month"] == selected_month
        ]
        .nlargest(10, "Revenue")
        .sort_values("Revenue")
    )

    title = (
        "Top 10 products by monthly revenue"
        f"<br><sup>{month_label}</sup>"
    )

    if selected.empty:
        return empty_chart(title, height=550)

    # Fixed revenue scale across months for the selected channel/country.
    axis_max = monthly_products["Revenue"].max() * 1.15

    fig = px.bar(
        selected,
        x="Revenue",
        y="Product",
        orientation="h",
        text="Revenue",
        title=title,
        labels={"Revenue": "Monthly revenue"},
    )

    fig.update_traces(
        marker_color=BLUE,
        texttemplate="%{x:,.0f}",
        textposition="auto",
        hovertemplate="%{y}<br>Revenue: %{x:,.2f}<extra></extra>",
    )

    style_chart(fig, 550)
    fig.update_xaxes(range=[0, max(float(axis_max), 1)])
    fig.update_yaxes(
        categoryorder="array",
        categoryarray=selected["Product"].tolist(),
    )

    return fig
@app.callback(
    Output("animated-product-bars", "children"),
    Input("playback-slider", "value"),
    Input("channel-filter", "value"),
    Input("country-filter", "value"),
)
def update_animated_bars(month_index, channel, country):
    selected_month = playback_months[int(month_index or 0)]
    filtered = playback_data

    if channel != "All":
        filtered = filtered.loc[filtered["Channel"] == channel]

    if country != "All":
        filtered = filtered.loc[filtered["Country"] == country]

    if filtered.empty:
        return html.P("No sales found for the selected filters.")

    # Select the same products for the entire playback period.
    top_products = (
        filtered.groupby("Product")["Revenue"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .index.tolist()
    )

    monthly = (
        filtered.loc[filtered["Product"].isin(top_products)]
        .groupby(["Month", "Product"], as_index=False)
        .agg(Revenue=("Revenue", "sum"))
    )

    # Keep a fixed scale across all months.
    scale_max = max(float(monthly["Revenue"].max()), 1)

    month_values = (
        monthly.loc[monthly["Month"] == selected_month]
        .set_index("Product")["Revenue"]
    )

    colors = [
        "#60a5fa",
        "#38bdf8",
        "#2dd4bf",
        "#a78bfa",
        "#fbbf24",
        "#fb923c",
        "#f472b6",
        "#a3e635",
        "#818cf8",
        "#22d3ee",
    ]

    rows = []

    for index, product in enumerate(top_products):
        revenue = float(month_values.get(product, 0))
        width = max(0, min(revenue / scale_max * 100, 100))

        rows.append(
            html.Div(
                [
                    html.Div(
                        product,
                        className="animated-product-name",
                    ),
                    html.Div(
                        [
                            html.Div(
                                className="animated-product-bar",
                                style={
                                    "width": f"{width:.4f}%",
                                    "backgroundColor": colors[index],
                                },
                            ),
                            html.Span(
                                f"{revenue:,.0f}",
                                className="animated-product-value",
                            ),
                        ],
                        className="animated-product-track",
                    ),
                ],
                key=product,
                className="animated-product-row",
            )
        )

    return rows


# ---------- Start server ----------
if __name__ == "__main__":
    app.run(debug=False)