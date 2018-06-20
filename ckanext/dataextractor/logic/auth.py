import logging

from ckan.plugins import toolkit as t

log = logging.getLogger(__name__)

def sysadmin(context, data_dict):
    return {
        'success':  False,
        'msg': t._('User not authorized to delete blobs')
    }

blobs_delete = sysadmin