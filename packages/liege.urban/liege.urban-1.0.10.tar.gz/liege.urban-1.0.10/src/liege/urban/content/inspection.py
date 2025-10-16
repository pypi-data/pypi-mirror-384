# -*- coding: utf-8 -*-

from liege.urban import UrbanMessage as _
from liege.urban import interfaces

from Products.Archetypes.atapi import Schema
from Products.Archetypes.atapi import StringField

from Products.urban.content.licence.Inspection import Inspection

from plone import api


specific_schema = Schema((
    StringField(
        name='formal_notice_old_reference',
        widget=StringField._properties['widget'](
            size=60,
            label=_('urban_label_formal_notice_old_reference', default='Formal_notice_old_reference'),
        ),
        schemata='urban_description',
    ),
),)


def update_item_schema(baseSchema):
    LicenceSchema = baseSchema + specific_schema.copy()

    # move some fields
    LicenceSchema.moveField('formal_notice_old_reference', after='referenceDGATLP')
    return LicenceSchema


Inspection.schema = update_item_schema(Inspection.schema)


def updateTitle(self):
    """
        Update the title to clearly identify the licence
    """
    proprietary = ''
    proprietaries = [pro for pro in self.getProprietaries()
                     if api.content.get_state(pro) == 'enabled']
    if proprietaries:
        proprietary = ', '.join([prop.Title() for prop in proprietaries])
    AD_refs = self.getFormal_notice_old_reference()
    title = "{}{}{} - {}".format(
        self.getReference(),
        AD_refs and ' - {}'.format(AD_refs) or '',
        proprietary and ' - {}'.format(proprietary) or '',
        self.getLicenceSubject()
    )
    self.setTitle(title)
    self.reindexObject(idxs=('Title', 'sortable_title',))


def getLastBuidlingDivisionAttestationMail(self):
    return self.getLastEvent(interfaces.IInspectionBuidlingDivisionAttestationMail)


def getLastBuidlingDivisionAttestationCollege(self):
    return self.getLastEvent(interfaces.IInspectionBuidlingDivisionAttestationCollege)


Inspection.updateTitle = updateTitle
Inspection.getLastBuidlingDivisionAttestationMail = getLastBuidlingDivisionAttestationMail
Inspection.getLastBuidlingDivisionAttestationCollege = getLastBuidlingDivisionAttestationCollege
