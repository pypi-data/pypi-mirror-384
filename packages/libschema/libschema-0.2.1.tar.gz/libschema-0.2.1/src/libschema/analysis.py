# -*- coding: utf-8 -*-
"""
Created on Fri Jul 19 14:03:02 2024

@author: dphilippus

This file contains analysis helpers.
"""

import pandas as pd
import numpy as np
import os
rng = np.random.default_rng()

def anomilize(data: pd.DataFrame,
              timestep: str,
              by: str,
              variables: list[str]) -> pd.DataFrame:
    """
    Convert a timeseries to an anomaly timeseries.

    Parameters
    ----------
    data : pd.DataFrame
        Data to be processed
    timestep : str
        Column identifying the main timestep, e.g., date.
    by : str
        Column identifying the recurring timestep, e.g., day-of-year.
    variables : list[str]
        Columns to analyze.

    Returns
    -------
    pd.DataFrame
        DataFrame indexed on `timestep` and `by`, with `variables` anomalies

    """
    data = data[[timestep, by] + variables].dropna()
    return data.set_index([timestep, by])[variables] - data.groupby(by)[variables].mean()


def nse(sim, obs):
    sim = sim.to_numpy()
    obs = obs.to_numpy()
    obsvar = np.std(obs)**2
    if obsvar > 0:
        return 1 - np.mean((sim - obs)**2) / obsvar
    return np.nan
    

def perf_summary(data, obs="temperature", mod="prediction", timestep="date", period="day", long_timestep=lambda x: x["date"].dt.year,
                 statlag=1):
    """Summarize the performance of a modeled column in data compared to an
    observed column.
    
    Goodness-of-fit metrics computed:
        R2, coefficient of determination
        RMSE, root mean square error
        NSE, Nash-Sutcliffe Efficiency, with comparison points:
            StationaryNSE, NSE of "same as N days ago" (using statlag)
            ClimatologyNSE, NSE of "day-of-year mean"
            Note that neither comparison is entirely fair for an ungaged model.
        AnomalyNSE: NSE of the anomaly component only
        Pbias: percent bias (positive equals overestimation)
        Bias: absolute bias, or mean error (positive equals overestimation)
        MaxMiss: mean absolute error of annual maximum temperature
    

    Parameters
    ----------
    data : pandas DataFrame
        DataFrame containing the timeseries data to be analyzed.  This should
        just be for the group of interest, e.g. applied to a grouped DF.
    obs : str
        Column containing observations.
    mod : str
        Column containing predictions.
    timestep : str
        Column containing the timestep, e.g., date.
    period : str
        Column containing the period, e.g., day-of-year.
    long_timestep : function
        Column for extracting a long grouping period (e.g., year) from the data frame.
    statlag : integer
        How many days of lag to use for stationary NSE. Useful for evaluating
        forecast lead time.

    Returns
    -------
    pandas DataFrame
        Single-row data frame containing performance statistics.

    """
    anoms = anomilize(data, timestep, period, [obs, mod])
    clim = data[[timestep, period]].merge(
        data.groupby(period, as_index=False)[obs].mean())
    anom_nse = nse(anoms[mod], anoms[obs])
    clim_nse = nse(clim[obs], data[obs])
    stat_nse = nse(data[obs][:-statlag], data[obs][statlag:])
    return pd.DataFrame({
            "R2": [data[obs].corr(data[mod])**2],
            "RMSE": np.sqrt(np.mean((data[mod] - data[obs])**2)),
            "NSE": nse(data[mod], data[obs]),
            "StationaryNSE": stat_nse,
            "ClimatologyNSE": clim_nse,
            "AnomalyNSE": anom_nse,
            "Pbias": np.mean(data[mod] - data[obs]) / np.mean(data[obs])*100,
            "Bias": np.mean(data[mod] - data[obs]),
            "MaxMiss": data.assign(long=long_timestep).groupby("long")[[obs, mod]].max().assign(maxmiss=lambda x: abs(x[obs] - x[mod]))["maxmiss"].mean()
        })

def kfold(data, modbuilder, parallel=0, by="id", k=10, output=None, redo=False):
    """
    Run a k-fold cross-validation over the given data.  If k=1, run leave-one-
    out instead.  Return and save the results.
    
    This can run over an arbitrary grouping variable, e.g. for regional
    cross-validation.  It's also designed to cache results for repeated use
    in a validation notebook or similar: if `output` exists and `redo` is False,
    it will just load the previous run from `output` and return that.

    Parameters
    ----------
    data : dataframe
        Contains id, date, (observed) temperature, any predictor columns, and
        [by] - the grouping variable.  Must not contain a GroupNo column.
    by : str
        Name of the grouping variable over which to cross-validate.
    modbuilder : function: dataframe -> (dataframe -> Watershed model)
        Function which prepares a coefficient model.  Accepts data, then
        returns a function which itself accepts predictor data and returns a
        prediction data frame.
    k : int
        Number of "folds".  k=1 will cause leave-one-out validation instead.
    output : str, filename
        File name for where to store raw results.
    redo : Bool
        If True, will rerun cross-validation regardless of whether it has
        already been done.  If False, will check if results already exist
        and just return those if that is the case.

    Returns
    -------
    Dataframe of raw cross-validation results.

    """
    if (not redo) and (output is not None) and os.path.exists(output):
        return pd.read_csv(output, dtype={"id": str}).\
            assign(date = lambda x: pd.to_datetime(x["date"]))
    groups = pd.DataFrame({by: data[by].unique()})
    if k==1:
        groups["GroupNo"] = np.arange(len(groups))
    else:
        # Randomly ordered indices, guaranteed at least floor(len/k) per index
        indices = np.arange(len(groups)) % k
        rng.shuffle(indices)
        groups["GroupNo"] = indices
    data = data.merge(groups, on=by)
    def rungrp(grp):
        (gn, df) = grp
        mod = modbuilder(data[data["GroupNo"] != gn].copy())
        return pd.concat([mod(wsdat)
                          for _, wsdat in df.groupby("id")])
    result = pd.concat([rungrp(grp) for grp in data.groupby("GroupNo")])
    if output is not None:
        result.to_csv(output, index=False)
    return result
