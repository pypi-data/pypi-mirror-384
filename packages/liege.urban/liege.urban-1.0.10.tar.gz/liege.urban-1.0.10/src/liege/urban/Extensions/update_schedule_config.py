# -*- coding: utf-8 -*-

from imio.schedule.content.task_config import ITaskConfig

from plone import api


def set_administrative_default_owner():
    cat = api.portal.get_tool('portal_catalog')
    task_configs = [br.getObject() for br in cat(object_provides=ITaskConfig.__identifier__)]
    for task_config in task_configs:
        if task_config.default_assigned_group == 'administrative_editors':
            task_config.default_assigned_user = 'to_assign'
