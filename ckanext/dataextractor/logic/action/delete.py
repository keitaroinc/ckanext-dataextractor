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

# -*- coding: utf-8 -

try:
    # CKAN 2.7 and later
    from ckan.common import config
except ImportError:
    # CKAN 2.6 and earlier
    from pylons import config

import logging
import json
import ckan.logic as l
from ckan.common import _

from ckanext.dataextractor.lib import AzureStorageService

log = logging.getLogger(__name__)


def resource_filters_delete(context, data_dict):
    """Delete extract filters for a given resource.

    :param resource_id: id of the resource that filters should be deleted from.
    :type resource_id: string

    :param filters: list of filters i.e. ['electricity', 'date']
    :type filters: list

    :returns: resource object
    :rtype: dictionary
    """
    resource_id = l.get_or_bust(data_dict, 'resource_id')
    filters = data_dict.pop('filters')

    # Fetch available columns from the datastore and check against filters
    ds = l.get_action('datastore_info')(context, {'id': resource_id})

    # Loop through datastore schema and validate filters
    available_filters = map(lambda val: val.lower(), ds.get('schema').keys())
    for _f in filters:
        if _f.lower() not in available_filters:
            raise l.ValidationError(
                _('\'{0}\' filter type not supported. Supported types are: {1}'.format(
                    _f, available_filters
                ))
            )

    # Remove filters
    active_filters = l.get_action('active_resource_filters')(context, {'resource_id': resource_id})
    for _f in active_filters:
        if _f['name'] in filters:
            active_filters.remove(_f)

    payload = {'id': resource_id}
    payload.update({'filters': json.dumps(active_filters)})
    l.get_action('resource_patch')(context, payload)

    return l.get_action('resource_show')(context, {'id': resource_id})


def azure_blobs_delete(context, data_dict):
    """Delete all existing blobs on azure older than configured time.

    :returns: number of deleted blobs
    :rtype: integer
    """

    azure_storage = AzureStorageService()

    l.check_access('blobs_delete', context, data_dict)

    return azure_storage.blobs_delete()

