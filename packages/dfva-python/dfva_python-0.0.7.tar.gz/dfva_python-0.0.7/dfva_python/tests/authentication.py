import time
import unittest
from dfva_python.client import Client
from .utils import AUTHENTICATION_RESPONSE_TABLE, TIMEWAIT, AUTH_WAIT
import os

TEST_WITH_BCCR = os.getenv('TEST_WITH_BCCR', '') == 'True'
AUTH_ALLOWED_TEST = [] #["01-1100-2211"]

authtransactions = {}
authclient = Client()


def load_authentication():
    for identification in AUTHENTICATION_RESPONSE_TABLE.keys():
        if AUTH_ALLOWED_TEST and identification not in AUTH_ALLOWED_TEST:
            continue

        auth_resp = authclient.authenticate(identification)
        authtransactions[identification] = auth_resp
        eq = AUTHENTICATION_RESPONSE_TABLE[identification][1]
        idx = AUTHENTICATION_RESPONSE_TABLE[identification][2]
        if eq == '=':
            if auth_resp['id_transaction'] != idx:
                raise
        elif eq == '!':
            if auth_resp['id_transaction'] == idx:
                raise

        #time.sleep(AUTH_WAIT)


# def setUpModule():
#     print("AUTHENTICACION")
#     # load_authentication()
#     # time.sleep(TIMEWAIT)


class TestAuthentication (unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        load_authentication()
        time.sleep(TIMEWAIT)
        print("Recuerde modificar los archivos de configuración y registrar " +
              "la institución en dfva\n" +
              "export TEST_WITH_BCCR=True si se ejecuta con el BCCR")

    def do_checks(self, identification):
        if AUTH_ALLOWED_TEST and identification not in AUTH_ALLOWED_TEST:
            return
        if identification in ['500000000000',
                              '01-1919-2222',
                              '01-1919-2020',
                              '01-1919-2121',
                              '9-0000-0000-000']:
            self.assertEqual(AUTHENTICATION_RESPONSE_TABLE[identification][0],
                             authtransactions[identification]['status'])
            return
        res = authclient.authenticate_check(authtransactions[identification][
            'id_transaction'])
        self.assertEqual(AUTHENTICATION_RESPONSE_TABLE[identification][3],
                         res['status'])
        delauth = authclient.authenticate_delete(
            authtransactions[identification]['id_transaction'])
        self.assertEqual(delauth, True)

    def test_common_auth(self):
        # BCCR have not 88-8888-8888 identififcation
        if TEST_WITH_BCCR:
            return
        auth_resp = authclient.authenticate('88-8888-8888')
        self.assertEqual(auth_resp['status'], 0)
        self.assertNotEqual(auth_resp['id_transaction'], 0)
        authclient.authenticate_delete(auth_resp['id_transaction'])

    def test_auth_0119192020(self):
        self.do_checks("01-1919-2020")

    def test_auth_0111002211(self):
        self.do_checks("01-1100-2211")

    def test_auth_0177889900(self):
        self.do_checks("01-7788-9900")

    def test_auth_0133445566(self):
        self.do_checks("01-3344-5566")

    def test_auth_0160607070(self):
        self.do_checks("01-6060-7070")

    def test_auth_900000000000(self):
        self.do_checks("9-0000-0000-000")

    def test_auth_100000000000(self):
        self.do_checks("100000000000")

    def test_auth_0120203030(self):
        self.do_checks("01-2020-3030")

    def test_auth_0110102020(self):
        self.do_checks("01-1010-2020")

    def test_auth_500000000000(self):
        self.do_checks("500000000000")

    def test_auth_0119192222(self):
        self.do_checks("01-1919-2222")

    def test_auth_0140405050(self):
        self.do_checks("01-4040-5050")

    def test_auth_0180809090(self):
        self.do_checks("01-8080-9090")

    def test_auth_0119192121(self):
        self.do_checks("01-1919-2121")
