# -*- coding: utf-8 -*-

from plone import api

import csv


def do_import():
    site = api.portal.get()
    notaries_folder = site.urban.notaries
    fieldnames = [
        'id',
        'name1',
        'name2',
        'street1',
        'street2',
        'number',
        'zipcode',
        'city',
        'phone',
        'fax',
        'title',
        'double',
    ]

    title_maping = {
        'Notaire': 'master',
        'Société': 'company',
    }

    reader = csv.DictReader(open('notaires.csv', 'r'), fieldnames, delimiter=';')
    notaries_args = [row for row in reader if row['name1']][1:]
    for notary_arg in notaries_args:
        notary_arg['street'] = '{} {}'.format(notary_arg.pop('street1'), notary_arg.pop('street2'))
        notary_arg['personTitle'] = title_maping.get(notary_arg.pop('title'), 'notitle')
        notaries_folder.invokeFactory('Notary', **notary_arg)
