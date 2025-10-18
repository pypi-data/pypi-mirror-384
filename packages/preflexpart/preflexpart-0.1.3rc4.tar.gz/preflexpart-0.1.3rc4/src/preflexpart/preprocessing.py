"""Preprocessing for FLEXPART."""

import logging

import numpy as np
import xarray as xr

from preflexpart.input_fields import CONSTANT_FIELDS
from preflexpart.operators.time import time_rate
from preflexpart.operators.vertical import omega_slope

logger = logging.getLogger(__name__)


def _has_step(da: xr.DataArray) -> bool:
    return "step" in da.dims


def preprocess(ds: dict[str, xr.DataArray]) -> dict[str, xr.DataArray]:
    """
    Preprocess the input fields for FLEXPART.

    This function:
      - De-accumulates precipitation to mm/h.
      - De-accumulates radiation/flux/stress to per-second.
      - Computes omega slope for vertical velocity.
      - Copies constant fields as-is.
      - For common vars, keeps steps from index 1 onward (since rates use diffs).

    Parameters
    ----------
    ds : dict[str, xarray.DataArray]
        Mapping shortName to DataArray.

    Returns
    -------
    dict[str, xarray.DataArray]
        Processed fields.
    """
    out: dict[str, xr.DataArray] = {}

    # ---- Precipitation (m to mm h-1) ----
    for var in ("cp", "lsp"):
        if var not in ds:
            continue
        if not _has_step(ds[var]):
            logger.warning("%s has no 'step' dim; skipping de-accumulation", var)
            continue

        units = ds[var].attrs.get("units")
        if units != "m":
            logger.warning("Unexpected units for %s: %r (expected 'm')", var, units)

        with xr.set_options(keep_attrs=True):
            rate = time_rate(ds[var], np.timedelta64(1, "h")) * 1000.0
            rate.attrs["units"] = "mm h-1"
            out[var] = rate

    # ---- Radiation / Heat Flux / Surface Stress (per second) ----
    for var in ("ssr", "sshf", "ewss", "nsss"):
        if var not in ds:
            continue
        if not _has_step(ds[var]):
            logger.warning("%s has no 'step' dim; skipping de-accumulation", var)
            continue
        out[var] = time_rate(ds[var], np.timedelta64(1, "s"))

    # ---- Omega slope  ----
    needed = ("sp", "etadot", "ak", "bk")
    if all(k in ds for k in needed):
        try:
            omg = omega_slope(ds["sp"], ds["etadot"], ds["ak"], ds["bk"])
            # levels 40..137 (0-based slice 39:137); drop first step if present
            if "level" in omg.dims:
                omg = omg.isel(level=slice(39, 137))
            if "step" in omg.dims:
                omg = omg.isel(step=slice(1, None))
            out["omega"] = omg
        except Exception as exc:
            logger.error("Failed to compute omega: %s", exc)
    else:
        missing = [k for k in needed if k not in ds]
        logger.warning("Skipping omega: missing %s", ", ".join(missing))

    # ---- Constant fields ----
    for name in CONSTANT_FIELDS:
        if name in ds:
            out[name] = ds[name]

    # ---- Keep common vars (drop first step if present) ----
    keep = ("q", "u", "v", "t", "sp", "sd", "tcc", "2d", "10u", "10v", "2t")
    for var in keep:
        if var not in ds:
            continue
        out[var] = ds[var].isel(step=slice(1, None)) if _has_step(ds[var]) else ds[var]

    return out
