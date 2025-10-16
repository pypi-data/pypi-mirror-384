# -*- coding: utf-8 -*-

from imio.schedule.content.task import IAutomatedTask

from liege.urban.interfaces import IShore

from plone.indexer import indexer

from zope.component import queryAdapter


@indexer(IAutomatedTask)
def task_reference_index(task):
    """
    Index licence reference on their tasks to be able
    to query on it.
    """
    licence = task.get_container()
    reference = licence.getReference()
    return reference


@indexer(IAutomatedTask)
def task_shore_index(task):
    """
    Index licence shore on their tasks to be able
    to query on it.
    """
    licence = task.get_container()
    adapter = queryAdapter(licence, IShore)
    shore = adapter.get_shore()
    return shore
