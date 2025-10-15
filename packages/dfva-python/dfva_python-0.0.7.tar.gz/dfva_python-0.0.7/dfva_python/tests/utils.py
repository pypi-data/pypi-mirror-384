import os
from base64 import b64encode

TIMEWAIT = 6
FORMAT_WAIT = 2
AUTH_WAIT = 0.5

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

AUTHENTICATION_RESPONSE_TABLE = {
    '500000000000':     (1, '=', 0, 0),
    '01-1919-2222':     (4, '=', 0, 0),
    '01-1919-2020':     (5, '=', 0, 0),
    '01-1919-2121':     (9, '=', 0, 0),
    '9-0000-0000-000':  (10, '=', 0, 0),
    # Con notificacion
    '100000000000':     (0, '!', 0, 1),
    '01-1010-2020':     (0, '!', 0, 2),
    '01-2020-3030':     (0, '!', 0, 3),
    '01-4040-5050':     (0, '!', 0, 4),
    '01-6060-7070':     (0, '!', 0, 9),
    '01-8080-9090':     (0, '!', 0, 10),
    '01-1100-2211':     (0, '!', 0, 11),
    '01-3344-5566':     (0, '!', 0, 13),
    '01-7788-9900':     (0, '!', 0, 14)
}

DOCUMENT_RESPONSE_TABLE = {
    # cedula    respuesta  comparacion   status   respuesta_notificacion
    "500000000000": (1, '!', 0, 0),
    "01-1919-2222": (4, '=', 0, 0),
    "01-1919-2020": (5, '=', 0, 0),
    "01-1919-2121": (9, '=', 0, 0),
    "9-0000-0000-000": (10, '=', 0, 0),
    # Con notificación
    '100000000000': (0, '!', 0, 1),
    '01-1010-2020': (0, '!', 0, 2),
    '01-2020-3030': (0, '!', 0, 3),
    '01-4040-5050': (0, '!', 0, 4),
    '01-6060-7070': (0, '!', 0, 9),
    '01-8080-9090': (0, '!', 0, 10),
    '01-1100-2211': (0, '!', 0, 11),
    '01-3344-5566': (0, '!', 0, 13),
    '01-7788-9900': (0, '!', 0, 14)
}

DOCUMENT_FORMATS = ['xml_cofirma', 'xml_contrafirma',
                    'odf', 'msoffice', 'pdf']


DOCUMENT_STAMP_CODE ={
    '1000': (0, '=', 0, 0),
    '1001': (1, '=', 0, 1),
    '1004': (4, '=', 0, 4),
    '1005': (5, '=', 0, 5),
    '1007': (7, '=', 0, 7),
    '1008': (8, '=', 0, 8),
}

def read_files(_format, doc_path="dfva_testdocument/files",
               post_read_fn=lambda x: x, name='test.'):
    defaultpath = os.path.join(os.path.dirname(BASE_DIR), doc_path)
    f = None
    fpath = None
    if _format in ['xml_cofirma', 'xml_contrafirma']:
        fpath = os.path.join(defaultpath, "test.xml")
    elif 'odf' == _format:
        fpath = os.path.join(defaultpath, "test.odt")
    elif 'msoffice' == _format:
        fpath = os.path.join(defaultpath, "test.docx")
    elif 'pdf' == _format:
        fpath = os.path.join(defaultpath, "test.pdf")
    else:
        fpath = os.path.join(defaultpath, name+_format)
    with open(fpath, 'rb') as arch:
        f = arch.read()
    return post_read_fn(f)
