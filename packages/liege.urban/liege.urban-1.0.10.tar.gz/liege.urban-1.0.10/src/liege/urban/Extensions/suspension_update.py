# -*- coding: utf-8 -*-

from collective.wfadaptations.api import apply_from_registry

from imio.schedule.content.object_factories import EndConditionObject
from imio.schedule.content.object_factories import MacroEndConditionObject

from plone import api


def apply_wf_adaptations():
    apply_from_registry()


def add_suspension_state():
    """
    """
    # update the buildlicence workflow with the suspension state
    apply_from_registry()

    # update the schdule conditions
    portal_urban = api.portal.get_tool('portal_urban')
    schedule_cfg = portal_urban.buildlicence.schedule

    for task_cfg in schedule_cfg.get_all_task_configs():

        if task_cfg.id == 'suspension':
            continue

        # add 'suspension' to the ending states
        ending_states = task_cfg.ending_states
        if ending_states and 'suspension' not in ending_states:
            new_states = tuple(ending_states) + ('suspension',)
            task_cfg.ending_states = set(new_states)

        # add 'suspension' to the end conditions
        end_conditions = task_cfg.end_conditions or []
        end_condition_ids = end_conditions and [c.condition for c in end_conditions]
        suspension_id = 'urban.schedule.condition.suspension'
        if end_condition_ids and suspension_id not in end_condition_ids:
            if task_cfg.portal_type == 'MacroTaskConfig':
                suspension_condition = MacroEndConditionObject(suspension_id, 'OR')
            else:
                suspension_condition = EndConditionObject(suspension_id, 'OR')
            task_cfg.end_conditions = (suspension_condition,) + tuple(end_conditions)


def add_abandoned_state():
    """
    """
    # update the buildlicence workflow with the abandoned state
    apply_from_registry()

    # update the schedule conditions
    portal_urban = api.portal.get_tool('portal_urban')
    schedule_cfg = portal_urban.buildlicence.schedule

    for task_cfg in schedule_cfg.get_all_task_configs():
        # add 'abandoned' to the ending states
        ending_states = task_cfg.ending_states
        if ending_states and 'abandoned' not in ending_states:
            new_states = tuple(ending_states) + ('abandoned',)
            task_cfg.ending_states = set(new_states)
