# -*- coding: utf-8 -*-

from plone import api


class IsLeaderUser(object):
    """
    Return is a user is in the group of the 'folder_tendency' field
    of the unique licence
    """

    def __init__(self, context, request):
        self.licence = context
        self.request = request
        self.tendency_mapping = {
            'env': set([
                'administrative_editors_environment',
                'administrative_validators_environment',
                'technical_editors_environment',
                'technical_validators_environment',
            ]),
            'urb': set([
                'administrative_editors',
                'administrative_validators',
                'technical_editors',
                'technical_validators',
            ]),
            '': set([])
        }

    def __call__(self):
        """
        """
        current_user = api.user.get_current()
        is_admin = self.is_admin(current_user)
        if is_admin:
            return True
        user_groups = self.get_groups_ids(current_user)
        is_leader = self.is_leader(current_user, user_groups)
        return is_leader

    def get_groups_ids(self, user):
        user_groups = set([g.id for g in api.group.get_groups(user=user)])
        return user_groups

    def is_admin(self, user):
        is_admin = api.user.get_permissions(user=user, obj=self.licence)['Manage portal']
        return is_admin

    def is_leader(self, user, user_groups):
        tendency_groups = self.tendency_mapping.get(self.licence.getFolderTendency(), set([]))
        is_leader = bool(tendency_groups.intersection(user_groups))
        return is_leader

    def is_in_group(self, groupname, groups_to_check):
        groups = self.tendency_mapping.get(groupname, set([]))
        is_in_group = bool(groups.intersection(groups_to_check))
        return is_in_group


class IsEnvironmentLeader(IsLeaderUser):
    """
    Return is a user is in environment group and if licence
    'folder_tendency' is environment.
    """

    def __call__(self):
        """
        """
        current_user = api.user.get_current()
        is_admin = self.is_admin(current_user)
        if is_admin:
            return True
        user_groups = self.get_groups_ids(current_user)
        is_leader = self.is_leader(current_user, user_groups)
        is_environment = self.is_in_group('env', user_groups)
        return is_leader and is_environment


class IsEnvironmentUser(IsLeaderUser):
    """
    Return is a user is in environment group
    """

    def __call__(self):
        """
        """
        current_user = api.user.get_current()
        is_admin = self.is_admin(current_user)
        if is_admin:
            return True
        user_groups = self.get_groups_ids(current_user)
        is_environment = self.is_in_group('env', user_groups)
        return is_environment


class IsUrbanLeader(IsLeaderUser):
    """
    Return is a user is in urban group and if licence
    'folder_tendency' is urban.
    """

    def __call__(self):
        """
        """
        current_user = api.user.get_current()
        is_admin = self.is_admin(current_user)
        if is_admin:
            return True
        user_groups = self.get_groups_ids(current_user)
        is_leader = self.is_leader(current_user, user_groups)
        is_urban = self.is_in_group('urb', user_groups)
        return is_leader and is_urban


class IsUrbanUser(IsLeaderUser):
    """
    Return is a user is in urban group
    """

    def __call__(self):
        """
        """
        current_user = api.user.get_current()
        is_admin = self.is_admin(current_user)
        if is_admin:
            return True
        user_groups = self.get_groups_ids(current_user)
        is_urban = self.is_in_group('urb', user_groups)
        return is_urban
