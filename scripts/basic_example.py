import os
from tracemalloc import start
import requests
import time

url = "https://api.rollbar.com/api/1/metrics/occurrences"
project_token = os.environ["ROLLBAR_PROJECT_READ_ACCESS_TOKEN"]

# https://www.epochconverter.com/


   
end_time = int(time.time())
start_time = end_time - (14 * 24 * 60 * 60)


payload = {
    "start_time": start_time,
    "end_time": end_time,
    "filters": [{"field": "item_level",
                 "values": ["error"],
                 "operator": "eq"
                 },
                 {"field": "environment",
                 "values": ["production"],
                 "operator": "eq"
                 }

                ],
                "group_by": ["code_version", "item_level"],
                "aggregates": [
                    {
                        "field": "item_counter",
                        "function": "count_distinct",
                        "alias": "item_count"
                    },
                    {
                        "field": "person_id",
                        "function": "count_distinct",
                        "alias": "person_count"
                    },
                  ]
    }

headers = {
    "accept": "application/json",
    "X-Rollbar-Access-Token": project_token,
    "content-type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.text)

f = open("out.json", "w")
f.write(response.text)
f.close()
