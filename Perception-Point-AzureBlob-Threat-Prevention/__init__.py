import logging
import azure.functions as func
import azure.storage.blob as blob_client
import os,sys
import requests
import json
from datetime import datetime,timedelta

PP_TOKEN = os.environ.get('PP_TOKEN','')
PP_ENV = os.environ.get('PP_ENV', 'us-east-1')
DICT_OF_ENV_URL_PREFIXES = {'us-east-1':'.','eu-west-1': '.eu.', 'testing': '.testing.','testing-ext': '.testing.'}
ENV_URL_PREFIX = DICT_OF_ENV_URL_PREFIXES.get(PP_ENV,'.')
IGNORE_MIMETYPES = [m.strip().lower() for m in
                     os.environ.get('IGNORE_MIMETYPES', default="application/x-directory").split(',')]
IGNORE_MIMETYPES = [m for m in IGNORE_MIMETYPES if m]


def logger(item_path=None):
        logPrefix = item_path if item_path else 'Unknown'
        logging.getLogger().handlers = []
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(f'"{logPrefix}"'+',%(levelname)s,%(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger


def send_url_to_perception_point(url, item_path):
    log = logging.getLogger()
    post_data = {
                "download_link": url,
                "name":os.path.basename(item_path),
                "original_file_path": item_path,
                "sub_origin": "s3"
    }
    log.debug('sending data to PP:{},{}'.format(str(post_data),ENV_URL_PREFIX))
    response = requests.post(
        "https://api{}perception-point.io/api/v1/files/".format(ENV_URL_PREFIX),
        data=post_data,
        headers={"Authorization": "Token {}".format(PP_TOKEN)},
    )
    if response.ok:
        log.debug("({}): {}".format(response.status_code, response.content))
    else:
        log.debug("URL: {} | response ({}): {}".format(url, response.status_code, response.content))


def main(event: func.InputStream):
    log = logger(event.name)
    log.debug('uri:{}\nname:{}\nproperties:{}\nmetadata:{}\n'.format(event.uri,event.name,event.blob_properties,event.metadata))
    mimetype = event.blob_properties['ContentType']
    item_path = event.name

    log.debug('File mimetype:{}'.format(mimetype))
    if mimetype and mimetype.lower() in IGNORE_MIMETYPES:
        log.debug("Skipped file with mimetype: {}".format(mimetype))
        sys.exit()
    if event.length == 0:
        log.debug("Skipped empty object.")
        sys.exit()

    expiry= datetime.utcnow() + timedelta(hours=1)
    storageData = dict(x.split("=",1) for x in os.environ['AZURE_STORAGE_CONNECTION_STRING'].split(";"))
    sasToken = blob_client.generate_blob_sas(storageData['AccountName'],
                                             item_path.split('/')[0],
                                             os.path.basename(item_path),
                                             expiry=expiry,
                                             permission="r",
                                             account_key=storageData['AccountKey']
                                            )
    log.debug('sastoken:{}'.format(sasToken))

    log.debug('Generating presigned URL for download {}'.format(item_path))
    url = '{}?{}'.format(event.uri,sasToken)
    send_url_to_perception_point(url, item_path)
