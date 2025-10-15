import unittest
import time
from dfva_python.client import Client
from .utils import DOCUMENT_STAMP_CODE, DOCUMENT_FORMATS, read_files, \
    TIMEWAIT, FORMAT_WAIT

#{"01-4040-5050": ["pdf"]}
ALLOWED_TEST = {} #{"1000": [  'xml_contrafirma', 'pdf'] } #{"500000000000": [  'xml_contrafirma', 'pdf'], '01-1919-2121': ['xml_cofirma', 'msoffice'], '01-6060-7070': ['odf']}
transactions = {}

client = Client()


def load_stampdocuments():
    for idfunctionality in DOCUMENT_STAMP_CODE.keys():
        for _format in DOCUMENT_FORMATS:
            if ALLOWED_TEST:
                if not (idfunctionality in ALLOWED_TEST and
                        _format in ALLOWED_TEST[idfunctionality]):
                    continue
            auth_resp = client.stamp(
                read_files(_format),
                _format=_format,
                reason="Test" if _format == 'pdf' else None,
                place="algún lugar de la mancha" if _format == 'pdf' else None,
                id_functionality=int(idfunctionality)
                )
            if idfunctionality not in transactions:
                transactions[idfunctionality] = {}
            transactions[idfunctionality][_format] = auth_resp

        time.sleep(FORMAT_WAIT)


# def setUpModule():
#     load_stampdocuments()
#     time.sleep(TIMEWAIT)


class TestStampDocument(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        load_stampdocuments()
        time.sleep(TIMEWAIT)
        print("Recuerde modificar los archivos de configuración y registrar " +
              "la institución en dfva")

    def do_checks(self, _format, idfuntionality):
        if ALLOWED_TEST:
            if not (idfuntionality in ALLOWED_TEST and
                    _format in ALLOWED_TEST[idfuntionality]):
                return

        if idfuntionality == '1000':
            self.assertEqual(DOCUMENT_STAMP_CODE[idfuntionality][0],
                             transactions[idfuntionality][_format]['status'])

        res = client.stamp_check(transactions[idfuntionality][_format]['id_transaction'])
        self.assertEqual(DOCUMENT_STAMP_CODE[idfuntionality][3], res['status'])
        client.stamp_delete(transactions[idfuntionality][_format]['id_transaction'])

    def test_stamp_xml_cofirma_1000(self):
        self.do_checks("xml_cofirma", "1000")

    def test_stamp_xml_cofirma_1001(self):
        self.do_checks("xml_cofirma", "1001")

    def test_stamp_xml_cofirma_1004(self):
        self.do_checks("xml_cofirma", "1004")

    def test_stamp_xml_cofirma_1005(self):
        self.do_checks("xml_cofirma", "1005")

    def test_stamp_xml_cofirma_1007(self):
        self.do_checks("xml_cofirma", "1007")

    def test_stamp_xml_cofirma_1008(self):
        self.do_checks("xml_cofirma", "1008")

    def test_stamp_xml_contrafirma_1000(self):
        self.do_checks("xml_contrafirma", "1000")

    def test_stamp_xml_contrafirma_1001(self):
        self.do_checks("xml_contrafirma", "1001")

    def test_stamp_xml_contrafirma_1004(self):
        self.do_checks("xml_contrafirma", "1004")

    def test_stamp_xml_contrafirma_1005(self):
        self.do_checks("xml_contrafirma", "1005")

    def test_stamp_xml_contrafirma_1007(self):
        self.do_checks("xml_contrafirma", "1007")

    def test_stamp_xml_contrafirma_1008(self):
        self.do_checks("xml_contrafirma", "1008")

    def test_stamp_odf_1000(self):
        self.do_checks("odf", "1000")

    def test_stamp_odf_1001(self):
        self.do_checks("odf", "1001")

    def test_stamp_odf_1004(self):
        self.do_checks("odf", "1004")

    def test_stamp_odf_1005(self):
        self.do_checks("odf", "1005")

    def test_stamp_odf_1007(self):
        self.do_checks("odf", "1007")

    def test_stamp_odf_1008(self):
        self.do_checks("odf", "1008")

    def test_stamp_msoffice_1000(self):
        self.do_checks("msoffice", "1000")

    def test_stamp_msoffice_1001(self):
        self.do_checks("msoffice", "1001")

    def test_stamp_msoffice_1004(self):
        self.do_checks("msoffice", "1004")

    def test_stamp_msoffice_1005(self):
        self.do_checks("msoffice", "1005")

    def test_stamp_msoffice_1007(self):
        self.do_checks("msoffice", "1007")

    def test_stamp_msoffice_1008(self):
        self.do_checks("msoffice", "1008")

    def test_stamp_pdf_1000(self):
        self.do_checks("pdf", "1000")

    def test_stamp_pdf_1001(self):
        self.do_checks("pdf", "1001")

    def test_stamp_pdf_1004(self):
        self.do_checks("pdf", "1004")

    def test_stamp_pdf_1005(self):
        self.do_checks("pdf", "1005")

    def test_stamp_pdf_1007(self):
        self.do_checks("pdf", "1007")

    def test_stamp_pdf_1008(self):
        self.do_checks("pdf", "1008")
