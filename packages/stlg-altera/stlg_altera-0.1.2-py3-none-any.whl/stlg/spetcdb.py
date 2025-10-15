#!/usr/intel/bin/python3

import requests
import json
import hashlib
import hmac
import base64
import pandas as pd
from datetime import datetime
import argparse
import sys
import os
import time
import re
import fnmatch
from collections import defaultdict
import random
import logging

def generateSpetcHeaders(obj):
    """
    Generates custom headers required for making authenticated requests to the SPETC API.

    Parameters
    ----------
    obj : dict
        A dictionary containing the following keys:
            method : str
                HTTP method (e.g., 'GET', 'POST', 'DELETE').
            fullUrl : str
                Full URL of the API endpoint including query parameters.
            clientId : str
                Client ID used for authentication.
            secretKey : str
                Secret key used to generate HMAC signature.
            data : str or None
                Request payload (if applicable).
            cache : bool
                Flag indicating whether caching should be disabled.

    Returns
    -------
    dict
        Dictionary of headers including:
            Authorization : str
                HMAC-based signature for authentication.
            X-Date : str
                Current UTC date in RFC 1123 format.
            Content-Type : str
                Set to 'application/json' if applicable.
            Cache-Control, Pragma, Expires : str
                Set if caching is disabled.
    """
    # Get the current UTC date in RFC 1123 format
    date = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')

    # Extract base URL (without query parameters)
    url = obj['fullUrl'].split('?')[0]

    # Initialize headers
    content_type = ''
    content_md5 = ''

    # Set Content-Type and Content-MD5 for applicable methods
    if obj['method'] != 'GET' and (obj['method'] != 'DELETE' or obj['data']):
        content_type = 'application/json'
        content_md5 = hashlib.md5((obj['data'] or '').encode()).hexdigest()

    # Construct the string to sign
    string_to_sign = "{}\n{}\n{}\n{}\n{}\n{}".format(
        obj['method'],
        url,
        content_type,
        obj['clientId'],
        date,
        content_md5
    )

    # Generate HMAC SHA256 signature
    hash = hmac.new(obj['secretKey'].encode(), string_to_sign.encode(), hashlib.sha256)
    signature = base64.b64encode(hash.digest()).decode()

    # Build headers
    headers = {
        'Authorization': f"{obj['clientId']}:{signature}",
        'X-Date': date,
        'Content-Type': content_type
    }

    # Add cache-control headers if caching is disabled
    if obj['cache'] is False:
        headers.update({
            'Cache-Control': 'no-cache, no-store, must-revalidate, post-check=0, pre-check=0',
            'Pragma': 'no-cache',
            'Expires': '0'
        })

    return headers

def flatten_lists_for_sql(data):
    """
    Converts any list values in a dictionary to comma-separated strings.
    Useful for preparing data for CSV output.
    """
    flattened = {}
    for key, value in data.items():
        if isinstance(value, list):
            
            flattened[key] = ",".join(map(str, value))
        else:
            flattened[key] = value
    return flattened

#Extracting the device and topology from the param
def extract_params(param_str):
    """
    Extracts topology and device name from the parameter string using regex.

    Args:
        param_str (str): String containing parameters.

    Returns:
        dict: Dictionary with 'topology' and 'dev_name' keys.
    """
    topology_match = re.search(r'--topology="([^"]+)"', param_str)
    dev_name_match = re.search(r'--dev_name="([^"]+)"', param_str)
    return {
        'topology': topology_match.group(1) if topology_match else None,
        'dev_name': dev_name_match.group(1) if dev_name_match else None
        }
        
# Mapping of simulator names to their resource tag patterns
simulator_patterns = {
"questasim": "*modelsim_se-lic*",
"vcs": "*vcs-vcsmx-lic*",
"riviera": "*riviera-lic*",
"xcelium": "*cadence_xcelium-lic*",
"questafe": "*questa_fe_tag*"
}

def load_local_data(spetc_id, full_path):
    """
    Attempts to load local CSV data for a given SPeTC ID.

    Args:
        spetc_id (str): SPeTC ID.
        full_path (str): Path to the directory containing CSV files.

    Returns:
        pd.DataFrame or None: DataFrame if file exists, else None.
    """
    path = os.path.join(full_path, f"{spetc_id}_complete_data.csv")
    try:
        #Getting data from csv and storing it in DataFrame
        final_df = pd.read_csv(path,low_memory=False)
        logging.info(f"Local data loaded successfully for spetc_id: {spetc_id}")
        return final_df
    except FileNotFoundError:
        logging.info(f"Local data not found for SPeTC ID {spetc_id}.")
        return None

def fetch_data_from_api(spetc_id, full_path, publicAccessKey, secretAccessKey, method, contentType, contentMd5):
    """
    Fetches test results from the SPeTC API, paginates through all results,
    and stores the complete data as a CSV.

    Args:
        spetc_id (str): SPeTC ID.
        full_path (str): Directory to save logs and CSVs.
        publicAccessKey, secretAccessKey: API credentials.
        method, contentType, contentMd5: HTTP request details.

    Returns:
        pd.DataFrame: DataFrame with relevant test result columns.
    """
    
    logging.info("Data loading started for SPeTC Id: "+spetc_id+" at "+datetime.now().strftime("%H:%M:%S"))
    #Fetching overall data and saving it.
    url = "https://temp.acds-central-api.altera.com/test-infra-api/v3/testResultSummary/noCache?testRunId="+spetc_id+"&collapseSubtestsToParent=false&includeOrgData=false&testCasePath="
    headers = generateSpetcHeaders(
    { 
        'clientId': publicAccessKey, 
        'secretKey': secretAccessKey, 
        'method': method, 
        'fullUrl': url,
        'contentType': contentType, 
        'contentMd5': contentMd5, 
        'cache': True 
    }
    )
    
    #Creating a file to store overall data
    filename_log = os.path.join(full_path, spetc_id + '_overall_results.txt')
    file_log=open(filename_log,'w')
    #Fetching the data and storing it.
    response = requests.get(url, headers=headers)
    if (response.ok):  
        #Loading data in json format.
        response_data = json.loads(response.content) 
        #Saving the data in DataFrame.
        response_df = pd.DataFrame([response_data])
        #saving only some specific columns from dataframe
        required_df=response_df[['countTotalTest', 'countPassedTest', 'countFailedTest', 'countPendingTest', 'countRunningTest', 'totalCpuTime']]
        #Getting the total test count value.
        totalcount=required_df['countTotalTest'].iloc[0]
        passedcount=required_df['countPassedTest'].iloc[0]
        if (totalcount==0):
            #if testcount is zero then the spetc_id is invalid.
            logging.info ("Error: Enter Valid SPeTC Id ")            
            if os.path.exists(filename_log):
                os.remove(filename_log)
            sys.exit(0)
        else:
            file_log.write(required_df.to_string())
            file_log.write("\n")
    else:
        logging.info ("Error: SPeTC server is busy try once again!!")
    
    #Fetching the TestResultSummary for a spetc_id using  API.
    all_results = []  # Storing all results from all pages.
    page = 1          # Start from first page.
    pageSize = 25000   # maximum allowed page size.
    MAX_RETRIES = 10  # Number of times to retry
    RETRY_DELAY = 10  # Seconds to wait before retrying
    
    while True:
        url = f"https://temp.acds-central-api.altera.com/test-infra-api/v3/testResults?listDataType=dataOnly&testRunId={spetc_id}&collapseSubtestsToParent=false&pagingRequired=true&page={page}&pageSize={pageSize}"
    
        headers = generateSpetcHeaders({
            'clientId': publicAccessKey,
            'secretKey': secretAccessKey,
            'method': method,
            'fullUrl': url,
            'contentType': contentType,
            'contentMd5': contentMd5,
            'cache': True
        })
        
        success = False
        # Retry logic for network reliability
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = requests.get(url, headers=headers)
                if response.ok:
                    success = True
                    break  # Success, exit retry loop
                else:
                    logging.info(f"Failed to fetch page {page} (Attempt {attempt}/{MAX_RETRIES}): {response.status_code}")
                    time.sleep(RETRY_DELAY)  # Wait and try again
            except Exception as e:
                logging.error(f"Exception during request on page {page}: {e}")
                break
                
        if not success:
            logging.warning(f"Stopping fetch due to failure on page {page}. Returning collected results.")
            break  # Exit loop and return collected data
            
        try:
            #Loading data in json format.
            jData = response.json()
            results = jData.get("testResults", [])
            logging.info(f"Fetched {len(results)} results from page {page} at {datetime.now().strftime('%H:%M:%S')}")
            
        except Exception as e:
            logger.error(f"Failed to parse JSON on page {page}: {e}")
            break  # Exit loop and return collected data
        
        if not results:
            break  # No more results to fetch.
        #Converting any list to comma-separated string and collecting all results.
        flattened_results = [flatten_lists_for_sql(item) for item in results]
        all_results.extend(flattened_results)
        
        #If the number of results is less than pageSize, it is the last page.
        if len(results) < pageSize:
            break
        page += 1
        #Avoid hitting rate limits.
        time.sleep(5)
        
    #Storing the flattened results in a DataFrame. 
    if all_results:
        results_df = pd.DataFrame(all_results)

        # Mapping the status.
        status_mapping = {0: 'Pending', 1: 'Running', 2: 'Passed', 3: 'Failed'}
        results_df['status'] = results_df['status'].map(status_mapping)

        # Extracting parameters from param.
        df_extracted = results_df['param'].apply(extract_params).apply(pd.Series)
        results_df = pd.concat([results_df, df_extracted], axis=1)

        # Saving the complete results to csv.
        path = os.path.join(full_path, f"{spetc_id}_complete_data.csv")
        results_df.to_csv(path, index=False)
        logging.info(f"Total results fetched: {len(results_df)}")

        # Extract final columns
        final_df = results_df[['id', 'ownerName', 'testCasePath', 'resourceTagValue', 'resultLocation',
                               'status', 'variation', 'testRunTitle', 'startTime', 'finishTime',
                               'official', 'param', 'farmLink', 'topology', 'dev_name','familyTagValue']].copy()
        return final_df
    else:
        logging.info("Enter Valid SPeTC Id")
        sys.exit(0)
    
def overall_result(user_input,path,filters,loadlocaldata,count,releasebranch,workweek):
    """
    Main entry point to fetch, filter, and return test paths for the provided SPeTC IDs.

    Args:
        user_input (str): Comma-separated SPeTC IDs.
        path (str): Output directory path.
        filters (list): Filtering criteria for test selection.
        loadlocaldata (bool): Whether to use locally cached data.
        count (int): Number of test cases to retrieve.
        releasebranch (str): Release branch identifier.

    Returns:
        list: List of filtered test case paths.
    """
    
    #Seperating the spetc_ids by ','.
    spetc_ids = user_input.split(',')  
    method = 'GET'
    #Credentials for SPeTC API's
    publicAccessKey = "ddae53ec-95a9-410c-81ba-e1f127464e06"
    secretAccessKey = "3yNSztcvkVKAGkm4LQyz"
    contentType = ''
    contentMd5 = ''
    #Creating a Directory 'Data' if it doesn't exists for saving results. 
    dir_name="Data"
    full_path=os.path.join(path,dir_name)
    total_fetched_results=[]
    all_selected_dfs = []
    if not os.path.exists(full_path):
        os.makedirs(full_path)
    if workweek and releasebranch:
        sub_dir_name = f"{workweek}_{releasebranch}"
        full_path = os.path.join(full_path, sub_dir_name)
        os.makedirs(full_path, exist_ok=True)
    for spetc_id in spetc_ids:
        final_df = None
        # Attempt to load data from local cache if enabled
        if loadlocaldata:
            final_df = load_local_data(spetc_id, full_path)
        
        # Otherwise, fetch data from the API
        if final_df is None:
            final_df = fetch_data_from_api(spetc_id, full_path, publicAccessKey, secretAccessKey, method, contentType, contentMd5)
        
        total_fetched_results.append(final_df)
        
        # Using final_df for further processing of data.
        #Applying the status filter taking only passed cases.
        allowed_statuses = ['Passed']
        final_df = final_df[final_df['status'].isin(allowed_statuses)]        
        # Apply provided filters if any
        filter_dict = {}
        if filters:
            for item in filters:
                
                if '!=' in item:
                    key, values = item.split('!=', 1)
                    key = key.lower()
                    value_list = [v.strip("'\"").lower() for v in values.split(',')]
                    filter_dict[key] = {'exclude': value_list}
                elif '=' in item:
                    key, values = item.split('=', 1)
                    key = key.lower()
                    value_list = [v.strip("'\"").lower() for v in values.split(',')]
                    filter_dict[key] = value_list
            
                filtered_parts = []
                #Applying the simulators filter
                if 'simulators' in filter_dict:
                    
                    sim_patterns = [simulator_patterns[s] for s in filter_dict['simulators'] if s in simulator_patterns]
                    
                    final_df = final_df[final_df['resourceTagValue'].apply(lambda x: isinstance(x, str) and any(fnmatch.fnmatch(x, pattern) for pattern in sim_patterns))]
                    filtered_parts.append(final_df)
                    
                #Applying the topology filter.
                if 'topology' in filter_dict:
                    allowed_topologies = filter_dict['topology']
                    final_df = final_df[final_df['topology'].isin(allowed_topologies)]
                    filtered_parts.append(final_df)
                #Applying the device_name filter.
                if 'dev_name' in filter_dict:
                    allowed_dev_names = filter_dict['dev_name']
                    final_df = final_df[final_df['dev_name'].isin(allowed_dev_names)]
                    filtered_parts.append(final_df)
                def normalize_family(f):
                    return f.replace(" ", "").lower()

                if 'family' in filter_dict and filter_dict['family']:
                    family_filter = filter_dict['family']

                    # 1. Normalize familyTagValue column ONCE
                    if 'familyTagValue' in final_df.columns:
                        final_df = final_df.copy()
                        final_df.loc[:, 'familyTagValue'] = final_df['familyTagValue'].apply(
                            lambda x: ','.join([normalize_family(f) for f in str(x).split(',')])
                        )

                    # 2. Apply filters
                    if isinstance(family_filter, list):
                        filter_values = set(normalize_family(f) for f in family_filter)
                        logging.info(f"Families to include: {filter_values}")

                        def has_family(row):
                            families = set(f.strip() for f in str(row).split(','))
                            return not filter_values.isdisjoint(families)

                        if 'familyTagValue' in final_df.columns:
                            final_df = final_df[final_df['familyTagValue'].apply(has_family)]

                    elif isinstance(family_filter, dict) and 'exclude' in family_filter:
                        exclude_values = set(normalize_family(f) for f in family_filter['exclude'])
                        logging.info(f"Families to exclude: {exclude_values}")

                        def has_no_excluded_family(row):
                            families = set(f.strip() for f in str(row).split(','))
                            return exclude_values.isdisjoint(families)

                        if 'familyTagValue' in final_df.columns:
                            final_df = final_df[final_df['familyTagValue'].apply(has_no_excluded_family)]

                    # 3. Logging and storing results
                    if 'familyTagValue' in final_df.columns:
                        logging.info(f"Filtered Families: {final_df['familyTagValue'].unique()}")

                    filtered_parts.append(final_df)

                # Storing all the filtered data in filtered_df.
                filtered_df = final_df.copy()    
        else:
            filtered_df =final_df.copy()
        # Standardize column names to lowercase
        filtered_df.columns = [col.lower() for col in filtered_df.columns]
        column_to_select="testcasepath"
        # Check if the column exists in the DataFrame
        if column_to_select not in filtered_df.columns:
        	logging.info(f"Warning: No data found for the applied filters.")
        	
        else :
            # Select only the specified column
            selected_df = filtered_df[[column_to_select]].copy()
            all_selected_dfs.append(selected_df)
        logging.info("Data loading done for SPeTC Id: "+spetc_id+" at "+datetime.now().strftime("%H:%M:%S"))
        time.sleep(5)
    # Concatenate all results and return as a list
    all_results_dfs=pd.concat(all_selected_dfs,ignore_index=True)
    total_fetched_results_df=pd.concat(total_fetched_results,ignore_index=True)
    logging.info(f"Total test results fetched : {len(total_fetched_results_df)}") 
    test_paths = all_results_dfs['testcasepath'].dropna().astype(str).tolist()
    test_paths = list(set(test_paths))
    if filters:
        
        if 'ipnames' in filter_dict:
            ipnames_filter = [ip.lower() for ip in filter_dict['ipnames']]
            # Compile pattern to match regtest/ip/<ip>/(<subip>)/...
            pattern = re.compile(r'regtest/(?:[^/]+)/([^/]+)(?:/([^/]+))?/')
            filtered_test_paths = []
            for path in test_paths:
                match = pattern.search(path)
                if match:
                    ip = match.group(1).lower()
                    subip = match.group(2).lower() if match.group(2) else None
                    if ip in ipnames_filter or (subip and subip in ipnames_filter):
                        filtered_test_paths.append(path)
            # Now filtered_test_paths contains only paths for the specified ip or subip
            test_paths = filtered_test_paths
            
    logging.info(f"Reading input DataFrame column '{column_to_select}' with {len(test_paths)} rows after filtering.")
    return test_paths
    logging.info("End time: "+datetime.now().strftime("%H:%M:%S"))
    
