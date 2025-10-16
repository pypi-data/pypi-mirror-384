# -*- coding: utf-8 -*-
from datetime import datetime
from Products.ZCatalog.ProgressHandler import ZLogHandler
from plone import api
from plone.z3cform.layout import FormWrapper
from Products.urban import interfaces

from z3c.form import button
from z3c.form import form, field
from z3c.form.browser.checkbox import CheckBoxFieldWidget

from zope import schema
from zope.browserpage.viewpagetemplatefile import ViewPageTemplateFile
from zope.interface import Interface
from liege.urban import UrbanMessage as _

import json
import logging
import os
import re
import time
import zipfile

logger = logging.getLogger("liege.urban")


class ILicencesExtractForm(Interface):
    start_date = schema.Date(
        title=_(u"Date start"),
        required=False,
    )

    end_date = schema.Date(
        title=_(u"Date end"),
        required=False,
    )

    date_index = schema.Choice(
        title=_(u"Date index"),
        vocabulary="urban.vocabularies.licence_date_indexes",
        default="created",
        required=False,
    )

    licence_type = schema.Set(
        title=_(u"Licence types"),
        value_type=schema.Choice(source="urban.vocabularies.licence_types"),
        required=False,
    )


class LicencesExtractForm(form.Form):
    method = "get"
    fields = field.Fields(ILicencesExtractForm)
    ignoreContext = True

    fields["licence_type"].widgetFactory = CheckBoxFieldWidget

    def updateWidgets(self):
        super(LicencesExtractForm, self).updateWidgets()

    @button.buttonAndHandler(u"Search")
    def handleSearch(self, action):
        data, errors = self.extractData()
        if errors:
            return False
        json_export = do_export(self.context, data)
        self.result = json_export
        response = self.context.REQUEST.RESPONSE
        response.setHeader("Content-type", "application/json")
        response.setHeader("Content-disposition", "attachment; filename=report.json")
        response.setBody(json_export, lock=True)
        return json_export


def do_export(portal, query, filename="activity_report"):
    logger.info("Starting export...")
    start_time = time.time()
    licences_brains = query_licences_brains(**query)
    query_end_time = time.time()
    query_time = query_end_time - start_time
    logger.info("query_licences_brains took {} seconds".format(query_time))
    licences_json = compute_json(licences_brains)
    compute_json_end_time = time.time()
    compute_json_time = compute_json_end_time - query_end_time
    logger.info("compute_json took {} seconds".format(compute_json_time))
    create_archive(filename, licences_json)
    end_time = time.time()
    logger.info("Export done.")
    total_time = end_time - start_time
    logger.info("Total time for {} elements: {} seconds".format(len(licences_brains), total_time))
    items_rate = len(licences_brains) / total_time
    logger.info("That's {} elements/sec on average".format(items_rate))
    if items_rate < 30 and len(licences_brains) > 5000:  # Doesn't make sense to warn when treating small sample
        logger.warn(
            "Something is wrong with the process. It should be at least 30 elements/sec for a decent processing time"
        )
    return licences_json


def create_archive(filename, content):
    if os.path.exists(filename):
        os.remove(filename)
    try:
        archive = zipfile.ZipFile("{}.zip".format(filename), "w", zipfile.ZIP_DEFLATED)
    except RuntimeError:
        archive = zipfile.ZipFile("{}.zip".format(filename), "w")
    archive.writestr("{}.json".format(filename), content)
    archive.close()
    return archive


def query_licences_brains(start_date, end_date, date_index="created", licence_type=[]):
    catalog = api.portal.get_tool("portal_catalog")
    query = {"portal_type": list(licence_type)}
    query[date_index] = {"query": (start_date, end_date), "range": "min:max"}
    licence_brains = catalog(**query)
    return licence_brains


def compute_json(licence_brains):
    CACHE_MINIMIZE_INTERVAL = 5000  # At each interval of element we'll minimize the ZODB's cache
    portal = api.portal.get()
    urban_tool = api.portal.get_tool("portal_urban")
    catalog = api.portal.get_tool("portal_catalog")
    pghandler = ZLogHandler(1000)
    pghandler.init("Building JSON of {} licences".format(len(licence_brains)), len(licence_brains))

    # The catalog is abnormally slow, so we'll make one big query and keep the streets in memory for later
    addresses_path = "/".join(urban_tool.getPhysicalPath()) + "/streets"
    streets_by_UID = {brain.UID: brain for brain in catalog(path=addresses_path, portal_type="Street")}

    # We'll build the JSON string ourself as it is more lightweight to keep a str in memory
    # than a huge json dict and dumps it at the end
    json_str = "["
    for i, brain in enumerate(licence_brains):
        pghandler.report(i)
        json_str += json.dumps(extract_licence_dict(brain, streets_by_UID))
        if i < len(licence_brains) - 1:
            json_str += ",\n"
        if i % CACHE_MINIMIZE_INTERVAL == 0:
            # Making sure we don't blow up the memory consumption
            portal._p_jar.db().cacheMinimize()
    pghandler.finish()
    json_str += "]"
    return json_str


def extract_licence_dict(brain, streets_by_UID):
    licence = brain.getObject()
    cfg = licence.getUrbanConfig()
    licence_dict = {
        "UID": brain.UID,
        "portal_type": brain.portal_type,
        "reference": brain.getReference,
        "address": [extract_address(addr) for addr in licence.getParcels()],
        "form_address": extract_form_address(licence, streets_by_UID),
        "subject": licence.getLicenceSubject(),
        "workflow_state": brain.review_state,
        "folder_managers": [extract_folder_managers(fm) for fm in licence.getFoldermanagers()],
        "applicants": [extract_applicants(obj) for obj in licence.getApplicants()],
        "applicants_historic": [extract_applicants(obj) for obj in licence.get_applicants_history()],
        "deposit_dates": extract_deposit_dates(licence),
        "deposit_types": extract_deposit_types(licence),
        "incomplete_dates": extract_incomplete_dates(licence),
        "inquiry_dates": extract_inquiry_dates(licence),
        "decision_date": extract_decision_date(licence),
        "decision": extract_decision(licence),
    }
    if brain.licence_final_duedate and brain.licence_final_duedate.year < 9000:
        licence_dict["due_date"] = str(brain.licence_final_duedate)
    else:
        licence_dict["due_date"] = ""

    if hasattr(licence, "getArchitects"):
        licence_dict["architects"] = [extract_applicants(arch) for arch in licence.getArchitects()]

    if hasattr(licence, "getLastAcknowledgment"):
        event = licence.getLastAcknowledgment()
        licence_dict["acknowledgement_date"] = event and str(event.getEventDate() or "")

    if hasattr(licence, "getLastLicenceNotification"):
        notification_event = licence.getLastLicenceNotification()
        notification_date = ""
        if notification_event:
            notification_date = str(notification_event.getTransmitDate() or "")
            notification_date = notification_date or str(notification_event.getEventDate() or "")
        licence_dict["notification_date"] = notification_date

    if hasattr(licence, "getLastRecourse"):
        event = licence.getLastRecourse()
        licence_dict["recourse_date"] = event and str(event.getEventDate() or "")
        licence_dict["recourse_decision_date"] = event and str(event.getDecisionDate() or "")
        licence_dict["recourse_decision"] = event and str(event.getRecourseDecision() or "")

    if hasattr(licence, "annoncedDelay"):
        licence_dict["delay"] = extract_annonced_delay(licence, cfg)

    if hasattr(licence, "getProcedureChoice") and hasattr(licence, "procedureChoice"):
        licence_dict["procedure_choice"] = licence.getProcedureChoice()

    if hasattr(licence, "getWorkType"):
        licence_dict["worktype_220"] = licence.getWorkType()

    if hasattr(licence, "getFolderCategoryTownship"):
        licence_dict["worktype_city"] = extract_foldercategory_township(licence, cfg)

    if hasattr(licence, "habitationsBeforeLicence"):
        licence_dict["habitations_before_licence"] = licence.getHabitationsBeforeLicence() or 0
        licence_dict["habitations_asked"] = licence.getAdditionalHabitationsAsked() or 0
        licence_dict["habitations_authorized"] = licence.getAdditionalHabitationsGiven() or 0

    if hasattr(licence, "getAuthority") and hasattr(licence, "authority"):
        licence_dict["authority"] = extract_authority(licence, cfg)

    if hasattr(licence, "getFolderTendency"):
        licence_dict["folder_tendency"] = licence.getFolderTendency()

    if licence.portal_type == "EnvClassBordering":
        licence_dict["external_address"] = extract_external_address(licence)
        licence_dict["external_parcels"] = extract_external_parcels(licence)

    if interfaces.IEnvironmentBase.providedBy(licence):
        licence_dict["authorization_start_date"] = licence.getLastLicenceEffectiveStart() and str(
            licence.getLastLicenceEffectiveStart().getEventDate() or ""
        )
        licence_dict["authorization_end_date"] = licence.getLastLicenceExpiration() and str(
            licence.getLastLicenceExpiration().getEventDate() or ""
        )
        licence_dict["displaying_date"] = licence.getLastDisplayingTheDecision() and str(
            licence.getLastDisplayingTheDecision().getEventDate() or ""
        )
        licence_dict["archives_date"] = licence.getLastSentToArchives() and str(
            licence.getLastSentToArchives().getEventDate() or ""
        )
        licence_dict["archives_description"] = (
            licence.getLastSentToArchives() and str(licence.getLastSentToArchives().getMisc_description()) or ""
        )
        licence_dict["activity_ended_date"] = licence.getLastActivityEnded() and str(
            licence.getLastActivityEnded().getEventDate() or ""
        )
        licence_dict["forced_end_date"] = licence.getLastForcedEnd() and str(
            licence.getLastForcedEnd().getEventDate() or ""
        )
        licence_dict["modification_registry_date"] = licence.getLastModificationRegistry() and str(
            licence.getLastModificationRegistry().getEventDate() or ""
        )
        licence_dict["iile_prescription_date"] = licence.getLastIILEPrescription() and str(
            licence.getLastIILEPrescription().getEventDate() or ""
        )
        licence_dict["provocation_date"] = licence.getLastProvocation() and str(
            licence.getLastProvocation().getEventDate() or ""
        )
        licence_dict["exploitant_change_date"] = licence.getLastProprietaryChangeEvent() and str(
            licence.getLastProprietaryChangeEvent().getEventDate() or ""
        )
        licence_dict["rubrics"] = extract_rubrics(licence)
        licence_dict["rubrics_history"] = extract_rubrics_history(licence)

    if hasattr(licence, "getReferenceSPE"):
        licence_dict["reference_SPE"] = licence.getReferenceSPE() or ""

    if hasattr(licence, "getDepositType"):
        licence_dict["envclass3_deposit_type"] = licence.getDepositType() or ""

    if hasattr(licence, "getInspection_context"):
        licence_dict["inspection_context"] = licence.getInspection_context() or ""

    if hasattr(licence, "getForm_composition") and hasattr(licence, "form_composition"):
        licence_dict["form_composition"] = licence.getForm_composition() or []

    if hasattr(licence, "getLastBuidlingDivisionAttestationMail"):
        event = licence.getLastBuidlingDivisionAttestationMail()
        date = event and str(event.getEventDate() or "")
        licence_dict["inspection_courrier_conformite_date"] = date or ""
        licence_dict["inspection_courrier_conformite_avis"] = event and event.getExternalDecision() or ""

    if hasattr(licence, "getLastBuidlingDivisionAttestationCollege"):
        event = licence.getLastBuidlingDivisionAttestationCollege()
        date = event and str(event.getEventDate() or "")
        licence_dict["inspection_college_conformite_date"] = date or ""
        licence_dict["inspection_college_conformite_avis"] = event and event.getExternalDecision() or ""

    return licence_dict


def extract_decision_date(licence):
    decision_event = _get_decision_event(licence)
    decision_date = decision_event and decision_event.getDecisionDate() or ""
    decision_date = decision_date and str(decision_date) or ""
    return decision_date


def extract_decision(licence):
    decision_event = _get_decision_event(licence)
    decision = decision_event and decision_event.getDecision() or ""
    decision = decision and str(decision) or ""
    return decision


def _get_decision_event(licence):
    decision_event = None
    if interfaces.IEnvironmentBase.providedBy(licence):
        decision_event = licence.getLastLicenceDelivery()
    elif hasattr(licence, "getLastTheLicence"):
        decision_event = licence.getLastTheLicence()
    return decision_event


def extract_annonced_delay(licence, cfg):
    delay = ""
    if licence.getAnnoncedDelay() and any(licence.getAnnoncedDelay()):
        raw_delay = licence.getAnnoncedDelay()
        vocterm = hasattr(cfg, "folderdelays") and cfg.folderdelays.get(licence.getAnnoncedDelay()) or None
        if not vocterm:
            match = re.match("(\d+)j", raw_delay)
            delay = match and match.groups()[0] or ""
        else:
            delay = vocterm.getDeadLineDelay()
    return delay


def extract_foldercategory_township(licence, cfg):
    if licence.getFolderCategoryTownship():
        term = cfg.townshipfoldercategories.get(licence.getFolderCategoryTownship())
        worktypes = []
        if term:
            match = re.match("(.*)\((.*)\)", term.Title())
            if match:
                code, label = match.groups()
                worktypes.append({"code": code, "label": label})
            else:
                worktypes.append({"code": "", "label": term.Title()})
        return worktypes
    else:
        return []


def extract_authority(licence, cfg):
    if licence.getAuthority():
        term = cfg.authority.get(licence.getAuthority())
        if term:
            return term.Title()
    return ""


def extract_rubrics(licence):
    rubrics = []
    for rubric in licence.getRubrics():
        rubric = {
            "num": rubric.id,
            "class": rubric.getExtraValue(),
            "description": rubric.description(),
        }
        rubrics.append(rubric)
    return rubrics


def extract_rubrics_history(licence):
    historic = []
    for line in getattr(licence, "rubrics_history", []):
        new_line = line.copy()
        new_line["time"] = str(line["time"])
        historic.append(new_line)
    return historic


def extract_address(address):
    address_dict = {
        "street_name": address.getStreet_name(),
        "street_number": address.getStreet_number(),
        "street_code": address.getStreet_code(),
        "zipe_code": address.getZip_code(),
        "address_point": address.getAddress_point(),
        "shore": address.getShore(),
    }
    try:
        capakey = address.get_capakey()
    except Exception:
        capakey = ""
    address_dict["capakey"] = capakey
    return address_dict


def extract_external_address(licence):
    addresses_dict = []
    for address in licence.getWorkLocations():
        address_dict = {
            "street_name": address["street"],
            "street_number": address["number"],
            "zipe_code": licence.getZipcode(),
            "city": licence.getCity(),
        }
        addresses_dict.append(address_dict)
    return addresses_dict


def extract_external_parcels(licence):
    parcels_dict = []
    for parcel in licence.getManualParcels():
        parcel_dict = {
            "parcel": parcel["ref"],
            "capakey": parcel["capakey"],
        }
        parcels_dict.append(parcel_dict)
    return parcels_dict


def extract_form_address(licence, streets_by_UID):
    addresses_dict = []
    for address in licence.getWorkLocations():
        street_brain = streets_by_UID.get(address["street"], None)
        if not street_brain:
            continue
        street = street_brain.getObject()
        address_dict = {
            "street_name": street.getStreetName(),
            "street_code": street.getStreetCode(),
            "street_number": address["number"],
        }
        addresses_dict.append(address_dict)
    return addresses_dict


def extract_folder_managers(folder_manager):
    fm_dict = {
        "firstname": folder_manager.getName2(),
        "lastname": folder_manager.getName1(),
    }
    return fm_dict


def extract_applicants(applicant_obj):
    applicant = {
        "firstname": applicant_obj.getName2(),
        "lastname": applicant_obj.getName1(),
        "street": applicant_obj.getStreet(),
        "number": applicant_obj.getNumber(),
        "zipe_code": applicant_obj.getZipcode(),
        "city": applicant_obj.getCity(),
        "country": applicant_obj.getCountry(),
        "phone": applicant_obj.getPhone(),
        "email": applicant_obj.getEmail(),
    }
    if hasattr(applicant_obj, "denomination"):
        applicant["lastname"] = applicant_obj.getDenomination()
    if hasattr(applicant_obj, "legalForm"):
        applicant["firstname"] = applicant_obj.getLegalForm()
    return applicant


def extract_deposit_dates(licence):
    deposits = licence.getAllEvents(interfaces.IDepositEvent)
    dates = [str(event.getEventDate()) for event in deposits]
    return dates


def extract_deposit_types(licence):
    deposits = licence.getAllEvents(interfaces.IDepositEvent)
    deposit_types = [str(event.getDepositType() or "") for event in deposits]
    return deposit_types


def extract_incomplete_dates(licence):
    deposits = licence.getAllEvents(interfaces.IMissingPartEvent)
    dates = [str(event.getEventDate()) for event in deposits]
    return dates


def extract_inquiry_dates(licence):
    inquiries = licence.getAllEvents(interfaces.IInquiryEvent)
    announcements = licence.getAllEvents(interfaces.IAnnouncementEvent)
    all_inquiries = inquiries + announcements
    dates = [
        {"start_date": str(inq.getInvestigationStart()), "end_date": str(inq.getInvestigationEnd())}
        for inq in all_inquiries
    ]
    return dates


class LicencesExtractFormView(FormWrapper):
    """ """

    form = LicencesExtractForm
    index = ViewPageTemplateFile("templates/activity_report.pt")

    def __init__(self, context, request):
        super(LicencesExtractFormView, self).__init__(context, request)

    def render(self):
        form = self.form_instance
        if hasattr(form, "result"):
            result = form.result
            delattr(form, "result")
            return result
        else:
            return super(LicencesExtractFormView, self).render()

    def monthly_export_name(self):
        filename = "monthly_activity_report.zip"
        if os.path.exists(filename):
            mtime = datetime.fromtimestamp(os.path.getmtime(filename))
            return "Rapport d'activité {}".format(mtime.strftime("%d/%m/%Y"))
        return "Pas de rapport disponible"
