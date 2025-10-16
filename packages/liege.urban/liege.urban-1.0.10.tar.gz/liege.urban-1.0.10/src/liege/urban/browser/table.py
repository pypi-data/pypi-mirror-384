## -*- coding: utf-8 -*-

from Products.urban.browser.table.column import ParcelTitleDisplay
from Products.urban.browser.table.column import RelatedLicencesColumn
from Products.urban.browser.table.column import TitleColumnHeader

from z3c.table.column import Column
from z3c.table.table import Table

from zope.i18n import translate


class AddressTitleColumnHeader(TitleColumnHeader):

    def update(self):
        self.label = 'label_colname_address'


class AddressesListingTable(Table):
    """
    Table used to list address point search results
    """

    cssClasses = {'table': 'listing largetable'}
    batchProviderName = 'plonebatch'
    startBatchingAt = 20


class AddressColumn(Column):
    """
    """

    header = 'label_colname_streetname'
    weight = 20

    def renderCell(self, record):
        address = u'{}, {}'.format(record.street_name, record.street_number)
        return address


class AddressTitleDisplay(ParcelTitleDisplay):
    """
    """

    def render(self):
        address = self.obj
        street_address = u'{}, {}'.format(address.getStreet_name().decode('utf-8'), str(address.getStreet_number()).decode('utf-8'))
        city_name = address.getDivisionAlternativeName().split('(')[0]
        city = u'{} {}'.format((address.getZip_code() or '').decode('utf-8'), city_name)
        full_address = u'{}<br />{}'.format(street_address, city)
        return full_address.encode('utf-8')


class ShoreColumn(Column):
    """
    """
    header = 'label_colname_shore'
    weight = 15

    def renderHeadCell(self):
        """Header cell content."""
        return translate(self.header, 'urban', context=self.request)

    def renderCell(self, address):
        return '<div style="text-align:center">%s</div>' % address.getShore()


class CapakeyColumn(Column):
    """
    """

    header = 'label_colname_capakey'
    weight = 30

    def renderCell(self, record):
        return record.capakey


class GIDColumn(Column):
    """
    """

    header = 'label_colname_gid'
    weight = 40

    def renderCell(self, record):
        return record.address_point


class AddAddressColumn(Column):
    """
    """

    header = 'label_colname_add'
    weight = 1000

    def renderCell(self, record):

        inputs = []
        for k, v in record.iteritems():
            form_input = u'<input type="hidden" name="{key}" value="{value}" />'.format(key=k, value=v)
            inputs.append(form_input)
        inputs.append(u'<input type="image" src="icon_add.gif" name="add_address" alt="Add this address"/>')

        licence_url = self.context.context.absolute_url()
        add_form = u'<form action="{}/create_address">{}</form>'.format(licence_url, u''.join(inputs))

        return add_form


class AddressParcelColumn(RelatedLicencesColumn):
    """
    """

    def renderCell(self, parcel):
        related_licences = super(AddressParcelColumn, self).renderCell(parcel)

        cell = '{title}<br />{related}'.format(title=parcel.Title(), related=related_licences)

        return cell
