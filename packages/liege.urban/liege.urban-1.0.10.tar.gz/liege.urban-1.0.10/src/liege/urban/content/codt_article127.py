# -*- coding: utf-8 -*-

from Products.urban.content.licence.CODT_Article127 import CODT_Article127

# buildlicence and article127 schema should have the same changes
from liege.urban.content.buildlicence import update_item_schema
from liege.urban.licence_fields_permissions import set_field_permissions

permissions_mapping = {
    'urban_description': ('liege.urban: External Reader', 'liege.urban: Description Editor'),
    'urban_analysis': ('liege.urban: Internal Reader', 'liege.urban: Internal Editor'),
    'urban_location': ('liege.urban: External Reader', 'liege.urban: Road Editor'),
    'urban_road': ('liege.urban: Road Reader', 'liege.urban: Road Editor'),
    'urban_habitation': ('liege.urban: External Reader', 'liege.urban: Habitation Editor'),
}


CODT_Article127.schema = update_item_schema(CODT_Article127.schema)
CODT_Article127.schema = set_field_permissions(
    CODT_Article127.schema,
    permissions_mapping,
)


def getProcedureDelays(self, *values):
    selection = [v['val'] for v in values if v['selected']]
    unknown = 'ukn' in selection
    opinions = 'external_opinions' in selection
    inquiry = 'inquiry' in selection or 'light_inquiry' in selection

    if unknown:
        return ''
    elif not opinions and not inquiry:
        return '30j'
    else:
        return '60j'


CODT_Article127.getProcedureDelays = getProcedureDelays
