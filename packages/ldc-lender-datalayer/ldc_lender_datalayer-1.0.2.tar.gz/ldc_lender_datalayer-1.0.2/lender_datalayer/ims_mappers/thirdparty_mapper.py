from django.conf import settings

from ..base_datalayer import BaseDataLayer, DataLayerUtils
from ..common.constants import CashFreeConstants, FMPPInvestmentType, InvestorSource, TransactionStatus, TransactionType

ADJUST_DATE_THRESHOLD = settings.ADJUST_DATE_THRESHOLD
APPSFLYER_DATE_THRESHOLD = settings.APPSFLYER_DATE_THRESHOLD


class ThirdPartyMapper(BaseDataLayer):
    def __init__(self, db_alias="default"):
        super().__init__(db_alias)

    def get_entity_name(self):
        return "IMS_THIRDPARTY"

    @staticmethod
    def insert_into_thirdparty_cashfree(
        action, json_response, status, json_request, user_source_id, user_id
    ):
        sql = """
                    INSERT INTO 
                    lendenapp_thirdpartycashfree 
                    (action, json_response, status, json_request, 
                    user_source_group_id, user_id)
                    VALUES 
                    (%(action)s, %(json_response)s, %(status)s, 
                    %(json_request)s, %(user_source_group_id)s, %(user_id)s)
                    RETURNING id 
                """
        params = {
            "action": action,
            "json_response": json_response,
            "status": status,
            "json_request": json_request,
            "user_source_group_id": user_source_id,
            "user_id": user_id,
        }
        return ThirdPartyMapper().execute_sql(sql, params, return_rows_count=True)

    @staticmethod
    def get_scheme_investment_count(user_id, date_threshold=True):
        sql = """
                SELECT COUNT(*) FROM lendenapp_transaction lt
                WHERE lt.user_source_group_id=%(user_id)s and 
                lt.type = ANY(%(investment_type)s) and 
                lt.status = ANY(%(transaction_status)s)
            """

        params = {
            "user_id": user_id,
            "investment_type": [
                TransactionType.FMPP_INVESTMENT,
                TransactionType.MANUAL_LENDING,
            ],
            "transaction_status": [
                TransactionStatus.COMPLETED,
                TransactionStatus.SUCCESS,
            ],
        }

        if date_threshold:
            sql += " and lt.created_date::DATE > %(adjust_date_threshold)s"
            params["adjust_date_threshold"] = ADJUST_DATE_THRESHOLD

        params = DataLayerUtils().prepare_sql_params(params=params)
        return ThirdPartyMapper().sql_execute_fetch_one(
            sql=sql, params=params, index_result=True
        )

    @staticmethod
    def get_add_money_count(user_source_group_id, date_threshold=True):
        sql = """
                SELECT COUNT(*) FROM lendenapp_transaction lt
                WHERE lt.user_source_group_id=%(user_source_group_id)s and 
                lt.type = %(investment_type)s and 
                lt.status = ANY(%(transaction_status)s)
            """

        params = {
            "user_source_group_id": user_source_group_id,
            "investment_type": TransactionType.ADD_MONEY,
            "transaction_status": [
                TransactionStatus.COMPLETED,
                TransactionStatus.SUCCESS,
            ],
        }

        if date_threshold:
            sql += " and lt.created_date::DATE > %(adjust_date_threshold)s"
            params["adjust_date_threshold"] = ADJUST_DATE_THRESHOLD

        params = DataLayerUtils().prepare_sql_params(params)
        return ThirdPartyMapper().sql_execute_fetch_one(
            sql=sql, params=params, index_result=True
        )

    @staticmethod
    def get_product_type_and_tenure_of_otl(batch_number, scheme_id):
        sql = """
            SELECT CONCAT('AF_Lumpsum_',tenure,'M') AS Tenure, 
            CONCAT('AF_Lumpsum_Repayment_',product_type) AS Repayment
            FROM lendenapp_otl_scheme_tracker 
            WHERE batch_number = %(batch_number)s
            AND scheme_id = %(scheme_id)s
        """

        params = {"batch_number": batch_number, "scheme_id": scheme_id}

        return ThirdPartyMapper().sql_execute_fetch_all(
            sql=sql, params=params, to_dict=True
        )

    @staticmethod
    def get_tp_user_details_from_user_id(user_id):

        sql = """SELECT lc.id as user_pk, lusg.id as user_source_group_id from lendenapp_customuser lc
               inner join lendenapp_user_source_group lusg on lusg.user_id = lc.id
               where lc.user_id = %(user_id)s and lusg.source_id = 7"""
        params = {"user_id": user_id}
        return ThirdPartyMapper().sql_execute_fetch_all(
            sql=sql, params=params, to_dict=True
        )

    @staticmethod
    def get_otl_scheme_investment_count(user_id, date_threshold=True):
        sql = """
                SELECT count(*) from lendenapp_schemeinfo ls
                WHERE ls.user_source_group_id = %(user_id)s 
                AND ls.investment_type = %(investment_type)s
                AND ls.status = ANY(%(status)s)
            """

        params = {
            "user_id": user_id,
            "investment_type": FMPPInvestmentType.ONE_TIME_LENDING,
            "status": [TransactionStatus.COMPLETED, TransactionStatus.SUCCESS],
        }

        if date_threshold:
            sql += " and ls.created_date::DATE > %(adjust_date_threshold)s"
            params["adjust_date_threshold"] = ADJUST_DATE_THRESHOLD

        params = DataLayerUtils().prepare_sql_params(params)
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
        return ThirdPartyMapper().execute_sql(sql=sql, params=params)

    @staticmethod
    def store_request_log(params):
        sql = """
                INSERT INTO lendenapp_thirdparty_event_logs(source, data,
                data_type, status_code, created_dtm, user_id_pk)
                VALUES(%(source)s, %(data)s, %(data_type)s,
                  %(status_code)s, NOW(), %(user_id_pk)s)
            """
        return ThirdPartyMapper().execute_sql(sql=sql, params=params)

    @staticmethod
    def get_investor_from_device_id(device_id):
        query = "select id from lendenapp_customuser where device_id = %(device_id)s order by id desc limit 1"
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
    def get_device_type_from_user_source_id(user_source_id):
        query = """
            select comment from lendenapp_applicationinfo la 
            where user_source_group_id = %(user_source_id)s 
            order by id desc LIMIT 1
        """

        params = {"user_source_id": user_source_id}
        return ThirdPartyMapper().sql_execute_fetch_one(
            sql=query, params=params, index_result=True
        )

    @staticmethod
    def get_bank_detail_from_cashfree(account_number, ifsc_code, user_source_id):
        sql = """select json_request,json_response,status from 
            lendenapp_thirdpartycashfree where 
            user_source_group_id = %(usg_id)s and "action" = %(action)s and 
            status =%(status)s and json_request->>'url' ~ %(check_bank_exits)s 
            and json_response->>'accountStatus' = %(account_status)s 
            order by id desc limit 1
        """

        params = {
            "usg_id": user_source_id,
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
