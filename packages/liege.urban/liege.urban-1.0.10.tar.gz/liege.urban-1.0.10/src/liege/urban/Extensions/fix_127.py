# -*- coding: utf-8 -*-

from Products.urban.interfaces import IArticle127

from plone import api


def fix_127_dates():
    """
    """
    catalog = api.portal.get_tool('portal_catalog')
    all_127_brains = catalog(object_provides=IArticle127.__identifier__)
    for brain in all_127_brains:
        licence = brain.getObject()
        licence_objs = licence.objectValues()
        FD_event = [obj for obj in licence_objs if obj.Title() == 'Transmis 2eme dossier RW']
        college_opinion_event = [obj for obj in licence_objs if obj.Title() == 'Avis du collège (FD)']
        decision_event = [obj for obj in licence_objs if obj.Title() == 'Décision du FD sur 127']
        if FD_event and college_opinion_event and decision_event:
            FD_event = FD_event[0]
            college_opinion_event = college_opinion_event[0]
            decision_event = decision_event[0]
            decision_event.setEventDate(college_opinion_event.getEventDate())
            college_opinion_event.setEventDate(FD_event.getEventDate())
            api.content.delete(FD_event)
