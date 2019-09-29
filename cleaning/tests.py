# -*- coding: utf-8 -*-
from unittest import TestCase

from extract import (pdf_metadata, arxivid_from, ARXIV_ABS_URL)


class TestExtract(TestCase):
    def setUp(self):
        self.xmlfpath = "./src-metadata/test.xml"

    def test_pdf_metadata(self):
        output = list(pdf_metadata(self.xmlfpath))
        self.assertEqual(len(output), 2, output)
        self.assertTrue(all(output[0]), "Expect all fields "
                        "populated for the first metadatum.")
        self.assertEqual(output[0]["filename"], "pdf/arXiv_pdf_0001_001.tar")
        self.assertEqual(output[1]["filename"], "pdf/arXiv_pdf_0001_002.tar")
        self.assertEqual(output[1]["timestamp"], None)

    def test_arxivid_from(self):
        self.assertEqual(
            arxivid_from("quant-ph0001119"),
            ARXIV_ABS_URL + "quant-ph/0001119",
        )
        self.assertEqual(
            arxivid_from("1909.11826"),
            ARXIV_ABS_URL + "1909.11826",
        )
        for case in ["20-34abc", "", "XYZ", "$1909.1"]:
            with self.assertRaises(ValueError):
                arxivid_from(case)
