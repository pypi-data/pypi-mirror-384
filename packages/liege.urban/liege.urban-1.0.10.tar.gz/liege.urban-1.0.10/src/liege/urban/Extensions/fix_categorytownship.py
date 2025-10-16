# -*- coding: utf-8 -*-

from plone import api

from Products.urban.interfaces import IGenericLicence

import re


def fix():
    all_vocabulary_mapping = rename_voc()
    catalog = api.portal.get_tool('portal_catalog')
    licences = [b.getObject() for b in catalog(object_provides=IGenericLicence.__identifier__)]
    unmatched_voc = {}

    for licence in licences:
        raw_val = licence.getFolderCategoryTownship()
        if not raw_val:
            continue
        raw_vals = type(raw_val) in (list, tuple) and raw_val or [raw_val]
        new_vals = []
        vocabulary_mapping = all_vocabulary_mapping[licence.portal_type.lower()]
        for old_val in raw_vals:
            new_val = None
            if old_val:
                if old_val in vocabulary_mapping:
                    new_val = vocabulary_mapping[old_val]
                    new_vals.append(new_val)
                elif old_val.upper() in vocabulary_mapping.values():
                    new_val = old_val.upper()
                    new_vals.append(new_val)
                elif vocabulary_mapping:
                    unmatched_voc[old_val] = licence
                    new_vals = []
                    break
        if new_vals:
            licence.setFolderCategoryTownship(new_vals)
        else:
            licence.setFolderCategoryTownship(raw_vals)

    if unmatched_voc:
        import ipdb; ipdb.set_trace()
        raise Exception


def rename_voc():
    urban_tool = api.portal.get_tool('portal_urban')
    cfgs = urban_tool.objectValues('LicenceConfig')
    mapping = {}
    for cfg in cfgs:
        mapping[cfg.id] = {}
        voc_folder = getattr(cfg, 'townshipfoldercategories', None)
        if not voc_folder:
            continue

        for vocterm in cfg.townshipfoldercategories.objectValues():
            match = re.match('(.*)\((.*)\)', vocterm.Title())
            if match:
                code = match.group(1).strip()[:3]
                mapping[cfg.id][vocterm.id] = code
                api.content.rename(obj=vocterm, new_id=code)

    return mapping
