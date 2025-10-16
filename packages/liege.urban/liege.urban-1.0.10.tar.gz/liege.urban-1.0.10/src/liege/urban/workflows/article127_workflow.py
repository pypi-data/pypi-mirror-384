# -*- coding: utf-8 -*-

from Products.urban.workflows.adaptation import SimplifyWorkflowAdaptation


class Article127WorkflowAdaptation(SimplifyWorkflowAdaptation):
    """
    Adapt article 127 workflow:
    - copy the Buildlicence workflow
    - remove the complete/incomplete states and the FD opinion state
    """

    states_to_remove = [
        "incomplete",
        "checking_completion",
        "FD_opinion",
    ]
    transitions_to_remove = [
        "ask_complements",
        "invalidate_completion",
        "receive_complements",
        "validate_report_2",
        "receive_FD_opinion",
    ]
    transitions_new_target = {
        "validate_address": "complete",
        "validate_temporary_address": "complete",
    }
