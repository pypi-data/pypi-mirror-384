from KorAPClient import KorAPConnection

kcon = KorAPConnection(verbose=True)

q = kcon.corpusQuery("Ameisenplage", metadataOnly = True).fetchAll()
df = q.slots['collectedMatches']
print(df)

q = kcon.corpusQuery("Ameisenplage", metadataOnly = False).fetchAll()
df = q.slots['collectedMatches']
print(df)


q = kcon.corpusQuery("Ameisenplage", metadataOnly = False).fetchAll(True)

df = q.slots['collectedMatches']
print(df)

