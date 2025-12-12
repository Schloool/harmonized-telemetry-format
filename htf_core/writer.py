from htf_core.models import HarmonizedTelemetryRecording, HarmonizedMetadataEntry, HarmonizedTelemetryChannel


class HtfWriter:
    def __init__(self, recording: HarmonizedTelemetryRecording):
        self.recording = recording

    def serialize(self) -> str:
        lines = []
        if self.recording.metadata:
            for entry in self.recording.metadata:
                lines.append(self.compose_metadata_entry(entry))

        for channel in self.recording.channels:
            lines.append(self.compose_channel(channel))

        return "\n".join(lines)

    @staticmethod
    def compose_metadata_entry(entry: HarmonizedMetadataEntry) -> str:
        headers = ";".join(entry.column_names)
        preamble = f"[{entry.name};{headers}]"

        if not entry.column_names:
            raise "No column names provided"

        first_column_key = entry.column_names[0]
        num_rows = len(entry.column_values.get(first_column_key, []))

        row_data_list = []

        for data_index in range(num_rows):
            current_row_values = []

            for col_name in entry.column_names:
                column_list = entry.column_values.get(col_name, [])

                if data_index < len(column_list):
                    current_row_values.append(str(column_list[data_index]))

            row_data_list.append(";".join(current_row_values))

        data = ";".join(row_data_list)

        return f"{preamble}{data}"

    @staticmethod
    def compose_channel(channel: HarmonizedTelemetryChannel) -> str:
        frequency = channel.frequency if channel.frequency is not None else ""
        preamble = f"({channel.name};{channel.unit};{frequency};{channel.total_values})"

        # Create index-value pairs, omitting repeating values
        value_pairs = [f"{index}={value}"
                       for index, value in channel.values
                       if index == 0 or value != channel.values[index - 1]]

        values = ";".join(value_pairs)
        return f"{preamble}{values}"
