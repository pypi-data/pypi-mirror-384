"""
IMS Authentication Data Layer Module

This module contains the IMSAuthenticationDataLayer class that provides
all SQL functions used by authentication classes in the ims/common/authentication.py file.

Each SQL query from the original authentication classes has been converted
to a function in this data layer for better organization and reusability.
"""

from ..base_datalayer import BaseDataLayer
from ..common.constants import UserGroup


class IMSAuthenticationDataLayer(BaseDataLayer):
    def __init__(self, db_alias="default"):
        super().__init__(db_alias)

    """
    Data layer for IMS authentication-related database operations.
    Contains all SQL queries used by authentication classes as functions.

    This class inherits from BaseDataLayer and provides:
    - get_ims_user_by_token(): For IMSAuthentication
    - get_multiuser_auth_data(): For MultiUserAuthentication
    - get_multiuser_cp_auth_data(): For MultiUserCPAuthentication
    - get_retail_user_auth_data(): For RetailMultiUserAuthentication
    - get_fmpp_user_data(): For FmppUserAuthentication
    - get_manager_user_data(): For ManagerAuthentication
    - get_pp_dashboard_user_data(): For PPDashboardBaseTokenAuthentication
    - get_retail_user_auth_data_v2(): For RetailMultiUserAuthenticationV2
    - check_investor_under_partner(): For JwtCPInvestorAuthentication
    - check_cp_under_mcp(): For JwtCPInvestorAuthentication
    - get_jwt_cp_mcp_user_data(): For JwtCpMcpAuthentication
    - get_jwt_retail_user_validation(): For JwtRetailMultiUserAuthentication
    """

    def get_entity_name(self):
        """Return the entity name for this data layer."""
        return "IMS_AUTHENTICATION"

    def get_ims_user_by_token(self, key):
        """
        SQL function for IMSAuthentication - Get user by token with account status.

        Original SQL from IMSAuthentication.authenticate()

        Args:
            key: Authentication token key

        Returns:
            Tuple: (user_pk, user_id, account_status, group_id, group_name, token) or None
        """
        sql = """
            SELECT
                att.user_id, lc.user_id, la.status, lcg.group_id group_id, 
                ag.name group_name, att.key
            FROM authtoken_token att 
            INNER JOIN lendenapp_customuser lc on lc.id = att.user_id
            LEFT JOIN lendenapp_account la on la.user_id=lc.id
            LEFT JOIN lendenapp_customuser_groups lcg 
            on lcg.customuser_id=lc.id
            LEFT JOIN auth_group ag on lcg.group_id = ag.id
            WHERE att.key=%s and lc.is_active
        """
        return self.sql_execute_fetch_one(sql, [key])

    def get_multiuser_auth_data(self, token, investor_id, source_name, group_id):
        """
        SQL function for MultiUserAuthentication - Complex multi-user authentication with account status.

        Original SQL from MultiUserAuthentication.authenticate()

        Args:
            token: Authentication token
            investor_id: Investor ID
            source_name: Source name/partner code
            group_id: User group ID

        Returns:
            Tuple: (user_pk, cp_user_pk, user_id, is_active, status, group_id, user_source_id, account_status, user_email) or None
        """
        sql = """
            with cp_investor as (
              with tab as(
                with auth_token_tab as(
                  select 
                    (
                      select user_id from 
                        authtoken_token at where key = %(token)s
                    ) as token_pk, 
                    (
                      select id from lendenapp_customuser lc where user_id = %(investor_id)s
                    ) as investor_pk
                ) 
                select token_pk, investor_pk, investor_pk = token_pk as is_investor_token from auth_token_tab
                where token_pk is not null
              ) 
              select 
                token_pk, investor_pk, is_investor_token,
                (
                  select id from lendenapp_channelpartner lc2 where user_id = token_pk and not is_investor_token
                ) as cp_id 
              from 
                tab
            ) 
            select 
                cp_investor.investor_pk as user_pk, case when cp_id is not null then token_pk end as cp_user_pk, lc.user_id, 
                lc.is_active, lusg.status,lusg.group_id, lusg.id as user_source_id, la.status as account_status,
                lc.encoded_email as user_email
            from 
              cp_investor 
              join lendenapp_customuser lc on lc.id = investor_pk 
              join lendenapp_user_source_group lusg on lusg.user_id = lc.id 
              and case when not cp_investor.is_investor_token then lusg.channel_partner_id = cp_investor.cp_id else true end
              and lusg.group_id = %(group_id)s 
              join lendenapp_source ls on ls.id = lusg.source_id 
              and ls.source_name = %(source_name)s 
              join lendenapp_account la on la.user_source_group_id = lusg.id
        """
        params = {
            "token": token,
            "group_id": group_id,
            "source_name": source_name,
            "investor_id": investor_id,
        }
        return self.sql_execute_fetch_one(sql, params)

    def get_multiuser_cp_auth_data(
        self,
        token,
        partner_id,
        source_name,
        investor_id,
        group_id,
        mcp_group_id,
        lcp_source,
    ):
        """
        SQL function for MultiUserCPAuthentication - Complex CP authentication with referral verification.

        Original SQL from MultiUserCPAuthentication.authenticate()

        Args:
            token: Authentication token
            partner_id: Partner ID
            source_name: Source name
            investor_id: Investor ID
            group_id: User group ID
            mcp_group_id: MCP group ID
            lcp_source: LCP source name

        Returns:
            Tuple: (partner_user_pk, user_source, partner_id, token_partner_id, token_user_pk, user_id, is_active, user_status, task_id, investor_pk, account_status) or None
        """
        sql = """
            WITH referral_verification_tab AS(
              with partner_id_verification_tab as(
                WITH auth_token_tab AS (
                  SELECT 
                    lc3.partner_id AS token_partner_id, 
                    lc3.id AS channel_partner_id ,
                    lc3.user_id as token_pk
                  FROM 
                    authtoken_token at 
                    LEFT JOIN lendenapp_channelpartner lc3 ON lc3.user_id = at.user_id 
                  WHERE 
                    KEY = %(token)s
                ) 
                SELECT 
                  token_pk,	
                  token_partner_id, 
                  channel_partner_id,
                  (
                    SELECT 
                      id 
                    FROM 
                      lendenapp_customuser lc 
                    WHERE 
                      user_id = %(investor_id)s
                  ) AS investor_pk
                FROM 
                  auth_token_tab 
                WHERE 
                  token_pk IS NOT NULL
              )
              select %(source_name)s <> %(lcp_source)s as indirect_mapping, *,
              case when %(source_name)s <> %(lcp_source)s
              then
              coalesce((select true from lendenapp_convertedreferral lc5 
              join lendenapp_customuser_groups lcg on lcg.customuser_id = lc5.referred_by_id
              where lc5.referred_by_id =token_pk and lcg.group_id = %(mcp_group_id)s and lc5.user_id =
              (select user_id from lendenapp_channelpartner lc4 where lc4.partner_id=%(partner_id)s)),false)
              else true end as reference
              from partner_id_verification_tab pivt 
              )
              SELECT 
              lc2.user_id,
              ls.source_name,
              lc2.partner_id,
              referral_verification_tab.token_partner_id,
              token_pk AS token_user_pk, 
              lc.user_id, 
              lc.is_active, 
              lusg.status, 
              lt.id AS task_id,
              investor_pk AS user_pk,
              la.status as account_status
            FROM 
              referral_verification_tab 
              JOIN lendenapp_customuser lc ON lc.id = investor_pk 
              JOIN lendenapp_user_source_group lusg ON lusg.user_id = investor_pk 
              JOIN lendenapp_channelpartner lc2 ON lc2.id = lusg.channel_partner_id
              JOIN lendenapp_task lt ON lt.user_source_group_id = lusg.id 
              JOIN lendenapp_source ls ON ls.id = lusg.source_id 
              JOIN lendenapp_account la ON la.task_id = lt.id
              where ls.source_name = case when referral_verification_tab.indirect_mapping and 
              referral_verification_tab.reference then %(lcp_source)s else %(source_name)s end
              and lc2.partner_id = case when referral_verification_tab.indirect_mapping and 
              referral_verification_tab.reference then %(partner_id)s else referral_verification_tab.token_partner_id end
              and lusg.group_id = %(group_id)s
        """
        params = {
            "token": token,
            "partner_id": partner_id,
            "source_name": source_name,
            "investor_id": investor_id,
            "group_id": group_id,
            "mcp_group_id": mcp_group_id,
            "lcp_source": lcp_source,
        }
        return self.sql_execute_fetch_one(sql, params)

    def get_retail_user_auth_data(
        self, token, source_name, investor_id, partner_id=None
    ):
        """
        SQL function for RetailMultiUserAuthentication - Dynamic retail user authentication.

        Original SQL from RetailMultiUserAuthentication.authenticate()

        Args:
            token: Authentication token
            group_id: Group ID
            source_name: Source name
            investor_id: Investor ID
            partner_id: Optional partner ID

        Returns:
            Tuple: (user_pk, user_id, is_active, user_status, account_status, group_id, user_source_id, cp_user_pk, user_email) or None
        """
        selected_columns = [
            "lc.id as user_pk",
            "lc.user_id as user_id",
            "lc.is_active",
            "lusg.status as user_status",
            "la.status as account_status",
            "lusg.group_id as group_id",
            "lusg.id as user_source_id",
            "lc2.user_id as cp_user_pk" if partner_id else "null as cp_user_pk",
            "lc.encoded_email as user_email",
        ]

        params = {
            "token": token,
            "group_id": UserGroup.LENDER,
            "source_name": source_name,
            "investor_id": investor_id,
        }

        conditions = f"""
                    where at.key = %(token)s 
                    and lc.user_id = %(investor_id)s 
                    and ls.source_name = %(source_name)s 
                    and lusg.group_id = %(group_id)s
                """

        if partner_id:
            params["partner_id"] = partner_id
            conditions += " and lc2.partner_id = %(partner_id)s"

        sql = f"""
                select
                  {', '.join(selected_columns)}
                from
                  lendenapp_customuser lc
                join
                  lendenapp_user_source_group lusg on lusg.user_id = lc.id
                join
                  lendenapp_source ls on ls.id = lusg.source_id
                join
                  authtoken_token at on lc.id = at.user_id
                join
                  lendenapp_account la on la.user_source_group_id = lusg.id
                {('join lendenapp_channelpartner lc2 '
                  'on lusg.channel_partner_id = lc2.id') if partner_id else ''}
                """

        sql += conditions

        return self.sql_execute_fetch_one(sql, params)

    def get_fmpp_user_data(self, token, user_pk):
        """
        SQL function for FmppUserAuthentication - Get FMPP user data.

        Original SQL from FmppUserAuthentication.authenticate()

        Args:
            token: Authentication token
            user_pk: User primary key (from settings.FMPP_USER_ID)

        Returns:
            Tuple: (user_pk, user_id, user_source_id) or None
        """
        sql = """
            SELECT
                att.user_id, lc.user_id, lusg.id
            FROM authtoken_token att
            INNER JOIN lendenapp_customuser lc on lc.id = att.user_id
            INNER JOIN lendenapp_user_source_group lusg 
            on lc.id = lusg.user_id
            WHERE att.key = %(token)s and att.user_id = %(user_pk)s
        """
        params = {"token": token, "user_pk": user_pk}
        return self.sql_execute_fetch_one(sql, params)

    def get_manager_user_data(self, token, user_pk):
        """
        SQL function for ManagerAuthentication - Get manager user data.

        Original SQL from ManagerAuthentication.authenticate()

        Args:
            token: Authentication token

        Returns:
            Tuple: (user_pk, user_id, group_name) or None
        """
        sql = """
                SELECT
                    att.user_id, lc.user_id, lusg.id
                FROM authtoken_token att
                INNER JOIN lendenapp_customuser lc on lc.id = att.user_id
                INNER JOIN lendenapp_user_source_group lusg 
                on lc.id = lusg.user_id
                WHERE att.key = %(token)s and att.user_id = %(user_pk)s
        """
        params = {"token": token, "user_pk": user_pk}
        return self.sql_execute_fetch_one(sql, params)

    def get_pp_dashboard_user_data(self, user_id):
        """
        SQL function for PPDashboardBaseTokenAuthentication - Get PP dashboard user data.

        Original SQL from PPDashboardBaseTokenAuthentication.authenticate()

        Args:
            user_id: User ID from validated token

        Returns:
            Tuple: (user_pk,) or None
        """
        sql = """select id from lendenapp_customuser lc where user_id =%(user_id)s"""
        params = {"user_id": user_id}
        return self.sql_execute_fetch_one(sql, params)

    def get_retail_user_auth_data_v2(
        self, token, source_name, investor_id, partner_id=None
    ):
        """
        SQL function for RetailMultiUserAuthenticationV2 - Similar to RetailMultiUserAuthentication but V2.

        Original SQL from RetailMultiUserAuthenticationV2.authenticate()

        Args:
            token: Authentication token
            group_id: Group ID
            source_name: Source name
            investor_id: Investor ID
            partner_id: Optional partner ID

        Returns:
            Tuple: (user_pk, user_id, is_active, user_status, account_status, group_id, user_source_id, cp_user_pk) or None
        """
        selected_columns = [
            "lc.id as user_pk",
            "lc.user_id as user_id",
            "lc.is_active",
            "lusg.status as user_status",
            "la.status as account_status",
            "lusg.group_id as group_id",
            "lusg.id as user_source_id",
            "lc2.user_id as cp_user_pk" if partner_id else "null as cp_user_pk",
        ]

        params = {
            "token": token,
            "group_id": UserGroup.LENDER,
            "source_name": source_name,
            "investor_id": investor_id,
        }

        conditions = """
            where at.key = %(token)s 
            and lc.user_id = %(investor_id)s 
            and ls.source_name = %(source_name)s 
            and lusg.group_id = %(group_id)s
        """

        if partner_id:
            params["partner_id"] = partner_id
            conditions += " and lc2.partner_id = %(partner_id)s"

        sql = f"""
            select
              {', '.join(selected_columns)}
            from
              lendenapp_customuser lc
            join
              lendenapp_user_source_group lusg on lusg.user_id = lc.id
            join
              lendenapp_source ls on ls.id = lusg.source_id
            join
              authtoken_token at on lc.id = at.user_id
            join
              lendenapp_account la on la.user_source_group_id = lusg.id
            {('join lendenapp_channelpartner lc2 '
              'on lusg.channel_partner_id = lc2.id') if partner_id else ''}
        """
        sql += conditions

        return self.sql_execute_fetch_one(sql, params, to_dict=False)

    def check_investor_under_partner(self, investor_id, partner_id):
        """
        SQL function for JwtCPInvestorAuthentication.check_if_investor_under_partner.

        Original SQL from JwtCPInvestorAuthentication.check_if_investor_under_partner()

        Args:
            investor_id: Investor ID
            partner_id: Partner ID

        Returns:
            Dictionary: investor-partner relationship data or None
        """
        sql = """
            SELECT lc.id AS investor_pk, ls.source_name, lc.first_name,
            lusg.id AS user_source_id, lc2.user_id AS partner_user_pk, 
            lc.is_active AS is_investor_active, lusg.status AS user_status, 
            la.status AS account_status, lc.encoded_email as user_email,
            lc.is_family_member
            FROM lendenapp_user_source_group lusg 
            JOIN lendenapp_account la ON la.user_source_group_id = lusg.id
            JOIN lendenapp_source ls ON ls.id = lusg.source_id
            JOIN lendenapp_customuser lc ON lc.id = lusg.user_id
            JOIN lendenapp_channelpartner lc2 
            ON lc2.id = lusg.channel_partner_id
            WHERE lc.user_id = %(investor_id)s 
            AND lc2.partner_id = %(partner_id)s;
        """
        params = {
            "investor_id": investor_id,
            "partner_id": partner_id,
        }
        return self.sql_execute_fetch_one(sql, params, to_dict=True)

    def check_cp_under_mcp(self, cp_partner_id, mcp_user_pk):
        """
        SQL function for JwtCPInvestorAuthentication.check_cp_under_mcp.

        Original SQL from JwtCPInvestorAuthentication.check_cp_under_mcp()

        Args:
            cp_partner_id: Channel partner ID
            mcp_user_pk: MCP user primary key

        Returns:
            Dictionary: CP-MCP relationship data or None
        """
        sql = """
            SELECT lc.user_id as cp_user_pk, lc2.is_active as is_cp_active 
            FROM lendenapp_channelpartner lc
            JOIN lendenapp_customuser lc2 
            ON lc2.id = lc.user_id
            WHERE partner_id = %(cp_partner_id)s 
            AND referred_by_id = %(mcp_user_pk)s;
        """
        params = {"cp_partner_id": cp_partner_id, "mcp_user_pk": mcp_user_pk}
        return self.sql_execute_fetch_one(sql, params, to_dict=True)

    def get_jwt_cp_mcp_user_data(self, user_id):
        """
        SQL function for JwtCpMcpAuthentication - Get JWT CP/MCP user data.

        Original SQL from JwtCpMcpAuthentication.authenticate()

        Args:
            user_id: User ID from JWT token

        Returns:
            Tuple: (first_name, is_active, group_id, email, group_name) or None
        """
        sql = """
            SELECT lc.first_name, lc.is_active, lcg.group_id,
            lc.encoded_email, ag.name
            FROM lendenapp_customuser lc
            JOIN lendenapp_customuser_groups lcg 
            ON lc.id = lcg.customuser_id
            JOIN auth_group ag ON lcg.group_id = ag.id
            WHERE lc.user_id = %(user_id)s;
        """
        params = {"user_id": user_id}
        return self.sql_execute_fetch_one(sql, params)

    def get_jwt_retail_user_validation(self, user_id, user_source_group_id):
        """
        SQL function for JwtRetailMultiUserAuthentication - Get retail user validation data.

        Original SQL from JwtRetailMultiUserAuthentication.authenticate()

        Args:
            user_id: User ID
            user_source_group_id: User source group ID

        Returns:
            Tuple: (is_active, user_status, account_status) or None
        """
        selected_columns = [
            "lc.is_active",
            "lusg.status as user_status",
            "la.status as account_status",
        ]

        params = {"user_source_group_id": user_source_group_id, "user_id": user_id}

        conditions = """
            where lc.user_id = %(user_id)s 
            and la.user_source_group_id = %(user_source_group_id)s
        """

        sql = f"""
            select
              {', '.join(selected_columns)}
            from
              lendenapp_customuser lc
            join
              lendenapp_user_source_group lusg on lusg.user_id = lc.id
            join
              lendenapp_account la on la.user_source_group_id = lusg.id
        """
        sql += conditions

        return self.sql_execute_fetch_one(sql, params)
