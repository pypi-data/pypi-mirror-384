import unittest
from dfva_python.client import Client
from .utils import read_files
from base64 import b64encode
from asn1crypto import pem
valclient = Client()


def pem_to_base64(certificate):
    if pem.detect(certificate):
        _, _, der_bytes = pem.unarmor(certificate)
    else:
        der_bytes = certificate
    dev = b64encode(der_bytes).decode()
    # certificate = certificate.decode()
    # dev = certificate.replace("-----BEGIN CERTIFICATE-----\n", '').replace(
    #     '\n-----END CERTIFICATE-----', ''
    # ).replace('\n', '')
    # print(dev)
    return dev


def CERT_FUNC(x):
    return pem_to_base64(x)


class TestValidateCertificates (unittest.TestCase):

    def setUp(self):
        self.path = "dfva_testdocument/files/certs/"
        self.experated = {
            # '539895508773': ('Carlos Alvarado Quesada', 1, True),
            # '02-4132-3596': ('José Rodríguez Zeledón', 4, False),
            # '166306239151': ('Juan Quirós Segura', 10, False),
            # '03-4685-3514': ('Mario Echandi Jiménez', 5, False),
            # '03-4562-5753': ('Óscar Arias', 4, False),
            # '08-2959-7760': ('Rafael Yglesias Castro', 7, False),

            '01-0001-0002': ('ANA ROJAS PRUEBA', 0, True),
            '199887755443': ('NARCISO CASCANTE PRUEBA', 0, True),

            '01-0001-0002exp': ('ANA ROJAS PRUEBA', 3, False),
            '199887755443exp': ('NARCISO CASCANTE PRUEBA', 3, False),

            '01-0001-0002rev': ('ANA ROJAS PRUEBA', 4, False),
            '199887755443rev': ('NARCISO CASCANTE PRUEBA', 4, False)
        }

    def make_validation(self, identification):
        cert = read_files('crt',  doc_path=self.path,
                          name=identification.replace("-", '')+".",
                          post_read_fn=CERT_FUNC)
        result = valclient.validate(cert, 'certificate')
        data = self.experated[identification]
        self.assertEqual(result['status'], data[1])
        if data[2]:
            self.assertEqual(result['full_name'], data[0])
            self.assertEqual(result['was_successfully'], data[2])

    # def test_certificado_ok(self):
    #     #         "04-0212-0119"
    #     cert = read_files('pem',  doc_path="dfva_testdocument/files/",
    #                       name="certificado.",
    #                       post_read_fn=CERT_FUNC)
    #     result = valclient.validate(cert, 'certificate')
    #     self.assertEqual(result['status'], 0)
    #     self.assertEqual(result['was_successfully'], True)

    def test_0100010002(self):
        self.make_validation("01-0001-0002")

    def test_199887755443(self):
        self.make_validation("199887755443")

    def test_0100010002exp(self):
        self.make_validation("01-0001-0002exp")

    def test_199887755443exp(self):
        self.make_validation("199887755443exp")

    def test_0100010002rev(self):
        self.make_validation("01-0001-0002rev")

    def test_199887755443rev(self):
        self.make_validation("199887755443rev")

    # def test_0829597760(self):
    #     self.make_validation("08-2959-7760")


class TestValidateDocuments(unittest.TestCase):
    def setUp(self):
        self.expected = {
            'cofirma': ("""527789139593,José María Montealegre Fernández
145764968887,José Figueres Ferrer
""", True, [23, 45, 21, 48, 12, 16]),
            'contrafirma': ("""09-2171-6656,Ascensión Esquivel Ibarra
08-9841-4375,Francisco Orlich Bolmarcich
""", True, [13, 24, 11, 80]),
            'msoffice': ("""06-5980-2076,Federico Tinoco Granados
01-4121-6048,Vicente Herrera Zeledón
""", True, [32, 47, 69, 36]),
            'odf': ("""04-2191-3685,Luis Monge Álvarez
06-2119-5314,José María Alfaro Zamora
""", True, [67, 51, 52, 53, 55]),
            'pdf': ("""01-2645-3949,Juan Mora Fernández
05-9062-3516,Rafael Calderón Fournier
""", True, [1]),
        }

    def get_list_names(self, namestr):
        dev = []
        for cedname in namestr.split("\n"):
            if cedname:
                ced, name = cedname.split(",")
                dev.append(ced)
        dev.sort()
        return dev

    def prepare_names(self, nameslist):
        dev = []
        for data in nameslist:
            # collectdata = {}
            if 'identification_number' in data:
                dev.append(data['identification_number'])
        dev.sort()
        return dev

    def extract_codes(self, codes):
        dev = []
        for data in codes:
            if 'code' in data:
                dev.append(int(data['code']))
        dev.sort()
        return dev

    def do_check(self, _format, filename):
        if _format in ['cofirma','contrafirma', 'pdf', 'odf', 'msoffice']:
            document = read_files(filename, post_read_fn=b64encode).decode()
        else:
            document = read_files(filename).decode()
        result = valclient.validate(document, 'document', _format=_format)
        extracted_errors = self.extract_codes(result['errors'])
        extracted_signers = self.prepare_names(result['signers'])

        # expected
        expected_signers = self.get_list_names(
            self.expected[_format][0])
        expected_errors = self.expected[_format][2]

        expected_errors.sort()
        expected_signers.sort()

        self.assertListEqual(extracted_signers,
                             expected_signers)
        self.assertListEqual(extracted_errors, expected_errors)
        self.assertEqual(self.expected[_format][1],
                         result['was_successfully'])

    def test_document_cofirma(self):
        self.do_check('cofirma', 'xml')

    def test_document_contrafirma(self):
        self.do_check('contrafirma', 'xml')

    def test_document_msoffice(self):
        self.do_check('msoffice', 'msoffice')

    def test_document_odf(self):
        self.do_check('odf', 'odf')

    def test_document_pdf(self):
        self.do_check('pdf', 'pdf')

