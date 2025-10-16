# -*- coding: utf-8 -*-

from Products.urban.content.licence.UrbanCertificateTwo import UrbanCertificateTwo

# buildlicence and article127 schema should have the same changes
from liege.urban.content.buildlicence import update_item_schema
from liege.urban.licence_fields_permissions import set_field_permissions

permissions_mapping = {
    'urban_description': ('liege.urban: External Reader', 'liege.urban: Description Editor'),
    'urban_description': ('liege.urban: External Reader', 'liege.urban: Description Editor'),
    'urban_location': ('liege.urban: External Reader', 'liege.urban: Road Editor'),
    'urban_road': ('liege.urban: Road Reader', 'liege.urban: Road Editor'),
}


UrbanCertificateTwo.schema = update_item_schema(UrbanCertificateTwo.schema)
UrbanCertificateTwo.schema = set_field_permissions(
    UrbanCertificateTwo.schema,
    permissions_mapping,
)
