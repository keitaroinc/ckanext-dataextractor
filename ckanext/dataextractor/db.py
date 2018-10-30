# -*- coding: utf-8 -*-
import logging
import re

import ckan.logic as l
import ckan.model as m
from ckan.common import c

log = logging.getLogger(__name__)

from ckanext.datastore.backend.postgres import (_get_engine_from_url, _get_fields_types, _PG_ERR_CODE, _get_unique_key)
from ckanext.dataextractor.helpers import get_operator, eds_search_limit
from datetime import datetime, date, time
from collections import OrderedDict

from sqlalchemy.exc import ProgrammingError, DBAPIError

DATE_FORMAT = '%Y-%m-%d'
TIME_FORMAT = '%H:%M'


def _where(data_dict):
    filters = data_dict.pop('filters', [])
    clause = ''
    if any(filters):
        if len(filters) > 1:
            # Loop through filters and create SQL query
            for idx, _ in enumerate(filters):
                op = get_operator(_['operator'])
                name = _['name'].encode('utf-8')

                if idx == 0:

                    if _['operator'] == 'NOT BETWEEN':
                        name = _['name'].encode('utf-8')
                        values = _['value'].split(' AND ')
                        clause = 'WHERE ("{0}" {1} \'{2}\''.format(name, '<', _normalize_value(values[0]))
                        clause += ' OR "{0}" {1} \'{2}\')'.format(name, '>', _normalize_value(values[1]))

                    elif _['operator'] == 'BETWEEN':
                        name = _['name'].encode('utf-8')
                        values = _['value'].split(' AND ')
                        clause = 'WHERE ("{0}" {1} \'{2}\''.format(name, '>=', _normalize_value(values[0]))
                        clause += ' AND "{0}" {1} \'{2}\')'.format(name, '<=', _normalize_value(values[1]))
                    else:
                        clause = 'WHERE ("{0}" {1} \'{2}\')'.format(name, op, _normalize_value(_['value']))
                else:

                    if _['operator'] == 'NOT BETWEEN':
                        op = _['operator']
                        name = _['name'].encode('utf-8')
                        values = _['value'].split(' AND ')
                        clause += ' AND ("{0}" {1} \'{2}\''.format(name, '<', _normalize_value(values[0]))
                        clause += ' OR "{0}" {1} \'{2}\')'.format(name, '>', _normalize_value(values[1]))

                    elif _['operator'] == 'BETWEEN':
                        name = _['name'].encode('utf-8')
                        values = _['value'].split(' AND ')
                        clause += ' AND ("{0}" {1} \'{2}\''.format(name, '>=', _normalize_value(values[0]))
                        clause += ' AND "{0}" {1} \'{2}\')'.format(name, '<=', _normalize_value(values[1]))
                    else:
                        clause += ' AND ("{0}" {1} \'{2}\')'.format(name, op, _normalize_value(_['value']))

        else:
            _ = filters[0]
            if _['operator'] == 'NOT BETWEEN':
                op = _['operator']
                name = _['name'].encode('utf-8')
                values = _['value'].split(' AND ')
                clause = 'WHERE ("{0}" {1} \'{2}\''.format(name, '<', _normalize_value(values[0]))
                clause += ' OR "{0}" {1} \'{2}\')'.format(name, '>', _normalize_value(values[1]))

            elif _['operator'] == 'BETWEEN':
                name = _['name'].encode('utf-8')
                values = _['value'].split(' AND ')
                clause = 'WHERE ("{0}" {1} \'{2}\''.format(name, '>=', _normalize_value(values[0]))
                clause += ' AND "{0}" {1} \'{2}\')'.format(name, '<=', _normalize_value(values[1]))
            else:
                op = get_operator(_['operator'])
                name = _['name'].encode('utf-8')
                clause = 'WHERE ("{0}" {1} \'{2}\')'.format(name, op, _normalize_value(_['value']))

    return clause

def _normalize_value(value):
    return value.replace('%', '%%').encode('utf-8')


def _total_count(context, resource, where):
    sql_string = '''SELECT count(1) AS _count FROM "{resource}" {where}'''.format(
        resource=resource,
        where=where
    )
    return context['connection'].execute(sql_string).scalar()


def _format_results(context, resource_id, types, results, count, naive_time=True, tz=False):
    records = []
    resource_attr = l.get_action('resource_show')(context, {'id': resource_id})['attributes']

    for result in results:
        _ = OrderedDict()

        for k, v in zip(types, result):
            time_utc = False

            if isinstance(v, (datetime, date, time)):
                # Chech if field is in UTC or DK time
                for attr in resource_attr:
                    if k == attr['name_of_field']:
                        if attr['type'] == 'timestamptz':
                            time_utc = True

                if naive_time:
                    _.update({k.encode('utf-8'): v.strftime(
                        '{0} {1}'.format(DATE_FORMAT,
                                         TIME_FORMAT))
                    })
                elif not naive_time and tz and time_utc:
                    _.update({k.encode('utf-8'): v.strftime(
                        '{0}T{1}Z'.format(DATE_FORMAT,
                                          TIME_FORMAT))
                    })
                elif not naive_time and not tz and time_utc:
                    _.update({k.encode('utf-8'): v.strftime(
                        '{0} {1}Z'.format(DATE_FORMAT,
                                          TIME_FORMAT))
                    })
                #DK time
                elif not naive_time and tz and not time_utc:
                    _.update({k.encode('utf-8'): v.strftime(
                        '{0}T{1}'.format(DATE_FORMAT,
                                          TIME_FORMAT))
                    })
                elif not naive_time and not tz and not time_utc:
                    _.update({k.encode('utf-8'): v.strftime(
                        '{0} {1}'.format(DATE_FORMAT,
                                          TIME_FORMAT))
                    })
            else:
                _.update({k.encode('utf-8'): v})
        records.append(_)

    out = {'records': records,
           'records_count': len(records),
           'total': count}
    return out


def _search_data(context, data_dict):
    # TODO: Get defaults from config

    resource_id = data_dict.get('resource_id')
    _types = _get_fields_types(context, data_dict)
    _types = map(lambda i: i, _types)
    _types.remove('_id')

    _types_str = map(lambda t: '"{0}"'.format(t.encode('utf-8')), _types)
    select = ', '.join(_types_str)

    # Generate string for the sort criteria
    sort = data_dict.get('sort', None)
    sort_clause = 'ORDER BY "{0}" DESC'.format(_types[0])
    if sort:
        sort = sort.split(',')
        _ = ','.join('"{0}"'.format(s.strip().encode('utf-8')) for s in sort[:-1])
        sort_clause = 'ORDER BY {0} {1}'.format(_, sort[-1].strip())

    where_clause = _where(data_dict)

    # apply limit & offset for pagination
    limit = data_dict.get('limit', eds_search_limit())
    offset = data_dict.get('offset', 0)

    _count = _total_count(context, resource_id, where_clause)

    # generate the final SQL query string
    sql_string = '''SELECT {select} FROM "{resource}" {where} {sort}'''.format(
        select=select,
        resource=resource_id,
        where=where_clause,
        sort=sort_clause)

    _all_data = data_dict.pop('_all_data', False)
    if not _all_data:
        sql_string = '{0} LIMIT {1} OFFSET {2}'.format(sql_string, limit, offset)

    naive_time = data_dict.pop('naive_time', True)
    tz = data_dict.pop('tz', False)
    results = context['connection'].execute(sql_string).fetchall()
    out = _format_results(context, resource_id, _types, results, _count, naive_time=naive_time, tz=tz)

    fields = []
    for k, v in _get_fields_types(context, data_dict).items():
        if k == '_id':
            continue
        fields.append({'id': k, 'type': v})
    out['fields'] = fields
    return out


def search(context, data_dict):

    engine = _get_engine_from_url(data_dict['connection_url'])
    context['connection'] = engine.connect()

    # Default timeout 60000 ms
    timeout = context.get('ckanext.dataextractor.query_timeout', 60000)
    try:
        context['connection'].execute(
            u'SET LOCAL statement_timeout TO {0}'.format(timeout))
        return _search_data(context, data_dict)
    except ProgrammingError as e:
        log.error('ProgrammingError: %r', e)
        message = e.message
        if 'does not exist' in e.message:
            raise l.NotFound(
                'Resource "{0}" does not contain record in the datastore.'.format(data_dict['resource_id'])
            )
        raise l.ValidationError({
            'message': message
        })
    except DBAPIError, e:
        log.error('DBAPIError: %r', e)
        message = e.message
        if 'invalid input syntax' in e.message:
            message = 'Invalid input values for the given filters.'
        raise l.ValidationError({
            'message': message
        })
    except Exception as e:
        log.error('GeneralException: %r', e)
    finally:
        context['connection'].close()
