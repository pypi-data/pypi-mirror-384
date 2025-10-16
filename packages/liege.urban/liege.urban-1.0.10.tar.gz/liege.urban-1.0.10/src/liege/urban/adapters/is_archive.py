# -*- coding: utf-8 -*-

from DateTime import DateTime

from Products.urban.interfaces import IIsArchive

from zope.interface import implements


class IsArchive(object):
    """ Adapts a licence into an archive"""
    implements(IIsArchive)

    def __init__(self, licence):
        self.licence = licence

    def is_archive(self):
        return self.licence.creation_date < DateTime('2017/03/23')
