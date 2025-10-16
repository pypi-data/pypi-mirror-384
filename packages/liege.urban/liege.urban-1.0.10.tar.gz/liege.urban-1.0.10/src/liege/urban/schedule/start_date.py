# -*- coding: utf-8 -*-

from imio.schedule.content.logic import StartDate


class AskOpinionDate(StartDate):
    """
    Returns ask date of the opinion request.
    """

    def start_date(self):
        opinion_request = self.task_container
        ask_date = opinion_request.getTransmitDate()

        # case where we just pushed the 'ask_opinion' button but the date has
        # no been set yet.
        if not ask_date:
            for wf_action in opinion_request.workflow_history['opinion_request_workflow']:
                if wf_action['action'] == 'ask_opinion':
                    ask_date = wf_action['time']

        return ask_date


class ReportAnalysisDate(StartDate):
    """
    Returns analysis date of the report event.
    """

    def start_date(self):
        licence = self.task_container
        analyse_date = licence.creation_date

        for wf_action in licence.workflow_history['inspection_workflow'][::-1]:
            if wf_action['action'] in ['analyse', 'analyse2', 'analyse_again', 'reopen']:
                return wf_action['time']

        return analyse_date
