"""
Config Mapper using BaseDataLayer architecture
Converts the old config_mappers.py to use the new data layer pattern
"""

import json
import logging

from ..base_datalayer import BaseDataLayer

logger = logging.getLogger("normal")


class ConfigMapper(BaseDataLayer):
    """
    Config Mapper using BaseDataLayer for database operations
    Handles application configuration and logging operations
    """

    def __init__(self, db_alias="default"):
        super().__init__(db_alias)

    def get_entity_name(self):
        """Return the entity name this mapper handles"""
        return "IOS_CONFIG"

    def get_ip_whitelist_config(self, request_path):
        sql = """
            SELECT config_value 
            FROM lendenapp_application_config 
            WHERE config_key = 'IP_WHITELISTING' AND is_active = TRUE
            ORDER BY id DESC LIMIT 1
        """
        result = self.sql_execute_fetch_one(sql, {}, to_dict=True)
        if not result or not result.get('config_value'):
            return None
        try:
            configs = json.loads(result['config_value'])
            for config in configs:
                if config.get('endpoint') == request_path:
                    return {
                        'allowed_ips': config.get('allowed_ips', []),
                        'allowed_users': config.get('allowed_users', [])
                    }
        except Exception as e:
            logger.error(f"Failed to parse IP whitelist config: {str(e)}")
        return None

    def log_request(self, request, activity, additional_detail=None):
        try:
            user_identifier = request.headers.get('USER-IDENTIFIER')
            if not user_identifier:
                user_identifier = request.user_data.email or 'unknown'
            ip_address = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', 'unknown'))
            log_sql = """
                INSERT INTO lendenapp_timeline (activity, detail)
                VALUES (%s, %s)
            """
            detail = f"{user_identifier} | {ip_address} | {additional_detail}"
            log_params = (activity, detail)
            return self.execute_sql(log_sql, log_params)
        except Exception as e:
            logger.error(f"Failed to log request to lendenapp_timeline: {str(e)}")
            return None


    @staticmethod
    def get_otl_max_amount_config():
        sql = """
                SELECT config_value 
                FROM lendenapp_application_config 
                WHERE config_key = 'OTL_AMOUNT_LIMIT' AND is_active = TRUE
            """

        result = ConfigMapper().sql_execute_fetch_one(sql, {}, to_dict=True)

        if not result:
            return None

        final_config = {}

        try:
            config_data = json.loads(result["config_value"])  # This is a list of dicts
            final_config = {"LDC": [], "LCP": [], "MCP": []}

            for config in config_data:
                cp_config = config.get("CP", [])
                ldc_config = config.get("LDC", [])

                final_config["LDC"].extend(ldc_config)
                final_config["LCP"].extend(cp_config)
                final_config["MCP"].extend(cp_config)

        except Exception as e:
            logger.exception(f"Failed to parse otl max amount config: {str(e)}")

        return final_config
