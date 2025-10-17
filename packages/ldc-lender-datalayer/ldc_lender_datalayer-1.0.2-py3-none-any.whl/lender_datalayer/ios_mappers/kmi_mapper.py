"""
KMI Mapper using BaseDataLayer architecture
Converts the old kmi_mapper.py to use the new data layer pattern
"""

from ..base_datalayer import BaseDataLayer


class KMIMapper(BaseDataLayer):
    """
    KMI Mapper using BaseDataLayer for database operations
    Handles KYC Management Interface operations
    """

    def __init__(self, db_alias="default"):
        super().__init__(db_alias)

    def get_entity_name(self):
        """Return the entity name this mapper handles"""
        return "IOS_KMI"

    @staticmethod
    def check_if_tracking_id_exist(tracking_id, user_source_group_id, user_pk):
        query = """SELECT EXISTS (
                   SELECT 1 
                   FROM lendenapp_userkyc 
                   WHERE tracking_id = %(tracking_id)s 
                   AND user_id = %(user_pk)s
                   """

        params = {"tracking_id": tracking_id, "user_pk": user_pk}

        if user_source_group_id:
            query += " AND user_source_group_id = %(user_source_group_id)s "
            params["user_source_group_id"] = user_source_group_id

        query += " ) AS record_exists "

        return KMIMapper().sql_execute_fetch_one(query, params, index_result=True)

    @staticmethod
    def get_kyc_data(tracking_id):
        query = f"""
                SELECT lusg.id as user_source_id, lc.id as user_id,
                lu.kyc_type, lc.encoded_pan, lc.dob, lc.first_name, 
                lc.encoded_mobile as mobile_number,ls.source_name,
                lc.encoded_email as email,
                lc.email_verification, lc.is_family_member
                FROM lendenapp_userkyctracker lu
                JOIN lendenapp_customuser lc ON lc.id = lu.user_id
                LEFT JOIN lendenapp_user_source_group lusg 
                ON lusg.id = lu.user_source_group_id
                LEFT JOIN lendenapp_source ls ON lusg.source_id = ls.id
                WHERE tracking_id = %(tracking_id)s"""
        params = {"tracking_id": tracking_id}
        return KMIMapper().sql_execute_fetch_one(query, params, to_dict=True)

    @staticmethod
    def get_kmi_status(investor_pk, tracking_id, user_source_group_id=None):
        query = """
                SELECT status, service_type AS service, provider, 
                       event_code, status_code  
                FROM lendenapp_userkyc lu 
                WHERE user_id=%(user_id)s  
                AND tracking_id=%(tracking_id)s
        """

        params = {
            "user_id": investor_pk,
            "tracking_id": tracking_id,
        }

        if user_source_group_id:
            query += " AND user_source_group_id=%(user_source_group_id)s"
            params["user_source_group_id"] = user_source_group_id

        query += " ORDER BY id DESC LIMIT 1"

        return KMIMapper().sql_execute_fetch_one(query, params, to_dict=True)

    @staticmethod
    def insert_kmi_response(user_id, tracking_id, user_source_group_id, data_dic={}):
        query = """INSERT INTO lendenapp_userkyc (user_id, 
        tracking_id, status, poi_name, poa_name, user_source_group_id,
        service_type, user_kyc_consent, event_status, provider, event_code, 
        status_code) 
        VALUES(%(user_id)s, %(tracking_id)s, %(status)s, %(poi_name)s,
        %(poa_name)s, %(user_source_group_id)s, %(service_type)s, 
        %(user_consent)s, %(event_status)s, %(provider)s, %(event_code)s, 
        %(status_code)s);"""
        params = {
            "user_id": user_id,
            "user_source_group_id": user_source_group_id,
            "tracking_id": tracking_id,
            "status": data_dic.get("kyc_status"),
            "poi_name": data_dic.get("poi_name"),
            "poa_name": data_dic.get("poa_name"),
            "event_status": data_dic.get("event_status"),
            "provider": data_dic.get("provider"),
            "event_code": data_dic.get("event_code"),
            "status_code": data_dic.get("status_code"),
            "service_type": data_dic.get("service"),
            "user_consent": True,
        }
        KMIMapper().execute_sql(query, params)
        return True

    @staticmethod
    def get_lender_kyc_data(data):
        sql = """
            SELECT 
                lc.encoded_email AS email,
                lc.encoded_mobile AS mobile_number,
                lc.email_verification,
                lc.id AS id,
                CASE 
                    WHEN lc.ckycr_number = %(ckycr_number)s THEN TRUE 
                    ELSE FALSE 
                END AS ckycr_match, 
                lc.is_family_member, lusg.id AS user_source_id
            FROM lendenapp_userkyctracker lu 
            JOIN lendenapp_user_source_group lusg 
                ON lu.user_source_group_id = lusg.id 
            JOIN lendenapp_customuser lc 
                ON lusg.user_id = lc.id 
            WHERE lu.tracking_id = %(tracking_id)s
        """

        params = {
            "tracking_id": data["tracking_id"],
            "ckycr_number": data["ckycr_number"],
        }
        return KMIMapper().sql_execute_fetch_one(sql, params, to_dict=True)
