# -*- coding: utf-8 -*-

from plone import api

from Products.cron4plone.browser.configlets.cron_configuration import ICronConfiguration
from Products.urban.config import URBAN_TYPES
from Products.urban.config import URBAN_ENVIRONMENT_TYPES
from Products.urban.setuphandlers import createScheduleConfig
from Products.urban.utils import getEnvironmentLicenceFolderIds
from Products.urban.utils import getLicenceFolderId

from imio.schedule.utils import set_schedule_view

from zope.component import queryUtility
from zope.interface import alsoProvides
from zExceptions import BadRequest

import os


def post_install(context):
    """Post install script"""
    if context.readDataFile('liegeurban_default.txt') is None:
        return
    # Do something during the installation of this package

    setAllowedTypes(context)
    addLiegeGroups(context)
    setDefaultApplicationSecurity(context)
    setupSurveySchedule(context)
    addScheduleConfigs(context)
    addTestUsers(context)
    addDefaultCronJobs(context)


def setAllowedTypes(context):
    """
    New content types are added on liege profile. Allow these types to be created.
    """
    portal_types = api.portal.get_tool('portal_types')
    licence_types = (
        'BuildLicence',
        'Article127',
        'UniqueLicence',
        'IntegratedLicence',
        'UrbanCertificateTwo',
        'CODT_BuildLicence',
        'CODT_Article127',
        'CODT_UniqueLicence',
        'CODT_IntegratedLicence',
        'CODT_UrbanCertificateTwo',
        'Inspection',
        'Ticket',
    )

    for licence_type in licence_types:
        type_info = getattr(portal_types, licence_type)
        values = type_info.allowed_content_types
        if 'UrbanEventAcknowledgment' not in values:
            type_info.allowed_content_types = values + ('UrbanEventAcknowledgment',)

    for licence_type in URBAN_ENVIRONMENT_TYPES:
        type_info = getattr(portal_types, licence_type)
        values = type_info.allowed_content_types
        if 'UrbanEventMayor' not in values:
            type_info.allowed_content_types = values + ('UrbanEventMayor',)
        if 'UrbanEventWithEnvironmentValidation' not in values:
            type_info.allowed_content_types = values + ('UrbanEventWithEnvironmentValidation',)

    for licence_type in URBAN_TYPES:
        type_info = getattr(portal_types, licence_type)
        values = type_info.allowed_content_types
        if 'UrbanEventMayor' not in values:
            type_info.allowed_content_types = values + ('UrbanEventMayor',)

    type_info = getattr(portal_types, 'CODT_UniqueLicence')
    new_values = type_info.allowed_content_types
    if 'UrbanEventAcknowledgment' not in new_values:
        new_values = new_values + ('UrbanEventAcknowledgment',)
    if 'UrbanEventPreliminaryAdvice' not in new_values:
        new_values = new_values + ('UrbanEventPreliminaryAdvice',)
    type_info.allowed_content_types = new_values


def addLiegeGroups(context):
    """
    Add a groups of application users.
    """

    portal_groups = api.portal.get_tool('portal_groups')
    portal_urban = api.portal.get_tool('portal_urban')
    app_folder = getattr(api.portal.get(), "urban")

    portal_groups.addGroup("urban_internal_readers", title="Internal readers")
    portal_groups.setRolesForGroup('urban_internal_readers', ('UrbanMapReader', ))
    portal_urban.manage_addLocalRoles("urban_internal_readers", ("Reader", ))
    portal_groups.addPrincipalToGroup("urban_internal_readers", 'urban_readers')

    portal_groups.addGroup("administrative_editors", title="Administrative Editors")
    portal_groups.setRolesForGroup('administrative_editors', ('UrbanMapReader', ))
    portal_urban.manage_addLocalRoles("administrative_editors", ("Reader", ))
    portal_groups.addPrincipalToGroup("administrative_editors", 'urban_internal_readers')
    portal_groups.addPrincipalToGroup("administrative_editors", 'urban_editors')

    portal_groups.addGroup("administrative_validators", title="Administrative Validators")
    portal_groups.setRolesForGroup('administrative_validators', ('UrbanMapReader', ))
    portal_urban.manage_addLocalRoles("administrative_validators", ("Reader", ))
    portal_groups.addPrincipalToGroup("administrative_validators", 'urban_internal_readers')
    portal_groups.addPrincipalToGroup("administrative_validators", 'urban_editors')
    portal_groups.addPrincipalToGroup("administrative_validators", 'administrative_editors')

    portal_groups.addGroup("technical_editors", title="Technical Editors")
    portal_groups.setRolesForGroup('technical_editors', ('UrbanMapReader', ))
    portal_urban.manage_addLocalRoles("technical_editors", ("Reader", ))
    portal_groups.addPrincipalToGroup("technical_editors", 'urban_internal_readers')

    portal_groups.addGroup("technical_validators", title="Technical Validators")
    portal_groups.setRolesForGroup('technical_validators', ('UrbanMapReader', ))
    portal_urban.manage_addLocalRoles("technical_validators", ("Reader", ))
    portal_groups.addPrincipalToGroup("technical_validators", 'urban_internal_readers')
    portal_groups.addPrincipalToGroup("technical_validators", 'technical_editors')

    portal_groups.addGroup("administrative_editors_environment", title="Administrative Editors Environment")
    portal_groups.setRolesForGroup('administrative_editors_environment', ('UrbanMapReader', ))
    portal_urban.manage_addLocalRoles("administrative_editors_environment", ("Reader", ))
    portal_groups.addPrincipalToGroup("administrative_editors_environment", 'environment_readers')
    portal_groups.addPrincipalToGroup("administrative_editors_environment", 'environment_editors')

    portal_groups.addGroup("administrative_validators_environment", title="Administrative Validators Environment")
    portal_groups.setRolesForGroup('administrative_validators_environment', ('UrbanMapReader', ))
    portal_urban.manage_addLocalRoles("administrative_validators_environment", ("Reader", ))
    portal_groups.addPrincipalToGroup("administrative_validators_environment", 'environment_readers')
    portal_groups.addPrincipalToGroup("administrative_validators_environment", 'environment_editors')
    portal_groups.addPrincipalToGroup("administrative_validators_environment", 'administrative_editors_environment')

    portal_groups.addGroup("technical_editors_environment", title="Technical Editor Environments")
    portal_groups.setRolesForGroup('technical_editors_environment', ('UrbanMapReader', ))
    portal_urban.manage_addLocalRoles("technical_editors_environment", ("Reader", ))
    portal_groups.addPrincipalToGroup("technical_editors_environment", 'environment_readers')

    portal_groups.addGroup("technical_validators_environment", title="Technical Validators Environment")
    portal_groups.setRolesForGroup('technical_validators_environment', ('UrbanMapReader', ))
    portal_urban.manage_addLocalRoles("technical_validators_environment", ("Reader", ))
    portal_groups.addPrincipalToGroup("technical_validators_environment", 'environment_readers')
    portal_groups.addPrincipalToGroup("technical_validators_environment", 'technical_editors_environment')

    portal_groups.addGroup("survey_editors", title="Survey Editors")
    portal_groups.setRolesForGroup('survey_editors', ('UrbanMapReader', ))
    portal_urban.manage_addLocalRoles("survey_editors", ("Reader", ))

    portal_groups.addGroup("inspection_validators", title="Inspection Validators")
    portal_groups.setRolesForGroup('inspection_validators', ('UrbanMapReader', ))
    portal_urban.manage_addLocalRoles("inspection_validators", ("Reader", ))
    portal_groups.addPrincipalToGroup("inspection_validators", 'inspection_editors')

    portal_groups.addGroup("fittingout_technicians", title="Roaddecrees editors")
    portal_groups.setRolesForGroup('fittingout_technicians', ('UrbanMapReader', ))
    portal_urban.manage_addLocalRoles("fittingout_technicians", ("Reader", ))
    portal_groups.addPrincipalToGroup("fittingout_technicians", 'urban_readers')

    portal_groups.addGroup("fittingout_technicians_validators", title="Roaddecrees validators")
    portal_groups.setRolesForGroup('fittingout_technicians_validators', ('UrbanMapReader', ))
    portal_urban.manage_addLocalRoles("fittingout_technicians_validators", ("Reader", ))
    portal_groups.addPrincipalToGroup("fittingout_technicians_validators", 'urban_readers')

    portal_groups.addGroup("Voirie_readers", title="Roaddecrees readers")
    portal_groups.setRolesForGroup('Voirie_readers', ('RoadReader', ))
    portal_urban.manage_addLocalRoles("Voirie_readers", ("Reader",'RoadReader', ))
    roaddecrees_folder = getattr(app_folder, "roaddecrees")
    roaddecrees_folder.manage_addLocalRoles("Voirie_readers", ("Reader",'RoadReader',))

    # external services
    services = ['Voirie', 'Access', 'Plantation', 'SSSP', 'EDII']
    for service in services:
        portal_groups.addGroup("{}_editors".format(service), title="{} Editors".format(service))
        portal_groups.setRolesForGroup('{}_editors'.format(service), ('UrbanMapReader', ))
        portal_urban.manage_addLocalRoles("{}_editors".format(service), ("Reader", ))
        portal_groups.addPrincipalToGroup("{}_editors".format(service), 'opinions_editors')
        portal_groups.addGroup("{}_validators".format(service), title="{} Validators".format(service))
        portal_groups.setRolesForGroup('{}_validators'.format(service), ('UrbanMapReader', ))
        portal_urban.manage_addLocalRoles("{}_validators".format(service), ("Reader", ))
        portal_groups.addPrincipalToGroup("{}_validators".format(service), 'opinions_editors')

    portal_urban.reindexObjectSecurity()


def setDefaultApplicationSecurity(context):
    """
       Set sharing on differents folders to access the application
    """
    site = context.getSite()
    app_folder = getattr(site, "urban")
    uniquelicences_names = [
        getLicenceFolderId('UniqueLicence'),
        getLicenceFolderId('CODT_UniqueLicence'),
        getLicenceFolderId('IntegratedLicence'),
        getLicenceFolderId('CODT_IntegratedLicence'),
    ]
    environment_folder_names = getEnvironmentLicenceFolderIds() + uniquelicences_names
    for folder_name in environment_folder_names:
        if hasattr(app_folder, folder_name):
            folder = getattr(app_folder, folder_name)
            try:
                folder.manage_addProperty('urbanConfigId', folder_name.strip('s'), 'string')
            except BadRequest:
                pass
            folder.manage_delLocalRoles(["environment_editors"])
            folder.manage_delLocalRoles(["administrative_editors_environment"])
            folder.manage_delLocalRoles(["administrative_validators_environment"])
            folder.manage_delLocalRoles(["inspection_editors"])
            folder.manage_delLocalRoles(["inspection_validators"])
            if folder_name in environment_folder_names:
                folder.manage_addLocalRoles("environment_readers", ("Reader", ))
                folder.manage_addLocalRoles("administrative_editors_environment", ("Contributor",))
                folder.manage_addLocalRoles("administrative_validators_environment", ("Contributor",))
            if folder_name == 'envclasthrees':
                folder.manage_addLocalRoles("technical_editors_environment", ("Contributor",))
                folder.manage_addLocalRoles("technical_validators_environment", ("Contributor",))
    inspection_folder_names = [
        getLicenceFolderId('Inspection'),
    ]
    for folder_name in inspection_folder_names:
        if hasattr(app_folder, folder_name):
            folder = getattr(app_folder, folder_name)
            try:
                folder.manage_addProperty('urbanConfigId', folder_name.strip('s'), 'string')
            except BadRequest:
                pass
            folder.manage_delLocalRoles(["inspection_editors"])
            folder.manage_delLocalRoles(["inspection_validators"])
            folder.manage_delLocalRoles(["administrative_editors"])
            folder.manage_delLocalRoles(["administrative_validators"])
            folder.manage_addLocalRoles("inspection_editors", ("Contributor", ))
            folder.manage_addLocalRoles("inspection_validators", ("Contributor", ))
            folder.manage_addLocalRoles("administrative_editors", ("Contributor",))
            folder.manage_addLocalRoles("administrative_validators", ("Contributor",))


def setupSurveySchedule(context):
    """
    Enable schedule faceted navigation on schedule folder.
    """
    site = context.getSite()
    urban_folder = site.urban
    portal_urban = api.portal.get_tool('portal_urban')

    if not hasattr(urban_folder, 'survey_schedule'):
        urban_folder.invokeFactory('Folder', id='survey_schedule')
    schedule_folder = getattr(urban_folder, 'survey_schedule')
    schedule_folder.manage_addLocalRoles("survey_editors", ("Reader", ))
    schedule_folder.reindexObjectSecurity()

    schedule_config = createScheduleConfig(
        container=portal_urban,
        portal_type='GenericLicence',
        title=u'Configuration d\'échéances survey',
        id='survey_schedule'
    )

    config_path = '{}/schedule/config/survey_schedule.xml'.format(os.path.dirname(__file__))
    set_schedule_view(schedule_folder, config_path, schedule_config)


def addScheduleConfigs(context):
    """
    Add schedule config for each licence type.
    """
    if context.readDataFile('liegeurban_default.txt') is None:
        return

    profile_name = context._profile_path.split('/')[-1]
    module_name = 'liege.urban.profiles.%s.schedule_config' % profile_name
    attribute = 'schedule_config'
    module = __import__(module_name, fromlist=[attribute])
    schedule_config = getattr(module, attribute)

    portal_urban = api.portal.get_tool('portal_urban')

    for schedule_config_id in ['survey_schedule', 'opinions_schedule']:
        schedule_folder = getattr(portal_urban, schedule_config_id)
        _create_task_configs(schedule_folder, schedule_config[schedule_config_id])

    for urban_type in URBAN_TYPES:
        licence_config_id = urban_type.lower()
        if licence_config_id in schedule_config:
            config_folder = getattr(portal_urban, licence_config_id)
            schedule_folder = getattr(config_folder, 'schedule')
            taskconfigs = schedule_config[licence_config_id]
            _create_task_configs(schedule_folder, taskconfigs)


def _create_task_configs(container, taskconfigs):
    """
    """
    for taskconfig_kwargs in taskconfigs:
        subtasks = taskconfig_kwargs.get('subtasks', [])
        task_config_id = taskconfig_kwargs['id']

        if task_config_id not in container.objectIds():
            marker_interface = taskconfig_kwargs.get('marker_interface', None)

            task_config_id = container.invokeFactory(**taskconfig_kwargs)
            task_config = getattr(container, task_config_id)

            # set custom view fields
            task_config.dashboard_collection.customViewFields = (
                u'sortable_title',
                u'address_column',
                u'assigned_user_column',
                u'status',
                u'due_date',
                u'task_actions_column',
            )

            # set marker_interface
            if marker_interface:
                alsoProvides(task_config, marker_interface)

        task_config = getattr(container, task_config_id)
        for subtasks_kwargs in subtasks:
            _create_task_configs(container=task_config, taskconfigs=subtasks)


def addTestUsers(context):
    """
    Add some test users for each group
    """
    password = 'Aaaaa12345@'
    email = 'dll@imio.be'

    users = [
        {
            'username': 'rich',
            'group': 'administrative_editors',
            'properties': {'fullname': 'Richard Administrative'},
        },
        {
            'username': 'rach',
            'group': 'administrative_validators',
            'properties': {'fullname': 'Rachel Val Administrative'},
        },
        {
            'username': 'gert',
            'group': 'technical_editors',
            'properties': {'fullname': 'Gertrude Technical'},
        },
        {
            'username': 'gont',
            'group': 'technical_validators',
            'properties': {'fullname': 'Gontrand Val Technical'},
        },
        {
            'username': 'rich_e',
            'group': 'administrative_editors_environment',
            'properties': {'fullname': 'Richard Administrative Environment'},
        },
        {
            'username': 'rach_e',
            'group': 'administrative_validators_environment',
            'properties': {'fullname': 'Rachel Val Administrative Environment'},
        },
        {
            'username': 'gert_e',
            'group': 'technical_editors_environment',
            'properties': {'fullname': 'Gertrude Technical Environment'},
        },
        {
            'username': 'gont_e',
            'group': 'technical_validators_environment',
            'properties': {'fullname': 'Gontrand Val Technical Environment'},
        },
        {
            'username': 'survivor',
            'group': 'survey_editors',
            'properties': {'fullname': 'Survivor Survey'},
        },
        {
            'username': 'gadget',
            'group': 'inspection_editors',
            'properties': {'fullname': 'Inspector Gadget'},
        },
        {
            'username': 'derrick',
            'group': 'inspection_validators',
            'properties': {'fullname': 'Inspector Derrick'},
        },
    ]

    for user_args in users:
        group_id = user_args.pop('group')
        if not api.user.get(username=user_args.get('username')):
            user = api.user.create(password=password, email=email, **user_args)
            api.group.add_user(groupname=group_id, username=user.id)


def addDefaultCronJobs(context):
    cron_cfg = queryUtility(ICronConfiguration, name='cron4plone_config', context=api.portal.get())
    if u'55 0 1 * portal/@@monthly_activity_report' not in cron_cfg.cronjobs:
        cron_cfg.cronjobs = cron_cfg.cronjobs + [
            u'55 0 1 * portal/@@monthly_activity_report',
        ]
