# -*- coding: utf-8 -*-

from imio.schedule.interfaces import IDefaultEndingStates
from imio.schedule.interfaces import IDefaultFreezeStates
from imio.schedule.interfaces import IDefaultThawStates

from liege.urban.config import LICENCE_FINAL_STATES

from plone import api

from zope.interface import implements


class LiegeLicencesDefaultEndingStates(object):
    """
    """
    implements(IDefaultEndingStates)

    def __init__(self, task_container):
        self.licence = task_container

    def __call__(self):
        return LICENCE_FINAL_STATES


class LiegeLicencesDefaultFreezeStates(object):
    """
    """
    implements(IDefaultFreezeStates)

    def __init__(self, task_container):
        self.licence = task_container

    def __call__(self):
        return ['frozen_suspension']


class LiegeLicencesDefaultThawStates(object):
    """
    """
    implements(IDefaultThawStates)

    def __init__(self, task_container):
        self.licence = task_container

    def __call__(self):
        workflow_tool = api.portal.get_tool('portal_workflow')
        licence = self.context
        workflow_def = workflow_tool.getWorkflowsFor(licence)[0]
        states = [state_id for state_id in workflow_def.states.keys() if state_id != 'frozen_suspension']
        return states
