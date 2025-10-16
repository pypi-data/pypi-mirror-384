# -*- coding: utf-8 -*-

from Products.urban.browser.licence.codt_uniquelicenceview import CODTUniqueLicenceView
from Products.urban.browser.licence.licenceedit import LicenceEditView
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import PloneMessageFactory as _


class CODTIntegratedLicenceView(CODTUniqueLicenceView):
    """
      This manage the view of BuildLicence
    """
    def __init__(self, context, request):
        super(CODTIntegratedLicenceView, self).__init__(context, request)
        self.context = context
        self.request = request
        # disable portlets on licences
        self.request.set('disable_plone.rightcolumn', 1)
        self.request.set('disable_plone.leftcolumn', 1)
        plone_utils = getToolByName(context, 'plone_utils')
        if not self.context.getParcels():
            plone_utils.addPortalMessage(_('warning_add_a_parcel'), type="warning")
        if not self.context.getApplicants():
            plone_utils.addPortalMessage(_('warning_add_an_applicant'), type="warning")
        if self.hasOutdatedParcels():
            plone_utils.addPortalMessage(_('warning_outdated_parcel'), type="warning")

    def getMacroViewName(self):
        return 'codt_integratedlicence-macros'

    def getTabs(self):
        # display the environment tab all the time (conditionnal in
        # Products.urban)
        tabs = super(CODTIntegratedLicenceView, self).getTabs()
        return tabs


class CODT_IntegratedLicenceEditView(LicenceEditView):
    """
    """

    def getTabs(self):
        cfg = self.getLicenceConfig()
        available_tabs = self.context.schema.getSchemataNames()
        tabs = []
        # display the environment tab all the time (conditionnal in
        # Products.urban)
        for active_tab in cfg.getActiveTabs():
            tab = {
                'id': 'urban_{}'.format(active_tab['value']),
                'display_name': active_tab['display_name']
            }
            if tab['id'] in available_tabs:
                tabs.append(tab)
        return tabs
