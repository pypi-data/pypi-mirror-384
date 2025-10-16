# -*- coding: utf-8 -*-

from liege.urban.interfaces import IShore

from Products.Archetypes.atapi import Schema

from Products.urban.content.licence.CODT_UniqueLicence import CODT_UniqueLicence

from liege.urban import UrbanMessage as _
# buildlicence and uniquelicence schema should have the same changes
from liege.urban.content.buildlicence import update_item_schema as base_update_item_schema
from liege.urban.licence_fields_permissions import set_field_permissions

from zope.i18n import translate
from zope.component import queryAdapter

specific_schema = Schema((
),)


def update_item_schema(baseSchema):
    LicenceSchema = baseSchema + specific_schema.copy()

    # move some fields
    LicenceSchema['pipelines'].schemata = 'urban_environment'
    LicenceSchema['pipelinesDetails'].schemata = 'urban_environment'
    LicenceSchema['procedureChoice'].schemata = 'urban_description'
    LicenceSchema['annoncedDelay'].schemata = 'urban_description'
    LicenceSchema['annoncedDelayDetails'].schemata = 'urban_description'
    LicenceSchema['prorogation'].schemata = 'urban_description'
    # show and hide inquiry fields
    LicenceSchema['inquiry_type'].widget.visible = {'view': 'invisible', 'edit': 'invisible'}
    LicenceSchema['investigationArticles'].widget.visible = {'edit': 'visible', 'view': 'visible'}
    LicenceSchema['investigationArticlesText'].widget.visible = {'edit': 'visible', 'view': 'visible'}
    LicenceSchema['derogationDetails'].widget.visible = {'edit': 'visible', 'view': 'visible'}
    LicenceSchema['investigationReasons'].widget.visible = {'edit': 'visible', 'view': 'visible'}
    LicenceSchema['demandDisplay'].widget.visible = {'edit': 'visible', 'view': 'visible'}
    LicenceSchema['investigationDetails'].widget.visible = {'edit': 'visible', 'view': 'visible'}
    # reorder fields
    LicenceSchema.moveField('folderTendency', after='licenceSubject')
    LicenceSchema.moveField('inquiry_category', after='divergenceDetails')
    LicenceSchema.moveField('rubricsDetails', after='rubrics')
    LicenceSchema.moveField('minimumLegalConditions', after='rubricsDetails')
    LicenceSchema.moveField('additionalLegalConditions', after='minimumLegalConditions')
    LicenceSchema.moveField('description', after='ftSolicitOpinionsTo')
    LicenceSchema.moveField('procedureChoice', after='folderCategory')
    LicenceSchema.moveField('annoncedDelay', after='procedureChoice')
    LicenceSchema.moveField('annoncedDelayDetails', after='annoncedDelay')
    LicenceSchema.moveField('prorogation', after='annoncedDelayDetails')
    # rename some fields
    LicenceSchema['reference'].widget.label = _('urban_label_urbanReference')
    LicenceSchema['referenceDGATLP'].widget.label = _('urban_label_referenceFD')
    LicenceSchema['procedureChoice'].widget.label = _('urban_label_folderCategory')
    LicenceSchema['commentsOnSPWOpinion'].widget.label = _('urban_label_CommentsOnDecisionProject')
    LicenceSchema['ftSolicitOpinionsTo'].widget.label = _('urban_label_decisionNotificationTo')
    # change permissions of some fields
    LicenceSchema['claimsSynthesis'].read_permission = 'liege.urban: External Reader'
    LicenceSchema['claimsSynthesis'].write_permission = 'Review portal content'
    LicenceSchema['environmentTechnicalAdviceAfterInquiry'].read_permission = 'liege.urban: External Reader'
    LicenceSchema['environmentTechnicalAdviceAfterInquiry'].write_permission = 'Review portal content'
    LicenceSchema['commentsOnSPWOpinion'].read_permission = 'liege.urban: External Reader'
    LicenceSchema['commentsOnSPWOpinion'].write_permission = 'liege.urban: Environment Contributor'
    LicenceSchema['conclusions'].read_permission = 'liege.urban: External Reader'
    LicenceSchema['conclusions'].write_permission = 'liege.urban: Environment Contributor'

    return LicenceSchema


CODT_UniqueLicence.schema = update_item_schema(base_update_item_schema(CODT_UniqueLicence.schema))


permissions_mapping = {
    'urban_description': ('liege.urban: External Reader', 'liege.urban: Description Editor'),
    'urban_analysis': ('liege.urban: Internal Reader', 'liege.urban: Urban Editor'),
    'urban_environment': ('liege.urban: Internal Reader', 'liege.urban: Environment Editor'),
    'urban_road': ('liege.urban: Road Reader', 'liege.urban: Road Editor'),
    'urban_habitation': ('liege.urban: External Reader', 'liege.urban: Habitation Editor'),
}

# claimsSynthesis and environmentTechnicalAdviceAfterInquiry must have reviewer
# write permission to be able to freeze them in the workflow
exceptions = [
    'portal_type',
    'id',
    'claimsSynthesis',
    'environmentTechnicalAdviceAfterInquiry',
    'commentsOnSPWOpinion',
    'conclusions'
]

CODT_UniqueLicence.schema = set_field_permissions(
    CODT_UniqueLicence.schema,
    permissions_mapping,
    exceptions,
)


def updateTitle(self):
    """
        Update the title to clearly identify the licence
    """
    if self.getApplicants():
        applicantTitle = ', '.join([app.Title() for app in self.getApplicants()])
    else:
        applicantTitle = translate('no_applicant_defined', 'urban', context=self.REQUEST).encode('utf8')
    to_shore = queryAdapter(self, IShore)
    title = "%s %s - %s - %s - %s" % (
        self.getReference(),
        to_shore.display(),
        self.getReferenceSPE(),
        self.getLicenceSubject(),
        applicantTitle
    )
    self.setTitle(title)
    self.reindexObject(idxs=('Title', 'applicantInfosIndex', 'sortable_title', ))
    return title


CODT_UniqueLicence.updateTitle = updateTitle
