from typing import Optional


class HarmonizedTelemetryChannel:
    """A telemetry channel used within a recording."""

    def __init__(self, name: str, unit: str, frequency: Optional[int],
                 total_values: int, values: list[tuple[[int, object]]]):
        self.name = name
        self.unit = unit
        self.frequency = frequency
        self.total_values = total_values
        self.values = values


class HarmonizedMetadataEntry:
    """
    Unified class for both static metadata (single record, n=1) and dimensional aggregations (n>=1).
    Maps directly to the HTF line structure: [name;property_1;property_2;...]value1_1;value1_2;value2_1;value2_2;...
    """

    # TODO: Values are wrong
    def __init__(self, name: str, column_names: list[str], column_values: dict[str, list[object]]):
        self.name = name
        self.column_names = column_names
        self.column_values = column_values
        self._n = len(column_names)

    @property
    def is_static(self) -> bool:
        """Helper to quickly identify single-record static metadata."""
        return self._n == 1 and len(self.column_values) == 1


class HarmonizedTelemetryRecording:
    """Representation of a complete telemetry recording with metadata and channels."""
    def __init__(self, metadata: Optional[list[HarmonizedMetadataEntry]], channels: list[HarmonizedTelemetryChannel]):
        self.metadata = metadata
        self.channels = channels
