#!/usr/bin/python

from KorAPClient import KorAPConnection, KorAPClient
import plotly.express as px
import pandas as pd
import highcharts as hc
#plt.style.use("ggplot") # only for matplotlib >= 1.4

years = list(range(1980, 2011))
query = ["[tt/l=machen] []{0,3} [tt/l=Sinn]"]

df = pd.DataFrame({'year': years,
                   'vc': ["textType = /Zeit.*/ " +
                          "& availability!=QAO-NC-LOC:ids " +
                          f"& pubDate in {y}" for y in years]}) \
    .merge(pd.DataFrame(query, columns=["variant"]), how='cross')

results = KorAPClient.ipm(KorAPConnection(verbose=True) \
    .frequencyQuery(df['variant'], df['vc'], **{"as.alternatives": False}))
df = pd.concat([df, results.reset_index(drop=True)], axis=1)
df['error_y'] = df["conf.high"] - df["ipm"]
df['error_y_minus'] = df["ipm"] - df["conf.low"]
px.line(df, x="year", y="ipm", color="variant", error_y="error_y").show()
#df.plot_bokeh.scatter(x="year", y="f", color="variant", line_color="variant")
#df.plot(y="f");
##display_charts(df, title="Brownian Motion")

def df_to_hc(df, chart_type='bar'):
    H = hc.Highchart(width=750, height=600)
    options = {
        'xAxis': {
            'categories': list(df.columns)
        }
    }
    H.set_dict_options(options)
    # use .tolist() instead of list() to convert numpy to native types
    for r in list(df.index): H.add_data_set(df.loc[r].tolist(), chart_type, r)
    return H

#chart = df_to_hc(df, chart_type='line')
#chart.save_file()

