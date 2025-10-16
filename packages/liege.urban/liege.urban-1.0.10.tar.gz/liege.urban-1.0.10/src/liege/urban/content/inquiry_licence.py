# -*- coding: utf-8 -*-

from Products.urban.content.CODT_Inquiry import CODT_Inquiry
from Products.urban.content.licence.Article127 import Article127
from Products.urban.content.licence.BuildLicence import BuildLicence
from Products.urban.content.licence.CODT_Article127 import CODT_Article127
from Products.urban.content.licence.CODT_BuildLicence import CODT_BuildLicence
from Products.urban.content.licence.CODT_IntegratedLicence import CODT_IntegratedLicence
from Products.urban.content.licence.CODT_ParcelOutLicence import CODT_ParcelOutLicence
from Products.urban.content.licence.CODT_UniqueLicence import CODT_UniqueLicence
from Products.urban.content.licence.CODT_UrbanCertificateTwo import CODT_UrbanCertificateTwo
from Products.urban.content.licence.EnvClassOne import EnvClassOne
from Products.urban.content.licence.EnvClassThree import EnvClassThree
from Products.urban.content.licence.EnvClassTwo import EnvClassTwo
from Products.urban.content.licence.IntegratedLicence import IntegratedLicence
from Products.urban.content.licence.MiscDemand import MiscDemand
from Products.urban.content.licence.ParcelOutLicence import ParcelOutLicence
from Products.urban.content.licence.PatrimonyCertificate import PatrimonyCertificate
from Products.urban.content.licence.UniqueLicence import UniqueLicence
from Products.urban.content.licence.UrbanCertificateTwo import UrbanCertificateTwo

from liege.urban import UrbanMessage as _


def update_item_schema(baseSchema):

    LicenceSchema = baseSchema

    # some fields are only visible in edit
    LicenceSchema['investigationArticlesText'].widget.visible = {'edit': 'visible', 'view': 'invisible'}
    LicenceSchema['derogationDetails'].widget.visible = {'edit': 'visible', 'view': 'invisible'}
    LicenceSchema['investigationReasons'].widget.visible = {'edit': 'visible', 'view': 'invisible'}
    LicenceSchema['demandDisplay'].widget.visible = {'edit': 'visible', 'view': 'invisible'}
    LicenceSchema['investigationDetails'].widget.visible = {'edit': 'visible', 'view': 'invisible'}

    # reorder fields
    LicenceSchema.moveField('derogation', after='investigationArticlesText')
    LicenceSchema.moveField('derogationDetails', after='derogation')
    LicenceSchema.moveField('investigationReasons', after='demandDisplay')
    LicenceSchema.moveField('investigationDetails', after='roadModificationSubject')

    # re translate some fields
    LicenceSchema['solicitOpinionsTo'].widget.label = _('urban_label_solicitExternalOpinionsTo')
    LicenceSchema['solicitOpinionsToOptional'].widget.label = _('urban_label_solicitInternalOpinionsTo')

    return LicenceSchema


licence_classes = [
    Article127, BuildLicence, CODT_Article127, CODT_BuildLicence, CODT_IntegratedLicence,
    CODT_ParcelOutLicence, CODT_UniqueLicence, CODT_UrbanCertificateTwo, CODT_Inquiry,
    IntegratedLicence, MiscDemand, ParcelOutLicence, PatrimonyCertificate, UniqueLicence,
    UrbanCertificateTwo, EnvClassOne, EnvClassTwo, EnvClassThree
]

for licence_class in licence_classes:
    licence_class.schema = update_item_schema(licence_class.schema)
