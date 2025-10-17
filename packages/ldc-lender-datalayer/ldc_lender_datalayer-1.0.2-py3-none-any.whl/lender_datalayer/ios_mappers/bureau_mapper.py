"""
Bureau Mapper using BaseDataLayer architecture
Converts the old bureau_mapper.py to use the new data layer pattern
"""

from ..base_datalayer import BaseDataLayer


class BureauMapper(BaseDataLayer):
    """
    Bureau Mapper using BaseDataLayer for database operations
    Handles CRIF (Credit Information Bureau) data operations
    """

    def __init__(self, db_alias="default"):
        super().__init__(db_alias)

    def get_entity_name(self):
        """Return the entity name this mapper handles"""
        return "IOS_BUREAU"

    @staticmethod
    def insert_crif_data(columns_and_keys):
        sql = """
                INSERT INTO lendenapp_thirdparty_crif_logs(user_id, 
                user_source_group_id, report_id, inquiry_id, status, created_date, updated_date)
                VALUES (%(user_id)s, %(user_source_group_id)s,
                  %(report_id)s, %(inquiry_id)s,  %(status)s, now(), now())
               """

        return BureauMapper().execute_sql(sql=sql, params=columns_and_keys)

    @staticmethod
    def update_crif_data(columns_and_keys):
        sql = """
                UPDATE lendenapp_thirdparty_crif_logs SET pan = %(pan)s, name = %(name)s, 
                dob = %(dob)s, status = %(status)s, updated_date = now()
                WHERE report_id = %(report_id)s and inquiry_id = %(inquiry_id)s
               """
        return BureauMapper().execute_sql(sql=sql, params=columns_and_keys)

    @staticmethod
    def get_initial_user_status(columns_and_keys):
        sql = """
                SELECT  report_id, inquiry_id,crif_report_data,status
                FROM lendenapp_thirdparty_crif_logs
                WHERE user_source_group_id = %(user_source_group_id)s and user_id = %(user_id)s 
                ORDER BY id DESC
                LIMIT 1
               """

        return BureauMapper().sql_execute_fetch_one(
            sql=sql, params=columns_and_keys, to_dict=True
        )
