import unittest
import time
from dfva_python.client import Client
from .utils import DOCUMENT_RESPONSE_TABLE, DOCUMENT_FORMATS, read_files, \
    TIMEWAIT, FORMAT_WAIT

#{"01-4040-5050": ["pdf"]}
ALLOWED_TEST = {} #{"9-0000-0000-000": [  'xml_contrafirma', 'pdf'] } #{"500000000000": [  'xml_contrafirma', 'pdf'], '01-1919-2121': ['xml_cofirma', 'msoffice'], '01-6060-7070': ['odf']}
transactions = {}

client = Client()


def load_signdocuments():
    for identification in DOCUMENT_RESPONSE_TABLE.keys():
        for _format in DOCUMENT_FORMATS:
            if ALLOWED_TEST:
                if not (identification in ALLOWED_TEST and
                        _format in ALLOWED_TEST[identification]):
                    continue
            auth_resp = client.sign(
                identification,
                read_files(_format),
                "test %s" % (_format),
                _format=_format,
                reason="Test" if _format == 'pdf' else None,
                place="algún lugar de la mancha" if _format == 'pdf' else None,
                )
            if identification not in transactions:
                transactions[identification] = {}
            transactions[identification][_format] = auth_resp
            if auth_resp['id_transaction'] == 0 and identification not in [
                                                    "500000000000",
                                                    "01-1919-2222",
                                                    "01-1919-2020",
                                                    "01-1919-2121",
                                                    "9-0000-0000-000"]:
                raise Exception("ID transaction is not 0 as experected")
        time.sleep(FORMAT_WAIT)


# def setUpModule():
#     load_signdocuments()
#     time.sleep(TIMEWAIT)


class TestDocumentReceived (unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        load_signdocuments()
        time.sleep(TIMEWAIT)
        print("Recuerde modificar los archivos de configuración y registrar " +
              "la institución en dfva")

    def do_checks(self, _format, identification):
        if ALLOWED_TEST:
            if not (identification in ALLOWED_TEST and
                    _format in ALLOWED_TEST[identification]):
                return

        if identification in ["500000000000",
                              "01-1919-2222",
                              "01-1919-2020",
                              "01-1919-2121",
                              "9-0000-0000-000"]:
            self.assertEqual(DOCUMENT_RESPONSE_TABLE[identification][0],
                             transactions[identification][_format]['status'])
            return
        res = client.sign_check(transactions[identification][_format][
                'id_transaction'])
        self.assertEqual(DOCUMENT_RESPONSE_TABLE[identification][3],
                         res['status'])
        client.sign_delete(transactions[identification][_format][
                'id_transaction'])

    def test_sign_xml_cofirma_0180809090(self):
        self.do_checks("xml_cofirma", "01-8080-9090")

    def test_sign_xml_cofirma_0177889900(self):
        self.do_checks("xml_cofirma", "01-7788-9900")

    def test_sign_xml_cofirma_0111002211(self):
        self.do_checks("xml_cofirma", "01-1100-2211")

    def test_sign_xml_cofirma_0119192121(self):
        self.do_checks("xml_cofirma", "01-1919-2121")

    def test_sign_xml_cofirma_0133445566(self):
        self.do_checks("xml_cofirma", "01-3344-5566")

    def test_sign_xml_cofirma_0110102020(self):
        self.do_checks("xml_cofirma", "01-1010-2020")

    def test_sign_xml_cofirma_0119192222(self):
        self.do_checks("xml_cofirma", "01-1919-2222")

    def test_sign_xml_cofirma_0119192020(self):
        self.do_checks("xml_cofirma", "01-1919-2020")

    def test_sign_xml_cofirma_0160607070(self):
        self.do_checks("xml_cofirma", "01-6060-7070")

    def test_sign_xml_cofirma_0120203030(self):
        self.do_checks("xml_cofirma", "01-2020-3030")

    def test_sign_xml_cofirma_100000000000(self):
        self.do_checks("xml_cofirma", "100000000000")

    def test_sign_xml_cofirma_0140405050(self):
        self.do_checks("xml_cofirma", "01-4040-5050")

    def test_sign_xml_cofirma_500000000000(self):
        self.do_checks("xml_cofirma", "500000000000")

    def test_sign_xml_cofirma_900000000000(self):
        self.do_checks("xml_cofirma", "9-0000-0000-000")

    def test_sign_xml_contrafirma_0180809090(self):
        self.do_checks("xml_contrafirma", "01-8080-9090")

    def test_sign_xml_contrafirma_0177889900(self):
        self.do_checks("xml_contrafirma", "01-7788-9900")

    def test_sign_xml_contrafirma_0111002211(self):
        self.do_checks("xml_contrafirma", "01-1100-2211")

    def test_sign_xml_contrafirma_0119192121(self):
        self.do_checks("xml_contrafirma", "01-1919-2121")

    def test_sign_xml_contrafirma_0133445566(self):
        self.do_checks("xml_contrafirma", "01-3344-5566")

    def test_sign_xml_contrafirma_0110102020(self):
        self.do_checks("xml_contrafirma", "01-1010-2020")

    def test_sign_xml_contrafirma_0119192222(self):
        self.do_checks("xml_contrafirma", "01-1919-2222")

    def test_sign_xml_contrafirma_0119192020(self):
        self.do_checks("xml_contrafirma", "01-1919-2020")

    def test_sign_xml_contrafirma_0160607070(self):
        self.do_checks("xml_contrafirma", "01-6060-7070")

    def test_sign_xml_contrafirma_0120203030(self):
        self.do_checks("xml_contrafirma", "01-2020-3030")

    def test_sign_xml_contrafirma_100000000000(self):
        self.do_checks("xml_contrafirma", "100000000000")

    def test_sign_xml_contrafirma_0140405050(self):
        self.do_checks("xml_contrafirma", "01-4040-5050")

    def test_sign_xml_contrafirma_500000000000(self):
        self.do_checks("xml_contrafirma", "500000000000")

    def test_sign_xml_contrafirma_900000000000(self):
        self.do_checks("xml_contrafirma", "9-0000-0000-000")

    def test_sign_odf_0180809090(self):
        self.do_checks("odf", "01-8080-9090")

    def test_sign_odf_0177889900(self):
        self.do_checks("odf", "01-7788-9900")

    def test_sign_odf_0111002211(self):
        self.do_checks("odf", "01-1100-2211")

    def test_sign_odf_0119192121(self):
        self.do_checks("odf", "01-1919-2121")

    def test_sign_odf_0133445566(self):
        self.do_checks("odf", "01-3344-5566")

    def test_sign_odf_0110102020(self):
        self.do_checks("odf", "01-1010-2020")

    def test_sign_odf_0119192222(self):
        self.do_checks("odf", "01-1919-2222")

    def test_sign_odf_0119192020(self):
        self.do_checks("odf", "01-1919-2020")

    def test_sign_odf_0160607070(self):
        self.do_checks("odf", "01-6060-7070")

    def test_sign_odf_0120203030(self):
        self.do_checks("odf", "01-2020-3030")

    def test_sign_odf_100000000000(self):
        self.do_checks("odf", "100000000000")

    def test_sign_odf_0140405050(self):
        self.do_checks("odf", "01-4040-5050")

    def test_sign_odf_500000000000(self):
        self.do_checks("odf", "500000000000")

    def test_sign_odf_900000000000(self):
        self.do_checks("odf", "9-0000-0000-000")

    def test_sign_msoffice_0180809090(self):
        self.do_checks("msoffice", "01-8080-9090")

    def test_sign_msoffice_0177889900(self):
        self.do_checks("msoffice", "01-7788-9900")

    def test_sign_msoffice_0111002211(self):
        self.do_checks("msoffice", "01-1100-2211")

    def test_sign_msoffice_0119192121(self):
        self.do_checks("msoffice", "01-1919-2121")

    def test_sign_msoffice_0133445566(self):
        self.do_checks("msoffice", "01-3344-5566")

    def test_sign_msoffice_0110102020(self):
        self.do_checks("msoffice", "01-1010-2020")

    def test_sign_msoffice_0119192222(self):
        self.do_checks("msoffice", "01-1919-2222")

    def test_sign_msoffice_0119192020(self):
        self.do_checks("msoffice", "01-1919-2020")

    def test_sign_msoffice_0160607070(self):
        self.do_checks("msoffice", "01-6060-7070")

    def test_sign_msoffice_0120203030(self):
        self.do_checks("msoffice", "01-2020-3030")

    def test_sign_msoffice_100000000000(self):
        self.do_checks("msoffice", "100000000000")

    def test_sign_msoffice_0140405050(self):
        self.do_checks("msoffice", "01-4040-5050")

    def test_sign_msoffice_500000000000(self):
        self.do_checks("msoffice", "500000000000")

    def test_sign_msoffice_900000000000(self):
        self.do_checks("msoffice", "9-0000-0000-000")

    def test_sign_pdf_0180809090(self):
        self.do_checks("pdf", "01-8080-9090")

    def test_sign_pdf_0177889900(self):
        self.do_checks("pdf", "01-7788-9900")

    def test_sign_pdf_0111002211(self):
        self.do_checks("pdf", "01-1100-2211")

    def test_sign_pdf_0119192121(self):
        self.do_checks("pdf", "01-1919-2121")

    def test_sign_pdf_0133445566(self):
        self.do_checks("pdf", "01-3344-5566")

    def test_sign_pdf_0110102020(self):
        self.do_checks("pdf", "01-1010-2020")

    def test_sign_pdf_0119192222(self):
        self.do_checks("pdf", "01-1919-2222")

    def test_sign_pdf_0119192020(self):
        self.do_checks("pdf", "01-1919-2020")

    def test_sign_pdf_0160607070(self):
        self.do_checks("pdf", "01-6060-7070")

    def test_sign_pdf_0120203030(self):
        self.do_checks("pdf", "01-2020-3030")

    def test_sign_pdf_100000000000(self):
        self.do_checks("pdf", "100000000000")

    def test_sign_pdf_0140405050(self):
        self.do_checks("pdf", "01-4040-5050")

    def test_sign_pdf_500000000000(self):
        self.do_checks("pdf", "500000000000")

    def test_sign_pdf_900000000000(self):
        self.do_checks("pdf", "9-0000-0000-000")


class ContrafirmaWrong(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        _format = "xml_contrafirma"
        auth_resp = client.sign(
            '03-0110-2020',
            read_files("xml", name='no_contrafirmado.'),
            "test %s" % (_format),
            _format=_format,
            )
        transactions['03-0110-2020'] = {}
        transactions['03-0110-2020']["xml_contrafirma"] = auth_resp
        if auth_resp['id_transaction'] == 0:
            raise
        time.sleep(TIMEWAIT)

    def test_sign_contrafirma_not_ok(self):
        res = client.sign_check(
            transactions['03-0110-2020']["xml_contrafirma"]['id_transaction'])
        self.assertEqual(15, res['status'])
        client.sign_delete(transactions['03-0110-2020']["xml_contrafirma"][
                'id_transaction'])
