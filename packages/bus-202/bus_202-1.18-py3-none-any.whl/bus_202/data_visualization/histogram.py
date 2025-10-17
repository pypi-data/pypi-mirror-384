import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from .trim import trim

def histogram(series, title=None, bins=30, trim_outliers=100, details=False, dpi=150, figsize=(6, 4)):
    # Create figure and axis
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    
    # Get base title
    if not title:
        title = series.name
    
    # Store original data for statistics BEFORE any trimming
    original_data = np.array(series.dropna()).flatten()
    
    # Apply trimming if trim < 100
    if trim_outliers < 100:
        series = trim(series, trim_outliers)
        title = f"{title} (outliers removed at {trim_outliers}% level)"
    
    # Convert to numpy array and handle NaN
    data = np.array(series.dropna()).flatten()
    
    # Create histogram
    ax.hist(data, 
            bins=bins,
            edgecolor='black',
            color='skyblue',
            alpha=0.7)
    
    # Add labels and styling
    ax.set_title(title)
    ax.set_ylabel('Count')
    ax.ticklabel_format(style='plain', axis='x')
    ax.grid(True, linestyle='--', alpha=0.7)
    
    if details:
        # Add mean and median lines
        mean = np.mean(original_data)
        median = np.median(original_data)
        ax.axvline(mean, color='red', linestyle='--', label=f'Mean: {mean:.2f}')
        ax.axvline(median, color='green', linestyle='--', label=f'Median: {median:.2f}')
        
        # Calculate standard deviations
        std = np.std(original_data)
        
        # Calculate percentages within SDs
        within_1sd = np.sum((original_data >= mean - std) & (original_data <= mean + std)) / len(original_data) * 100
        within_2sd = np.sum((original_data >= mean - 2*std) & (original_data <= mean + 2*std)) / len(original_data) * 100
        within_3sd = np.sum((original_data >= mean - 3*std) & (original_data <= mean + 3*std)) / len(original_data) * 100
        
        skew_val = pd.Series(original_data).skew()
        
        # Add text box with statistics
        stats_text = (
            f'Skewness: {skew_val:.3f}\n'
            f'Within 1 SD: {within_1sd:.1f}%\n'
            f'Within 2 SD: {within_2sd:.1f}%\n'
            f'Within 3 SD: {within_3sd:.1f}%'
        )
        plt.text(0.95, 0.95, stats_text,
                transform=ax.transAxes,
                verticalalignment='top',
                horizontalalignment='right',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # Add legend
        plt.legend()
    
    plt.show(block=False)
