# -*- coding: utf-8 -*-

from liege.urban.workflows.urbanevent_workflow import StateRolesMapping as BaseRolesMapping


class StateRolesMapping(BaseRolesMapping):
    """
    """

    def get_editors(self):
        """ """
        event = self.event
        licence = self.licence
        mapping = {
            'urban_only': [
                'administrative_editors',
            ],
            'environment_only': [
                'administrative_editors_environment',
            ],
            'urban_and_environment': [
                'administrative_editors',
                'administrative_editors_environment',
            ]
        }
        allowed_group = self.get_allowed_groups(licence, event)
        if allowed_group in mapping:
            return mapping.get(allowed_group)

    def get_validators(self):
        """ """
        event = self.event
        licence = self.licence
        mapping = {
            'urban_only': [
                'administrative_validators',
            ],
            'environment_only': [
                'administrative_validators_environment',
            ],
            'urban_and_environment': [
                'administrative_validators',
                'administrative_validators_environment',
            ]
        }
        allowed_group = self.get_allowed_groups(licence, event)
        if allowed_group in mapping:
            return mapping.get(allowed_group)

    mapping = {
        'preparing_documents': {
            get_editors: ('Editor',),
            get_validators: ('Contributor',),
            BaseRolesMapping.get_readers: ('Reader',),
        },

        'to_validate': {
            get_validators: ('Contributor',),
            BaseRolesMapping.get_readers: ('Reader',),
        },

        'sending_documents': {
            get_editors: ('Editor',),
            get_validators: ('Contributor',),
            BaseRolesMapping.get_readers: ('Reader',),
        },

        'in_progress': {
            get_editors: ('Editor', 'ClaimantEditor'),
            get_validators: ('Contributor',  'ClaimantEditor'),
            BaseRolesMapping.get_readers: ('Reader',),
        },

        'closed': {
            get_editors: ('ClaimantEditor',),
            get_validators: ('Contributor', 'ClaimantEditor',),
            BaseRolesMapping.get_readers: ('Reader',),
        },

    }
