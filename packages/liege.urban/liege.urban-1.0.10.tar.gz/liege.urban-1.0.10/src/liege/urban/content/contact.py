# -*- coding: utf-8 -*-

from Products.Archetypes.atapi import Schema

from Products.urban.Applicant import Applicant
from Products.urban.Claimant import Claimant
from Products.urban.Corporation import Corporation
from Products.urban.FolderManager import FolderManager


def update_item_schema(baseSchema):

    specificSchema = Schema((),)

    ContactSchema = baseSchema + specificSchema.copy()

    # remove fax field
    ContactSchema.delField('fax')

    return ContactSchema


Applicant.schema = update_item_schema(Applicant.schema)
Claimant.schema = update_item_schema(Claimant.schema)
Corporation.schema = update_item_schema(Corporation.schema)
FolderManager.schema = update_item_schema(FolderManager.schema)
