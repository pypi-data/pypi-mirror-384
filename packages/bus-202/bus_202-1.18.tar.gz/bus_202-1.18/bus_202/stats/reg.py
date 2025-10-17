def reg(df, y, x, fe=None, logistic=False):
    import statsmodels.api as sm
    import pandas as pd
    import numpy as np
    
    # Convert ivs to list if it's a single string
    if isinstance(x, str):
        x = [x]
    
    # Create copy of dataframe to avoid modifying original
    df_reg = df.copy()
    
    # Convert main variables to numeric
    numeric_cols = [y] + x
    for col in numeric_cols:
        df_reg[col] = pd.to_numeric(df_reg[col], errors='coerce')
    
    # Handle fixed effects if specified
    if fe is not None:
        # Convert fe to list if it's a single string
        if isinstance(fe, str):
            fe = [fe]
        
        # Create dummies for each fixed effect variable
        for fe_var in fe:
            # For logistic regression, only keep categories with sufficient variation
            if logistic:
                # Create cross-tab of fixed effect and dependent variable
                ct = pd.crosstab(df_reg[fe_var], df_reg[y])
                # Keep only categories with both 0s and 1s
                valid_categories = ct[(ct > 0).all(axis=1)].index
                df_reg = df_reg[df_reg[fe_var].isin(valid_categories)]
            
            # Create dummies, drop first category to avoid multicollinearity
            dummies = pd.get_dummies(df_reg[fe_var], prefix=fe_var, drop_first=True, dtype=float)
            
            # Add dummies to dataframe
            df_reg = pd.concat([df_reg, dummies], axis=1)
            
            # Add dummy column names to x list
            x.extend(dummies.columns)
    
    # Drop rows with NaN values
    df_reg = df_reg.dropna(subset=[y] + x)
    
    # Create X and y, adding constant
    X = sm.add_constant(df_reg[x].astype(float))
    y_data = df_reg[y].astype(float)
    
    # Run appropriate regression
    if logistic:
        model = sm.Logit(y_data, X)
        try:
            # Use more robust optimization method
            results = model.fit(method='bfgs', maxiter=100)
            print(results.summary())
            return results
        except Exception as e:
            print(f"Error fitting logistic model: {e}")
            print("\nTrying with reduced fixed effects...")
            
            # Try again with fewer fixed effects
            if fe is not None:
                # Keep only fixed effects with sufficient observations
                min_obs = 30  # minimum observations per category
                for fe_var in fe:
                    value_counts = df_reg[fe_var].value_counts()
                    valid_categories = value_counts[value_counts >= min_obs].index
                    df_reg = df_reg[df_reg[fe_var].isin(valid_categories)]
                
                # Rerun the regression with reduced sample
                try:
                    X = sm.add_constant(df_reg[x].astype(float))
                    y_data = df_reg[y].astype(float)
                    model = sm.Logit(y_data, X)
                    results = model.fit(method='bfgs', maxiter=100)
                    print("\nResults with reduced fixed effects:")
                    print(results.summary())
                    return results
                except Exception as e:
                    print(f"Error fitting reduced model: {e}")
    else:
        model = sm.OLS(y_data, X)
        try:
            results = model.fit()
            print(results.summary())
            return results
        except Exception as e:
            print(f"Error fitting model: {e}")
