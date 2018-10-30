from logging import getLogger

import ckan.plugins.toolkit as t
import ckan.lib.plugins as lib_plugins

from ckan.common import  _, request, c, g, response
from ckan.controllers.package import PackageController

import ckan.logic as l
import ckan.lib.base as base
import ckan.lib.helpers as h
import ckan.model as model
import ckan.lib.render

render = base.render
abort = base.abort
redirect = t.redirect_to

NotAuthorized = l.NotAuthorized
ValidationError = l.ValidationError
check_access = l.check_access
get_action = l.get_action
tuplize_dict = l.tuplize_dict
clean_dict = l.clean_dict
parse_params = l.parse_params
flatten_to_string_key = l.flatten_to_string_key
lookup_package_plugin = ckan.lib.plugins.lookup_package_plugin
logger = getLogger(__name__)


class ResourceFiltersController(PackageController):
    def _get_ctx(self):
        return {
            'model': model, 'session': model.Session,
            'user': c.user, 'auth_user_obj': c.userobj,
            'save': 'save' in request.params
        }

    def resource_filters_edit(self, name, resource_id):
        context = self._get_ctx()
        pkg = l.get_action('package_show')(context, {'id': name})
        resource = l.get_action('resource_show')(context, {'id': resource_id})
        active_filters = l.get_action('active_resource_filters')(
            context, {'resource_id': resource_id}
        )
        vars = {'pkg_dict': pkg, 'res': resource,
                'dataset_type': 'dataset',
                'active_filters': active_filters}

        return render('package/resource_filters_edit.html', extra_vars=vars)

    def resource_filters_delete(self, name, resource_id, filter_name):
        context = self._get_ctx()

        l.get_action('resource_filters_delete')(
            context, {
                'resource_id': resource_id,
                'filters': [filter_name,]
            })

        h.flash_notice(_('The filter has been deleted.'))
        redirect(t.url_for('resource_filters_edit', name=name, resource_id=resource_id))

    def resource_filters_create(self, name, resource_id):
        context = self._get_ctx()
        if t.request.method.lower() == 'post':
            filters = t.request.POST.getall('filters')
            l.get_action('resource_filters_create')(
                context, {
                    'resource_id': resource_id,
                    'filters': filters
                }
            )
            h.flash_success(_('Resource filters created successfully!'))
            redirect(t.url_for('resource_filters_edit', name=name, resource_id=resource_id))

        pkg = l.get_action('package_show')(context, {'id': name})
        resource = l.get_action('resource_show')(context, {'id': resource_id})
        available_filters = l.get_action('resource_filters')(
            context, {'resource_id': resource_id}
        )
        vars = {'pkg_dict': pkg, 'res': resource, 'dataset_type': 'dataset',
                'available_filters': available_filters}

        return render('package/resource_filters_create.html', extra_vars=vars)
