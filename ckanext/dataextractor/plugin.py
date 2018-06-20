import re
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

import ckanext.dataextractor.helpers as _h
import ckanext.dataextractor.logic.auth as a

from ckan.lib.plugins import DefaultTranslation


class DataextractorPlugin(plugins.SingletonPlugin, DefaultTranslation):
    plugins.implements(plugins.ITranslation)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.ITemplateHelpers)

    # IRoutes

    def before_map(self, map):
        ctrl = 'ckanext.dataextractor.controllers.resource_filters:ResourceFiltersController'
        dataextractor_ctrl = 'ckanext.dataextractor.controllers.dataextractor:DataextractorController'

        map.connect('resource_filters_edit',
                    '/dataset/{name}/resource_filters_edit/{resource_id}',
                    controller=ctrl, ckan_icon='tasks',
                    action='resource_filters_edit')
        map.connect('resource_filters_delete',
                    '/dataset/{name}/resource_filters_delete/{resource_id}/{filter_name}',
                    controller=ctrl, ckan_icon='delete',
                    action='resource_filters_delete')
        map.connect('resource_filters_save',
                    '/dataset/{name}/resource_filters_save/{resource_id}',
                    controller=ctrl, ckan_icon='save',
                    action='resource_filters_save')
        map.connect('resource_filters_create',
                    '/dataset/{name}/resource_filters_create/{resource_id}',
                    controller=ctrl, ckan_icon='plus',
                    action='resource_filters_create')

        map.connect('/dataset/{id}/resource_extract/{resource_id}', controller=dataextractor_ctrl,
                    action='resource_extractor_show')

        return map

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'dataextractor')

    # IActions

    def get_actions(self):
        module_root = 'ckanext.dataextractor.logic.action'
        action_functions = _h._get_logic_functions(module_root)

        return action_functions

    # ITemplateHelpers

    def get_helpers(self):
        return {
            'eds_get_current_url': _h.eds_get_current_url,
            'has_datastore_record': _h.has_datastore_record,
            'capitalize_string': lambda s: re.sub(r"(?<=[a-z])(?=[A-Z])", " ", s),
            'startswith': lambda s, _: s.startswith(_),
            'endswith': lambda s, _: s.endswith(_),
            'eds_search_limit': _h.eds_search_limit,
            'get_metadata_attr_field_for_column': _h.get_metadata_attr_field_for_column,
            'eds_datastore_root_url' : _h.datastore_root_url
        }

    # IAuthFunctions

    def get_auth_functions(self):
        return {
            'blobs_delete': a.blobs_delete
        }
