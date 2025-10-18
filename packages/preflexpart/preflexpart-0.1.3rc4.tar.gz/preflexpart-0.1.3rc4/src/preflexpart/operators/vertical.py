"""This module provides the vertical operators for FLEXPART preprocessing."""

# Standard library
import numpy as np
import xarray as xr


def omega_slope(
    ps: xr.DataArray, etadot: xr.DataArray, ak: xr.DataArray, bk: xr.DataArray
)-> xr.DataArray:
    """Compute the omega slope.

    Converts ECMWF etadot (deta/dt) to etadot * dp/deta, required by FLEXPART.

    Parameters
    ----------
    ps : xarray.DataArray
        Pressure (S) (not reduced) in Pa.
    etadot : xarray.DataArray
        Eta-coordinate vertical velocity (deta/dt) in s**-1.
    ak : xarray.DataArray
        Hybrid level A coefficient.
    bk : xarray.DataArray
        Hybrid level B coefficient.


    Returns
    -------
    xarray.DataArray
        Vertical velocity (pressure) in Pa s**-1.

    """
    # Surface pressure reference for omega slope
    surface_pressure_ref = 101325.0  # [Pa]

    dak_dz = ak.diff(dim="level")
    dbk_dz = bk.diff(dim="level")

    res = (
        2.0
        * etadot
        * ps
        * (dak_dz / ps + dbk_dz)
        / (dak_dz / surface_pressure_ref + dbk_dz)
    ).reduce(cumdiff, dim="level")

    return xr.DataArray(
        data=res,
        attrs=etadot.attrs,
        name="omega"
    )

def cumdiff(input_array: np.ndarray, axis: int)-> np.ndarray:
    """Computes the cumulative difference along a specified axis.
    This function is used to integrate the pressure differences
    over hybrid levels in the omega computation.

    Parameters
    ----------
    input_array : np.ndarray
        Input array.
    axis : int
        Axis along which to compute the cumulative difference.

    Returns
    -------
    np.ndarray
        Array with cumulative differences applied along the specified axis.
    """

    r = np.empty(np.shape(input_array))
    t = 0  # op = the ufunc being applied to A's  elements
    for i in range(np.shape(input_array)[axis]):
        t = np.take(input_array, i, axis) - t

        slices = []
        for dim in range(input_array.ndim):
            if dim == axis:
                slices.append(slice(i, i + 1))
            else:
                slices.append(slice(None))

        r[tuple(slices)] = np.expand_dims(t, axis=axis)
    return r
