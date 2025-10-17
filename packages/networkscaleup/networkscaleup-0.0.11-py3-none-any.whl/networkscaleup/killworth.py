import numpy as np
import pandas as pd

def killworth(ard, known_sizes=None, known_ind=None, N=None, model="MLE"):
    # Ensure ARD is a DataFrame
    if isinstance(ard, np.ndarray):
        ard = pd.DataFrame(ard)
    
    # Coerce known_sizes to 1D array, works for Series or DataFrame slice
    if known_sizes is not None:
        if isinstance(known_sizes, pd.DataFrame) or isinstance(known_sizes, pd.Series):
            known_sizes = known_sizes.values.flatten()
        else:
            known_sizes = np.ravel(np.array(known_sizes))
    else:
        known_sizes = np.array([])
    
    if known_ind is None:
        known_ind = list(range(len(known_sizes)))
    print("ARD Variables:")
    print(ard.head())
    print("\nKnown Sizes:", known_sizes)
    print("Known Indices:", known_ind)
    print("N:", N)
    print("Column names in ARD:", ard.columns)

    # Extract dimensions
    N_i, N_k = ard.shape
    N_k = N_k

    # Number of respondents and subpopulations
   
    if known_sizes is None:
        known_sizes = []
    if known_ind is None:
        known_ind = list(range(len(known_sizes)))
    #print("known sizes is ", known_sizes, "known ind is", known_ind)
    
    n_known = len(known_sizes)

    n_unknown = N_k - n_known
    unknown_ind = [i for i in range(N_k) if i not in known_ind]
    print("\nUnknown_ind:")
    print(unknown_ind)
    
    if model not in {"MLE", "PIMLE"}:
        raise ValueError("model must be one of 'MLE' or 'PIMLE'")
    
    if len(known_sizes) != len(known_ind):
        raise ValueError("known_sizes and known_ind must be the same length")

    
    # Estimate degrees
    d_est = N * ard.iloc[:, known_ind].sum(axis=1) / sum(known_sizes)
    print("\nEstimated Degrees:")
    print(d_est)
    print(f"d_est length: {len(d_est)}")
    
    if n_unknown == 1:
        # If only 1 unknown subpopulation
        if model == "MLE":
            N_est = N * ard.iloc[:, unknown_ind].sum().sum() / d_est.sum()
        else:
            pos_ind = d_est > 0
            if not pos_ind.all():
                print("Warning: Estimated a 0 degree for at least one respondent. Ignoring response for PIMLE")
            colname = ard.columns[unknown_ind[0]] 
            N_est = N * (ard.loc[pos_ind, colname] / d_est[pos_ind]).mean()
            #N_est = N * (ard.loc[pos_ind, unknown_ind].sum(axis=1) / d_est[pos_ind]).mean()
    else:
        # If multiple unknown subpopulations
        N_est = np.full(n_unknown, np.nan)
        
        if model == "MLE":
            for k, idx in enumerate(unknown_ind):
                N_est[k] = N * ard.iloc[:, idx].sum() / d_est.sum()
        else:
            pos_ind = d_est > 0
            if not pos_ind.all():
                print("Warning: Estimated a 0 degree for at least one respondent. Ignoring response for PIMLE")
            for k, idx in enumerate(unknown_ind):
                colname = ard.columns[idx]
                N_est[k] = N * (ard.loc[pos_ind, colname] / d_est[pos_ind]).mean()
                #N_est[k] = N * (ard.loc[pos_ind, idx] / d_est[pos_ind]).mean()
    print("\nEstimated Sizes:")
    print(N_est)
    return {"degrees": d_est, "sizes": N_est}
