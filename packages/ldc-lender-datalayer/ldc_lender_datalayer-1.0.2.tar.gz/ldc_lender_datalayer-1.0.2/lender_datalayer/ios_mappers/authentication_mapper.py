"""
Authentication Data Layer Module

This module contains the AuthenticationDataLayer class that provides
all SQL functions used by authentication classes in the authentication.py file.

Each SQL query from the original authentication classes has been converted
to a function in this data layer for better organization and reusability.
"""

from ..base_datalayer import BaseDataLayer


class AuthenticationDataLayer(BaseDataLayer):
    def __init__(self, db_alias="default"):
        super().__init__(db_alias)

    """
    Data layer for authentication-related database operations.
    Contains all SQL queries used by authentication classes as functions.

    This class inherits from BaseDataLayer and provides:
    - get_ios_user_by_token(): For IOSAuthentication
    - get_multiuser_auth_data(): For MultiUserAuthentication
    - get_ops_user_data(): For OpsAuthentication
    - get_jwt_user_data(): For JwtCpMcpAuthentication
    - check_investor_under_partner(): For JwtCPInvestorAuthentication
    - check_cp_under_mcp(): For JwtCPInvestorAuthentication
    - get_retail_user_validation(): For JwtRetailMultiUserAuthentication
    - get_multiuser_auth_data_v2(): For MultiUserAuthenticationV2
    """

    def get_entity_name(self):
        """Return the entity name for this data layer."""
        return "IOS_AUTHENTICATION"

    def get_ios_user_by_token(self, key):
        """
        SQL function for IOSAuthentication - Get user by token.

        Original SQL from IOSAuthentication.authenticate()

        Args:
            key: Authentication token key

        Returns:
            Tuple: (user_id, user_id, group_id, key, first_name) or None
        """
        sql = """
            SELECT att.user_id, lc.user_id, lcg.group_id, 
            att.key, lc.first_name
            FROM authtoken_token att 
            INNER JOIN lendenapp_customuser lc on lc.id = att.user_id 
            left join lendenapp_customuser_groups lcg on lcg.customuser_id=lc.id 
            WHERE att.key=%s and lc.is_active
        """
        return self.sql_execute_fetch_one(sql, [key])

    def get_multiuser_auth_data(self, token, investor_id, source_name, group_id):
        """
        SQL function for MultiUserAuthentication - Complex multi-user authentication.

        Original SQL from MultiUserAuthentication.authenticate()

        Args:
            token: Authentication token
            investor_id: Investor ID
            source_name: Source name/partner code
            group_id: User group ID

        Returns:
            Tuple: (user_pk, user_id, is_active, status, group_id, user_source_id) or None
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
                cp_investor.investor_pk as user_pk, lc.user_id, 
                lc.is_active, lusg.status, lusg.group_id, 
                lusg.id as user_source_id
            from 
              cp_investor 
              join lendenapp_customuser lc on lc.id = investor_pk 
              join lendenapp_user_source_group lusg on lusg.user_id = lc.id 
              and case when not cp_investor.is_investor_token then lusg.channel_partner_id = cp_investor.cp_id else true end
              and lusg.group_id = %(group_id)s 
              join lendenapp_source ls on ls.id = lusg.source_id 
              and ls.source_name = %(source_name)s 
        """
        params = {
            "token": token,
            "group_id": group_id,
            "source_name": source_name,
            "investor_id": investor_id,
        }
        return self.sql_execute_fetch_one(sql, params)

    def get_ops_user_data(self, token, group_name):
        """
        SQL function for OpsAuthentication - Get operations user data.

        Original SQL from OpsAuthentication.authenticate()

        Args:
            token: Authentication token
            group_name: Group name for operations

        Returns:
            Tuple: (user_id, user_id, email, group_id, group_name, key) or None
        """
        sql = """
            SELECT
                att.user_id, lc.user_id, lc.encoded_email as email,
                lcg.group_id group_id, ag.name group_name, att.key
            FROM authtoken_token att
            INNER JOIN lendenapp_customuser lc on lc.id = att.user_id
            INNER JOIN lendenapp_customuser_groups lcg 
            on lcg.customuser_id=lc.id
            INNER JOIN auth_group ag on lcg.group_id = ag.id
            WHERE att.key = %(token)s AND ag.name = %(group_name)s
        """
        params = {
            "token": token,
            "group_name": group_name,
        }
        return self.sql_execute_fetch_one(sql, params)

    def get_jwt_user_data(self, user_id):
        """
        SQL function for JwtCpMcpAuthentication - Get JWT user data.

        Original SQL from JwtCpMcpAuthentication.authenticate()

        Args:
            user_id: User ID from JWT token

        Returns:
            Tuple: (first_name, is_active, group_id, user_pk, type) or None
        """
        sql = """
            SELECT lc.first_name, lc.is_active, lcg.group_id, 
            lc.id as user_pk, lc.type 
            FROM lendenapp_customuser lc
            JOIN lendenapp_customuser_groups lcg 
            ON lc.id = lcg.customuser_id
            WHERE lc.user_id = %(user_id)s;
        """
        params = {"user_id": user_id}
        return self.sql_execute_fetch_one(sql, params)

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
            SELECT lc.id AS investor_pk, ls.source_name, 
            lusg.id AS user_source_id, lc2.user_id AS partner_user_pk, 
            lc.is_active AS is_investor_active, lusg.status AS user_status, 
            la.status as account_status, lc.encoded_email AS user_email, 
            lc.first_name, lc.encoded_mobile AS user_mobile, lc.is_family_member
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
        return self.sql_execute_fetch_one(sql, params)

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
        return self.sql_execute_fetch_one(sql, params)

    def get_retail_user_validation(
        self, investor_id, source_name, group_id, partner_id=None
    ):
        """
        SQL function for JwtRetailMultiUserAuthentication - Dynamic retail user validation.

        Original SQL from JwtRetailMultiUserAuthentication.authenticate()

        Args:
            investor_id: Investor ID
            source_name: Source name
            group_id: Group ID
            partner_id: Optional partner ID

        Returns:
            Tuple: (is_active, user_status, group_id, cp_user_pk) or None
        """
        selected_columns = [
            "lc.is_active",
            "lusg.status as user_status",
            "lusg.group_id as group_id",
            "lc2.user_id as cp_user_pk" if partner_id else "null as cp_user_pk",
        ]

        params = {
            "group_id": group_id,
            "source_name": source_name,
            "investor_id": investor_id,
        }

        conditions = """
            where lc.user_id = %(investor_id)s 
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
              lendenapp_task lt on lt.user_source_group_id = lusg.id
            join
              lendenapp_source ls on ls.id = lusg.source_id
            {('join lendenapp_channelpartner lc2 '
              'on lusg.channel_partner_id = lc2.id') if partner_id else ''}
            {conditions}
        """

        return self.sql_execute_fetch_one(sql, params)

    def get_multiuser_auth_data_v2(self, token, investor_id, source_name, group_id):
        """
        SQL function for MultiUserAuthenticationV2 - Similar to MultiUserAuthentication but V2.

        Original SQL from MultiUserAuthenticationV2.authenticate()

        Args:
            token: Authentication token
            investor_id: Investor ID
            source_name: Source name/partner code
            group_id: User group ID

        Returns:
            Tuple: (user_pk, user_id, is_active, status, group_id, user_source_id) or None
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
                cp_investor.investor_pk as user_pk, lc.user_id, lc.is_active, lusg.status,lusg.group_id, lusg.id as user_source_id
            from 
              cp_investor 
              join lendenapp_customuser lc on lc.id = investor_pk 
              join lendenapp_user_source_group lusg on lusg.user_id = lc.id 
              and case when not cp_investor.is_investor_token then lusg.channel_partner_id = cp_investor.cp_id else true end
              and lusg.group_id = %(group_id)s 
              join lendenapp_source ls on ls.id = lusg.source_id 
              and ls.source_name = %(source_name)s 
        """
        params = {
            "token": token,
            "group_id": group_id,
            "source_name": source_name,
            "investor_id": investor_id,
        }
        return self.sql_execute_fetch_one(sql, params)
