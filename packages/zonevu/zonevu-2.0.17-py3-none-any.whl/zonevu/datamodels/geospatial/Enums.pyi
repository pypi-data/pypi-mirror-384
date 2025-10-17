from strenum import StrEnum

class UnitsSystemEnum(StrEnum):
    Metric = 'Metric'
    US = 'US'

class DistanceUnitsEnum(StrEnum):
    Undefined = 'Undefined'
    Meters = 'Meters'
    Feet = 'Feet'
    FeetUS = 'FeetUS'
    @classmethod
    def units_system(cls, units: DistanceUnitsEnum) -> UnitsSystemEnum: ...

class DepthUnitsEnum(StrEnum):
    Undefined = 'Undefined'
    Meters = 'Meters'
    Feet = 'Feet'
    @classmethod
    def units_system(cls, units: DepthUnitsEnum) -> UnitsSystemEnum: ...

class DatumTypeEnum(StrEnum):
    WGS1984 = 'WGS1984'
    NAD1927 = 'NAD1927'
    NAD1983 = 'NAD1983'
