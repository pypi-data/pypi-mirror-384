# -*- coding: utf-8 -*-

from liege.urban.browser.table import AddressesListingTable
from liege.urban.services import address_service

from plone import api
from plone.z3cform.layout import FormWrapper

from Products.urban.browser.table.urbantable import ParcelsTable

from zope.browserpage.viewpagetemplatefile import ViewPageTemplateFile

from z3c.form import button
from z3c.form import form, field

from zope.interface import Interface
from zope.schema import TextLine
from zope.i18nmessageid import MessageFactory
_ = MessageFactory('liege.urban')


class StreetNameField(TextLine):
    """ """


class INSCodeField(TextLine):
    """ """


class StreetNumberField(TextLine):
    """ """


class IAddressSearchForm(Interface):

    street_name = StreetNameField(
        title=_(u'Street name'),
        required=False
    )

    INS_code = INSCodeField(
        title=_(u'Street code'),
        required=False
    )

    street_number = StreetNumberField(
        title=_(u'Street number'),
        required=False
    )


class FieldDefaultValue(object):
    """ """

    def __init__(self, licence, request, form, field, widget):
        self.licence = licence
        self.request = request
        self.form = form
        self.field = field
        self.widget = widget

    def get(self):
        """ To implements."""

    def get_address_to_find(self):
        """Return the first street on the licence """
        location = self.licence.getWorkLocations()
        if not location:
            return (None, None)

        catalog = api.portal.get_tool('portal_catalog')
        addresses_street_codes = set([int(adr.getStreet_code() or 0) for adr in self.licence.getParcels()])

        for manual_address in location:
            street_UID = manual_address['street']
            street_brains = catalog(UID=street_UID)
            if street_brains:
                street = street_brains[0].getObject()
                if street.getStreetCode() not in addresses_street_codes:
                    return manual_address, street

        return (None, None)

    def get_default_street(self):
        """Return the first street on the licence """
        manual_address, street = self.get_address_to_find()
        return street


class DefaultStreetName(FieldDefaultValue):
    """ """

    def get(self):
        """ """
        street = self.get_default_street()
        if not street:
            return ''

        street_name = street.Title().split('(')[0]
        return street_name


class DefaultINSCode(FieldDefaultValue):
    """ """

    def get(self):
        """ """
        street = self.get_default_street()
        if not street:
            return None

        ins_code = street.getStreetCode()
        return ins_code


class DefaultStreetNumber(FieldDefaultValue):
    """ """

    def get(self):
        """ """
        manual_address, street = self.get_address_to_find()
        if not manual_address:
            return ''

        street_number = manual_address['number']

        return street_number


class AddressSearchForm(form.Form):

    method = 'get'
    fields = field.Fields(IAddressSearchForm)
    ignoreContext = True

    def updateWidgets(self):
        super(AddressSearchForm, self).updateWidgets()

    @button.buttonAndHandler(u'Search')
    def handleSearch(self, action):
        data, errors = self.extractData()
        if errors:
            return False


class AddressSearchFormView(FormWrapper):
    """
    """
    form = AddressSearchForm
    index = ViewPageTemplateFile('templates/address_search.pt')

    def __init__(self, context, request):
        super(AddressSearchFormView, self).__init__(context, request)
        # disable portlets on licences
        self.request.set('disable_plone.rightcolumn', 1)
        self.request.set('disable_plone.leftcolumn', 1)

    def search_submitted(self):
        """
        """
        form_inputs = self.form_instance.extractData()[0]
        submitted = any(form_inputs.values())
        return submitted

    def get_search_args(self):
        """
        """
        form_inputs = self.form_instance.extractData()[0]
        return form_inputs

    def update(self):
        super(AddressSearchFormView, self).update()

        self.search_result = AddressesListingTable(self, self.request)
        self.search_result.update()

    def values(self):
        if self.search_submitted():
            session = address_service.new_session()
            inputs = self.get_search_args()
            inputs = dict([(k, v) for k, v in inputs.iteritems() if v])
            records = session.query_addresses(**inputs)
            session.close()
            values = [AddressRecord(**record._asdict()) for record in records]
            return values

        return []

    def refreshBatch(self, batch_start):
        self.search_result.batchStart = batch_start
        self.search_result.update()

    def renderParcelsListing(self):
        parcels = self.context.getParcels()
        if not parcels:
            return ''
        parceltable = ParcelsTable(self.context, self.request, values=parcels)
        parceltable.update()
        parcels_listing = parceltable.render()
        return parcels_listing


class AddressRecord(object):
    """Dummy class for address search result records """

    def __init__(self, **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)

    def iteritems(self):
        return self.__dict__.iteritems()
