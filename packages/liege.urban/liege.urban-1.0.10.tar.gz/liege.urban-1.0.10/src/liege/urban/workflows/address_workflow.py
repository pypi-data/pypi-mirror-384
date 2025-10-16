# -*- coding: utf-8 -*-

from Products.urban.interfaces import IEnvironmentBase
from Products.urban.workflows.adapter import LocalRoleAdapter

from plone import api


class StateRolesMapping(LocalRoleAdapter):
    """
    """

    def __init__(self, context):
        self.context = context
        self.licence = self.context

    def get_allowed_groups(self, licence):
        if IEnvironmentBase.providedBy(licence):
            return 'environment_only'
        else:
            return 'urban_only'

    def get_editors(self):
        """ """
        licence = self.licence
        mapping = {
            'urban_only': [
                'administrative_editors',
                'administrative_validators',
            ],
            'environment_only': [
                'administrative_editors_environment',
                'administrative_validators_environment',
            ],
        }
        allowed_group = self.get_allowed_groups(licence)
        if allowed_group in mapping:
            return mapping.get(allowed_group)

    def get_readers(self):
        """ """
        licence = self.licence
        mapping = {
            'urban_only': [
                'urban_readers',
            ],
            'environment_only': [
                'environment_readers',
            ],
        }
        allowed_group = self.get_allowed_groups(licence)
        if allowed_group in mapping:
            return mapping.get(allowed_group)

    def get_parcel_roles(self):
        licence = self.context.aq_parent
        if api.content.get_state(licence) == 'deposit':
            return ('Editor', 'Reader')
        return ('Reader',)

    mapping = {
        'draft': {
            get_editors: (get_parcel_roles,),
            get_readers: ('Reader',),
            'survey_editors': ('AddressEditor',),
        },

        'validated': {
            get_readers: ('Reader',),
            'survey_editors': ('AddressEditor',),
        },

    }
