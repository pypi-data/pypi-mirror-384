# -*- coding: utf-8 -*-

from Products.urban.content.licence.PreliminaryNotice import PreliminaryNotice

from liege.urban.licence_fields_permissions import set_field_permissions

permissions_mapping = {
    'urban_description': ('liege.urban: External Reader', 'liege.urban: Description Editor'),
    'urban_analysis': ('liege.urban: Internal Reader', 'liege.urban: Internal Editor'),
}


PreliminaryNotice.schema = set_field_permissions(
    PreliminaryNotice.schema,
    permissions_mapping,
)
