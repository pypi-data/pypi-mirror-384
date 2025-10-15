'''
Created on 2 nov. 2017

@author: luisza
'''

from time import sleep
from dfva_python.client import Client
c = Client()
"""
print("Authenticate:")
auth_resp = c.authenticate('04-0212-0119')
print(auth_resp)

auth_check_resp=c.authenticate_check(auth_resp['id_transaction'])
print(auth_check_resp)
print("\n\nSIGN:")
"""
DOCUMENT = '''IyEvYmluL2Jhc2gKCk5PRk9SQ0U9dHJ1ZQpBUFRfQ0FDSEU9IiIKCndoaWxlIGdldG9wdHMgY2h5
IG9wdGlvbgpkbwogY2FzZSAiJHtvcHRpb259IgogaW4KIHkpIE5PRk9SQ0U9ZmFsc2U7OwogYykg
QVBUX0NBQ0hFPXRydWU7OwogaCkgbXloZWxwCiAgICBleGl0IDAgOzsKIGVzYWMKZG9uZQoKaWYg
WyAkQVBUX0NBQ0hFIF07IHRoZW4gCiBlY2hvICJCSU5HTyIgCmZpCgo='''

stamp_resp=c.stamp(DOCUMENT.encode(), _format='xml_cofirma')
print(stamp_resp)
sleep(6)
stamp_check_resp=c.stamp_check(stamp_resp['id_transaction'])
print(stamp_check_resp)
stamp_delete = c.stamp_delete(stamp_resp['id_transaction'])
print(stamp_delete)

"""
sign_resp=c.sign( '04-0212-0119', DOCUMENT.encode(), "resumen ejemplo", _format='xml_cofirma')
print(sign_resp)
sign_check_resp=c.sign_check(sign_resp['id_transaction'])
print(sign_check_resp)

print("\n\nVALIDATE:")
validate_cert_resp=c.validate(DOCUMENT, 'certificate')
print(validate_cert_resp)
validate_doc_resp=c.validate(DOCUMENT, 'document', _format='cofirma')
print(validate_doc_resp)

print("\n\nIS connected:")
is_connect=c.is_suscriptor_connected('04-0212-0119')
print(is_connect)
"""
