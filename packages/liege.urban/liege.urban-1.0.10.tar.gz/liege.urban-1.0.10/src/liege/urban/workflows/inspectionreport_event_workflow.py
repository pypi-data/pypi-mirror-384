# -*- coding: utf-8 -*-

from liege.urban.workflows.urbanevent_workflow import StateRolesMapping as BaseRolesMapping


class StateRolesMapping(BaseRolesMapping):
    """
    """

    mapping = {
        'writing_report': {
            'inspection_editors': ('Editor',),
            'technical_editors': ('Editor',),
            'technical_validators': ('Contributor',),
            BaseRolesMapping.get_readers: ('Reader',),
        },

        'to_validate': {
            'inspection_editors': ('Reader',),
            'inspection_validators': ('Contributor',),
            'technical_editors': ('Reader',),
            'technical_validators': ('Contributor',),
            BaseRolesMapping.get_readers: ('Reader',),
        },

        'closed': {
            'inspection_editors': ('Reader',),
            'inspection_validators': ('Contributor',),
            'technical_editors': ('Contributor',),  # allow technical editors to reopen the event.
            'technical_validators': ('Contributor',),
            BaseRolesMapping.get_readers: ('Reader',),
        },

    }
