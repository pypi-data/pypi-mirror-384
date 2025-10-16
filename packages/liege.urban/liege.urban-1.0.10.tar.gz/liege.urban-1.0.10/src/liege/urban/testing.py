# -*- coding: utf-8 -*-

from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneWithPackageLayer
from plone.testing import z2
from plone.app.testing import helpers
from plone import api

import liege.urban


def override_testing_profile(profile):
    profile.zcml_filename = "testing.zcml"
    profile.zcml_package = liege.urban
    profile.additional_z2_products = (
        'Products.urban',
        'liege.urban',
        'Products.CMFPlacefulWorkflow',
        'imio.dashboard',
    )
    profile.gs_profile_id = 'liege.urban:tests'


def override_testing_layers(layers):
    """ """

    from Products.urban.testing import UrbanConfigFunctionalLayer
    from Products.urban.testing import UrbanConfigLayer
    from Products.urban.testing import UrbanImportsLayer
    from Products.urban.testing import UrbanLicencesFunctionalLayer
    from Products.urban.testing import UrbanLicencesLayer
    from Products.urban.testing import UrbanWithUsersFunctionalLayer
    from Products.urban.testing import UrbanWithUsersLayer

    LIEGE_URBAN_FIXTURE = PloneWithPackageLayer(
        zcml_filename="testing.zcml",
        zcml_package=liege.urban,
        additional_z2_products=(
            'Products.urban',
            'liege.urban',
            'Products.CMFPlacefulWorkflow',
            'imio.dashboard',
        ),
        gs_profile_id='liege.urban:tests',
        name="LIEGE_URBAN_FIXTURE"
    )

    LIEGE_URBAN_TESTS_PROFILE_INTEGRATION = IntegrationTesting(
        bases=(LIEGE_URBAN_FIXTURE,), name="LIEGE_URBAN_TESTS_PROFILE_INTEGRATION")

    LIEGE_URBAN_TESTS_PROFILE_FUNCTIONAL = FunctionalTesting(
        bases=(LIEGE_URBAN_FIXTURE,), name="LIEGE_URBAN_TESTS_PROFILE_FUNCTIONAL")

    class UrbanLiegeWithUsersLayer(UrbanWithUsersLayer):
        """ """
        default_user = 'rach'
        default_password = 'Aaaaa12345@'

    LIEGE_URBAN_TESTS_INTEGRATION = UrbanLiegeWithUsersLayer(
        bases=(LIEGE_URBAN_FIXTURE, ), name="LIEGE_URBAN_TESTS_INTEGRATION")

    class UrbanLiegeConfigLayer(UrbanConfigLayer, UrbanLiegeWithUsersLayer):
        """ """

        def setUp(self):
            super(UrbanLiegeConfigLayer, self).setUp()
            with helpers.ploneSite() as portal:
                portal.setupCurrentSkin(portal.REQUEST)
                setup_tool = api.portal.get_tool('portal_setup')
                setup_tool.runImportStepFromProfile('profile-liege.urban:default', 'workflow')

    LIEGE_URBAN_TESTS_CONFIG = UrbanLiegeConfigLayer(
        bases=(LIEGE_URBAN_FIXTURE, ), name="LIEGE_URBAN_TESTS_CONFIG")

    LIEGE_URBAN_TESTS_LICENCES = UrbanLicencesLayer(
        bases=(LIEGE_URBAN_FIXTURE, ), name="LIEGE_URBAN_TESTS_LICENCES")

    LIEGE_URBAN_IMPORTS = UrbanImportsLayer(
        bases=(LIEGE_URBAN_FIXTURE, ), name="LIEGE_URBAN_IMPORTS")

    class UrbanLiegeWithUsersFunctionalLayer(UrbanWithUsersFunctionalLayer):
        """
        Instanciate test users

        Must collaborate with a layer that installs Plone and Urban
        Useful for performances: Plone site is instanciated only once
        """
        default_user = 'rach'
        default_password = 'Aaaaa12345@'

    LIEGE_URBAN_TESTS_FUNCTIONAL = UrbanLiegeWithUsersFunctionalLayer(
        bases=(LIEGE_URBAN_FIXTURE, ), name="LIEGE_URBAN_TESTS_FUNCTIONAL")

    class UrbanLiegeConfigFunctionalLayer(UrbanConfigFunctionalLayer, UrbanLiegeWithUsersFunctionalLayer):
        """ """
        default_user = 'rich'
        default_password = 'Aaaaa12345@'

        def setUp(self):
            super(UrbanLiegeConfigFunctionalLayer, self).setUp()
            with helpers.ploneSite() as portal:
                portal.setupCurrentSkin(portal.REQUEST)
                setup_tool = api.portal.get_tool('portal_setup')
                setup_tool.runImportStepFromProfile('profile-liege.urban:default', 'workflow')

    LIEGE_URBAN_TESTS_CONFIG_FUNCTIONAL = UrbanLiegeConfigFunctionalLayer(
        bases=(LIEGE_URBAN_FIXTURE, ), name="LIEGE_URBAN_TESTS_CONFIG_FUNCTIONAL")

    LIEGE_URBAN_TESTS_LICENCES_FUNCTIONAL = UrbanLicencesFunctionalLayer(
        bases=(LIEGE_URBAN_FIXTURE, ), name="LIEGE_URBAN_TESTS_LICENCES_FUNCTIONAL")

    LIEGE_URBAN_TEST_ROBOT = UrbanConfigFunctionalLayer(
        bases=(
            LIEGE_URBAN_FIXTURE,
            REMOTE_LIBRARY_BUNDLE_FIXTURE,
            z2.ZSERVER_FIXTURE
        ),
        name="LIEGE_URBAN_ROBOT"
    )

    layers_mapping = {
        'URBAN_TESTS_PROFILE_DEFAULT': LIEGE_URBAN_FIXTURE,
        'URBAN_TESTS_PROFILE_INTEGRATION': LIEGE_URBAN_TESTS_PROFILE_INTEGRATION,
        'URBAN_TESTS_PROFILE_FUNCTIONAL': LIEGE_URBAN_TESTS_PROFILE_FUNCTIONAL,
        'URBAN_TESTS_INTEGRATION': LIEGE_URBAN_TESTS_INTEGRATION,
        'URBAN_TESTS_CONFIG': LIEGE_URBAN_TESTS_CONFIG,
        'URBAN_TESTS_LICENCES': LIEGE_URBAN_TESTS_LICENCES,
        'URBAN_IMPORTS': LIEGE_URBAN_IMPORTS,
        'URBAN_TESTS_FUNCTIONAL': LIEGE_URBAN_TESTS_FUNCTIONAL,
        'URBAN_TESTS_CONFIG_FUNCTIONAL': LIEGE_URBAN_TESTS_CONFIG_FUNCTIONAL,
        'URBAN_TESTS_LICENCES_FUNCTIONAL': LIEGE_URBAN_TESTS_LICENCES_FUNCTIONAL,
        'URBAN_TEST_ROBOT': LIEGE_URBAN_TEST_ROBOT,
    }
    new_layers = dict([(layer.__name__, layers_mapping[layer.__name__]) for layer in layers])
    return new_layers
