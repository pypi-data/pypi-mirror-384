import matplotlib.pyplot as plt
import numpy as np
from .trim import trim

def boxplot(series, title=None, trim_outliers=100, dpi=150, figsize=(6, 4)):
    # Create figure and axis
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    
    if not title:
        title = series.name
        
    # Apply trimming if trim < 100
    if trim_outliers < 100:
        series = trim(series, trim_outliers)
        title = f"{title} (outliers removed at {trim_outliers}% level)"
    
    # Convert to numpy array and ensure 1D
    data = np.array(series.dropna()).flatten()
    
    # Create boxplot on the axis
    ax.boxplot(data,
        patch_artist=True,
        boxprops=dict(facecolor='skyblue', color='black'),
        medianprops=dict(color='black'),
        flierprops=dict(marker='o', markerfacecolor='gray'),
        whiskerprops=dict(color='black'),
        capprops=dict(color='black'))
    
    # Add labels and styling
    ax.set_title(title)
    ax.ticklabel_format(style='plain', axis='y')
    ax.grid(True, linestyle='--', alpha=0.7)
    
    plt.show(block=False)
