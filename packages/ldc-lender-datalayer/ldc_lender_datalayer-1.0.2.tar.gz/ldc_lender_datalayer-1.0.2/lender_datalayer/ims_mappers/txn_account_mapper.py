from ..base_datalayer import BaseDataLayer
from ..common.constants import CancellationExpiryBuffer, TransactionType


class TxnAccountMapper(BaseDataLayer):
    def __init__(self, investor_pk=None, db_alias="default"):
        super().__init__(db_alias)
        self.investor_pk = investor_pk

    def get_entity_name(self):
        return "IMS_TXN_ACCOUNT"

    def insert_txn_account(self, data):
        sql = """
               insert into lendenapp_transaction_amount_tracker (transaction_id, initial_amount, action_amount,
               expiry_dtm, type, user_source_group_id, balance)
               values (%(transaction_id)s, %(initial_amount)s, %(action_amount)s, 
               (((now() AT TIME ZONE 'Asia/Kolkata')::date + interval %(days)s) + interval '23:59:59'),
                %(type)s, %(user_source_group_id)s, %(balance)s ) returning id 
           """

        params = {
            "transaction_id": data.get("transaction_id"),
            "initial_amount": data.get("initial_amount"),
            "action_amount": data.get("action_amount"),
            "type": data["type"] if data.get("type") else TransactionType.ADD_MONEY,
            "user_source_group_id": data["user_source_group_id"],
            "balance": data.get("balance"),
            "days": (
                data["days"]
                if data.get("days")
                else CancellationExpiryBuffer.INTERVAL_ONE_DAY
            ),
        }

        return self.sql_execute_fetch_one(sql, params, index_result=True)

    @staticmethod
    def fetch_available_txn(usg_id):
        # we are not checking the expiry dtm here because we dont want fund to be hold
        query = """
                    SELECT id, balance 
                    FROM lendenapp_transaction_amount_tracker
                    WHERE user_source_group_id = %(usg_id)s AND balance > 0
                    ORDER BY id ASC
                    FOR UPDATE;
            """

        params = {"usg_id": usg_id}

        return TxnAccountMapper().sql_execute_fetch_all(query, params, to_dict=True)

    @staticmethod
    def update_fully_txn_acc_records(txn_acc_id, txn_type, reversal_txn_id=None):

        sql = """
                UPDATE lendenapp_transaction_amount_tracker
                SET balance = 0, action_amount = balance,
                type = %(type)s, updated_date = now()
            """

        params = {"id": txn_acc_id, "type": txn_type}

        if reversal_txn_id:
            sql += ", reversal_txn_id = %(reversal_txn_id)s"
            params["reversal_txn_id"] = reversal_txn_id

        sql += " WHERE id = %(id)s RETURNING id"

        return TxnAccountMapper().sql_execute_fetch_one(sql, params, index_result=True)

    @staticmethod
    def update_partially_txn_acc_records(txn_acc_id, action_amount, txn_type):
        sql = """
               UPDATE lendenapp_transaction_amount_tracker
                SET balance = balance - %(action_amount)s, type = %(type)s,
                action_amount = %(action_amount)s, updated_date = now()
                WHERE id = %(id)s AND balance >= %(action_amount)s
            """

        params = {"id": txn_acc_id, "type": txn_type, "action_amount": action_amount}

        TxnAccountMapper().execute_sql(sql, params)

    @staticmethod
    def get_user_available_balance(usg_id, for_update=None):
        sub_query = """
                select balance
                    from lendenapp_transaction_amount_tracker ltat  
                    where user_source_group_id = %(usg_id)s
                    and reversal_txn_id is null
                    and balance>0 
        """
        if for_update:
            sub_query += " FOR UPDATE NOWAIT"

        sql = f"SELECT COALESCE(SUM(balance), 0) FROM ({sub_query}) AS subquery"

        params = {"usg_id": usg_id}

        return TxnAccountMapper().sql_execute_fetch_one(sql, params, index_result=True)

    @staticmethod
    def fetch_available_balance(usg_id):
        query = """
                    SELECT id
                    FROM lendenapp_transaction_amount_tracker
                    WHERE user_source_group_id = %(usg_id)s AND balance >= 0
                    ORDER BY id DESC
                    FOR UPDATE;
            """

        params = {"usg_id": usg_id}

        return TxnAccountMapper().sql_execute_fetch_one(
            query, params, index_result=True
        )

    @staticmethod
    def credit_txn_record(txn_acc_id, action_amount):
        sql = """
               UPDATE lendenapp_transaction_amount_tracker
                SET balance = balance + %(action_amount)s,
                action_amount = %(action_amount)s, updated_date = now()
                WHERE id = %(id)s 
            """

        params = {"id": txn_acc_id, "action_amount": action_amount}

        TxnAccountMapper().execute_sql(sql, params)
