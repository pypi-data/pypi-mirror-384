from python_sdk_remote.our_object import OurObject

ENTITY_NAME = "FieldLocal"


class FieldLocal(OurObject):

    # TODO Add all FieldLocal
    FieldLocal = {
        "field_id",
        "field_name",
        "display_as",
    }
    field_id: int = 0
    field_name: str = ""

    def __init__(self, entity_name=ENTITY_NAME, **kwargs):
        super().__init__(entity_name, **kwargs)

    # Mandatory pure virtual method from OurObject
    # def get_name(self):
    #     print(f"{ENTITY_NAME} get_name() self.FieldLocal.display_as={self.FieldLocal.display_as}")
    #     return self.FieldLocal.display_as

    # def update_field_in_core_table(self, unique_index_id: int, value: any,  data_source_instance_id: int):
    #     # TODO Get the table_id from the field_table based on the field_id
    #     # TODO Get the table_name from the table_definition_table based on the table_id
    #     # TODO Create SQL to UPSET the value in the table_name where the created_user_id = UserContext.get_user_id() and the data_source_instance_id = data_source_instance_id or NULL
    #     # TODO If the field has entity_id we should also update the mapping table (i.e. email_address, phone ...)