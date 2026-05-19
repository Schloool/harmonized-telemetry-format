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
        # trailing indices 3 and 4 are forward-filled with the last value (300)
        self.assertEqual(channel.values, [(0, 100), (1, 200), (2, 300), (3, 300), (4, 300)])

    def test_reads_all_channel_values_including_duplicates(self):
        valid_channel_line = "(ChannelName;Unit;;5)0=100;1=100;2=200;3=200;4=300"
        reader = HtfReader(entries=[valid_channel_line])

        channel = reader.read_telemetry_channel(valid_channel_line)

        self.assertIsNone(channel.frequency)
        self.assertEqual(channel.total_values, 5)
        self.assertEqual(channel.values, [(0, 100), (1, 100), (2, 200), (3, 200), (4, 300)])

    def test_sets_none_values_for_missing_frequency(self):
        channel_line = "(ChannelName;Unit;;3)0=100;1=200;2=300"
        reader = HtfReader(entries=[channel_line])

        channel = reader.read_telemetry_channel(channel_line)

        self.assertIsNone(channel.frequency)

    def test_sets_none_values_for_missing_channel_values(self):
        channel_line = "(ChannelName;Unit;;3)0="
        reader = HtfReader(entries=[channel_line])

        channel = reader.read_telemetry_channel(channel_line)

        # index 0 is None, indices 1 and 2 are forward-filled as None
        self.assertEqual(channel.values, [(0, None), (1, None), (2, None)])

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

    def test_parses_static_metadata_string_value(self):
        line = "[simulation_setup_label;]Living Lab - Hexapod"
        entry = HtfReader.read_metadata_entry(line)

        self.assertEqual(entry.name, "simulation_setup_label")
        self.assertEqual(entry.column_names, ["simulation_setup_label"])
        self.assertEqual(entry.column_values, {"simulation_setup_label": ["Living Lab - Hexapod"]})
        self.assertTrue(entry.is_static)

    def test_parses_static_metadata_numeric_value(self):
        line = "[static_metadata;]12.51"
        entry = HtfReader.read_metadata_entry(line)

        self.assertEqual(entry.name, "static_metadata")
        self.assertEqual(entry.column_names, ["static_metadata"])
        self.assertEqual(entry.column_values, {"static_metadata": ["12.51"]})
        self.assertTrue(entry.is_static)

    def test_parses_static_metadata_multiple_values(self):
        line = "[multi_values;]val1;val2;val3"
        entry = HtfReader.read_metadata_entry(line)

        self.assertEqual(entry.name, "multi_values")
        self.assertEqual(entry.column_names, ["multi_values"])
        self.assertEqual(entry.column_values, {"multi_values": ["val1", "val2", "val3"]})

    def test_static_metadata_does_not_affect_named_column_metadata(self):
        line = "[Metadata;Property1;Property2]Value1;Value2"
        entry = HtfReader.read_metadata_entry(line)

        self.assertEqual(entry.column_names, ["Property1", "Property2"])
        self.assertEqual(entry.column_values, {"Property1": ["Value1"], "Property2": ["Value2"]})
        self.assertFalse(entry.is_static)

    def test_parses_multi_dim_metadata_multiple_rows(self):
        line = "[multi_dim_1;a;b]val1a;val1b;val2a;val2b;val3a;val3b"
        entry = HtfReader.read_metadata_entry(line)

        self.assertEqual(entry.name, "multi_dim_1")
        self.assertEqual(entry.column_names, ["a", "b"])
        self.assertEqual(entry.column_values, {
            "a": ["val1a", "val2a", "val3a"],
            "b": ["val1b", "val2b", "val3b"],
        })
        self.assertFalse(entry.is_static)

    def test_parses_multi_dim_metadata_single_row(self):
        line = "[multi_dim_2;a;b]val1a;val1b"
        entry = HtfReader.read_metadata_entry(line)

        self.assertEqual(entry.name, "multi_dim_2")
        self.assertEqual(entry.column_names, ["a", "b"])
        self.assertEqual(entry.column_values, {"a": ["val1a"], "b": ["val1b"]})
        self.assertFalse(entry.is_static)

    def test_forward_fills_gap_between_stored_channel_values(self):
        channel_line = "(ChannelName;Unit;10;5)0=1;3=99"
        channel = HtfReader.read_telemetry_channel(channel_line)

        # indices 1 and 2 forward-filled from index 0; index 4 forward-filled from index 3
        self.assertEqual(channel.values, [(0, 1), (1, 1), (2, 1), (3, 99), (4, 99)])
