"""This module provides the time operators for FLEXPART preprocessing."""

# Standard library
import numpy as np
import xarray as xr


def time_rate(var: xr.DataArray, dtime: np.timedelta64)-> xr.DataArray:

    """Compute a time rate for a given delta in time.

    It assumes the input data is an accumulated value
    between two time steps of the time coordinate

    Args:
        var: variable that contains the input data
        dtime: delta time of the desired output time rate

    """
    result = var.diff("step") * (dtime / var["step"].diff("step"))

    # TODO: The fields passed to this operator are currently in GRIB1 but will be
    # converted to GRIB2. Override the metadata accordingly.
    return xr.DataArray(
        data=result,
        attrs=var.attrs
    )
