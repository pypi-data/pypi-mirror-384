# encoding: utf-8

from imio.schedule.content.object_factories import CreationConditionObject
from imio.schedule.content.object_factories import MacroCreationConditionObject
from imio.schedule.content.object_factories import MacroRecurrenceConditionObject
from imio.schedule.content.object_factories import RecurrenceConditionObject

from plone import api


import logging

logger = logging.getLogger('urban: migrations')


def migrate_internal_advices(context):
    """ """
    logger = logging.getLogger('urban: migrate colleg urban event types')
    logger.info("starting migration step")
    catalog = api.portal.get_tool('portal_catalog')
    logger.info("start migration of opinion request even types")
    to_migrate = [b.getObject() for b in catalog(portal_type='OpinionRequestEventType') if b.id.startswith('ask_')]
    for event_type in to_migrate:
        event_type.setIs_internal_service(True)
        event_type.setInternal_service(event_type.id.split('_')[1])
    logger.info("migrated opinion request even types")

    logger.info("start migration of internal services schedule config")
    portal_urban = api.portal.get_tool('portal_urban')
    schedule_folder = portal_urban.opinions_schedule
    to_fix = [b for b in schedule_folder.objectValues()[1:] if b.recurrence_conditions]
    for task_config in to_fix:
        creation_conditions = task_config.creation_conditions
        if creation_conditions and 'liege' in creation_conditions[0].condition:
            if task_config.portal_type == 'MacroTaskConfig':
                new_condition = MacroCreationConditionObject('urban.schedule.condition.is_internal_opinion')
            else:
                new_condition = CreationConditionObject('urban.schedule.condition.is_internal_opinion')
            task_config.creation_conditions = (new_condition,)
        recurrence_conditions = task_config.recurrence_conditions
        if recurrence_conditions and 'liege' in recurrence_conditions[0].condition:
            if task_config.portal_type == 'MacroTaskConfig':
                new_condition = MacroRecurrenceConditionObject('urban.schedule.condition.is_internal_opinion')
            else:
                new_condition = RecurrenceConditionObject('urban.schedule.condition.is_internal_opinion')
            task_config.recurrence_conditions = (new_condition,)
        if task_config.id.endswith('_1'):
            api.content.rename(obj=task_config, new_id='give_{}_opinion'.format(task_config.id.split('_')[1]))
    logger.info("migrated internal services schedule config")
    logger.info("migration step done!")


def migrate(context):
    logger = logging.getLogger('urban: migrate to 2.3')
    logger.info("starting migration steps")
    setup_tool = api.portal.get_tool('portal_setup')
    setup_tool.runImportStepFromProfile('profile-Products.urban:preinstall', 'update-workflow-rolemap')
    migrate_internal_advices(context)
    logger.info("migration done!")
