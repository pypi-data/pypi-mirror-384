# -*- coding: utf-8 -*-

from imio.schedule.content.condition import EndCondition

from plone import api


class ParcelsAdded(EndCondition):
    """
    At least one parcel should be defined.
    """

    def evaluate(self):
        licence = self.task_container
        return bool(licence.getParcels())


class AllParcelsAreValidated(EndCondition):
    """
    All parcels should be in the state 'validated'.
    """

    def evaluate(self):
        licence = self.task_container
        for parcel in licence.getParcels():
            if api.content.get_state(parcel) != 'validated':
                return False
        return True


class LicenceInTemporaryAddressState(EndCondition):
    """
    """

    def evaluate(self):
        licence = self.task_container
        return api.content.get_state(licence) == 'waiting_address'


class WaitingForOpinionRequests(EndCondition):
    """
    All opinion request events should be in a state different than 'creation'.
    """

    def evaluate(self):
        licence = self.task_container
        or_events = licence.getOpinionRequests()

        if len(or_events) != len(licence.getSolicitOpinionsTo()):
            return False

        for or_event in or_events:
            if api.content.get_state(or_event) == 'creation':
                return False
        return True
