"""
Channel Partner Mapper using BaseDataLayer architecture
Converts the old cp_mapper.py to use the new data layer pattern
"""

import ast

from ..base_datalayer import BaseDataLayer, DataLayerUtils
from ..common.constants import CashFreeConstants, KYCConstant, SearchKey, UserGroup, UserGroupSourceStatus


class CPMapper(BaseDataLayer):
    """
    Channel Partner Mapper using BaseDataLayer for database operations
    Handles channel partner related database operations
    """

    def __init__(self, cp_user_pk=None, db_alias="default"):
        super().__init__(db_alias)
        self.cp_user_pk = cp_user_pk

    def get_entity_name(self):
        """Return the entity name this mapper handles"""
        return "IOS_CHANNEL_PARTNER"

    def get_cp_data_by_pk(self):
        """
        Retrieves partner_id and status from lendenapp_channelpartner table.
        """
        sql = """
            SELECT partner_id, status 
            FROM lendenapp_channelpartner lc 
            WHERE user_id = %(user_pk)s
        """
        params = {"user_pk": self.cp_user_pk}

        return self.sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def get_cp_check_list(column, value, selected_column):
        selected_columns_str = ", ".join(selected_column)

        query = f"""select {selected_columns_str} from lendenapp_task lt
                    where {column} = %(value)s """
        params = {"value": value}
        try:
            result = CPMapper().sql_execute_fetch_one(query, params, index_result=True)
            if isinstance(result, str):
                return ast.literal_eval(result)
            return result
        except Exception:
            return {}

    def get_cp_bank_details(self, purpose=None):
        sql = """
               select ifsc_code ,"number" ,lb2."name" as bank_name, 
               lb."name" as account_holder_name, type  from
                lendenapp_bankaccount lb left join lendenapp_bank lb2 
                on lb.bank_id =lb2.id 
               WHERE user_id = %(user_id)s
               AND lb.is_active = True
               """
        if purpose:
            sql += " AND purpose = %(purpose)s"
        params = {"user_id": self.cp_user_pk, "purpose": purpose}
        return self.sql_execute_fetch_one(sql, params, to_dict=True)

    def get_cp_company_details(self):
        sql = """select name, gst_number, encoded_pan
                from lendenapp_reference 
                where user_id = %(user_id)s
                AND type ='COMPANY_DETAILS'
             """
        param = {"user_id": self.cp_user_pk}
        return self.sql_execute_fetch_one(sql, param, to_dict=True)

    @staticmethod
    def update_data(table_name, data, condition):
        update_data = ", ".join([f"{key} = %({key})s" for key in data.keys()])
        filter_data = " AND ".join([f"{key} = %({key})s" for key in condition.keys()])
        sql = f"""
                           UPDATE {table_name}
                           SET {update_data}
                           WHERE {filter_data};
                      """
        params = {**condition, **data}
        CPMapper().execute_sql(sql, params)

    @staticmethod
    def create_reference_entry(user_data):
        columns = ", ".join(user_data.keys())
        values = ", ".join(["%s"] * len(user_data))

        sql = (
            f"INSERT INTO lendenapp_reference"
            f"({columns}) VALUES ({values}) RETURNING id"
        )

        return CPMapper().sql_execute_fetch_one(
            sql, list(user_data.values()), index_result=True
        )

    @staticmethod
    def get_details_from_partner_id(partner_id):
        sql = """
                select at.key as token, lcg.group_id as group_id 
                from lendenapp_channelpartner lc
                join authtoken_token at 
                on at.user_id = lc.user_id
                join lendenapp_customuser_groups lcg 
                on lcg.customuser_id = lc.user_id
                where lc.partner_id = %(partner_id)s
            """
        params = {"partner_id": partner_id}
        return CPMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    def check_cp_under_mcp(self, cp_user_id, selected_col=["*"]):
        selected_columns_str = ", ".join(selected_col)
        sql = f"""
            select {selected_columns_str} from lendenapp_channelpartner lc 
            join lendenapp_customuser lc2 on lc2.id = lc.user_id
            where lc.referred_by_id = %(user_id)s 
            and lc2.user_id = %(cp_user_id)s
        """
        params = {"user_id": self.cp_user_pk, "cp_user_id": cp_user_id}
        return self.sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def get_cp_details(columns_and_values, selected_column=None):
        if not selected_column:
            selected_column = ["*"]
        selected_columns_str = ", ".join(selected_column)

        conditions = " AND ".join(
            [f"{column} = %s" for column in columns_and_values.keys()]
        )

        sql = f"""select {selected_columns_str} from lendenapp_channelpartner lcp
                join lendenapp_customuser lc on lc.id = lcp.user_id
                where  {conditions}
        """
        param = tuple(columns_and_values.values())
        return CPMapper().sql_execute_fetch_one(sql, param, to_dict=True)

    def get_list_of_cp_under_mcp(self):
        sql = """
            select lc.user_id from lendenapp_convertedreferral lc 
            join lendenapp_customuser_groups lcg on lc.user_id =lcg.customuser_id 
            where lc.referred_by_id = %(user_id)s and lcg.group_id =%(group)s 
        """
        params = {"user_id": self.cp_user_pk, "group": UserGroup.CP}
        rows = self.sql_execute_fetch_all(sql, params, to_dict=False)
        return [row[0] for row in rows if row]

    def fetch_investors_eligible_for_rekyc(self, user_ids, cp_group_name, request_data):
        first_sql = """
            SELECT max(id) id
            FROM lendenapp_userkyctracker lu2
            WHERE lu2.status=%(kyc_status)s
            GROUP BY lu2.user_source_group_id
        """
        params = {"kyc_status": KYCConstant.SUCCESS}
        result = self.sql_execute_fetch_all(first_sql, params, to_dict=True)
        kyc_tracker_ids = [row["id"] for row in result if row]

        sql = """
            SELECT
                lu.user_source_group_id
            FROM lendenapp_user_source_group lusg
            JOIN lendenapp_source ls on ls.id=lusg.source_id
            JOIN lendenapp_channelpartner lc2 on lc2.id=lusg.channel_partner_id
            JOIN lendenapp_customuser lc on lc.id=lusg.user_id
            JOIN lendenapp_userkyctracker lu on lusg.id = lu.user_source_group_id
            WHERE
                lc2.user_id = ANY(%(user_ids)s) AND ls.source_name = %(source)s AND 
                lusg.status=%(user_status)s AND lu.id = ANY(%(kyc_tracker_ids)s)
                AND lu.next_kyc_date - INTERVAL '3 months' < CURRENT_DATE
        """

        params = {
            "user_ids": tuple(user_ids),
            "source": cp_group_name,
            "kyc_status": KYCConstant.SUCCESS,
            "user_status": UserGroupSourceStatus.ACTIVE,
            "kyc_tracker_ids": tuple(kyc_tracker_ids),
        }
        search = request_data.get("search")
        search_query_type = request_data.get("search_query_type")
        if search:
            sql += " AND " + self.dashboard_search_sql_query(
                params, search, search_query_type
            )

        params_update = DataLayerUtils().prepare_sql_params(params)
        user_source_ids = self.sql_execute_fetch_all(sql, params_update, to_dict=True)
        return [row["user_source_group_id"] for row in user_source_ids if row]

    @staticmethod
    def fetch_investor_kyc_details(user_source_ids, data):
        limit = data.get("limit")
        offset = data.get("offset")

        sql = """
            SELECT
                lc.first_name investor_name, lc.encoded_mobile, lc.user_id,
                lc.encoded_email, lu.next_kyc_date, lc2.partner_id,
                (CASE WHEN (lu.next_kyc_date - CURRENT_DATE) < 0 THEN 0
                 ELSE (lu.next_kyc_date - CURRENT_DATE) END) remaining_days,
                (CASE WHEN lu.status = %(success_status)s THEN %(pending_status)s WHEN 
                lu.status=%(initiated_status)s THEN %(inprogress_status)s
                ELSE lu.status END),
                (lc.mnrl_status = 'REJECTED') AS is_mnrl_flagged
            FROM lendenapp_userkyctracker lu
            JOIN lendenapp_user_source_group lusg ON lusg.id=lu.user_source_group_id
            JOIN lendenapp_customuser lc on lc.id=lusg.user_id
            JOIN lendenapp_source ls on ls.id=lusg.source_id
            JOIN lendenapp_channelpartner lc2 on lc2.id=lusg.channel_partner_id
            WHERE lu.user_source_group_id = ANY(%(user_source_ids)s)
                  AND lu.is_latest_kyc=%(is_latest_kyc)s
        """

        params = {
            "is_latest_kyc": True,
            "user_source_ids": tuple(user_source_ids),
            "success_status": KYCConstant.SUCCESS,
            "inprogress_status": KYCConstant.IN_PROGRESS,
            "initiated_status": KYCConstant.INITIATED,
            "pending_status": KYCConstant.PENDING,
        }
        if limit is not None and offset is not None:
            params["limit"] = limit
            params["offset"] = offset
            sql += """ LIMIT %(limit)s OFFSET %(offset)s"""

        params_updated = DataLayerUtils().prepare_sql_params(params)

        return CPMapper().sql_execute_fetch_all(sql, params_updated, to_dict=True)

    def fetch_rekyc_data(
        self,
        user_ids,
        cp_group_name,
        request_data,
        is_mcp_all_investors=False,
        mcp_user_id=None,
    ):
        """
        Single optimized method that combines fetch_investors_eligible_for_rekyc
        and fetch_investor_kyc_details logic into one efficient query with COUNT
        """
        limit = request_data.get("limit")
        offset = request_data.get("offset")
        search = request_data.get("search")
        search_query_type = request_data.get("search_query_type")

        # Build the optimized query with COUNT - consolidated into one CTE
        sql = """
            WITH filtered_data AS (
                SELECT DISTINCT ON (lusg.id) 
                    lusg.id as user_source_group_id,
                    lu.id as kyc_tracker_id,
                    lu.next_kyc_date,
                    lu.status
                FROM lendenapp_user_source_group lusg
                JOIN lendenapp_source ls on ls.id=lusg.source_id
                JOIN lendenapp_channelpartner lc2 on lc2.id=lusg.channel_partner_id
                JOIN lendenapp_customuser lc on lc.id=lusg.user_id
                JOIN lendenapp_userkyctracker lu on lusg.id = lu.user_source_group_id
        """

        # Handle MCP all investors logic directly in SQL
        if is_mcp_all_investors and mcp_user_id:
            sql += """
                JOIN lendenapp_channelpartner mcp_cp on mcp_cp.id=lusg.channel_partner_id
                JOIN lendenapp_customuser_groups lcg on mcp_cp.user_id=lcg.customuser_id
                WHERE mcp_cp.referred_by_id = %(mcp_user_id)s 
                  AND lcg.group_id = %(cp_group)s
                  AND ls.source_name = %(source)s 
                  AND lusg.status=%(user_status)s
                  AND lu.is_latest_kyc = True
                  AND (lu.next_kyc_date IS NULL OR lu.next_kyc_date - INTERVAL '3 months' < CURRENT_DATE)
                  AND (
                      (lu.status = %(success_status)s AND lu.kyc_type = 'LIVE KYC') OR
                      (lu.status = %(success_status)s AND lu.kyc_type = 'MANUAL') OR
                      (lu.status IN (%(success_status)s, %(failed_status)s, %(initiated_status)s, %(inprogress_status)s) AND lu.kyc_type = 'RE KYC')
                  )
            """
        else:
            sql += """
                WHERE lc2.user_id = ANY(%(user_ids)s) 
                  AND ls.source_name = %(source)s 
                  AND lusg.status=%(user_status)s
                  AND lu.is_latest_kyc = True
                  AND (lu.next_kyc_date IS NULL OR lu.next_kyc_date - INTERVAL '3 months' < CURRENT_DATE)
                  AND (
                      (lu.status = %(success_status)s AND lu.kyc_type = 'LIVE KYC') OR
                      (lu.status = %(success_status)s AND lu.kyc_type = 'MANUAL') OR
                      (lu.status IN (%(success_status)s, %(failed_status)s, %(initiated_status)s, %(inprogress_status)s) AND lu.kyc_type = 'RE KYC')
                  )
            """

        params = {
            "user_ids": tuple(user_ids),
            "source": cp_group_name,
            "user_status": UserGroupSourceStatus.ACTIVE,
            "success_status": KYCConstant.SUCCESS,
            "inprogress_status": KYCConstant.IN_PROGRESS,
            "initiated_status": KYCConstant.INITIATED,
            "pending_status": KYCConstant.PENDING,
            "failed_status": KYCConstant.FAILED,
            "mcp_user_id": mcp_user_id,
            "cp_group": UserGroup.CP,
        }

        # Add search conditions to filtered_data CTE
        if search:
            sql += " AND " + self.dashboard_search_sql_query(
                params, search, search_query_type
            )

        sql += """
                ORDER BY lusg.id, lu.id DESC
            ),
            total_count AS (
                SELECT COUNT(*) as total_records
                FROM filtered_data
            )
            SELECT
                lc.first_name investor_name, 
                lc.encoded_mobile, 
                lc.user_id,
                lc.encoded_email, 
                fd.next_kyc_date, 
                lc2.partner_id,
                (CASE WHEN (fd.next_kyc_date - CURRENT_DATE) < 0 THEN 0
                 ELSE (fd.next_kyc_date - CURRENT_DATE) END) remaining_days,
                (CASE WHEN fd.status = %(success_status)s THEN %(pending_status)s 
                 WHEN fd.status=%(initiated_status)s THEN %(inprogress_status)s
                 ELSE fd.status END) as status,
                (lc.mnrl_status = 'REJECTED') AS is_mnrl_flagged,
                tc.total_records
            FROM filtered_data fd
            JOIN lendenapp_user_source_group lusg on lusg.id = fd.user_source_group_id
            JOIN lendenapp_source ls on ls.id=lusg.source_id
            JOIN lendenapp_channelpartner lc2 on lc2.id=lusg.channel_partner_id
            JOIN lendenapp_customuser lc on lc.id=lusg.user_id
            CROSS JOIN total_count tc
        """

        # Add pagination
        if limit is not None and offset is not None:
            params["limit"] = limit
            params["offset"] = offset
            sql += """ LIMIT %(limit)s OFFSET %(offset)s"""

        params_updated = DataLayerUtils().prepare_sql_params(params)
        results = self.sql_execute_fetch_all(sql, params_updated, to_dict=True)

        if not results:
            return {"count": 0, "kyc_data": []}

        # Extract count from first row (same for all rows)
        total_count = results[0]["total_records"]

        # Remove count column from data
        kyc_data = []
        for row in results:
            row_data = dict(row)
            row_data.pop("total_records")
            kyc_data.append(row_data)

        return {"count": total_count, "kyc_data": kyc_data}

    @staticmethod
    def dashboard_search_sql_query(params, search, search_query_type):
        search_query_map = {
            SearchKey.USER_ID: "lc.user_id = %(search)s",
            SearchKey.MOBILE_NO: "lc.encoded_mobile = %(search)s",
            SearchKey.EMAIL: "lc.encoded_email = %(search)s",
        }
        params["search"] = search
        return search_query_map.get(search_query_type, "")

    @staticmethod
    def get_data_from_thirdparty_cashfree(user_id, user_source_id):
        try:
            sql = """
            SELECT
                cu.first_name AS channel_partner_firstname,
                lc.first_name AS user_firstname,
                lc.encoded_email,
                lc.encoded_mobile,
                lc.user_id,
                tpc.json_response,
                tpc.status,
                tpc.comments AS esign_reference_number
            FROM
                lendenapp_user_source_group usg
            JOIN
                lendenapp_channelpartner cp ON cp.id = usg.channel_partner_id
            JOIN
                lendenapp_customuser cu ON cu.id = cp.user_id
            JOIN
                lendenapp_customuser lc ON lc.id = usg.user_id
            LEFT JOIN
                lendenapp_thirdpartycashfree tpc ON tpc.id = (
                    SELECT id
                    FROM lendenapp_thirdpartycashfree
                    WHERE
                        user_id = usg.user_id
                        AND user_source_group_id = usg.id
                        AND action = %(action)s
                    ORDER BY
                        id DESC
                    LIMIT 1
                )
            WHERE
                usg.user_id = %(user_id)s
                AND usg.id = %(user_source_id)s;
            """
            data = CPMapper().sql_execute_fetch_one(
                sql=sql,
                params={
                    "user_id": user_id,
                    "user_source_id": user_source_id,
                    "action": CashFreeConstants.ESIGN,
                },
                to_dict=True,
            )
            return data
        except Exception as e:
            return None
