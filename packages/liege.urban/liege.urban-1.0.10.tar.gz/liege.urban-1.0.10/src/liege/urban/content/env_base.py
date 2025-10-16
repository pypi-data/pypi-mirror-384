# -*- coding: utf-8 -*-

from liege.urban import interfaces
from liege.urban import UrbanMessage as _
from liege.urban.licence_fields_permissions import set_field_permissions
from liege.urban.licence_fields_permissions import set_environment_field_permissions
from Products.urban.content.licence.EnvClassBordering import EnvClassBordering
from Products.urban.content.licence.EnvClassOne import EnvClassOne
from Products.urban.content.licence.EnvClassThree import EnvClassThree
from Products.urban.content.licence.EnvClassTwo import EnvClassTwo
from Products.urban.content.licence.EnvironmentBase import EnvironmentBase


def update_base_schema(baseSchema):
    LicenceSchema = baseSchema.copy()

    # hide some fields
    LicenceSchema['folderCategory'].widget.visible = {'edit': 'invisible', 'view': 'invisible'}
    LicenceSchema['natura2000'].widget.visible = {'edit': 'invisible', 'view': 'invisible'}
    LicenceSchema['natura2000location'].widget.visible = {'edit': 'invisible', 'view': 'invisible'}
    LicenceSchema['natura2000Details'].widget.visible = {'edit': 'invisible', 'view': 'invisible'}

    # move road fields schemata
    LicenceSchema['businessDescription'].schemata = 'urban_environment'
    LicenceSchema['pipelines'].schemata = 'urban_environment'
    LicenceSchema['pipelinesDetails'].schemata = 'urban_environment'
    LicenceSchema['sevesoSite'].schemata = 'urban_environment'
    LicenceSchema['natura_2000'].schemata = 'urban_environment'
    LicenceSchema['rubrics'].schemata = 'urban_environment'
    LicenceSchema['rubricsDetails'].schemata = 'urban_environment'
    LicenceSchema['minimumLegalConditions'].schemata = 'urban_environment'
    LicenceSchema['additionalLegalConditions'].schemata = 'urban_environment'
    # show and hide inquiry fields
    LicenceSchema['investigationArticles'].widget.visible = {'edit': 'visible', 'view': 'visible'}
    LicenceSchema['investigationArticlesText'].widget.visible = {'edit': 'visible', 'view': 'visible'}
    LicenceSchema['derogation'].widget.visible = {'edit': 'invisible', 'view': 'invisible'}
    LicenceSchema['derogationDetails'].widget.visible = {'edit': 'invisible', 'view': 'invisible'}
    LicenceSchema['divergence'].widget.visible = {'edit': 'invisible', 'view': 'invisible'}
    LicenceSchema['divergenceDetails'].widget.visible = {'edit': 'invisible', 'view': 'invisible'}
    LicenceSchema['investigationReasons'].widget.visible = {'edit': 'visible', 'view': 'visible'}
    LicenceSchema['demandDisplay'].widget.visible = {'edit': 'visible', 'view': 'visible'}
    LicenceSchema['investigationDetails'].widget.visible = {'edit': 'visible', 'view': 'visible'}
    # reorder fields
    LicenceSchema.moveField('rubricsDetails', after='rubrics')
    LicenceSchema.moveField('minimumLegalConditions', after='rubricsDetails')
    LicenceSchema.moveField('additionalLegalConditions', after='minimumLegalConditions')
    LicenceSchema.moveField('businessDescription', after='additionalLegalConditions')
    LicenceSchema.moveField('natura_2000', after='sevesoSite')
    # rename fields
    LicenceSchema['procedureChoice'].widget.label = _('urban_label_procedureType')
    LicenceSchema['workLocations'].widget.label = _('urban_label_exploitationAddress')
    LicenceSchema['folderCategoryTownship'].widget.label = _('urban_label_ExploitationUsage')
    LicenceSchema['additionalLegalConditions'].widget.label = _('urban_label_LiegeEnvironmentConditions')

    return LicenceSchema


env_base_classes = [
    EnvClassOne, EnvClassThree, EnvClassTwo, EnvClassBordering
]

for licence_class in env_base_classes:
    licence_class.schema = update_base_schema(licence_class.schema)
EnvClassThree.schema = set_environment_field_permissions(EnvClassThree.schema)


def update_classthree_schema(baseSchema):
    LicenceSchema = baseSchema.copy()
    # reorder fields
    LicenceSchema.moveField('description', after='inadmissibilityreasonsDetails')
    return LicenceSchema


EnvClassThree.schema = update_classthree_schema(EnvClassThree.schema)


def update_licences_schema(baseSchema):
    LicenceSchema = baseSchema.copy()

    # hide some fields
    LicenceSchema['isSeveso'].widget.visible = {'edit': 'invisible', 'view': 'invisible'}
    # rename fields
    if hasattr(LicenceSchema, 'ftSolicitOpinionsTo'):
        LicenceSchema['ftSolicitOpinionsTo'].widget.label = _('urban_label_decisionNotificationTo')
    LicenceSchema['commentsOnSPWOpinion'].widget.label = _('urban_label_CommentsOnDecisionProject')
    # reorder fields
    LicenceSchema.moveField('description', after='hasEnvironmentImpactStudy')
    if hasattr(LicenceSchema, 'ftSolicitOpinionsTo'):
        LicenceSchema.moveField('description', after='ftSolicitOpinionsTo')
    LicenceSchema.moveField('referenceFT', after='referenceDGATLP')
    # change permissions of some fields
    LicenceSchema['claimsSynthesis'].read_permission = 'liege.urban: Internal Reader'
    LicenceSchema['claimsSynthesis'].write_permission = 'Review portal content'
    LicenceSchema['environmentTechnicalAdviceAfterInquiry'].read_permission = 'liege.urban: Internal Reader'
    LicenceSchema['environmentTechnicalAdviceAfterInquiry'].write_permission = 'Review portal content'
    LicenceSchema['commentsOnSPWOpinion'].read_permission = 'liege.urban: Internal Reader'
    LicenceSchema['commentsOnSPWOpinion'].write_permission = 'liege.urban: Environment Contributor'
    LicenceSchema['conclusions'].read_permission = 'liege.urban: Internal Reader'
    LicenceSchema['conclusions'].write_permission = 'liege.urban: Environment Contributor'

    return LicenceSchema


env_licence_classes = [
    EnvClassOne, EnvClassTwo, EnvClassBordering
]


licences_permissions_mapping = {
    'urban_description': ('liege.urban: External Reader', 'liege.urban: Description Editor'),
    'urban_location': ('liege.urban: External Reader', 'liege.urban: Internal Editor'),
    'urban_environment': ('liege.urban: Internal Reader', 'liege.urban: Environment Editor'),
    'urban_road': ('liege.urban: Road Reader', 'liege.urban: Road Editor'),
}

exceptions = [
    'portal_type',
    'id',
    'claimsSynthesis',
    'environmentTechnicalAdviceAfterInquiry',
    'commentsOnSPWOpinion',
    'conclusions'
]

for licence_class in env_licence_classes:
    licence_class.schema = update_licences_schema(licence_class.schema)
    licence_class.schema = set_field_permissions(
        licence_class.schema,
        licences_permissions_mapping,
        exceptions,
    )
# env class bordering has no specific worfklow, apply same permissions than class 3
EnvClassBordering.schema = set_environment_field_permissions(EnvClassBordering.schema)


def getAllValidationEvents(self):
    return self.getAllEvents(interfaces.IUrbanEventWithEnvironmentValidation)


EnvironmentBase.getAllValidationEvents = getAllValidationEvents
