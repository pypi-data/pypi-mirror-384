#!/usr/intel/bin/python3


import requests
import json
import hashlib
import hmac
import base64
import pandas as pd
import sys
from datetime import datetime,UTC

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

#Function to fetch the SPeTC ids based upon the Workweek and releasebranch
def spetc_ids_req(workweek,releasebranch):
    """
    Fetches SPeTC IDs for the given workweek and release branch using the SPeTC API.

    Args:
        workweek (str): The workweek identifier (e.g., 'WW35').
        releasebranch (str): The release branch name (e.g., 'main').

    Returns:
        spetc_ids or None: A comma-separated string of SPeTC IDs if found, otherwise None.
    """
    # Import the function to generate SPeTC headers
    
    # API request details
    method = 'GET'
    url = "https://acds-central-api-prod.altera.com/test-infra-api/v3/testRuns/workWeek?*"
    publicAccessKey = "ddae53ec-95a9-410c-81ba-e1f127464e06"
    secretAccessKey = "3yNSztcvkVKAGkm4LQyz"
    contentType = ''
    contentMd5 = ''
    # Generate API request headers using the provided keys and method
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
    # Make the GET request to the SPeTC API
    response = requests.get(url, headers=headers,verify=True)
    #Checks whether response is successful or not.
    if (response.ok):
        # Parse the JSON response content
        jData = json.loads(response.content)
        # Convert JSON data to a pandas DataFrame
        response_df=  pd.DataFrame(jData)
        if releasebranch not in response_df['releaseVersion'].values:
            print(f"Error: Release Branch {releasebranch} not available.")
            sys.exit(0)
        # Filter the DataFrame based on workweek and releasebranch
        print(f"Fetching spetc_ids for {workweek} for releasebranch {releasebranch}")
        result=response_df.loc[(response_df['workWeek']==workweek) & (response_df['releaseVersion']==releasebranch) ,'testRunIds']
        # If no matching records found, return None
        if result.empty:
        	return None
        # Join the testRunIds into a comma-separated string
        spetc_ids=','.join(str(x) for x in result.iloc[0]) 
    else:
        print ("Response not found for the API")
        return None
    # Return the comma-separated SPeTC IDs (or None)
    return spetc_ids


