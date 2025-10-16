# -*- coding: utf-8 -*-


from liege.urban.workflows.licences_workflow import DefaultStateRolesMapping as LiegeBase


class StateRolesMapping(LiegeBase):
    """ """

    mapping = {
        'deposit': {
            'administrative_editors_environment': ('Editor',),
            'administrative_validators_environment': ('Contributor',),
            'technical_editors_environment': ('Editor',),
            'technical_validators_environment': ('Contributor',),
            'environment_readers': ('Reader', 'InternalReader'),
        },

        'validating_address': {
            LiegeBase.get_opinion_editors: ('ExternalReader',),
            'survey_editors': ('Reader', 'AddressEditor'),
            'administrative_editors_environment': ('Editor',),
            'administrative_validators_environment': ('Contributor',),
            'technical_editors_environment': ('EnvironmentEditor',),
            'technical_validators_environment': ('EnvironmentContributor',),
            'survey_editors': ('Reader', 'AddressEditor'),
            'environment_readers': ('Reader', 'InternalReader'),
        },

        'waiting_address': {
            LiegeBase.get_opinion_editors: ('ExternalReader',),
            'survey_editors': ('Reader', 'AddressEditor'),
            'administrative_editors_environment': ('Editor',),
            'administrative_validators_environment': ('Contributor',),
            'technical_editors_environment': ('EnvironmentEditor',),
            'technical_validators_environment': ('EnvironmentContributor',),
            'environment_readers': ('Reader', 'InternalReader'),
        },


        'checking_completion': {
            LiegeBase.get_opinion_editors: ('ExternalReader',),
            'survey_editors': ('Reader', 'AddressEditor'),
            'administrative_editors_environment': ('Editor',),
            'administrative_validators_environment': ('Contributor',),
            'technical_editors_environment': ('EnvironmentEditor',),
            'technical_validators_environment': ('EnvironmentContributor',),
            'environment_readers': ('Reader', 'InternalReader'),
        },

        'complete': {
            LiegeBase.get_opinion_editors: ('ExternalReader',),
            'survey_editors': ('Reader', 'AddressEditor'),
            'administrative_editors_environment': ('Editor',),
            'administrative_validators_environment': ('Contributor',),
            'technical_editors_environment': ('EnvironmentEditor',),
            'technical_validators_environment': ('EnvironmentContributor',),
            'environment_readers': ('Reader', 'InternalReader'),
        },

        'incomplete': {
            LiegeBase.get_opinion_editors: ('ExternalReader',),
            'survey_editors': ('Reader', 'AddressEditor'),
            'administrative_editors_environment': ('Editor',),
            'administrative_validators_environment': ('Contributor',),
            'technical_editors_environment': ('Editor',),
            'technical_validators_environment': ('Contributor',),
            'environment_readers': ('Reader', 'InternalReader'),
        },

        'technical_report_validation': {
            LiegeBase.get_opinion_editors: ('ExternalReader',),
            'survey_editors': ('Reader', 'AddressEditor'),
            'administrative_editors_environment': ('Editor',),
            'administrative_validators_environment': ('Contributor',),
            'technical_validators_environment': ('EnvironmentContributor',),
            'environment_readers': ('Reader', 'InternalReader'),
        },

        'college_in_progress': {
            LiegeBase.get_opinion_editors: ('ExternalReader',),
            'survey_editors': ('Reader', 'AddressEditor'),
            'administrative_editors_environment': ('Editor',),
            'administrative_validators_environment': ('Contributor',),
            'technical_editors_environment': ('EnvironmentEditor',),
            'technical_validators_environment': ('EnvironmentContributor',),
            'environment_readers': ('Reader', 'InternalReader'),
        },

        'FT_opinion': {
            LiegeBase.get_opinion_editors: ('ExternalReader',),
            'survey_editors': ('Reader', 'AddressEditor'),
            'administrative_editors_environment': ('Editor',),
            'administrative_validators_environment': ('Contributor',),
            'technical_editors_environment': ('EnvironmentEditor',),
            'technical_validators_environment': ('EnvironmentContributor',),
            'environment_readers': ('Reader', 'InternalReader'),
        },

        'technical_synthesis_validation': {
            LiegeBase.get_opinion_editors: ('ExternalReader',),
            'survey_editors': ('Reader', 'AddressEditor'),
            'administrative_editors_environment': ('Editor',),
            'administrative_validators_environment': ('Contributor',),
            'technical_validators_environment': ('EnvironmentContributor',),
            'environment_readers': ('Reader', 'InternalReader'),
        },

        'final_decision_in_progress': {
            LiegeBase.get_opinion_editors: ('ExternalReader',),
            'survey_editors': ('Reader', 'AddressEditor'),
            'administrative_editors_environment': ('Editor',),
            'administrative_validators_environment': ('Contributor',),
            'technical_editors_environment': ('EnvironmentEditor',),
            'technical_validators_environment': ('EnvironmentContributor',),
            'environment_readers': ('Reader', 'InternalReader'),
        },

        'inacceptable': {
            LiegeBase.get_opinion_editors: ('ExternalReader',),
            'survey_editors': ('Reader', 'AddressEditor'),
            'administrative_editors_environment': ('Editor',),
            'administrative_validators_environment': ('Contributor',),
            'technical_editors_environment': ('EnvironmentEditor',),
            'technical_validators_environment': ('EnvironmentContributor',),
            'environment_readers': ('Reader', 'InternalReader'),
        },

        'authorized': {
            LiegeBase.get_opinion_editors: ('ExternalReader',),
            'survey_editors': ('Reader', 'AddressEditor'),
            'administrative_editors_environment': ('Editor',),
            'administrative_validators_environment': ('Contributor',),
            'technical_editors_environment': ('EnvironmentEditor',),
            'technical_validators_environment': ('EnvironmentContributor',),
            'environment_readers': ('Reader', 'InternalReader'),
        },

        'refused': {
            LiegeBase.get_opinion_editors: ('ExternalReader',),
            'survey_editors': ('Reader', 'AddressEditor'),
            'administrative_editors_environment': ('Editor',),
            'administrative_validators_environment': ('Contributor',),
            'technical_editors_environment': ('EnvironmentEditor',),
            'technical_validators_environment': ('EnvironmentContributor',),
            'environment_readers': ('Reader', 'InternalReader'),
        },

        'abandoned': {
            LiegeBase.get_opinion_editors: ('ExternalReader',),
            'survey_editors': ('Reader', 'AddressEditor'),
            'administrative_editors_environment': ('Editor',),
            'administrative_validators_environment': ('Contributor',),
            'technical_editors_environment': ('EnvironmentEditor',),
            'technical_validators_environment': ('EnvironmentContributor',),
            'environment_readers': ('Reader', 'InternalReader'),
        },
    }
