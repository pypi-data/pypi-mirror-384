#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: charlescostanzo
"""

import numpy as np
import pandas as pd
from networkscaleup import cmdstan_utils

def overdispersedStan(ard, known_sizes = None, known_ind = None, G1_ind = None,
                      G2_ind = None, B2_ind = None, N = None, chains = 3,
                      cores = 1, warmup = 1000, iter = 1500, thin = 1,
                      return_fit = False, **kwargs):
    cmdstan_utils.ensure_cmdstan_installed()
    N_i, N_k = ard.shape
    known_prevalences = known_sizes/N
    prevalences_vec = np.full(N_k, np.nan)
    prevalences_vec[known_ind] = known_prevalences
    
    if G1_ind is not None:
        Pg1 = np.sum(prevalences_vec[G1_ind])
    if G2_ind is not None:
        Pg2 = np.sum(prevalences_vec[G2_ind])
    if B2_ind is not None:
        Pb2 = np.sum(prevalences_vec[B2_ind])
    
    stan_data = {
        "n_i": N_i,
        "n_k": N_k,
        "y": ard
        }
    
    model = cmdstan_utils.load_stan_model("Overdispersed_Stan")
    
    overdispersed_fit = model.sample(
    data=stan_data,
    chains=chains,
    parallel_chains=cores,
    iter_sampling=iter,
    iter_warmup=warmup,
    refresh=100,
    thin=thin,
    **kwargs
    )
    draws = overdispersed_fit.stan_variables()
    
    betas = draws["betas"]
    mu_beta = draws["mu_beta"]
    alphas = draws["alphas"]
    mu_alpha = np.full(betas.shape[0], np.nan)
    
    if G1_ind is None:
      pass  
    elif G2_ind is None or B2_ind is None:
        for ind in range(betas.shape[0]):
            C1 = np.log(np.sum(np.exp(betas[ind, G1_ind]) / Pg1))
            C = C1
            alphas[ind,:] = alphas[ind,:] + C
            mu_alpha[ind] = C
            betas[ind,:] = betas[ind,:] - C
            mu_beta[ind] = mu_beta[ind] - C
        draws["betas"] = betas
        draws["alphas"] = alphas
        draws["mu_beta"] = mu_beta
        draws["mu_alpha"] = mu_alpha
        draws["degrees"] = np.exp(draws["alphas"])
        draws["sizes"] = np.exp(draws["betas"]) * N
    else:
        for ind in range(betas.shape[0]):
            C1 = np.log(np.sum(np.exp(betas[ind, G1_ind])/Pg1))
            C2 = np.log(np.sum(np.exp(betas[ind, B2_ind])/Pb2)) - np.log(np.sum(np.exp(betas[ind, G2_ind])/Pg2))
            
            C = C1 + 1/2 * C2
            alphas[ind,:] = alphas[ind,:] + C
            mu_alpha[ind] = C
            betas[ind,:] = betas[ind,:] - C
            mu_beta[ind] = mu_beta[ind] - C
        draws["betas"] = betas
        draws["alphas"] = alphas
        draws["mu_beta"] = mu_beta
        draws["mu_alpha"] = mu_alpha
        draws["degrees"] = np.exp(draws["alphas"])
        draws["sizes"] = np.exp(draws["betas"]) * N
    if return_fit:
        return overdispersed_fit
    else:
        return draws


