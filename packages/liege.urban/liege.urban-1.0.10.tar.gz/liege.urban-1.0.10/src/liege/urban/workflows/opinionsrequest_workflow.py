# -*- coding: utf-8 -*-

from collections import OrderedDict

from imio.schedule.content.task import IAutomatedTask

from Products.urban.interfaces import IEnvironmentBase
from Products.urban.interfaces import ICODT_UniqueLicence
from Products.urban.workflows.adapter import LocalRoleAdapter

from plone import api


class StateRolesMapping(LocalRoleAdapter):
    """
    """
    def __init__(self, context):
        self.context = context
        self.licence = self.context.aq_parent

    def get_opinion_group(self, groupe_type='editors'):
        opinion_request = self.context

        portal_urban = api.portal.get_tool('portal_urban')
        schedule_config = portal_urban.opinions_schedule

        task = None
        for task_config in schedule_config.get_all_task_configs():
            for obj in opinion_request.objectValues():
                is_task = IAutomatedTask.providedBy(obj)
                if is_task and obj.task_config_UID == task_config.UID():
                    if obj.assigned_group.endswith(groupe_type):
                        task = obj
                        break

        if task:
            return (task.assigned_group,)

        return ('technical_editors', 'technical_editors_environment')

    def get_administrative_editors(self):
        if ICODT_UniqueLicence.providedBy(self.licence):
            return ('administrative_editors_environment', 'administrative_editors')
        if IEnvironmentBase.providedBy(self.licence):
            return ('administrative_editors_environment',)
        return ('administrative_editors',)

    def get_administrative_validators(self):
        if ICODT_UniqueLicence.providedBy(self.licence):
            return ('administrative_validators_environment', 'administrative_validators')
        if IEnvironmentBase.providedBy(self.licence):
            return ('administrative_validators_environment',)
        return ('administrative_validators',)

    def get_opinion_editor(self):
        return self.get_opinion_group('editors')

    def get_opinion_validator(self):
        return self.get_opinion_group('validators')

    def get_opinion_editor_role(self):
        groups = self.get_opinion_editor()
        if 'technical_editors' in groups:
            return ('Reader', 'Contributor',)
        return ('Reader', 'Editor',)

    def get_technical_roles(self):
        if 'technical_editors' in self.get_opinion_editor():
            return ('Reader', 'Contributor',)
        return ('Reader',)

    mapping = {
        'creation': OrderedDict([
            (get_administrative_editors, ('Editor',)),
            (get_administrative_validators, ('Contributor',)),
            ('opinions_editors', ('Reader',)),
            ('Voirie_editors', ('Reader',)),
            ('Voirie_validators', ('Reader',)),
            ('survey_editors', ('Reader',)),
            (LocalRoleAdapter.get_readers, ('Reader',)),
        ]),

        'waiting_opinion': OrderedDict([
            (get_administrative_editors, (get_technical_roles,)),
            (get_administrative_validators, (get_technical_roles,)),
            ('technical_editors', (get_technical_roles,)),
            ('Voirie_editors', ('Reader',)),   # !!! order matters, let voirie role be overwritten
            ('Voirie_validators', ('Reader',)),# by ('get_opinion_...' if needed
            (get_opinion_editor, (get_opinion_editor_role,)),
            (get_opinion_validator, (get_opinion_editor_role,)),
            ('survey_editors', ('Reader',)),
            (LocalRoleAdapter.get_readers, ('Reader',)),
        ]),

        'opinion_validation': OrderedDict([
            ('Voirie_editors', ('Reader',)),   # !!! order matters, let voirie role be overwritten
            ('Voirie_validators', ('Reader',)),# by ('get_opinion_...' if needed
            (get_opinion_editor, ('Reader',)),
            (get_opinion_validator, ('Reader', 'Contributor',)),
            ('survey_editors', ('Reader',)),
            (LocalRoleAdapter.get_readers, ('Reader',)),
        ]),

        'opinion_given': OrderedDict([
            ('Voirie_editors', ('Reader',)),   # !!! order matters, let voirie role be overwritten
            ('Voirie_validators', ('Reader',)),# by ('get_opinion_...' if needed
            (get_opinion_editor, (get_technical_roles,)),
            (get_opinion_validator, (get_technical_roles,)),
            ('administrative_editors', (get_technical_roles,)),
            ('survey_editors', ('Reader',)),
            (LocalRoleAdapter.get_readers, ('Reader',)),
        ]),

    }
