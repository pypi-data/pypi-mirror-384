# TODO Please rename the filename from entity_constants.py to your entity. If your entity is country please change the file name to country_constants.py
from logger_local.LoggerComponentEnum import LoggerComponentEnum

# WHATSAPP_MESSAGE_INFORU_API_TYPE_ID = 8

WHATSAPP_LOGGER_COMPONENT_ID = 298
WHATSAPP_LOGGER_COMPONENT_NAME = "WhatsApp_InforU_SERVERLESS_PYTHON"
WHATSAPP_DEVELOPER_EMAIL = "zvi.n@circ.zone"


# Please change everywhere there is "FieldsLocal" to your entity name i.e. "Country"  (Please pay attention the C is in uppercase)
class ConstantsSrcFieldsLocal:
    """This is a class of all the constants of FieldsLocal"""

    # TODO Please update your email
    DEVELOPER_EMAIL = 'tal.r@circ.zone'

    # TODO Please change everywhere in the code "FIELDS_LOCAL" to "COUNTRY_LOCAL_PYTHON" in case your entity is Country.
    # TODO Please send a message in the Slack to #request-to-open-component-id and get your COMPONENT_ID
    # For example COUNTRY_COMPONENT_ID = 34324
    # TODO search for the CODE_COMPONENT_ID and TEST_COMPONENT_ID in component.compontent_table (if needed INSERT new record)    
    FIELDS_LOCAL_CODE_COMPONENT_ID = 5000010
    FIELDS_LOCAL_TEST_COMPONENT_ID = 5000011
    # TODO Please write your own COMPONENT_NAME
    FIELDS_LOCAL_COMPONENT_NAME = 'FieldsLocal local Python package'
    FIELDS_LOCAL_CODE_LOGGER_OBJECT = {
        'component_id': FIELDS_LOCAL_CODE_COMPONENT_ID,
        'component_name': FIELDS_LOCAL_COMPONENT_NAME,
        'component_category': LoggerComponentEnum.ComponentCategory.Code.value,
        'developer_email_address': DEVELOPER_EMAIL
    }
    # FIELDS_LOCAL_TEST_LOGGER_OBJECT = {
    #     'componentId': FIELDS_LOCAL_TEST_COMPONENT_ID,
    #     'componentName': FIELDS_LOCAL_COMPONENT_NAME,
    #     'componentCategory': LoggerComponentEnum.ComponentCategory.Unit_Test.value,
    #     'testingFramework': LoggerComponentEnum.testingFramework.pytest.value,  # TODO Please add the framework you use
    #     'developerEmailAddress': DEVELOPER_EMAIL
    # }

    UNKNOWN_FIELDS_LOCAL_ID = 0

    # TODO Please update if you need default values i.e. for testing
    # DEFAULT_XXX_NAME = None
    # DEFAULT_XXX_NAME = None

    FIELD_SCHEMA_NAME = 'field'
    FIELD_LOCAL_TABLE_NAME = 'field_table'
    FIELD_LOCAL_VIEW_NAME = 'field_view'
    FIELD_LOCAL_ML_TABLE_NAME = 'field_ml_table'  # TODO In case you don't use ML table, delete this
    FIELD_LOCAL_ML_VIEW_NAME = 'field_ml_view'
    FIELD_LOCAL_COLUMN_NAME = 'field_id'


def get_logger_object(category: str = LoggerComponentEnum.ComponentCategory.Code):
    if category == LoggerComponentEnum.ComponentCategory.Code:
        return {
            'component_id': WHATSAPP_LOGGER_COMPONENT_ID,
            'component_name': WHATSAPP_LOGGER_COMPONENT_NAME,
            'component_category': LoggerComponentEnum.ComponentCategory.Code,
            'developer_email_address': WHATSAPP_DEVELOPER_EMAIL
        }
    elif category == LoggerComponentEnum.ComponentCategory.Unit_Test:
        return {
            'component_id': WHATSAPP_LOGGER_COMPONENT_ID,
            'component_name': WHATSAPP_LOGGER_COMPONENT_NAME,
            'component_category': LoggerComponentEnum.ComponentCategory.Unit_Test,
            'developer_email_address': WHATSAPP_DEVELOPER_EMAIL
        }
