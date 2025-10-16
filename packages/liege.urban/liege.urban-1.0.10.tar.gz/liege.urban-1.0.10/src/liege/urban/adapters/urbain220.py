# -*- coding: utf-8 -*-

from Products.urban.interfaces import IToUrbain220Street

from zope.interface import implements


class LiegeLicenceToUrbain220Street(object):
    """ """

    implements(IToUrbain220Street)

    def __init__(self, licence):
        first_address = None
        for address in licence.objectValues('PortionOut'):
            if address.street_name and address.street_code:
                first_address = address
                break
        self.street_name = first_address and first_address.street_name.encode('utf-8')
        self.street_code = first_address and first_address.street_code.encode('utf-8')
        self.street_number = first_address and first_address.street_number
