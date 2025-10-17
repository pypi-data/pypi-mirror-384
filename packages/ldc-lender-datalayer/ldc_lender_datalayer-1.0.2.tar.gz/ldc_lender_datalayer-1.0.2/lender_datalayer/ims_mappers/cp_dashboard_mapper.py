from collections import defaultdict
from datetime import timedelta

from ..base_datalayer import BaseDataLayer, DataLayerUtils
from ..common.constants import (AccountStatus, DashboardFilterTypes, DashboardInvestorFilter, DateFormat, GroupName,
                              InvestorSource, InvestorSourceId, ReportFilterKey, ReportFilterType, SummaryType,
                              TransactionStatus, TransactionType, UserGroup, UserGroupSourceStatus)


class CPDashboardMapper(BaseDataLayer):
    def __init__(self, from_date = None, to_date = None, filter_type = None, cp_user_pk = None, db_alias="default"):
        super().__init__(db_alias)
        self.from_date = from_date
        self.to_date = to_date
        self.filter_type = filter_type
        self.cp_user_pk = cp_user_pk

    def get_entity_name(self):
        return "IMS_CP_DASHBOARD"

    def get_investors_count_by_month(self, group_name):
        sql = """
                SELECT
                    lusg.created_at,
                    (lc2.user_id, lc.partner_id) as user_id
                from lendenapp_user_source_group lusg
                INNER JOIN lendenapp_channelpartner lc 
                ON lc.id = lusg.channel_partner_id
                INNER JOIN lendenapp_account la 
                ON la.user_source_group_id = lusg.id
                INNER JOIN lendenapp_source ls 
                ON ls.id = lusg.source_id
                INNER JOIN lendenapp_customuser lc2 
                on lc2.id = lusg.user_id
                WHERE 
                    lusg.group_id = %(group_id)s AND la.status = %(status)s
                    AND lusg.created_at::date BETWEEN %(from_date)s AND %(to_date)s
                    AND ls.source_name = ANY(%(source_name)s)
                    AND lusg.status = %(active_status)s
                    AND
            """
        if group_name == GroupName.MCP:
            filter_map = {
                DashboardFilterTypes.ALL: "(lc.referred_by_id = %(user_pk)s OR lc.user_id = %(user_pk)s)",
                DashboardFilterTypes.ALL_CP: "lc.referred_by_id = %(user_pk)s",
                DashboardFilterTypes.SELF: "lc.user_id = %(user_pk)s",
            }
            sql += filter_map.get(self.filter_type, "")
        else:
            sql += "lc.user_id = %(user_pk)s"

        params = {
            "user_pk": self.cp_user_pk,
            "group_id": UserGroup.LENDER,
            "status": AccountStatus.LISTED,
            "from_date": self.from_date,
            "to_date": self.to_date,
            "source_name": [InvestorSource.LCP, InvestorSource.MCP],
            "active_status": UserGroupSourceStatus.ACTIVE,
        }

        # Prepare parameters for PostgreSQL array handling
        prepared_params = DataLayerUtils().prepare_sql_params(params)
        rows = self.sql_execute_fetch_all(sql, prepared_params, to_dict=True)
        investors_by_month = defaultdict(int)
        investor_cp_dict = defaultdict(list)
        for row in rows:
            month = row["created_at"].strftime("%b")
            investors_by_month[month] += 1
            investor_cp_dict[month].append(row["user_id"])

        return investors_by_month, investor_cp_dict

    def get_partner_id_from_user_id(self):
        sql = """
            SELECT 
                partner_id
            FROM
                lendenapp_channelpartner
            WHERE 
                user_id=%(user_id)s
        """
        param = {"user_id": self.cp_user_pk}
        return self.sql_execute_fetch_one(sql, param, index_result=True)

    def check_if_user_is_mcp(self):
        sql = "SELECT EXISTS(SELECT 1 FROM auth_group ag \
                   INNER JOIN lendenapp_customuser_groups lcg ON lcg.group_id = ag.id \
                   WHERE lcg.customuser_id=%s and ag.name=%s)"
        return self.sql_execute_fetch_one(
            sql, [self.cp_user_pk, GroupName.MCP], index_result=True
        )

    def get_total_withdram_money_cp_investor(
        self, filter_type, group_name, cp_user_id=None
    ):
        sql = """ 
            SELECT 
                SUM(amount) AS total_amount,
                    DATE_TRUNC('month', lt.created_date::date) AS month
            FROM lendenapp_transaction lt
            INNER JOIN lendenapp_user_source_group lusg 
            ON lusg.id = lt.user_source_group_id 
            INNER JOIN lendenapp_channelpartner lc 
            ON lc.id=lusg.channel_partner_id
            INNER JOIN lendenapp_customuser lc2 
	        on lc2.id = lc.user_id 
            WHERE 
                lt.status = ANY(%(status_list)s)
                AND lt.created_date 
                BETWEEN %(from_date)s AND %(to_date)s
                AND lt.type = ANY(%(type_list)s)
                AND lusg.source_id = ANY(%(investor_source)s)
                AND lusg.status = %(active_status)s
                AND
        """

        filter_map = {
            DashboardFilterTypes.ALL: "(lc.referred_by_id = %(user_pk)s OR lc.user_id = %(user_pk)s)",
            DashboardFilterTypes.ALL_CP: "lc.referred_by_id = %(user_pk)s",
            DashboardFilterTypes.SELF: "lc.user_id = %(user_pk)s",
            DashboardFilterTypes.CP_USER_ID: "lc2.user_id = %(partner_id)s",
        }
        sql += filter_map.get(filter_type, "")

        sql += """
                    GROUP BY month;        
        """

        params = {
            "user_pk": self.cp_user_pk,
            "type_list": list(TransactionType.WITHDRAWAL_TRANSACTION_TYPE),
            "status_list": [
                TransactionStatus.SUCCESS,
                TransactionStatus.PROCESSING,
                TransactionStatus.SCHEDULED,
            ],
            "from_date": self.from_date,
            "to_date": self.to_date,
            "investor_source": [InvestorSourceId.LCP, InvestorSourceId.MCP],
            "active_status": UserGroupSourceStatus.ACTIVE,
            "partner_id": cp_user_id,
        }

        params = DataLayerUtils().prepare_sql_params(params)

        return self.sql_execute_fetch_all(sql, params, to_dict=True)

    @staticmethod
    def get_inactive_with_zero_aum_investor_ids(cp_ids, cp_group_name):
        sql = """
            select lusg.user_id , lc2.user_id  
            from lendenapp_user_source_group lusg
            join lendenapp_source ls on ls.id=lusg.source_id 
            join lendenapp_channelpartner lc on lc.id=lusg.channel_partner_id
            join lendenapp_customuser lc2 on lc2.id=lusg.user_id 
            join lendenapp_account la on lusg.id=la.user_source_group_id
            left join lendenapp_transaction lt 
            on lt.user_source_group_id = lusg.id  
            and lt.type = ANY(%(transaction_types)s)
            where lusg.group_id = %(investor_group)s
            and lt.id is null 
            and la.status = %(account_status)s
            and lc.user_id = ANY(%(referred_by_ids)s)
            and ls.source_name = ANY(%(source)s)
            and lusg.status = %(active_status)s
        """
        params = {
            "referred_by_ids": cp_ids,
            "investor_group": UserGroup.LENDER,
            "account_status": AccountStatus.LISTED,
            "transaction_types": [
                TransactionType.FMPP_INVESTMENT,
                TransactionType.MANUAL_LENDING,
                TransactionType.AUTO_LENDING,
            ],
            "source": cp_group_name,
            "active_status": UserGroupSourceStatus.ACTIVE,
        }

        # Prepare parameters for PostgreSQL array handling
        prepared_params = DataLayerUtils().prepare_sql_params(params)
        zero_investment_investors = (
            CPDashboardMapper().sql_execute_fetch_all(
                sql, prepared_params, to_dict=True
            )
            or []
        )
        return [row["user_id"] for row in zero_investment_investors]

    @staticmethod
    def get_investor_ids_based_on_account_status(
        cp_ids,
        cp_group_name,
        account_status=AccountStatus.OPEN,
        from_date=None,
        to_date=None,
    ):
        sql = """
            select lusg.user_id , lc2.user_id,
            (lc2.user_id, partner_id) as investor_cp_id
            from lendenapp_user_source_group lusg
            join lendenapp_source ls on ls.id=lusg.source_id 
            join lendenapp_channelpartner lc on lc.id=lusg.channel_partner_id
            join lendenapp_customuser lc2 on lc2.id=lusg.user_id  
            join lendenapp_account la ON la.user_source_group_id = lusg.id
            WHERE 
            lc.user_id = ANY(%(referred_by_ids)s)
            AND lusg.group_id = %(investor_group)s
            and ls.source_name = ANY(%(source)s)
            AND la.status = %(account_status)s
            and lusg.status = %(active_status)s
        """

        params = {
            "referred_by_ids": cp_ids,
            "investor_group": UserGroup.LENDER,
            "account_status": account_status,
            "source": cp_group_name,
            "active_status": UserGroupSourceStatus.ACTIVE,
        }
        if from_date and to_date:
            sql += """
                AND lusg.created_at::date BETWEEN %(from_date)s AND %(to_date)s
            """
            params["from_date"] = from_date.strftime(DateFormat.YEAR_MONTH_DAY)
            params["to_date"] = to_date.strftime(DateFormat.YEAR_MONTH_DAY)

        # Prepare parameters for PostgreSQL array handling
        prepared_params = DataLayerUtils().prepare_sql_params(params)
        profile_not_completed_investors = (
            CPDashboardMapper().sql_execute_fetch_all(
                sql, prepared_params, to_dict=True
            )
            or []
        )

        investor_id = []
        investor_cp_ids = []

        for row in profile_not_completed_investors:
            investor_id.append(row["user_id"])
            investor_cp_ids.append(row["investor_cp_id"])

        return investor_id, investor_cp_ids

    @staticmethod
    def get_common_investors_detail(
        investor_ids, cp_ids, cp_group_name, summary_type=None
    ):
        sql = """
                select
                lc2.user_id as cp_id,
                lc2.first_name as cp_name,
                lc.listed_date as cp_onboarded_date,
                lc.partner_id,
                lc3.id as investor_pk,
                lc3.user_id as investor_user_id,
                lc3.first_name as investor_name,
                lc3.encoded_mobile as investor_contact_number,
                lc3.encoded_email as investor_email_id,
                la.listed_date as account_opening_date_of_investor,
                la.balance as available_balance_in_wallet,
                la.number as virtual_account_number, 
                lusg.id investor_user_source_id,
                la.status account_status
                from lendenapp_user_source_group lusg
                join lendenapp_source ls on ls.id=lusg.source_id 
                join lendenapp_channelpartner lc on lc.id=lusg.channel_partner_id
                join lendenapp_customuser lc2 on lc2.id = lc.user_id 
                join lendenapp_customuser lc3 on lc3.id=lusg.user_id 
                join lendenapp_account la ON la.user_source_group_id=lusg.id
                WHERE 
                lc3.user_id =ANY(%(investor_ids)s)
                and ls.source_name= ANY(%(source)s)
                and lc.user_id=ANY(%(referred_by_ids)s)
                and lusg.status = %(active_status)s
            """
        params = {
            "investor_ids": investor_ids,
            "referred_by_ids": cp_ids,
            "source": cp_group_name,
            "active_status": UserGroupSourceStatus.ACTIVE,
        }
        if summary_type == SummaryType.CMC:
            params["account_status"] = AccountStatus.LISTED
            sql += """ AND la.status=%(account_status)s """

        return CPDashboardMapper().sql_execute_fetch_all(sql, params, to_dict=True)

    def fetch_transaction_data_by_cp_ids(
        self, transaction_type, cp_pks, status, **kwargs
    ):

        sql = """
            select lc3.first_name as cp_name, lc3.encoded_email as cp_email, 
            lc.first_name as investor_name, lc.encoded_email as email, 
            lt.amount,
            CASE WHEN lt.type = %(redemption_type)s THEN %(scheme_maturity_type)s 
             WHEN lt.type = %(idle_fund_withdrawal)s THEN %(inactivity_withdrawal)s 
             ELSE lt.type END AS type, 
            (CASE WHEN lt.status = 'HOLD' THEN 'PROCESSING' ELSE lt.status END) AS status,
             lt.transaction_id, to_char(lt.date AT TIME ZONE 'Asia/Kolkata', 
                'DD-MM-YYYY') as date, lt.description as description,
            coalesce(lsrd.principal::varchar, '-') as principal, 
            coalesce(lsrd.interest::varchar, '-') as interest,
            to_char(lt.updated_date AT TIME ZONE 'Asia/Kolkata', 
                'DD-MM-YYYY') as updated_date,
            coalesce(lt.utr_no, '-') as UTR
            from lendenapp_transaction lt 
            join lendenapp_user_source_group lusg 
            on lusg.id = lt.user_source_group_id
            join lendenapp_customuser lc on lc.id=lusg.user_id
            join lendenapp_channelpartner lc2 on lc2.id = lusg.channel_partner_id
            join lendenapp_customuser lc3 on lc3.id = lc2.user_id
            left join lendenapp_scheme_repayment_details lsrd 
            on lt.id = lsrd.repayment_id
            where lc2.user_id = ANY(%(cp_pks)s)
        """

        params = {
            "cp_pks": cp_pks,
            "transaction_type": transaction_type,
            "status": status,
            "from_date": f"{self.from_date} 00:00:00",
            "to_date": f"{self.to_date} 23:59:59.999",
            "active_status": UserGroupSourceStatus.ACTIVE,
            "redemption_type": TransactionType.FMPP_REDEMPTION,
            "scheme_maturity_type": ReportFilterKey.SCHEME_MATURITY,
            "idle_fund_withdrawal": TransactionType.IDLE_FUND_WITHDRAWAL,
            "inactivity_withdrawal": ReportFilterKey.INACTIVITY_WITHDRAWAL,
        }

        if kwargs.get("investor_user_id"):
            sql += " and lc.user_id = %(investor_user_id)s "
            params["investor_user_id"] = kwargs["investor_user_id"]

        sql += """
            and lt.type = ANY(%(transaction_type)s)
            and lusg.status = %(active_status)s
            and lt.status = ANY(%(status)s)
            and lt.date >= %(from_date)s AND lt.date <= %(to_date)s
            order by lt.date desc
            """
        if kwargs.get("limit") is not None and kwargs.get("offset") is not None:
            params["limit"] = kwargs["limit"]
            params["offset"] = kwargs["offset"]
            sql += " limit %(limit)s offset %(offset)s"

        # Prepare parameters for PostgreSQL array handling
        return self.sql_execute_fetch_all(sql, params, to_dict=True)

    def get_money_based_on_type_of_cp_investors(self, user_pk, _type, selected_user_id):
        selected_user_id_str = ", ".join(selected_user_id)
        sql = f"""
                SELECT 
                    {selected_user_id_str}
                FROM lendenapp_transaction lt
                INNER JOIN lendenapp_user_source_group lusg 
                on lusg.id = lt.user_source_group_id 
                INNER JOIN lendenapp_source ls on lusg.source_id = ls.id  
                INNER JOIN lendenapp_channelpartner lc 
                on lc.id = lusg.channel_partner_id        
                INNER JOIN lendenapp_customuser lc2 on lc2.id = lusg.user_id
                WHERE 
                    lt.status =ANY(%(status_list)s)
                    AND ls.source_name =ANY(%(source_name)s) 
                    AND lt.created_date >= %(from_date)s 
                    AND lt.created_date < %(to_date)s 
                    AND (lc.referred_by_id = %(user_pk)s  OR lc.user_id = %(user_pk)s)
                    AND lt.type= ANY(%(type)s)
                    AND lusg.status = %(active_status)s
                        GROUP BY lc2.id, lc.partner_id;
            """
        params = {
            "user_pk": user_pk,
            "status_list": [TransactionStatus.SUCCESS, TransactionStatus.COMPLETED],
            "from_date": self.from_date,
            "to_date": self.to_date,
            "source_name": [InvestorSource.LCP, InvestorSource.MCP],
            "active_status": UserGroupSourceStatus.ACTIVE,
            "type": _type,
        }
        if _type in [TransactionType.ADD_MONEY, TransactionType.FMPP_REDEMPTION]:
            _type = [_type]
        elif _type == TransactionType.WITHDRAW_MONEY:
            _type = TransactionType.WITHDRAWAL_TRANSACTION_TYPE
            params["status_list"] = (
                TransactionStatus.SUCCESS,
                TransactionStatus.SCHEDULED,
                TransactionStatus.PROCESSING,
            )

        params["type"] = tuple(_type)
        params = DataLayerUtils().prepare_sql_params(params)
        return self.sql_execute_fetch_all(sql, params, to_dict=True)

    @staticmethod
    def fetch_untilized_funds_of_cp_investors(cp_pk, source_name, filter_type):
        sql = """
            select
                lc2.user_id as cp_id,
                lc2.first_name as cp_name,
                lc.partner_id,
                lc3.id as investor_pk,
                lc3.user_id as investor_user_id,
                lc3.first_name as investor_name,
                lc3.encoded_mobile as investor_contact_number,
                lc3.encoded_email as investor_email_id,
                la.listed_date as account_opening_date_of_investor,
                la.balance as available_balance_in_wallet,
                la.number as virtual_account_number, 
                lusg.id investor_user_source_id,
                la.status account_status
            from lendenapp_account la 
            join lendenapp_user_source_group lusg 
            on lusg.id=la.user_source_group_id 
            join lendenapp_source ls on ls.id=lusg.source_id 
            join lendenapp_channelpartner lc on lc.id = lusg.channel_partner_id 
            join lendenapp_customuser lc2 on lc.user_id = lc2.id 
            join lendenapp_customuser lc3 on lc3.id = lusg.user_id 
            where la.balance>0 
            and la.status = %(account_status)s and 
            lusg.status = %(active_status)s
            and 
        """
        if source_name == GroupName.MCP:
            filter_map = {
                DashboardFilterTypes.ALL: "(lc.referred_by_id = %(cp_pk)s OR lc.user_id = %(cp_pk)s)",
                DashboardFilterTypes.ALL_CP: "lc.referred_by_id = %(cp_pk)s",
                DashboardFilterTypes.SELF: "lc.user_id = %(cp_pk)s",
            }
            sql += filter_map.get(filter_type, "")
        else:
            sql += "lc.user_id = %(cp_pk)s"

        params = {
            "cp_pk": cp_pk,
            "account_status": AccountStatus.LISTED,
            "active_status": UserGroupSourceStatus.ACTIVE,
        }

        return CPDashboardMapper().sql_execute_fetch_all(sql, params, to_dict=True)

    @staticmethod
    def fetch_investor_details_on_filter(
        cp_ids, cp_group_name, filter_key=None, investor_partner_ids=None
    ):
        sql = """
            select
            lc2.user_id as cp_id,
            lc2.first_name as cp_name,
            lc.listed_date as cp_onboarded_date,
            lc.partner_id,
            lc3.id as investor_pk,
            lc3.user_id as investor_user_id,
            lc3.first_name as investor_name,
            lc3.encoded_mobile as investor_contact_number,
            lc3.encoded_email as investor_email_id,
            la.listed_date as account_opening_date_of_investor,
            la.balance as available_balance_in_wallet,
            la.number as virtual_account_number, 
            lusg.id investor_user_source_id,
            la.status account_status
            from lendenapp_user_source_group lusg
            join lendenapp_source ls on ls.id=lusg.source_id 
            join lendenapp_channelpartner lc on lc.id=lusg.channel_partner_id
            join lendenapp_customuser lc2 on lc2.id = lc.user_id 
            join lendenapp_customuser lc3 on lc3.id=lusg.user_id 
            join lendenapp_account la ON la.user_source_group_id=lusg.id """

        params = {
            "source": tuple(cp_group_name),
            "active_status": UserGroupSourceStatus.ACTIVE,
        }

        if filter_key and filter_key == DashboardInvestorFilter.INACTIVE_WITH_ZERO_AUM:
            sql += """
            left join lendenapp_transaction lt2 on lt2.user_source_group_id=lusg.id  
            and lt2.type= ANY(%(transaction_types)s) 
            """
            params["transaction_types"] = (
                TransactionType.FMPP_INVESTMENT,
                TransactionType.AUTO_LENDING,
                TransactionType.MANUAL_LENDING,
                TransactionType.SHORT_TERM_LENDING,
            )

        sql += """ WHERE 
            ls.source_name= ANY(%(source)s)
            and lusg.status = %(active_status)s
        """

        if filter_key and filter_key == DashboardInvestorFilter.INACTIVE_WITH_ZERO_AUM:
            params["account_status"] = AccountStatus.LISTED
            params["referred_by_ids"] = tuple(cp_ids)

            sql += """  AND lc.user_id = ANY(%(referred_by_ids)s)
                        AND lt2.id is null
                        AND la.status=%(account_status)s  """

        if filter_key and filter_key == DashboardInvestorFilter.PROFILE_NOT_COMPLETED:
            params["account_status"] = AccountStatus.OPEN
            params["referred_by_ids"] = tuple(cp_ids)

            sql += """  AND la.status=%(account_status)s  
                        AND lc.user_id = ANY(%(referred_by_ids)s)
                   """

        if investor_partner_ids:
            # Build OR conditions for each (user_id, partner_id) pair
            conditions = []
            for i, (user_id, partner_id) in enumerate(investor_partner_ids):
                param_user_key = f"user_id_{i}"
                param_partner_key = f"partner_id_{i}"
                conditions.append(
                    f"(lc3.user_id = %({param_user_key})s AND lc.partner_id = %({param_partner_key})s)"
                )
                params[param_user_key] = user_id
                params[param_partner_key] = partner_id

            if conditions:
                sql += f" AND ({' OR '.join(conditions)})"

        params = DataLayerUtils().prepare_sql_params(params)
        return CPDashboardMapper().sql_execute_fetch_all(sql, params, to_dict=True)

    def cmb_by_user_source_id(self, user_pk):
        sql = """ 
                SELECT 
                    SUM(amount) total_fund,
                    DATE_TRUNC('month', lt.created_date::date) AS month,
                    lt.type
                FROM lendenapp_transaction lt 
                JOIN 
                lendenapp_user_source_group lusg 
                ON lusg.id = lt.user_source_group_id 
                JOIN
                lendenapp_channelpartner lc 
                ON lc.id = lusg.channel_partner_id        
                WHERE 
                    (lc.referred_by_id = %(user_pk)s or lc.user_id = %(user_pk)s)
                    AND lt.created_date >= %(from_date)s
                    AND lt.created_date < %(to_date)s
                    AND lt.type = ANY(%(type)s)
                    AND lt.status = ANY(%(status_list)s)
                GROUP BY month, lt.type;        
        """

        params = {
            "user_pk": user_pk,
            "type": [TransactionType.ADD_MONEY, TransactionType.FMPP_REDEMPTION],
            "status_list": [TransactionStatus.SUCCESS, TransactionStatus.COMPLETED],
            "from_date": self.from_date,
            "to_date": self.to_date,
        }

        # Prepare parameters for PostgreSQL array handling
        prepared_params = DataLayerUtils().prepare_sql_params(params)
        return self.sql_execute_fetch_all(sql, prepared_params, to_dict=True)

    @staticmethod
    def get_total_amount_group_by_type(user_pk, filter_type, group_name):
        sql = f"""
                SELECT 
                    SUM(amount), lt.type
                FROM lendenapp_transaction lt
                JOIN 
                lendenapp_user_source_group lusg 
                ON lusg.id = lt.user_source_group_id 
                JOIN
                lendenapp_channelpartner lc 
                ON lc.id = lusg.channel_partner_id        
                WHERE 
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

        sql += """
                    AND lt.type = ANY(%(types)s)
                    AND lt.status = ANY(%(status_list)s)
                    GROUP BY lt.type;
        """
        params = {
            "user_pk": user_pk,
            "status_list": [
                TransactionStatus.SUCCESS,
                TransactionStatus.COMPLETED,
                TransactionStatus.SCHEDULED,
                TransactionStatus.PROCESSING,
            ],
            "types": [TransactionType.ADD_MONEY, TransactionType.WITHDRAW_MONEY],
        }

        # Prepare parameters for PostgreSQL array handling
        prepared_params = DataLayerUtils().prepare_sql_params(params)
        return CPDashboardMapper().sql_execute_fetch_all(
            sql, prepared_params, to_dict=True
        )

    def fetch_transaction_data(
        self, transaction_type, cp_pks, investor_user_id, status, selected_column
    ):
        selected_column_str = ", ".join(selected_column)

        select_sql = f"""
            select {selected_column_str}
            from lendenapp_transaction lt
            join lendenapp_user_source_group lusg on lusg.id = lt.user_source_group_id
            join lendenapp_channelpartner lc2  on lc2.id = lusg.channel_partner_id 
        """

        where_clause = """
            where lc2.user_id =ANY(%(cp_pks)s) 
        """
        params = {
            "cp_pks": cp_pks,
            "transaction_type": transaction_type,
            "status": status,
            "from_date": f"{self.from_date} 00:00:00",
            "to_date": f"{self.to_date} 23:59:59.999",
            "active_status": UserGroupSourceStatus.ACTIVE,
        }

        if investor_user_id:
            select_sql += " join lendenapp_customuser lc on lc.id = lusg.user_id"
            where_clause += " and lc.user_id = %(investor_user_id)s"
            params["investor_user_id"] = investor_user_id

        where_clause += """
            and lt.type =ANY(%(transaction_type)s) 
            and lusg.status = %(active_status)s
            and lt.status= ANY(%(status)s)
            and lt.date >= %(from_date)s AND lt.date <= %(to_date)s
        """
        sql = select_sql + where_clause
        return self.sql_execute_fetch_one(sql, params, index_result=True)

    def fetch_lenders_and_cp_count(self, cp_partner_id=None):
        sql = f"""
        WITH channelpartner_count AS (
            SELECT COUNT(user_id) AS count
            FROM lendenapp_channelpartner lc
            WHERE """

        if self.filter_type == DashboardFilterTypes.ALL or DashboardFilterTypes.ALL_CP:
            sql += "(lc.referred_by_id = %(user_pk)s OR lc.user_id = %(user_pk)s)"
        elif self.filter_type == DashboardFilterTypes.SELF:
            sql += "lc.user_id = %(user_pk)s"
        else:
            sql += "lc.partner_id = %(cp_partner_id)s"

        sql += """
        ),
        user_source_group_count AS (
            SELECT COUNT(lusg.user_id) AS count
            FROM lendenapp_channelpartner lc
            JOIN lendenapp_user_source_group lusg ON lusg.channel_partner_id = lc.id
            AND lusg.status = %(active)s 
            WHERE """

        if self.filter_type == DashboardFilterTypes.ALL:
            sql += "(lc.referred_by_id = %(user_pk)s OR lc.user_id = %(user_pk)s)"
        elif self.filter_type == DashboardFilterTypes.ALL_CP:
            sql += "lc.referred_by_id = %(user_pk)s"
        elif self.filter_type == DashboardFilterTypes.SELF:
            sql += "lc.user_id = %(user_pk)s"
        else:
            sql += "lc.partner_id = %(cp_partner_id)s"

        sql += """
        )
        SELECT 
            (SELECT count FROM channelpartner_count) AS cp_count,
            (SELECT count FROM user_source_group_count) AS investor_count;
        """
        params = {
            "user_pk": self.cp_user_pk,
            "active": UserGroupSourceStatus.ACTIVE,
            "cp_partner_id": cp_partner_id,
        }
        if cp_partner_id:
            params["cp_partner_id"] = cp_partner_id
        return self.sql_execute_fetch_one(sql, params, to_dict=True)

    def get_cp_lender_data(self, selected_columns=None):
        if not selected_columns:
            selected_columns = ["*"]
        selected_col_str = ",".join(selected_columns)
        sql = f"""
            select {selected_col_str}  
            from lendenapp_user_source_group lusg
            -- join lendenapp_source ls on ls.id = lusg.source_id 
            join lendenapp_channelpartner lc on lc.id = lusg.channel_partner_id
            join lendenapp_customuser lc2 on lc2.id = lusg.user_id 
            join lendenapp_customuser lc3 on lc3.id = lc.user_id 
            where lc.user_id = %(user_id)s
        """
        params = {"user_id": self.cp_user_pk}
        if self.filter_type == ReportFilterType.ALL:
            sql += " or lc.referred_by_id = %(user_id)s"

        return self.sql_execute_fetch_all(sql, params, to_dict=True)

    def fetch_stl_repayment_transfer(
        self, user_pk, filter_type, group_name, report_key, cp_user_id=None
    ):

        # If cp_user_id is provided, convert it to user_pk
        if cp_user_id:
            user_lookup_sql = """
                SELECT id FROM lendenapp_customuser 
                WHERE user_id = %(cp_user_id)s
            """
            user_lookup_result = self.sql_execute_fetch_one(
                user_lookup_sql, {"cp_user_id": cp_user_id}, to_dict=True
            )
            if user_lookup_result:
                user_pk = user_lookup_result["id"]
            else:
                # Return empty data if user not found
                return []

        sql = """
            SELECT 
                lt.created_date::date AS date,
                COALESCE(SUM(lt.amount), 0) AS total_amount,
                COUNT(DISTINCT lt.user_source_group_id) AS unique_groups
            FROM lendenapp_transaction lt
            JOIN lendenapp_user_source_group lusg ON lt.user_source_group_id = lusg.id
            JOIN lendenapp_channelpartner lcp ON lusg.channel_partner_id = lcp.id
            WHERE 
                lt.created_date >= %(start_date)s 
                AND lt.created_date <= %(end_date)s
                AND lt.type = %(repayment_transaction_type)s
                AND lt.status = %(success_status)s
            
        """
        params = {
            "start_date": self.from_date,
            "end_date": f"{self.to_date} 23:59:59.999",
            "repayment_transaction_type": report_key,
            "success_status": TransactionStatus.SUCCESS,
            "user_pk": user_pk,
        }

        filter_sql_map = {
            DashboardFilterTypes.SELF: " AND lcp.user_id = %(user_pk)s",
            DashboardFilterTypes.CP_USER_ID: " AND lcp.user_id = %(user_pk)s",
            DashboardFilterTypes.ALL_CP: "AND lcp.referred_by_id = %(user_pk)s",
            DashboardFilterTypes.ALL: "AND (lcp.user_id = %(user_pk)s OR lcp.referred_by_id = %(user_pk)s)",
        }

        sql += (
            filter_sql_map[filter_type]
            + """
            GROUP BY lt.created_date::date
            ORDER BY date DESC
        """
        )

        result = self.sql_execute_fetch_all(sql, params, to_dict=True)

        date_map = {row["date"]: row for row in result}
        complete_data = []

        for i in range((self.to_date - self.from_date).days + 1):
            current_date = self.to_date - timedelta(days=i)
            if current_date in date_map:
                complete_data.append(date_map[current_date])
            else:
                complete_data.append(
                    {"date": current_date, "total_amount": 0, "unique_groups": 0}
                )

        return complete_data[::-1]
