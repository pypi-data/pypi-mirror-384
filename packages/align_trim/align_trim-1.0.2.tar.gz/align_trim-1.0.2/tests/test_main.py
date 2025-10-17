import pathlib
import unittest
from primalbedtools.scheme import Scheme
from primalbedtools.bedfiles import merge_primers
from primalbedtools.amplicons import create_amplicons

from align_trim.main import (
    create_primer_lookup,
    find_primer_with_lookup,
)

BED_PATH_V5_3_2 = pathlib.Path(__file__).parent / "test_data/primer.bed"
BED_PATH_V1_0_0 = pathlib.Path(__file__).parent / "test_data/v1.0.0.primer.bed"


class TestCreatePrimerLookup(unittest.TestCase):
    """
    Tests for the create_primer_lookup function
    """

    def setUp(self):
        self.scheme = Scheme.from_file(str(BED_PATH_V5_3_2.absolute()))
        self.pools = {bl.pool for bl in self.scheme.bedlines}
        self.scheme.bedlines = merge_primers(self.scheme.bedlines)
        self.amplicons = create_amplicons(self.scheme.bedlines)

        # Create ref len
        self.ref_len = [("MN908947.3", 29903)]
        return super().setUp()

    def test_create_primer_lookup(self):
        """
        Test that the primer lookup is created correctly
        """
        # Create the primer lookup with 0 padding
        padding = 0
        primer_lookup = create_primer_lookup(
            ref_len_tuple=self.ref_len,
            amplicons=self.amplicons,
            padding=padding,
        )
        # Check that the primer lookup is a dictionary
        self.assertIsInstance(primer_lookup, dict)
        # Check that the primer lookup contains the expected keys
        self.assertEqual(
            set(x[0] for x in self.ref_len),
            set(primer_lookup.keys()),
        )

        # Check the size of the primer lookup
        self.assertEqual(
            primer_lookup["MN908947.3"].shape,
            (2, 29903 + 1),  # +1 for half open interval
        )

        # Check each amplicon is present in the lookup and in correct pool
        for amplicon in self.amplicons:
            contents = []
            for row in primer_lookup[amplicon.chrom][
                :, amplicon.amplicon_start - padding : amplicon.amplicon_end + padding
            ]:
                contents.append(set(row))
            self.assertIn(set([amplicon]), contents)

            # Check padding is aligned correctly
            for row in primer_lookup[amplicon.chrom][
                :, amplicon.amplicon_start - padding - 1
            ]:
                self.assertIsNot(row, amplicon)

            for row in primer_lookup[amplicon.chrom][
                :, amplicon.amplicon_end + padding  # +1 -1
            ]:
                self.assertIsNot(row, amplicon)

    def test_create_primer_lookup_padding(self):
        """
        Test that the primer lookup is created correctly
        """
        # Create the primer lookup with 35 padding
        padding = 35
        primer_lookup = create_primer_lookup(
            ref_len_tuple=self.ref_len,
            amplicons=self.amplicons,
            padding=padding,
        )
        # Check that the primer lookup is a dictionary
        self.assertIsInstance(primer_lookup, dict)
        # Check that the primer lookup contains the expected keys
        self.assertEqual(
            set(x[0] for x in self.ref_len),
            set(primer_lookup.keys()),
        )

        # Check the size of the primer lookup
        self.assertEqual(
            primer_lookup["MN908947.3"].shape,
            (2, 29903 + 1),  # +1 for half open interval
        )

        # Check each amplicon is present in the lookup
        for amplicon in self.amplicons:
            # Check amplicon spans correct region
            contents = []
            for row in primer_lookup[amplicon.chrom][
                :,
                max(0, amplicon.amplicon_start - padding) : min(
                    amplicon.amplicon_end + padding, 29903 + 1
                ),
            ]:
                contents.append(set(row))
            self.assertIn(set([amplicon]), contents)

            # Check padding is aligned correctly
            for row in primer_lookup[amplicon.chrom][
                :, amplicon.amplicon_start - padding - 1
            ]:
                self.assertIsNot(row, amplicon)

            for row in primer_lookup[amplicon.chrom][
                :, amplicon.amplicon_end + padding  # +1 -1
            ]:
                self.assertIsNot(row, amplicon)

    def test_create_primer_lookup_no_overlap(self):
        """
        Test that the primer lookup is created correctly
        """
        # Create the primer lookup with a single amplicon
        padding = 0
        primer_lookup = create_primer_lookup(
            ref_len_tuple=self.ref_len,
            amplicons=[self.amplicons[0]],
            padding=padding,
        )

        # Check the size of the primer lookup
        self.assertEqual(
            primer_lookup["MN908947.3"].shape,
            (1, 29903 + 1),  # +1 for half open interval
        )

    def test_create_primer_lookup_overlap(self):
        """
        Test that the primer lookup is created correctly
        """
        # Create some fake amplicon
        # 	nCoV-2019_3 overlaps with nCoV-2019_1
        scheme = Scheme.from_str(
            "MN908947.3	30	54	nCoV-2019_1_LEFT_1	1	+	ACCAACCAACTTTCGATCTCTTGT\n"
            "MN908947.3	385	410	nCoV-2019_1_RIGHT_1	1	-	CATCTTTAAGATGTTGACGTGCCTC\n"
            "MN908947.3	320	342	nCoV-2019_2_LEFT_1	2	+	CTGTTTTACAGGTTCGCGACGT\n"
            "MN908947.3	704	726	nCoV-2019_2_RIGHT_1	2	-	TAAGGATCAGTGCCAAGCTCGT\n"
            "MN908947.3	385	400	nCoV-2019_3_LEFT_1	1	+	CGGTAATAAAGGAGCTGGTGGC\n"
            "MN908947.3	800	820	nCoV-2019_3_RIGHT_1	1	-	AAGGTGTCTGCAATTCATAGCTCT\n"
        )
        scheme.bedlines = merge_primers(scheme.bedlines)
        amplicons = create_amplicons(scheme.bedlines)

        # Create the primer lookup with a single amplicon
        padding = 0
        primer_lookup = create_primer_lookup(
            ref_len_tuple=self.ref_len,
            amplicons=amplicons,
            padding=padding,
        )

        # Check the size of the primer lookup
        self.assertEqual(
            primer_lookup["MN908947.3"].shape,
            (3, 29903 + 1),  # +1 for half open interval
        )


class TestFindPrimerWithLookup(unittest.TestCase):
    def setUp(self):
        self.scheme = Scheme.from_file(str(BED_PATH_V5_3_2.absolute()))
        self.pools = {bl.pool for bl in self.scheme.bedlines}
        self.scheme.bedlines = merge_primers(self.scheme.bedlines)
        self.amplicons = create_amplicons(self.scheme.bedlines)

        # Create ref len and lookup
        self.ref_len = [("MN908947.3", 29903)]
        self.primer_lookup = create_primer_lookup(
            ref_len_tuple=self.ref_len,
            amplicons=self.amplicons,
            padding=0,
        )

        return super().setUp()

    def test_find_primer(self):
        # For each position in each amplicons ensure the correct primer is found
        for amplicon in self.amplicons:
            for fpos in range(amplicon.amplicon_start, amplicon.amplicon_start + 50):
                # Find left
                lp = find_primer_with_lookup(
                    self.primer_lookup, fpos, "+", amplicon.chrom
                )
                self.assertEqual(lp, amplicon.left[0])
            for rpos in range(amplicon.amplicon_end - 50, amplicon.amplicon_end):
                # Find Right
                rp = find_primer_with_lookup(
                    self.primer_lookup, rpos, "-", amplicon.chrom
                )
                self.assertEqual(rp, amplicon.right[0])


class TestTrim(unittest.TestCase):
    def setUp(self) -> None:
        return super().setUp()

    def test_trim_basic(self):
        pass


if __name__ == "__main__":
    unittest.main()
