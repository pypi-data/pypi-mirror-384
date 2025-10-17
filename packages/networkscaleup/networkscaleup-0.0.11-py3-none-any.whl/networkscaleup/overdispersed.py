#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

@author: charlescostanzo
"""

import numpy as np
import pandas as pd
import networkscaleup
from math import lgamma
from scipy.stats import binom, norm, chi2
from scipy.special import gammaln
import os

from networkscaleup.killworth import killworth

def rinvchisq(size, df, scale=None):
    if scale is None:
        scale = 1/df
    x = np.atleast_1d(chi2.rvs(df, size=size))
    x[x == 0] = 1e-100
    result = (df * scale)/x
    return np.squeeze(result)

def overdispersed(ard = None, known_sizes = None, known_ind = None, G1_ind = None, 
                  G2_ind = None, B2_ind = None, N = None, warmup = 1000, 
                  iter = 1500, refresh = None, thin = 1, verbose = False, 
                  alpha_tune = 0.4, beta_tune = 0.2, omega_tune = 0.2, init = "MLE"):
    N_i, N_k = ard.shape
    
    # convert DataFrames to NumPy arrays
    if isinstance(known_sizes, pd.DataFrame):
        known_sizes = known_sizes.to_numpy().flatten()
    if isinstance(ard, pd.DataFrame):
        ard = ard.to_numpy()
        
    if refresh is None:
        refresh = np.round(iter/10)
        
    known_prevalences = known_sizes/N
    prevalences_vec = np.full(N_k, np.nan)
    prevalences_vec[known_ind] = known_prevalences
    
    if G1_ind is not None:
        Pg1 = np.sum(prevalences_vec[G1_ind])
    if G2_ind is not None:
        Pg2 = np.sum(prevalences_vec[G2_ind])
    if B2_ind is not None:
        Pb2 = np.sum(prevalences_vec[B2_ind])
    alphas = np.full(shape = (iter, N_i), fill_value = np.nan, dtype=float)
    betas = np.full(shape = (iter, N_k), fill_value = np.nan, dtype=float)
    omegas = np.full(shape = (iter, N_k), fill_value = np.nan, dtype=float)
    mu_alpha = np.full(iter, np.nan, dtype=float)
    mu_beta = np.full(iter, np.nan, dtype=float)
    sigma_sq_alpha = np.full(iter, np.nan, dtype=float)
    sigma_sq_beta = np.full(iter, np.nan, dtype=float)
    C1 = np.nan
    C2 = np.nan
    C = np.nan
    
    if isinstance(init, dict):
        if "alpha" in init:
            alphas[0,:] = init["alpha"]
        else:
            alphas[0,:] = np.random.normal(loc = 0, scale = 1, size = N_i)
        
        if "beta" in init:
            betas[0,:] = init["beta"]
        else:
            betas[0,:] = np.random.normal(loc = 0, scale = 1, size = N_k)
        
        if "omega" in init:
            omegas[0,:] = init["omega"]
        else:
            omegas[0,:] = 20
    elif init == "random":
        alphas[0,:] = np.random.normal(loc = 0, scale = 1, size = N_i)
        betas[0,:] = np.random.normal(loc = 0, scale = 1, size = N_k)
        omegas[0,] = 20
    else:
        killworth_init = killworth(pd.DataFrame(ard, 
                                                columns=[f"Group_{i}" for i in range(ard.shape[1])]), 
                                   known_sizes,
                                   known_ind, N, model = "MLE")
        alphas[0,:] = np.log(killworth_init["degrees"])
        alphas[0, np.isinf(alphas[0,:])] = -10
        beta_vec = np.full(N_k, np.nan, dtype = "float")
        beta_vec[known_ind] = known_sizes
        
        unknown_ind = [i for i in range(N_k) if i not in known_ind]
        beta_vec[unknown_ind] = killworth_init["sizes"]
        beta_vec = np.log(beta_vec/N)
        betas[0,:] = beta_vec
        omegas[0,:] = 20
        
    mu_alpha[0] = np.mean(alphas[0,:])
    sigma_alpha_hat = np.mean((alphas[0,:] - mu_alpha[0])**2)
    sigma_sq_alpha[0] = rinvchisq(size = 1, df = N_i - 1, scale = sigma_alpha_hat)
    mu_beta[0] = np.mean(betas[0,:])
    sigma_beta_hat = np.mean((betas[0,:] - mu_beta[0])**2)
    sigma_sq_beta[0] = rinvchisq(size = 1, df = N_k - 1, scale = sigma_beta_hat)
    
    for ind in range(1, iter):
        for i in range(0, N_i):
            alpha_prop = alphas[ind - 1, i] + np.random.normal(loc = 0, scale = alpha_tune)
            zeta_prop = np.exp(alpha_prop + betas[ind - 1,:])/(omegas[ind - 1,:] - 1)
            zeta_old  = np.exp(alphas[ind - 1, i] + betas[ind - 1,:])/(omegas[ind - 1,:] - 1)
            sum1 = np.sum(gammaln(ard[i,:] + zeta_prop) - gammaln(zeta_prop) - 
                       zeta_prop * np.log(omegas[ind - 1,:])) + norm.logpdf(alpha_prop, loc = mu_alpha[ind - 1], scale = np.sqrt(sigma_sq_alpha[ind - 1]))
            sum2 = np.sum(gammaln(ard[i,:] + zeta_old) - gammaln(zeta_old) -
                       zeta_old * np.log(omegas[ind - 1,:])) + norm.logpdf(alphas[ind - 1, i], loc = mu_alpha[ind - 1], scale = np.sqrt(sigma_sq_alpha[ind - 1]))
            prob_acc = np.exp(sum1 - sum2)
            if prob_acc > np.random.uniform(0,1):
                alphas[ind, i] = alpha_prop
            else:
                alphas[ind,i] = alphas[ind - 1, i]
        for k in range(0, N_k):
            beta_prop = betas[ind - 1, k] + np.random.normal(loc = 0, scale = beta_tune)
            zeta_prop = np.exp(alphas[ind,:] + beta_prop)/(omegas[ind - 1, k] - 1)
            zeta_old = np.exp(alphas[ind,:] + betas[ind - 1, k])/(omegas[ind - 1, k] - 1)
            sum1 = np.sum(gammaln(ard[:,k] + zeta_prop) - gammaln(zeta_prop) - 
                          zeta_prop * np.log(omegas[ind - 1, k])) + norm.logpdf(beta_prop, loc = mu_beta[ind - 1], scale = np.sqrt(sigma_sq_beta[ind - 1]))
            sum2 = np.sum(gammaln(ard[:,k] + zeta_old) - gammaln(zeta_old) -
                          zeta_old * np.log(omegas[ind - 1, k])) + norm.logpdf(betas[ind - 1, k], loc = mu_beta[ind - 1], scale = np.sqrt(sigma_sq_beta[ind - 1]))
            prob_acc = np.exp(sum1 - sum2)
            if prob_acc > np.random.uniform(0,1):
                betas[ind, k] = beta_prop
            else:
                betas[ind, k] = betas[ind - 1, k]
        mu_alpha_hat = np.mean(alphas[ind,:])
        mu_alpha[ind] = np.random.normal(loc = mu_alpha_hat, scale = np.sqrt(sigma_sq_alpha[ind-1]/2))
        sigma_alpha_hat = np.mean((alphas[ind,:] - mu_alpha[ind])**2)
        sigma_sq_alpha[ind] = rinvchisq(size = 1, df = N_i - 1, scale = sigma_alpha_hat)
        mu_beta_hat = np.mean(betas[ind,:])
        mu_beta[ind] = np.random.normal(loc = mu_beta_hat, scale = np.sqrt(sigma_sq_beta[ind - 1]/2))
        sigma_beta_hat = np.mean((betas[ind,:] - mu_beta[ind])**2)
        sigma_sq_beta[ind] = rinvchisq(size = 1, df = N_k - 1, scale = sigma_beta_hat)
        for k in range(0, N_k):
            omega_prop = omegas[ind - 1, k] + np.random.normal(loc = 0, scale = omega_tune)
            if omega_prop > 1:
                zeta_prop = np.exp(alphas[ind,:] + betas[ind, k])/(omega_prop - 1)
                zeta_old = np.exp(alphas[ind,:] + betas[ind, k])/(omegas[ind - 1, k] - 1)
                sum1 = np.sum(gammaln(ard[:,k] + zeta_prop) - gammaln(zeta_prop) -
                              zeta_prop * np.log(omega_prop) + ard[:,k] * np.log((omega_prop - 1)/omega_prop))
                sum2 = np.sum(gammaln(ard[:,k] + zeta_old) - gammaln(zeta_old) -
                              zeta_old * np.log(omegas[ind - 1, k]) + 
                              ard[:,k] * np.log((omegas[ind - 1, k] - 1)/omegas[ind - 1, k]))
                prob_acc = np.exp(sum1 - sum2)
                if prob_acc > np.random.uniform(0,1):
                    omegas[ind, k] = omega_prop
                else:
                    omegas[ind, k] = omegas[ind - 1, k]
            else:
                omegas[ind, k] = omegas[ind - 1, k]
        if G1_ind is None:
            C = 0
        elif G2_ind is None or B2_ind is None:
            C1 = np.log(np.sum(np.exp(betas[ind, [G1_ind]])/Pg1))
            C = C1
        else:
            C1 = np.log(np.sum(np.exp(betas[ind, [G1_ind]])/Pg1))
            C2 = np.log(np.sum(np.exp(betas[ind, [B2_ind]])/Pb2)) - np.log(np.sum(np.exp(betas[ind, [G2_ind]])/Pg2))
            C = C1 + ((1/2) * C2)
        alphas[ind,:] = alphas[ind,:] + C
        mu_alpha[ind] = mu_alpha[ind] + C
        betas[ind,:] = betas[ind,:] - C
        mu_beta[ind] = mu_beta[ind] - C
        
        if verbose == True:
            if ind % refresh == 0:
                print(f"Iteration: {ind} / {iter} [{round(ind / iter * 100)}%]")
    
    alphas = alphas[warmup:,:]
    betas = betas[warmup:,:]
    omegas = omegas[warmup:,:]
    mu_alpha = mu_alpha[warmup:]
    mu_beta = mu_beta[warmup:]
    sigma_sq_alpha = sigma_sq_alpha[warmup:]
    sigma_sq_beta = sigma_sq_beta[warmup:]
    thin_ind = np.arange(0, alphas.shape[0], thin)
    alphas = alphas[thin_ind,:]
    betas = betas[thin_ind,:]
    omegas = omegas[thin_ind,:]
    mu_alpha = mu_alpha[thin_ind]
    mu_beta = mu_beta[thin_ind]
    sigma_sq_alpha = sigma_sq_alpha[thin_ind]
    sigma_sq_beta = sigma_sq_beta[thin_ind]
    return_dict = {
        "alphas" : alphas,
        "degrees" : np.exp(alphas),
        "betas" : betas,
        "sizes" : np.exp(betas) * N,
        "omegas" : omegas,
        "mu_alpha" : mu_alpha,
        "mu_beta" : mu_beta,
        "sigma_sq_alpha" : sigma_sq_alpha,
        "sigma_sq_beta" : sigma_sq_beta
        }
    return return_dict










