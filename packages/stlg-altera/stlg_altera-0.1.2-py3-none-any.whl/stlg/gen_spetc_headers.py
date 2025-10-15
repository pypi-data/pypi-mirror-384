#!/usr/intel/bin/python3
from datetime import datetime
import hashlib
import hmac
import base64

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
