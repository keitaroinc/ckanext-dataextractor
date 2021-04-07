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

try:
    # CKAN 2.7 and later
    from ckan.common import config
except ImportError:
    # CKAN 2.6 and earlier
    from pylons import config

import ckan.logic as logic
import ckan.lib.base as base
import ckan.model as model
import ckan.plugins as p
import ckan.lib.helpers as h

from ckan.controllers.package import PackageController
from ckan.common import _, c, request

render = base.render
abort = base.abort

NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
ValidationError = logic.ValidationError
check_access = logic.check_access
get_action = logic.get_action
tuplize_dict = logic.tuplize_dict
clean_dict = logic.clean_dict
parse_params = logic.parse_params

log = logging.getLogger(__name__)

CTRL = 'ckanext.dataextractor.controllers.dataextractor:DataextractorController'


class DataextractorController(PackageController):
    def _get_ctx(self):
        return {
            'model': model, 'session': model.Session,
            'user': c.user,
            'auth_user_obj': c.userobj,
            'for_view': True
        }

    def __get_page_number(self, params):
        if p.toolkit.check_ckan_version(min_version='2.5.0', max_version='2.5.10'):
            return self._get_page_number(params)
        return h.get_page_number(params)

    def _setup_dataextractor_vars(self, resource_id, context, request):
        page = self.__get_page_number(request.params)
        limit = int(config.get('ckanext.dataextractor.resource_rows_limit', 10))
        pagination_limit = int(config.get('ckanext.dataextractor.pagination_limit', 6))
        c.page = page
        c.limit = limit
        c.pagination_limit = pagination_limit
        c.resource_attr = logic.get_action('resource_show')(context, {'id': resource_id})['attributes']

        # required to populate available resource filters
        c.active_resource_filters = get_action('active_resource_filters')(
            context, {
                'resource_id': resource_id
            })

        c.sort_fields = map(lambda f: f['name'], c.active_resource_filters)

        if request.method.lower() == 'post':
            applied_filters = request.POST.getall('applied-filters')
            c.sort_criteria = request.POST.get('sort')
            c.page = 1
        elif request.method.lower() == 'get':
            applied_filters = request.params.getall('applied-filters')
            c.sort_criteria = request.params.get('sort')

        _filters = []
        for _f in applied_filters:
            _ = _f.split('|')
            _filters.append({'name': _[0],
                             'operator': _[1],
                             'value': _[2],
                             'filter_string': _f})

        c.applied_filters = _filters
        c.resource_data = logic.get_action('datastore_resource_search')(
            context, {
                'resource_id': resource_id,
                'filters': _filters,
                'limit': limit,
                'offset': (page - 1) * limit if page > 1 else 0,
                'sort': c.sort_criteria,
                'naive_time': False,
                'tz': False
            })

        # Update active filter types to match field types
        # This is a hack due to bug in the datastore_info action which does not return correct info
        for obj in c.active_resource_filters:
            for _obj in c.resource_data['fields']:
                if obj['name'] != _obj['id']:
                    continue
                if obj['type'] in ('date'):
                    obj['type'] = _obj['type']

        c.total = c.resource_data['total']

    def resource_extractor_show(self, id, resource_id):
        context = self._get_ctx()

        try:
            c.package = get_action('package_show')(context, {'id': id})
        except (NotFound, NotAuthorized):
            abort(404, _('Dataset not found'))

        for resource in c.package.get('resources', []):
            if resource['id'] == resource_id:
                c.resource = resource
                break
        if not c.resource:
            abort(404, _('Resource not found'))

        c.datastore_api = '%s/api/action' % \
                          config.get('ckan.site_url', '').rstrip('/')

        # required for nav menu
        c.pkg = context['package']
        c.pkg_dict = c.package
        dataset_type = c.pkg.type or 'dataset'

        # get package license info
        license_id = c.package.get('license_id')
        try:
            c.package['isopen'] = model.Package. \
                get_license_register()[license_id].isopen()
        except KeyError:
            c.package['isopen'] = False

        c.resource['can_be_previewed'] = self._resource_preview(
            {'resource': c.resource, 'package': c.package})

        resource_views = get_action('resource_view_list')(
            context, {'id': resource_id})
        c.resource['has_views'] = len(resource_views) > 0
        vars = {'dataset_type': dataset_type}

        try:
            self._setup_dataextractor_vars(resource_id=resource_id,
                                           context=context,
                                           request=request)
        except ValidationError as e:
            h.flash_error(e.error_dict['message'])
            base.redirect(h.url_for(controller=CTRL,
                                    action='resource_extractor_show',
                                    id=id, resource_id=resource_id))
        except NotFound as e:
            h.flash_error(e.message)
            base.redirect(h.url_for(controller='package',
                                    action='resource_read',
                                    id=id, resource_id=c.resource['id']))

        return render('package/resource_extractor.html', extra_vars=vars)

