# -*- coding: utf-8 -*-

from Products.urban.config import ExternalConfig
from liege.urban.services.address import LiegeAddressService

try:
    config = ExternalConfig('services')
except:
    config = {}
address_service = LiegeAddressService(**(config and config.liege_address))
