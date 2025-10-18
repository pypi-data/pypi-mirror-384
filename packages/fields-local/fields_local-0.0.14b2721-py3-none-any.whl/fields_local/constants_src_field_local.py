# TODO Please rename the filename from entity_constants.py to your entity. If your entity is country please change the file name to country_constants.py
from logger_local.LoggerComponentEnum import LoggerComponentEnum

# FIELD_MESSAGE_INFORU_API_TYPE_ID = 8

FIELD_LOCAL_CODE_COMPONENT_ID = 5000012
FIELD_LOCAL_CODE_COMPONENT_NAME = "FIELD_InforU_SERVERLESS_PYTHON"
FIELD_LOCAL_CODE_DEVELOPER_EMAIL = "zvi.n@circ.zone"

FIELD_LOGGER_CODE_COMPONENT_ID = 5000012
FIELDS_LOCAL_PYTHON_CODE_COMPONENT_NAME = "Fields Local Python Code"
FIELD_LOGGER_COMPONENT_NAME = "FIELD_InforU_SERVERLESS_PYTHON"
FIELD_DEVELOPER_EMAIL = "zvi.n@circ.zone"

FIELDS_LOCAL_PYTHON_CODE_COMPONENT_ID = 5000012


# Please change everywhere there is "FieldsLocal" to your entity name i.e. "Country"  (Please pay attention the C is in uppercase)
class ConstantsSrcFieldLocal:
    """This is a class of all the constants of FieldsLocal"""

    # TODO Please update your email
    FIELD_DEVELOPER_EMAIL = 'zvi.n@circ.zone'

    # TODO Please change everywhere in the code "FIELD_LOCAL" to "COUNTRY_LOCAL_PYTHON" in case your entity is Country.
    # For example COUNTRY_COMPONENT_ID = 34324
    FIELD_LOGGER_CODE_COMPONENT_ID = 500012
    # TODO Please write your own COMPONENT_NAME
    FIELD_LOCAL_CODE_COMPONENT_NAME = 'FieldsLocal local Python package'
    FIELD_LOCAL_CODE_LOGGER_OBJECT = {
        'componentId': FIELD_LOCAL_CODE_COMPONENT_ID,
        'componentName': FIELD_LOCAL_CODE_COMPONENT_NAME,
        'componentCategory': LoggerComponentEnum.ComponentCategory.Code.value,
        'developerEmailAddress': FIELD_LOCAL_CODE_DEVELOPER_EMAIL
    }

    UNKNOWN_FIELD_ID = 0

    # TODO Please update if you need default values i.e. for testing
    # DEFAULT_XXX_NAME = None
    # DEFAULT_XXX_NAME = None

    FIELD_SCHEMA_NAME = 'field_schema'
    FIELD_TABLE_NAME = 'field_table'
    FIELD_VIEW_NAME = 'field_view'
    FIELD_ML_TABLE_NAME = 'field_ml_table'  # TODO In case you don't use ML table, delete this
    FIELD_ML_VIEW_NAME = 'field_ml_view'
    FIELD_COLUMN_NAME = 'field_id'


# TODO Shall we use get_logger_object function in the code instead of FIELD_LOCAL_CODE_LOGGER_OBJECT and FIELD_LOCAL_TEST_LOGGER_OBJECT?
def get_logger_object(category: str = LoggerComponentEnum.ComponentCategory.Code):
    if category == LoggerComponentEnum.ComponentCategory.Code:
        return {
            'component_id': FIELD_LOGGER_CODE_COMPONENT_ID,
            'component_name': FIELD_LOGGER_COMPONENT_NAME,
            'component_category': LoggerComponentEnum.ComponentCategory.Code,
            'developer_email_address': FIELD_DEVELOPER_EMAIL
        }
    elif category == LoggerComponentEnum.ComponentCategory.Unit_Test:
        return {
            'component_id': FIELDS_LOCAL_PYTHON_CODE_COMPONENT_ID,
            'component_name': FIELD_LOGGER_COMPONENT_NAME,
            'component_category': LoggerComponentEnum.ComponentCategory.Unit_Test,
            'developer_email_address': FIELD_DEVELOPER_EMAIL
        }

