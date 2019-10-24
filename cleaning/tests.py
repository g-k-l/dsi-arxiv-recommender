# -*- coding: utf-8 -*-
from datetime import datetime
from os.path import dirname, join
from unittest import TestCase

from .extract_meta import (pdf_metadata, arxivid_from, ARXIV_ABS_URL)
from .pipeline import (pdf_to_text, to_tokens, yield_pdfs_only)


class TestExtract(TestCase):
    def setUp(self):
        self.xmlfpath = join(dirname(__file__), "testfiles/test.xml")

    def test_pdf_metadata(self):
        output = list(pdf_metadata(self.xmlfpath))
        self.assertEqual(len(output), 2, output)
        self.assertTrue(all(output[0]), "Expect all fields "
                        "populated for the first metadatum.")
        self.assertEqual(output[0]["filename"], "pdf/arXiv_pdf_0001_001.tar")
        self.assertEqual(output[0]["num_items"], 1797)
        self.assertEqual(output[0]["size"], 524304163)
        self.assertEqual(output[0]["timestamp"],
                         datetime(year=2019, month=5, day=22, second=5))
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


class TestPipeline(TestCase):
    def setUp(self):
        self.testpdf_path = join(dirname(__file__), "testfiles/testfile.pdf")
        self.testdir = join(dirname(__file__), "testfiles/")

    def test_pdf_to_text(self):
        pdf_content = pdf_to_text(self.testpdf_path)
        self.assertEqual(pdf_content.strip(), "Test PDF File")

    def test_to_tokens(self):
        raw_content = "I am 29 years old."
        expected = ["year", "old"]
        self.assertEqual(expected, to_tokens(raw_content))

        raw_content = "This is fun. I am having fun."
        expected = ["fun", "fun"]
        self.assertEqual(expected, to_tokens(raw_content))

        raw_content = """The truncation errors in equations of state
            (EOSs) of nuclear matter derived from the chiral nucleon-nucleon
            (N N ) potentials"""
        expected = ['truncation',
                    'error',
                    'equation',
                    'state',
                    'eos',
                    'nuclear',
                    'matter',
                    'derived',
                    'chiral',
                    'nucleon-nucleon',
                    'potential']
        self.assertEqual(expected, to_tokens(raw_content))

    def test_yield_pdfs_only(self):
        yielded = list(yield_pdfs_only(self.testdir))
        self.assertEqual(len(yielded), 1)
        self.assertEqual(yielded[0][1], "testfile.pdf")

