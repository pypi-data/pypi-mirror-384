dfva cliente para python
#############################

Este cliente permite comunicarse con DFVA_ para proveer servicios de firma digital para Costa Rica a institutiones.

.. _DFVA: https://github.com/luisza/dfva

Instalación y configuración
--------------------------------

Instale mediante pypi:

.. code:: bash

    pip install dfva-python

También se puede instalar utilizando el código fuente

.. code:: bash

   git clone https://github.com/luisza/dfva_python.git
   cd dfva_python
   python setup.py install

Adicionalmente se crea un archivo de configuración en $HOME/.dfva_python/client.conf donde se ingresan los datos de la institución, una buena forma de crear este archivo es:

.. code:: python

   python 
   >>> from dfva_python.settings import Settings
   >>> settings=Settings()
   # a este punto ya se ha creado el archivo de configuración, 
   #pero puede ser de utilidad modificar las propiedades de la 
   # institución así
   >>> settings.PRIVATE_KEY=''
   >>> settings.SERVER_PUBLIC_KEY=''
   >>> settings.PUBLIC_CERTIFICATE=''
   >>> settings.CODE=''
   >>> settings.URL_NOTIFY='N/D'
   >>> settings.save()  

Modo de uso 
################

Este cliente permite:

* Autenticar personas y verificar estado de autenticación
* Firmar documento xml, odf, ms office y verificar estado de firma durante el tiempo que el usuario está firmando
* Validar un certificado emitido con la CA nacional de Costa Rica provista por el BCCR
* Validar un documento XML firmado.
* Revisar si un suscriptor está conectado.


Ejemplo de uso
----------------

**Nota:** notificationURL debe estar registrado en dfva o ser N/D en clientes no web

Si se desea autenticar y revisar estado de la autenticación

.. code:: python

    from dfva_python.client import Client
    client = Client()
    auth_resp = client.authenticate('04-0212-0119')
    print(auth_resp)
    client.authenticate_check(auth_resp['id_transaction'])
    # eliminando la peticion
    client.authenticate_delete(auth_resp['id_transaction'])


Si se desea revisar si un suscriptor está conectado

.. code:: python

    client.is_suscriptor_connected('04-0777-08888')


Si se desea firmar y revisar estado de la firma.

.. code:: python

    DOCUMENT = '''IyEvYmluL2Jhc2gKCk5PRk9SQ0U9dHJ1ZQpBUFRfQ0FDSEU9IiIKCndoaWxlIGdldG9wdHMgY2h5
    IG9wdGlvbgpkbwogY2FzZSAiJHtvcHRpb259IgogaW4KIHkpIE5PRk9SQ0U9ZmFsc2U7OwogYykg
    QVBUX0NBQ0hFPXRydWU7OwogaCkgbXloZWxwCiAgICBleGl0IDAgOzsKIGVzYWMKZG9uZQoKaWYg
    WyAkQVBUX0NBQ0hFIF07IHRoZW4gCiBlY2hvICJCSU5HTyIgCmZpCgo='''

    sign_resp=client.sign( '04-0212-0119', DOCUMENT.encode(), "resumen ejemplo", _format='xml_cofirma')
    # _format puede ser xml_cofirma, xml_contrafirma, odf, msoffice
    print(sign_resp)
    client.sign_check(sign_resp['id_transaction'])
    # eliminando la peticion
    client.sign_delete(auth_resp['id_transaction'])

**Nota:** La revisión de estado de la autenticación/firma no es necesaria en servicios web ya que estos son notificados por en la URL de institución proporcionado.

Si se desea validar un certificado

.. code:: python

    client.validate(DOCUMENT, 'certificate')
    

Si se desea validar un documento

.. code:: python

    client.validate(DOCUMENT, 'document', 'cofirma')
    # cofirma, contrafirma, odf, msoffice, pdf


Running tests
----------------

Necesita instalar el gestor de pruebas 

.. code:: python

    pip install nose


Ejecute el simulador de FVA BCCR  y su cliente de celery

EN FVA BCCR ejecute 

.. code:: bash

    python manage.py runserver 8001
    celery  -A fva_bccr worker  -l info

Puede ejecutar además celery beat  para mayor exactitud, 
('''celery  -A fva_bccr worker -BE -l info'''), aunque puede causar inestabilidad
en las pruebas.  También es importante acceder a http://localhost:8001/admin/constance/config/
y habilitar `USE_UNITEST` para que no espere el `TASK_WAIT_TO_RESPONSE`  definido o 
poner un `TASK_WAIT_TO_RESPONSE`  bajo como 1 segundo.



Por último ejecute las pruebas

.. code:: bash

    nosetests -v --nocapture dfva_python.tests


Además se incluye un utilitario para generar las combinaciones de las pruebas
con la finalidad de hacer más simple la codificación de los diferentes casos

.. code:: python

    from dfva_python.utils_test import build_test_document_python
    build_test_document_python("TestAuthenticate")


Esto podría ser util para correr las pruebas cuando se conecta a BCCR

.. code:: bash

    export REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
    export TEST_WITH_BCCR=True
