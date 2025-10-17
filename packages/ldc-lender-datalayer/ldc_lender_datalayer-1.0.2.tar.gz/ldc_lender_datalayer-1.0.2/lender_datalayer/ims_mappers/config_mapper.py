import json
import logging

from ..base_datalayer import BaseDataLayer

logger = logging.getLogger("normal")


class ConfigMapper(BaseDataLayer):
    def __init__(self, db_alias="default"):
        super().__init__(db_alias)

    def get_entity_name(self):
        return "IMS_CONFIG"

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
