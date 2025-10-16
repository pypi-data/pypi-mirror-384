# -*- coding: utf-8 -*-

from Products.urban.workflows.adapter import LocalRoleAdapter


class StateRolesMapping(LocalRoleAdapter):
    """ """

    mapping = {
        'creation': {
            'administrative_editors': ('Editor', 'AddressEditor'),
            'administrative_validators': ('Contributor', 'AddressEditor'),
            'inspection_editors': ('Reader',),
            'urban_readers': ('Reader',),
        },

        'prosecution_analysis': {
            'administrative_editors': ('Editor', 'AddressEditor'),
            'administrative_validators': ('Contributor', 'AddressEditor'),
            'inspection_editors': ('Reader',),
            'urban_readers': ('Reader',),
        },

        'technical_analysis': {
            'administrative_editors': ('Editor', 'AddressEditor'),
            'administrative_validators': ('Contributor', 'AddressEditor'),
            'technical_editors': ('Editor', 'AddressEditor'),
            'technical_validators': ('Editor', 'AddressEditor'),
            'inspection_editors': ('Reader',),
            'urban_readers': ('Reader',),
        },

        'technical_validation': {
            'administrative_editors': ('Editor', 'AddressEditor'),
            'administrative_validators': ('Contributor', 'AddressEditor'),
            'technical_validators': ('Contributor', 'AddressEditor'),
            'inspection_editors': ('Reader',),
            'urban_readers': ('Reader',),
        },

        'waiting_for_agreement': {
            'administrative_editors': ('Editor', 'AddressEditor'),
            'administrative_validators': ('Contributor', 'AddressEditor'),
            'inspection_editors': ('Reader',),
            'urban_readers': ('Reader',),
        },

        'waiting_to_finalize': {
            'administrative_editors': ('Editor', 'AddressEditor'),
            'administrative_validators': ('Contributor', 'AddressEditor'),
            'inspection_editors': ('Reader',),
            'urban_readers': ('Reader',),
        },

        'in_court': {
            'administrative_editors': ('Editor', 'AddressEditor'),
            'administrative_validators': ('Contributor', 'AddressEditor'),
            'inspection_editors': ('Reader',),
            'urban_readers': ('Reader',),
        },

        'ended': {
            'administrative_editors': ('Editor', 'AddressEditor'),
            'administrative_validators': ('Contributor', 'AddressEditor'),
            'inspection_editors': ('Reader',),
            'urban_readers': ('Reader',),
        },
    }
