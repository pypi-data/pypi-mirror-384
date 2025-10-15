import os
import unittest
from datetime import datetime

from dmi_open_data import ClimateDataParameter, OceanographicDataParameter, Parameter


class TestEnums(unittest.TestCase):
    def test_enums_not_overlapping(self):
        parameter_set = set(Parameter)
        climate_data_parameter_set = set(ClimateDataParameter)
        oceanographic_data_parameter_set = set(OceanographicDataParameter)
        self.assertEqual(parameter_set & climate_data_parameter_set, set())
        self.assertEqual(parameter_set & oceanographic_data_parameter_set, set())
        self.assertEqual(climate_data_parameter_set & oceanographic_data_parameter_set, set())


if __name__ == "__main__":
    unittest.main()
