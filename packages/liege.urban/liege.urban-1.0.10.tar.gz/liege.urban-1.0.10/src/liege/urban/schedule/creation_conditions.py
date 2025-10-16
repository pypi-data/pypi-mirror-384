# -*- coding: utf-8 -*-

from imio.schedule.content.condition import CreationCondition

from Products.urban.schedule.conditions.creation import InspectionCreationCondition

from plone import api

from zope.component import getMultiAdapter


class LicenceInValidatingAddressState(CreationCondition):
    """
    """

    def evaluate(self):
        licence = self.task_container
        return api.content.get_state(licence) == 'validating_address'


class AcknowledgmentProposedToValidationCondition(CreationCondition):
    """
    """

    def evaluate(self):
        licence = self.task_container
        ack_event = licence.getLastAcknowledgment()
        if not ack_event:
            return False

        return api.content.get_state(ack_event) == 'to_validate'


class AcknowledgmentToWriteCondition(CreationCondition):
    """
    """

    def evaluate(self):
        licence = self.task_container
        ack_event = licence.getLastAcknowledgment()
        if not ack_event:
            return True

        return api.content.get_state(ack_event) == 'draft'


class PreliminaryAdviceCondition(CreationCondition):
    """
    """
    def __init__(self, licence, task_config):
        super(PreliminaryAdviceCondition, self).__init__(licence, task_config)
        self.preliminary_advice_event = licence.getLastInternalPreliminaryAdvice()


class PreliminaryAdviceEventCreated(PreliminaryAdviceCondition):
    """
    Preliminary advice event is created and proposed to technical validation
    """

    def evaluate(self):
        if not self.preliminary_advice_event:
            return False
        return api.content.get_state(self.preliminary_advice_event) == 'in_progress'


class PreliminaryAdviceWritten(PreliminaryAdviceCondition):
    """
    Preliminary advice event is created and proposed to technical validation
    """

    def evaluate(self):
        if not self.preliminary_advice_event:
            return False
        return api.content.get_state(self.preliminary_advice_event) == 'technical_validation'


class PreliminaryAdviceTechnicalValidationDone(PreliminaryAdviceCondition):
    """
    Preliminary advice event is proposed to executive validation
    """

    def evaluate(self):
        if not self.preliminary_advice_event:
            return False
        return api.content.get_state(self.preliminary_advice_event) == 'executive_validation'


class FTOpinionStateOrIsTemporaryLicence(CreationCondition):
    """
    Preliminary advice event is proposed to executive validation
    """

    def evaluate(self):
        licence = self.task_container
        if licence.getProcedureChoice() == 'temporary':
            return api.content.get_state(licence) in ['complete', 'FT_opinion']
        return api.content.get_state(licence) == 'FT_opinion'


class MayorCollegeCondition(CreationCondition):
    """
    Base class for college event based conditions
    """

    def __init__(self, licence, task):
        super(MayorCollegeCondition, self).__init__(licence, task)
        self.mayor_events = licence.getAllMayorColleges()
        self.licence = licence


class OneMayorCollegeProjectCreated(MayorCollegeCondition):
    """
    At least one MayorCollege project is created
    """

    def evaluate(self):
        mayor_events = self.licence.getAllMayorColleges()
        if not mayor_events:
            return False
        for event in mayor_events:
            if api.content.get_state(event) == 'draft':
                return True
        return False


class OneMayorCollegeProjectWritten(MayorCollegeCondition):
    """
    At least one MayorCollege project is written
    """

    def evaluate(self):
        if not self.mayor_events:
            return False
        for event in self.mayor_events:
            if api.content.get_state(event) == 'to_validate':
                return True
        return False


class OneProjectsSentToMayorCollege(MayorCollegeCondition):
    """
    At least one MayorCollege project is sent to college and college is not finished
    """

    def evaluate(self):
        if not self.mayor_events:
            return False
        request = api.portal.getRequest()
        ws4pm = getMultiAdapter((api.portal.get(), request), name='ws4pmclient-settings')

        for event in self.mayor_events:
            try:
                sent = ws4pm.checkAlreadySentToPloneMeeting(event)
            except:
                return False
            if sent:
                try:
                    items = ws4pm._rest_searchItems({'externalIdentifier': event.UID()})
                except:
                    return False

                if not items:
                    return False

                accepted_states = ['accepted', 'accepted_but_modified', 'accepted_and_returned']
                mayor_college_done = items and items[0]['review_state'] in accepted_states

                if not mayor_college_done:
                    return True
        return False


class OneMayorCollegeMeetingDone(MayorCollegeCondition):
    """
    At least one MayorCollege project is sent to college, college is finished
    but the event is not closed
    """

    def evaluate(self):
        if not self.mayor_events:
            return False
        request = api.portal.getRequest()
        ws4pm = getMultiAdapter((api.portal.get(), request), name='ws4pmclient-settings')

        for event in self.mayor_events:
            if api.content.get_state(event) == 'closed':
                continue

            try:
                sent = ws4pm.checkAlreadySentToPloneMeeting(event)
            except:
                return False
            if sent:
                try:
                    items = ws4pm._rest_searchItems({'externalIdentifier': event.UID()})
                except:
                    continue

                if not items:
                    continue

                accepted_states = ['accepted', 'accepted_but_modified', 'accepted_and_returned']
                mayor_college_done = items and items[0]['review_state'] in accepted_states

                if mayor_college_done:
                    return True
        return False


class ShouldWriteInspectionReportEvent(InspectionCreationCondition):
    """
    The report event does not exist
    """

    def evaluate(self):
        report = self.get_current_inspection_report()
        if not report:
            return True

        return False


class ShouldReWriteInspectionReportEvent(InspectionCreationCondition):
    """
    The report event validation has been refused
    """

    def evaluate(self):
        report = self.get_current_inspection_report()
        if not report:
            return False

        workflow_history = report.workflow_history.values()[0]
        last_transition = workflow_history[-1]['action']
        # restart the task if the report validation is refused
        if last_transition == 'refuse':
            return True

        return False


class InspectionReportRedacted(CreationCondition):
    """
    InspectionReportEvent has been submited to validation.
    """

    def evaluate(self):
        licence = self.task_container
        report_event = licence.getLastReportEvent()
        if not report_event:
            return False

        is_redacted = api.content.get_state(report_event) == 'to_validate'
        return is_redacted


class EnvironmentValidationCondition(CreationCondition):
    """
    Base class for environnement validation event based conditions
    """

    def __init__(self, licence, task):
        super(EnvironmentValidationCondition, self).__init__(licence, task)
        self.validation_events = licence.getAllValidationEvents()
        self.licence = licence


class EventWithEnvValidationWritten(EnvironmentValidationCondition):
    """
    At least one validation event is proposed.
    """

    def evaluate(self):
        if not self.validation_events:
            return False
        for event in self.validation_events:
            if api.content.get_state(event) == 'to_validate':
                return True
        return False


class EventWithEnvValidationRefused(EnvironmentValidationCondition):
    """
    At least one validation event is refused.
    """

    def evaluate(self):
        if not self.validation_events:
            return False
        for event in self.validation_events:
            wf_history = event.workflow_history.get('env_validation_event_workflow', [])
            refused = len(wf_history) > 1
            if api.content.get_state(event) == 'draft' and refused:
                return True
        return False


class EventWithEnvValidationValidated(EnvironmentValidationCondition):
    """
    At least one validation event is validated.
    """

    def evaluate(self):
        if not self.validation_events:
            return False
        for event in self.validation_events:
            if api.content.get_state(event) == 'to_send':
                return True
        return False
