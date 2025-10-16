#!/usr/bin/env python3
from KorAPClient import KorAPClient, KorAPConnection
import plotly.express as px
import os
import pandas

TITLE = "Adjectives + male/female singular nouns in different newspaper sources"

kcon = KorAPConnection(verbose=True)

# read list of newspapers to query separately
newspaper_sources = pandas.read_csv(os.getcwd() + "/" + "newspapers.csv", encoding='utf8')

# read queries and conditions from csv file
queries = pandas.read_csv(os.getcwd() + "/" + "queries.csv", encoding='utf8')

# init new data frame with all combinations of newspaper sources and queries
df = newspaper_sources.merge(queries, how='cross')

# add column vc with virtual corpora specifications
df['vc'] = ['corpusTitle="' + title + '"' for title in df["title"]]

# perform corpus queries
query_results = KorAPClient.ipm(kcon.frequencyQuery(df.q, df.vc))

# join query result columns (axis=1 ...) with condition information columns
# (why are these reset_indexex needed?)
df =  pandas.concat([df.reset_index(drop=True), query_results.reset_index(drop=True)], axis=1)

# export results
df.to_csv(os.getcwd() + "/" + "exported_data.csv", index=False)

# add confidence intervals the way plotly express way (relative to ipm values)
df['error_y_plus'] = df['conf.high'] - df['ipm']
df['error_y_minus'] = df['ipm'] - df['conf.low']

# show faceted bar plots
fig = px.bar(df, title=TITLE, x="term", y="ipm", error_y="error_y_plus", error_y_minus="error_y_minus", color="gender",
             barmode="group", facet_row="title")
fig.show()
