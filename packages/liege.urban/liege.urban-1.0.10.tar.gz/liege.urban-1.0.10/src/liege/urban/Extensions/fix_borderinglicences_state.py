# -*- coding: utf-8 -*-

from plone import api

from Products.urban.interfaces import IEnvClassBordering


def fix_final_state():
    catalog = api.portal.get_tool('portal_catalog')
    licences_brains = catalog(
        object_provides=IEnvClassBordering.__identifier__,
        Creator='admin',
    )
    portal_workflow = api.portal.get_tool('portal_workflow')
    workflow_def = None

    for brain in licences_brains:
        if brain.review_state == 'final_decision_in_progress':
            licence = brain.getObject()
            workflow_def = workflow_def or portal_workflow.getWorkflowsFor(licence)[0]
            workflow_id = workflow_def.getId()
            workflow_state = portal_workflow.getStatusOf(workflow_id, licence)
            workflow_state['review_state'] = 'in_progress'
            portal_workflow.setStatusOf(workflow_id, licence, workflow_state.copy())
            licence.reindexObject()
            print "fixed state of {}".format(brain.Title)
