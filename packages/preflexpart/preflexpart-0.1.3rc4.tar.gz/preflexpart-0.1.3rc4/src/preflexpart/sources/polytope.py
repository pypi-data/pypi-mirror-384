"""Polytope-backed IFS retrieval

This module retrieves IFS fields using earthkit-data's Polytope source,
which fetches data from the ECMWF MARS archive via the Polytope API,
and returns them in memory as a dict mapping variable names to
`xarray.DataArray`. No temporary GRIB files are written.

Note
------------
Some parameters must be requested from the "swiss-meteo" Polytope collection,
NOT the default "ecmwf-mars" collection. These were not available through the
MARS collection for our use-case, so we split the routing as follows:
- Core winds/temperature on model levels and etadot come from `swiss-meteo`
- Everything else (other ML, SFC, constants) goes via `ecmwf-mars`
"""
import logging

import earthkit.data as ekd
import earthkit.data.readers.grib.file as grib_file
import numpy as np
import xarray as xr

from preflexpart.input_fields import (CONSTANT_FIELDS, ETADOT_FIELDS,
                                      ML_FIELDS, SURFACE_FIELDS)

logger = logging.getLogger(__name__)

# Parameters fetched from the "swiss-meteo" collection (see module docstring).
_SWISS_ML_IDS = {"130", "131", "132"}  # t/u/v on model levels [40, 137]
_SWISS_ETADOT = {"77"}                 # etadot on model levels [1, 137]


# ------------------------- helpers ------------------------- #

def _slash(ids: list[str]) -> str:
    return "/".join(ids)

def _to_xarray(grib_obj: grib_file.GRIBReader) -> list[xr.Dataset]:
    """
    Convert an Earthkit GRIBReader → list[xr.Dataset].

    Notes
    -----
    - Polytope retrievals return a single GRIBReader (one virtual GRIB file).
    - ``split_dims='param'`` ensures one Dataset per GRIB parameter,
      avoiding grid-mismatch errors between different grids or levels.
    - ``profile='grib'`` enables Earthkit’s GRIB profile, which already
      sets ``add_earthkit_attrs=True``.
      See: https://earthkit-data.readthedocs.io/en/latest/guide/xarray/grib_profile.html#profiles-grib
    """
    datasets = grib_obj.to_xarray(profile="grib", split_dims="param")
    return datasets if isinstance(datasets, list) else [datasets]


def _attach_hybrid_coeffs_from_pv(data_dict: dict[str, xr.DataArray]) -> None:
    """
    Attach ECMWF hybrid vertical coordinate coefficients ('ak', 'bk') from GRIB 'pv' metadata.

    In the IFS model, pressure at level η is p(η) = A(η) + B(η)*ps, where A=ak and B=bk.
    """
    # try likely ML variables first, then any ML field you defined
    for name in ("q", "u", "t", "v", *ML_FIELDS.keys()):
        if name in data_dict:
            da = data_dict[name]
            pv = da.earthkit.metadata.get("pv") if hasattr(da, "_earthkit") else None
            if pv is None:
                continue
            pv = np.asarray(pv)
            n = pv.size
            if n > 0 and n % 2 == 0:
                i = n // 2
                data_dict["ak"] = xr.DataArray(pv[:i], dims=("level",))
                data_dict["bk"] = xr.DataArray(pv[i:], dims=("level",))
                return

def _list_to_dict(ds_list: list[xr.Dataset]) -> dict[str, xr.DataArray]:
    """
    Flatten a list of single-variable xarray.Datasets into {name: DataArray}.
    Also attaches hybrid coefficients 'ak'/'bk' from GRIB 'pv' metadata if available.
    """
    allowed = set(ML_FIELDS) | set(ETADOT_FIELDS) | set(CONSTANT_FIELDS) | set(SURFACE_FIELDS)
    out: dict[str, xr.DataArray] = {}

    for i, ds in enumerate(ds_list):
        # Type check
        if not isinstance(ds, xr.Dataset):
            logger.warning("Entry %d is not an xarray.Dataset (type=%s): %r", i, type(ds), ds)
            continue

        # Must have exactly one variable
        nvars = len(ds.data_vars)
        if nvars == 0:
            logger.warning("Dataset %d has no data_vars. attrs=%s", i, ds.attrs)
            continue
        if nvars > 1:
            logger.error("Dataset %d has %d data_vars but exactly 1 is expected: %s",
                         i, nvars, list(ds.data_vars))
            # Choose: either skip, or raise to fail fast. Here we fail fast:
            raise ValueError(f"Expected single-var Dataset at index {i}, got {nvars}")

        # Extract the single var
        name = next(iter(ds.data_vars))
        if name not in allowed:
            logger.warning("Dataset %d variable %r not in allowed set; skipping.", i, name)
            continue

        # Handle duplicates deterministically (last one wins) & warn
        if name in out:
            logger.warning("Duplicate variable %r at index %d; replacing previous value.", name, i)

        out[name] = ds[name]

    _attach_hybrid_coeffs_from_pv(out)

    return out

def _count_steps(step: str) -> int:
    """Parser for ECMWF step expressions like '0/to/6/by/3'."""
    if "/to/" in step and "/by/" in step:
        start, rest = step.split("/to/")
        end, stride = rest.split("/by/")
        return (int(end) - int(start)) // int(stride) + 1
    try:
        return len(step.split("/"))
    except Exception:
        return 0


# ------------------------- public API ------------------------- #

def retrieve_ifs(
    date: str,
    time: str,
    step: str,
    max_level: int,
) -> dict[str, xr.DataArray]:
    """
    Retrieve IFS fields via Polytope and return {name: DataArray} in memory.

    Parameters
    ----------
    date : str
        Request date (YYYYMMDD or YYYY-MM-DD).
    time : str
        Forecast cycle time (HH).
    step : str
        Forecast steps expression understood by the backend (e.g. "0/to/6/by/1").
        **Important:** At least two forecast steps are required, since
        de-accumulation (e.g. for precipitation/radiation) needs consecutive steps.
    max_level : int
        Highest model level to request (inclusive).

    Returns
    -------
    dict[str, xarray.DataArray]
        A mapping from shortName to DataArray. Hybrid coefficients 'ak'/'bk' are
        included in the dictionnary.
    """

    n_steps = _count_steps(step)
    if n_steps < 2:
        raise ValueError(
            f"Invalid step specification {step!r}: "
            "at least two forecast steps are required for de-accumulated variables."
        )

    # Param universes (string IDs as required by the request)
    ml_ids_all     = [str(v) for v in ML_FIELDS.values()]
    etadot_ids_all = [str(v) for v in ETADOT_FIELDS.values()]
    sfc_ids_all    = [str(v) for v in SURFACE_FIELDS.values()]
    cst_ids_all    = [str(v) for v in CONSTANT_FIELDS.values()]

    # swiss buckets (special collection; see note at top)
    swiss_ml_ids = sorted(set(ml_ids_all) & _SWISS_ML_IDS)
    swiss_eta    = sorted(set(etadot_ids_all) & _SWISS_ETADOT)

    # mars buckets = everything not handled by swiss
    ml_ids_mars  = [p for p in ml_ids_all if p not in (_SWISS_ML_IDS | _SWISS_ETADOT)]
    sfc_ids_mars = [p for p in sfc_ids_all if p not in _SWISS_ML_IDS]
    cst_ids_mars = [p for p in cst_ids_all if p not in _SWISS_ML_IDS]

    base_swiss = {
        "type": "fc",
        "class": "od",
        "stream": "oper",
        "expver": "9666",
        "database": "fdbtest",
        "domain": "g",
        "date": date,
        "time": time,
    }
    base_mars = {
        "type": "fc",
        "class": "od",
        "stream": "oper",
        "expver": "1",
        "domain": "g",
        "date": date,
        "time": time,
    }

    ds_list: list[xr.Dataset] = []

    # --- SWISS: ML (t/u/v) with 40..N (special collection)
    if swiss_ml_ids:
        req = {**base_swiss, "levtype": "ml", "levelist": f"40/to/{max_level}",
               "step": step, "param": _slash(swiss_ml_ids)}
        ds_list.extend(_to_xarray(
            ekd.from_source("polytope", "swiss-meteo", req, stream=False)
        ))

    # --- SWISS: etadot with 1..N (special collection; separate request)
    if swiss_eta:
        req = {**base_swiss, "levtype": "ml", "levelist": f"1/to/{max_level}",
               "step": step, "param": "77"}
        ds_list.extend(_to_xarray(
            ekd.from_source("polytope", "swiss-meteo", req, stream=False)
        ))

    # --- MARS gateway: remaining ML (q)
    if ml_ids_mars:
        req = {**base_mars, "levtype": "ml", "levelist": f"40/to/{max_level}",
               "step": step, "param": _slash(ml_ids_mars)}
        ds_list.extend(_to_xarray(
            ekd.from_source("polytope", "ecmwf-mars", req, stream=False)
        ))

    # --- MARS gateway: SFC
    if sfc_ids_mars:
        req = {**base_mars, "levtype": "sfc", "step": step, "param": _slash(sfc_ids_mars)}
        ds_list.extend(_to_xarray(
            ekd.from_source("polytope", "ecmwf-mars", req, stream=False)
        ))

    # --- MARS gateway: constants
    if cst_ids_mars:
        req = {**base_mars, "levtype": "sfc", "param": _slash(cst_ids_mars)}
        ds_list.extend(_to_xarray(
            ekd.from_source("polytope", "ecmwf-mars", req, stream=False)
        ))

    try:
        return _list_to_dict(ds_list)
    except Exception as e:
        logger.error("Error converting Polytope data to xarray dict: %s", e)
        return {}
