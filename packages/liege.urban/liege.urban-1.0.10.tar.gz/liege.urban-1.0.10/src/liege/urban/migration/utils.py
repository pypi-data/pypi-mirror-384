# -*- coding: utf-8 -*-

from plone import api


def refresh_workflow_permissions(workflow_id, folder_path=None, for_states=None):
    if not folder_path:
        folder_path = '/'.join(api.portal.get().getPhysicalPath())
    portal_workflow = api.portal.get_tool('portal_workflow')
    portal_catalog = api.portal.get_tool('portal_catalog')

    for at_type, wf_ids in portal_workflow._chains_by_type.items():
        if len(wf_ids) < 1:
            continue
        if wf_ids[0] == workflow_id:
            workflow = portal_workflow.getWorkflowById(wf_ids[0])
            query = {
                'path': {'query': folder_path},
                'portal_type': at_type,
            }
            if for_states is not None:
                query["review_state"] = for_states
            results = portal_catalog.unrestrictedSearchResults(query)
            for brain in results:
                obj = brain.getObject()
                workflow.updateRoleMappingsFor(obj)
                obj.reindexObjectSecurity()
                obj.reindexObject(idxs=['allowedRolesAndUsers'])
