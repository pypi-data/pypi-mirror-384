import re
import random
import argparse
import logging
from collections import defaultdict
import pandas as pd

def filter_test_paths(test_paths, count):
    """
    Sample and filter test case paths according to IP, device, variant, test type, and user filters.

    Args:
        test_paths (list of str): All available test paths.
        count (int): Number of test cases to select.
        

    Returns:
        list of str: Filtered and sampled test case paths.
    """
    # Nested defaultdict for grouping: ip -> device -> variant -> list of (path, test_type)
    data = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    # Regex pattern to extract IP, device, variant, and test type
    test_types = [
        'rtl_sim_questafe_vhdl', 'rtl_sim_questafe_vlg', 'rtl_sim_msim_vhdl', 'rtl_sim_msim_vlg',
        'rtl_sim_vcs_vlg', 'rtl_sim_vcs_vhdl', 'rtl_sim_vcsmx_vlg', 'rtl_sim_vcsmx_vhdl',
        'rtl_sim_xcelium_vlg', 'rtl_sim_xcelium_vhdl', 'rtl_sim_riviera_vlg', 'rtl_sim_riviera_vhdl'
    ]

    # Compile regex pattern
    pattern = re.compile(
        r'regtest/ip/([^/]+)(?:/([^/]+))?/.*?/device__([^/]+)(?:/csv_parser)?/qsys__([^/]+).*?/'
        r'(' + '|'.join(test_types) + ')'
    )
    
    # Group each path by IP, device, variant, and test type
    for path in test_paths:
        match = pattern.search(path)
        
        if match:
            ip_name = match.group(1)
            inner_ip = match.group(2) or ip_name
            device = match.group(3)
            variant = match.group(4)
            test_type = match.group(5)
            data[ip_name][device][variant].append((path, test_type))
    

    logging.info(f"Total IPs found: {len(data)}")
    filtered_paths = []
    
    for ip, devices in data.items():
        #Selecting random devices for an ip.
        selected_devices = random.sample(list(devices.keys()), min(1, len(devices)))
        logging.info(f"Selected devices for IP {ip}: {selected_devices}")
        #Selecting random variants for an device.
        for device in selected_devices:
            variants = devices[device]
            selected_variants = random.sample(list(variants.keys()), min(1, len(variants)))
            logging.info(f"Selected variants for device {device}: {selected_variants}")
            #getting the test_type for the variant selected.
            for variant in selected_variants:
                tests_by_type = defaultdict(list)
                for path, test_type in variants[variant]:
                    tests_by_type[test_type].append(path)
                # Randomly select one test path per test type, if available
                for tt in test_types:
                    if tests_by_type[tt]:
                        filtered_paths.append(random.choice(tests_by_type[tt]))

    # Fill remaining slots to reach count
    remaining_paths = set(test_paths) - set(filtered_paths)
    if len(filtered_paths) < count and remaining_paths:
        additional_paths = random.sample(list(remaining_paths), min(count - len(filtered_paths), len(remaining_paths)))
        filtered_paths.extend(additional_paths)
    if len(filtered_paths) > count:
        filtered_paths = random.sample(filtered_paths, count)
    logging.info(f"Total filtered paths: {len(filtered_paths)}")
    
    return filtered_paths
