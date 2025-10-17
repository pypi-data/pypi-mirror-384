import numpy as np

def trim(series, percentile_keep = 100):
    # Calculate how much to remove
    remove_pct = 100 - percentile_keep
    
    # Find the threshold for most extreme values
    # This gets the absolute distance from median for each point
    median_val = np.median(series)
    abs_deviations = np.abs(series - median_val)
    
    # Find the threshold - keep values with smaller deviations
    threshold = np.percentile(abs_deviations, percentile_keep)
    
    # Return values within the threshold
    return series[abs_deviations <= threshold]
