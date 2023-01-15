import json
import requests

url = "http://localhost:4001/db/execute"
payload = ["CREATE TABLE foo (id INTEGER NOT NULL PRIMARY KEY, name TEXT, age INTEGER)"]

# curl -XPOST 'localhost:4001/db/execute?pretty&timings' -H "Content-Type: application/json" -d '[
#     "CREATE TABLE foo (id INTEGER NOT NULL PRIMARY KEY, name TEXT, age INTEGER)"
# ]'

resp = requests.post(url=url, json=payload)
print(resp)
print(resp.text)
