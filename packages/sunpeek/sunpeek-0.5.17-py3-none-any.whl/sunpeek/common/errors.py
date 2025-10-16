class SunPeekError(Exception):
    pass


class ConfigurationError(SunPeekError):
    pass


class CollectorDefinitionError(SunPeekError):
    """Error in Collector definition.
    E.g. if supplied information is contradictory or not sufficient for full Collector definition.
    See #70 for valid Collector definitions.
    """


class IncompatibleUnitError(SunPeekError):
    """Supplied unit (of raw sensor) is not compatible with the expected unit, e.g. as defined in SensorType.
    """


class VirtualSensorConfigurationError(SunPeekError):
    """Error in calculation of virtual sensor due to missing input or input being None.
    """


class PowerCheckError(SunPeekError):
    """General error in definition / configuration / calculation of ISO 24194 Power Check.
    """


class CalculationError(SunPeekError):
    """General error in definition / handling of virtual sensor.
    """


class AlgorithmError(SunPeekError):
    """Error in some core_method algorithm.
    """


class DuplicateNameError(SunPeekError):
    """Error due to creating a component with a duplicate name, where this is not allowed"""


class SensorNotFoundError(SunPeekError):
    """Error due to not finding a sensor when one was expected to exist"""


class SensorDataNotFoundError(SunPeekError):
    """Error due to not finding a data column for a sensor in the current data store"""


class NoDataError(SunPeekError):
    """No data are available in the selected data range"""


class TimeIndexError(SunPeekError):
    """Error handling or retrieving plant.time_index."""


class TimeZoneError(SunPeekError):
    """Error related to time zone"""


class DataProcessingError(SunPeekError):
    """Error related to data upload and processing"""


class DatabaseAlreadyExistsError(SunPeekError):
    pass
