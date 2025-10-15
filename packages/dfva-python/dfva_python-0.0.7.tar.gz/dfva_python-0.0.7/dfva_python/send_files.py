from dfva_python.client import Client


def read_files(fpath):
    with open(fpath, 'rb') as arch:
        f = arch.read()
    return f


client = Client()
doc1 = read_files("docs/test_1kb.pdf")
doc2 = read_files("docs/test_10kb.pdf")
doc3 = read_files("docs/test_100kb.pdf")
doc4 = read_files("docs/test_1mb.pdf")

respuesta = client.sign(
    "01-1010-2020",
    doc1,
    "test 1 kb",
    _format="pdf",
    reason="Test",
    place="algún lugar de la mancha"
)
print(respuesta)
res = client.sign_check(respuesta['id_transaction'])
print(res)

respuesta = client.sign(
    "01-1010-2020",
    doc1,
    "test 1 kb",
    _format="pdf",
    reason="Test",
    algorithm="sha384",
    place="algún lugar de la mancha"
)


respuesta = client.sign(
    "01-1010-2020",
    doc3,
    "test 100 kb",
    _format="pdf",
    reason="Test",
    place="algún lugar de la mancha"
)


respuesta = client.sign(
    "01-1010-2020",
    doc4,
    "test 1 mb",
    _format="pdf",
    reason="Test",
    place="algún lugar de la mancha"
)
