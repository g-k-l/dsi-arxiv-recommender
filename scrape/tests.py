# -*- coding: utf-8 -*-
from datetime import datetime
from unittest import TestCase

from extract import get_fields


class TestExtract(TestCase):
    def setUp(self):
        self.f = open("test.xml", "r")
        self.xmlstr = self.f.read()

    def tearDown(self):
        self.f.close()

    def test_get_fields(self):
        actual = get_fields(self.xmlstr)
        self.assertEqual(actual, (
            "http://arxiv.org/abs/0704.0147",
            "A POVM view of the ensemble approach to polarization optics",
            ["Sudha", "Rao, A. V. Gopala", "Devi, A. R. Usha",
             "Rajagopal, A. K."],
            ["Physics - Optics", "Physics - Classical Physics"],
            "redacted, redacted, redacted, redacted, redacted",
            datetime.strptime("2007-06-20", "%Y-%m-%d").date(),
        ))

