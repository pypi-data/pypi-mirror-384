# -*- coding: utf-8 -*-

from Products.urban.interfaces import IGenericLicence
from plone import api


def close_env_licences():
    cat = api.portal.get_tool('portal_catalog')
    ref_file = open('liege_to_close.csv', 'r')
    refs = [line.replace('\n', '') for line in ref_file.readlines()]
    licences = [cat(getReference=ref, object_provides=IGenericLicence.__identifier__)[0].getObject() for ref in refs]
    for licence in licences:
        api.content.transition(obj=licence, transition='ask_address_validation')
        api.content.transition(obj=licence, transition='validate_address')
        api.content.transition(obj=licence, transition='is_complete')
        api.content.transition(obj=licence, transition='propose_technical_report')
        api.content.transition(obj=licence, transition='validate_technical_report')
        api.content.transition(obj=licence, transition='college_done')
        api.content.transition(obj=licence, transition='propose_technical_synthesis')
        api.content.transition(obj=licence, transition='validate_technical_synthesis')
        api.content.transition(obj=licence, transition='authorize_licence')
