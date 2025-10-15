from pydantic import BaseModel

from .common_models import Vec3


class WindProbeData(BaseModel):
    """
    Represents data from a wind probe.
    """

    timestamp_s: float
    wind_velocity_mps_probe_ref: Vec3  # Raw data
    wind_velocity_mps_windshaper_ref: Vec3
    wind_velocity_mps_windshaper_ref_corrected: Vec3  # Corrected for probe movement

    temperature_celcius: float
    atmospheric_pressure_hpascal: float
    static_pressure_pascal: float
