import os
from tracemalloc import start
import requests
import datetime

url = "https://api.rollbar.com/api/1/metrics/occurrences"
project_token = os.environ['ROLLBAR_PROJECT_READ_ACCESS_TOKEN']

# https://www.epochconverter.com/


start_time = 1662033600
end_time = start_time + (1 * 24 * 60 * 60) # 1665587613


payload = {
    "start_time": start_time,
    "end_time": end_time,
    "filters": [{"field": "item_level",
                 "values": ['error', 'critical'],
                 "operator": "eq"
                 }
                ],
    "group_by": ["environment", "item_level"],
    "granularity": "hour",
    'aggregates': [
                    {
                        'field': 'person_id',
                        'function': 'count_distinct',
                        'alias': 'person_count'
                    }
                  ]
    }

headers = {
    "accept": "application/json",
    "X-Rollbar-Access-Token": project_token,
    "content-type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.text)

f = open('out.csv', 'w')
f.write(response.text)
f.close()
