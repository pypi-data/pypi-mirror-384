"""
S2S Communication Mapper using BaseDataLayer architecture
Converts the old s2s_communication.py to use the new data layer pattern
"""

from ..base_datalayer import BaseDataLayer, DataLayerUtils
from ..common.constants import InvestorSource, TransactionStatus


class S2SCommunicationMapper(BaseDataLayer):
    """
    S2S Communication Mapper using BaseDataLayer for database operations
    Handles S2S Communication service operations
    """

    def __init__(self, db_alias="default"):
        super().__init__(db_alias)

    def get_entity_name(self):
        """Return the entity name this mapper handles"""
        return "S2S_COMMUNICATION"

    def get_live_kyc_data(self, user_source_id, kyc_status):
        sql = """
                SELECT status, event_status, service_type, event_code
                FROM lendenapp_userkyc lu 
                WHERE lu.user_source_group_id = %(user_source_id)s
                AND (event_status = %(kyc_status)s OR status=%(kyc_status)s)
                ORDER by id DESC 
                LIMIT 1
        """
        params = {"user_source_id": user_source_id, "kyc_status": kyc_status}
        return self.sql_execute_fetch_one(sql, params, to_dict=True)

    def get_user_details(self, user_source_id):
        sql = """
            select lc.* from public.lendenapp_customuser lc join 
            lendenapp_task lt on lt.created_by_id = lc.id
            where lt.user_source_group_id= %s;
        """
        return self.sql_execute_fetch_all(sql, [user_source_id], to_dict=True)

    def get_user_details_by_user_id(self, user_id):
        sql = """
            select lc.* from public.lendenapp_customuser lc
            where lc.user_id= %s;
        """
        return self.sql_execute_fetch_all(sql, [user_id], to_dict=True)

    def check_kyc_completed(self, user_id_pk):
        sql = """
                SELECT EXISTS(
                    SELECT 1
                    FROM lendenapp_thirdparty_clevertap_logs, 
                    LATERAL jsonb_array_elements(event_data::jsonb->'d') AS d_obj
                    WHERE d_obj->'evtData'->>'KYC Method' = 'USER_ADDRESS' 
                    AND d_obj->'evtData'->>'Status' = 'SUCCESS' and user_id=%(user_id_pk)s
                )
        """
        params = {"user_id_pk": str(user_id_pk)}
        return self.sql_execute_fetch_one(sql, params, index_result=True)

    def get_source_name(self, user_source_id):
        query = """
            SELECT source_name from lendenapp_source 
            where id=(
                SELECT source_id from lendenapp_user_source_group where id = %s
            )
        """
        return self.sql_execute_fetch_one(query, [user_source_id], index_result=True)

    def get_user_listed_status(self, user_source_id):
        query = """
            SELECT status from lendenapp_account
            WHERE user_source_group_id = %s
        """

        return self.sql_execute_fetch_one(query, [user_source_id], index_result=True)

    def get_account_status(self, user_source_id):
        query = (
            "select status from lendenapp_account where " "user_source_group_id = %s"
        )
        return self.sql_execute_fetch_one(query, [user_source_id], index_result=True)

    def get_referee_data(self, user_id_pk):
        sql = """
                SELECT lc.user_id from lendenapp_customuser lc
                WHERE lc.id = (
                    SELECT lc1.referred_by_id from lendenapp_convertedreferral lc1
                    JOIN lendenapp_user_source_group lusg ON 
                    lc1.referred_by_id = lusg.user_id
                    JOIN lendenapp_source ls ON lusg.source_id = ls.id 
                    WHERE lc1.user_id = %(user_id_pk)s 
                    AND ls.source_name=%(source_name)s
                    ORDER BY lc1.created_date desc
                    LIMIT 1
                ) 
        """

        params = {"user_id_pk": user_id_pk, "source_name": InvestorSource.LDC}
        return self.sql_execute_fetch_one(sql, params, to_dict=True)

    def get_account_status_by_user_id(self, user_id_pk):
        query = """
                SELECT la.status FROM lendenapp_account la JOIN 
                lendenapp_user_source_group lusg ON la.user_source_group_id = lusg.id
                JOIN lendenapp_source ls ON lusg.source_id = ls.id 
                WHERE lusg.user_id=%(user_id_pk)s AND ls.source_name=%(source_name)s;
        """
        params = {"user_id_pk": user_id_pk, "source_name": InvestorSource.LDC}

        return self.sql_execute_fetch_one(query, params=params, to_dict=True)

    def get_device_id(self, user_id):
        query = "select device_id, adid from lendenapp_customuser where id = %(user_id)s order by id desc LIMIT 1"
        params = {"user_id": user_id}
        return self.sql_execute_fetch_all(sql=query, params=params, to_dict=True)

    def additional_referee_data(self, user_id_pk, scheme_creation_types):
        query = """
                SELECT 
                la.status, 
                COALESCE(SUM(lt.amount), 0.0) AS total_amount 
                FROM 
                    lendenapp_account la
                LEFT JOIN 
                    lendenapp_user_source_group lusg 
                    ON lusg.user_id = la.user_id AND lusg.source_id = 7
                LEFT JOIN 
                    lendenapp_transaction lt 
                    ON lusg.id = lt.user_source_group_id 
                    AND lt.type = ANY(%(scheme_creation_transaction_types)s)
                    AND lt.status = %(transaction_status)s
                WHERE 
                    la.user_id = %(user_id_pk)s
                GROUP BY 
                    la.status;
        """
        params = {
            "user_id_pk": user_id_pk,
            "scheme_creation_transaction_types": list(scheme_creation_types),
            "transaction_status": TransactionStatus.COMPLETED,
        }

        params = DataLayerUtils().prepare_sql_params(params)
        return self.sql_execute_fetch_all(query, params=params, to_dict=True)

    def get_account_balance(self, transaction_id):
        query = """
                    select balance 
                    from lendenapp_account where user_source_group_id = 
                    (select user_source_group_id from lendenapp_transaction lt
                    where transaction_id = %s);
                """
        return self.sql_execute_fetch_one(query, [transaction_id], index_result=True)

    def get_otl_scheme_details(self, urn_id, FMPPDB):
        query = f"""
                    SELECT
                    investment_amount as "FMPP Amount",
                    expected_temp_interest_repayment_sum as "Maturity Amount",
                    tis.expected_roi as "ROI",
                    tsm.tenure as "Period",
                    lost.product_type as "Product Type"
                    FROM {FMPPDB}.t_investor_scheme tis
                    INNER JOIN {FMPPDB}.t_scheme_master tsm ON tsm.id = tis.scheme_master_id
                    INNER JOIN lendenapp_otl_scheme_tracker lost ON lost.scheme_id = tis.urn_id AND lost.is_latest
                    WHERE tis.urn_id = %(urn_id)s AND lost.status = %(scheme_status)s;
                """
        params = {"urn_id": urn_id, "scheme_status": TransactionStatus.SUCCESS}
        return self.sql_execute_fetch_all(query, params=params, to_dict=True)

    def get_bulk_lending_scheme_details(self, order_id, FMPPDB):
        query = f"""
                    SELECT max(urn_id) as "Scheme ID",
                    SUM(expected_temp_interest_repayment_sum) as "Maturity Amount", 
                    avg(tis.expected_roi) as "ROI", 
                    max(maturity_date) as "Maturity Date", 
                    max(tsm.tenure) as "Period",
                    EXTRACT(epoch from max(maturity_date))::int as "Maturity Timestamp"
                    FROM {FMPPDB}.t_investor_scheme tis
                    INNER JOIN {FMPPDB}.t_scheme_master tsm ON tsm.id = tis.scheme_master_id
                    WHERE order_id = %(order_id)s;
                """
        params = {"order_id": order_id}
        return self.sql_execute_fetch_all(query, params=params, to_dict=True)

    def get_ml_scheme_details(self, scheme_id, FMPPDB):
        query = f"""
                    SELECT
                    expected_temp_interest_repayment_sum as "Maturity Amount" 
                    FROM {FMPPDB}.t_investor_scheme tis
                    WHERE urn_id = %(scheme_id)s;
                """
        params = {"scheme_id": scheme_id}
        return self.sql_execute_fetch_all(query, params=params, to_dict=True)
