from edp.redy.services.houses.constants import HOUSE_URL


DEVICES_URL = HOUSE_URL + '/device'
MODULES_URL = HOUSE_URL + '/modules'
MODULE_URL = HOUSE_URL + '/modules' + '/{module_id}'

INTERFACE_DATA_URL = HOUSE_URL + '/interfacedata'

METERING_API_URL = '/meteringapi'
METERING_URL = METERING_API_URL + \
    '/house/{house_id}/device/{device_id}/module/{module_id}/energy/graph'
COST_PER_KWH_URL = METERING_API_URL + \
    '/house/{house_id}/energy/graph/cost-per-kwh'
