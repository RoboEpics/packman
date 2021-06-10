from django.conf import settings
from django.utils.crypto import get_random_string
from django.utils.module_loading import import_string

from fusionauth.fusionauth_client import FusionAuthClient

import boto3
from botocore.config import Config
from minio import Minio

from kubernetes import client, config

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from gitlab import Gitlab

from pydiscourse import DiscourseClient


def random_path() -> str:
    return get_random_string(10)


class Clients:
    fusionauth_client = FusionAuthClient(settings.FUSION_AUTH_API_KEY, settings.FUSION_AUTH_BASE_URL)

    queue_client = import_string(settings.QUEUE_CLIENT)(settings.QUEUE_SERVER_API_URL)

    s3_client = boto3.client('s3', endpoint_url=settings.S3_ENDPOINT_URL, aws_access_key_id=settings.S3_ACCESS_KEY_ID,
                             aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY, config=Config(signature_version='s3v4'))
    minio_client = Minio(settings.MINIO_STORAGE_ENDPOINT, settings.MINIO_STORAGE_ACCESS_KEY, settings.MINIO_STORAGE_SECRET_KEY)

    gitlab_client = Gitlab.from_config(gitlab_id=settings.GITLAB_ID, config_files=[settings.GITLAB_CONFIG_PATH])

    discourse_client = DiscourseClient(settings.DISCOURSE_HOST, settings.DISCOURSE_API_USERNAME, settings.DISCOURSE_API_KEY)

    @property
    def kubernetes_core(self):
        # Initialize a Core V1 kubernetes client each time this property is used
        # because the library deletes the SSL files after some time
        config.load_kube_config(settings.KUBERNETES_CONFIG_PATH)
        return client.CoreV1Api()

    @property
    def kubernetes_batch(self):
        # Initialize a Batch V1 kubernetes client each time this property is used
        # because the library deletes the SSL files after some time
        config.load_kube_config(settings.KUBERNETES_CONFIG_PATH)
        return client.BatchV1Api()

    @property
    def google_drive_client(self):
        credentials = Credentials.from_service_account_file(settings.GOOGLE_SERVICE_ACCOUNT_CREDENTIALS_PATH)
        return build('drive', 'v3', credentials=credentials, cache_discovery=False)
