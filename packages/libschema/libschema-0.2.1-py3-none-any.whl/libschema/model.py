"""
Author: Daniel Philippus
Date: 2025-02-05

This file implements the core SCHEMA model class.
"""

import pandas as pd
import numpy as np
from yaml import load, dump, Loader
from libschema.classes import Anomaly, Seasonality, ModEngine
from libschema.analysis import anomilize

class SCHEMA(object):
    """A generic implementation of the SCHEMA framework (https://doi.org/10.1016/j.jhydrol.2025.133321).
    
    Parameters
    ----------
    seasonality : classes.Seasonality
        Seasonality implementation.
    anomaly : classes.Anomaly
        Anomaly implementation.
    periodics : pd.DataFrame with [period, columns]
        Periodic values of all columns.
    engines : list of [(frequency, classes.ModEngine)]
        Modification engines to apply at specified frequencies.
    columns : [str]
        List of required column names.
    max_period : int
        Point at which the period resets to 0 if not specified.
    window : int, optional
        Lookback window for anomaly history. The default is 1.
    stepsize : number, optional
        Number of steps (in periodic function) per runtime step. The
        default is 1.
    logfile : str, optional
        Where to log, if any. The default is None.
    static_coefs : bool, optional
        For use with modification engines: should engines act on the
        initial coefficients (True), or the current coefficients (False)?
        In other words, where engine at timestep is fi(x) of coefficients (x),
        should xi=fi(x0) or xi=fi(fi-1(fi-2(...(x0))))?
        The default is True (xi=fi(x0)).
    init_period : int, optional
        Default initial period, if any. The default is None.
    """
    def __init__(self, seasonality: Seasonality,
                 anomaly: Anomaly,
                 periodics: pd.DataFrame,
                 engines: list[tuple[int, ModEngine]],
                 columns: list[str],
                 max_period: int,
                 window:int=1,
                 stepsize:int=1,
                 logfile:str=None,
                 static_coefs:bool=True,
                 init_period:int=None):
        """
        Parameters
        ----------
        seasonality : classes.Seasonality
            Seasonality implementation.
        anomaly : classes.Anomaly
            Anomaly implementation.
        periodics : pd.DataFrame with [period, columns]
            Periodic values of all columns.
        engines : list of [(frequency, classes.ModEngine)]
            Modification engines to apply at specified frequencies.
        columns : [str]
            List of required column names.
        max_period : int
            Point at which the period resets to 0 if not specified.
        window : int, optional
            Lookback window for anomaly history. The default is 1.
        stepsize : number, optional
            Number of steps (in periodic function) per runtime step. The
            default is 1.
        logfile : str, optional
            Where to log, if any. The default is None.
        static_coefs : bool, optional
            For use with modification engines: should engines act on the
            initial coefficients (True), or the current coefficients (False)?
            In other words, where engine at timestep is fi(x) of coefficients (x),
            should xi=fi(x0) or xi=fi(fi-1(fi-2(...(x0))))?
            The default is True (xi=fi(x0)).
        init_period : int, optional
            Default initial period, if any. The default is None.

        Returns
        -------
        SCHEMA
            The SCHEMA object.

        """
        self.step = None
        self.period = init_period
        self.seasonality = seasonality
        self.anomaly = anomaly
        self.periodics = periodics
        self.engine_periods = [i[0] for i in engines]
        self.engines = {i[0]: i[1] for i in engines}
        self.columns = columns
        self.max_period = max_period
        self.window = window
        self.stepsize = stepsize
        self.logfile = logfile
        self.output = None
        self.periodic_output = None
        self.values = {}
        self.prediction = None
        self.static_coefs = static_coefs
        if self.static_coefs:
            self.ssn_static = self.seasonality
            self.anom_static = self.anomaly
    
    @classmethod
    def from_file(cls, filename: str):
        try:
            with open(filename) as f:
                coefs = load(f, Loader)
            return cls(**coefs)
        except Exception as e:
            with open("unspecified_log.txt", "w") as f:
                f.write(f"Error in loading {filename}: {e}")
    
    def to_file(self, filename: str):
        data = {
            "seasonality": self.seasonality,
            "anomaly": self.anomaly,
            "periodics": self.periodics,
            "engines": [(i, self.engines[i]) for i in self.engine_periods],
            "columns": self.columns,
            "max_period": self.max_period,
            "window": self.window,
            "stepsize": self.stepsize,
            "logfile": self.logfile,
            "init_period": self.period
            }
        with open(filename, "w") as f:
            dump(data, f)
    
    def to_dict(self):
        coefs = {"window": self.window}
        for item in [self.seasonality, self.anomaly] + list(self.engines.values()):
            coefs = coefs | item.to_dict()
        return coefs
    
    def log(self, text, reset=False):
        if self.logfile is not None:
            with open(self.logfile, "w" if reset else "a") as f:
                f.write(text + "\n")

    def initialize_run(self, period: int):
        # Initialize a model run for incremental use. Period is the initial
        # period.
        self.output = None
        self.periodic_output = None
        self.anomaly_output = None
        self.anomaly_history = None
        self.step = 0
        self.period = period
        self.history = {x: [] for x in self.columns} | {"period": [],
                                                        "anomaly": [],
                                                        "ssn": [],
                                                        "prediction": []}
    
    def get_history(self) -> pd.DataFrame:
        return pd.DataFrame(self.history)
        
    def trigger_engine(self, engine: ModEngine):
        if self.static_coefs:
            self.ssn_static = self.seasonality
            self.anom_static = self.anomaly
        ssn = self.ssn_static if self.static_coefs else self.seasonality
        anom = self.anom_static if self.static_coefs else self.anomaly
        (self.seasonality, self.anomaly, self.periodics) =\
            engine.apply(ssn, anom, self.periodics,
                         self.get_history())
    
    def set_val(self, key, value, bmiroll=False):
        """
        BMI set-value functionality. You may wish to implement custom functionality
        here, e.g., to handle specific variables differently.
        
        bmiroll allows for mismatched timesteps, such as running a daily-resolution
        model in an hourly NextGen setup. The BMI implementation can pass an
        array of values which can be handled as a single mean value here.
        """
        if bmiroll:
            value = np.mean(value)
        self.values[key] = value

    def run_step(self, inputs=None, period=None):
        """
        Run a single step, incrementally.  Updates history and returns
        today's prediction.
        
        inputs is a dictionary of the required inputs, unless they have been
        specified by setting values.
        
        period can be used to change the current period (e.g., skipping a few days).
        Otherwise, it increments by 1.
        """
        if inputs is None:
            inputs = {}
        for k in self.columns:
            if not k in inputs:
                if not k in self.values:
                    raise ValueError(f"In step, must provide all specified data. Missing: {k}")
                inputs[k] = self.values[k]
            self.history[k].append(inputs[k])
        self.step += 1
        if period is None:
            self.period += 1
        else:
            self.period = period
        self.history["period"].append(self.period)
        # today = self.periodics.loc[self.periodics["period"] == self.period].set_index("period")
        # Now, build the prediction
        ssn = self.seasonality.apply(self.period)
        self.periodic_output = ssn
        self.history["ssn"].append(ssn)
        # Compute anomaly history
        window = self.window if self.window <= self.step else self.step
        # All this weird stuff is to get the right coverage.
        history = pd.DataFrame({k: self.history[k][-window:]
                                for k in self.columns + ["period"]}).set_index("period")
        # Specifically, we don't want a bunch of NAs for unmatched rows in periodics.
        anom_hist = (history - self.periodics.set_index("period").filter(history.index, axis=0)
                     )[self.columns]
        self.anomaly_history = anom_hist
        anom = self.anomaly.apply(ssn, self.period, anom_hist)
        self.anomaly_output = anom
        self.history["anomaly"].append(anom)
        # Final result
        pred = ssn + anom
        self.history["prediction"].append(pred)
        self.output = pred
        # Run triggers
        for eng_step in self.engine_periods:
            if self.step % eng_step == 0:
                self.trigger_engine(self.engines[eng_step])
        return pred
    
    def run_series_incremental(self, data, period=None):
        """
        Run a full timeseries at once, but internally use the stepwise approach.
        This is useful if modification engines are in use.
        Period specifies a period column if one exists.
        """
        self.initialize_run(0 if period is None else data[period].iloc[0])
        for row in data.itertuples():
            inputs = {k: getattr(row, k) for k in self.columns}
            if period is None:
                perval = None
            else:
                perval = getattr(row, period)
            yield self.run_step(inputs, perval)
        

    def run_series(self, data, timestep_col, init_period=1, period_col=None, context=True):
        """
        Run a full timeseries at once if modification engines are not present.
        Otherwise, reverts to run_series_incremental.
        Period_col specifies a period column if one exists.
        Returns the predicted array (if context=False) or the data with an added prediction
        column (if context=True).
        """
        if len(self.engine_periods) > 0:
            # There are modification engines, so we need to run incrementally.
            # This could be "smartened" to run in blocks except when engine
            # application is needed, but this will do for now.
            output = list(self.run_series_incremental(data, period_col))
            return self.get_history().assign(output=output)
        # Run in a single pass.
        if period_col is None:
            period_steps = (np.arange(init_period, len(data) + init_period) *
                            self.stepsize) % self.max_period
        else:
            period_steps = data[period_col].to_numpy()
        ssn = self.seasonality.apply_vec(period_steps)
        data["period"] = period_steps
        periodics = self.periodics.set_index("period")
        selcols = [c for c in self.columns if not c in [timestep_col,
                                                        period_col]]
        anom_hist = (data.set_index([timestep_col, "period"])[selcols] -
                     periodics[selcols])
        anom = self.anomaly.apply_vec(ssn, period_steps, anom_hist)
        pred = ssn + anom
        self.prediction = pred
        if context:
            data["prediction"] = pred
            return data
        return pred

    def from_data(data):
        raise NotImplementedError("SCHEMA.from_data")
