# -*- coding: utf-8 -*-

from collections import OrderedDict

from plone import api

from Products.urban.workflows.urbanevent_workflow import StateRolesMapping as BaseRolesMapping
from Products.urban.interfaces import IEnvClassBordering


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
                'administrative_editors',
            ],
            'environment_only': [
                'technical_editors_environment',
                'administrative_editors_environment',
            ],
            'urban_and_environment': [
                'technical_editors',
                'administrative_editors',
                'technical_editors_environment',
                'administrative_editors_environment',
            ]
        }
        allowed_group = self.get_allowed_groups(licence, event)
        if allowed_group in mapping:
            return mapping.get(allowed_group)

    def get_readers(self):
        """ """
        reader_groups = super(StateRolesMapping, self).get_readers()
        if IEnvClassBordering.providedBy(self.licence):
            reader_groups.append('urban_readers')
        if api.content.get_state(self.licence) in ['validating_address', 'waiting_address']:
            reader_groups.append('survey_editors')
        return reader_groups

    mapping = {
        'in_progress': OrderedDict([
            (get_readers, ('Reader',)),
            (get_editors, ('Editor',)),  # !!! order matters, let editors group be overwritten
        ]),

        'closed': OrderedDict([
            (get_readers, ('Reader',)),
            (get_editors, ('Editor',)),  # !!! order matters, let editors group be overwritten
        ]),
    }
