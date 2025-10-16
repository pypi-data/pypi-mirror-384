# -*- coding: utf-8 -*-

from plone import api


def merge_foldermanagers_config():
    portal_urban = api.portal.get_tool('portal_urban')
    to_merge = portal_urban.foldermanagers_old
    foldermanagers = portal_urban.foldermanagers
    for foldermanager in to_merge.objectValues():
        if foldermanager.id not in foldermanager.objectIds():
            api.content.move(foldermanager, foldermanagers)
            print "copied foldermanager{}".format(foldermanager.Title())
