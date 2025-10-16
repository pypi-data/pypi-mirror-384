# -*- coding: utf-8 -*-

from liege.urban.workflows.licences_workflow import DefaultStateRolesMapping as LiegeBase


class StateRolesMapping(LiegeBase):
    """
    State role mapping adapter for RoadDecree content type
    """

    mapping = {

        'folder_creation': {
            LiegeBase.get_opinion_editors: ('ExternalReader',),
            'administrative_editors': ('Editor', 'AddressEditor'),
            'administrative_validators': ('Contributor',),
            'fittingout_technicians': ('Editor', ),
            'fittingout_technicians_validators': ('Contributor',),
            'Voirie_readers': ('Reader', 'RoadReader'),
            'urban_readers': ('Reader', 'RoadReader'),
            'urban_internal_readers': ('InternalReader', 'RoadReader'),
            'Voirie_editors': ('ExternalReader',),
            'Voirie_validators': ('ExternalReader',),
        },

        'public_investigation': {
            LiegeBase.get_opinion_editors: ('ExternalReader',),
            'administrative_editors': ('Editor', 'AddressEditor'),
            'administrative_validators': ('Contributor',),
            'fittingout_technicians': ('Editor', ),
            'fittingout_technicians_validators': ('Contributor',),
            'Voirie_readers': ('Reader', 'RoadReader'),
            'urban_readers': ('Reader', 'RoadReader'),
            'urban_internal_readers': ('InternalReader', 'RoadReader'),
            'Voirie_editors': ('ExternalReader',),
            'Voirie_validators': ('ExternalReader',),
        },

        'technical_analysis_post_investigation': {
            LiegeBase.get_opinion_editors: ('ExternalReader',),
            'administrative_editors': ('Editor', 'AddressEditor'),
            'administrative_validators': ('Contributor',),
            'fittingout_technicians': ('Editor', ),
            'fittingout_technicians_validators': ('Contributor',),
            'Voirie_readers': ('Reader', 'RoadReader'),
            'urban_readers': ('Reader', 'RoadReader'),
            'urban_internal_readers': ('InternalReader', 'RoadReader'),
            'Voirie_editors': ('ExternalReader',),
            'Voirie_validators': ('ExternalReader',),
        },

        'technical_analysis_validation': {
            LiegeBase.get_opinion_editors: ('ExternalReader',),
            'administrative_editors': ('Editor', 'AddressEditor'),
            'administrative_validators': ('Contributor',),
            'fittingout_technicians': ('Reader',),
            'fittingout_technicians_validators': ('Contributor',),
            'Voirie_readers': ('Reader', 'RoadReader'),
            'urban_readers': ('Reader', 'RoadReader'),
            'urban_internal_readers': ('InternalReader', 'RoadReader'),
            'Voirie_editors': ('ExternalReader',),
            'Voirie_validators': ('ExternalReader',),
        },

        'college_council_passage': {
            LiegeBase.get_opinion_editors: ('ExternalReader',),
            'administrative_editors': ('Editor', 'AddressEditor'),
            'administrative_validators': ('Contributor',),
            'fittingout_technicians': ('Editor', ),
            'fittingout_technicians_validators': ('Contributor',),
            'Voirie_readers': ('Reader', 'RoadReader'),
            'urban_readers': ('Reader', 'RoadReader'),
            'urban_internal_readers': ('InternalReader', 'RoadReader'),
            'Voirie_editors': ('ExternalReader',),
            'Voirie_validators': ('ExternalReader',),
        },

        'display_in_progress': {
            LiegeBase.get_opinion_editors: ('ExternalReader',),
            'administrative_editors': ('Editor', 'AddressEditor'),
            'administrative_validators': ('Contributor',),
            'fittingout_technicians': ('Editor', ),
            'fittingout_technicians_validators': ('Contributor',),
            'Voirie_readers': ('Reader', 'RoadReader'),
            'urban_readers': ('Reader', 'RoadReader'),
            'urban_internal_readers': ('InternalReader', 'RoadReader'),
            'Voirie_editors': ('ExternalReader',),
            'Voirie_validators': ('ExternalReader',),
        },

        'authorized': {
            LiegeBase.get_opinion_editors: ('ExternalReader',),
            'administrative_editors': ('Editor', 'AddressEditor'),
            'administrative_validators': ('Contributor',),
            'fittingout_technicians': ('Editor', ),
            'fittingout_technicians_validators': ('Contributor',),
            'Voirie_readers': ('Reader', 'RoadReader'),
            'urban_readers': ('Reader', 'RoadReader'),
            'urban_internal_readers': ('InternalReader', 'RoadReader'),
            'Voirie_editors': ('ExternalReader',),
            'Voirie_validators': ('ExternalReader',),
        },

        'refused': {
            LiegeBase.get_opinion_editors: ('ExternalReader',),
            'administrative_editors': ('Editor', 'AddressEditor'),
            'administrative_validators': ('Contributor',),
            'fittingout_technicians': ('Editor', ),
            'fittingout_technicians_validators': ('Contributor',),
            'Voirie_readers': ('Reader', 'RoadReader'),
            'urban_readers': ('Reader', 'RoadReader'),
            'urban_internal_readers': ('InternalReader', 'RoadReader'),
            'Voirie_editors': ('ExternalReader',),
            'Voirie_validators': ('ExternalReader',),
        },

        'abandoned': {
            LiegeBase.get_opinion_editors: ('ExternalReader',),
            'administrative_editors': ('Editor', 'AddressEditor'),
            'administrative_validators': ('Contributor',),
            'fittingout_technicians': ('Editor', ),
            'fittingout_technicians_validators': ('Contributor',),
            'Voirie_readers': ('Reader', 'RoadReader'),
            'urban_readers': ('Reader', 'RoadReader'),
            'urban_internal_readers': ('InternalReader', 'RoadReader'),
            'Voirie_editors': ('ExternalReader',),
            'Voirie_validators': ('ExternalReader',),
        },
    }
