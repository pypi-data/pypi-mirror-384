"""
Write FLEXPART-ready GRIB2 files.

FLEXPART expects its meteorological inputs in GRIB2 format, one file per forecast
step (e.g., dispfYYYYMMDDHH.grib). This module takes a mapping of
``{shortName: xarray.DataArray}`` and writes each forecast step to GRIB2.

All GRIB1 messages are converted to GRIB2 by overriding their metadata based on
a GRIB2 Template 4.0 (instantaneous forecast). The main rules are:

1) GRIB2 fields not processed (q, u, v, t): kept unchanged.
2) GRIB1 fields not processed (10u, 10v, 2t, 2d, sp, tcc, sd, lsm, z, sdor):
   converted to GRIB2 with the correct vertical definition.
3) Processed fields (cp, lsp, ssr, sshf, ewss, nsss): written as 1-hour
   accumulations (PDT 8)
4) Omega/w: instantaneous (PDT 0) on hybrid model level K (Pa s⁻¹) with
   `shortName="w"`
"""
import logging
import tempfile
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd
import xarray as xr

from preflexpart.input_fields import CONSTANT_FIELDS

logger = logging.getLogger(__name__)

# Short names written as 1-hour accumulations (PDT 8)
ACCUM_SHORTNAMES: set[str] = {"lsp", "sshf", "ewss", "nsss", "cp", "ssr"}


# =============================== time helpers =============================== #

def _parse_reference_time(da: xr.DataArray) -> pd.Timestamp | None:
    """Extract cycle (reference) time from GRIB metadata as UTC pandas Timestamp."""
    md: Dict[str, Any] = _meta_dict(da)
    date = md.get("dataDate") or md.get("date")
    time = md.get("dataTime") or md.get("time")
    if date is None or time is None:
        return None
    time_str = str(int(time)).zfill(4)  # HHMM
    try:
        return pd.to_datetime(f"{int(date)}{time_str}", format="%Y%m%d%H%M", utc=True)
    except Exception:
        return None


def _to_minutes(step_val: object) -> int:
    """
    Convert a 'step' value to whole minutes.

    Accepts numpy/pandas timedeltas, ints (treated as hours), or strings ("3h").
    """
    if isinstance(step_val, np.timedelta64):
        return int(pd.to_timedelta(step_val).total_seconds() // 60)
    if isinstance(step_val, pd.Timedelta):
        return int(step_val.total_seconds() // 60)
    if isinstance(step_val, (int, np.integer)):  # type: ignore[arg-type]
        return int(step_val) * 60
    if isinstance(step_val, str):
        return int(pd.to_timedelta(step_val).total_seconds() // 60)
    return int(pd.to_timedelta(step_val).total_seconds() // 60)  # may raise


# ============================= metadata helpers ============================= #

def _meta_handle(da: xr.DataArray) -> Any:
    """Return the earthkit metadata *handle* if available; else None."""
    ek = getattr(da, "earthkit", None)
    return getattr(ek, "metadata", None)


def _meta_dict(da: xr.DataArray) -> dict[str, Any]:
    """
    Return a plain metadata dict from the earthkit accessor if available,
    otherwise fall back to attrs["_earthkit"]["metadata"] (tests) or {}.
    """
    mdh: Any = _meta_handle(da)

    # Case A: mdh is already a dict-like mapping
    if isinstance(mdh, dict):
        return mdh

    # Case B: mdh is a handle-like object with .get / iterable of pairs
    if mdh is not None:
        try:
            return dict(mdh)
        except Exception:
            if hasattr(mdh, "get"):
                out: dict[str, Any] = {}
                for k in (
                    "dataDate",
                    "dataTime",
                    "editionNumber",
                    "productDefinitionTemplateNumber",
                    "shortName",
                    "level",
                ):
                    try:
                        v = mdh.get(k)  # type: ignore[call-arg]
                    except Exception:
                        v = None
                    if v is not None:
                        out[k] = v
                if out:
                    return out

    # Case C: tests may stash a metadata dict under attrs["_earthkit"]["metadata"]
    ek_attr: Any = da.attrs.get("_earthkit")
    if isinstance(ek_attr, dict) and isinstance(ek_attr.get("metadata"), dict):
        return ek_attr["metadata"]  # type: ignore[return-value]

    return {}


def _pick_grib2_template_metadata(fields: dict[str, xr.DataArray]) -> Any:
    """
    Return a GRIB-2 Template 4.0 metadata HANDLE to use as the override base.
    """
    for da in fields.values():
        mdh: Any = _meta_handle(da)
        if mdh is None:
            continue
        try:
            if mdh.get("editionNumber") == 2 and mdh.get("productDefinitionTemplateNumber") == 0:
                if hasattr(mdh, "override"):
                    return mdh
        except Exception:
            continue
    raise RuntimeError("No GRIB-2 Template 4.0 message handle found (edition=2 & PDTN=0).")


def _unset_surface_scaled_values(md: Any) -> Any:
    """
    Ensure GRIB2 surface validity.

    For surface fields (typeOfFirstFixedSurface=1), the scale factor/value
    keys must be *missing*, not set to 0 or 255. This helper unsets them so
    ecCodes validity checks pass when converting from hybrid-level templates.
    """
    h = getattr(md, "_handle", None)
    if h is None:
        return md
    # earthkit message handle exposes set_missing(name)
    for k in ("scaleFactorOfFirstFixedSurface", "scaledValueOfFirstFixedSurface"):
        try:
            h.set_missing(k)
        except Exception:
            # Best-effort; if we can't unset, validity checks may fail.
            pass
    return md


def _override_time(md: Any, *, step_h: int, window_h: int, short_name: str | None) -> Any:
    """
    Apply forecast time keys in HOURS.

    If window_h > 0 → PDT 8 (statistical interval, accumulation).
    """
    start_h = max(0, step_h - window_h)

    kv: dict[str, Any] = dict(
        indicatorOfUnitOfTimeRange=1,   # hours
        stepUnits=1,                    # hours
        forecastTime=step_h,            # valid-at time
        shortName=short_name,
        stepRange=str(step_h) if window_h == 0 else f"{start_h}-{step_h}",
    )
    if window_h > 0:
        kv.update(
            productDefinitionTemplateNumber=8,  # PDT 8 = statistical interval
            typeOfStatisticalProcessing=1,      # accumulation/sum over interval
            indicatorOfUnitForTimeRange=1,      # hours
            lengthOfTimeRange=window_h,         # 1 hour for our list
            startStep=start_h,
            endStep=step_h,
        )
    else:
        kv.update(productDefinitionTemplateNumber=0)  # instantaneous

    return md.override(**kv)


def _apply_vertical_overrides(md: Any, shortname: str) -> Any:
    """
    Apply vertical level/type overrides for GRIB1→GRIB2 conversions when the
    field did not undergo any additional processing.
    """
    # 2 m fields
    if shortname in ("2t", "2d"):
        return md.override(
            typeOfFirstFixedSurface=103,  # heightAboveGround
            scaleFactorOfFirstFixedSurface=0,
            scaledValueOfFirstFixedSurface=2,
            typeOfSecondFixedSurface=255,
        )

    # 10 m winds
    if shortname in ("10u", "10v"):
        return md.override(
            typeOfFirstFixedSurface=103,
            scaleFactorOfFirstFixedSurface=0,
            scaledValueOfFirstFixedSurface=10,
            typeOfSecondFixedSurface=255,
        )

    # Surface pressure, land-sea mask
    if shortname in ("sp", "lsm"):
        md = md.override(
            typeOfFirstFixedSurface=1,    # surface
            typeOfSecondFixedSurface=255,
        )
        return _unset_surface_scaled_values(md)

    # Sub-grid orography standard deviation (sdor)
    if shortname == "sdor":
        return md.override(
            typeOfFirstFixedSurface=105,  # hybrid
            scaleFactorOfFirstFixedSurface=0,
            scaledValueOfFirstFixedSurface=1,
            typeOfSecondFixedSurface=255,
        )

    # Geopotential on model level 1
    if shortname == "z":
        return md.override(
            typeOfFirstFixedSurface=105,
            scaleFactorOfFirstFixedSurface=0,
            scaledValueOfFirstFixedSurface=1,
            typeOfSecondFixedSurface=255,
        )

    # Total cloud cover: layer from surface (1) to nominal TOA (8)
    if shortname == "tcc":
        md = md.override(
            typeOfFirstFixedSurface=1,    # surface
            typeOfSecondFixedSurface=8,   # nominal top of atmosphere
        )
        return _unset_surface_scaled_values(md)

    # Snow depth: hybrid level 1
    if shortname == "sd":
        return md.override(
            typeOfFirstFixedSurface=105,
            scaleFactorOfFirstFixedSurface=0,
            scaledValueOfFirstFixedSurface=1,
            typeOfSecondFixedSurface=255,
        )

    # default: leave as-is
    return md


def _filename_stem_for_step(
    fields_step: dict[str, xr.DataArray],
    step_val: object,
) -> str:
    """
    Build filename stem like 'dispfYYYYMMDDHH' from reference_time + step.
    """
    if "u" in fields_step:
        ref_da = fields_step["u"]
    else:
        ref_da = next(iter(fields_step.values()))
    ref_time = _parse_reference_time(ref_da)
    if ref_time is None:
        raise RuntimeError("Cannot determine reference time from GRIB metadata.")
    step_min = _to_minutes(step_val)
    valid = ref_time + pd.to_timedelta(step_min, unit="m")
    return f"dispf{valid.strftime('%Y%m%d%H')}"


# ================================ public API ================================ #

def write_grib(
    fields: dict[str, xr.DataArray],
    output_dir: str | Path = "./",
    *,
    suffix: str = ".grib",
) -> list[Path]:
    """
    Write one GRIB file per forecast step by overriding message metadata.

    Parameters
    ----------
    fields
        Mapping {shortName: DataArray}. Non-constant fields must have a 'step'
        coordinate (timedelta-like) and carry GRIB metadata at
        DataArray.earthkit.metadata.
    output_dir
        Directory to write files (created if missing).
    suffix
        File extension/suffix (default: ".grib"). Use "" to omit.

    Returns
    -------
    list[pathlib.Path]
        Paths written (one per step).
    """
    if not fields:
        raise ValueError("fields is empty.")

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Baseline: GRIB2, PDT 4.0 message used as template for overrides.
    ref_md: Any = _pick_grib2_template_metadata(fields)

    # Steps from a representative field
    rep = fields["u"] if "u" in fields else next(iter(fields.values()))
    if "step" not in rep.coords:
        raise ValueError("Expected a 'step' coordinate on at least one field.")
    steps = rep.coords["step"].values

    written: list[Path] = []

    for step in steps:
        # Build per-step dict
        fields_step: dict[str, xr.DataArray] = {}
        for name, da in fields.items():
            if name in CONSTANT_FIELDS:
                fields_step[name] = da
            else:
                if "step" not in da.coords:
                    raise ValueError(f"Field '{name}' is missing 'step' coord.")
                fields_step[name] = da.sel(step=step)

        stem = _filename_stem_for_step(fields_step, step)
        out_path = out_dir / f"{stem}{suffix}"
        logger.info("Writing GRIB: %s", out_path)

        # Create/empty file
        with open(out_path, "wb"):
            pass

        step_min = _to_minutes(step)
        step_h = int(step_min // 60)

        for name, field in fields_step.items():
            # Skip empty
            if field.isnull().all():
                logger.info("Ignoring '%s' - only NaN values.", name)
                continue

            meta: Dict[str, Any] = _meta_dict(field)
            shortname = (meta.get("shortName") or name)

            # Start from template & set shortName
            md: Any = ref_md.override(shortName=shortname)

            # Determine if this message is an hourly accumulation
            window_h = 1 if shortname in ACCUM_SHORTNAMES else 0
            md = _override_time(md, step_h=step_h, window_h=window_h, short_name=shortname)

            # ---------------- processed accumulations (PDT 8) ----------------
            if shortname in ACCUM_SHORTNAMES:
                # Keep only shortName + surface level (no triple), then unset scale keys
                md = md.override(
                    shortName=shortname,
                    typeOfFirstFixedSurface=1,
                    typeOfSecondFixedSurface=255,
                )
                md = _unset_surface_scaled_values(md)

            # ---------------- omega / w (instantaneous, hybrid level K) ------
            elif name in {"omega", "w"} or shortname in {"omega", "w"}:
                lvl = int(meta.get("level", 1))
                md = md.override(
                    productDefinitionTemplateNumber=0,   # instantaneous
                    indicatorOfUnitOfTimeRange=1,        # hours
                    stepUnits=1,
                    forecastTime=step_h,
                    stepRange=str(step_h),

                    typeOfFirstFixedSurface=105,         # hybrid level
                    scaleFactorOfFirstFixedSurface=0,
                    scaledValueOfFirstFixedSurface=lvl,
                    typeOfSecondFixedSurface=255,

                    shortName="w",                        # canonical omega/w short name
                )

            # ------------- unprocessed, GRIB1→GRIB2 vertical fixes ----------
            else:
                md = _apply_vertical_overrides(md, shortname)

            # Inject raw message buffer and append
            # md._handle is an ecCodes handle (opaque to typing)
            field.attrs["_earthkit"] = {"message": md._handle.get_buffer()}  # type: ignore[attr-defined]

            with tempfile.NamedTemporaryFile(suffix="") as tmp:
                field.earthkit.to_grib(tmp.name)  # type: ignore[attr-defined]
                with open(tmp.name, "rb") as fh_in, open(out_path, "ab") as fh_out:
                    fh_out.write(fh_in.read())

        written.append(out_path)
        logger.info("Saved: %s", out_path)

    return written
