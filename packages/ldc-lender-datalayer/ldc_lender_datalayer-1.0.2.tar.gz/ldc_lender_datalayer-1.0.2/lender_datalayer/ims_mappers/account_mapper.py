from ..base_datalayer import BaseDataLayer, DataLayerUtils
from ..common.constants import CKYCServiceType, FMITransactionStatus, TimeZone, TransactionStatus, TransactionType
from ..common.utils.datetime_utils import get_date_from_request


class AccountMapper(BaseDataLayer):
    def __init__(self, investor_pk=None, db_alias="default"):
        super().__init__(db_alias)
        self.investor_pk = investor_pk

    def get_entity_name(self):
        return "IMS_ACCOUNT"

    def fetch_fmpp_account_statement(
        self,
        user_source_id,
        transaction_type_list,
        status_list,
        filter_data,
        get_total_count=False,
        order="DESC",
    ):
        filters = ""
        if filter_data.get("from_date") and filter_data.get("to_date"):
            filters = (
                f" and (created_date AT TIME ZONE 'Asia/Kolkata')::date between '"
                f"{get_date_from_request(filter_data.get('from_date'))}'"
                f" and '{get_date_from_request(filter_data.get('to_date'))}'"
            )

        limit_offset = ""
        if get_total_count:
            order_by = ""
            column = f" count(*)"
        else:
            column = f""" 
                        transaction_id,
                        CASE 
                            WHEN type = ANY(ARRAY['SHORT TERM LENDING', 'MEDIUM TERM LENDING']) 
                            THEN (updated_date AT TIME ZONE 'Asia/Kolkata')
                            ELSE (created_date AT TIME ZONE 'Asia/Kolkata')
                        END created_date,
                        type,
                        amount,
                        description,
                        status
                    """
            order_by = f" ORDER BY created_date {order}, id {order}"

            limit = filter_data.get("limit")
            offset = filter_data.get("offset")

            if limit and offset is not None:
                limit_offset = f" LIMIT {limit} OFFSET {offset}"

        query = (
            """
        SELECT
            """
            + column
            + """
        FROM
            lendenapp_transaction
        WHERE
            (from_user_id = %(investor_pk)s OR to_user_id = %(investor_pk)s)
            AND type = ANY(%(transaction_type)s)
            and user_source_group_id = %(user_source_group_id)s
            AND status = ANY(%(status)s) """
            + filters
            + order_by
            + limit_offset
            + """
        """
        )

        params = {
            "investor_pk": self.investor_pk,
            "transaction_type": transaction_type_list,
            "status": status_list,
            "user_source_group_id": user_source_id,
        }

        params = DataLayerUtils().prepare_sql_params(params)
        if get_total_count:
            return self.sql_execute_fetch_one(query, params, index_result=True)

        return self.sql_execute_fetch_all(query, params, to_dict=True)

    @staticmethod
    def fetch_transaction_details(transaction_id=None, request_id=None):
        query = """
            SELECT 
                id, status,  created_date, type, amount,
                description, from_user_id, to_user_id, utr_no,
                rejection_reason, user_source_group_id, type_id, transaction_id
            FROM lendenapp_transaction 
        """
        if transaction_id and request_id:
            query = f"""
                ({query} WHERE transaction_id = %(transaction_id)s AND type_id = %(request_id)s)
                UNION ALL
                ({query} WHERE transaction_id = %(transaction_id)s AND response_id = %(request_id)s)
            """
        elif request_id:
            query = f"""
                ({query} WHERE type_id = %(request_id)s)
                UNION ALL
                ({query} WHERE response_id = %(request_id)s)
            """
        else:
            query += """WHERE transaction_id=%(transaction_id)s """

        data = AccountMapper().sql_execute_fetch_all(
            query,
            {"transaction_id": transaction_id, "request_id": request_id},
            to_dict=True,
        )
        if data:
            return data[0]
        return None

    @staticmethod
    def fetch_fmpp_scheme_details_using_request_id(request_id):
        query = """
                SELECT
                    description, transaction_id, created_date
                FROM
                    lendenapp_transaction
                WHERE
                    type_id = %(request_id)s and 
                    type in %(type)s
                    """
        return AccountMapper().sql_execute_fetch_one(
            query,
            {
                "request_id": request_id,
                "type": (
                    TransactionType.FMPP_INVESTMENT,
                    TransactionType.MANUAL_LENDING,
                    TransactionType.SHORT_TERM_LENDING,
                ),
            },
            to_dict=True,
        )

    def get_payment_link_for_cp_investor(self, cp_user_pk):

        sql = f"""
                select created_date from lendenapp_paymentlink
                where created_by_id = %(cp_user_pk)s and
                created_for_id = %(investor_pk)s 
                order by created_date desc
                LIMIT 1
        """

        param = {"cp_user_pk": cp_user_pk, "investor_pk": self.investor_pk}

        return self.sql_execute_fetch_one(sql, param, to_dict=True)

    def fetch_transaction_data(self, user_source_group_id):
        sql = f"""
            select id from lendenapp_transaction 
            where user_source_group_id = %(user_source_group_id)s 
            and type = %(transaction_type)s and 
            status = ANY(%(status_type)s)
        """

        params = {
            "user_source_group_id": user_source_group_id,
            "transaction_type": TransactionType.ADD_MONEY,
            "status_type": (TransactionStatus.SUCCESS, TransactionStatus.COMPLETED),
        }

        params = DataLayerUtils().prepare_sql_params(params)
        return self.sql_execute_fetch_one(sql, params, to_dict=True)

    def fetch_recent_transaction(self, limit, offset, user_source_id):
        status = (
            TransactionStatus.FAILED,
            TransactionStatus.FAIL,
            TransactionStatus.SUCCESS,
            TransactionStatus.SCHEDULED,
            TransactionStatus.PROCESSING,
            TransactionStatus.PENDING,
        )

        types = (
            TransactionType.ADD_MONEY,
            TransactionType.WITHDRAW_MONEY,
            TransactionType.MIP_AUTO_WITHDRAWAL,
            TransactionType.MANUAL_LENDING_AUTO_WITHDRAWAL,
            TransactionType.LUMPSUM_AUTO_WITHDRAWAL,
            TransactionType.SHORT_TERM_LENDING_AUTO_WITHDRAWAL,
            TransactionType.IDLE_FUND_WITHDRAWAL,
            TransactionType.REPAYMENT_AUTO_WITHDRAWAL,
            TransactionType.FMPP_REPAYMENT_WITHDRAWAL,
            TransactionType.AUTO_LENDING_REPAYMENT_WITHDRAWAL,
            TransactionType.AUTO_LENDING_REPAYMENT_ADD_MONEY,
        )

        failed_status = (TransactionStatus.FAILED, TransactionStatus.FAIL)

        query = (
            """
            SELECT 
                created_date AT TIME ZONE %(indian_time)s AS created_date, 
                type, 
                amount, 
                transaction_id,
                status <> ALL((%(failed_status)s)) AS success,
                response_id AS payment_reference_id,
                 CASE 
                    WHEN status = ANY(%(failed_status)s) THEN '"""
            + TransactionStatus.FAILED
            + """' 
                   ELSE status 
               END AS label,
                COUNT(*) OVER() AS total
            FROM lendenapp_transaction
            WHERE user_source_group_id = %(user_source_group_id)s
              AND type = ANY(%(type)s)
              AND status = ANY(%(status)s)
            ORDER BY created_date DESC
            LIMIT %(limit)s
        """
        )

        params = {
            "failed_status": failed_status,
            "type": types,
            "status": status,
            "limit": limit,
            "indian_time": TimeZone.indian_time,
            "user_source_group_id": user_source_id,
        }

        if offset:
            params["offset"] = offset
            query += " OFFSET %(offset)s"

        params = DataLayerUtils().prepare_sql_params(params)
        result = self.sql_execute_fetch_all(query, params, to_dict=True)

        total_count = result[0]["total"] if result else 0

        return {"transaction_count": total_count, "transaction_list": result}

    @staticmethod
    def get_total_amount_from_transaction(user_source_id, transaction_type, status):
        sql = """
            SELECT SUM(amount)
            FROM lendenapp_transaction
            WHERE user_source_group_id = %(user_source_id)s
            AND type = ANY(%(transaction_type)s)
            AND status = ANY(%(status)s)
        """

        params = {
            "user_source_id": user_source_id,
            "transaction_type": transaction_type,
            "status": status,
        }
        params = DataLayerUtils().prepare_sql_params(params)
        return AccountMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def fetch_withdrawal_list(
        status=TransactionStatus.SCHEDULED,
        txn_type=None,
        source=None,
        from_date=None,
        to_date=None,
        txn_id=None,
        amount_range=None,
        user_name=None,
    ):
        sql = """
               SELECT
                    lc.first_name AS customer_name,
                    lt.amount, 
                    lba.number AS masked_account, 
                    lba.ifsc_code, 
                    TO_CHAR(lt.created_date AT TIME ZONE 'Asia/Kolkata', 'DD Mon YYYY HH24:MI:SS') AS withdrawal_dtm,
                    lt.type, 
                    lt.transaction_id, 
                    lt.details,
                    CASE 
                        WHEN lt.status = %(success_status)s THEN %(completed_status)s 
                        ELSE lt.status 
                    END AS status, 
                    COALESCE(TO_CHAR(lba.cashfree_dtm AT TIME ZONE 'Asia/Kolkata', 'DD Mon YYYY HH24:MI:SS'), '') AS last_cashfree_dtm,
                    ls.source_name, 
                    lba.user_source_group_id,
                    COALESCE(
                        (SELECT poi_name 
                         FROM lendenapp_userkyc 
                         WHERE service_type = %(ckyc_service_type)s 
                           AND user_source_group_id = lusg.id
                         ORDER BY id DESC LIMIT 1),
                        '-'
                    ) AS pan_name,    
                    COALESCE(lba.name, '-') AS account_name
                FROM
                      lendenapp_customuser lc
                JOIN lendenapp_user_source_group lusg ON lc.id = lusg.user_id 
                JOIN lendenapp_account la on la.user_source_group_id = lusg.id
                JOIN lendenapp_bankaccount lba ON la.bank_account_id = lba.id 
                JOIN lendenapp_transaction lt ON lusg.id = lt.user_source_group_id
                JOIN lendenapp_source ls ON ls.id = lusg.source_id

            """

        where_conditions = ["lba.is_active = TRUE AND lba.purpose= 'PRIMARY'"]
        params = {
            "status": (
                status
                if status != TransactionStatus.COMPLETED
                else TransactionStatus.SUCCESS
            )
        }

        if status == TransactionStatus.IN_PROGRESS:
            where_conditions.append(
                """lt.status = %(status)s 
                AND EXISTS (
                    SELECT 1 FROM lendenapp_fmi_withdrawals lfw 
                    WHERE lfw.transaction_id = lt.transaction_id 
                      AND lfw.status = ANY(%(fmi_statuses)s)
                )"""
            )
            params["fmi_statuses"] = [
                FMITransactionStatus.IN_PROGRESS,
                FMITransactionStatus.FAILED,
            ]
        else:
            where_conditions.append(
                """(lt.status = %(status)s 
                OR (lt.status = %(in_progress_status)s 
                    AND EXISTS (
                        SELECT 1 FROM lendenapp_fmi_withdrawals lfw 
                        WHERE lfw.transaction_id = lt.transaction_id 
                          AND lfw.status = ANY(%(fmi_statuses)s)
                    )))"""
            )
            params["in_progress_status"] = TransactionStatus.IN_PROGRESS
            params["fmi_statuses"] = [
                FMITransactionStatus.IN_PROGRESS,
                FMITransactionStatus.FAILED,
            ]
        where_conditions.append("lt.date <= NOW()")

        if txn_type:
            where_conditions.append("lt.type = %(txn_type)s")
            params["txn_type"] = txn_type
        else:
            where_conditions.append("lt.type= ANY(%(txn_type)s)")
            params["txn_type"] = TransactionType.WITHDRAWAL_TRANSACTION_TYPE

        if source:
            where_conditions.append("ls.source_name = %(source)s")
            params["source"] = source

        if txn_id:
            where_conditions.append("lt.transaction_id= ANY(%(txn_id)s)")
            params["txn_id"] = txn_id

        if amount_range:
            amount_ranges = {
                1: "lt.amount <= 500",
                2: "lt.amount BETWEEN 501 AND 5000",
                3: "lt.amount BETWEEN 5001 AND 50000",
                4: "lt.amount BETWEEN 50001 AND 500000",
                5: "lt.amount >= 500001",
            }
            where_conditions.append(amount_ranges[amount_range])

        if user_name:
            where_conditions.append("lc.first_name ILIKE %(user_name)s")
            params["user_name"] = f"%{user_name}%"

        if from_date and to_date:
            where_conditions.append(
                "lt.created_date >= %(from_date)s AND lt.created_date <= %(to_date)s"
            )
            params["from_date"] = f"{from_date} 00:00:00"
            params["to_date"] = f"{to_date} 23:59:59.999"

        sql += " WHERE " + " AND ".join(where_conditions)
        sql += " ORDER BY lt.created_date DESC"

        params["success_status"] = TransactionStatus.SUCCESS
        params["completed_status"] = TransactionStatus.COMPLETED
        params["ckyc_service_type"] = CKYCServiceType.NAME_MATCH

        return AccountMapper().sql_execute_fetch_all(sql, params, to_dict=True)

    @staticmethod
    def update_transaction_status_cppl(
        status, response_id, transaction_id=None, transaction_status=None
    ):
        sql = """
                UPDATE lendenapp_transaction
                SET status = %(status)s, status_date = CURRENT_DATE,
                updated_date = now()
             """

        params = {"status": status}

        conditions = ["response_id = %(response_id)s"]

        params["response_id"] = response_id

        if transaction_id:
            conditions.append("transaction_id <> %(transaction_id)s")
            params["transaction_id"] = transaction_id

        if transaction_status:
            conditions.append("status in %(transaction_status)s")
            params["transaction_status"] = tuple(transaction_status)

        if conditions:
            sql += " WHERE " + " AND ".join(conditions)

        sql += " returning id"

        AccountMapper().sql_execute_fetch_all(sql, params, to_dict=True)

    @staticmethod
    def get_transaction(columns_and_values, for_update=True):
        where_conditions = " AND ".join(
            [f"{column} = %s" for column in columns_and_values.keys()]
        )

        sql = f"""
                        SELECT transaction_id, amount, status, user_source_group_id,
                        type, created_date, description
                        FROM lendenapp_transaction
                        WHERE {where_conditions} 
        """
        params = tuple(columns_and_values.values())

        if for_update:
            sql += " FOR UPDATE NOWAIT "

        return AccountMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def get_account_by_task_id(user_source_group_id, selected_columns=["*"]):
        selected_columns_str = ", ".join(selected_columns)

        sql = f"""
                    SELECT {selected_columns_str}
                    FROM lendenapp_account
                    WHERE user_source_group_id=%(user_source_group_id)s and balance > 0;
                """
        params = {"user_source_group_id": user_source_group_id}

        return AccountMapper().sql_execute_fetch_one(sql, params, to_dict=True)
