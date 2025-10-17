"""
User Source Group Mapper using BaseDataLayer architecture
Converts the old user_source_group_mapper.py to use the new data layer pattern
"""

from ..base_datalayer import BaseDataLayer
from ..common.constants import UserGroup, UserGroupSourceStatus


class UserSourceGroupMapper(BaseDataLayer):
    """
    User Source Group Mapper using BaseDataLayer for database operations
    Handles user source group related operations
    """

    def __init__(self, user_pk=None, source_id=None, cp_id=None, db_alias="default"):
        super().__init__(db_alias)
        self.user_pk = user_pk
        self.source_id = source_id
        self.cp_id = cp_id
        self.user_source_group_id = None

    def get_entity_name(self):
        """Return the entity name this mapper handles"""
        return "IOS_USER_SOURCE_GROUP"

    def get_user_source_group(self):
        sql = """select *  from lendenapp_user_source_group where
         user_id =%(user_id)s and source_id =%(source_id)s and 
         channel_partner_id """ + (
            "is NULL " if self.cp_id is None else """= %(cp_id)s"""
        )

        params = {
            "user_id": self.user_pk,
            "source_id": self.source_id,
            "cp_id": self.cp_id,
        }
        result = self.sql_execute_fetch_one(sql, params, to_dict=True)
        if result:
            self.user_source_group_id = result["id"]
            return result
        return None

    def insert_user_source_group(self):
        sql = """INSERT INTO public.lendenapp_user_source_group
            (user_id, source_id, group_id, channel_partner_id,
             status, created_at, updated_at)VALUES(%(user_id)s,
              %(source_id)s, %(group_id)s, %(cp_id)s, %(status)s,
               CURRENT_TIMESTAMP, CURRENT_TIMESTAMP) returning id;"""
        params = {
            "user_id": self.user_pk,
            "source_id": self.source_id,
            "group_id": UserGroup.LENDER,
            "cp_id": self.cp_id,
            "status": UserGroupSourceStatus.ACTIVE,
        }
        self.user_source_group_id = self.sql_execute_fetch_one(
            sql, params, to_dict=True
        )["id"]
