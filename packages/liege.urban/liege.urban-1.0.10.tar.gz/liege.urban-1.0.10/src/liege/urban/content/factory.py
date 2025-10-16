# -*- coding: utf-8 -*-

from liege.urban.interfaces import IAddressFactory

from plone import api

from Products.Five import BrowserView
from Products.urban.services import cadastre

from zope.interface import implements

NOT_FOUND = []


class AdressFactory(BrowserView):
    """
    """
    implements(IAddressFactory)

    def __call__(self):
        address_args = self.get_address_args()
        if address_args:
            self.create_address(**address_args)

        return self.request.response.redirect(self.request['HTTP_REFERER'])

    def get_address_args(self):
        args = {}
        for key in ['address_point', 'street_code', 'street_name', 'street_number', 'zip_code', 'capakey', 'shore']:
            val = self.request.get(key, NOT_FOUND)
            if val is NOT_FOUND:
                return NOT_FOUND
            args[key] = val
        return args

    def create_address(self, **address_args):
        session = cadastre.new_session()
        capakey = address_args.pop('capakey')
        parcel = session.query_parcel_by_capakey(capakey)
        session.close()
        if parcel:
            reference_dict = parcel.reference_as_dict()
        else:
            reference_dict = self.parse_cadastral_reference(capakey)

        licence = self.context
        portal_urban = api.portal.get_tool('portal_urban')

        with api.env.adopt_roles(['Manager']):
            portal_urban.createPortionOut(licence, **reference_dict)

        address = licence.getParcels()[-1]
        for field_name, value in address_args.iteritems():
            field = address.getField(field_name)
            field.set(address, value)

        licence.updateTitle()
        licence.reindexObject(idxs=['parcelInfosIndex', 'shore'])

    def parse_cadastral_reference(sef, capakey):
        """
        """
        reference_as_dict = {
            'division': capakey[0:5],
            'section': capakey[5],
            'radical': int(capakey[6:10]) and str(int(capakey[6:10])) or '',
            'bis': int(capakey[11:13]) and str(int(capakey[11:13])) or '',
            'exposant': capakey[13] and capakey[13] or '',
            'puissance': int(capakey[14:17]) and str(int(capakey[14:17])) or '',
        }
        return reference_as_dict
