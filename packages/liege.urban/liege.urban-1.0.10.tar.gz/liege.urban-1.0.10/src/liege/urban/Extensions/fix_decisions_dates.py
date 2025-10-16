# -*- coding: utf-8 -*-

from DateTime import DateTime

from plone import api

from Products.urban.interfaces import IGenericLicence


def fix_decisions_dates():
    catalog = api.portal.get_tool('portal_catalog')
    licences_brains = catalog(
        object_provides=IGenericLicence.__identifier__,
        Creator='admin',
#        created={
#            'query': [
#                DateTime('18/01/2011'), DateTime('19/03/2017')
#            ],
#            'range': 'minmax'
#        }
    )
    for brain in licences_brains:
        licence = brain.getObject()
        if hasattr(licence, 'getLastTheLicence'):
            decision_event = licence.getLastTheLicence()
            if decision_event:
                if decision_event.getEventDate() and not decision_event.getDecisionDate():
                    decision_event.setDecisionDate(decision_event.getEventDate())
                    print "fixed decision date of licence {}".format(licence.getReference())
