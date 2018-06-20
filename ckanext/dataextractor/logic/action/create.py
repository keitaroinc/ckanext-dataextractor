# -*- coding: utf-8 -
import json

try:
    # CKAN 2.7 and later
    from ckan.common import config
except ImportError:
    # CKAN 2.6 and earlier
    from pylons import config

import logging

import ckan.logic as l
from ckan.common import _

from ckanext.dataextractor.lib import AzureStorageService
from ckanext.dataextractor.lib import FileWriterService

log = logging.getLogger(__name__)


def resource_filters_create(context, data_dict):
    """Create custom extract filters for a given resource.

    :param resource_id: id of the resource that filters should be added to.
    :type resource_id: string

    :param filters: filters i.e. ['electricity', 'date']
    :type filters: list of strings

    :returns: the newly created resource
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
                _('\'{0}\' filter type not supported. Supported types are: {1}'.format(_f, available_filters))
            )

    # Check if filter already exist for the given resource
    active_filters = l.get_action('active_resource_filters')(context, {'resource_id': resource_id})
    for _f in active_filters:
        if _f['name'] in filters:
            raise l.ValidationError(
                _('\'{0}\' already exists for the given resource'.format(_f))
            )

    resource_meta = l.get_action('datastore_search')(context, {'resource_id': resource_id, 'limit': 1})
    fields = resource_meta['fields']

    # Add new filters
    payload = {'id': resource_id}
    for _f in fields:
        if _f['id'] in filters:
            active_filters.append(
                {'name': _f['id'],
                 'type': _f['type']}
            )
    payload.update({'filters': json.dumps(active_filters)})
    l.get_action('resource_patch')(context, payload)
    
    return l.get_action('resource_show')(context, {'id': resource_id})


def azure_blob_create(context, data_dict):
    """Create file in specified format and upload it to azure blob storage.

    :param resource_id:
    :type resource_id: string

    :param filters: list of applied filters
    :type filters: list

    :param sort: sort criteria
    :type string: sort criteria string

    :param format: format of the file that will be created. i.e. 'csv', 'tsv', 'json', 'xml', 'xlsx'
    :type format: string

    :param delimiter: delimiter . i.e. 'tab', 'comma', 'pipe', 'semicolon'
    :type delimiter: string

    :returns: azure blob storage url to the created file.
    :rtype: string
    """

    azure_storage = AzureStorageService()
    writer = FileWriterService()

    resource_id = data_dict.get('resource_id')
    filters = data_dict.get('filters', [])
    format = data_dict.get('format', 'csv')
    delimiter = data_dict.get('delimiter')
    sort = data_dict.get('sort', None)

    all_data = config.get('ckanext.dataextractor.enable_full_download', False)
    resource = l.get_action('resource_show')(context, {'id': resource_id})
    name = resource.get('name').replace(' ', '_')
    payload = {
        'resource_id': resource_id,
        'filters': filters,
        '_all_data': all_data
    }


    if sort:
        payload['sort'] = sort

    if format.lower() in ('json', 'xml'):
        payload.update({'naive_time': False, 'tz': True})
    elif format.lower() in ('csv', 'xlsx'):
        payload.update({'naive_time': True, 'tz': False})

    resource_data = l.get_action('datastore_resource_search')(context, payload)
    stream = writer.write_to_file(resource_data.get('fields'),
                                  resource_data.get('records'),
                                  format,
                                  delimiter)
    try:
        blob_url = azure_storage.blob_create(stream, format, name)
    except Exception as e:
        raise Exception(e)
    finally:
        stream.close()

    return blob_url
