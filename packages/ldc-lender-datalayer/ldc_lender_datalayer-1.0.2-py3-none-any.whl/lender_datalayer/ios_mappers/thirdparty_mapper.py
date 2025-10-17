"""
Third Party Mapper using BaseDataLayer architecture
Converts the old thirdparty_mapper.py to use the new data layer pattern
"""

from datetime import datetime

from django.conf import settings

from ..base_datalayer import BaseDataLayer
from ..common.constants import CashFreeConstants, InvestorSource

ADJUST_DATE_THRESHOLD = settings.ADJUST_DATE_THRESHOLD
APPSFLYER_DATE_THRESHOLD = settings.APPSFLYER_DATE_THRESHOLD


class ThirdPartyMapper(BaseDataLayer):
    """
    Third Party Mapper using BaseDataLayer for database operations
    Handles third-party service integrations
    """

    def __init__(self, db_alias="default"):
        super().__init__(db_alias)

    def get_entity_name(self):
        """Return the entity name this mapper handles"""
        return "IOS_THIRDPARTY"

    @staticmethod
    def insert_into_thirdparty_cashfree(
        action,
        json_response,
        status,
        json_request,
        user_source_group_id,
        user_id,
        created_date=None,
        updated_date=None,
        comments=None,
    ):
        if created_date is None:
            created_date = datetime.now()
        if updated_date is None:
            updated_date = datetime.now()

        sql = """
                INSERT INTO
                 lendenapp_thirdpartycashfree
                (action, json_request, json_response, status, comments,
                user_id,user_source_group_id, 
                created_date, updated_date)
                VALUES
                (%(action)s,  %(json_request)s, %(json_response)s, %(status)s,
                 %(comments)s, %(user_id)s, %(user_source_group_id)s,
                %(created_date)s, %(updated_date)s) 
                RETURNING id
                """

        params = {
            "action": action,
            "json_request": json_request,
            "json_response": json_response,
            "status": status,
            "comments": comments,
            "user_id": user_id,
            "user_source_group_id": user_source_group_id,
            "created_date": created_date,
            "updated_date": updated_date,
        }
        return ThirdPartyMapper().execute_sql(sql, params, return_rows_count=True)

    @staticmethod
    def get_user_id_from_user_source_group(user_source_id):

        sql = (
            "SELECT user_id from lendenapp_user_source_group "
            "where id = %(user_source_id)s"
        )
        params = {"user_source_id": user_source_id}
        return ThirdPartyMapper().sql_execute_fetch_one(
            sql=sql, params=params, index_result=True
        )

    @staticmethod
    def check_investor_onboading_date(user_id):
        sql = """
                SELECT EXISTS(
                    SELECT * FROM lendenapp_user_source_group where user_id=%(user_id)s and
                    source_id = 7 and
                    date(created_at)>%(adjust_date_threshold)s); 
            """

        params = {"user_id": user_id, "adjust_date_threshold": ADJUST_DATE_THRESHOLD}
        return ThirdPartyMapper().sql_execute_fetch_one(
            sql=sql, params=params, index_result=True
        )

    @staticmethod
    def get_user_source_group_id_by_user_id(user_id):
        sql = """SELECT id as user_source_group_id 
                 FROM lendenapp_user_source_group 
                 WHERE user_id = %(user_id)s AND source_id = 7"""
        params = {"user_id": user_id}
        return ThirdPartyMapper().sql_execute_fetch_one(
            sql=sql, params=params, to_dict=True
        )

    @staticmethod
    def check_appsflyer_investor_onboading_date(user_id):
        sql = """
                    SELECT EXISTS (
                        SELECT 1 
                            FROM lendenapp_user_source_group lusg
                            JOIN lendenapp_source ls 
                                ON lusg.source_id = ls.id
                            WHERE lusg.user_id = %(user_id)s AND ls.source_name = %(source_name)s
                              AND DATE(lusg.created_at) > %(appsflyer_date_threshold)s
                    );
                """
        params = {
            "user_id": user_id,
            "source_name": InvestorSource.LDC,
            "appsflyer_date_threshold": APPSFLYER_DATE_THRESHOLD,
        }
        return ThirdPartyMapper().sql_execute_fetch_one(
            sql=sql, params=params, index_result=True
        )

    @staticmethod
    def store_thirdparty_logs(params):
        sql = """
                INSERT INTO lendenapp_thirdparty_event_logs(source, data,
                created_dtm, data_type, user_id_pk)
                VALUES(%(source)s, %(data)s, 
                  NOW(), %(data_type)s, %(user_id_pk)s)
            """

        ThirdPartyMapper().execute_sql(sql=sql, params=params)

    @staticmethod
    def store_request_log(params):
        sql = """
                INSERT INTO lendenapp_thirdparty_event_logs(source, data, 
                data_type, status_code, created_dtm, user_id_pk)
                VALUES(%(source)s, %(data)s, %(data_type)s,
                  %(status_code)s, NOW(), %(user_id_pk)s)
            """

        ThirdPartyMapper().execute_sql(sql=sql, params=params)

    @staticmethod
    def get_investor_from_device_id(device_id):
        query = "SELECT id from lendenapp_customuser where device_id = %(device_id)s order by id desc LIMIT 1"
        params = {"device_id": device_id}
        return ThirdPartyMapper().sql_execute_fetch_one(
            sql=query, params=params, index_result=True
        )

    @staticmethod
    def get_device_type(user_source_group_id):

        query = "select comment from lendenapp_applicationinfo la where user_source_group_id = %(user_source_group_id)s order by id desc LIMIT 1"
        params = {"user_source_group_id": user_source_group_id}
        return ThirdPartyMapper().sql_execute_fetch_one(
            sql=query, params=params, index_result=True
        )

    @staticmethod
    def store_adid_in_customuser(params, distinct):
        if distinct == "user_id":
            sql = """
                    UPDATE lendenapp_customuser
                    SET adid = %(adid)s
                    WHERE user_id = %(user_id)s
                """
        else:
            sql = """
                    UPDATE lendenapp_customuser
                    SET adid = %(adid)s
                    WHERE device_id = %(device_id)s
                """

        return ThirdPartyMapper().execute_sql(sql=sql, params=params)

    @staticmethod
    def get_bank_detail_from_cashfree(account_number, ifsc_code, user_source_group_id):

        sql = """select json_request,json_response,status from 
            lendenapp_thirdpartycashfree where 
            user_source_group_id =%(user_source_group_id)s and "action" = %(action)s and 
            status =%(status)s and json_request->>'url' ~ %(check_bank_exits)s 
            and json_response->>'accountStatus' = %(account_status)s 
            order by id desc limit 1;
        """
        params = {
            "user_source_group_id": user_source_group_id,
            "action": CashFreeConstants.BANK_ACCOUNT,
            "status": CashFreeConstants.SUCCESS,
            "check_bank_exits": f"&bankAccount={account_number}&ifsc={ifsc_code}",
            "account_status": CashFreeConstants.VALID,
        }
        return ThirdPartyMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def get_device_id(user_id):
        query = """
                SELECT device_id 
                    FROM lendenapp_customuser 
                WHERE id = %(user_id)s 
            """

        params = {"user_id": user_id}
        return ThirdPartyMapper().sql_execute_fetch_one(
            sql=query, params=params, index_result=True
        )

    @staticmethod
    def get_appsflyer_id(user_id, device_type):
        query = """
                SELECT appsflyer_id
                FROM fcm_django_fcmdevice
                WHERE user_id = %(user_id)s
                  AND type = %(device_type)s;
            """

        params = {"user_id": user_id, "device_type": device_type}
        return ThirdPartyMapper().sql_execute_fetch_one(
            sql=query, params=params, index_result=True
        )
