# -*- coding: utf-8 -*-

from liege.urban import UrbanMessage as _
from liege.urban.interfaces import IShore
from liege.urban.licence_fields_permissions import set_field_permissions

from Products.Archetypes.atapi import Schema

from Products.urban.content.licence.Article127 import Article127
from Products.urban.content.licence.BuildLicence import BuildLicence
from Products.urban.content.licence.CODT_Article127 import CODT_Article127
from Products.urban.content.licence.CODT_BuildLicence import CODT_BuildLicence
from Products.urban.content.licence.CODT_IntegratedLicence import CODT_IntegratedLicence
from Products.urban.content.licence.CODT_UniqueLicence import CODT_UniqueLicence
from Products.urban.content.licence.CODT_UrbanCertificateBase import CODT_UrbanCertificateBase
from Products.urban.content.licence.CODT_UrbanCertificateTwo import CODT_UrbanCertificateTwo
from Products.urban.content.licence.Declaration import Declaration
from Products.urban.content.licence.Division import Division
from Products.urban.content.licence.EnvClassOne import EnvClassOne
from Products.urban.content.licence.EnvClassThree import EnvClassThree
from Products.urban.content.licence.EnvClassTwo import EnvClassTwo
from Products.urban.content.licence.GenericLicence import GenericLicence
from Products.urban.content.licence.Inspection import Inspection
from Products.urban.content.licence.IntegratedLicence import IntegratedLicence
from Products.urban.content.licence.MiscDemand import MiscDemand
from Products.urban.content.licence.ParcelOutLicence import ParcelOutLicence
from Products.urban.content.licence.PatrimonyCertificate import PatrimonyCertificate
from Products.urban.content.licence.RoadDecree import RoadDecree
from Products.urban.content.licence.Ticket import Ticket
from Products.urban.content.licence.UniqueLicence import UniqueLicence
from Products.urban.content.licence.UrbanCertificateBase import UrbanCertificateBase
from Products.urban.content.licence.UrbanCertificateTwo import UrbanCertificateTwo

from zope.i18n import translate
from zope.component import queryAdapter

specificSchema = Schema((
),)


def update_item_schema(baseSchema):

    LicenceSchema = baseSchema + specificSchema.copy()

    # some fields are edit only
    LicenceSchema['missingPartsDetails'].widget.visible = {'edit': 'visible', 'view': 'invisible'}
    LicenceSchema['protectedBuildingDetails'].widget.visible = {'edit': 'visible', 'view': 'invisible'}
    rcu_details = LicenceSchema.get('rcuDetails', None)
    if rcu_details:
        rcu_details.widget.visible = {'edit': 'visible', 'view': 'invisible'}
    LicenceSchema['prenuDetails'].widget.visible = {'edit': 'visible', 'view': 'invisible'}
    LicenceSchema['prevuDetails'].widget.visible = {'edit': 'visible', 'view': 'invisible'}
    LicenceSchema['airportNoiseZoneDetails'].widget.visible = {'edit': 'visible', 'view': 'invisible'}
    LicenceSchema['pashDetails'].widget.visible = {'edit': 'visible', 'view': 'invisible'}
    LicenceSchema['catchmentAreaDetails'].widget.visible = {'edit': 'visible', 'view': 'invisible'}
    LicenceSchema['karstConstraintsDetails'].widget.visible = {'edit': 'visible', 'view': 'invisible'}
    LicenceSchema['floodingLevelDetails'].widget.visible = {'edit': 'visible', 'view': 'invisible'}

    # move folderCategoryTownship field on description schemata
    LicenceSchema['folderCategoryTownship'].schemata = 'urban_description'
    LicenceSchema['folderCategoryTownship'].widget.label = _('urban_label_UsageTownship')
    LicenceSchema['roadCoating'].widget.label = _('urban_label_pathCoating')
    LicenceSchema['futureRoadCoating'].widget.label = _('urban_label_futurePathCoating')
    LicenceSchema.moveField('folderCategoryTownship', after='folderCategory')

    # move some road fields to location schemata
    LicenceSchema['protectedBuilding'].schemata = 'urban_location'
    LicenceSchema.moveField('protectedBuilding', after='enoughRoadEquipmentDetails')
    LicenceSchema['protectedBuildingDetails'].schemata = 'urban_location'
    LicenceSchema.moveField('protectedBuildingDetails', after='protectedBuilding')
    LicenceSchema['sevesoSite'].schemata = 'urban_location'
    LicenceSchema.moveField('sevesoSite', after='airportNoiseZoneDetails')
    LicenceSchema['pipelines'].schemata = 'urban_location'
    LicenceSchema.moveField('pipelines', after='sevesoSite')
    LicenceSchema['pipelinesDetails'].schemata = 'urban_location'
    LicenceSchema.moveField('pipelinesDetails', after='pipelines')
    LicenceSchema['natura_2000'].schemata = 'urban_location'
    LicenceSchema.moveField('natura_2000', after='pipelinesDetails')
    LicenceSchema['roadType'].schemata = 'urban_location'
    LicenceSchema.moveField('roadType', after='natura_2000')
    LicenceSchema['pash'].schemata = 'urban_location'
    LicenceSchema.moveField('pash', after='roadType')
    LicenceSchema['pashDetails'].schemata = 'urban_location'
    LicenceSchema.moveField('pashDetails', after='pash')
    LicenceSchema['catchmentArea'].schemata = 'urban_location'
    LicenceSchema.moveField('catchmentArea', after='pashDetails')
    LicenceSchema['catchmentAreaDetails'].schemata = 'urban_location'
    LicenceSchema.moveField('catchmentAreaDetails', after='catchmentArea')
    LicenceSchema['karstConstraints'].schemata = 'urban_location'
    LicenceSchema.moveField('karstConstraints', after='catchmentAreaDetails')
    LicenceSchema['karstConstraintsDetails'].schemata = 'urban_location'
    LicenceSchema.moveField('karstConstraintsDetails', after='karstConstraints')
    LicenceSchema['floodingLevel'].schemata = 'urban_location'
    LicenceSchema.moveField('floodingLevel', after='karstConstraintsDetails')
    LicenceSchema['floodingLevelDetails'].schemata = 'urban_location'
    LicenceSchema.moveField('floodingLevelDetails', after='floodingLevel')

    LicenceSchema['locationTechnicalRemarks'].widget.label = _('urban_label_description')
    LicenceSchema['pipelinesDetails'].widget.label = _('urban_label_pipeSevesoDetails')
    rcu = LicenceSchema.get('RCU', None)
    if rcu:
        rcu.widget.label = _('urban_label_RCB')
    if rcu_details:
        rcu_details.widget.label = _('urban_label_rcbDetails')

    return LicenceSchema


licence_classes = [
    Article127, BuildLicence, Declaration, Division, EnvClassOne,
    EnvClassThree, EnvClassTwo, MiscDemand, ParcelOutLicence, PatrimonyCertificate,
    UrbanCertificateBase, UrbanCertificateTwo, IntegratedLicence, UniqueLicence,
    CODT_Article127, CODT_BuildLicence, CODT_UrbanCertificateTwo, CODT_IntegratedLicence,
    CODT_UniqueLicence, CODT_UrbanCertificateBase, Inspection, Ticket, RoadDecree
]

for licence_class in licence_classes:
    licence_class.schema = update_item_schema(licence_class.schema)
    permissions_mapping = {
        'urban_analysis': ('liege.urban: Internal Reader', 'liege.urban: Internal Editor'),
    }
    licence_class.schema = set_field_permissions(licence_class.schema, permissions_mapping)


def updateTitle(self):
    """
        Update the title to clearly identify the licence
    """
    if self.getApplicants():
        applicantTitle = ', '.join([app.Title() for app in self.getApplicants()])
    else:
        applicantTitle = translate('no_applicant_defined', 'urban', context=self.REQUEST).encode('utf8')
    to_shore = queryAdapter(self, IShore)
    title = "%s %s - %s - %s" % (self.getReference(), to_shore.display(), self.getLicenceSubject(), applicantTitle)
    self.setTitle(title)
    self.reindexObject(idxs=('Title', 'applicantInfosIndex', 'sortable_title', ))
    return title


GenericLicence.updateTitle = updateTitle
