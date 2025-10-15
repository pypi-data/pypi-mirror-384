import json
from dfva_python.crypto import encrypt, get_hash_sum, decrypt
from datetime import datetime
import requests
import pytz
from dfva_python.settings import Settings
import logging
from base64 import b64encode
import traceback
from dfva_python.jmeter_logger import add_jmetter_server

logger = logging.getLogger('dfva_python')


class MaxSizeException(Exception):
    pass


class InternalClient(object):
    def __init__(self, settings=Settings()):
        if not settings.SETTINGS_LOADED:
            settings.load_settings_from_file()
        self.settings = settings
        self.institution = settings.get_institution()
        self.tz = pytz.timezone(self.settings.TIMEZONE)

    def decrypt(self, data, algorithm):
        datahash = data['data_hash']
        data = decrypt(self.institution.private_key,
                       data['data'], as_str=False)
        newhash = get_hash_sum(data,  algorithm)
        if newhash != datahash:
            data = json.dumps({"code": "N/D",
                               "status": -2,
                               "identification": None,
                               "received_notification": None,
                               "status_text": "Problema: suma hash difiere"
                               }).encode()
        data = json.loads(data.decode())
        return data

    def authenticate(self, identification, algorithm=None):
        algorithm = algorithm or self.settings.ALGORITHM
        logger.info("Info authenticate: %s %r" % (identification, algorithm))
        data = {
            'institution': self.institution.code,
            'notification_url': self.institution.url_notify or 'N/D',
            'identification': identification,
            'request_datetime': datetime.now(self.tz).strftime("%Y-%m-%d %H:%M:%S"),
        }

        str_data = json.dumps(data)
        logger.debug("data authenticate: %s " % (str_data,))
        edata = encrypt(self.institution.server_public_key, str_data)
        hashsum = get_hash_sum(edata,  algorithm)
        edata = edata.decode()
        params = {
            "data_hash": hashsum,
            "algorithm": algorithm,
            "public_certificate": self.institution.public_certificate,
            'institution': self.institution.code,
            "data": edata,
        }

        url = self.settings.DFVA_SERVER_URL
        url += self.settings.AUTHENTICATE_INSTITUTION
        if self.settings.LOGGING_ENCRYPTED_DATA:
            logger.debug("Send authenticate: %s --> %r" % (url, params))
        if self.settings.BUILD_JMETER_TEST:
            add_jmetter_server(self.settings, "Authenticate_"+identification, url, params)
        result = requests.post(
            url, json=params)
#        with open('/tmp/index.html', 'wb') as arch:
#            arch.write(result.content)
        data = result.json()
        if self.settings.LOGGING_ENCRYPTED_DATA:
            logger.debug("Received authenticate: %r" % (data,))
        data = self.decrypt(data,  algorithm)
        logger.debug("Decrypted authenticate: %r" % (data,))
        return data

    def authenticate_check(self, code, algorithm=None):
        algorithm = algorithm or self.settings.ALGORITHM
        logger.info("check authenticate:   %r %r" % (code, algorithm))
        data = {
            'institution': self.institution.code,
            'notification_url': self.institution.url_notify or 'N/D',
            'request_datetime': datetime.now(self.tz).strftime("%Y-%m-%d %H:%M:%S"),
        }

        str_data = json.dumps(data)
        logger.debug("Data check authenticate: %s " % (str_data,))
        edata = encrypt(self.institution.server_public_key, str_data)
        hashsum = get_hash_sum(edata,  algorithm)
        edata = edata.decode()
        params = {
            "data_hash": hashsum,
            "algorithm": algorithm,
            "public_certificate": self.institution.public_certificate,
            'institution': self.institution.code,
            "data": edata,
        }

        url = self.settings.DFVA_SERVER_URL + \
            self.settings.CHECK_AUTHENTICATE_INSTITUTION % (code,)
        if self.settings.LOGGING_ENCRYPTED_DATA:
            logger.debug("Send check authenticate: %s --> %r" % (url, params))
        else:
            logger.debug("Send check authenticate: %s" % (url,))
        result = requests.post(
            url, json=params)

        data = result.json()
        if self.settings.LOGGING_ENCRYPTED_DATA:
            logger.debug("Received check authenticate: %r" % (data,))
        data = self.decrypt(data,  algorithm)
        logger.debug("Decrypted check authenticate: %r" % (data,))
        return data

    def authenticate_delete(self, code, algorithm=None):
        algorithm = algorithm or self.settings.ALGORITHM
        logger.info("Delete authenticate: %r %r" % (code, algorithm))
        data = {
            'institution': self.institution.code,
            'notification_url': self.institution.url_notify or 'N/D',
            'request_datetime': datetime.now(self.tz).strftime("%Y-%m-%d %H:%M:%S"),
        }

        str_data = json.dumps(data)
        logger.debug("Data delete authenticate: %s " % (str_data,))
        edata = encrypt(self.institution.server_public_key, str_data)
        hashsum = get_hash_sum(edata,  algorithm)
        edata = edata.decode()
        params = {
            "data_hash": hashsum,
            "algorithm": algorithm,
            "public_certificate": self.institution.public_certificate,
            'institution': self.institution.code,
            "data": edata,
        }
        url = self.settings.DFVA_SERVER_URL + \
            self.settings.AUTHENTICATE_DELETE % (code,)
        if self.settings.LOGGING_ENCRYPTED_DATA:
            logger.debug("Send delete authenticate: %s --> %r" % (url, params))
        else:
            logger.debug("Send delete authenticate: %s" % (url, ))
        result = requests.post(
            url, json=params)

        data = result.json()
        if self.settings.LOGGING_ENCRYPTED_DATA:
            logger.debug("Received delete authenticate: %r" % (data,))
        data = self.decrypt(data,  algorithm)
        logger.debug("Decrypted delete authenticate: %r" % (data,))
        return data['result'] if 'result' in data else False

    def sign(self, identification,
             document, resume, _format='xml_cofirma', algorithm=None,
             place=None, reason=None):
        algorithm = algorithm or self.settings.ALGORITHM
        logger.info("Info sign: %s %s %s %r" % (identification, resume,
                                                _format, algorithm))
        if type(document) == str:
            document = document.encode()
        b64document = b64encode(document).decode()
        data = {
            'institution': self.institution.code,
            'notification_url': self.institution.url_notify or 'N/D',
            'document': b64document,
            'format': _format,
            'algorithm_hash': algorithm,
            'document_hash': get_hash_sum(document,  algorithm, b64=True),
            'identification': identification,
            'resumen': resume,
            'request_datetime': datetime.now(self.tz).strftime("%Y-%m-%d %H:%M:%S"),
        }
        if _format == 'pdf':
            data['reason'] = reason
            data['place'] = place

        str_data = json.dumps(data)
        logger.debug("Data sign: %s " % (str_data,))
        edata = encrypt(self.institution.server_public_key, str_data)
        hashsum = get_hash_sum(edata,  algorithm)
        edata = edata.decode()
        params = {
            "data_hash": hashsum,
            "algorithm": algorithm,
            "public_certificate": self.institution.public_certificate,
            'institution': self.institution.code,
            "data": edata,
        }

        headers = {'Accept': 'application/json',
                   'Content-Type': 'application/json'}

        url = self.settings.DFVA_SERVER_URL + self.settings.SIGN_INSTUTION
        if self.settings.LOGGING_ENCRYPTED_DATA:
            logger.debug("Send sign: %s --> %r" % (url, params))
        if self.settings.BUILD_JMETER_TEST:
            add_jmetter_server(self.settings, "Sign_"+_format+"_"+identification, url, params)

        result = requests.post(
            url, json=params, headers=headers)

        if result.status_code not in [200, 201]:
            logger.error("Código de error %r"%result.status_code)
            logger.error(result.content)
        if result.status_code == 413:
            raise MaxSizeException("Documento tiene un tamaño mayor al soportado")
        data = result.json()
        if self.settings.LOGGING_ENCRYPTED_DATA:
            logger.debug("Received sign: %r" % (data,))
        data = self.decrypt(data,  algorithm)
        logger.debug("Decrypted sign: %r" % (data,))

        return data

    def sign_check(self, code, algorithm=None):
        algorithm = algorithm or self.settings.ALGORITHM
        logger.info("check sign:  %r %r" % (code, algorithm))
        data = {
            'institution': self.institution.code,
            'notification_url': self.institution.url_notify or 'N/D',
            'request_datetime': datetime.now(self.tz).strftime("%Y-%m-%d %H:%M:%S"),
        }

        str_data = json.dumps(data)
        logger.debug("Data check sign: %s " % (str_data,))
        edata = encrypt(self.institution.server_public_key, str_data)
        hashsum = get_hash_sum(edata,  algorithm)
        edata = edata.decode()
        params = {
            "data_hash": hashsum,
            "algorithm": algorithm,
            "public_certificate": self.institution.public_certificate,
            'institution': self.institution.code,
            "data": edata,
        }
        url = self.settings.DFVA_SERVER_URL + \
            self.settings.CHECK_SIGN_INSTITUTION % (code,)
        if self.settings.LOGGING_ENCRYPTED_DATA:
            logger.debug("Send check sign: %s --> %r" % (url, params))
        else:
            logger.debug("Send check sign: %s" % (url,))
        result = requests.post(url, json=params)
        data = result.json()
        if self.settings.LOGGING_ENCRYPTED_DATA:
            logger.debug("Received check sign: %r" % (data,))
        data = self.decrypt(data,  algorithm)
        logger.debug("Decrypted check sign: %r" % (data,))
        return data

    def sign_delete(self, code, algorithm=None):
        algorithm = algorithm or self.settings.ALGORITHM
        logger.info("Delete sign: %r %r" % (code, algorithm))
        data = {
            'institution': self.institution.code,
            'notification_url': self.institution.url_notify or 'N/D',
            'request_datetime': datetime.now(self.tz).strftime(
                "%Y-%m-%d %H:%M:%S"),
        }

        str_data = json.dumps(data)
        logger.debug("Data delete sign: %s " % (str_data,))
        edata = encrypt(self.institution.server_public_key, str_data)
        hashsum = get_hash_sum(edata,  algorithm)
        edata = edata.decode()
        params = {
            "data_hash": hashsum,
            "algorithm": algorithm,
            "public_certificate": self.institution.public_certificate,
            'institution': self.institution.code,
            "data": edata,
        }
        url = self.settings.DFVA_SERVER_URL + \
            self.settings.SIGN_DELETE % (code,)
        if self.settings.LOGGING_ENCRYPTED_DATA:
            logger.debug("Send delete sign: %s --> %r" % (url, params))
        else:
            logger.debug("Send delete sign: %s" % (url, ))
        result = requests.post(url, json=params)

        data = result.json()
        if self.settings.LOGGING_ENCRYPTED_DATA:
            logger.debug("Received delete sign: %r" % (data,))
        data = self.decrypt(data,  algorithm)
        logger.debug("Decrypted delete sign: %r" % (data,))
        return data['result'] if 'result' in data else False

    def stamp(self, document, _format='xml_cofirma', algorithm=None,
             place=None, reason=None, eta=None, id_functionality=-1):
        algorithm = algorithm or self.settings.ALGORITHM
        logger.info("Info Stamp:  %s %r" % (_format, algorithm))
        if type(document) == str:
            document = document.encode()
        b64document = b64encode(document).decode()
        data = {
            'institution': self.institution.code,
            'notification_url': self.institution.url_notify or 'N/D',
            'document': b64document,
            'format': _format,
            'algorithm_hash': algorithm,
            'id_functionality': id_functionality,
            'document_hash': get_hash_sum(document,  algorithm, b64=True),
            'request_datetime': datetime.now(self.tz).strftime("%Y-%m-%d %H:%M:%S"),
        }
        if _format == 'pdf':
            data['reason'] = reason
            data['place'] = place
        if eta:
            data['eta'] = eta.strftime("%Y-%m-%d %H:%M:%S")

        str_data = json.dumps(data)
        logger.debug("Data stamp: %s " % (str_data,))
        edata = encrypt(self.institution.server_public_key, str_data)
        hashsum = get_hash_sum(edata,  algorithm)
        edata = edata.decode()
        params = {
            "data_hash": hashsum,
            "algorithm": algorithm,
            "public_certificate": self.institution.public_certificate,
            'institution': self.institution.code,
            "data": edata,
        }

        headers = {'Accept': 'application/json',
                   'Content-Type': 'application/json'}

        url = self.settings.DFVA_SERVER_URL + self.settings.STAMP_INSTUTION
        if self.settings.LOGGING_ENCRYPTED_DATA:
            logger.debug("Send stamp: %s --> %r" % (url, params))
        if self.settings.BUILD_JMETER_TEST:
            add_jmetter_server(self.settings, "Stamp_"+_format, url, params)

        result = requests.post(
            url, json=params, headers=headers)

        if result.status_code not in [200, 201]:
            logger.error("Código de error %r"%result.status_code)
            logger.error(result.content)
        if result.status_code == 413:
            raise MaxSizeException("Documento tiene un tamaño mayor al soportado")
        data = result.json()
        if self.settings.LOGGING_ENCRYPTED_DATA:
            logger.debug("Received stamp: %r" % (data,))
        data = self.decrypt(data,  algorithm)
        logger.debug("Decrypted stamp: %r" % (data,))

        return data

    def stamp_check(self, code, algorithm=None):
        algorithm = algorithm or self.settings.ALGORITHM
        logger.info("check stamp:  %r %r" % (code, algorithm))
        data = {
            'institution': self.institution.code,
            'notification_url': self.institution.url_notify or 'N/D',
            'request_datetime': datetime.now(self.tz).strftime("%Y-%m-%d %H:%M:%S"),
        }

        str_data = json.dumps(data)
        logger.debug("Data check stamp: %s " % (str_data,))
        edata = encrypt(self.institution.server_public_key, str_data)
        hashsum = get_hash_sum(edata,  algorithm)
        edata = edata.decode()
        params = {
            "data_hash": hashsum,
            "algorithm": algorithm,
            "public_certificate": self.institution.public_certificate,
            'institution': self.institution.code,
            "data": edata,
        }
        url = self.settings.DFVA_SERVER_URL + \
            self.settings.CHECK_STAMP_INSTITUTION % (code,)
        if self.settings.LOGGING_ENCRYPTED_DATA:
            logger.debug("Send check stamp: %s --> %r" % (url, params))
        else:
            logger.debug("Send check stamp: %s" % (url,))
        result = requests.post(url, json=params)
        data = result.json()
        if self.settings.LOGGING_ENCRYPTED_DATA:
            logger.debug("Received check stamp: %r" % (data,))
        data = self.decrypt(data,  algorithm)
        logger.debug("Decrypted check stamp: %r" % (data,))
        return data

    def stamp_delete(self, code, algorithm=None):
        algorithm = algorithm or self.settings.ALGORITHM
        logger.info("Delete stamp: %r %r" % (code, algorithm))
        data = {
            'institution': self.institution.code,
            'notification_url': self.institution.url_notify or 'N/D',
            'request_datetime': datetime.now(self.tz).strftime(
                "%Y-%m-%d %H:%M:%S"),
        }

        str_data = json.dumps(data)
        logger.debug("Data delete stamp: %s " % (str_data,))
        edata = encrypt(self.institution.server_public_key, str_data)
        hashsum = get_hash_sum(edata,  algorithm)
        edata = edata.decode()
        params = {
            "data_hash": hashsum,
            "algorithm": algorithm,
            "public_certificate": self.institution.public_certificate,
            'institution': self.institution.code,
            "data": edata,
        }
        url = self.settings.DFVA_SERVER_URL + \
            self.settings.STAMP_DELETE % (code,)
        if self.settings.LOGGING_ENCRYPTED_DATA:
            logger.debug("Send delete stamp: %s --> %r" % (url, params))
        else:
            logger.debug("Send delete stamp: %s" % (url, ))
        result = requests.post(url, json=params)

        data = result.json()
        if self.settings.LOGGING_ENCRYPTED_DATA:
            logger.debug("Received delete stamp: %r" % (data,))
        data = self.decrypt(data,  algorithm)
        logger.debug("Decrypted delete stamp: %r" % (data,))
        return data['result'] if 'result' in data else False

    def validate(self, document, _type, algorithm=None, _format=None):
        algorithm = algorithm or self.settings.ALGORITHM
        logger.info("Validate:  %r %r %r" % (_type, _format, algorithm))
        data = {
            'institution': self.institution.code,
            'notification_url': self.institution.url_notify or 'N/D',
            'document': document,
            'request_datetime': datetime.now(self.tz).strftime(
                "%Y-%m-%d %H:%M:%S"),
        }

        if _format is not None:
            data['format'] = _format

        str_data = json.dumps(data)
        logger.debug("Data Validate: %s " % (str_data,))
        edata = encrypt(self.institution.server_public_key, str_data)
        hashsum = get_hash_sum(edata,  algorithm)
        edata = edata.decode()
        params = {
            "data_hash": hashsum,
            "algorithm": algorithm,
            "public_certificate": self.institution.public_certificate,
            'institution': self.institution.code,
            "data": edata,
        }

        if _type == 'certificate':
            url = self.settings.VALIDATE_CERTIFICATE
        else:
            url = self.settings.VALIDATE_DOCUMENT
        headers = {'Accept': 'application/json',
                   'Content-Type': 'application/json'}

        url = self.settings.DFVA_SERVER_URL + url
        if self.settings.BUILD_JMETER_TEST:
            add_jmetter_server(self.settings, "Validate_"+_type, url, params)
        if self.settings.LOGGING_ENCRYPTED_DATA:
            logger.debug("Send validate: %s --> %r" % (url, params))
        else:
            logger.debug("Send validate: %s" % (url,))
        result = requests.post(url, json=params, headers=headers)
        data = result.json()
        if self.settings.LOGGING_ENCRYPTED_DATA:
            logger.debug("Received validate: %r" % (data,))
        data = self.decrypt(data,  algorithm)
        logger.debug("Decrypted validate: %r" % (data,))
        return data

    def is_suscriptor_connected(self, identification, algorithm=None):
        algorithm = algorithm or self.settings.ALGORITHM
        logger.info("Suscriptor connected: %s %r" %
                    (identification, algorithm))
        data = {
            'institution': self.institution.code,
            'notification_url': self.institution.url_notify or 'N/D',
            'identification': identification,
            'request_datetime': datetime.now(self.tz).strftime(
                "%Y-%m-%d %H:%M:%S"),
        }
        str_data = json.dumps(data)
        logger.debug("Suscriptor connected: %s " % (str_data,))
        edata = encrypt(self.institution.server_public_key, str_data)
        hashsum = get_hash_sum(edata,  algorithm)
        edata = edata.decode()
        params = {
            "data_hash": hashsum,
            "algorithm": algorithm,
            "public_certificate": self.institution.public_certificate,
            'institution': self.institution.code,
            "data": edata,
        }
        url = self.settings.DFVA_SERVER_URL + \
            self.settings.SUSCRIPTOR_CONNECTED
        if self.settings.LOGGING_ENCRYPTED_DATA:
            logger.debug("Send Suscriptor connected: %s --> %r" %
                         (url, params))
        result = requests.post(url, json=params)

        data = result.json()
        logger.debug("Received Suscriptor connected: %r" % (data,))
        dev = False
        if 'is_connected' in data:
            dev = data['is_connected']
        return dev

    def get_notify_data(self, data):
        if self.settings.LOGGING_ENCRYPTED_DATA:
            logger.debug("notify: %r" % (data,))
        data = self.decrypt(data,  self.settings.ALGORITHM)
        logger.debug("Notify decrypted: %r" % (data,))
        return data


class Client(InternalClient):
    def __init__(self, settings=Settings()):
        super(Client, self).__init__(settings=settings)
        self.error_sign_auth_data = {
            "code": "N/D",
            "status": 2,
            "identification": None,
            "id_transaction": 0,
            "request_datetime": "",
            "signed_document": "",
            "expiration_datetime": "",
            "received_notification": True,
            "duration": 0,
            "status_text": "Problema de comunicación interna"
        }

        self.error_validate_data = {
            "code": "N/D",
            "status": 2,
            "identification": None,
            "received_notification": None,
            "status_text": "Problema de comunicación interna"
        }
        self.error_stamp_data = {
            "status": 2,
            "id_transaction": 0,
            "request_datetime": "",
            "signed_document": "",
            "expiration_datetime": "",
            "received_notification": True,
            "duration": 0,
            "status_text": "Problema de comunicación interna"
        }
    def authenticate(self, identification, algorithm=None):
        try:
            dev = super(Client, self).authenticate(identification,
                                                   algorithm=algorithm)
        except Exception as e:
            logger.error("authenticate %r" % (e), exc_info=True)
            dev = self.error_sign_auth_data

        return dev

    def authenticate_check(self, code, algorithm=None):
        try:
            dev = super(Client, self).authenticate_check(code,
                                                         algorithm=algorithm)
        except Exception as e:
            logger.error("authenticate check %r" % (e), exc_info=True)
            dev = self.error_sign_auth_data

        return dev

    def authenticate_delete(self, code, algorithm=None):
        try:
            dev = super(Client, self).authenticate_delete(code,
                                                          algorithm=algorithm)
        except Exception as e:
            logger.error("authenticate delete %r" % (e), exc_info=True)
            dev = False

        return dev

    def sign(self, identification, document, resume, _format='xml_cofirma',
             algorithm=None, place=None, reason=None):
        if _format not in self.settings.SUPPORTED_SIGN_FORMAT:
            return {
                "code": "N/D",
                "status": 12,
                "identification": None,
                "id_transaction": 0,
                "request_datetime": "",
                "signed_document": "",
                "expiration_datetime": "",
                "received_notification": True,
                "duration": 0,
                "status_text": "Formato de documento inválido, posibles:" +
                ",".join(self.settings.SUPPORTED_SIGN_FORMAT)
            }
        if _format == 'pdf' and (reason is None or place is None):
            return {
                "code": "N/D",
                "status": 13,
                "identification": None,
                "id_transaction": 0,
                "request_datetime": "",
                "signed_document": "",
                "expiration_datetime": "",
                "received_notification": True,
                "duration": 0,
                "status_text": "Firma pdf sin lugar o razón de firma"
            }
        try:
            dev = super(Client, self).sign(identification,
                                           document, resume, _format=_format,
                                           algorithm=algorithm,
                                           place=place, reason=reason)
        except MaxSizeException as me:
            return {
                "code": "N/D",
                "status": 14,
                "identification": None,
                "id_transaction": 0,
                "request_datetime": "",
                "signed_document": "",
                "expiration_datetime": "",
                "received_notification": True,
                "duration": 0,
                "status_text": "El documento es demasiado grande para ser procesado"
            }
        except Exception as e:
            logger.error("Sign %r" % (e), exc_info=True)
            dev = self.error_sign_auth_data

        return dev

    def sign_check(self, code, algorithm=None):
        try:
            dev = super(Client, self).sign_check(code, algorithm=algorithm)
        except Exception as e:
            logger.error("Sign check %r" % (e), exc_info=True)
            dev = self.error_sign_auth_data
        return dev

    def sign_delete(self, code, algorithm=None):
        try:
            dev = super(Client, self).sign_delete(code, algorithm=algorithm)
        except Exception as e:
            logger.error("Sign delete %r" % (e))
            dev = False
        return dev

    def stamp(self, document, _format='xml_cofirma',
             algorithm=None, place=None, reason=None, id_functionality=-1, eta=None):
        if _format not in self.settings.SUPPORTED_SIGN_FORMAT:
            return {
                "status": 12,
                "id_transaction": 0,
                "request_datetime": "",
                "signed_document": "",
                "expiration_datetime": "",
                "received_notification": True,
                "duration": 0,
                "id_functionality": id_functionality,
                "status_text": "Formato de documento inválido, posibles:" +
                ",".join(self.settings.SUPPORTED_SIGN_FORMAT)
            }
        if _format == 'pdf' and (reason is None or place is None):
            return {
                "status": 13,
                "id_transaction": 0,
                "request_datetime": "",
                "signed_document": "",
                "expiration_datetime": "",
                "received_notification": True,
                "duration": 0,
                "id_functionality": id_functionality,
                "status_text": "Firma pdf sin lugar o razón de firma"
            }
        try:
            dev = super(Client, self).stamp(document, _format=_format, algorithm=algorithm, eta=eta,
                                           id_functionality=id_functionality, place=place, reason=reason)
        except MaxSizeException as me:
            return {

                "status": 14,
                "identification": None,
                "id_transaction": 0,
                "request_datetime": "",
                "signed_document": "",
                "expiration_datetime": "",
                "received_notification": True,
                "id_functionality": id_functionality,
                "duration": 0,
                "status_text": "El documento es demasiado grande para ser procesado"
            }
        except Exception as e:
            logger.error("Stamp %r" % (e), exc_info=True)
            dev = self.error_stamp_data

        return dev

    def stamp_check(self, code, algorithm=None):
        try:
            dev = super(Client, self).stamp_check(code, algorithm=algorithm)
        except Exception as e:
            logger.error("Stamp check %r" % (e), exc_info=True)
            dev = self.error_stamp_data
        return dev

    def stamp_delete(self, code, algorithm=None):
        try:
            dev = super(Client, self).stamp_delete(code, algorithm=algorithm)
        except Exception as e:
            logger.error("Stamp delete %r" % (e))
            dev = False
        return dev

    def validate(self, document, _type, algorithm=None, _format=None):
        if _format is not None and _format not in \
                self.settings.SUPPORTED_VALIDATE_FORMAT:
            return {"code": "N/D",
                    "status": 14,
                    "identification": None,
                    "received_notification": None,
                    "status_text": "Formato inválido posibles: " +
                    ",".join(self.settings.SUPPORTED_VALIDATE_FORMAT)
                    }
        try:
            dev = super(Client, self).validate(document, _type,
                                               algorithm=algorithm,
                                               _format=_format)
        except Exception as e:
            logger.error("Validate %r" % (e), exc_info=True)
            dev = self.error_validate_data

        return dev

    def is_suscriptor_connected(self, identification, algorithm=None):
        try:
            dev = super(Client, self).is_suscriptor_connected(
                identification,
                algorithm=algorithm)
        except Exception as e:
            logger.error("Suscriptor connected %r" % (e), exc_info=True)
            dev = False

        return dev

    def get_notify_data(self, data):
        dev = {}
        try:
            dev = super(Client, self).get_notify_data(data)
        except Exception as e:
            logger.error("Notify data %r" % (e), exc_info=True)

        return dev
