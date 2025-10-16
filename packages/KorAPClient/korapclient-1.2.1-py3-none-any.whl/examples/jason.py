import pandas as pd
from KorAPClient import KorAPConnection

YEARS = range(2017,2020)
vcs = [f"pubDate in {y}" for y in YEARS]
kcon = KorAPConnection(verbose=True)

df = pd.DataFrame()

for vc in vcs:
    q = kcon.corpusQuery("Hello World", vc, metadataOnly = False).fetchAll()
    df = df._append(q.slots['collectedMatches'])

print(df)
