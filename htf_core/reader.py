import ast
import re
from io import TextIOWrapper

from htf_core.models import HarmonizedTelemetryRecording, HarmonizedMetadataEntry, HarmonizedTelemetryChannel


METADATA_REGEX = re.compile(
    r"^\[(?P<preamble_content>[^]]+)]"
    r"(?P<data_content>.*)$"
)

CHANNEL_REGEX = re.compile(
    r"^\("
    r"(?P<name>[^;]+);"
    r"(?P<unit>[^;]+);"
    r"(?P<frequency>[^;]*);"
    r"(?P<value_count>[^)]+)\)"
    r"(?P<data_content>.*)$"
)


class HtfReader:
    def __init__(self, entries: list[str]):
        self.entries = entries

    @classmethod
    def from_str(cls, text: str):
        content = text.split("\n")
        return cls(content)

    @classmethod
    def from_file(cls, file: TextIOWrapper):
        content = file.readlines()
        return cls(content)

    def read(self) -> HarmonizedTelemetryRecording:
        metadata_entries = []
        telemetry_channels = []
        for entry in self.entries:
            metadata_match = METADATA_REGEX.match(entry)
            if metadata_match:
                metadata_entries.append(self.read_metadata_entry(entry))
                continue

            channel_match = CHANNEL_REGEX.match(entry)
            if channel_match:
                telemetry_channels.append(self.read_telemetry_channel(entry))
                continue

            raise ValueError(f"Entry does not match metadata or channel format: {entry}")
        return HarmonizedTelemetryRecording(
            metadata=metadata_entries if len(metadata_entries) > 0 else None,
            channels=telemetry_channels
        )

    @staticmethod
    def read_metadata_entry(line: str) -> HarmonizedMetadataEntry:
        match = METADATA_REGEX.match(line)
        if not match:
            raise ValueError(f"Line does not match metadata format: {line}")

        preamble_content = match.group("preamble_content")
        data_content = match.group("data_content")

        parts = preamble_content.split(";")
        name = parts[0]
        column_names = parts[1:]

        column_values = {col_name: [] for col_name in column_names}
        data_values = data_content.split(";")
        for i, value in enumerate(data_values):
            col_name = column_names[i % len(column_names)]
            column_values[col_name].append(value)

        return HarmonizedMetadataEntry(
            name=name,
            column_names=column_names,
            column_values=column_values,
        )


def read_telemetry_channel_with_all_values(line: str) -> HarmonizedTelemetryChannel:
    match = CHANNEL_REGEX.match(line)
    if not match:
        raise ValueError(f"Line does not match channel format: {line}")

    name = match.group("name")
    unit = match.group("unit")
    frequency_str = match.group("frequency")
    frequency = int(frequency_str) if frequency_str else None
    total_values = int(match.group("value_count"))
    data_content = match.group("data_content")

    values = []
    if data_content:
        # Split and filter out empty strings from trailing semicolons
        value_pairs = [p for p in data_content.split(";") if p]

        last_index = -1
        last_value = None

        for pair in value_pairs:
            index_str, value_str = pair.split("=", 1)
            current_index = int(index_str)
            current_value = ast.literal_eval(value_str) if value_str else None

            # Fill the gap between the last recorded index and this one
            # using the previous value (Forward Fill)
            for gap_index in range(last_index + 1, current_index):
                values.append((gap_index, last_value))

            values.append((current_index, current_value))

            last_index = current_index
            last_value = current_value

        # Fill up to last index if there are trailing missing values
        for gap_index in range(last_index + 1, total_values):
            values.append((gap_index, last_value))

    return HarmonizedTelemetryChannel(
        name=name,
        unit=unit,
        frequency=frequency,
        total_values=total_values,
        values=values
    )
