# -*- coding: utf-8 -*-

from zope.i18nmessageid import MessageFactory
UrbanMessage = MessageFactory('liege.urban')

import liege.urban.content.genericlicence
import liege.urban.content.inquiry_licence
import liege.urban.content.env_base
# !!! import order matters, always import genericlicence schema and
# inquiry_licence changes before other licence types schema changes
import liege.urban.content.article127
import liege.urban.content.buildlicence
import liege.urban.content.codt_article127
import liege.urban.content.codt_buildlicence
import liege.urban.content.codt_cu2
import liege.urban.content.codt_integratedlicence
import liege.urban.content.codt_uniquelicence
import liege.urban.content.contact
import liege.urban.content.cu2
import liege.urban.content.env_bordering
import liege.urban.content.integratedlicence
import liege.urban.content.uniquelicence
import liege.urban.content.foldermanager
import liege.urban.content.inquiry_event
import liege.urban.content.inspection
import liege.urban.content.portion_out
import liege.urban.content.preliminarynotice
import liege.urban.content.urbanevent
import liege.urban.content.urbanevent_opinionrequest
import liege.urban.content.roaddecree  # noqa
from liege.urban.config import LICENCE_FINAL_STATES


# hide assigned_user and assigned_group fields from task
from collective.task.behaviors import ITask
from plone.directives.form import mode
from zope.interface import Interface
mode_values = ITask._Element__tagged_values.get(mode.key, [])
mode_values.append((Interface, 'assigned_user', 'hidden'))
mode_values.append((Interface, 'assigned_group', 'hidden'))
ITask._Element__tagged_values[mode.key] = mode_values
# END # hide assigned_user and assigned_group fields from task

from Products.urban.schedule.vocabulary import URBAN_TYPES_INTERFACES
from liege.urban.interfaces import IInternalOpinionRequestEvent
URBAN_TYPES_INTERFACES[u'Avis de services internes à la ville'] = IInternalOpinionRequestEvent
from Products.urban import config
config.LICENCE_FINAL_STATES = LICENCE_FINAL_STATES


def initialize(context):
    """Initializer called when used as a Zope 2 product."""
    from liege.urban import config
    from Products.Archetypes import atapi
    from Products.CMFCore import utils

    content_types, constructors, ftis = atapi.process_types(
        atapi.listTypes(config.PROJECTNAME),
        config.PROJECTNAME)

    for atype, constructor in zip(content_types, constructors):
        utils.ContentInit('%s: %s' % (config.PROJECTNAME, atype.portal_type),
                          content_types=(atype, ),
                          permission=config.ADD_PERMISSIONS[atype.portal_type],
                          extra_constructors=(constructor, ),
                          ).initialize(context)

from Products.urban import config
config.registerClasses()
