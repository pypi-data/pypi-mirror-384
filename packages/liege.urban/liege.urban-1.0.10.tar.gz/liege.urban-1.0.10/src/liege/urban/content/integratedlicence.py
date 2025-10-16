# -*- coding: utf-8 -*-

from Products.urban.content.licence.IntegratedLicence import IntegratedLicence

# buildlicence and article127 schema should have the same changes
from liege.urban.content.buildlicence import update_item_schema
from liege.urban.licence_fields_permissions import set_field_permissions

permissions_mapping = {
    'urban_description': ('liege.urban: External Reader', 'liege.urban: Description Editor'),
    'urban_habitation': ('liege.urban: External Reader', 'liege.urban: Habitation Editor'),
}


IntegratedLicence.schema = update_item_schema(IntegratedLicence.schema)
IntegratedLicence.schema = set_field_permissions(
    IntegratedLicence.schema,
    permissions_mapping,
)
