# -*- coding: utf-8 -*-

from liege.urban.interfaces import IShore

from plone.indexer import indexer

from Products.urban.interfaces import IBaseAllBuildLicence
from Products.urban.interfaces import IGenericLicence

from zope.component import queryAdapter


@indexer(IGenericLicence)
def genericlicence_shore_index(licence):
    """
    Index Liège shore value
    """
    adapter = queryAdapter(licence, IShore)
    shore = adapter.get_shore()
    return shore


@indexer(IBaseAllBuildLicence)
def allbuildlicences_decisiondate(licence):
    decision_event = licence.getLastTheLicence()
    if decision_event:
        return decision_event.getDecisionDate()
