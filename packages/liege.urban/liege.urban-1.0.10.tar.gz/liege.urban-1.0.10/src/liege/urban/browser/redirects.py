# -*- coding: utf-8 -*-

from Products.urban.interfaces import IUrbanRootRedirects

from plone import api

from zope.interface import implements


class UrbanRootRedirects(object):
    """
    Adapter deault views to return for different urban liege groups.
    """
    implements(IUrbanRootRedirects)

    def __init__(self, user):
        self.user = user

    def get_redirection_path(self):
        """
        """
        if self.user.getId() is None:
            return None
        else:
            try:
                user_groups = api.group.get_groups(user=self.user)
            except AttributeError:  # This happen with admin user
                user_groups = []
            group_ids = [g.id for g in user_groups]
            if 'survey_editors' in group_ids:
                return 'urban/survey_schedule'
            if 'urban_readers' in group_ids or 'environment_readers' in group_ids:
                return 'urban'
            if 'opinions_editors' in group_ids:
                return 'urban/opinions_schedule'
            if 'Voirie_readers' in group_ids:
                return 'urban/roaddecrees'
            return 'urban'
