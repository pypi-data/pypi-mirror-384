"""PDAL dimension names and data types."""

from __future__ import annotations

from enum import Enum
from typing import Final


class DataType(str, Enum):
    """PDAL dimension data types."""

    # Signed integers
    INT8 = "int8"
    INT16 = "int16"
    INT32 = "int32"
    INT64 = "int64"

    # Unsigned integers
    UINT8 = "uint8"
    UINT16 = "uint16"
    UINT32 = "uint32"
    UINT64 = "uint64"

    # Floating point
    FLOAT = "float"
    FLOAT32 = "float32"
    DOUBLE = "double"
    FLOAT64 = "float64"


class Dimension:
    """PDAL standard dimension names with default types."""

    # Geometry and position
    X: Final[str] = "X"
    Y: Final[str] = "Y"
    Z: Final[str] = "Z"
    INTENSITY: Final[str] = "Intensity"
    GPS_TIME: Final[str] = "GpsTime"
    RETURN_NUMBER: Final[str] = "ReturnNumber"
    NUMBER_OF_RETURNS: Final[str] = "NumberOfReturns"
    POINT_SOURCE_ID: Final[str] = "PointSourceId"
    POINT_ID: Final[str] = "PointId"

    # Color and imagery
    RED: Final[str] = "Red"
    GREEN: Final[str] = "Green"
    BLUE: Final[str] = "Blue"
    INFRARED: Final[str] = "Infrared"
    ALPHA: Final[str] = "Alpha"

    # Classification and flags
    CLASSIFICATION: Final[str] = "Classification"
    SYNTHETIC: Final[str] = "Synthetic"
    KEY_POINT: Final[str] = "KeyPoint"
    WITHHELD: Final[str] = "Withheld"
    OVERLAP: Final[str] = "Overlap"
    SCAN_ANGLE_RANK: Final[str] = "ScanAngleRank"
    SCAN_DIRECTION_FLAG: Final[str] = "ScanDirectionFlag"
    EDGE_OF_FLIGHT_LINE: Final[str] = "EdgeOfFlightLine"
    USER_DATA: Final[str] = "UserData"

    # Neighborhood and geometry metrics
    CURVATURE: Final[str] = "Curvature"
    EIGENVALUE0: Final[str] = "Eigenvalue0"
    EIGENVALUE1: Final[str] = "Eigenvalue1"
    EIGENVALUE2: Final[str] = "Eigenvalue2"
    EIGEN_ENTROPY: Final[str] = "Eigenentropy"
    PLANARITY: Final[str] = "Planarity"
    LINEARITY: Final[str] = "Linearity"
    SCATTERING: Final[str] = "Scattering"
    OMNIVARIANCE: Final[str] = "Omnivariance"
    ANISOTROPY: Final[str] = "Anisotropy"
    SURFACE_VARIATION: Final[str] = "SurfaceVariation"

    # Normal vectors
    NORMAL_X: Final[str] = "NormalX"
    NORMAL_Y: Final[str] = "NormalY"
    NORMAL_Z: Final[str] = "NormalZ"

    # Orientation and pose
    PITCH: Final[str] = "Pitch"
    ROLL: Final[str] = "Roll"
    HEADING: Final[str] = "Heading"
    YAW: Final[str] = "Yaw"
    X_BODY_ACCEL: Final[str] = "XBodyAccel"
    Y_BODY_ACCEL: Final[str] = "YBodyAccel"
    Z_BODY_ACCEL: Final[str] = "ZBodyAccel"
    X_BODY_ANG_RATE: Final[str] = "XBodyAngRate"
    Y_BODY_ANG_RATE: Final[str] = "YBodyAngRate"
    Z_BODY_ANG_RATE: Final[str] = "ZBodyAngRate"

    # Return and pulse characteristics
    PULSE_WIDTH: Final[str] = "PulseWidth"
    REFLECTED_PULSE: Final[str] = "ReflectedPulse"
    PASSIVE_SIGNAL: Final[str] = "PassiveSignal"
    ECHO_NORM: Final[str] = "EchoNorm"
    ECHO_POS: Final[str] = "EchoPos"
    ECHO_RANGE: Final[str] = "EchoRange"

    # Height metrics
    HEIGHT_ABOVE_GROUND: Final[str] = "HeightAboveGround"
    HAG: Final[str] = "HAG"

    # Additional LAS 1.4 fields
    SCAN_CHANNEL: Final[str] = "ScanChannel"
    CLASS_FLAGS: Final[str] = "ClassFlags"
    NIR: Final[str] = "NIR"

    # Waveform
    WAVEFORM_PACKET_DESCRIPTOR_INDEX: Final[str] = "WaveformPacketDescriptorIndex"
    WAVEFORM_BYTE_OFFSET: Final[str] = "WaveformByteOffset"
    WAVEFORM_PACKET_SIZE: Final[str] = "WaveformPacketSize"
    WAVEFORM_RETURN_POINT_LOCATION: Final[str] = "WaveformReturnPointLocation"
    WAVEFORM_X_T: Final[str] = "WaveformXt"
    WAVEFORM_Y_T: Final[str] = "WaveformYt"
    WAVEFORM_Z_T: Final[str] = "WaveformZt"


# Dimension default types mapping
DIMENSION_TYPES: Final[dict[str, DataType]] = {
    Dimension.X: DataType.DOUBLE,
    Dimension.Y: DataType.DOUBLE,
    Dimension.Z: DataType.DOUBLE,
    Dimension.INTENSITY: DataType.UINT16,
    Dimension.GPS_TIME: DataType.DOUBLE,
    Dimension.RETURN_NUMBER: DataType.UINT8,
    Dimension.NUMBER_OF_RETURNS: DataType.UINT8,
    Dimension.POINT_SOURCE_ID: DataType.UINT16,
    Dimension.POINT_ID: DataType.UINT32,
    Dimension.RED: DataType.UINT16,
    Dimension.GREEN: DataType.UINT16,
    Dimension.BLUE: DataType.UINT16,
    Dimension.INFRARED: DataType.UINT16,
    Dimension.ALPHA: DataType.UINT16,
    Dimension.CLASSIFICATION: DataType.UINT8,
    Dimension.SYNTHETIC: DataType.UINT8,
    Dimension.KEY_POINT: DataType.UINT8,
    Dimension.WITHHELD: DataType.UINT8,
    Dimension.OVERLAP: DataType.UINT8,
    Dimension.CURVATURE: DataType.DOUBLE,
    Dimension.EIGENVALUE0: DataType.DOUBLE,
    Dimension.EIGENVALUE1: DataType.DOUBLE,
    Dimension.EIGENVALUE2: DataType.DOUBLE,
    Dimension.EIGEN_ENTROPY: DataType.DOUBLE,
    Dimension.PLANARITY: DataType.DOUBLE,
    Dimension.LINEARITY: DataType.DOUBLE,
    Dimension.SCATTERING: DataType.DOUBLE,
    Dimension.PITCH: DataType.FLOAT,
    Dimension.ROLL: DataType.FLOAT,
    Dimension.HEADING: DataType.DOUBLE,
    Dimension.PULSE_WIDTH: DataType.FLOAT,
    Dimension.REFLECTED_PULSE: DataType.INT32,
    Dimension.PASSIVE_SIGNAL: DataType.INT32,
    Dimension.ECHO_NORM: DataType.DOUBLE,
    Dimension.ECHO_POS: DataType.DOUBLE,
    Dimension.ECHO_RANGE: DataType.DOUBLE,
    Dimension.HEIGHT_ABOVE_GROUND: DataType.DOUBLE,
    Dimension.NORMAL_X: DataType.DOUBLE,
    Dimension.NORMAL_Y: DataType.DOUBLE,
    Dimension.NORMAL_Z: DataType.DOUBLE,
}


# ASPRS Classification codes
class Classification(int, Enum):
    """ASPRS LAS classification codes."""

    CREATED_NEVER_CLASSIFIED = 0
    UNCLASSIFIED = 1
    GROUND = 2
    LOW_VEGETATION = 3
    MEDIUM_VEGETATION = 4
    HIGH_VEGETATION = 5
    BUILDING = 6
    LOW_POINT = 7
    MODEL_KEY_POINT = 8
    WATER = 9
    RAIL = 10
    ROAD_SURFACE = 11
    OVERLAP_POINTS = 12
    WIRE_GUARD = 13
    WIRE_CONDUCTOR = 14
    TRANSMISSION_TOWER = 15
    WIRE_STRUCTURE_CONNECTOR = 16
    BRIDGE_DECK = 17
    HIGH_NOISE = 18
