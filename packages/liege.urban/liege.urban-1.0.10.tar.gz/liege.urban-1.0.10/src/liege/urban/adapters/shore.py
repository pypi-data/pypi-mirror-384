# -*- coding: utf-8 -*-

from liege.urban.interfaces import IShore

from zope.interface import implements


class LicenceToShore(object):
    """
    """
    implements(IShore)

    def __init__(self, licence):
        self.licence = licence

    def get_shore(self):
        shores = set([])
        for address in self.licence.getParcels():
            shores.add(address.getShore())
        return sorted(list(shores))

    def display(self):
        return ''.join(self.get_shore())
