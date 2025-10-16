import re
import pandas as pd
import numpy as np


def decode_b_value(val):
    """
    Attempt to decode a DICOM b-value from various formats (DataElement, string, bytes, list, etc.)
    
    Parameters:
        val: The value to decode (can be a pydicom DataElement, str, bytes, list, etc.)
    
    Returns:
        float: Decoded b-value or NaN if decoding fails.
    """
    try:
        # Step 1: Get .value if it's a DataElement
        if hasattr(val, 'value'):
            val = val.value

        # Step 2: If it's a numeric type, return as float
        if isinstance(val, (int, float)):
            return float(val)

        # Step 3: If it's a string, strip and convert
        if isinstance(val, str):
            return float(val.strip())

        # Step 4: If it's bytes, decode and convert
        if isinstance(val, bytes):
            return float(val.decode('ascii').strip())

        # Step 5: If it's a list-like structure (e.g., list of ints), try to decode as characters
        if isinstance(val, (list, tuple, np.ndarray)):
            chars = ''.join(chr(int(v)) for v in val if 32 <= int(v) <= 126)
            return float(chars.strip())

    except (ValueError, TypeError) as e:
        print(f"Warning: Failed to decode b-value: {e} | Original value: {val}")

    # Step 6: If all decoding attempts fail, return NaN
    return float('nan')


def extract_bval(info):
    """
    Extract the b-value from a DICOM dataset using known tag locations.
    
    Parameters:
        info (Dataset): The DICOM dataset from which to extract the b-value.
    
    Returns:
        tuple: (bval, bval_source) where bval is a float and bval_source is a tag identifier string.
    """
    bval = float('nan')
    bval_source = ''

    # Step 1: Try to extract value using a series of known tag paths
    def try_tag(tag_path, label):
        nonlocal bval, bval_source
        val = info.get(tag_path, None)
        if val is not None:
            bval_candidate = decode_b_value(val)
            if not pd.isna(bval_candidate):
                bval = bval_candidate
                bval_source = label

    try_tag((0x0018, 0x9087), '(0018,9087)')
    if pd.isna(bval):
        try_tag((0x0019, 0x100c), '(0019,100c)')
    if pd.isna(bval):
        try_tag((0x0043, 0x1039), '(0043,1039)')
    if pd.isna(bval):
        try_tag((0x2001, 0x1003), '(2001,1003)')

    # Step 2: Fallback to parsing b-value from 'SequenceName' if available
    if pd.isna(bval) and 'SequenceName' in info:
        matches = re.findall(r'(\d+)', str(info.SequenceName))
        if matches:
            bval = float(matches[0])
            bval_source = '(0018,0024)'

    return bval, bval_source
