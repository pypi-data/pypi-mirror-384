"""
Document Mapper using BaseDataLayer architecture
Converts the old document_mapper.py to use the new data layer pattern
"""

from ..base_datalayer import BaseDataLayer
from ..common.constants import DocumentConstant


class DocumentMapper(BaseDataLayer):
    """
    Document Mapper using BaseDataLayer for database operations
    Handles document related database operations
    """

    def __init__(self, user_source_id=None, db_alias="default"):
        super().__init__(db_alias)
        self.user_source_id = user_source_id

    def get_entity_name(self):
        """Return the entity name this mapper handles"""
        return "IOS_DOCUMENT"

    def get_document_by_type(self, document_type):

        sql = f"""
                select id, file,remark, created_date,modified_date 
                from lendenapp_document where 
                user_source_group_id=%s and type=%s order by id desc
            """

        return self.sql_execute_fetch_one(
            sql, [self.user_source_id, document_type], to_dict=True
        )

    @staticmethod
    def get_networth_document(user_pk):
        sql = f"""
                select id,file,remark,created_date,modified_date from 
                lendenapp_document where 
                user_id=%(user_id)s and type=%(type)s order by id desc
            """
        params = {
            "user_id": user_pk,
            "type": DocumentConstant.SIGNED_NETWORTH_CERTIFICATE,
        }

        return DocumentMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def insert_into_document(data):
        columns = ", ".join(data.keys())
        values = ", ".join(["%s"] * len(data))

        sql = (
            f"INSERT INTO lendenapp_document "
            f"({columns}) VALUES ({values}) RETURNING id"
        )

        return DocumentMapper().sql_execute_fetch_one(
            sql, list(data.values()), index_result=True
        )

    def get_document_type_list(self):
        sql = """
                select distinct(type) from lendenapp_document 
                where user_source_group_id=%s
            """
        return self.sql_execute_fetch_all(sql, [self.user_source_id], to_dict=False)

    @staticmethod
    def update_document_table(data, document_type, user_id, doc_id=None):
        sql = f""" UPDATE lendenapp_document SET {data} 
                   WHERE user_id=%(user_id)s 
                   and type=%(type)s """

        params = {"user_id": user_id, "type": document_type}

        if doc_id:
            params["doc_id"] = doc_id
            sql += " and id=%(doc_id)s"
        DocumentMapper().execute_sql(sql, params)

    @staticmethod
    def get_investor_documents(doc_types, user_source_id):
        sql = f"""
                SELECT type, file
                from lendenapp_document 
                where "type" in %s
                and user_source_group_id = %s
                order by created_date desc 
            """

        params = (tuple(doc_types), user_source_id)
        return DocumentMapper().sql_execute_fetch_all(sql, params, to_dict=True)

    @staticmethod
    def get_document_by_user_id(user_id):

        sql = f"""
                select type,file from lendenapp_document 
                where user_id = %(user_id)s 
            """
        params = {"user_id": user_id}
        return DocumentMapper().sql_execute_fetch_all(sql, params, to_dict=True)

    @staticmethod
    def get_file_from_document_table(user_pk):

        sql = """
                SELECT file
                FROM lendenapp_document
                WHERE type=%(type)s
                AND user_id =%(user_id)s
            """

        params = {"type": DocumentConstant.PHOTOGRAPH, "user_id": user_pk}

        return DocumentMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def check_if_document_id_exist(doc_type, user_pk=None, user_source_group_id=None):
        query = """SELECT EXISTS (
                   SELECT 1 
                   FROM lendenapp_document
                   WHERE type=%(type)s"""

        if user_source_group_id:
            query += " AND user_source_group_id=%(user_source_group_id)s)"
            params = {"type": doc_type, "user_source_group_id": user_source_group_id}

        else:
            query += " AND user_id= %(user_id)s)"
            params = {"type": doc_type, "user_id": user_pk}

        return DocumentMapper().sql_execute_fetch_one(query, params, index_result=True)

    @staticmethod
    def get_document(selected_col, column, value):
        sql = f"""
            SELECT
                {selected_col}
            FROM lendenapp_document
            WHERE {column}=%(value)s;
        """
        params = {"value": value}
        return DocumentMapper().sql_execute_fetch_one(
            sql=sql, params=params, to_dict=True
        )
