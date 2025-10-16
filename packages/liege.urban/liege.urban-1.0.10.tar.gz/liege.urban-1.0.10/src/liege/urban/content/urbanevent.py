# -*- coding: utf-8 -*-

from liege.urban import UrbanMessage as _

from Products.Archetypes.atapi import Schema
from Products.Archetypes.atapi import RichWidget
from Products.Archetypes.atapi import TextField

from Products.urban.interfaces import IOptionalFields
from Products.urban.UrbanEvent import UrbanEvent
from Products.urban.utils import setOptionalAttributes

from zope.interface import implements


specific_schema = Schema((
    TextField(
        name='pmObject',
        allowable_content_types=('text/html',),
        widget=RichWidget(
            label=_('urban_label_pmObject', default='Pmobject'),
        ),
        default_method='getDefaultText',
        default_content_type='text/html',
        default_output_type='text/html',
        optional=True,
        pm_text_field=True,
    ),
    TextField(
        name='motivation',
        allowable_content_types=('text/html',),
        widget=RichWidget(
            label=_('urban_label_motivation', default='Motivation'),
        ),
        default_method='getDefaultText',
        default_content_type='text/html',
        default_output_type='text/html',
        optional=True,
        pm_text_field=True,
    ),
    TextField(
        name='device',
        allowable_content_types=('text/html',),
        widget=RichWidget(
            label=_('urban_label_device', default='Device'),
        ),
        default_method='getDefaultText',
        default_content_type='text/html',
        default_output_type='text/html',
        optional=True,
        pm_text_field=True,
    ),
    TextField(
        name='deviceContinuation',
        allowable_content_types=('text/html',),
        widget=RichWidget(
            label=_('urban_label_deviceContinuation', default='DeviceContinuation'),
        ),
        default_method='getDefaultText',
        default_content_type='text/html',
        default_output_type='text/html',
        optional=True,
        pm_text_field=True,
    ),
    TextField(
        name='deviceEnd',
        allowable_content_types=('text/html',),
        widget=RichWidget(
            label=_('urban_label_deviceEnd', default='DeviceEnd'),
        ),
        default_method='getDefaultText',
        default_content_type='text/html',
        default_output_type='text/html',
        optional=True,
        pm_text_field=True,
    ),
),)

optional_fields = [field.getName() for field in specific_schema.filterFields(isMetadata=False)]
setOptionalAttributes(specific_schema, optional_fields)


class UrbanEventOptionalFields(object):
    """
    """
    implements(IOptionalFields)

    def __init__(self, context):
        self.context = context

    def get(self):
        return specific_schema.fields()


def update_item_schema(baseSchema):

    UrbanEventSchema = baseSchema + specific_schema.copy()

    return UrbanEventSchema


UrbanEvent.schema = update_item_schema(UrbanEvent.schema)
