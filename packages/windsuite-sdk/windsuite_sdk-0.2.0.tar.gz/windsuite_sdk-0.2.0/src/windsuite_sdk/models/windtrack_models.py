from pydantic import BaseModel

from .common_models import Quat, Vec3

tracked_object_name = str


class TrackingData(BaseModel):
    """
    Represents tracking data for a single object.

    - Position in meters in the world reference frame,
    - Orientation as a quaternion in the world reference frame,

    ! Special case for the windshaper itself that will have the same as it's his reference frame
    - Position in meters in the windshaper reference frame,
    - Orientation as a quaternion in the windshaper reference frame,

    - Velocity in meters per second,
    - Angular velocity in degrees per second.
    """

    timestamp: float

    position_meters_world_ref: Vec3
    rotation_world_ref: Quat

    position_meters_windshaper_ref: Vec3
    rotation_windshaper_ref: Quat

    velocity_mps_world_ref: Vec3
    angular_velocity_degps_world_ref: Vec3

    velocity_mps_windshaper_ref: Vec3
    angular_velocity_degps_windshaper_ref: Vec3


class TrackingDataDict(BaseModel):
    data: dict[tracked_object_name, TrackingData]
