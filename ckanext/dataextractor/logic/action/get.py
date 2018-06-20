# -*- coding: utf-8 -
import json
import logging

try:
    # CKAN 2.7 and later
    from ckan.common import config
except ImportError:
    # CKAN 2.6 and earlier
    from pylons import config

import ckan.logic as l

from ckanext.dataextractor.db import search as dbsearch
from ckanext.dataextractor.helpers import eds_search_limit

log = logging.getLogger(__name__)


@l.side_effect_free
def resource_filters(context, data_dict):
    """Fetch all available filters for a given resource.

    :param resource_id: id of the resource.
    :type resource_id: string

    :returns: available filters for the resource
    :rtype: list of dictionaries
    """

    resource_id = l.get_or_bust(data_dict, 'resource_id')
    ds = l.get_action('datastore_info')(context, {'id': resource_id})

    # Loop through datastore schema and validate filters
    available_filters = map(lambda val: val, ds.get('schema').keys())

    _ = l.get_action('active_resource_filters')(context, {'resource_id': resource_id})
    used_filters = map(lambda _f: _f['name'], _)

    out = []
    diff = list(set(available_filters) - set(used_filters))

    resource_meta = l.get_action('datastore_search')(context, {'resource_id': resource_id, 'limit': 1})
    fields = resource_meta['fields']

    # Make sure the order is always like the order of the metadata fields
    for _f in fields:
        if _f['id'] in diff:
            out.append(
                {'name': _f['id'],
                 'type': _f['type']}
            )

    return out


@l.side_effect_free
def active_resource_filters(context, data_dict):
    """Fetch all active filters for a given resource.

    :param resource_id: id of the resource.
    :type resource_id: string

    :returns: available filters for the resource
    :rtype: list of dictionaries
    """
    resource_id = l.get_or_bust(data_dict, 'resource_id')
    resource = context['model'].Resource.get(resource_id)
    filters = []
    out = []
    if 'filters' in resource.extras:
        filters = json.loads(resource.extras['filters'])
    filter_names = map(lambda val: val['name'], filters)

    resource_meta = l.get_action('datastore_search')(context, {'resource_id': resource_id, 'limit': 1})
    fields = resource_meta['fields']

    # Make sure the order is always like the order of the metadata fields
    for _f in fields:
        if _f['id'] in filter_names:
            out.append(
                {'name': _f['id'],
                 'type': _f['type']}
            )

    return out


def datastore_resource_search(context, data_dict):
    """Search through the DataStore for a given resource.

    :param resource_id: id of the resource that you want to search against.
    :type resource_id: string

    :param filters: List of filter objects to apply i.e. [{"name": "Dato og tid", "operator": "<=", "value": "2017-03-03"}, ...] (optional).
    :type filters: string

    :param sort: Sort criteria i.e. Column Name, ASC (optional).
    :type sort: string

    :param limit: Limit the search criteria (defaults to 10000).
    :type limit: integer

    :param offset: Offset for the search criteria (defaults to 0).
    :type offset: integer

    :returns: dictionary
    
    For more information refer to the `DataStore Search API Documentation <http://docs.ckan.org/en/latest/maintaining/datastore.html#ckanext.datastore.logic.action.datastore_search/>`_.

    :rtype: json
    """

    # TODO: Check access

    l.get_or_bust(data_dict, 'resource_id')
    data_dict['connection_url'] = config.get('ckan.datastore.read_url')

    # Set default limit
    if 'limit' in data_dict:
        limit = data_dict.pop('limit')
        data_dict['limit'] = limit if limit <= eds_search_limit() else eds_search_limit()
    else:
        data_dict['limit'] = eds_search_limit()

    results = dbsearch(context, data_dict)
    return results
