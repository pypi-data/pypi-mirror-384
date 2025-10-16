# -*- coding: utf-8 -*-

from liege.urban.interfaces import IInternalOpinionRequestEvent


def set_dates(urban_event, event):
    """
    """

    # only automatcially set dates for internal opinion requests
    if not IInternalOpinionRequestEvent.providedBy(urban_event):
        return

    ask_date = None
    opinion_date = None

    for wf_action in urban_event.workflow_history['opinion_request_workflow']:
        if wf_action['action'] == 'ask_opinion':
            ask_date = wf_action['time']
        elif wf_action['action'] == 'send_opinion':
            opinion_date = wf_action['time']

    urban_event.setEventDate(ask_date)
    urban_event.setTransmitDate(ask_date)
    urban_event.setReceiptDate(opinion_date)
