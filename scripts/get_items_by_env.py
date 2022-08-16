
import json
import logging
import math
import requests
import os

import datetime, time

import metrics_base as mb
from metrics_base import Project

#
# This script requires 1 environment variable
# Go to your Rollbar account settings and creatE a read scope access token
# https://rollbar.com/settings/accounts/YOUR_ACCOUNT_SLUG/access_tokens/
#
# export ACCOUNT_READ_ACCESS_TOKEN_FOR_METRICS=MY_READ_SCOPE_ACCESS_TOKEN
#

def process_all():

 
    account_read_token = os.environ['ACCOUNT_READ_ACCESS_TOKEN_FOR_METRICS'] 
    allowed_proj_token_names = ['metrics_api_token', 'read']

    projects = mb.get_project_objects(account_read_token, allowed_proj_token_names)
    starttime_unix, finaltime_unix = get_start_and_final_time()

    output_csv_file = 'all_items_by_proj_and_env.csv'

    if os.path.exists(output_csv_file):
        os.rename(output_csv_file, time.mktime(datetime.datetime.now().timetuple()) + '_' + output_csv_file)


    # Get data in batches of batch_size seconds
    batch_size = 60 * 60 * 24

    for proj in projects:

        next_time = starttime_unix + batch_size
        while next_time <= finaltime_unix:
            result = get_items_by_env(proj, starttime_unix, next_time)
            add_results_to_csv_file(proj, result, output_csv_file, starttime_unix, next_time)

            if next_time >= finaltime_unix:
                break


            starttime_unix = next_time
            next_time = next_time + batch_size

            if next_time > finaltime_unix:
                next_time = finaltime_unix

                
        
    


def get_start_and_final_time():
    final_time = datetime.datetime.today()
    start_time = final_time - datetime.timedelta(days=30)

    finaltime_unix = math.floor(time.mktime(final_time.timetuple()))   
    starttime_unix = math.floor(time.mktime(start_time.timetuple()))

    if starttime_unix >= finaltime_unix:
        raise ValueError('Start time needs to be less than the final time')

    return starttime_unix, finaltime_unix



def get_items_by_env(proj, starttime_unix, endtime_unix):

    query_data = {
            # epoch time in seconds
            'start_time': starttime_unix,
            'end_time':  endtime_unix,
            'group_by': ['environment', 'item_level'],
             'filters': [
              {
                'field': 'item_level',
                'values': ['error', 'critical', 'warning', 'info'],
                'operator': 'eq'
              }
              ]
            }
    result = mb.make_occ_metrics_api_call(proj, query_data)

    return result


def add_results_to_csv_file(proj, result, output_csv_file, starttime_unix, endtime_unix):

    try:
        mb.process_result(proj, result, output_csv_file,
            datetime.datetime.fromtimestamp(starttime_unix).strftime('%c'),
            datetime.datetime.fromtimestamp(endtime_unix).strftime('%c'))
    except Exception as ex:
        msg = 'Exception caclulating metrics for {}'.format(proj.name)
        logging.exception(msg, exc_info=ex)
    
    logging.info('Finished writing CSV file %s for %s: %s', output_csv_file, proj.name, starttime_unix)


if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO,
                    format='%(process)d-%(levelname)s-%(message)s',
                    handlers=[logging.StreamHandler()]
                    )

    process_all()

    


