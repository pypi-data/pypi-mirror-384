"""
Module defining input parameter mappings.

Reference: https://codes.ecmwf.int/grib/param-db/<param_id>
"""

ML_FIELDS = {
    "q": "133",  # Specific humidity
    "u": "131",  # Eastward component of the wind
    "v": "132",  # Northward component of the wind
    "t": "130",  # Temperature
}

ETADOT_FIELDS = {
    "etadot": "77",  # Vertical velocity
}

CONSTANT_FIELDS = {
    "z": "129",  # Geopotential height
    "lsm": "172",  # Land-sea mask
    "sdor": "160",  # Standard deviation of orography
}

SURFACE_FIELDS = {
    "sp": "134",  # Surface pressure
    "lsp": "142",  # Large-scale precipitation [m]
    "cp": "143",  # Convective precipitation [m]
    "sd": "141",  # Snow depth
    "tcc": "164",  # Total cloud cover
    "2d": "168",  # 2m dewpoint temperature
    "10u": "165",  # 10m eastward wind component
    "10v": "166",  # 10m northward wind component
    "2t": "167",  # 2m temperature [K]
    "ssr": "176",  # Surface net shortwave radiation [J/m²]
    "sshf": "146",  # Surface sensible heat flux [J/m²]
    "ewss": "180",  # Eastward turbulent surface stress [N/m²·s]
    "nsss": "181",  # Northward turbulent surface stress [N/m²·s]
}
