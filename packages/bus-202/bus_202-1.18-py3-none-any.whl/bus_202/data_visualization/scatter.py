def scatter(df, y, x, fit_line=False, dpi=150, figsize=(6, 4)):
    """
    Create a nice scatter plot with optional fit line and correlation coefficient
    
    Parameters:
    df (pandas DataFrame): Input data
    y (str): Column name for y-axis variable
    x (str): Column name for x-axis variable
    fit_line (bool): If True, adds best fit line
    """
    import seaborn as sns
    import matplotlib.pyplot as plt
    import numpy as np
    
    # Calculate correlation coefficient
    corr = df[x].corr(df[y])
    
    # Set style
    sns.set_style("whitegrid")
    
    # Create figure
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    
    # Create scatter plot
    if fit_line:
        # Use seaborn's regplot for scatter + fit line
        sns.regplot(data=df, 
                   x=x, 
                   y=y,
                   scatter_kws={'alpha':0.5},
                   line_kws={'color': 'red'},
                   ci=None)
    else:
        # Use seaborn's scatterplot
        sns.scatterplot(data=df,
                       x=x,
                       y=y,
                       alpha=0.5)
    
    # Customize plot
    plt.title(f'{y} vs {x}\nCorrelation: {corr:.3f}', pad=15)
    plt.xlabel(x)
    plt.ylabel(y)
    
    # Adjust layout
    plt.tight_layout()
    
    # Show plot without blocking
    plt.show(block=False)
