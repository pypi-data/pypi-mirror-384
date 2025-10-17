"""
Dashboard Mapper using BaseDataLayer architecture
Converts the old dashboard_mapper.py to use the new data layer pattern
"""

from ..base_datalayer import BaseDataLayer
from ..common.constants import ProductFormConstants


class DashboardMapper(BaseDataLayer):
    """
    Dashboard Mapper using BaseDataLayer for database operations
    Handles dashboard configuration and user management operations
    """

    def __init__(self, db_alias="default"):
        super().__init__(db_alias)

    def get_entity_name(self):
        """Return the entity name this mapper handles"""
        return "IOS_DASHBOARD"

    @staticmethod
    def get_dashboard_config_keys(logical_reference):
        query = """
            SELECT config_type, config_key
            FROM lendenapp_application_config
        """

        params = {}
        if "ALL" not in logical_reference:
            query += f"WHERE logical_reference = ANY(%s) "
            params = [logical_reference]

        query += """
            GROUP BY config_type, config_key
            ORDER BY config_type, config_key
        """

        return DashboardMapper().sql_execute_fetch_all(query, params, to_dict=True)

    @staticmethod
    def get_all_form_configuration(logical_reference):
        refs = logical_reference or []
        required_logical_reference = [
            ProductFormConstants.PRODUCT_FORM,
            ProductFormConstants.FORM,
        ]
        has_all = "ALL" in refs
        has_required_subset = all(
            form_reference in refs for form_reference in required_logical_reference
        )

        if not has_all and not has_required_subset:
            return []

        query = """
          SELECT config_type, config_key
          FROM lendenapp_application_config
          WHERE form_configuration IS NOT NULL or logical_reference=%(logical_reference)s
        """
        params = {"logical_reference": ProductFormConstants.PRODUCT_FORM}

        return DashboardMapper().sql_execute_fetch_all(query, params, to_dict=True)

    @staticmethod
    def get_config_value_form_configuration(config_type, config_key):
        query = """
         SELECT config_value,form_configuration
         FROM lendenapp_application_config
         WHERE config_type = %s AND config_key = %s and form_configuration is not null
        """
        params = [config_type, config_key]
        return DashboardMapper().sql_execute_fetch_all(query, params, to_dict=True)

    def get_dashboard_users(self, allowed_roles):
        query = """
            SELECT 
            lc.first_name as name,
            lc.email,
            lc.id,
            array_agg(ag.name) as roles
            FROM
                lendenapp_customuser lc
            JOIN
                lendenapp_customuser_groups lcg ON lc.id = lcg.customuser_id
            JOIN
                auth_group ag ON ag.id = lcg.group_id
            WHERE
                ag.name = ANY(%(allowed_roles)s)
            GROUP BY
                lc.id;
        """

        params = {"allowed_roles": allowed_roles}
        return self.sql_execute_fetch_all(query, params, to_dict=True)

    def delete_user_role(self, user_pk, role):
        query = """
            DELETE FROM lendenapp_customuser_groups
            WHERE customuser_id = %(user_pk)s
            AND group_id = (SELECT id FROM auth_group WHERE name = %(role)s) RETURNING 1
        """
        params = {"user_pk": user_pk, "role": role}
        return self.sql_execute_fetch_all(query, params, to_dict=True)

    def search_user(self, search_term):
        query = """
            SELECT 
            lc.first_name as name,
            lc.email,
            lc.id,
            array_agg(ag.name) as roles
            FROM
                lendenapp_customuser lc
            LEFT JOIN
                lendenapp_customuser_groups lcg ON lc.id = lcg.customuser_id
            LEFT JOIN
                auth_group ag ON ag.id = lcg.group_id
            WHERE
                lc.email = %(search_term)s
            GROUP BY lc.id;
        """
        params = {"search_term": search_term}
        return self.sql_execute_fetch_all(query, params, to_dict=True)

    def get_roles(self, user_id):
        query = """
            SELECT ag.name
            FROM auth_group ag
            JOIN lendenapp_customuser_groups lcg ON ag.id = lcg.group_id
            WHERE lcg.customuser_id = %(user_id)s
        """
        params = {"user_id": user_id}
        return self.sql_execute_fetch_all(query, params, to_dict=True)

    def assign_role(self, user_id, role_name):
        query = """
            INSERT INTO lendenapp_customuser_groups (customuser_id, group_id)
            VALUES (%(user_id)s, (SELECT id FROM auth_group WHERE name = %(role_name)s))
            RETURNING 1
        """
        params = {"user_id": user_id, "role_name": role_name}
        return self.sql_execute_fetch_all(query, params, to_dict=True)

    @staticmethod
    def get_dashboard_data(query):
        return DashboardMapper().sql_execute_fetch_all(query, [], to_dict=True)
