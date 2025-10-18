"""Load GRIB files from disk into (dict[str, xr.DataArray])."""

import logging
from pathlib import Path

import earthkit.data as ekd
import earthkit.data.readers.grib.file as grib_file
import earthkit.data.readers.grib.index as grib_index
import numpy as np
import xarray as xr

from preflexpart.input_fields import (CONSTANT_FIELDS, ETADOT_FIELDS,
                                      ML_FIELDS, SURFACE_FIELDS)

logger = logging.getLogger(__name__)

_ALLOWED = (
    set(ML_FIELDS.keys())
    | set(ETADOT_FIELDS.keys())
    | set(SURFACE_FIELDS.keys())
    | set(CONSTANT_FIELDS.keys())
)

# ------------------------- helpers ------------------------- #

def _to_xarray(
    grib_obj: grib_index.GribMultiFieldList | grib_file.GRIBReader
) -> list[xr.Dataset]:
    """
    Convert an Earthkit GRIB object → list[xr.Dataset].

    Notes
    -----
    - ``grib_obj`` is a GRIBReader (one file) or GribMultiFieldList (many files).
    - ``split_dims='param'`` ensures one Dataset per GRIB parameter,
      avoiding grid-mismatch errors (GRIB1/GRIB2/surface/ml).
    - ``profile='grib'`` applies Earthkit’s GRIB profile and other GRIB-specific settings.
      See: https://earthkit-data.readthedocs.io/en/latest/guide/xarray/grib_profile.html#profiles-grib
    """
    datasets = grib_obj.to_xarray(profile="grib", split_dims="param")

    if isinstance(datasets, xr.Dataset):
        return [datasets]
    return list(datasets)


def _attach_hybrid_coeffs_from_pv(data_dict: dict[str, xr.DataArray]) -> None:
    """
    Attach ECMWF hybrid vertical coordinate coefficients ('ak', 'bk') from GRIB 'pv' metadata.

    In the IFS model, pressure at level η is p(η) = A(η) + B(η)*ps, where A=ak and B=bk.
    """
    # Try likely ML variables first, then any ML field you defined
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

def _list_to_dict(ds_lists: list[xr.Dataset]) -> dict[str, xr.DataArray]:
    """
    Flatten a list of single-variable xarray.Datasets into {name: DataArray}.
    Only keep variables we know about (_ALLOWED). Also attaches hybrid 'ak'/'bk' if available.

    Contract:
      - Each element of ds_lists MUST be an xr.Dataset with exactly one data_var.
      - Variable names must be in the allowed set; others are skipped with a warning.
    """
    out: dict[str, xr.DataArray] = {}

    for i, ds in enumerate(ds_lists):
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
            logger.error(
                "Dataset %d has %d data_vars but exactly 1 is expected: %s",
                i, nvars, list(ds.data_vars)
            )
            raise ValueError(f"Expected single-var Dataset at index {i}, got {nvars}")

        # Extract the single var
        name = next(iter(ds.data_vars))
        if name not in _ALLOWED:
            logger.warning("Dataset %d variable %r not in allowed set; skipping.", i, name)
            continue

        if name in out:
            logger.warning("Duplicate variable %r at index %d; replacing previous value.", name, i)

        out[name] = ds[name]

    _attach_hybrid_coeffs_from_pv(out)
    return out

# ------------------------- public API ------------------------- #

def load_grib(path: str | Path | list[str | Path]) -> dict[str, xr.DataArray]:
    """
    Load GRIB messages into memory and return {shortName: DataArray}.

    Parameters
    ----------
    path : str | Path | list[str | Path]
        - A directory containing GRIB files, or
        - A single GRIB file, or
        - A **list** of GRIB file paths (e.g., ["test.grib", "test4.grib"]).

    Returns
    -------
    dict[str, xarray.DataArray]
        Mapping shortName -> DataArray (plus 'ak'/'bk' if derivable).
    """
    try:
        # Case 1: explicit list of files
        if isinstance(path, list):
            files = [str(Path(p)) for p in path]
            if not files:
                logger.error("Empty file list provided to load_grib().")
                return {}
            missing = [f for f in files if not Path(f).exists()]
            if missing:
                logger.warning("Some files do not exist and will be skipped: %s", missing)
                files = [f for f in files if f not in missing]
            if not files:
                logger.error("No existing files left to read after filtering missing paths.")
                return {}
            source_arg = files

        # Case 2: directory or single file
        else:
            p = Path(path)  # type: ignore[arg-type]
            if not p.exists():
                logger.error("Path does not exist: %s", p)
                return {}
            source_arg = str(p)

        # Load with Earthkit
        grib_obj = ekd.from_source("file", source_arg)

        # Convert to list of xarray datasets (one per GRIB parameter)
        datasets = _to_xarray(grib_obj)

        # Convert list of datasets → {name: DataArray}
        field_dict = _list_to_dict(datasets)

        if not field_dict:
            logger.warning("No known variables found in %s", source_arg)

        return field_dict

    except Exception as e:
        logger.error("Failed to load GRIB(s) from %r: %s", path, e)
        return {}
