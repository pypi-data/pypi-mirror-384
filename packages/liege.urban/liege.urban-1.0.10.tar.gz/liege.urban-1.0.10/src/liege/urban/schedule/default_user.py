# -*- coding: utf-8 -*-

from imio.schedule.content.logic import AssignTaskGroup
from imio.schedule.content.logic import AssignTaskUser

from plone import api


class SurveyGroup(AssignTaskGroup):
    """
    Adapts a TaskContainer(the licence) into a default user
    to assign to its tasks (the licence folder manager).
    """

    def group_id(self):
        return 'survey_editors'


class LiegeDefaultTaskOwner(AssignTaskUser):
    """
    """

    def user_id(self):
        """
        Should return:
            - the current user if he is in the task assigned group.
            - else, the first licence foldermanager in the task assigned group
            - else, the owner of the previous task with the same assigned group
            - else, the user 'TO ASSIGN'
        """
        task = self.task
        licence = self.task_container
        task_group = api.group.get(task.assigned_group)
        group_users = task_group.getGroupMemberIds()

        # try to assign licence foldermanager
        for foldermanager in licence.getFoldermanagers():
            user_id = foldermanager.getPloneUserId()
            if user_id in group_users:
                return user_id

        # try to assign current user
        user = api.user.get_current()
        user_id = user.getUserName()
        if user_id in group_users:
            return user_id

        # try to assign owner of previous task with the same group
        # TO IMPLEMENTS

        # return the user 'TO ASSIGN'
        return 'to_assign'
