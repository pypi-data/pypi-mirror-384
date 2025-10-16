# -*- coding: utf-8 -*-

from imio.schedule.content.task_config import ITaskConfig
from imio.schedule.interfaces import IToIcon

from zope.interface import implements


class ToIconBase(object):
    """
    Base class to adapt a context into an icon.
    """
    implements(IToIcon)

    def __init__(self, context):
        self.context = context

    def _icon_url(self, icon_name):
        return '++resource++liege.urban/{}.png'.format(icon_name)


class ScheduleCollectionToIcon(ToIconBase):
    """
    Adapts a collection into a group icon.
    """

    def get_icon_url(self):
        """
        """
        cfg = self.context.aq_parent

        if ITaskConfig.providedBy(cfg) and cfg.default_assigned_group:
            return self._icon_url(cfg.default_assigned_group)

        return self._icon_url('all')


class TaskGroupToIcon(ToIconBase):
    """
    Adapts a task into a group icon.
    """

    def get_icon_url(self):
        """
        """
        assigned_group = self.context.assigned_group

        if assigned_group:
            return self._icon_url(assigned_group)

        return None
