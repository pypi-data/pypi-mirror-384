#!/usr/intel/bin/python3

import argparse
import os
import sys
import logging
from datetime import datetime


# Function to get the deepest valid base path from a target directory
def get_base_path(target_dir, base_synced_regtests_path):
    """
    Determines the deepest valid base path from a target directory.

    Args:
        target_dir (str): The target directory path to evaluate.
        base_synced_regtests_path (str): The base path where regtest files are synced.

    Returns:
        str: The deepest valid base path found within the target directory.
    """
    # Split the target directory into components
    directories = target_dir.strip('/').split('/')
    bpath = ''
    deepest_bpath = ''
    # Iterate through the directory levels to find the deepest valid path
    for i in range(len(directories)):
        bpath = bpath + directories[i] + '/'
        newpath = os.path.join(base_synced_regtests_path, bpath)
        if not os.path.isdir(newpath):
            # Stop if the directory does not exist
            break
        else:
            # Update the deepest valid base path
            deepest_bpath = bpath
    return deepest_bpath

# Function to get the base paths for the filtered testcase paths
def get_base_paths_from_target_list(filtered_paths, releasebranch):
    

    base_path_arr = []
    # Construct the base path where regtest files are synced for the release branch
    base_synced_regtests_path = f"/p/psg/swip/regtestfiles/{releasebranch}/current"
    
    base_paths_checklist = filtered_paths
    # Iterate through each path in the filtered list
    for path in base_paths_checklist:
        path = path.strip()
        # Check whether the testcase path starts with 'regtest'
        if not path.startswith('regtest'):
            logging.info(f"Warning: Ignoring invalid line {path}")
            continue
        # Find the deepest valid base path for the testcase path
        base_path = get_base_path(path, base_synced_regtests_path)
        if not base_path:
            pass  # Skip if no valid base path found
        else:
            base_path_arr.append(base_path)
    logging.info(f"Number of regtestpaths found {len(base_path_arr)}")
    # Remove duplicate base paths while preserving order
    uniq_arr = list(dict.fromkeys(base_path_arr))
    logging.info(f"Number of unique base paths found {len(uniq_arr)}")
    return uniq_arr