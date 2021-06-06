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

SELECTED_LOG_LEVEL = os.environ.get('LOG_LEVEL', 'info')
LOG_LEVELS = {'info':logging.INFO,'warning': logging.WARNING, 'error': logging.ERROR, 'debug':logging.DEBUG}
CURRENT_LOG_LEVEL = LOG_LEVELS.get(SELECTED_LOG_LEVEL, '')


def logger(item_path=None):
        logPrefix = item_path if item_path else 'Unknown'
        logging.getLogger().handlers = []
        logger = logging.getLogger()
        logger.setLevel(CURRENT_LOG_LEVEL)
        handler = logging.StreamHandler()
        handler.setLevel(CURRENT_LOG_LEVEL)
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
                "callback_params":json.dumps({
                                              "azure_account_id":'?????',
                                              "queue_region":'?????'
                                   }),
                "sub_origin": "s3"
    }
    log.debug('sending data to PP:{},{}'.format(str(post_data),ENV_URL_PREFIX))
    response = requests.post(
        "https://api{}perception-point.io/api/v1/files/".format(ENV_URL_PREFIX),
        data=post_data,
        headers={"Authorization": "Token {}".format(PP_TOKEN)},
    )
    if response.ok:
        log.info("({}): {}".format(response.status_code, response.content))
    else:
        log.error("URL: {} | response ({}): {}".format(url, response.status_code, response.content))


def main(item: func.InputStream):
    log = logger(item.name)
    log.info('uri:{}\nname:{}\nproperties:{}\nmetadata:{}\n'.format(item.uri,item.name,item.blob_properties,item.metadata))
    mimetype = item.blob_properties['ContentType']
    item_path = item.name

    log.debug('File mimetype:{}'.format(mimetype))
    if mimetype and mimetype.lower() in IGNORE_MIMETYPES:
        log.info("Skipped file with mimetype: {}".format(mimetype))
        sys.exit()
    if item.length == 0:
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
    log.info('sastoken:{}'.format(sasToken))

    log.debug('Generating presigned URL for download {}'.format(item_path))
    url = '{}?{}'.format(item.uri,sasToken)
    send_url_to_perception_point(url, item_path)