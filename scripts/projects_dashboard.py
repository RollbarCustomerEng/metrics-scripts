from metrics_base import get_all_projects
from metrics_base import add_read_token_to_projects
from metrics_base import get_item_metrics

import datetime
import logging
import math
import os
import pandas as pd
import time

from metrics_base import ItemMetrics
from tabulate import tabulate

"""
A script that generates a table view of the top X (default=20) items
with the highest occurrence counts in the last Y (default=30) days

This scripts loops through each project in the account and generates a table for each project

This was tested with Python 3.9.1

Requirements:
1. An environment variable ACCOUNT_READ_ACCESS_TOKEN_FOR_METRICS with an account level access
   token with read scope. Set the environment variable in the following way: 

export ACCOUNT_READ_ACCESS_TOKEN_FOR_METRICS=MyAccountAccessTokenWithReadScope

2. Review the DAYS variable. This is the number fo days teh script gets data for

3. Review the TOP_ITEM_LIST. The number of items to display in the table

4. Review the SORT_FIELD. 


5. In order to get data for a project, there MUST be a READ-ONLY scope token 
with an access token name of 'read' or 'metrics_api_token'

6. You need to install the following python packages

pip3 install request
pip3 install tabulate
pip3 install pandas

"""

# Read the environment variable
ACCOUNT_READ_TOKEN = os.environ['ACCOUNT_READ_ACCESS_TOKEN_FOR_METRICS']

# Last number fo days to get the data for
DAYS = 30

# The number of items to display in the table for each project
TOP_ITEM_LIST = 10

# Field to sort by. For example 'occurrence_count', 'ip_address_count' etc.
SORT_FIELD = 'ip_address_count'


def get_projects():
    proj_list = get_all_projects(ACCOUNT_READ_TOKEN)
    add_read_token_to_projects(proj_list, ACCOUNT_READ_TOKEN, ['metrics_api_token', 'read'])

    return proj_list

def get_last_x_days_metrics(proj, days):

    # last 24 hours
    final_time = datetime.datetime.now()
    start_time = final_time - datetime.timedelta(days=days)
    final_time_unix = math.floor(time.mktime(final_time.timetuple()))   
    start_time_unix = math.floor(time.mktime(start_time.timetuple()))

    metrics: ItemMetrics
    metrics = get_item_metrics(proj, start_time_unix, final_time_unix)

    metrics_list_of_dicts = []
    for item_metrics in metrics:
        metrics_list_of_dicts.append(item_metrics.__dict__)


    df = None 
    if len(metrics_list_of_dicts) > 0:
        df = pd.DataFrame(metrics_list_of_dicts)

    return df

def print_metrics(df_orig):

    df = df_orig
    del df['project_id']
    del df['start_time_unix']
    del df['end_time_unix']
    del df['id']

    # truncate the title
    df['title'] = df['title'].str.slice(0, 20)


    # df = df.nlargest(TOP_ITEM_LIST, 'ip_address_count')
    df = df.nlargest(TOP_ITEM_LIST, SORT_FIELD)

    print(tabulate(df, headers='keys', tablefmt='grid'))   
    print('')
    print()     

def generate_dashboard():
    print('Generate dashboard')
    proj_list = get_projects()


    for proj in proj_list:
        df = get_last_x_days_metrics(proj, DAYS)
        if df is not None:
            print_metrics(df)



if __name__ == "__main__":

    logging.basicConfig(level=logging.WARNING,
                format='%(process)d-%(levelname)s-%(message)s',
                handlers=[logging.StreamHandler()]
                )
    generate_dashboard()