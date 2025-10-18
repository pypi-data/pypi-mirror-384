"""MARS-backed IFS retrieval (in-memory, no files).

Downloads IFS HRES fields directly from the ECMWF MARS archive using
earthkit-data’s ``"mars"`` source, and returns them in memory as
``{shortName: xarray.DataArray}``. No temporary GRIB files are written.

What it fetches
---------------
- Model-level variables (levels 40..max_level) and etadot (1..max_level)
- Surface fields and static constants
- Hybrid coefficients ``ak``/``bk`` derived from GRIB ``pv`` metadata when present
"""
import logging

import earthkit.data as ekd
import earthkit.data.readers.grib.file as grib_file
import numpy as np
import xarray as xr

from preflexpart.input_fields import (CONSTANT_FIELDS, ETADOT_FIELDS,
                                      ML_FIELDS, SURFACE_FIELDS)

logger = logging.getLogger(__name__)

# ------------------------- helpers ------------------------- #

def _slash(ids: list[str]) -> str:
    return "/".join(ids)

def _to_xarray(grib_obj: grib_file.GRIBReader) -> list[xr.Dataset]:
    """
    Convert a MARS GRIBReader → list[xr.Dataset].

    Notes
    -----
    - MARS returns one virtual GRIB file per request → GRIBReader.
    - split_dims='param' produces one Dataset per parameter and avoids grid mismatches.
    - profile='grib' preserves GRIB metadata (add_earthkit_attrs is implied).
    """
    datasets = grib_obj.to_xarray(profile="grib", split_dims="param")
    return datasets if isinstance(datasets, list) else [datasets]

def _attach_hybrid_coeffs_from_pv(data_dict: dict[str, xr.DataArray]) -> None:
    """
    Attach ECMWF hybrid vertical coordinate coefficients ('ak', 'bk') from GRIB 'pv' metadata.

    In the IFS model, pressure at level η is p(η) = A(η) + B(η)*ps, where A=ak and B=bk.
    """
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
        if not isinstance(ds, xr.Dataset):
            logger.warning("Entry %d is not an xarray.Dataset (type=%s): %r", i, type(ds), ds)
            continue

        nvars = len(ds.data_vars)
        if nvars == 0:
            logger.warning("Dataset %d has no data_vars. attrs=%s", i, ds.attrs)
            continue
        if nvars > 1:
            logger.error("Dataset %d has %d data_vars but exactly 1 is expected: %s",
                         i, nvars, list(ds.data_vars))
            raise ValueError(f"Expected single-var Dataset at index {i}, got {nvars}")

        name = next(iter(ds.data_vars))
        if name not in allowed:
            logger.warning("Dataset %d variable %r not in allowed set; skipping.", i, name)
            continue

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
    *,
    class_: str = "od",
    stream: str = "oper",
    expver: str = "1",
    area: list[float] = [65, -10, 35, 47],  # [N, W, S, E]
    grid: list[float] = [0.1, 0.1],
) -> dict[str, xr.DataArray]:
    """
    Retrieve IFS fields via MARS (earthkit-data) and return {name: DataArray}.

    Parameters
    ----------
    date : str
        Request date (YYYYMMDD or YYYY-MM-DD).
    time : str
        Forecast cycle time (HH or HHMM).
    step : str
        Forecast steps expression (e.g., "0/to/6/by/1").
        **Important:** At least two forecast steps are required, since
        de-accumulation (e.g. for precipitation/radiation) needs consecutive steps.
    max_level : int
        Highest model level to request (inclusive).
    class_, stream, expver : str
        MARS routing flags (default "od", "oper", "1").
    area : list[float]
        [North, West, South, East].
    grid : list[float]
        Target grid resolution applied to all requests (e.g., [0.1, 0.1]).

    Returns
    -------
    dict[str, xarray.DataArray]
        Mapping shortName → DataArray. Includes 'ak'/'bk' if available.
    """
    n_steps = _count_steps(step)
    if n_steps < 2:
        raise ValueError(
            f"Invalid step specification {step!r}: "
            "at least two forecast steps are required for de-accumulated variables."
        )

    # Param universes (string IDs as required by the request)
    ml_param_ids     = [str(v) for v in ML_FIELDS.values()]
    etadot_param_ids = [str(v) for v in ETADOT_FIELDS.values()]
    sfc_param_ids    = [str(v) for v in SURFACE_FIELDS.values()]
    cst_param_ids    = [str(v) for v in CONSTANT_FIELDS.values()]

    base = {
        "type": "fc",
        "class": class_,
        "stream": stream,
        "expver": expver,
        "date": date,
        "time": time,
        "area": area,
        "grid": grid,
    }

    ds_list: list[xr.Dataset] = []

    # --- ML (40..N)
    if ml_param_ids:
        req = {**base, "levtype": "ml", "levelist": f"40/to/{max_level}",
               "step": step, "param": _slash(ml_param_ids)}
        ds_list.extend(_to_xarray(ekd.from_source("mars", req)))

    # --- ETADOT (1..N)
    if etadot_param_ids:
        req = {**base, "levtype": "ml", "levelist": f"1/to/{max_level}",
               "step": step, "param": _slash(etadot_param_ids)}
        ds_list.extend(_to_xarray(ekd.from_source("mars", req)))

    # --- SFC
    if sfc_param_ids:
        req = {**base, "levtype": "sfc", "step": step, "param": _slash(sfc_param_ids)}
        ds_list.extend(_to_xarray(ekd.from_source("mars", req)))

    # --- Constants
    if cst_param_ids:
        req = {**base, "levtype": "sfc", "param": _slash(cst_param_ids)}
        ds_list.extend(_to_xarray(ekd.from_source("mars", req)))

    try:
        return _list_to_dict(ds_list)
    except Exception as e:
        logger.error("Error converting MARS data to xarray dict: %s", e)
        return {}
