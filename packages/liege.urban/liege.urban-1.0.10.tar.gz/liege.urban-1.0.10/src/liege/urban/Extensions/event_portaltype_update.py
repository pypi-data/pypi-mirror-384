# -*- coding: utf-8 -*-

from plone import api


def update_event_portaltype():

    mapping = {
        'Products.urban.interfaces.IOpinionRequestEvent': 'UrbanEventOpinionRequest',
        'Products.urban.interfaces.IWalloonRegionOpinionRequestEvent': 'UrbanEventOpinionRequest',
        'Products.urban.interfaces.IInquiryEvent': 'UrbanEventInquiry',
        'Products.urban.interfaces.ICollegeEvent': 'UrbanEventCollege',
        'Products.urban.interfaces.ISimpleCollegeEvent': 'UrbanEventCollege',
        'Products.urban.interfaces.IAcknowledgmentEvent': 'UrbanEventAcknowledgment',
        'liege.urban.interfaces.IInternalOpinionRequestEvent': 'UrbanEventOpinionRequest',
    }

    catalog = api.portal.get_tool('portal_catalog')
    for brain in catalog(portal_type=['UrbanEventType', 'OpinionRequestEventType']):
        uet = brain.getObject()
        event_type_type = uet.getEventTypeType()
        event_portaltype = mapping.get(event_type_type, 'UrbanEvent')
        uet.setEventPortalType(event_portaltype)
