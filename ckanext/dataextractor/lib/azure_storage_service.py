"""
Copyright (c) 2018 Keitaro AB

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import logging
import uuid
from datetime import datetime


try:
    # CKAN 2.7 and later
    from ckan.common import config
except ImportError:
    # CKAN 2.6 and earlier
    from pylons import config


from azure.storage.blob import BlockBlobService

log = logging.getLogger(__name__)


class AzureStorageService():

    def __init__(self):

        self.account_name = config.get('ckanext.dataextractor.azure_storage_account_name', None)
        self.account_key = config.get('ckanext.dataextractor.azure_storage_account_key', None)
        self.container_name = config.get('ckanext.dataextractor.azure_storage_container_name', None)
        self.blob_expiration_days = config.get('ckanext.dataextractor.blob_expiration_days', 10)

        if not self.account_name or not self.account_key or not self.container_name:
            raise ValueError('azure_storage_account_name, azure_storage_account_key, '
                             'azure_storage_container_name')

        self.service = BlockBlobService(account_name=self.account_name,
                                        account_key=self.account_key)


    def _get_blob_reference(self, prefix, format):
        prefix = prefix.replace('/', '')
        return '{}{}.{}'.format(prefix + '-', str(uuid.uuid4()).replace('-', ''), format.lower())


    def blob_create(self, stream, format, resource_name):

        blob_name = self._get_blob_reference(resource_name,format)
        self.service.create_blob_from_stream(self.container_name, blob_name, stream)
        blob_url = self.service.make_blob_url(self.container_name, blob_name)

        return blob_url

    def blobs_delete(self):

         blobs = self.service.list_blobs(self.container_name)
         blobs_deleted = 0

         for blob in blobs:
             time_diff = datetime.now() - blob.properties.last_modified.replace(tzinfo=None)
             if time_diff.days >= int(self.blob_expiration_days):
                 blobs_deleted += 1
                 self.service.delete_blob(self.container_name, blob.name)

         return blobs_deleted




