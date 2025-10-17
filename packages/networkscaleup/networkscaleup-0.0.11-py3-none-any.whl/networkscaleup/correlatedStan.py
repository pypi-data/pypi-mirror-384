#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: charlescostanzo
"""

import numpy as np
import pandas as pd
from networkscaleup import cmdstan_utils
from networkscaleup.scaling import scaling as scaling_fn

def correlatedStan(ard,
                   known_sizes = None,
                   known_ind = None,
                   N = None,
                   model = "correlated",
                   scaling = "all",
                   x = None,
                   z_global = None,
                   z_subpop = None,
                   G1_ind = None,
                   G2_ind = None,
                   B2_ind = None,
                   chains = 3,
                   cores = 1,
                   warmup = 1000,
                   iter = 1500,
                   thin = 1,
                   return_fit = False,
                   **kwargs):
    
    N_i, N_k = ard.shape
    
    valid_models = ["correlated", "uncorrelated"]
    assert model in valid_models, f"Invalid model type: {model!r}. Must be one of {valid_models}"
    
    valid_scalings = ["all", "overdispersed", "weighted", "weighted_sq"]
    assert scaling in valid_scalings, f"Invalid scaling type: {scaling!r}. Must be one of {valid_scalings}"

    ## Check dimensions of x
    
    if x is not None:
        if x.shape != (N_i, N_k):
            raise ValueError("Dimensions of x do not match dimensions of ard")
            
    ## Check for scaling method
    if model == "uncorrelated" and scaling in ["weighted", "weighted_sq"]:
        raise ValueError("Model must be 'correlated' to using 'weighted' or 'weightedsq' scaling")
        
    ## Check dimensions of z
    if z_global is not None:
        if z_global.shape[0] != N_i:
            raise ValueError("Dimensions of z_global do not match dimensions of ard")
        else:
            z_global_size = z_global.shape[1]
    
    if z_subpop is not None:
        if z_subpop.shape[0] != N_i:
            raise ValueError("Dimensions of z_subpop do not match dimensions of ard")
        else: 
            z_subpop_size = z_subpop.shape[1]
    
    ## Set model of 16 possible combinations
    if model == "correlated":
        if x is None:
            ## No level of respect
            if z_global is None:
                ## No global covariates
                if z_subpop is None:
                    ## No subpop covariates
                    ## Basic model
                    stan_data = {
                        "N": N,
                        "n_i": N_i,
                        "n_k": N_k,
                        "y": ard
                        }
                    ## Fit model
                    model = cmdstan_utils.load_stan_model("Correlated_basic")
                
                    model_fit = model.sample(
                        data = stan_data,
                        chains = chains,
                        parallel_chains = cores,
                        iter_sampling = iter,
                        iter_warmup = warmup,
                        thin = thin,
                        **kwargs
                        )
                
                else:
                    ## Includes only zsubpop
                    stan_data = {
                        "N": N,
                        "n_i": N_i,
                        "n_k": N_k,
                        "z_subpop_size": z_subpop_size,
                        "z_subpop": z_subpop,
                        "y": ard
                        }
                    ## Fit model
                    model = cmdstan_utils.load_stan_model("Correlated_zsubpop")
                    
                    model_fit = model.sample(
                        data = stan_data,
                        chains = chains,
                        parallel_chains = cores,
                        iter_sampling = iter,
                        iter_warmup = warmup,
                        thin = thin,
                        **kwargs)
            else:
                ## Does not include global covariates
                if z_subpop is None:
                    ## No subpop covariates
                    ## Only global
                    stan_data = {
                        "N": N,
                        "n_i": N_i,
                        "n_k": N_k,
                        "z_global_size": z_global_size,
                        "z_global": z_global,
                        "y": ard}
                    
                    ## Fit model
                    model = cmdstan_utils.load_stan_model("Correlated_zglobal")
                    
                    model_fit = model.sample(
                        data = stan_data,
                        chains = chains,
                        parallel_chains = cores,
                        iter_sampling = iter,
                        iter_warmup = warmup,
                        thin = thin,
                        **kwargs)
                else:
                    ## Includes zglobal and zsubpop
                    stan_data = {
                        "N": N,
                        "n_i": N_i,
                        "n_k": N_k,
                        "z_global_size": z_global_size,
                        "z_global": z_global,
                        "z_subpop_size": z_subpop_size,
                        "z_subpop": z_subpop,
                        "y": ard
                        }
                    
                    ## Fit model
                    model = cmdstan_utils.load_stan_model("Correlated_zsubpop_zglobal")
                    
                    model_fit = model.sample(
                        data = stan_data,
                        chains = chains,
                        parallel_chains = cores,
                        iter_sampling = iter,
                        iter_warmup = warmup,
                        thin = thin,
                        **kwargs)
        else:
            ## Includes z
            if z_global is None:
                ## No global covariates
                if z_subpop is None:
                    ## No subpop covariates
                    ## Only x
                    stan_data = {
                        "N": N,
                        "n_i": N_i,
                        "n_k": N_k,
                        "x": x.tolist(),
                        "y": ard}
                    
                    ## Fit model
                    model = cmdstan_utils.load_stan_model("Correlated_x")
                    
                    model_fit = model.sample(
                        data = stan_data,
                        chains = chains,
                        parallel_chains = cores,
                        iter_sampling = iter,
                        iter_warmup = warmup,
                        thin = thin,
                        **kwargs)
                else:
                    ## Includes x and z_subpop
                    stan_data = {
                        "N": N,
                        "n_i": N_i,
                        "n_k": N_k,
                        "x": x.tolist(),
                        "z_subpop_size": z_subpop_size,
                        "z_subpop": z_subpop,
                        "y": ard}
                    
                    ## Fit model
                    model = cmdstan_utils.load_stan_model("Correlated_x_zsubpop")
                    
                    model_fit = model.sample(
                        data = stan_data,
                        chains = chains,
                        parallel_chains = cores,
                        iter_sampling = iter,
                        iter_warmup = warmup,
                        thin = thin,
                        **kwargs)
            else:
                ## Does include global covariates
                if z_subpop is None:
                    ## No subpop covariates
                    ## Includes x and zglobal
                    stan_data = {
                        "N": N,
                        "n_i" : N_i,
                        "n_k": N_k,
                        "x": x.tolist(),
                        "z_global_size": z_global_size,
                        "z_global": z_global,
                        "y": ard}
                    
                    ## Fit model
                    model = cmdstan_utils.load_stan_model("Correlated_x_zglobal")
                    
                    model_fit = model.sample(
                        data = stan_data,
                        chains = chains,
                        parallel_chains = cores,
                        iter_sampling = iter,
                        iter_warmup = warmup,
                        thin = thin,
                        **kwargs)
                    
                else:
                    ## Includes x, zglobal, and zsubpop
                    stan_data = {
                        "N": N,
                        "n_i": N_i,
                        "n_k": N_k,
                        "x": x.tolist(),
                        "z_global_size": z_global_size,
                        "z_global": z_global.tolist(),
                        "z_subpop_size": z_subpop_size,
                        "z_subpop": z_subpop.tolist(),
                        "y": ard.tolist()}
                    
                    ## Fit model
                    model = cmdstan_utils.load_stan_model("Correlated_x_zsubpop_zglobal")
                    
                    model_fit = model.sample(
                        data = stan_data,
                        chains = chains,
                        parallel_chains = cores,
                        iter_sampling = iter,
                        iter_warmup = warmup,
                        thin = thin,
                        **kwargs)
    elif model == "uncorrelated":
        if x is None:
            ## No level of respect
            if z_global is None:
                ## no global covariates
                if z_subpop is None:
                    ## No subpop covariates
                    ## Basic model
                    stan_data = {
                        "N": N,
                        "n_i": N_i,
                        "n_k": N_k,
                        "y": ard}
                    ## Fit model
                    model = cmdstan_utils.load_stan_model("Uncorrelated_basic")
                    
                    model_fit = model.sample(
                        data = stan_data,
                        chains = chains,
                        parallel_chains = cores,
                        iter_sampling = iter,
                        iter_warmup = warmup,
                        thin = thin,
                        **kwargs)
                else:
                    ## Includes only zsubpop
                    stan_data = {
                        "N": N,
                        "n_i": N_i,
                        "n_k": N_k,
                        "z_subpop_size": z_subpop_size,
                        "z_subpop": z_subpop,
                        "y": ard}
                    
                    ## Fit model
                    model = cmdstan_utils.load_stan_model("Uncorrelated_zsubpop")
    
                    model_fit = model.sample(
                        data = stan_data,
                        chains = chains,
                        parallel_chains = cores,
                        iter_sampling = iter,
                        iter_warmup = warmup,
                        thin = thin,
                        **kwargs)
            else:
                ## Does include global covariates
                if z_subpop is None:
                    ## No subpop covariates
                    ## Only global
                    stan_data = {
                        "N": N,
                        "n_i": N_i,
                        "n_k": N_k,
                        "z_global_size": z_global_size,
                        "z_global": z_global,
                        "y": ard}
                    
                    ## Fit model
                    model = cmdstan_utils.load_stan_model("Uncorrelated_zglobal")
    
                    model_fit = model.sample(
                        data = stan_data,
                        chains = chains,
                        parallel_chains = cores,
                        iter_sampling = iter,
                        iter_warmup = warmup,
                        thin = thin,
                        **kwargs)
                else:
                    ## Includes zglobal and zsubpop
                    stan_data = {
                        "N": N,
                        "n_i": N_i,
                        "n_k": N_k,
                        "z_global_size": z_global_size,
                        "z_global": z_global,
                        "z_subpop_size": z_subpop_size,
                        "z_subpop": z_subpop,
                        "y": ard}
                    
                    ## Fit model
                    model = cmdstan_utils.load_stan_model("Uncorrelated_zsubpop_zglobal")
    
                    model_fit = model.sample(
                        data = stan_data,
                        chains = chains,
                        parallel_chains = cores,
                        iter_sampling = iter,
                        iter_warmup = warmup,
                        thin = thin,
                        **kwargs)
        else:
            ## Includes x
            if z_global is None:
                ## No global covariates
                if z_subpop is None:
                    ## No subpop covariates
                    ## Only x
                    stan_data = {
                        "N": N,
                        "n_i": N_i,
                        "n_k": N_k,
                        "x": x.tolist(),
                        "y": ard
                        }
                    
                    ## Fit model
                    model = cmdstan_utils.load_stan_model("Uncorrelated_x")
    
                    model_fit = model.sample(
                        data = stan_data,
                        chains = chains,
                        parallel_chains = cores,
                        iter_sampling = iter,
                        iter_warmup = warmup,
                        thin = thin,
                        **kwargs)
                else:
                    ## Includes x and z_subpop
                    stan_data = {
                        "N": N,
                        "n_i": N_i,
                        "n_k": N_k,
                        "x": x.tolist(),
                        "z_subpop_size": z_subpop_size,
                        "z_subpop": z_subpop,
                        "y": ard
                        }
                    
                    ## Fit model
                    model = cmdstan_utils.load_stan_model("Uncorrelated_x_zsubpop")
    
                    model_fit = model.sample(
                        data = stan_data,
                        chains = chains,
                        parallel_chains = cores,
                        iter_sampling = iter,
                        iter_warmup = warmup,
                        thin = thin,
                        **kwargs)
            else: 
                ## Does include global covariates
                if z_subpop is None:
                    ## No subpop covariates
                    ## Includes x and zglobal
                    stan_data = {
                        "N": N,
                        "n_i": N_i,
                        "n_k": N_k,
                        "x": x.tolist(),
                        "z_global_size": z_global_size,
                        "z_global": z_global,
                        "y": ard
                        }
                    
                    ## Fit model
                    model = cmdstan_utils.load_stan_model("Uncorrelated_x_zglobal")
    
                    model_fit = model.sample(
                        data = stan_data,
                        chains = chains,
                        parallel_chains = cores,
                        iter_sampling = iter,
                        iter_warmup = warmup,
                        thin = thin,
                        **kwargs)
                else:
                    ## Includes x, zglobal, and zsubpop
                    stan_data = {
                        "N": N,
                        "n_i": N_i,
                        "n_k": N_k,
                        "x": x.tolist(),
                        "z_global_size": z_global_size,
                        "z_global": z_global,
                        "z_subpop_size": z_subpop_size,
                        "z_subpop": z_subpop,
                        "y": ard
                        }
                    ## Fit model
                    model = cmdstan_utils.load_stan_model("Uncorrelated_x_zsubpop_zglobal")
    
                    model_fit = model.sample(
                        data = stan_data,
                        chains = chains,
                        parallel_chains = cores,
                        iter_sampling = iter,
                        iter_warmup = warmup,
                        thin = thin,
                        **kwargs)
    else:
        raise ValueError("Invalid model choice")
        
    ## Extract draws
    ## Exclude eps and L_Omega (if correlated) for memory
    if model == "correlated":
        all_draws = model_fit.stan_variables()
        
        draws = {k: v for k, v in all_draws.items() if k not in ["eps", "L_Omega"]}
    else:
        all_draws = model_fit.stan_variables()
        draws = {k: v for k, v in all_draws.items() if k != "eps"}
    
    ## Perform scaling procedure
    delta = draws["delta"]
    sigma_delta = draws["sigma_delta"]
    
    n_draws, N_i = delta.shape
    log_degrees = np.full((n_draws, N_i), np.nan)
    
    for i in range(n_draws):
        log_degrees[i,:] = delta[i,:] * sigma_delta[i]
    
    if scaling is not None:
        if scaling == "weighted" or scaling == "weighted_sq":
            ## First get point estimate for correlation matrix
            Correlation = draws["Corr"].mean(axis=0)
            scaling_res = scaling_fn(
                log_degrees = log_degrees,
                log_prevalences = draws["rho"],
                scaling = scaling,
                known_sizes = known_sizes,
                known_ind = known_ind,
                Correlation = Correlation,
                N = N
                )
        elif scaling == "all":
            scaling_res = scaling_fn(
                log_degrees = log_degrees,
                log_prevalences = draws["rho"],
                scaling = scaling,
                known_sizes = known_sizes,
                known_ind = known_ind,
                N = N)
        
        elif scaling == "overdispersed":
            scaling_res = scaling_fn(
                log_degrees = log_degrees,
                log_prevalences = draws["rho"],
                scaling = scaling,
                known_sizes = known_sizes,
                known_ind = known_ind,
                G1_ind = G1_ind,
                G2_ind = G2_ind,
                B2_ind = B2_ind,
                N = N)
            
        draws["log_degrees"] = scaling_res["log_degrees"]
        draws["degrees"] = np.exp(draws["log_degrees"])
        draws["log_prevalences"] = scaling_res["log_prevalences"]
        draws["sizes"] = np.exp(draws["log_prevalences"]) * N
        
        ## Return values
        
    if return_fit:
        return model_fit
    else:
        return draws
    
    
    
    
    
    
    
    
    