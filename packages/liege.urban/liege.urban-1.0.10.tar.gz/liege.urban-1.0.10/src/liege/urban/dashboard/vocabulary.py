# -*- coding: utf-8 -*-

from Products.urban.dashboard.vocabularies import WorkflowStatesVocabulary


class BuildLicenceWorkflowStates(WorkflowStatesVocabulary):
    """
    List all states of BuildLicence workflow.
    """

    workflow_name = 'buildlicence_workflow'
