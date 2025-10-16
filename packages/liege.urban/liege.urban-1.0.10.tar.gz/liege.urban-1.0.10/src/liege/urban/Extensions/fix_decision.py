# -*- coding: utf-8 -*-

from DateTime import DateTime

from Products.urban.interfaces import IGenericLicence

from plone import api


def fix_decision():
    cat = api.portal.get_tool('portal_catalog')
    date_range = {'query': (DateTime('2017-03-01 00:00:00'), DateTime('2017-11-01 00:00:00'),), 'range': 'min:max'}
    brains = cat(created=date_range, object_provides=IGenericLicence.__identifier__)
    licences = [b.getObject() for b in brains]
    events = []
    for l in licences:
        events.extend(l.getAllEvents())
    to_correct = [e for e in events if e.getExternalDecision() == ['-1']]
    for e in to_correct:
        e.setExternalDecision('none')
