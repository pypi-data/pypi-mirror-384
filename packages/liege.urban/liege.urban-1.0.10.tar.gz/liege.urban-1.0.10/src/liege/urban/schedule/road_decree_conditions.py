# -*- coding: utf-8 -*-
from Products.urban import interfaces
from imio.schedule.content.condition import Condition
from plone import api

class StreetTechnicalAnalysisCompleted(Condition):

    def evaluate(self):
        licence = self.task_container
        if licence.getRoadAnalysis():
            return True
        return False


class StreetTechnicalAnalysisValidated(Condition):

    def evaluate(self):
        # XXX Should be implemented
        return True


class DecreeProjectWrited(Condition):

    def evaluate(self):
        # XXX Should be implemented
        return True


class DecreeProjectValidatedSended(Condition):

    def evaluate(self):
        licence = self.task_container

        decree_project_validated_sended = False
        college_event = licence.getLastEvent(interfaces.ISimpleCollegeEvent)
        if college_event:
            decree_project_validated_sended = api.content.get_state(college_event) != 'closed'

        return decree_project_validated_sended


class CollegeInProgress(Condition):

    def evaluate(self):
        licence = self.task_container

        college_in_progress = False
        college_event = licence.getLastEvent(interfaces.ISimpleCollegeEvent)
        if college_event:
            college_in_progress = api.content.get_state(college_event) != 'closed'

        return college_in_progress


class CollegeCompleted(Condition):

    def evaluate(self):
        licence = self.task_container

        college_done = False
        college_event = licence.getLastEvent(interfaces.ISimpleCollegeEvent)
        if college_event:
            college_done = api.content.get_state(college_event) == 'closed'

        return college_done


class CouncilInProgress(Condition):

    def evaluate(self):
        licence = self.task_container

        council_in_progress = False
        council_event = licence.getLastEvent(interfaces.ISimpleCollegeEvent)
        if council_event:
            council_in_progress = api.content.get_state(council_event) != 'closed'

        return council_in_progress


class CouncilCompleted(Condition):

    def evaluate(self):
        licence = self.task_container

        council_completed = False
        council_event = licence.getLastEvent(interfaces.ISimpleCollegeEvent)
        if council_event:
            council_completed = api.content.get_state(council_event) == 'closed'

        return council_completed


class DisplayInProgress(Condition):

    def evaluate(self):
        licence = self.task_container

        display_in_progress = False
        display_event = licence.getLastEvent(interfaces.IMayorCollegeEvent)
        if display_event:
            display_in_progress = api.content.get_state(display_event) != 'closed'

        return display_in_progress


class DisplayCompleted(Condition):

    def evaluate(self):
        licence = self.task_container

        display_completed = False
        display_event = licence.getLastEvent(interfaces.IMayorCollegeEvent)
        if display_event:
            display_completed = api.content.get_state(display_event) == 'closed'

        return display_completed