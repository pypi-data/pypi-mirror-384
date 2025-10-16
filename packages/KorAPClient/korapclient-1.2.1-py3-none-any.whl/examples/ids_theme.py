#!/usr/bin/env python3
import altair as alt
import pandas as pd
import re
from KorAPClient import KorAPClient, KorAPConnection

QUERY = "Hello World"
YEARS = range(2010, 2019)
COUNTRIES = ["DE", "CH"]


def ids_theme():
#    font = "Fira Sans Condensed"
    font = "Times New Roman"
    primary_color = "#F63366"
    font_color = "#262730"
    grey_color = "#f0f2f6"
    base_size = 24
    lg_font = base_size * 1.25
    sm_font = base_size * 0.8  # st.table size
    xl_font = base_size * 1.75

    config = {
        "config": {
            "view": {"fill": grey_color, "continuousWidth": 1024, "continuousHeight": 600},
            "title": {
                "font": font,
                "color": font_color,
                "fontSize": lg_font,
                "anchor": "start",
            },
            "axis": {
                "titleFont": font,
#                "titleColor": font_color,
                "titleFontSize": sm_font,
                "labelFont": font,
#                "labelColor": font_color,
                "labelFontSize": sm_font,
                "domain": False,
                # "domainColor": font_color,
#                "tickColor": font_color,
            },
            "header": {
                "labelFont": font,
                "titleFont": font,
                "labelFontSize": base_size,
                "titleFontSize": base_size,
            },
            "legend": {
                "titleFont": font,
#                "titleColor": font_color,
                "titleFontSize": sm_font,
                "labelFont": font,
#                "labelColor": font_color,
                "labelFontSize": sm_font,
            },
            "tooltip" : {
                "tooltipFont": font
            }
        }
    }
    return config


alt.themes.register("ids_theme", ids_theme)
alt.themes.enable("ids_theme")
df = pd.DataFrame(YEARS, columns=["Year"], dtype=str).merge(pd.DataFrame(COUNTRIES, columns=["Country"]), how="cross")
df["vc"] = "textType=/Zeit.*/ & pubPlaceKey = " + df.Country + " & pubDate in " + df.Year

kcon = KorAPConnection(verbose=True)

df = KorAPClient.ipm(kcon.frequencyQuery(QUERY, df.vc)).merge(df)
df['tooltip'] = "ctrl+click to open concordances in new tab"

band = alt.Chart(df).mark_errorband().encode(
    y=alt.Y("conf.low", title="ipm"),
    y2="conf.high",
    x="Year:T",
    color="Country",
    tooltip=["Country", "Year", alt.Tooltip("ipm", format=".2f")]
)

line = alt.Chart(df).mark_line(point=True).encode(
    y="ipm",
    x="Year:T",
    color="Country",
    href="webUIRequestUrl",
    tooltip="tooltip"
)

chart = (band + line).properties(
    width="container",
    height='container'
)
fname="test.html"
chart['usermeta'] = {
    "embedOptions": {
        'loader': {'target': '_blank'}
    }
}
chart.save(fname)
with open(fname, "r") as sources:
    lines = sources.readlines()
with open(fname, "w") as sources:
    for line in lines:
        sources.write(re.sub(r'<div id="vis">', '<div style="height: 95vH; width: 100%;" id="vis">', line))
