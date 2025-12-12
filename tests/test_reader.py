from unittest import TestCase

from htf_core.reader import HtfReader


class Test(TestCase):
    def test_reads_complete_recording(self):
        entries = [
            "[Metadata;Property1;Property2]Value1;Value2",
            "(ChannelName;Unit;10;3)0=100;1=200;2=300"
        ]
        reader = HtfReader(entries=entries)

        recording = reader.read()

        self.assertIsNotNone(recording.metadata)
        self.assertEqual(len(recording.metadata), 1)
        self.assertEqual(len(recording.channels), 1)

    def test_parses_valid_metadata(self):
        valid_metadata_line = "[Metadata;Property1;Property2]Value1;Value2"
        reader = HtfReader(entries=[valid_metadata_line])

        metadata_entry = reader.read_metadata_entry(valid_metadata_line)

        self.assertEqual(metadata_entry.name, "Metadata")
        self.assertEqual(metadata_entry.column_names, ["Property1", "Property2"])
        self.assertEqual(metadata_entry.column_values, {
            "Property1": ["Value1"],
            "Property2": ["Value2"]
        })

    def test_parses_valid_channel(self):
        valid_channel_line = "(ChannelName;Unit;10;5)0=100;1=200;2=300"
        reader = HtfReader(entries=[valid_channel_line])

        channel = reader.read_telemetry_channel(valid_channel_line)

        self.assertEqual(channel.name, "ChannelName")
        self.assertEqual(channel.unit, "Unit")
        self.assertEqual(channel.frequency, 10)
        self.assertEqual(channel.total_values, 5)
        self.assertEqual(channel.values, [(0, 100), (1, 200), (2, 300)])

    def test_emits_duplicate_channel_values(self):
        valid_channel_line = "(ChannelName;Unit;;5)0=100;1=100;2=200;3=200;4=300"
        reader = HtfReader(entries=[valid_channel_line])

        channel = reader.read_telemetry_channel(valid_channel_line)

        self.assertIsNone(channel.frequency)
        self.assertEqual(channel.total_values, 5)
        self.assertEqual(channel.values, [(0, 100), (2, 200), (4, 300)])

    def test_sets_none_values_for_missing_frequency(self):
        channel_line = "(ChannelName;Unit;;3)0=100;1=200;2=300"
        reader = HtfReader(entries=[channel_line])

        channel = reader.read_telemetry_channel(channel_line)

        self.assertIsNone(channel.frequency)

    def test_sets_none_values_for_missing_channel_values(self):
        channel_line = "(ChannelName;Unit;;3)0="
        reader = HtfReader(entries=[channel_line])

        channel = reader.read_telemetry_channel(channel_line)

        self.assertEqual(channel.values, [(0, None)])

    def test_throws_on_invalid_metadata(self):
        invalid_metadata_line = "[InvalidMetadata;Data;Data"
        reader = HtfReader(entries=[invalid_metadata_line])

        with self.assertRaises(ValueError):
            reader.read_metadata_entry(invalid_metadata_line)

    def test_throws_on_invalid_channel(self):
        invalid_channel_line = "(InvalidChannel;Unit;Frequency;TotalValues"
        reader = HtfReader(entries=[invalid_channel_line])

        with self.assertRaises(ValueError):
            reader.read_telemetry_channel(invalid_channel_line)
