# -*- coding: utf-8 -*-

from plone import api
import pprint


def stats():
    catalog = api.portal.get_tool('portal_catalog')

    result = {}

    for brain in catalog():
        portal_type = brain.portal_type
        if brain.portal_type in result:
            result[portal_type] = result[portal_type] + 1
        else:
            result[portal_type] = 1
