import logging

from ..base_datalayer import BaseDataLayer, DataLayerUtils
from ..common.constants import AccountStatus, DocumentConstant, DocumentRemark, DummyUserConstant, HOFMember

logger = logging.getLogger("normal")


class DocumentMapper(BaseDataLayer):
    def __init__(self, user_pk=None, user_source_id=None, db_alias="default"):
        super().__init__(db_alias)
        self.user_pk = user_pk
        self.user_source_id = user_source_id

    def get_entity_name(self):
        return "IMS_DOCUMENT"

    @staticmethod
    def insert_into_document(data):
        columns = ", ".join(data.keys())
        values = ", ".join(["%s"] * len(data))

        sql = (
            f"INSERT INTO lendenapp_document "
            f"({columns}) VALUES ({values}) RETURNING id"
        )

        return DocumentMapper().sql_execute_fetch_one(
            sql, list(data.values()), to_dict=True
        )

    def get_document_details(self, type, user_source_id, scheme_id):
        query = """
                select file,description from 
                lendenapp_document ld 
                where user_source_group_id=%(user_source_group_id)s 
                and description ~ %(scheme_id)s  
                and type = %(type)s
            """

        params = {
            "type": type,
            "user_source_group_id": user_source_id,
            "scheme_id": scheme_id,
        }

        results = self.sql_execute_fetch_one(query, params, to_dict=True)
        return results

    def delete_document_by_scheme_id(self, scheme_id):
        sql = """
                UPDATE lendenapp_document
                SET user_id = %(dummy_user_id)s,
                    user_source_group_id = NULL,
                    remark = 'DELETED',
                    modified_date = NOW()
                WHERE user_source_group_id = %(user_source_group_id)s 
                and type = %(type)s  and description ~ %(scheme_id)s;
        """

        params = {
            "user_source_group_id": self.user_source_id,
            "type": DocumentConstant.DIGITAL_CERTIFICATE,
            "scheme_id": scheme_id,
            "dummy_user_id": DummyUserConstant.DUMMY_USER_ID,
        }

        return self.execute_sql(sql, params, return_rows_count=True)

    @staticmethod
    def get_document_by_type_and_task_id(
        task_id, document_type, description, selected_columns="*"
    ):
        selected_columns_str = ",".join(selected_columns)
        sql = f"""
                select {selected_columns_str} from lendenapp_document ld where 
                task_id=%(task_id)s and type=%(type)s and 
                description=%(description)s
            """
        params = {"task_id": task_id, "type": document_type, "description": description}
        return DocumentMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def get_networth_document(user_pk, selected_columns):
        """
        selected_columns - It will be a list of columns associated
                            with lendenapp_document table in db
        """

        selected_columns_str = ", ".join(selected_columns)
        sql = f"""
                select {selected_columns_str} from lendenapp_document where user_id=%(user_id)s
                and type=%(type)s order by id desc
            """
        params = {
            "user_id": user_pk,
            "type": DocumentConstant.NETWORTH_CERTIFICATE_TYPE,
        }

        return DocumentMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def get_details_from_document_table(
        columns_and_values, order_by=False, fetch_all=False, limit_data=None
    ):
        conditions = " AND ".join(
            [f"{column} = %s" for column in columns_and_values.keys()]
        )

        sql = f"""
                    SELECT id,type,file,modified_date,created_date,
                    remark, fiscal_year, description
                    FROM lendenapp_document
                    WHERE {conditions}
                """
        if order_by:
            sql += " order by id desc "

        if limit_data:
            sql += f" limit {limit_data['limit']} offset {limit_data['offset']} "

        params = tuple(columns_and_values.values())

        if fetch_all:
            return DocumentMapper().sql_execute_fetch_all(sql, params, to_dict=True)

        return DocumentMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    def get_all_documents(self):
        query = """
            SELECT 
                DISTINCT ON (type) type, 
                file, 
                Date(created_date)
            FROM 
                lendenapp_document 
            WHERE 
                user_id =%s 
                AND file IS NOT NULL 
            ORDER BY 
                type, id DESC
        """

        return self.sql_execute_fetch_all(query, [self.user_pk], to_dict=True)

    def fetch_document_for_user(self, columns_and_values, selected_columns=["*"]):
        conditions = []
        params = {}
        for column, value in columns_and_values.items():
            if isinstance(value, (list, tuple)):
                conditions.append(f"{column} = ANY(%({column})s)")
            else:
                conditions.append(f"{column} = %({column})s")
            params[column] = value

        selected_columns_str = ", ".join(selected_columns)
        conditions_str = " AND ".join(conditions)

        sql = f"""
                    SELECT {selected_columns_str}
                    FROM lendenapp_document
                    WHERE {conditions_str}
                """

        params = DataLayerUtils().prepare_sql_params(params)
        return self.sql_execute_fetch_all(sql, params=params, to_dict=True)

    def get_latest_document_name_by_user_source_id(self, types=None):

        sql = f"""
                SELECT file FROM lendenapp_document
                WHERE user_source_group_id = %(user_source_id)s 
              """

        params = {"user_source_id": self.user_source_id}

        if types:
            sql += " and type= ANY(%(types)s)"
            params["types"] = types

        sql += " ORDER BY id DESC"

        return self.sql_execute_fetch_one(sql, params, index_result=True)

    @staticmethod
    def get_document_by_user(conditions):

        sql = f"""
                select user_source_group_id, ld.user_id, remark, fiscal_year, 
                lc.type, lcg.group_id, lc.is_family_member
                from lendenapp_document ld
                join lendenapp_customuser lc on lc.id = ld.user_id
                join lendenapp_customuser_groups lcg on lc.id = lcg.customuser_id
                WHERE ld.id = %(document_id)s 
                and lc.user_id = %(user_id)s and ld.type = %(document_type)s
            """

        return DocumentMapper().sql_execute_fetch_one(sql, conditions, to_dict=True)

    @staticmethod
    def get_document_list(data):

        sql = f"""
                SELECT ld.type,ld.id as document_id,ld.file,ld.remark,
                ld.created_date,ld.modified_date,ld.description, ld.fiscal_year,
                lc.is_family_member
                 FROM lendenapp_document ld
                JOIN lendenapp_customuser lc on lc.id = ld.user_id
                WHERE lc.user_id = %(user_id)s
            """

        if data.get("user_source_id"):
            sql += " and ld.user_source_group_id = %(user_source_id)s"

        if data.get("document_type"):
            if set(data["document_type"]) & {
                DocumentConstant.BROKERAGE_INVOICE,
                DocumentConstant.SIGNED_NETWORTH_CERTIFICATE,
            }:
                if data.get("document_id"):
                    sql += " and ld.id = %(doc_id)s "
                if DocumentConstant.BROKERAGE_INVOICE in data["document_type"]:
                    sql += " and ld.fiscal_year = %(fiscal_month)s"

            sql += " and ld.type=ANY(%(doc_type)s)"
        else:
            sql += " and ld.type <> ALL(%(doc_type)s)"

        sql += " ORDER BY ld.id DESC"

        params = {
            "doc_type": (
                tuple(data.pop("document_type"))
                if data.get("document_type")
                else (
                    DocumentConstant.DIGITAL_CERTIFICATE,
                    DocumentConstant.AUTHORIZATION_LETTER,
                    DocumentConstant.LENDER_AGREEMENT,
                )
            ),
            "doc_id": data.get("document_id"),
            **data,
        }

        params = DataLayerUtils().prepare_sql_params(params)
        return DocumentMapper().sql_execute_fetch_all(sql, params, to_dict=True)

    def get_count_of_documents(self, valid_doc_list):
        sql = """
                    SELECT COUNT(ld.id)
                    FROM lendenapp_document ld 
                    where ld.user_id = %(user_id)s
                    AND ld.type =ANY(%(valid_doc_list)s);
             """

        params = {"user_id": self.user_pk, "valid_doc_list": list(valid_doc_list)}

        params = DataLayerUtils().prepare_sql_params(params)
        return self.sql_execute_fetch_one(sql, params, index_result=True)

    @staticmethod
    def get_cp_and_inv_details_by_doc_id(columns_and_values):
        conditions = " AND ".join(
            [f"{column} = %s" for column in columns_and_values.keys()]
        )

        sql = f"""
                select lc.first_name as inv_name,lc3.first_name as cp_name,
                lc3.encoded_email as cp_email from lendenapp_document ld 
                join lendenapp_customuser lc on lc.id = ld.user_id 
                join lendenapp_user_source_group lusg on lusg.id = ld.user_source_group_id 
                join lendenapp_channelpartner lc2 on lc2.id = lusg.channel_partner_id 
                join lendenapp_customuser lc3 on lc3.id = lc2.user_id
                where {conditions};
             """

        params = tuple(columns_and_values.values())
        return DocumentMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def update_document_table(data, document_type, user_id, doc_id):
        sql = f""" UPDATE lendenapp_document SET {data} 
                   WHERE user_id=%(user_id)s 
                   AND type=%(type)s AND id=%(doc_id)s """

        params = {"user_id": user_id, "type": document_type, "doc_id": doc_id}
        DocumentMapper().execute_sql(sql, params)

    @staticmethod
    def get_all_invoice_documents(data):
        sql = """
                SELECT ld.id as document_id, ld.remark, ld.file, ld.description,
                ld.created_date, lc.user_id, lc.first_name, ld.fiscal_year
                FROM lendenapp_document ld 
                JOIN lendenapp_customuser lc ON ld.user_id = lc.id
                WHERE ld.type = %(doc_type)s
                ORDER BY ld.id DESC
                LIMIT %(limit)s OFFSET %(offset)s
            """

        params = {
            "doc_type": DocumentConstant.BROKERAGE_INVOICE,
            "limit": data["limit"],
            "offset": data["offset"],
        }

        return DocumentMapper().sql_execute_fetch_all(sql, params, to_dict=True)

    @staticmethod
    def get_all_lender_documents(document_type_list, request_data):
        sql = """
                SELECT '' as file, ld.id as document_id, ld.remark as status, 
                TO_CHAR(ld.created_date, 'DD/MM/YYYY') AS uploaded_date, 
                lc.user_id, lc.first_name, ld.type as document_type, 
                lusg.id as user_source_id, lc.is_family_member,
                r.relation, lc2.first_name as cp_name
                FROM lendenapp_document ld 
                JOIN lendenapp_user_source_group lusg 
                ON ld.user_source_group_id = lusg.id
                JOIN lendenapp_customuser lc 
                ON lc.id = lusg.user_id
                JOIN lendenapp_account la 
                ON la.user_source_group_id = lusg.id
                LEFT JOIN lendenapp_channelpartner lcp 
                ON lcp.id = lusg.channel_partner_id
                LEFT JOIN lendenapp_customuser lc2
                ON lc2.id = lcp.user_id
                LEFT JOIN  lendenapp_reference r 
                    ON ld.user_source_group_id=r.user_source_group_id 
                    AND ld.type = ANY(%(relation_doc_type)s)
                    AND r.type = ANY(%(relation_type)s)
                WHERE ld.type = ANY(%(doc_type)s) 
                AND ld.remark = %(document_remark)s 
                AND la.status = %(account_status)s
                ORDER BY ld.id DESC
                LIMIT %(limit)s OFFSET %(offset)s
            """

        params = {
            "doc_type": document_type_list,
            "document_remark": DocumentRemark.SUBMITTED,
            "account_status": AccountStatus.OPEN,
            "limit": request_data["limit"],
            "offset": request_data["offset"],
            "relation_type": [HOFMember.REFERENCE_TYPE],
            "relation_doc_type": [DocumentConstant.RELATIONSHIP],
        }

        params = DataLayerUtils().prepare_sql_params(params)
        return DocumentMapper().sql_execute_fetch_all(sql, params, to_dict=True)

    @staticmethod
    def get_brokerage_invoice_count(user_pk=None, is_wm=False):
        sql = """
                    SELECT count(*) as total_count from lendenapp_document ld
                    where ld.type = %(doc_type)s
                """

        params = {"doc_type": DocumentConstant.BROKERAGE_INVOICE}

        if not is_wm:
            sql += " and ld.user_id = %(user_pk)s"
            params["user_pk"] = user_pk

        return DocumentMapper().sql_execute_fetch_one(sql, params, index_result=True)
