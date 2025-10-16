# -*- coding: utf-8 -*-

from imio.schedule.content.object_factories import EndConditionObject
from imio.schedule.content.object_factories import FreezeConditionObject
from imio.schedule.content.object_factories import MacroEndConditionObject

from liege.urban.setuphandlers import _create_task_configs

from plone import api


def add_licence_ended_condition():
    """
    """
    portal_urban = api.portal.get_tool('portal_urban')
    for licence_config in portal_urban.objectValues('LicenceConfig'):
        schedule_cfg = licence_config.schedule

        for task_cfg in schedule_cfg.get_all_task_configs():

            # add 'licence_ended' to the end conditions
            ending_states = task_cfg.ending_states
            end_conditions = task_cfg.end_conditions or []
            end_condition_ids = end_conditions and [c.condition for c in end_conditions]
            condition_id = 'liege.urban.schedule.licence_ended'
            if (end_condition_ids or not ending_states) and condition_id not in end_condition_ids:
                if task_cfg.portal_type == 'MacroTaskConfig':
                    condition = MacroEndConditionObject(
                        condition=condition_id,
                        operator='OR',
                        display_status=False
                    )
                else:
                    condition = EndConditionObject(
                        condition=condition_id,
                        operator='OR',
                        display_status=False
                    )
                task_cfg.end_conditions = (condition,) + tuple(end_conditions)


def add_licence_freeze_thaw_states():
    """
    """
    suspension_licences = [
        'codt_buildlicence',
        'integratedlicence',
        'codt_integratedlicence',
        'codt_uniquelicence',
    ]
    suspension_task_cfg = {
        'type_name': 'TaskConfig',
        'id': 'suspension',
        'title': 'Dossiers suspendus',
        'default_assigned_group': 'technical_editors',
        'default_assigned_user': 'liege.urban.schedule.assign_task_owner',
        'creation_state': ('frozen_suspension',),
        'starting_states': ('frozen_suspension',),
        'end_conditions': (
            EndConditionObject('urban.schedule.condition.LicenceThawed'),
        ),
        'freeze_conditions': (
            FreezeConditionObject('urban.schedule.condition.False'),
        ),
        'start_date': 'urban.schedule.start_date.creation_date',
        'additional_delay': 0,
    }
    portal_urban = api.portal.get_tool('portal_urban')
    for licence_config in portal_urban.objectValues('LicenceConfig'):
        if licence_config.id not in suspension_licences:
            continue

        schedule_cfg = licence_config.schedule
        _create_task_configs(schedule_cfg, [suspension_task_cfg])

        for task_cfg in schedule_cfg.get_all_task_configs():

            # add 'frozen_suspension' to the end states
            task_cfg.freeze_states = ['frozen_suspension']
