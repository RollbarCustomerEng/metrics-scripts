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



ACCOUNT_READ_TOKEN = os.environ['ACCOUNT_READ_ACCESS_TOKEN_FOR_METRICS']

def get_projects():
    proj_list = get_all_projects(ACCOUNT_READ_TOKEN)
    add_read_token_to_projects(proj_list, ACCOUNT_READ_TOKEN, ['read', 'metrics_api_token'])

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
    df['title'] = df['title'].str.slice(0,20)


    # df = df.nlargest(10, 'ip_address_count')
    df = df.nlargest(20, 'occurrence_count')

    print(tabulate(df, headers='keys', tablefmt='grid'))   
    print('')
    print()     

def generate_dashboard():
    print('Generate dashboard')
    proj_list = get_projects()


    for proj in proj_list:
        df = get_last_x_days_metrics(proj, 30)
        if df is not None:
            print_metrics(df)



if __name__ == "__main__":

    logging.basicConfig(level=logging.WARNING,
                format='%(process)d-%(levelname)s-%(message)s',
                handlers=[logging.StreamHandler()]
                )
    generate_dashboard()