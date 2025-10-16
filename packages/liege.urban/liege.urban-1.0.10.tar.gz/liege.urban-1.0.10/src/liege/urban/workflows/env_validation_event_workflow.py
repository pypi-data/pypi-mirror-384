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
                'technical_editors',
            ],
            'environment_only': [
                'technical_editors_environment',
            ],
            'urban_and_environment': [
                'technical_editors',
                'technical_editors_environment',
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
                'technical_validators',
            ],
            'environment_only': [
                'technical_validators_environment',
            ],
            'urban_and_environment': [
                'technical_validators',
                'technical_validators_environment',
            ]
        }
        allowed_group = self.get_allowed_groups(licence, event)
        if allowed_group in mapping:
            return mapping.get(allowed_group)

    def get_admin_editors(self):
        """ """
        event = self.event
        licence = self.licence
        mapping = {
            'urban_only': [
                'technical_editors',
                'administrative_editors',
            ],
            'environment_only': [
                'technical_editors_environment',
                'administrative_editors_environment',
            ],
            'urban_and_environment': [
                'technical_editors',
                'technical_editors_environment',
                'administrative_editors',
                'administrative_editors_environment',
            ]
        }
        allowed_group = self.get_allowed_groups(licence, event)
        if allowed_group in mapping:
            return mapping.get(allowed_group)

    def get_admin_validators(self):
        """ """
        event = self.event
        licence = self.licence
        mapping = {
            'urban_only': [
                'technical_validators',
                'administrative_validators',
            ],
            'environment_only': [
                'technical_validators_environment',
                'administrative_validators_environment',
            ],
            'urban_and_environment': [
                'technical_validators',
                'technical_validators_environment',
                'administrative_validators',
                'administrative_validators_environment',
            ]
        }
        allowed_group = self.get_allowed_groups(licence, event)
        if allowed_group in mapping:
            return mapping.get(allowed_group)

    mapping = {
        'draft': {
            get_editors: ('Editor',),
            get_validators: ('Editor', 'Contributor'),
            BaseRolesMapping.get_readers: ('Reader',),
        },

        'to_validate': {
            get_editors: ('Reader',),
            get_validators: ('Editor', 'Contributor'),
            BaseRolesMapping.get_readers: ('Reader',),
        },

        'to_send': {
            get_admin_editors: ('Editor',),
            get_admin_validators: ('Editor', 'Contributor'),
            BaseRolesMapping.get_readers: ('Reader',),
        },

        'closed': {
            get_editors: ('Reader',),
            get_validators: ('Editor', 'Contributor'),
            BaseRolesMapping.get_readers: ('Reader',),
        },

    }
