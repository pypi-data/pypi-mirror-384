# -*- coding: utf-8 -*-
"""
This file defines key classes for libSCHEMA.
"""

class ModEngine(object):
    """
    Generic modification engine. Internal structure is entirely arbitrary.
    Key logic requirements are specified in ModEngine.apply.
    """
    def apply(self, seasonality, anomaly, periodics, history):
        """
        Apply ModEngine to model coefficients and update them.

        Parameters
        ----------
        seasonality : Seasonality
            Current model seasonality object.
        anomaly : Anomaly
            Current model anomaly object.
        periodics : DataFrame
            Current model periodics (i.e. day-of-year means or similar).
        history : DataFrame
            Model input history dataframe containing required ModEngine inputs.

        Returns
        -------
        (Seasonality, Anomaly, DataFrame)
            Updated seasonality, anomaly, and periodics. May be unchanged.
        """
        raise NotImplementedError("ModEngine.apply")
        return (seasonality, anomaly, periodics)
    
    def coefficients(self):
        """
        Return a dictionary containing ModEngine coefficients, if applicable.
        Designed for use in analyzing ModEngines, e.g. as a dataframe, not necessarily
        reconstructing them.
        """
        raise NotImplementedError("ModEngine.coefficients")
        return {}
    
    def from_data():
        """
        Fit ModEngine from data, if applicable.
        """
        raise NotImplementedError("ModEngine.from_data")
    
    def to_dict(self):
        """
        Convert ModEngine to a dictionary, if applicable. This differs from .coefficients()
        because it is intended to contain information for rebuilding the entire ModEngine,
        not just coefficients - e.g., for to/from file.
        """
        raise NotImplementedError("ModEngine.to_dict")

    def from_dict(d):
        """
        Rebuild a ModEngine from a dictionary. This may be as simple as
        return ModEngine(**d), or more complex.
        """
        raise NotImplementedError("ModEngine.from_dict")
        

class Seasonality(object):
    def apply(self, period):
        raise NotImplementedError("Seasonality.apply")
    
    def apply_vec(self, period_array):
        raise NotImplementedError("Seasonality.apply_vec")
        
    def to_dict(self):
        raise NotImplementedError("Seasonality.to_dict")

    def from_dict(d):
        raise NotImplementedError("Seasonality.from_dict")


class Anomaly(object):
    def apply(self, periodic, period, anom_history):
        raise NotImplementedError("Anomaly.apply")
    
    def apply_vec(self, periodic, period, anom_history):
        raise NotImplementedError("Anomaly.apply_vec")
        
    def to_dict(self):
        raise NotImplementedError("Anomaly.to_dict")

    def from_dict(d):
        raise NotImplementedError("Anomaly.from_dict")
