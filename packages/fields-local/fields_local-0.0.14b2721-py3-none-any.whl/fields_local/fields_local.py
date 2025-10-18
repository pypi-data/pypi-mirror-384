from logger_local.LoggerLocal import Logger
from database_mysql_local.generic_crud_mysql import GenericCrudMysql
from logger_local.LoggerComponentEnum import LoggerComponentEnum

from .constants_src_fields_local import ConstantsSrcFieldsLocal


FIELD_SCHEMA_NAME = "field"
# TODO Can we comment out the below three lines? Do you know if this will be the default for the database package?
FIELD_TABLE_NAME = "field_table"
FIELD_VIEW_NAME = "field_view"
FIELD_GENERAL_VIEW_NAME = "field_general_view"

FIELD_LOCAL_PYTHON_PACKAGE_COMPONENT_ID = 229
FIELD_LOCAL_PYTHON_PACKAGE_COMPONENT_NAME = "field_main_local_python"
DEVELOPER_EMAIL = "zvi.n@circ.zone"

object_init = {
    "component_id": FIELD_LOCAL_PYTHON_PACKAGE_COMPONENT_ID,
    "component_name": FIELD_LOCAL_PYTHON_PACKAGE_COMPONENT_NAME,
    "component_category": LoggerComponentEnum.ComponentCategory.Code.value,
    "developer_email_address": DEVELOPER_EMAIL,
}

class FieldsLocal(GenericCrudMysql):
    
    def __init__(self, is_test_data: bool = False):
        super().__init__(
            default_schema_name=FIELD_SCHEMA_NAME,
            default_table_name=FIELD_TABLE_NAME,
            default_view_table_name=FIELD_VIEW_NAME, 
            is_test_data=is_test_data
        )

    def get_variable_id_name_dict(self, where: str = None, params:tuple = None) -> dict[int,str]:
        """ Returns a dictionary mapping variable ids to the variable name"""
        rows = self.select_multi_dict_by_where(
            select_clause_value="variable_id, name",
            view_table_name="variable_view",
            where=where,
            params=params,
            )
        data = {}
        for row in rows:
            data[row['variable_id']] = row['name']
        return data
    
    def get_field_name_by_field_id(self, field_id: int) -> str:
        """Returns the name of a field based on the field id"""
        field_name = self.select_one_value_by_where(
            select_clause_value="name",
            where="field_id=%s",
            params=(field_id,)
        )
        return field_name

    def get_field_id_by_field_name(self, field_name: str):
        """Returns the field id for a specific field name"""
        field_id = self.select_one_value_by_where(
            select_clause_value="field_id",
            where="name=%s",
            params=(field_name,)
        )
        return field_id

    # TODO name -> field_name
    def get_variable_id_by_field_name(self, name: str) -> int:
        """Returns the variable id that corresponds to a specific field name"""
        variable_id = self.select_one_value_by_where(
            select_clause_value="variable_id",
            where="name=%s",
            params=(name,)
        )
        return variable_id
    
    def get_field_name_by_variable_id(self, variable_id: int):
        """Returns the name of the field that corresponds to a specific variable id"""
        name = self.select_one_value_by_where(
            select_clause_value="name",
            where="variable_id=%s",
            params=(variable_id,)
        )
        return name

    def get_field_id_by_alias_name(self, name: str) -> int:
        """Returns the id of the field that has a specific alias"""
        field_id = self.select_one_value_by_where(
            view_table_name="field_alias_view",
            select_clause_value="field_id",
            where="field_name=%s",
            params=(name,)
        )
        return field_id

    def get_database_field_name_by_field_id(self, field_id: int):
        """Returns the database field name that corresponds to a specific field id"""
        field_id = self.select_one_value_by_where(
            select_clause_value="database_field_name",
            where="field_id=%s",
            params=(field_id,)
        )
        return field_id
    
    def get_table_id_by_field_id(self, field_id: int) -> int:
        """Returns the id of the table that contains a specific field based on the id of the field"""
        table_id = self.select_one_value_by_where(
            select_clause_value="table_id",
            where="field_id=%s",
            params=(field_id,)
        )
        return table_id
    
    def get_table_schema_by_table_id(self, table_id: int) -> str:
        """Returns the schema that contains a specific table based on the id of the table"""
        #manual query here because schema is a keyword and needs backticks
        query = 'SELECT  `schema` \
            FROM `database`.`table_definition_table` \
            WHERE (table_definition_id=%s AND `schema` IS NOT NULL) AND end_timestamp IS NULL  LIMIT 1;'
        params = (table_id,)
        self.cursor.execute(sql_statement=query,
                            sql_parameters=params
                            )
        table_schema = self.cursor.fetchone()[0]
        return table_schema

    def get_table_name_by_table_id(self, table_id: int) -> str:
        """Returns the name of the table based on the table id"""
        table_table = self.select_one_value_by_where(
            schema_name="database",
            view_table_name="table_definition_view",
            select_clause_value="table_name",
            where="table_definition_id=%s",
            params=(table_id,)
        )
        return table_table

    def get_table_view_name_by_table_id(self, table_id: int) -> str:
        """Returns the name of the view of a table based on the id of the table"""
        table_view = self.select_one_value_by_where(
            schema_name="database",
            view_table_name="table_definition_view",
            select_clause_value="view_name",
            where="table_definition_id=%s",
            params=(table_id,)
        )
        return table_view

    def get_table_schema_by_field_id(self, field_id: int) -> str:
        """Returns the schema of the table that contains a given field based on the field id"""
        table_id = self.get_table_id_by_field_id(field_id=field_id)
        table_schema = self.get_table_schema_by_table_id(table_id=table_id)
        return table_schema

    def get_table_name_by_field_id(self, field_id: int) -> str:
        """Returns the name of the table that contains a given field based on the field id"""
        table_id = self.get_table_id_by_field_id(field_id=field_id)
        table_name = self.get_table_name_by_table_id(table_id=table_id)
        return table_name

    def get_table_view_name_by_field_id(self, field_id: int) -> str:
        """Returns the view of the table that contains a given field based on the field id"""
        table_id = self.get_table_id_by_field_id(field_id=field_id)
        table_view_name = self.get_table_view_name_by_table_id(table_id=table_id)
        return table_view_name
    
    def get_fields(self) -> dict:
        """Returns a dictionary mapping field ids to field names"""
        fields = dict(self.select_multi_tuple_by_where(
            select_clause_value="field_id, name"
            ))
        return fields
        
    def get_field_name_by_field_id_and_data_source_type_id(self, field_id: int, data_source_type_id: int) -> str | None:
        """
        Get the field name from the database
        :param field_id: The field ID
        :param data_source_type_id: The data source ID
        :return: The field name
        """

        data_source_type__field_tuples = self.select_multi_tuple_by_where(
            schema_name="data_source_type__field",
            view_table_name="data_source_type__field_view",
            select_clause_value="external_field_name",
            where="data_source_type_id = %s AND field_id = %s",
            params=(data_source_type_id, field_id)
            )

        if data_source_type__field_tuples:
            field_name = data_source_type__field_tuples[0][0]
            # TODO Can we have one return statement?
            return field_name
        else:
            field_name = None
            return field_name
        
    def upsert_into_table_by_table_id(self, table_id: int, data_dict: dict, compare_dict: dict = None):
        schema_name = self.get_table_schema_by_table_id(table_id=table_id)
        table_name = self.get_table_name_by_table_id(table_id=table_id)
        view_name = self.get_table_view_name_by_table_id(table_id=table_id)
        row = self.upsert(schema_name=schema_name,
                    table_name=table_name,
                    view_table_name=view_name,
                    data_dict=data_dict,
                    data_dict_compare=compare_dict,
                    )
        return row