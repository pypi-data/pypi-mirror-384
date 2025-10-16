# -*- coding: utf-8 -*-

from Products.urban.content.licence.UniqueLicence import UniqueLicence

# buildlicence and uniquelicence schema should have the same changes
from liege.urban.content.buildlicence import update_item_schema
from liege.urban.content.codt_uniquelicence import updateTitle
from liege.urban.licence_fields_permissions import set_field_permissions

permissions_mapping = {
    'urban_description': ('liege.urban: External Reader', 'liege.urban: Description Editor'),
    'urban_analysis': ('liege.urban: Internal Reader', 'liege.urban: Internal Editor'),
    'urban_habitation': ('liege.urban: External Reader', 'liege.urban: Habitation Editor'),
}


UniqueLicence.schema = update_item_schema(UniqueLicence.schema)
UniqueLicence.schema = set_field_permissions(
    UniqueLicence.schema,
    permissions_mapping,
)


UniqueLicence.updateTitle = updateTitle
