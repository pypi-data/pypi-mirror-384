from .utils import DOCUMENT_FORMATS, DOCUMENT_RESPONSE_TABLE, \
    AUTHENTICATION_RESPONSE_TABLE


def build_authentication(name):
    print("""
class %s (unittest.TestCase):
    def setUp(self):
         pass

    def do_checks(self, identification):
         pass
""" % name)
    for identification in AUTHENTICATION_RESPONSE_TABLE:
        print("""
    def test_auth_%(identification_funcname)s(self):
        self.do_checks("%(identification)s")""" % {
            'identification': identification,
            'identification_funcname': identification.replace('-', '')})


def build_test_document_python(name):
    print("""
class %s (unittest.TestCase):
    def setUp(self):
         pass

    def do_checks(self, _format, identification):
         pass
""" % name)
    for _format in DOCUMENT_FORMATS:
        for identification in DOCUMENT_RESPONSE_TABLE:
            print("""
    def test_%(docformat)s_%(identification_funcname)s(self):
        self.do_checks("%(docformat)s", "%(identification)s")""" % {
                'docformat': _format, 'identification': identification,
                'identification_funcname': identification.replace('-', '')})
