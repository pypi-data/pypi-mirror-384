import ast
from datetime import date

from ..base_datalayer import BaseDataLayer, DataLayerUtils
from ..common.constants import (AccountStatus, AddressType, AMLConstants, CPPaymentTypes, DashboardFilterTypes,
                              DateFormat, FMPPInvestmentType, GroupName, InvestorSource, KYCConstant, NachStatus,
                              OfflinePaymentStatus, ReferenceConstant, SchemeInfoListStatus, SchemeStatus, SearchKey,
                              SortConstant, TransactionStatus, TransactionType, UserGroup, UserGroupSourceStatus)
from ..common.utils.datetime_utils import get_todays_date
from ..common.utils.encryption_utils import EncryptDecryptAES256

encryption = EncryptDecryptAES256()


class CPMapper(BaseDataLayer):
    """
    This class is inherited by CPDashboardMapper
    """

    def __init__(self, cp_user_pk=None, db_alias="default"):
        super().__init__(db_alias)
        self.cp_user_pk = cp_user_pk

    def get_entity_name(self):
        return "IMS_CP"

    def get_cp_id_list_under_mcp(self):
        sql = """
            select lc.user_id from lendenapp_channelpartner lc 
            where lc.referred_by_id = %(user_id)s 
        """
        params = {"user_id": self.cp_user_pk}
        rows = self.sql_execute_fetch_all(sql, params, to_dict=False)
        return [row[0] for row in rows if row]

    def get_investors_count(
        self, cp_group_name, investors_data, exclude_family=False
    ):
        sql = """
                select count(lusg.user_id) from lendenapp_user_source_group lusg
                join lendenapp_channelpartner lc2 on lc2.id=lusg.channel_partner_id
                join lendenapp_customuser lc on lc.id=lusg.user_id
                """
        if exclude_family:
            sql += " and not lc.is_family_member "
        params = {
            "user_id": self.cp_user_pk,
            "active_status": UserGroupSourceStatus.ACTIVE,
        }
        mandate_status = investors_data.get("mandate_status")

        if investors_data.get("all_mandate_data"):
            params["status_search"] = mandate_status
            params["bank_is_active"] = True
            sql += """ join lendenapp_bankaccount lb on lusg.id = lb.user_source_group_id 
                        and lb.is_active = %(bank_is_active)s"""
        if mandate_status:
            if mandate_status == NachStatus.NOT_INITIATED:
                sql += """ and lb.mandate_status is null """
            elif mandate_status in [NachStatus.PENDING, NachStatus.SUCCESS]:
                sql += """ and lb.mandate_status = %(status_search)s"""

        if investors_data.get("all") and cp_group_name == InvestorSource.MCP:
            sql += " where lc2.referred_by_id = %(user_id)s "
        else:
            sql += " where lc2.user_id = %(user_id)s "

        sql += """
                and lusg.status = %(active_status)s
            """

        if investors_data:
            sql = self._apply_search_and_date_filters(sql, params, investors_data)

        return self.sql_execute_fetch_one(sql, params, index_result=True)

    def get_investors_list_for_dropdown(self, cp_group_name, all_cp_filter):
        sql = """
            select lc.user_id, lc.first_name, lc2.partner_id
            from lendenapp_user_source_group lusg
            join lendenapp_channelpartner lc2 on lc2.id=lusg.channel_partner_id
            join lendenapp_customuser lc on lc.id=lusg.user_id
            join lendenapp_account la on la.user_source_group_id = lusg.id
        """
        if all_cp_filter and cp_group_name == InvestorSource.MCP:
            sql += " where lc2.referred_by_id = %(user_id)s "
        else:
            sql += " where lc2.user_id = %(user_id)s "

        sql += """
            and lusg.status = %(active_status)s
            and la.status = %(account_status)s
        """

        params = {
            "user_id": self.cp_user_pk,
            "source": cp_group_name,
            "active_status": UserGroupSourceStatus.ACTIVE,
            "account_status": AccountStatus.LISTED,
        }

        return self.sql_execute_fetch_all(sql, params, to_dict=True)

    @staticmethod
    def check_investor_under_cp_mcp(cp_pk, investor_user_id):
        sql = """
            select lusg.user_id 
            from lendenapp_user_source_group lusg
            join lendenapp_channelpartner lc on lc.id=lusg.channel_partner_id
            join lendenapp_customuser lc2 on lusg.user_id=lc2.id
            where lc.user_id = ANY(%(cp_pk)s)
                and lc2.user_id = %(investor_user_id)s
                and lusg.status = %(active_status)s
        """
        params = {
            "cp_pk": cp_pk,
            "investor_user_id": investor_user_id,
            "active_status": UserGroupSourceStatus.ACTIVE,
        }
        return CPMapper().sql_execute_fetch_one(sql, params, index_result=True)

    def get_investors_list(self, cp_group_name, investors_data):
        sql = """
            SELECT 
                lc3.id cp_id, 
                lc3.user_id cp_user_id, 
                lc3.first_name cp_name,
                lc3.encoded_mobile cp_mobile_number, 
                lc.id, 
                lc.user_id, 
                lc.first_name,
                lc.encoded_mobile as mobile_number, 
                lc.encoded_email as email,
                DATE(lt.created_date) created_date, 
                lc2.type, 
                lc2.partner_id,
                la.balance,
                CASE 
                    WHEN lukt.aml_category = ANY(%(strong_categories)s) THEN 'IN_REVIEW'
                    WHEN lukt.aml_category = 'REJECTED' THEN 'REJECTED'
                    ELSE la.status 
                END AS account_status,
                CASE
                    WHEN lc.mnrl_status = 'REJECTED' THEN True 
                    ELSE False
                END AS is_mnrl_flagged,
                lusg.id user_source_id,
                lt.checklist, 
                la.number, 
                lc.type inv_type,
                EXISTS (
                    SELECT 1 
                    FROM lendenapp_reference lr 
                    WHERE lr.owner_source_id = lusg.id 
                    AND lr.type = 'FAMILY_MEMBER'
                ) as has_family_member
            FROM lendenapp_user_source_group lusg
            JOIN lendenapp_channelpartner lc2 on lc2.id=lusg.channel_partner_id
            JOIN lendenapp_customuser lc  on lc.id=lusg.user_id 
                AND (
                    CASE 
                        WHEN %(family_head_source_id)s IS NULL 
                            THEN NOT lc.is_family_member
                        ELSE lc.is_family_member
                    END
                )
            join lendenapp_customuser lc3  on lc3.id=lc2.user_id 
            join lendenapp_task lt ON lt.user_source_group_id  = lusg.id
            join lendenapp_account la ON la.user_source_group_id  = lusg.id
            left join lendenapp_userkyctracker lukt 
            ON lukt.user_source_group_id = lusg.id and lukt.is_latest_kyc
        """
        if investors_data.get("family_head_source_id"):
            sql += " join lendenapp_reference lr on lr.user_source_group_id = lusg.id "

        if investors_data.get("all") and cp_group_name == InvestorSource.MCP:
            sql += " where lc2.referred_by_id = %(user_id)s "
        else:
            sql += " where lc2.user_id = %(user_id)s "

        sql += " and lusg.status = %(active_status)s "
        if investors_data.get("family_head_source_id"):
            sql += " and lr.owner_source_id = %(family_head_source_id)s "

        params = {
            "user_id": self.cp_user_pk,
            "source": cp_group_name,
            "limit": investors_data.get("limit"),
            "offset": investors_data.get("offset"),
            "active_status": UserGroupSourceStatus.ACTIVE,
            "strong_categories": ["STRONG", "POTENTIAL"],
            "family_head_source_id": investors_data.get("family_head_source_id"),
        }
        sortby = investors_data.get("sortby")
        sortdir = investors_data.get("sortdir")

        if investors_data["is_download_excel"]:
            sql += """ ORDER BY lt.created_date DESC """
        else:
            sql = self._apply_search_and_date_filters(sql, params, investors_data)
            # Apply sorting logic
            if sortby == SortConstant.BALANCE:
                sql += self._sort_or_search_keyword_sql_query(sortdir, "la.balance")
            elif sortby == SortConstant.CREATED_DATE:
                sql += self._sort_or_search_keyword_sql_query(
                    sortdir, "lt.created_date"
                )
            elif sortby not in [SortConstant.FMPP, SortConstant.VALUE_OF_INVESTMENT]:
                sql += """ ORDER BY lt.created_date DESC LIMIT 
                    %(limit)s OFFSET %(offset)s"""

        return self.sql_execute_fetch_all(sql, params, to_dict=True)

    @staticmethod
    def get_investor_investment_amount(investor_user_source_ids):
        extra_details_sql = """
                SELECT 
                    COALESCE(SUM(
                        CASE WHEN lt.type = %(add_money_type)s AND lt.status = %(add_money_status)s THEN amount END
                    ), 0) AS total_funds_added,
                    COALESCE(SUM(
                        CASE WHEN lt.type = %(withdraw_money_type)s AND lt.status = ANY(%(withdraw_money_status)s) THEN amount END
                    ), 0) AS total_funds_withdrawn, 
                    lt.user_source_group_id 
                FROM lendenapp_transaction lt 
                WHERE lt.user_source_group_id = ANY(%(user_source_group_ids)s)
                AND lt.type=ANY (%(type)s)
                GROUP BY lt.user_source_group_id
                """

        params = {
            "type": [TransactionType.ADD_MONEY, TransactionType.WITHDRAW_MONEY],
            "add_money_type": TransactionType.ADD_MONEY,
            "add_money_status": TransactionStatus.SUCCESS,
            "withdraw_money_type": TransactionType.WITHDRAW_MONEY,
            "withdraw_money_status": [
                TransactionStatus.SUCCESS,
                TransactionStatus.SCHEDULED,
                TransactionStatus.PROCESSING,
            ],
            "user_source_group_ids": investor_user_source_ids,
        }

        # Prepare parameters for PostgreSQL array handling
        prepared_params = DataLayerUtils().prepare_sql_params(params)
        return CPMapper().sql_execute_fetch_all(
            extra_details_sql, prepared_params, to_dict=True
        )

    @staticmethod
    def _created_date_sql_query(params, created_from):
        params["created_from"] = created_from
        params["to_date"] = get_todays_date()
        return """ AND Date(lusg.created_at) >= %(created_from)s 
                AND Date(lusg.created_at) <= %(to_date)s """

    @staticmethod
    def _search_keyword_sql_query(params, search):
        params["search"] = "%" + search + "%"
        return """ AND (lc.user_id LIKE %(search)s OR upper(lc.first_name) LIKE upper(%(search)s) 
                OR lc.encoded_email LIKE %(search)s OR lc.encoded_mobile LIKE %(search)s) """

    @staticmethod
    def _sort_or_search_keyword_sql_query(sortdir, sort_by_value):
        if sortdir == SortConstant.DESC:
            return f" ORDER BY {sort_by_value} DESC LIMIT %(limit)s OFFSET %(offset)s"
        else:
            return f" ORDER BY {sort_by_value} ASC LIMIT %(limit)s OFFSET %(offset)s "

    @staticmethod
    def get_cp_data_by_field(user_id):
        sql = f"""
                select partner_id from lendenapp_channelpartner lc 
                where user_id = %(user_id)s
            """

        return CPMapper().sql_execute_fetch_one(sql, {"user_id": user_id}, to_dict=True)

    def get_count_of_payment_links(
        self, from_date, to_date, validated_data, is_mcp=False
    ):
        payment_type = validated_data["type"]

        additional_conditions = """
            AND lp.payment_gateway in ('PMI', 'RAZORPAY')
            AND NOT (lp.status = 'PENDING' AND lp.created_date < NOW() - INTERVAL '7 days')
        """
        additional_joins = ""

        if payment_type == CPPaymentTypes.NACH:
            additional_joins = """
                JOIN lendenapp_transaction lt 
                ON lp.order_id = lt.response_id
            """
            additional_conditions = """ 
                AND lp.payment_gateway = 'NACH'
                AND lp.status = 'COMPLETED'
            """
            if validated_data.get("transaction_status"):
                additional_conditions += """
                    AND lt.status = %(transaction_status)s
                """

        sql = f"""
              SELECT COUNT(*)
              FROM lendenapp_paymentlink lp
              JOIN lendenapp_channelpartner lc2 
              ON lc2.user_id = lp.created_by_id
              {additional_joins}
              """

        if is_mcp:
            # OR condition is required here to show MCP all payments
            # done by himself and all his CPs in single response
            sql += (
                " WHERE (lc2.referred_by_id = %(user_id)s "
                "OR lc2.user_id = %(user_id)s)"
            )
        else:
            sql += " WHERE lc2.user_id = %(user_id)s"

        sql += f"""
              AND lp.created_date > %(from_date)s
              AND lp.created_date <= %(to_date)s
              {additional_conditions}
            """

        params = {
            "from_date": from_date,
            "to_date": to_date,
            "user_id": self.cp_user_pk,
            "transaction_status": validated_data.get("transaction_status"),
        }

        return self.sql_execute_fetch_one(sql, params, index_result=True)

    def get_payment_link_list(self, from_date, to_date, validated_data, is_mcp=False):
        limit = validated_data.get("limit")
        offset = validated_data.get("offset")
        payment_type = validated_data["type"]

        selected_columns = """
                            lp.reference_id, lp.invoice_id, 
                            lp.status as payment_link_status, 
                            lp.payment_gateway, lp.link, 
                            lp.payment_id, lp.order_id, lp.amount, lp.note, 
                            lp.created_date, lp.updated_date, 
                            lc.first_name AS created_for_name, 
                            lc.encoded_mobile AS created_for_mobile_number, 
                            lc.encoded_email AS created_for_email, 
                            lc3.first_name as cp_name, lc2.user_id as cp_user_id,
                            lc2.partner_id, lc.user_id
                            """

        additional_joins = ""
        additional_conditions = """
            AND lp.payment_gateway in ('PMI', 'RAZORPAY')
            AND NOT (lp.status = 'PENDING' AND lp.created_date < NOW() - INTERVAL '7 days')
        """

        if payment_type == CPPaymentTypes.NACH:
            selected_columns += ", lt.status as transaction_status, lt.transaction_id"
            additional_joins = """
                JOIN lendenapp_transaction lt 
                ON lp.order_id = lt.response_id
               """
            additional_conditions = """ 
                AND lp.payment_gateway = 'NACH'
                AND lp.status = 'COMPLETED'
            """

            if validated_data.get("transaction_status"):
                additional_conditions += """
                    AND lt.status = %(transaction_status)s
                """

        sql = f"""
               SELECT 
               {selected_columns}
               FROM lendenapp_paymentlink lp
               JOIN lendenapp_customuser lc ON lc.id = lp.created_for_id 
               JOIN lendenapp_channelpartner lc2 
               ON lc2.user_id = lp.created_by_id 
               JOIN lendenapp_customuser lc3 ON lc3.id = lc2.user_id
               {additional_joins}
            """

        if is_mcp:
            # OR condition is required here to show MCP all payments
            # done by himself and all his CPs in single response
            sql += (
                " WHERE (lc2.referred_by_id = %(user_id)s "
                "OR lc2.user_id = %(user_id)s)"
            )
        else:
            sql += " WHERE lc2.user_id = %(user_id)s"

        sql += f"""
                 AND lp.created_date > %(from_date)s
                 AND lp.created_date <= %(to_date)s
                 {additional_conditions}
               """

        params = {
            "user_id": self.cp_user_pk,
            "from_date": from_date,
            "to_date": to_date,
            "limit": limit,
            "offset": offset,
            "transaction_status": validated_data.get("transaction_status"),
        }

        sql += "ORDER BY lp.created_date DESC LIMIT %(limit)s offset %(offset)s"

        return self.sql_execute_fetch_all(sql, params, to_dict=True)

    def get_cp_count_under_mcp(self, validated_data):

        access_cp_sql = """SELECT COUNT(*) FROM lendenapp_channelpartner lcp 
               INNER JOIN lendenapp_customuser lc ON lc.id = lcp.user_id
               INNER JOIN lendenapp_customuser_groups lcg ON lcg.customuser_id = lcp.user_id
               WHERE lcp.referred_by_id=%(user_id)s and lcg.group_id = %(group)s
            """
        params = {"user_id": self.cp_user_pk, "group": UserGroup.CP}

        created_from_date = validated_data.get("created_from_date")
        search_query = validated_data.get("search_query")

        if search_query and ("@" in search_query or search_query.isdigit()):
            search_query = encryption.encrypt_data(search_query, encrypt=False)

        if created_from_date and search_query:
            access_cp_sql += self.filter_created_date_sql(params, created_from_date)
            access_cp_sql += self._search_keyword_sql_query(params, search_query)
        elif created_from_date:
            access_cp_sql += self.filter_created_date_sql(params, created_from_date)
        elif search_query:
            access_cp_sql += self._search_keyword_sql_query(params, search_query)

        return self.sql_execute_fetch_one(access_cp_sql, params, index_result=True)

    def get_channel_partner_list(self, validated_data):

        sql = """
                SELECT lcp.id, lcp.type, lc.first_name AS name, 
                lc.encoded_email AS email, lcp.listed_date, 
                DATE(lcp.created_date) AS created_date, 
                lc.encoded_mobile as mobile_number, lc.id AS user_pk,
                lc.user_id, lcp.partner_id, lcp.status account_status,
                CASE
                    WHEN lc.mnrl_status = 'REJECTED' THEN True 
                    ELSE False
                END AS is_mnrl_flagged
                FROM lendenapp_channelpartner lcp 
                INNER JOIN lendenapp_customuser lc ON lc.id = lcp.user_id 
                INNER JOIN lendenapp_customuser_groups lcg ON lcg.customuser_id = lcp.user_id
                WHERE lcp.referred_by_id=%(user_id)s and lcg.group_id=%(group)s
            """

        limit = validated_data.get("limit")
        offset = validated_data.get("offset")
        created_from_date = validated_data.get("created_from_date")
        search_query = validated_data.get("search_query")

        if search_query and ("@" in search_query or search_query.isdigit()):
            search_query = encryption.encrypt_data(search_query, encrypt=False)

        params = {
            "user_id": self.cp_user_pk,
            "group": UserGroup.CP,
            "limit": limit,
            "offset": offset,
        }
        if not validated_data["is_download_excel"]:
            if created_from_date and search_query:
                sql += self.filter_created_date_sql(params, created_from_date)
                sql += self._search_keyword_sql_query(params, search_query)

            elif created_from_date:
                sql += self.filter_created_date_sql(params, created_from_date)

            elif search_query:
                sql += self._search_keyword_sql_query(params, search_query)

        sql += """ 
                GROUP BY lcp.id, lcp.type, lc.first_name, lc.encoded_email, 
                lcp.created_date, lc.encoded_mobile, lc.id, lc.user_id, 
                lcp.listed_date
                ORDER BY created_date DESC
                """
        if limit and offset is not None and not validated_data["is_download_excel"]:
            sql += """ LIMIT %(limit)s OFFSET %(offset)s"""

        return self.sql_execute_fetch_all(sql, params, to_dict=True)

    @staticmethod
    def filter_created_date_sql(params, created_from):
        params["created_from"] = created_from
        params["to_date"] = date.today()
        return " AND Date(lcp.created_date) >= %(created_from)s AND Date(lcp.created_date) <= %(to_date)s"

    @staticmethod
    def fetch_mcp_of_cp(cp_user_pk):
        sql = f"""
                select referred_by_id, lc2.user_id from lendenapp_convertedreferral lc
                join lendenapp_customuser_groups lcg on lcg.customuser_id=lc.referred_by_id
                join lendenapp_customuser lc2 on lc.referred_by_id = lc2.id
                where lcg.group_id={UserGroup.MCP} and lc.user_id=%(cp_user_pk)s
                """
        params = {"cp_user_pk": cp_user_pk}

        return CPMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def fetch_partner_id(cp_user_pk):
        sql = """
            select partner_id from lendenapp_channelpartner lc where 
                user_id=%(cp_user_pk)s
            """

        params = {"cp_user_pk": cp_user_pk}

        return CPMapper().sql_execute_fetch_one(sql, params, to_dict=True)

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

    def get_cp_offline_payment_list(self, from_date, to_date, data, is_mcp):
        limit = data["limit"]
        offset = data["offset"]
        search = data.get("search")
        search_query_type = data.get("search_query_type")

        sql = """
                SELECT  
                    opr.request_id, 
                    opr."comment",
                    opr.amount AS requested_amount, 
                    opr.payment_mode, 
                    opr.deposit_date, 
                    opr.reference_number, 
                    CASE 
                        WHEN opr.status = 'COMPLETED' THEN 'APPROVED' 
                        ELSE opr.status 
                    END AS status,
                    lc.first_name AS inv_name,
                    lc.user_id AS inv_user_id,
                    lc2.first_name AS cp_name,
                    lc2.user_id AS cp_user_id
                FROM lendenapp_offline_payment_request opr
                join lendenapp_channelpartner lc3 on lc3.user_id = opr.requested_by_id 
                JOIN lendenapp_customuser lc ON lc.id = opr.investor_id 
                JOIN lendenapp_customuser lc2 ON lc2.id = lc3.user_id  
                WHERE 
                """

        if is_mcp:
            sql += " (lc3.referred_by_id = %(user_id)s or lc3.user_id = %(user_id)s) "
        else:
            sql += " lc3.user_id = %(user_id)s "

        sql += """
                AND opr.created_date > %(from_date)s 
                AND opr.created_date <= %(to_date)s
                """

        params = {
            "user_id": self.cp_user_pk,
            "from_date": from_date,
            "to_date": to_date,
            "limit": limit,
            "offset": offset,
        }

        search_query_map = {
            SearchKey.USER_ID: " AND lc.user_id = %(search)s",
            SearchKey.MOBILE_NO: " AND lc.encoded_mobile = %(search)s",
        }

        if search:
            params["search"] = search
            sql += search_query_map.get(search_query_type, "")

        sql += """ ORDER BY opr.created_date DESC LIMIT %(limit)s OFFSET %(offset)s"""

        return self.sql_execute_fetch_all(sql, params, to_dict=True)

    @staticmethod
    def fetch_offline_payment_request_data_for_wm(
        limit, offset, wm_id, search=None, wm_status_filter=None, lpm_status_filter=None
    ):

        sql = f"""
        select
          opv.status as wm_status,
          opr.status as request_status, 
          lc2.first_name AS cp_name, 
          lc2.user_id AS cp_id, 
          lc.first_name AS investor_name, 
          lc.user_id AS investor_id, 
          opr.amount AS amount, 
          opr.payment_mode, 
          opr.deposit_date,
          TO_CHAR(opr.created_date, 'DD/MM/YYYY') as created_date,
          TO_CHAR(opr.updated_date, 'DD/MM/YYYY') as closure_date, 
          opr.reference_number, 
          -- Concatenate all bank accounts as 'account_number/ifsc_code' and aggregate as array
          ARRAY_AGG(DISTINCT lb.number || '/' || lb.ifsc_code) AS bank_accounts,
          la.number AS va_number, 
          opv.remark as reason, 
          ARRAY_AGG(ld.file) AS document,
          ls.source_name,
          opr.request_id
        from lendenapp_offline_payment_request opr 
        left join lendenapp_offline_payment_verification opv on opr.id =opv.request_id 
        and opv.verified_by_id = %(user_id)s
        JOIN lendenapp_customuser lc ON lc.id = opr.investor_id 
        LEFT JOIN lendenapp_customuser lc2 ON lc2.id = opr.requested_by_id
        JOIN lendenapp_bankaccount lb 
        ON lb.user_source_group_id = opr.user_source_group_id
        JOIN lendenapp_account la 
        ON la.user_source_group_id = opr.user_source_group_id
        JOIN lendenapp_document ld ON ld.id = ANY(opr.document_id::int[])
        JOIN lendenapp_user_source_group lusg 
        on lusg.id = opr.user_source_group_id
        JOIN lendenapp_source ls on ls.id=lusg.source_id """

        params = {"user_id": wm_id}

        filter_condition = ["lb.is_active = TRUE"]

        if search:
            params["search"] = f"%{search}%"
            filter_condition.append(
                """ (lc.user_id LIKE %(search)s 
                OR upper(lc.first_name) LIKE upper(%(search)s)
                OR lc2.user_id LIKE %(search)s 
                OR upper(lc2.first_name) LIKE upper(%(search)s) 
                OR UPPER(opr.payment_mode) LIKE UPPER(%(search)s) 
                ) """
            )

        if wm_status_filter:
            wm_filter = (
                """ opr.status = %(wm_status_filter)s 
            """
                if wm_status_filter == OfflinePaymentStatus.IN_REVIEW
                else """
             opv.status = %(wm_status_filter)s """
            )

            filter_condition.append(wm_filter)

            params["wm_status_filter"] = wm_status_filter

        if lpm_status_filter:
            filter_condition.append(
                """ opr.status = %(lpm_status_filter)s
            """
            )
            params["lpm_status_filter"] = lpm_status_filter

        if filter_condition:
            sql += " WHERE " + " AND ".join(filter_condition)

        sql += """ GROUP by cp_name, cp_id, investor_name, lc.user_id, 
          amount, payment_mode, deposit_date, reference_number, 
          va_number, 
          opr.status, opv.remark, opr.created_date, opr.request_id, opv.status,
          opr.updated_date, opr.id, ls.source_name
        ORDER BY 
          opr.id DESC """

        if limit and offset is not None:
            params["limit"] = limit
            params["offset"] = offset
            sql += """ LIMIT %(limit)s OFFSET %(offset)s """

        return CPMapper().sql_execute_fetch_all(sql, params, to_dict=True)

    @staticmethod
    def fetch_offline_payment_request_data_for_lpm(
        limit, offset, lpm_id, search=None, lpm_status_filter=None
    ):
        sql = """
            select
              opv.status as verification_status,
              opr.status as request_status, 
              lc2.first_name AS cp_name, 
              lc2.user_id AS cp_id, 
              lc.first_name AS investor_name, 
              lc.user_id AS investor_id, 
              opr.amount AS amount, 
              opr.payment_mode, 
              opr.deposit_date,
              TO_CHAR(opr.created_date, 'DD/MM/YYYY') as created_date,
              TO_CHAR(opr.updated_date, 'DD/MM/YYYY') as closure_date,  
              opr.reference_number, 
              lb.number AS bank_acc_number,
              la.number AS va_number, 
              lb.ifsc_code, 
              opv.remark as reason, 
              ARRAY_AGG(ld.file) AS document,
              ls.source_name,
              opr.request_id
            from lendenapp_offline_payment_request opr 
            join lendenapp_offline_payment_verification opv on opr.id =opv.request_id 
            JOIN lendenapp_customuser lc ON lc.id = opr.investor_id 
            LEFT JOIN lendenapp_customuser lc2 ON lc2.id = opr.requested_by_id
            JOIN lendenapp_bankaccount lb 
            ON lb.user_source_group_id = opr.user_source_group_id
            JOIN lendenapp_account la 
            ON la.user_source_group_id = opr.user_source_group_id
            JOIN lendenapp_document ld ON ld.id = ANY(opr.document_id::int[])
            JOIN lendenapp_user_source_group lusg 
            on lusg.id = opr.user_source_group_id
            JOIN lendenapp_source ls on ls.id=lusg.source_id
            where lb.is_active = TRUE AND ( opr.status = %(request_status)s 
            or opv.verified_by_id  = %(lpm_id)s ) """

        params = {"lpm_id": lpm_id, "request_status": OfflinePaymentStatus.PROCESSING}

        if search:
            params["search"] = f"%{search}%"
            sql += """ AND ( lc.user_id LIKE %(search)s 
                       OR upper(lc.first_name) LIKE upper(%(search)s)
                       OR lc2.user_id LIKE %(search)s 
                       OR upper(lc2.first_name) LIKE upper(%(search)s) 
                       OR UPPER(opr.payment_mode) LIKE UPPER(%(search)s) 
                       ) """
        if lpm_status_filter:
            sql += """
            AND opr.status = %(lpm_status_filter)s
            """
            params["lpm_status_filter"] = lpm_status_filter

        sql += """ GROUP by
              cp_name, cp_id, investor_name, lc.user_id, 
              amount, payment_mode, deposit_date, reference_number, 
              bank_acc_number, va_number, ifsc_code, 
              opr.status, opr.created_date, opr.id, opr.request_id, opv.status, 
              opv.remark, opr.updated_date, ls.source_name
            ORDER BY opr.id DESC """

        if limit and offset is not None:
            params["limit"] = limit
            params["offset"] = offset
            sql += """ LIMIT %(limit)s OFFSET %(offset)s """

        return CPMapper().sql_execute_fetch_all(sql, params, to_dict=True)

    @staticmethod
    def fetch_count_offline_payment_request_for_wm(
        wm_id, search=None, wm_status_filter=None, lpm_status_filter=None
    ):

        sql = """
        select count(distinct opr.request_id)
        from lendenapp_offline_payment_request opr 
        left join lendenapp_offline_payment_verification opv 
        on opv.request_id = opr.id and opv.verified_by_id = %(wm_id)s
        join lendenapp_customuser lc on lc.id=opr.investor_id 
        left join lendenapp_customuser lc2 on lc2.id=opr.requested_by_id  """

        params = {"wm_id": wm_id}

        filter_condition = []

        if search:
            params["search"] = f"%{search}%"
            filter_condition.append(
                """ (lc.user_id LIKE %(search)s 
                        OR upper(lc.first_name) LIKE upper(%(search)s)
                        OR lc2.user_id LIKE %(search)s 
                        OR upper(lc2.first_name) LIKE upper(%(search)s) 
                        OR UPPER(opr.payment_mode) LIKE UPPER(%(search)s) 
                        ) """
            )

        if wm_status_filter:
            wm_filter = (
                """ opr.status = %(wm_status_filter)s 
                    """
                if wm_status_filter == OfflinePaymentStatus.IN_REVIEW
                else """
                     opv.status = %(wm_status_filter)s """
            )

            filter_condition.append(wm_filter)

            params["wm_status_filter"] = wm_status_filter

        if lpm_status_filter:
            filter_condition.append(
                """ opr.status = %(lpm_status_filter)s
                    """
            )
            params["lpm_status_filter"] = lpm_status_filter

        if filter_condition:
            sql += " WHERE " + " AND ".join(filter_condition)

        return CPMapper().sql_execute_fetch_one(sql, params, index_result=True)

    @staticmethod
    def fetch_count_offline_payment_request_for_lpm(
        lpm_id, search=None, lpm_status_filter=None
    ):
        sql = """
            select count(distinct opr.request_id)
            from lendenapp_offline_payment_request opr 
            join lendenapp_offline_payment_verification opv on opv.request_id=opr.id
            join lendenapp_customuser lc on lc.id=opr.investor_id 
            left join lendenapp_customuser lc2 on lc2.id=opr.requested_by_id
            where ( opr.status = %(request_status)s 
            or opv.verified_by_id  = %(lpm_id)s) """

        params = {"lpm_id": lpm_id, "request_status": OfflinePaymentStatus.PROCESSING}

        if search:
            params["search"] = f"%{search}%"
            sql += """ AND (lc.user_id LIKE %(search)s 
                OR upper(lc.first_name) LIKE upper(%(search)s)
                OR lc2.user_id LIKE %(search)s 
                OR upper(lc2.first_name) LIKE upper(%(search)s) 
                OR UPPER(opr.payment_mode) LIKE UPPER(%(search)s) 
                ) """
        if lpm_status_filter:
            sql += """
            AND opr.status = %(lpm_status_filter)s
            """
            params["lpm_status_filter"] = lpm_status_filter
        return CPMapper().sql_execute_fetch_one(sql, params, index_result=True)

    def get_cp_offline_payment_count(self, from_date, to_date, data, is_mcp):
        sql = """
                select count(*)
                from lendenapp_offline_payment_request opr 
                join lendenapp_channelpartner lc on lc.user_id = opr.requested_by_id
                join lendenapp_customuser lc2 on lc2.id = opr.investor_id 
                where
            """

        if is_mcp:
            sql += " (lc.referred_by_id = %(user_id)s or lc.user_id = %(user_id)s)"
        else:
            sql += " lc.user_id = %(user_id)s"

        sql += """
                AND opr.created_date > %(from_date)s 
                AND opr.created_date <= %(to_date)s
                """

        params = {
            "user_id": self.cp_user_pk,
            "from_date": from_date,
            "to_date": to_date,
        }

        search = data.get("search")
        search_query_type = data.get("search_query_type")

        search_query_map = {
            SearchKey.USER_ID: " AND lc2.user_id = %(search)s",
            SearchKey.MOBILE_NO: " AND lc2.encoded_mobile = %(search)s",
        }

        if search:
            params["search"] = search
            sql += search_query_map.get(search_query_type, "")

        return self.sql_execute_fetch_one(sql, params, index_result=True)

    @staticmethod
    def fetch_channel_partner_data(cp_user_id, user_group_id=None):
        sql = f"""
            select lc.id as cp_pk, lc2.partner_id, lcg.group_id, lc2.referred_by_id, 
            lc2.id as cp_user_pk from lendenapp_customuser lc
            join lendenapp_channelpartner lc2 on lc2.user_id = lc.id
            join lendenapp_customuser_groups lcg on lcg.customuser_id = lc.id
            where lc.user_id = %(cp_user_id)s
        """

        params = {"cp_user_id": cp_user_id}

        if user_group_id:
            sql += " and lcg.group_id = %(user_group_id)s "
            params["user_group_id"] = user_group_id

        return CPMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def get_offline_payment_request_details(request_id):
        sql = f"""
               SELECT 
               opr.amount, la.balance, 
               opr.payment_mode document_type,
               opr.reference_number,
               opr.deposit_date, opr.created_date,
               la.number, cp.user_id  cp_user_id,
               cp.first_name cp_name,
               cp.encoded_email cp_email,
               cp.encoded_mobile cp_mobile,
               inv.user_id inv_user_id,
               inv.first_name inv_name,
               inv.id inv_pk, opr.user_source_group_id,
               ls.source_name, cp.id cp_user_pk
               FROM lendenapp_offline_payment_request opr 
               INNER JOIN lendenapp_account la 
               ON la.user_source_group_id = opr.user_source_group_id 
               INNER JOIN lendenapp_customuser inv ON inv.id = opr.investor_id
               LEFT JOIN lendenapp_customuser cp 
               ON cp.id = opr.requested_by_id
               JOIN lendenapp_user_source_group lusg 
               ON lusg.id = opr.user_source_group_id
               JOIN lendenapp_source ls on ls.id=lusg.source_id
               WHERE request_id = %(request_id)s 
            """
        params = {
            "request_id": request_id,
        }
        return CPMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def get_cp_name_from_partner_ids(partner_ids):
        # Convert set to list if needed for psycopg3 compatibility
        if isinstance(partner_ids, set):
            partner_ids = list(partner_ids)

        sql = """
            select lc.first_name, lc2.partner_id 
            from lendenapp_customuser lc
            join lendenapp_channelpartner lc2
            on lc.id = lc2.user_id
            where lc2.partner_id = ANY(%(partner_ids)s)
        """
        params = {"partner_ids": partner_ids}
        params = DataLayerUtils().prepare_sql_params(params)
        return CPMapper().sql_execute_fetch_all(sql, params, to_dict=True)

    def cp_under_mcp(self, cp_user_id):
        sql = f"""
            select lc.partner_id, lc.user_id cp_pk from lendenapp_channelpartner lc 
            join lendenapp_customuser lc2 on lc2.id = lc.user_id
            where lc.referred_by_id = %(referred_by_id)s 
            and lc2.user_id = %(cp_user_id)s
        """
        params = {"referred_by_id": self.cp_user_pk, "cp_user_id": cp_user_id}
        return CPMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def get_cp_data_from_user_source_id(user_source_id):
        sql = f"""
            select lc.user_id as cp_pk, lc.partner_id from lendenapp_user_source_group lusg 
            join lendenapp_channelpartner lc 
            on lc.id = lusg.channel_partner_id 
            where lusg.id = %(user_source_id)s
            """

        return CPMapper().sql_execute_fetch_one(
            sql, {"user_source_id": user_source_id}, to_dict=True
        )

    @staticmethod
    def get_account_blc_by_cp_user_pk(user_pk, filter_type, group_name):
        sql = """
                    select 
                        sum(la.balance)
                    from 
                        lendenapp_account la
                    join 
                        lendenapp_user_source_group lusg 
                    ON 
					    la.user_source_group_id = lusg.id 
					join 
					    lendenapp_channelpartner lc 
					on 
					    lc.id = lusg.channel_partner_id 
                    where
                """
        if group_name == GroupName.MCP:
            filter_map = {
                DashboardFilterTypes.ALL: "(lc.referred_by_id = %(user_pk)s OR lc.user_id = %(user_pk)s)",
                DashboardFilterTypes.ALL_CP: "lc.referred_by_id = %(user_pk)s",
                DashboardFilterTypes.SELF: "lc.user_id = %(user_pk)s",
            }
            sql += filter_map.get(filter_type, "")
        else:
            sql += "lc.user_id = %(user_pk)s"
        params = {"user_pk": user_pk}
        return CPMapper().sql_execute_fetch_one(sql, params, index_result=True) or 0

    @staticmethod
    def get_cp_check_list(created_by_id):
        sql = f"""
                SELECT checklist
                FROM lendenapp_task
                WHERE created_by_id = %(created_by_id)s
               """
        try:
            result = CPMapper().sql_execute_fetch_one(
                    sql, {"created_by_id": created_by_id}, index_result=True
                )
            if isinstance(result, str):
                return ast.literal_eval(result)
            return result

        except Exception:
            return {}

    def fetch_cp_data_with_investors_count(self, data):
        sql = """
            select lc.id, lc.user_id, lc.first_name, lc.encoded_email as email, 
            lc3.user_id as mcp_user_id, lc3.first_name as mcp_name,
            lc.encoded_mobile as mobile_number, lc."type", 
            (lc.created_date + interval '5 hours 30 minutes')::date AS created_date, 
            lc.encoded_pan as pan,lb.number as account_number,lb.ifsc_code,
            ag."name",
            case
                when 
                    lc2.status='PENDING' then 'APPROVE' 
                    else lc2.status 
                end as profile_status,
            lt.checklist completed_steps, 
            (select count(*) from lendenapp_user_source_group lusg2 where channel_partner_id = lc2.id) as investor_count, 
            lr.encoded_email referred_by
            from lendenapp_customuser lc 
            join lendenapp_task lt on lc.id=lt.created_by_id 
            join lendenapp_channelpartner lc2 on lc.id=lc2.user_id 
            join lendenapp_customuser_groups lcg on lcg.customuser_id=lc.id 
            join auth_group ag on ag.id=lcg.group_id 
            left join lendenapp_bankaccount lb on lb.user_id=lc.id 
            left join lendenapp_customuser lc3 on lc3.id = lc2.referred_by_id
            left join lendenapp_reference lr on lr.user_id=lc.id 
            and lr.relation = %(reference_relation)s and lr.type = %(reference_type)s
            where 
        """

        params = {
            "groups": (UserGroup.CP, UserGroup.MCP),
            "reference_relation": ReferenceConstant.RELATION_RM,
            "reference_type": ReferenceConstant.TYPE_RM,
        }

        search = data.get("search")
        search_query_type = data.get("search_query_type")

        if search:
            sql += (
                self.dashboard_search_sql_query(params, search, search_query_type)
                + " and "
            )

        sql += """
            lcg.group_id= ANY(%(groups)s) and lc.is_active
            order by lc.created_date desc
        """

        if not data["is_download"]:
            params["limit"] = data["limit"]
            params["offset"] = data["offset"]
            sql += " LIMIT %(limit)s OFFSET %(offset)s"

        params = DataLayerUtils().prepare_sql_params(params)
        return self.sql_execute_fetch_all(sql, params, to_dict=True)

    def cp_count_as_per_search(self, search, search_query_type=None):
        sql = """
        SELECT count(*) 
            from lendenapp_customuser lc 
            join lendenapp_customuser_groups lcg on lcg.customuser_id=lc.id 
            where lcg.group_id= ANY(%(groups)s) and lc.is_active
        """
        params = {"groups": [UserGroup.CP, UserGroup.MCP]}

        if search:
            sql += " and " + self.dashboard_search_sql_query(
                params, search, search_query_type
            )

        params = DataLayerUtils().prepare_sql_params(params)
        return self.sql_execute_fetch_one(sql, params, index_result=True)

    @staticmethod
    def get_cp_bank_details(user_id):
        sql = f"""
               SELECT EXISTS (
                    SELECT 1 from lendenapp_bankaccount lb 
                   left join lendenapp_bank lb2 on lb.bank_id =lb2.id 
                   WHERE user_id = %(user_id)s AND lb.is_active
                ); 
               """

        return CPMapper().sql_execute_fetch_one(
            sql, {"user_id": user_id}, to_dict=True
        )["exists"]

    @staticmethod
    def get_cp_zoho_details_by_user_id(user_id):
        sql = f"""
                SELECT 
                lc.encoded_email as email,
                lc.encoded_mobile as mobile_number,
                lc.first_name, lc.id , lc.type, 
                la.city, la.state, cp.referred_by_id,
                lr2.gst_number, case when lr2.gst_number is null then 'No' else 'Yes' end as gst_treatment,
                lcg.group_id, b.name bank_name, ba.number, ba.ifsc_code,
                lr.encoded_email as rm_email
                FROM lendenapp_customuser lc 
                JOIN lendenapp_address la ON la.user_id=lc.id
                JOIN lendenapp_channelpartner cp ON lc.id=cp.user_id
                JOIN lendenapp_customuser_groups lcg ON lcg.customuser_id=lc.id 
                JOIN lendenapp_bankaccount ba ON ba.user_id=lc.id
                JOIN lendenapp_bank b ON b.id=ba.bank_id
                LEFT JOIN lendenapp_reference lr ON lr.user_id=lc.id 
                AND lr.relation=%(relation)s AND lr.type=%(reference_type)s
                LEFT JOIN lendenapp_reference lr2 ON lr2.user_id=lc.id 
                AND lr2.type=%(company_type)s  AND lc.type=lr2.relation
                WHERE lc.user_id=%(user_id)s AND la.type=%(type)s;
                """

        params = {
            "user_id": user_id,
            "type": AddressType.COMMUNICATION,
            "relation": ReferenceConstant.RELATION_RM,
            "reference_type": ReferenceConstant.TYPE_RM,
            "company_type": ReferenceConstant.TYPE_COMPANY_DETAILS,
        }

        return CPMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    def get_scheme_status_inv_list(self, investors_data):

        sql = """
                select lc.user_id, 
                lc.encoded_email as email, lc.encoded_mobile as mobile_number,
                CASE 
                    WHEN lsi.investment_type = 'ONE_TIME_LENDING' THEN 'SHORT_TERM_LENDING' 
                    ELSE lsi.investment_type 
                END AS investment_type, 
                lc.first_name, lc2.partner_id,
                lsi.scheme_id, lsi.amount, lsi.tenure, 
                lsi.start_date, lsi.maturity_date, lc3.first_name as cp_name, lc3.user_id as cp_id,
                (lsi.created_date AT TIME ZONE 'Asia/Kolkata')::DATE txn_date,
                CASE
                    WHEN lsi.status IN ('INITIATED', 'EXPIRED') THEN 'PENDING'
                    WHEN lsi.mandate_id IS NULL and lsi.status = %(success_status)s 
                    and lsi.investment_type='AUTO_LENDING' THEN 'PENDING'
                    ELSE lsi.status
                END AS scheme_status,
                CASE
                    WHEN lc.mnrl_status = 'REJECTED' THEN True 
                    ELSE False
                END AS is_mnrl_flagged,
                max(notification_count) notification_count, 
                min(last_notification_dtm) first_notification_dtm, 
                max(last_notification_dtm) latest_notification_dtm
                from lendenapp_user_source_group lusg
                join lendenapp_channelpartner lc2 on lc2.id=lusg.channel_partner_id
                join lendenapp_customuser lc on lc.id=lusg.user_id
                join lendenapp_schemeinfo lsi on lsi.user_source_group_id = lusg.id
                join lendenapp_customuser lc3 on lc2.user_id = lc3.id
                join lendenapp_otl_scheme_tracker lost on lost.scheme_id = lsi.scheme_id
                and lsi.investment_type = ANY(%(investment_type_list)s)
                where 
                """

        if investors_data.get("all"):
            sql += " lc2.referred_by_id = %(user_id)s "
        else:
            sql += " lc2.user_id = %(user_id)s "

        sql += """
                and lusg.status = %(active_status)s
                and lsi.investment_type = %(investment_type)s
                """

        params = {
            "user_id": self.cp_user_pk,
            "active_status": UserGroupSourceStatus.ACTIVE,
            "success_status": SchemeStatus.SUCCESS,
            "limit": investors_data.get("limit"),
            "offset": investors_data.get("offset"),
            "investment_type": investors_data["lending_type"],
            "investment_type_list": [
                FMPPInvestmentType.ONE_TIME_LENDING,
                FMPPInvestmentType.MEDIUM_TERM_LENDING,
            ],
        }

        search = investors_data.get("search")
        search_query_type = investors_data.get("search_query_type")
        from_date = investors_data.get("from_date")
        to_date = investors_data.get("to_date")
        scheme_info_status = investors_data["status"]

        search_query_map = {
            SearchKey.EMAIL: " and lc.encoded_email = %(search)s",
            SearchKey.MOBILE_NO: " and lc.encoded_mobile = %(search)s",
            SearchKey.USER_ID: " and lc.user_id = %(search)s",
        }

        if search:
            params["search"] = search
            sql += search_query_map.get(search_query_type, "")

        if scheme_info_status != SchemeInfoListStatus.ALL:
            if scheme_info_status == SchemeInfoListStatus.SUCCESS:
                params["scheme_info_status"] = SchemeInfoListStatus.SUCCESS
                sql += """
                    and lsi.status = %(scheme_info_status)s 
                """
                if investors_data["lending_type"] == FMPPInvestmentType.AUTO_LENDING:
                    sql += """
                        and lsi.mandate_id is not null
                    """
            elif scheme_info_status == SchemeInfoListStatus.CANCELLED:
                params["scheme_info_status"] = SchemeInfoListStatus.CANCELLED
                sql += """
                    and lsi.status = %(scheme_info_status)s 
                """
            else:
                params["scheme_info_status"] = SchemeStatus.INITIATED
                pending_condition = " lsi.status = %(scheme_info_status)s "
                if investors_data["lending_type"] == FMPPInvestmentType.AUTO_LENDING:
                    pending_condition += " or (lsi.mandate_id is null and lsi.status = %(success_status)s)"

                sql += f"""
                    and ({pending_condition})
                """

        if from_date and to_date:
            params["from_date"] = from_date.strftime(DateFormat.YEAR_MONTH_DAY)
            params["to_date"] = to_date.strftime(DateFormat.YEAR_MONTH_DAY)
            sql += """
                and lsi.created_date::date between %(from_date)s and %(to_date)s 
            """

        sql += """ 
        GROUP BY lc.id, lsi.id, lc2.partner_id, lc3.id
            ORDER BY lsi.created_date DESC """
        if (
            investors_data.get("limit") is not None
            and investors_data.get("offset") is not None
        ):
            sql += """ LIMIT %(limit)s OFFSET %(offset)s """

        return self.sql_execute_fetch_all(sql, params, to_dict=True)

    @staticmethod
    def dashboard_search_sql_query(params, search, search_query_type):
        search_query_map = {
            SearchKey.USER_ID: "lc.user_id = %(search)s",
            SearchKey.MOBILE_NO: "lc.encoded_mobile = %(search)s",
            SearchKey.EMAIL: "lc.encoded_email = %(search)s",
            SearchKey.PAN: "lc.encoded_pan = %(search)s",
        }

        params["search"] = search
        return search_query_map.get(search_query_type, "")

    def get_mandate_lender_count(self, investors_data):
        sql = """
                select count(lusg.user_id) from lendenapp_user_source_group lusg
                join lendenapp_channelpartner lc2 on lc2.id=lusg.channel_partner_id
                join lendenapp_customuser lc on lc.id=lusg.user_id
                join lendenapp_schemeinfo lsi on lsi.user_source_group_id = lusg.id 
                """

        params = {
            "user_id": self.cp_user_pk,
            "active_status": UserGroupSourceStatus.ACTIVE,
            "success_status": SchemeStatus.SUCCESS,
            "cancelled_status": SchemeStatus.CANCELLED,
            "investment_type": investors_data["lending_type"],
        }

        if investors_data.get("all"):
            sql += " where lc2.referred_by_id = %(user_id)s "
        else:
            sql += " where lc2.user_id = %(user_id)s "

        sql += """
                and lusg.status = %(active_status)s
                and lsi.investment_type = %(investment_type)s 
                """

        search = investors_data.get("search")
        search_query_type = investors_data.get("search_query_type")
        from_date = investors_data.get("from_date")
        to_date = investors_data.get("to_date")
        scheme_info_status = investors_data["status"]

        search_query_map = {
            SearchKey.EMAIL: " and lc.encoded_email = %(search)s",
            SearchKey.MOBILE_NO: " and lc.encoded_mobile = %(search)s",
            SearchKey.USER_ID: " and lc.user_id = %(search)s",
        }

        if search:
            params["search"] = search
            sql += search_query_map.get(search_query_type, "")

        if scheme_info_status != SchemeInfoListStatus.ALL:
            if scheme_info_status == SchemeInfoListStatus.SUCCESS:
                params["scheme_info_status"] = SchemeInfoListStatus.SUCCESS
                sql += """
                    and lsi.status = %(scheme_info_status)s 
                """
                if investors_data["lending_type"] == FMPPInvestmentType.AUTO_LENDING:
                    sql += """
                            and lsi.mandate_id is not null
                        """

            elif scheme_info_status == SchemeInfoListStatus.CANCELLED:
                params["scheme_info_status"] = SchemeInfoListStatus.CANCELLED
                sql += """
                    and lsi.status = %(scheme_info_status)s 
                """

            elif scheme_info_status == SchemeInfoListStatus.FAILED:
                params["scheme_info_status"] = SchemeInfoListStatus.FAILED
                sql += """
                    and lsi.status = %(scheme_info_status)s 
                """

            else:
                params["scheme_info_status"] = (
                    SchemeStatus.INITIATED,
                    SchemeStatus.PROCESSING,
                    SchemeStatus.EXPIRED,
                )
                pending_condition = "lsi.status =ANY(%(scheme_info_status)s)"
                if investors_data["lending_type"] == FMPPInvestmentType.AUTO_LENDING:
                    pending_condition += " or lsi.mandate_id is null"

                sql += f"""
                        and ({pending_condition})
                    """

        if from_date and to_date:
            params["from_date"] = from_date.strftime(DateFormat.YEAR_MONTH_DAY)
            params["to_date"] = to_date.strftime(DateFormat.YEAR_MONTH_DAY)
            sql += """
                and lsi.created_date::date between %(from_date)s and %(to_date)s 
            """

        params = DataLayerUtils().prepare_sql_params(params)
        return self.sql_execute_fetch_one(sql, params, index_result=True)

    def get_manual_lending_scheme_status(self, investors_data):
        sql = """
                SELECT lc.first_name, lc.user_id, lc.encoded_email as email,
                lc.encoded_mobile as mobile_number,
                lc3.first_name as cp_name, lc3.user_id as cp_id,
                lost.scheme_id scheme_id,
                (lost.created_date AT TIME ZONE 'Asia/Kolkata')::DATE created_date,
                lost.amount_per_loan amount_per_loan,
                lost.loan_count no_of_selected_loans,
                lost.lending_amount initial_lending_amount,
                lost.investment_type investment_type,
                lc2.partner_id, 
                (lsi.created_date AT TIME ZONE 'Asia/Kolkata')::DATE txn_date,
                CASE
                    WHEN lsi.status = 'SUCCESS' THEN 
                    (lsi.amount/amount_per_loan)
                END AS no_of_approved_loans,
                CASE
                    WHEN lsi.status = 'SUCCESS' THEN lsi.amount
                END AS total_lending_amount,
                CASE
                    WHEN lsi.status in ('SUCCESS', 'CANCELLED', 'FAILED') 
                    THEN lsi.status ELSE 'PENDING'
                END AS status
                FROM
                    lendenapp_otl_scheme_tracker lost
                JOIN
                    lendenapp_schemeinfo lsi ON lsi.scheme_id = lost.scheme_id
                JOIN
                    lendenapp_user_source_group lusg 
                    ON lsi.user_source_group_id = lusg.id
                JOIN
                    lendenapp_channelpartner lc2 
                    ON lc2.id = lusg.channel_partner_id
                JOIN
                    lendenapp_customuser lc ON lc.id = lusg.user_id
                JOIN
                    lendenapp_customuser lc3 ON lc2.user_id = lc3.id
                WHERE
            """

        if investors_data.get("all"):
            sql += " lc2.referred_by_id = %(user_id)s "
        else:
            sql += " lc2.user_id = %(user_id)s "

        sql += """
                AND lsi.investment_type = %(investment_type)s
                AND lost.is_latest = TRUE
            """

        params = {
            "user_id": self.cp_user_pk,
            "limit": investors_data.get("limit"),
            "offset": investors_data.get("offset"),
            "investment_type": FMPPInvestmentType.MANUAL_LENDING,
        }

        search = investors_data.get("search")
        search_query_type = investors_data.get("search_query_type")
        from_date = investors_data.get("from_date")
        to_date = investors_data.get("to_date")
        status = investors_data["status"]

        search_query_map = {
            SearchKey.EMAIL: " AND lc.encoded_email = %(search)s",
            SearchKey.MOBILE_NO: " AND lc.encoded_mobile = %(search)s",
            SearchKey.USER_ID: " AND lc.user_id = %(search)s",
        }

        if search:
            params["search"] = search
            sql += search_query_map.get(search_query_type, "")

        if status != SchemeStatus.ALL:
            if status == SchemeStatus.PENDING:
                params["status"] = (SchemeStatus.INITIATED, SchemeStatus.PROCESSING)
                sql += """
                        and lsi.status =ANY(%(status)s) 
                        """
            else:
                params["status"] = status
                sql += """
                        and lsi.status = %(status)s 
                        """

        if from_date and to_date:
            params["from_date"] = from_date.strftime(DateFormat.YEAR_MONTH_DAY)
            params["to_date"] = to_date.strftime(DateFormat.YEAR_MONTH_DAY)
            sql += """
                    and lost.created_date between %(from_date)s and %(to_date)s 
                """

        sql += """ ORDER BY lost.created_date DESC """
        if (
            investors_data.get("limit") is not None
            and investors_data.get("offset") is not None
        ):
            sql += """ LIMIT %(limit)s OFFSET %(offset)s """

        params = DataLayerUtils().prepare_sql_params(params)
        return self.sql_execute_fetch_all(sql, params, to_dict=True)

    def get_nach_details(self, group_name, user_id, data):
        limit = data.get("limit")
        offset = data.get("offset")

        # Build WHERE clause based on original logic
        where_clauses = []
        params = {"active_status": UserGroupSourceStatus.ACTIVE, "bank_is_active": True}

        # Determine which user_id field to use based on group_name and 'all'
        if data.get("all") and group_name == InvestorSource.MCP:
            where_clauses.append("lc2.referred_by_id = %(user_id)s")
        else:
            where_clauses.append("lc2.user_id = %(user_id)s")
        params["user_id"] = user_id

        where_clauses.append("lusg.status = %(active_status)s")
        where_clauses.append("lb.is_active = %(bank_is_active)s")

        # Mandate status filter
        if data.get("mandate_status"):
            if data["mandate_status"] == NachStatus.NOT_INITIATED:
                where_clauses.append("lb.mandate_status is null")
            else:
                where_clauses.append("lb.mandate_status = %(status_search)s")
            params["status_search"] = data.get("mandate_status")

        # Search filter
        search = data.get("search")
        if search and ("@" in search or search.isdigit()):
            search = encryption.encrypt_data(search, encrypt=False)

        # Compose the WHERE clause
        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        sql = f"""
        WITH user_mandate_status AS (
            SELECT
                lc.user_id,
                lc.first_name,
                lc3.first_name as cp_name,
                lc3.user_id as cp_user_id,
                lc2.partner_id,
                CASE
                    WHEN COUNT(*) = COUNT(CASE
                        WHEN lb.mandate_status IS NULL THEN 1
                        WHEN lm.mandate_type = 'E-NACH' AND lm.mandate_status <> 'SUCCESS' THEN 1
                        WHEN lm.mandate_type = 'PHYSICAL-NACH' AND lm.mandate_status NOT IN ('PENDING', 'SUCCESS') THEN 1
                        ELSE NULL
                    END) THEN true
                    ELSE false
                END AS setup_mandate,
                MAX(COALESCE(lb.mandate_status, 'NOT INITIATED')) as mandate_status,
                MAX(COALESCE(lm.remarks, '')) as remark,
                MAX(COALESCE(lm.mandate_type, '-')) AS mandate_type,
                MAX(COALESCE(lm.max_amount, 0)) AS max_amount,
                COALESCE(TO_CHAR(lm.created_date::DATE, 'DD-MM-YYYY'), '-') AS created_date,
                COALESCE(TO_CHAR(lm.updated_date::DATE, 'DD-MM-YYYY'), '-') AS updated_date
            FROM lendenapp_user_source_group lusg
            JOIN lendenapp_bankaccount lb ON lusg.id = lb.user_source_group_id
            JOIN lendenapp_customuser lc ON lusg.user_id = lc.id
            JOIN lendenapp_channelpartner lc2 ON lusg.channel_partner_id = lc2.id
            JOIN lendenapp_customuser lc3 ON lc2.user_id = lc3.id
            LEFT JOIN lendenapp_mandate lm ON lm.id = lb.mandate_id
            {where_sql}
            GROUP BY lc.user_id, lc.first_name, lc3.first_name, lc3.user_id,
                     lc2.partner_id, lm.created_date::DATE, lm.updated_date::DATE
        )
        SELECT
            cp_name,
            cp_user_id,
            first_name,
            user_id,
            mandate_status,
            partner_id,
            remark,
            mandate_type,
            max_amount,
            setup_mandate,
            created_date,
            updated_date
        FROM user_mandate_status
        """

        # Add search keyword logic (if present and not download_excel)
        if not data.get("is_download_excel") and search:
            # This assumes _search_keyword_sql_query returns a string like " AND ...", and may update params
            sql += self._search_keyword_sql_query(params, search)

        # Add ordering
        if data.get("is_download_excel"):
            sql += " ORDER BY user_id DESC"
        else:
            sql += " ORDER BY user_id DESC"

        # Add limit/offset for pagination
        if limit is not None and offset is not None:
            params["limit"] = limit
            params["offset"] = offset
            sql += " LIMIT %(limit)s OFFSET %(offset)s"

        return self.sql_execute_fetch_all(sql, params, to_dict=True)

    @staticmethod
    def get_pending_aml_data():
        sql = """
        WITH RankedEntries AS (
                SELECT
                    lc.user_id, lc.ucic_code, lc.encoded_pan as pan, 
            lb."number" as account_number, 
            CASE WHEN lcp.status = 'ONBOARDED' THEN 'EXISTING USER'
            ELSE 'NEW USER' END AS account_status,
            la.name_score, la.dob_score, la.pan_score, 
            la.address_score, la.matched_name, la.matched_dob, 
            la.matched_pan, la.matched_address, la.match_status,
            lu.overall_is_pep, lu.aml_category as overall_match_status, 
            lu.aml_tracking_id, entity_source, lu.tracking_id as kyc_tracking_id,
            CASE WHEN lcg.group_id = %(cp_group_id)s THEN %(cp_group)s ELSE %(mcp_group)s END as source,
                    ROW_NUMBER() OVER (
                        PARTITION BY lc.id, la.entity_source
                        ORDER BY la.pan_score DESC, la.name_score DESC, la.id DESC
                    ) AS rn
                FROM lendenapp_userkyctracker lu
        JOIN lendenapp_customuser lc ON lu.user_id = lc.id
        JOIN lendenapp_channelpartner lcp ON lc.id = lcp.user_id
        JOIN lendenapp_customuser_groups lcg ON lcg.customuser_id = lc.id 
        LEFT JOIN lendenapp_bankaccount lb ON lc.id = lb.user_id
        JOIN lendenapp_aml la ON la.user_id = lc.id
            WHERE lcg.group_id = ANY(%(groups)s)
            AND lu.is_latest_kyc
            AND lu.status = %(kyc_status)s
            AND lu.aml_status = %(aml_status)s
            )
            select user_id, ucic_code, pan, account_number, 
            name_score, dob_score, pan_score, 
            address_score, matched_name, matched_dob, 
            matched_pan, matched_address, match_status,
            overall_is_pep, overall_match_status, 
            aml_tracking_id, entity_source, kyc_tracking_id,
            source, account_status
            FROM
                RankedEntries
            WHERE
                rn = 1;
        """

        params = {
            "kyc_status": KYCConstant.SUCCESS,
            "aml_status": AMLConstants.IN_REVIEW,
            "groups": [UserGroup.CP, UserGroup.MCP],
            "cp_group_id": UserGroup.CP,
            "cp_group": InvestorSource.LCP,
            "mcp_group": InvestorSource.MCP,
        }
        params = DataLayerUtils().prepare_sql_params(params)
        return CPMapper().sql_execute_fetch_all(sql, params, to_dict=True)

    @staticmethod
    def get_aml_tracker_data(aml_tracking_id, user_id):
        sql = """
            SELECT lc.encoded_email as email, lc.first_name, 
                lc.encoded_mobile as mobile_number, lc.type,
                lc.id as user_pk, lu.id, lu.aml_status, lu.aml_category
            FROM lendenapp_userkyctracker lu 
            JOIN lendenapp_customuser lc ON lu.user_id = lc.id
            WHERE lu.aml_tracking_id = %(aml_tracking_id)s 
                AND lu.status = %(status)s 
                AND lu.is_latest_kyc 
                AND lc.user_id = %(user_id)s
        """

        params = {
            "aml_tracking_id": aml_tracking_id,
            "status": KYCConstant.SUCCESS,
            "user_id": user_id,
        }
        return CPMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    def get_kyc_tracker_data(self, cp_id):
        sql = """
            select tracking_id, aml_category from lendenapp_userkyctracker
            where user_id = %(user_id)s 
            and status =%(status)s and is_latest_kyc
            """

        params = {"user_id": cp_id, "status": KYCConstant.SUCCESS}

        return self.sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def fetch_cp_user_details(columns_and_values, selected_columns):

        conditions = " AND ".join(
            [f"{column} = %s" for column in columns_and_values.keys()]
        )

        selected_columns_str = ", ".join(selected_columns)

        sql = f"""
            SELECT {selected_columns_str}
            FROM lendenapp_customuser lc
            JOIN lendenapp_channelpartner lcp 
            ON lc.id = lcp.user_id
            WHERE {conditions}
        """

        params = tuple(columns_and_values.values())

        return CPMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    def get_cp_staff_data(self, data=None, order_by=False):
        if not data:
            data = {}
        sql = """ 
                select lc.first_name, lc.encoded_mobile, lc.encoded_email, 
                lcs.has_edit_access, lcs.is_active, lc.user_id, 
                lc.id as staff_pk
                from 
                lendenapp_cp_staff lcs
                join lendenapp_customuser lc
                    on lc.id = lcs.user_id
                where lcs.cp_id = %(cp_id)s
            """
        params = {"cp_id": self.cp_user_pk}

        if data.get("staff_id"):
            sql += """
             and lc.user_id = %(user_id)s
            """
            params["user_id"] = data["staff_id"]

            return self.sql_execute_fetch_one(sql, params, to_dict=True)

        if order_by:
            sql += """
                order by lcs.id desc 
            """

        # Add limit and offset if provided
        if data.get("limit") is not None and data.get("offset") is not None:
            params["limit"] = data["limit"]
            params["offset"] = data["offset"]
            sql += """
                    LIMIT %(limit)s
                    OFFSET %(offset)s
                """

        return self.sql_execute_fetch_all(sql, params, to_dict=True)

    def get_cp_staff_performed_action_data(self, limit, offset):
        sql = f"""
            WITH staff_actions AS (
                SELECT 
                    lc.first_name as cp_name, 
                    lc.user_id as cp_user_id, 
                    lc2.first_name as staff_name, 
                    lc2.user_id as staff_user_id,
                    lcsl.activity, 
                    lc3.first_name as user_name, 
                    lc3.user_id,
                    CASE 
                        WHEN lcsl.user_source_group_id IS NULL THEN 'CP' 
                        ELSE 'LENDER' 
                    END as source,
                    lcsl.created_date,
                    COUNT(*) OVER() as total_count
                FROM lendenapp_cp_staff_log lcsl 
                INNER JOIN lendenapp_customuser lc ON lcsl.owner_cp_id = lc.id
                INNER JOIN lendenapp_customuser lc2 ON lcsl.staff_id = lc2.id
                INNER JOIN lendenapp_customuser lc3 ON lcsl.user_id = lc3.id
                WHERE lcsl.owner_cp_id = %(cp_user_pk)s
                ORDER BY lcsl.created_date DESC, lcsl.id DESC
                LIMIT %(limit)s OFFSET %(offset)s
            )
            SELECT 
                cp_name, cp_user_id, staff_name, staff_user_id,
                activity, user_name, user_id, source, total_count
            FROM staff_actions
        """

        params = {"cp_user_pk": self.cp_user_pk, "limit": limit, "offset": offset}

        return self.sql_execute_fetch_all(sql, params, to_dict=True)

    def _apply_search_and_date_filters(self, sql, params, investors_data):
        """Helper function to apply search and date filters to SQL query"""
        search = investors_data.get("search")

        if search and ("@" in search or search.isdigit()):
            search = encryption.encrypt_data(search, encrypt=False)

        created_from_date = investors_data.get("created_from_date")

        if created_from_date and search:
            sql += self._created_date_sql_query(params, created_from_date)
            sql += self._search_keyword_sql_query(params, search)
        elif created_from_date:
            sql += self._created_date_sql_query(params, created_from_date)
        elif search:
            sql += self._search_keyword_sql_query(params, search)

        return sql
