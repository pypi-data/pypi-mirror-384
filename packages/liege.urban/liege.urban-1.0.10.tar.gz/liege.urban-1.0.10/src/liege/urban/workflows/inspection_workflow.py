# -*- coding: utf-8 -*-

from Products.urban.workflows.adapter import LocalRoleAdapter


class StateRolesMapping(LocalRoleAdapter):
    """ """

    mapping = {
        'creation': {
            'inspection_editors': ('Editor', 'AddressEditor'),
            'administrative_editors': ('Editor', 'AddressEditor'),
            'administrative_validators': ('Contributor', 'AddressEditor'),
            'urban_readers': ('Reader',),
        },

        'first_administrative_answer': {
            'inspection_editors': ('Reader',),
            'administrative_editors': ('Editor', 'AddressEditor'),
            'administrative_validators': ('Contributor', 'AddressEditor'),
            'urban_readers': ('Reader',),
        },

        'analysis': {
            'inspection_editors': ('Editor', 'AddressEditor'),
            'inspection_validators': ('Contributor', 'AddressEditor'),
            'administrative_editors': ('Editor', 'AddressEditor'),
            'administrative_validators': ('Contributor', 'AddressEditor'),
            'urban_readers': ('Reader',),
        },

        'administrative_answer': {
            'inspection_editors': ('Reader',),
            'administrative_editors': ('Editor', 'AddressEditor'),
            'administrative_validators': ('Contributor', 'AddressEditor'),
            'urban_readers': ('Reader',),
        },

        'inspection_follow_up': {
            'inspection_editors': ('Editor', 'AddressEditor'),
            'administrative_editors': ('Editor', 'AddressEditor'),
            'administrative_validators': ('Contributor', 'AddressEditor'),
            'urban_readers': ('Reader',),
        },

        'ended': {
            'inspection_editors': ('Editor', 'AddressEditor'),
            'administrative_editors': ('Editor', 'AddressEditor'),
            'administrative_validators': ('Contributor', 'AddressEditor'),
            'urban_readers': ('Reader',),
        },
    }
