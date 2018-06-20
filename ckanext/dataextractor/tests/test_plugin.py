"""Tests for plugin.py."""
import json
import requests
import datetime
import cStringIO
from nose.tools import assert_raises
from collections import Counter, OrderedDict

from ckan.tests import factories, helpers
from ckan.plugins import toolkit
from ckan import plugins
from ckan import logic

from azure.storage.blob import BlockBlobService

import ckanext.dataextractor.plugin as plugin


class ActionBase(object):
    @classmethod
    def setup_class(self):
        if not plugins.plugin_loaded('dataextractor'):
            plugins.load('dataextractor')

        if not plugins.plugin_loaded('datastore'):
            plugins.load('datastore')

    def setup(self):
        helpers.reset_db()

    @classmethod
    def teardown_class(self):
        if plugins.plugin_loaded('dataextractor'):
            plugins.unload('dataextractor')
        if plugins.plugin_loaded('datastore'):
            plugins.unload('datastore')


class TestDataExtractorActions(ActionBase):
    def setup_resource(self):
        '''Creates user, context, dataset and resource for testing purposes
        '''
        user = factories.Sysadmin()
        context = {'user': user['name']}
        organization = factories.Organization()

        with open('ckanext/dataextractor/tests/test_create_dataset.json') as data_file:
            kwargs = json.load(data_file)

        kwargs['owner_org'] = organization.get('name')

        dataset = helpers.call_action('package_create',
                                           context=context,
                                           **kwargs)

        with open('ckanext/dataextractor/tests/test_create_resource.json') as data_file:
            resource = json.load(data_file)

        resource['resource']['package_id'] = dataset['id']

        ds_create = helpers.call_action(
            'datastore_create',
            context=context,
            **resource)

        resource_id = ds_create['resource_id']

        return user, context, dataset, resource, resource_id


    def test_resource_filters_valid(self):
        '''Tests if the 'resource_filters' action lists the available filters
        for the given resource.
        '''
        user, context, dataset, resource, resource_id = self.setup_resource()

        fields = resource['fields']
        print fields

        list_ids = [field['id'] for field in fields]

        result = helpers.call_action(
            'resource_filters',
            context=context,
            resource_id=resource_id)

        ds_info = helpers.call_action(
            'datastore_info',
            context=context,
            id=resource_id)

        list_names = [names['name'] for names in result]

        assert Counter(list_ids) == Counter(list_names)

        helpers.call_action('datastore_delete', context=context, id=resource_id)


    def test_active_resource_filters_valid(self):
        '''Tests if 'active_resource_filters' action returns the active
        resource filters
        '''
        user, context, dataset, resource, resource_id = self.setup_resource()

        available_filters = helpers.call_action(
            'resource_filters',
            context=context,
            resource_id=resource_id)

        for _f in available_filters:
            activate_filter = helpers.call_action(
                'resource_filters_create',
                filters=[_f['name']],
                context=context,
                resource_id=resource_id)

            get_active_filters = helpers.call_action(
                'active_resource_filters',
                context=context,
                resource_id=resource_id)

            assert _f == get_active_filters.pop()

        helpers.call_action('datastore_delete', context=context, id=resource_id)


    def test_add_filter_valid(self):
        '''Tests if 'resource_filters_create' creates the correct resource
        filter
        '''
        user, context, dataset, resource, resource_id = self.setup_resource()

        available_filters = helpers.call_action(
            'resource_filters',
            context=context,
            resource_id=resource_id)


        for _f in available_filters:
            activate_filter = helpers.call_action(
                'resource_filters_create',
                context=context,
                filters=[_f['name']],
                resource_id=resource_id)

            for key, val in activate_filter.items():
                if key != 'filters':
                    continue
                filter = val.pop()

            assert _f['name'] == filter['name']

        helpers.call_action('datastore_delete', context=context, id=resource_id)


    def test_delete_filter(self):
        '''Tests if the 'resource_filters_delete' action is deleting the
        resource filter
        '''
        user, context, dataset, resource, resource_id = self.setup_resource()

        available_filters = helpers.call_action(
            'resource_filters',
            context=context,
            resource_id=resource_id)

        for _f in available_filters:
            activate_filter = helpers.call_action(
                'resource_filters_create',
                context=context,
                filters=[_f['name']],
                resource_id=resource_id)

            deactivate_filter = helpers.call_action(
                'resource_filters_delete',
                context=context,
                filters=[_f['name']],
                resource_id=resource_id)

            get_active_filters = helpers.call_action(
                'active_resource_filters',
                context=context,
                resource_id=resource_id)

            assert not get_active_filters

        helpers.call_action('datastore_delete', context=context, id=resource_id)


    def test_resource_filters_missing_id(self):
        """Tests if 'resource_filters' action raises a ValidationError
        if resource_id is missing
        """
        user, context, dataset, resource, resource_id = self.setup_resource()

        assert_raises(
            logic.ValidationError,
            helpers.call_action,
            'resource_filters',
            context=context)

        helpers.call_action('datastore_delete', context=context, id=resource_id)


    def test_add_filter_missing_id(self):
        '''Tests if the 'resource_filters_create' action raises a
        ValidationError if resource_id is missing
        '''
        user, context, dataset, resource, resource_id = self.setup_resource()

        available_filters = helpers.call_action(
            'resource_filters',
            context=context,
            resource_id=resource_id)

        for _f in available_filters:
            assert_raises(
                logic.ValidationError,
                helpers.call_action,
                'resource_filters_create',
                context=context,
                filters=[_f['name']])

        helpers.call_action('datastore_delete', context=context, id=resource_id)


    def test_active_resource_filters_missing_id(self):
        '''Tests if the 'active_resource_filters' action raises a
        ValidationError if resource_id is missing
        '''
        user, context, dataset, resource, resource_id = self.setup_resource()

        available_filters = helpers.call_action(
            'resource_filters',
            context=context,
            resource_id=resource_id)

        for _f in available_filters:
            activate_filter = helpers.call_action(
                'resource_filters_create',
                filters=[_f['name']],
                context=context,
                resource_id=resource_id)

        assert_raises(
                logic.ValidationError,
                helpers.call_action,
                'active_resource_filters',
                context=context)

        helpers.call_action('datastore_delete', context=context, id=resource_id)


    def test_delete_missing_id(self):
        '''Tests if the 'resource_filters_delete' action raises a
        ValidationError if resource_id is missing
        '''
        user, context, dataset, resource, resource_id = self.setup_resource()

        available_filters = helpers.call_action(
            'resource_filters',
            context=context,
            resource_id=resource_id)


        for _f in available_filters:
            activate_filter = helpers.call_action(
                'resource_filters_create',
                context=context,
                filters=[_f['name']],
                resource_id=resource_id)

            assert_raises(logic.ValidationError,
                helpers.call_action,
                'resource_filters_delete',
                context=context,
                filters=[_f['name']])

        helpers.call_action('datastore_delete', context=context, id=resource_id)


    def test_add_invalid_filter(self):
        '''Tests if 'resource_filters_create' action raises a ValidationError
        if an invalid filter is placed in the 'filters' argument
        '''
        user, context, dataset, resource, resource_id = self.setup_resource()

        available_filters = helpers.call_action(
            'resource_filters',
            context=context,
            resource_id=resource_id)

        for _f in available_filters:
             assert_raises(logic.ValidationError,
                helpers.call_action,
                'resource_filters_create',
                context=context,
                filters=[_f['name']+'fault'],
                resource_id=resource_id)

        helpers.call_action('datastore_delete', context=context, id=resource_id)


    def test_delete_filter_invalid_filter(self):
        '''Tests if the 'resource_filters_delete' action raises a
        ValidationError if an invalid filter is placed in the 'filters' argument
        '''
        user, context, dataset, resource, resource_id = self.setup_resource()

        available_filters = helpers.call_action(
            'resource_filters',
            context=context,
            resource_id=resource_id)

        for _f in available_filters:
            activate_filter = helpers.call_action(
                'resource_filters_create',
                context=context,
                filters=[_f['name']],
                resource_id=resource_id)

            assert_raises(logic.ValidationError,
                helpers.call_action,
                'resource_filters_delete',
                context=context,
                filters=[_f['name']+'fault'],
                resource_id=resource_id)

        helpers.call_action('datastore_delete', context=context, id=resource_id)


    def filtering(self, name='ImportCapacity', operator='eq', value='600.0', context=None, resource_id=None):
        '''Setup for varous filtering operators
        '''
        filter_params = [{'name':name, 'operator':operator, 'value':value}]
        result = helpers.call_action(
            'datastore_resource_search',
            context=context,
            filters=filter_params,
            resource_id=resource_id)

        return result


    def test_resource_search_operators(self):
        '''Testing the filtering feature
        '''
        user, context, dataset, resource, resource_id = self.setup_resource()


        filtered = self.filtering(operator='lt', context=context, resource_id=resource_id)
        assert filtered["total"] == 2

        filtered = self.filtering(operator='gt', context=context, resource_id=resource_id)
        assert filtered["total"] == 1

        filtered = self.filtering(operator='lte', context=context, resource_id=resource_id)
        assert filtered["total"] == 3

        filtered = self.filtering(operator='gte', context=context, resource_id=resource_id)
        assert filtered["total"] == 2

        filtered = self.filtering(operator='eq', context=context, resource_id=resource_id)
        assert filtered["total"] == 1

        filtered = self.filtering(operator='neq', context=context, resource_id=resource_id)
        assert filtered["total"] == 3

        filtered = self.filtering(operator='BETWEEN',
                                  value='500 AND 700',
                                  context=context,
                                  resource_id=resource_id)
        assert filtered["total"] == 3

        filtered = self.filtering(operator='NOT BETWEEN',
                                  value='200 AND 500',
                                  context=context,
                                  resource_id=resource_id)
        assert filtered["total"] == 2

        filtered = self.filtering(
            name='Hour',
            operator='eq',
            value='2017-01-01 01:00:00', context=context, resource_id=resource_id)
        assert filtered['total'] == 1

    def test_resource_search_result(self):
        '''Testing the search feature.
        '''
        user, context, dataset, resource, resource_id = self.setup_resource()


        filtered = self.filtering(operator='eq', context=context, resource_id=resource_id)
        resource_fields = resource['fields']
        resource_records = resource['records']

        filter_fields = filtered['fields']
        filter_records = filtered['records']

        for resource_record in resource_records:
            if resource_record['ImportCapacity'] == 600.0:
                filtered_record = filter_records.pop()
                for field in resource_fields:
                    if field['type'] == 'timestamp':
                        filtered_dt = datetime.datetime.strptime(
                            filtered_record[field['id']], "%Y-%m-%d %H:%M")
                        resource_dt = datetime.datetime.strptime(
                            resource_record[field['id']], "%Y-%m-%d %H:%M:%S")

                        print filtered_dt
                        print resource_dt

                        assert filtered_dt == resource_dt
                    else:
                        assert filtered_record[field['id']] == resource_record[field['id']]

        helpers.call_action('datastore_delete', context=context, id=resource_id)

    def azure_blob_create_format(self, format='', delimiter=None, filters=[]):
        '''Setup for varoius formats for the azure blob storage
        '''
        user, context, dataset, resource, resource_id = self.setup_resource()
        print resource_id

        result = helpers.call_action(
            'azure_blob_create',
            context=context,
            format=format,
            resource_id=resource_id,
            filters=filters,
            delimiter=delimiter)

        helpers.call_action('datastore_delete', context=context, id=resource_id)

        return result, resource


    def test_azure_blob_create_json(self):
        '''Testing if a json file can be uploaded to Azure
        '''
        blob_url, resource = self.azure_blob_create_format(format='json')
        response = requests.get(blob_url)
        assert response.status_code == 200


    def test_azure_blob_create_csv(self):
        '''Testing if a csv file can be uploaded to Azure
        '''
        blob_url, resource = self.azure_blob_create_format(format='csv')
        response = requests.get(blob_url)
        assert response.status_code == 200


    def test_azure_blob_create_csv_semicolon(self):
        '''Testing if a csv file can be uploaded to Azure
        '''
        blob_url, resource = self.azure_blob_create_format(format='csv', delimiter='semicolon')
        response = requests.get(blob_url)
        assert response.status_code == 200


    def test_azure_blob_create_csv_pipe(self):
        '''Testing if a csv file can be uploaded to Azure
        '''
        blob_url, resource = self.azure_blob_create_format(format='csv', delimiter='pipe')
        response = requests.get(blob_url)
        assert response.status_code == 200


    def test_azure_blob_create_csv_tab(self):
        '''Testing if a csv file can be uploaded to Azure
        '''
        blob_url, resource = self.azure_blob_create_format(format='csv', delimiter='tab')
        response = requests.get(blob_url)
        assert response.status_code == 200


    def test_azure_blob_create_xml(self):
        '''Testing if a xml file can be uploaded to Azure
        '''
        blob_url, resource = self.azure_blob_create_format(format='xml')
        response = requests.get(blob_url)
        assert response.status_code == 200


    def test_azure_blob_create_xlsx(self):
        '''Testing if a xlsx file can be uploaded to Azure
        '''
        blob_url, resource = self.azure_blob_create_format(format='xlsx')
        response = requests.get(blob_url)
        assert response.status_code == 200


    def test_azure_blob_delete(self):
        '''Tests if the created 7 azure blobs are deleted.
        '''
        # TODO: Should use separate config for Azure Blob Storage
        # If someone else uses the same environment this assertion will fail
        # so assert if number_deleted > 0 instead of exact number
        number_deleted = helpers.call_action('azure_blobs_delete')
        # assert number_deleted == 7, number_deleted
        assert number_deleted > 0, number_deleted

