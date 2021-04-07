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
import ckan.lib.helpers as h
import ckan.model as m
from ckan.common import c

from urllib import urlencode
from datetime import date, timedelta, datetime
from decimal import Decimal

log = logging.getLogger(__name__)

NAIVE_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
DATE_FORMAT = '%Y-%m-%d'
DATASTORE_DEFAULT_ROOT_URL  = datastore_api = '%s/api/action' % \
                          config.get('ckan.site_url', '').rstrip('/')

eds_search_limit = lambda: config.get('ckanext.dataextractor.default_search_limit', 10000)

datastore_root_url = lambda: config.get('ckanext.dataextractor.datastore_root_url',
                                        DATASTORE_DEFAULT_ROOT_URL)

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            return json.JSONEncoder.default(self, obj)
        except TypeError:
            if type(obj) is date:
                return obj.strftime(DATE_FORMAT)

            if type(obj) is datetime:
                return obj.strftime(NAIVE_DATETIME_FORMAT)

            if type(obj) is timedelta:
                # return it as rounded milliseconds
                return int(obj.total_seconds() * 1000)

            if type(obj) is Decimal:
                return str(obj)

            raise


def _get_context():
    return {
        'model': m,
        'session': m.Session,
        'user': c.user or c.author,
        'auth_user_obj': c.userobj
    }

def _get_logic_functions(module_root, logic_functions={}):
    '''Helper function that scans extension logic dir for all logic functions.'''
    for module_name in ['create', 'delete', 'get', 'patch', 'update']:
        module_path = '%s.%s' % (module_root, module_name,)

        module = __import__(module_path)

        for part in module_path.split('.')[1:]:
            module = getattr(module, part)

        for key, value in module.__dict__.items():
            if not key.startswith('_') and (hasattr(value, '__call__')
                                            and (value.__module__ == module_path)):
                logic_functions[key] = value

    return logic_functions


def get_operator(str):
    ops = {
        'lt': '<',
        'gt': '>',
        'lte': '<=',
        'gte': '>=',
        'eq': '=',
        'neq': '!='
    }
    _ = ops.get(str.lower(), None)
    if _ is not None:
        return _
    for key, val in ops.items():
        if val == str:
            _ = val
    return _


def eds_get_current_url(page, params, controller, action, id, resource_id, exclude_param=''):
    url = h.url_for(controller=controller, action=action, id=id, resource_id=resource_id)

    for k, v in params:
        if k == exclude_param:
            params.remove((k, v))

    params = [(k, v.encode('utf-8') if isinstance(v, basestring) else str(v))
              for k, v in params]

    if (params):
        url = url + u'?page=' + str(page) + '&' + urlencode(params)
    else:
        url = url + u'?page=' + str(page)

    return url


def has_datastore_record(resource_id):
    try:
        data = {
            'resource_id': resource_id,
            'limit': 0
        }
        l.get_action('datastore_resource_search')(None, data)
    except:
        return False
    return True

def get_metadata_attr_field_for_column(column_id, field_name, resource_attr):

    res = ''
    for attr in resource_attr:
        if attr['name_of_field'] == column_id:
            res = attr[field_name]
    return res




