# -*- coding: utf-8 -*-

from imio.schedule.config import CREATION
from imio.schedule.config import STARTED
from imio.schedule.config import states_by_status
from imio.schedule.content.task import IAutomatedTask

from liege.urban.config import LICENCE_FINAL_STATES

from plone import api

from Products.urban.interfaces import IGenericLicence

from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent


def close_old_tasks():
    catalog = api.portal.get_tool('portal_catalog')
    states = states_by_status[CREATION] = states_by_status[STARTED]
    task_brains = catalog(
        object_provides=IAutomatedTask.__identifier__,
        review_state=states
    )
    open_tasks = [b.getObject() for b in task_brains]
    licences = set([t.aq_parent for t in open_tasks if IGenericLicence.providedBy(t.aq_parent) and api.content.get_state(t.aq_parent) in LICENCE_FINAL_STATES])
    for licence in licences:
        notify(ObjectModifiedEvent(licence))
        print "notified licence {}".format(licence)
