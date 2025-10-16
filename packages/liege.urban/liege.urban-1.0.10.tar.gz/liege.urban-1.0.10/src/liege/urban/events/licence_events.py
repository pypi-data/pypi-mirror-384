# -*- coding: utf-8 -*-

from imio.schedule.utils import get_container_tasks

from plone import api


def reindex_licence_tasks(licence, event):
    """
    """
    with api.env.adopt_roles(['Manager']):
        for task in get_container_tasks(licence):
            task.reindexObject(idxs=['shore'])
