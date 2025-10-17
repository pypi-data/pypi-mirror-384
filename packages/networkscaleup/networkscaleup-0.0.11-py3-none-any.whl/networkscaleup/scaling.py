#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 15 20:34:53 2025

@author: charlescostanzo
"""

import numpy as np

def scaling(log_degrees,
            log_prevalences,
            scaling = "all",
            known_sizes = None,
            known_ind = None,
            Correlation = None,
            G1_ind = None,
            G2_ind = None,
            B2_ind = None,
            N = None):
    
    ## Extract dimensions
    iter, N_i = log_degrees.shape
    N_k = log_prevalences.shape[1]
    
    valid_scalings = ["all", "overdispersed", "weighted", "weighted_sq"]
    assert scaling in valid_scalings, f"Invalid scaling type: {scaling!r}. Must be one of {valid_scalings}"
    
    if Correlation is not None:
        np.fill_diagonal(Correlation, np.nan)
        
    alphas = log_degrees.copy()
    betas = log_prevalences.copy()
    
    known_sizes = np.array(known_sizes)
    known_prevalences = (known_sizes / N).flatten()
    prevalences_vec = np.full(N_k, np.nan)
    prevalences_vec[known_ind] = known_prevalences
    
    if G1_ind is not None:
        Pg1 = np.sum(prevalences_vec[G1_ind])
    if G2_ind is not None:
        Pg2 = np.sum(prevalences_vec[G2_ind])
    if B2_ind is not None:
        Pb2 = np.sum(prevalences_vec[B2_ind])
        
    if scaling == "overdispersed":
        if G1_ind is None:
            raise ValueError("G1_ind cannot be null for scaling option 'overdispersed'")
        if G2_ind is None or B2_ind is None:
            ## Perform scaling with only main
            for ind in range(iter):
                C1 = np.log(np.sum(np.exp(log_prevalences[ind, G1_ind]) / Pg2))
                C = C1
                
                alphas[ind,:] = alphas[ind,:] + C
                betas[ind,:] = betas[ind,:] - C
            else:
                ## Perform scaling with secondary groups
                for ind in range(iter):
                    C1 = np.log(np.sum(np.exp(log_prevalences[ind, G1_ind]) / Pg1))
                    C2 = np.log(np.sum(np.exp(log_prevalences[ind, B2_ind]) / Pb2)) - np.log(np.sum(np.exp(log_prevalences[ind, G2_ind]) / Pg2))
                    
                    C = C1 + (1/2) * C2
                    
                    alphas[ind,:] = alphas[ind,:] + C
                    betas[ind,:] = betas[ind,:] - C
    elif scaling == "all":
        for ind in range(iter):
            C = np.log(np.mean(np.exp(log_prevalences[ind, known_ind]) / known_prevalences))
            
            alphas[ind,:] = alphas[ind,:] + C
            betas[ind,:] = betas[ind,:] - C
    elif scaling == "weighted":
        if Correlation is None:
            raise ValueError("Correlation cannot be null for scaling option 'weighted'")
        for k in range(N_k):
            scale_weights = Correlation[k, known_ind].copy()
    
            scale_weights[scale_weights < 0] = 0
            
            n_valid = np.sum(~np.isnan(scale_weights))
            sum_valid = np.nansum(scale_weights)
            
            if sum_valid == 0:
                scale_weights[:] = 0
            else:
                scale_weights = scale_weights / sum_valid * n_valid
            
            for ind in range(iter):
                C = np.log(np.nanmean(
                    np.exp(log_prevalences[ind, known_ind]) * scale_weights / known_prevalences
                        ))
                
                betas[ind, k] = betas[ind, k] - C
          
        for ind in range(iter):
            C = np.log(np.mean(np.exp(log_prevalences[ind, known_ind]) / known_prevalences))
                
            alphas[ind,:] = alphas[ind,:] + C
                
    elif scaling == "weighted_sq":
        if Correlation is None:
            raise ValueError("Correlation cannot be null for scaling option 'weighted_sq'")
            
        for k in range(N_k):
            scale_weights = Correlation[k, known_ind].copy()

            scale_weights[scale_weights < 0] = 0
            scale_weights = scale_weights ** 2
            
            n_valid = np.sum(~np.isnan(scale_weights))
            sum_valid = np.nansum(scale_weights)
            
            if sum_valid == 0:
                scale_weights[:] = 0
            else:
                scale_weights = scale_weights / sum_valid * n_valid
                
            for ind in range(iter):
                C = np.log(np.nanmean(
                    np.exp(log_prevalences[ind, known_ind]) * scale_weights / known_prevalences[known_ind]
                    ))
                
                betas[ind, k] = betas[ind, k] - C
        for ind in range(iter):
            C = np.log(np.mean(np.exp(log_prevalences[ind, known_ind]) / known_prevalences[known_ind]))
            
            
            alphas[ind,:] = alphas[ind,:] + C
            
    return_dict = {
        "log_degrees": alphas,
        "log_prevalences": betas}
    return return_dict