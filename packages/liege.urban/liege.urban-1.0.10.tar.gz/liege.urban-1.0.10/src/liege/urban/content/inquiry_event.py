# -*- coding: utf-8 -*-

from Products.urban.content.UrbanEventInquiry import UrbanEventInquiry

from liege.urban import UrbanMessage as _


def update_item_schema(baseSchema):

    EventSchema = baseSchema

    # remove hours from date format
    EventSchema['explanationStartSDate'].widget.show_hm = False
    EventSchema['explanationStartSDate'].widget.format = '%d/%m/%Y'
    EventSchema['claimsDate'].widget.show_hm = False
    EventSchema['claimsDate'].widget.format = '%d/%m/%Y'

    # rename fields
    EventSchema['explanationStartSDate'].widget.label = _('urban_label_explanationDate')
    EventSchema['claimsDate'].widget.label = _('urban_label_closeDate')

    return EventSchema


UrbanEventInquiry.schema = update_item_schema(UrbanEventInquiry.schema)
