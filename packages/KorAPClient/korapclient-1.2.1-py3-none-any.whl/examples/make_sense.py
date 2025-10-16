#!/usr/bin/env python3

from KorAPClient import KorAPConnection
import plotly.express as px
import pandas as pd

years = list(range(1980, 2011))
query = ["macht []{0,3} Sinn", "ergibt []{0,3} Sinn"]

df = pd.DataFrame({'year': years,
                   'vc': ["textType = /Zeit.*/ & availability!=QAO-NC-LOC:ids " +
                          f"& pubDate in {y}" for y in years]}) \
    .merge(pd.DataFrame(query, columns=["variant"]), how='cross')

results = KorAPConnection() \
    .frequencyQuery(df['variant'], df['vc'], **{"as.alternatives": True})
df = pd.concat([df, results.reset_index(drop=True)], axis=1)
px.line(df, x="year", y="f", color="variant").show()
