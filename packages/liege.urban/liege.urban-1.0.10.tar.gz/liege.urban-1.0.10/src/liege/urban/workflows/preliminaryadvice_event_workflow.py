# -*- coding: utf-8 -*-

from Products.urban.workflows.adapter import LocalRoleAdapter


class StateRolesMapping(LocalRoleAdapter):
    """
    """

    mapping = {
        'in_progress': {
            'administrative_editors': ('Editor',),
            'technical_editors': ('Editor',),
            'technical_validators': ('Editor', 'Contributor'),
            'urban_readers': ('Reader', 'RoadReader'),
            'environment_readers': ('Reader', 'RoadReader'),
        },

        'technical_validation': {
            'administrative_editors': ('Editor',),
            'technical_validators': ('Editor', 'Contributor'),
            'urban_readers': ('Reader', 'RoadReader'),
            'environment_readers': ('Reader', 'RoadReader'),
        },

        'executive_validation': {
            'administrative_editors': ('Editor',),
            'administrative_validators': ('Editor', 'Contributor'),
            'urban_readers': ('Reader', 'RoadReader'),
            'environment_readers': ('Reader', 'RoadReader'),
        },

        'preliminary_advice_sent': {
            'administrative_validators': ('Editor', 'Contributor'),
            'technical_validators': ('Editor', 'Contributor'),
            'urban_readers': ('Reader', 'RoadReader'),
            'environment_readers': ('Reader', 'RoadReader'),
        },

    }
