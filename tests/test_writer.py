from unittest import TestCase

from htf_core.models import HarmonizedMetadataEntry
from htf_core.writer import HtfWriter


class Test(TestCase):
    def test_compose_static_metadata_entry(self):
        entry = HarmonizedMetadataEntry(
            name="Static",
            column_names=["Property1"],
            column_values={"Property1": [1]}
        )

        text = HtfWriter.compose_metadata_entry(entry)

        self.assertEqual(text, "[Static;Property1]1")

    def test_compose_dimensional_metadata_entry(self):
        entry = HarmonizedMetadataEntry(
            name="Dimensions",
            column_names=["Dim1", "Dim2"],
            column_values={
                "Dim1": [10, 20],
                "Dim2": ["A", "B"]
            }
        )

        text = HtfWriter.compose_metadata_entry(entry)

        self.assertEqual(text, "[Dimensions;Dim1;Dim2]10;A;20;B")
