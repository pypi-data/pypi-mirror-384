
import os
import unittest

import quartzbio


class QuartzBioTestCase(unittest.TestCase):
    # 'quartzbio:public:/HGNC/3.3.0-2020-10-29/HGNC'
    TEST_DATASET_FULL_PATH = "quartzbio:Public:/HGNC/3.3.1-2021-08-25/HGNC"
    # 'quartzbio:public:/ClinVar/5.1.0-20200720/Variants-GRCH38'
    TEST_DATASET_FULL_PATH_2 = (
        "quartzbio:Public:/ClinVar/5.2.0-20210110/Variants-GRCH38"
    )
    # 'quartzbio:public:/HGNC/3.3.0-2020-10-29/hgnc_1000_rows.txt'
    TEST_FILE_FULL_PATH = "quartzbio:Public:/HGNC/3.3.1-2021-08-25/HGNC-3-3-1-2021-08-25-HGNC-1904014068027535892-20230418174248.json.gz"  # noqa
    TEST_LARGE_TSV_FULL_PATH = ""

    def setUp(self):
        super(QuartzBioTestCase, self).setUp()
        api_key = os.environ.get("QUARTZBIO_API_KEY", None)
        api_host = os.environ.get("QUARTZBIO_API_HOST", None)
        self.client = quartzbio.QuartzBioClient(host=api_host, token=api_key)

    def check_response(self, response, expect, msg):
        subset = [(key, response[key]) for key in [x[0] for x in expect]]
        self.assertEqual(subset, expect)
