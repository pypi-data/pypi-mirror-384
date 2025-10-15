def ci(stat, n, sd=None, proportion=False, cl=0.95):
    """Returns confidence interval for a mean or proportion"""
    from scipy import stats
    import math
    
    if not 0 < cl < 1:  # Changed confidence_level to cl
        raise ValueError("Confidence level must be between 0 and 1")
    
    alpha = 1 - cl
    p = 1 - alpha/2
    
    if proportion:
        if not 0 <= stat <= 1:
            raise ValueError("Proportion must be between 0 and 1")
        
        se = math.sqrt((stat * (1 - stat)) / n)
        margin = stats.norm.ppf(p) * se
        
    else:
        if sd is None:  # Changed std to sd
            raise ValueError("Standard deviation required for means")
            
        df = n - 1
        se = sd / math.sqrt(n)
        margin = stats.t.ppf(p, df) * se
    
    return [float(round(stat - margin, 3)), float(round(stat + margin, 3))]
