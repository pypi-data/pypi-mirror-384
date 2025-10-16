# -*- coding: utf-8 -*-

from Products.urban.workflows.adapter import LocalRoleAdapter


class StateRolesMapping(LocalRoleAdapter):
    """ """

    mapping = {
        'deposit': {
            'administrative_editors': ('Editor', 'AddressEditor'),
            'administrative_validators': ('Contributor', 'AddressEditor'),
            'survey_editors': ('Reader', 'AddressEditor'),
            'urban_readers': ('Reader',),
            'urban_internal_readers': ('InternalReader', 'RoadReader'),
        },

        'analysis': {
            'technical_editors': ('Editor',),
            'technical_validators': ('Contributor',),
            'survey_editors': ('Reader', 'AddressEditor'),
            'urban_readers': ('Reader',),
            'urban_internal_readers': ('InternalReader', 'RoadReader'),
        },

        'analysis_validation': {
            'technical_validators': ('Contributor',),
            'survey_editors': ('Reader', 'AddressEditor'),
            'urban_readers': ('Reader',),
            'urban_internal_readers': ('InternalReader', 'RoadReader'),
        },

        'college': {
            'administrative_editors': ('Editor',),
            'administrative_validators': ('Contributor',),
            'survey_editors': ('Reader', 'AddressEditor'),
            'urban_readers': ('Reader',),
            'urban_internal_readers': ('InternalReader', 'RoadReader'),
        },

        'favorable': {
            'administrative_editors': ('Editor',),
            'administrative_validators': ('Editor',),
            'technical_editors': ('Editor',),
            'technical_validators': ('Editor',),
            'survey_editors': ('Reader', 'AddressEditor'),
            'urban_readers': ('Reader',),
            'urban_internal_readers': ('InternalReader', 'RoadReader'),
        },

        'defavorable': {
            'administrative_editors': ('Editor',),
            'administrative_validators': ('Editor',),
            'technical_editors': ('Editor',),
            'technical_validators': ('Editor',),
            'survey_editors': ('Reader', 'AddressEditor'),
            'urban_readers': ('Reader',),
            'urban_internal_readers': ('InternalReader', 'RoadReader'),
        },

        'abandoned': {
            'administrative_editors': ('Editor',),
            'administrative_validators': ('Editor',),
            'technical_editors': ('Editor',),
            'technical_validators': ('Editor',),
            'survey_editors': ('Reader', 'AddressEditor'),
            'urban_readers': ('Reader',),
            'urban_internal_readers': ('InternalReader', 'RoadReader'),
        },
    }
