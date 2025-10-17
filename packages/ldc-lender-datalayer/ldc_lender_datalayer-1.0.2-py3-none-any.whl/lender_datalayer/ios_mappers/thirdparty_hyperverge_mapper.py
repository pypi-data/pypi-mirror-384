"""
Third Party Hyperverge Mapper using BaseDataLayer architecture
Converts the old thirdparty_hyperverge_mapper.py to use the new data layer pattern
"""

from ..base_datalayer import BaseDataLayer


class ThirdPartyHypervergeMapper(BaseDataLayer):
    """
    Third Party Hyperverge Mapper using BaseDataLayer for database operations
    Handles Hyperverge third-party service operations
    """

    def __init__(self, db_alias="default"):
        super().__init__(db_alias)

    def get_entity_name(self):
        """Return the entity name this mapper handles"""
        return "IOS_THIRDPARTY_HYPERVERGE"

    @staticmethod
    def insert_into_thirdparty_hyperverge(
        user_id, user_source_group_id, action, json_request, json_response, status
    ):
        sql = """
            INSERT INTO lendenapp_thirdpartydatahyperverge 
            ( action, json_request, json_response, status,user_id, 
            user_source_group_id)
            VALUES 
            (%(action)s,%(json_request)s, %(json_response)s, %(status)s, 
            %(user_id)s, %(user_source_group_id)s)
            RETURNING id"""

        params = {
            "action": action,
            "json_request": json_request,
            "json_response": json_response,
            "status": status,
            "user_id": user_id,
            "user_source_group_id": user_source_group_id,
        }
        return ThirdPartyHypervergeMapper().sql_execute_fetch_one(
            sql, params, index_result=True
        )
