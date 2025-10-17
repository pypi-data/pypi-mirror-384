from ..base_datalayer import BaseDataLayer
from ..common.constants import AddBankAccountConstant, MandateStatus
from ..common.utils.datetime_utils import get_current_dtm


class BankMapper(BaseDataLayer):
    def __init__(self, bank_name=None, db_alias="default"):
        super().__init__(db_alias)
        self.bank_name = bank_name

    def get_entity_name(self):
        return "IMS_BANK"

    def get_bank_name_return_id(self):
        bank = {"name": self.bank_name}
        sql = """select id from lendenapp_bank where name =%(name)s"""
        bank_id = self.sql_execute_fetch_one(sql, bank, index_result=True)
        return bank_id

    def get_or_create_bank(self):
        get_sql = "select id from lendenapp_bank where name=%s"
        insert_sql = (
            "INSERT INTO lendenapp_bank(name, created_date, updated_date) "
            "VALUES(%(bank_name)s, %(created_date)s, %(updated_date)s) "
            "returning id"
        )
        bank_id = self.sql_execute_fetch_one(
            get_sql, [self.bank_name], index_result=True
        )

        if not bank_id:
            data = {
                "bank_name": self.bank_name,
                "created_date": get_current_dtm(),
                "updated_date": get_current_dtm(),
            }
            bank_id = self.sql_execute_fetch_one(insert_sql, data, index_result=True)
        return bank_id

    @staticmethod
    def check_account_exists(account_number, bank_name):
        sql = f"""
                    SELECT lba.user_id
                    FROM public.lendenapp_bankaccount AS lba
                    JOIN public.lendenapp_bank AS lb
                    ON lba.bank_id = lb.id
                    WHERE lba.number = %(number)s
                    AND lb.name = %(bank_name)s
                    AND lba.is_active = True;
                """
        data = {"number": account_number, "bank_name": bank_name}
        return BankMapper().sql_execute_fetch_one(sql, data, to_dict=True)

    @staticmethod
    def get_bank_account_details(user_source_group_id, user_pk, selected_columns):
        selected_columns_str = ", ".join(selected_columns)

        sql = f"""
                SELECT {selected_columns_str} 
                FROM lendenapp_bankaccount ba
                JOIN lendenapp_mandate lm ON ba.mandate_id = lm.id
                WHERE ba.user_source_group_id = %(user_source_group_id)s 
                AND ba.user_id=%(user_pk)s
                AND ba.is_active = True;
            """

        data = {"user_source_group_id": user_source_group_id, "user_pk": user_pk}
        return BankMapper().sql_execute_fetch_all(sql, data, to_dict=True)

    @staticmethod
    def count_active_bank_accounts(user_id, user_source_group_id):
        sql = """
            SELECT COUNT(*) as count
            FROM public.lendenapp_bankaccount
            WHERE user_id = %(user_id)s
            AND user_source_group_id = %(user_source_group_id)s
            AND is_active = True
        """
        params = {"user_id": user_id, "user_source_group_id": user_source_group_id}

        result = BankMapper().sql_execute_fetch_one(sql, params, to_dict=True)
        return result["count"] if result else 0

    @staticmethod
    def can_update_to_primary(user_source_group_id, is_cp=False):
        sql = """
            SELECT CASE 
                WHEN primary_status_updated_at IS NULL THEN true
                WHEN primary_status_updated_at::date <= (CURRENT_DATE - CAST(%(interval_str)s AS INTERVAL)) THEN true
                ELSE false
            END as update_date
            FROM public.lendenapp_account la
            WHERE la.user_source_group_id = %(user_source_group_id)s
        """

        days_interval = 1 if is_cp else 7

        params = {
            "user_source_group_id": user_source_group_id,
            "interval_str": f"{days_interval} days",
        }

        result = BankMapper().sql_execute_fetch_one(sql, params, to_dict=True)
        return result["update_date"] if result else True

    @staticmethod
    def update_all_bank_accounts_to_secondary(user_source_group_id, bank_id=None):
        sql = """
            UPDATE public.lendenapp_bankaccount
            SET purpose = %(purpose)s,
                updated_date = now()
            WHERE user_source_group_id = %(user_source_group_id)s
            AND is_active = True
        """

        params = {
            "user_source_group_id": user_source_group_id,
            "purpose": AddBankAccountConstant.SECONDARY_PURPOSE,
        }

        # Add bank_id condition only if it's provided
        if bank_id:
            sql += " AND id <> %(bank_id)s"
            params["bank_id"] = bank_id

        BankMapper().execute_sql(sql, params)

    @staticmethod
    def check_mandate_exists_for_user(user_source_id):
        """
        Check if a successful mandate exists for the given source_id
        """
        sql = """
            SELECT EXISTS (
                SELECT lusg.id
                FROM lendenapp_mandate lm
                JOIN public.lendenapp_user_source_group lusg on lm.user_source_group_id = lusg.id
                WHERE lusg.source_id=7
                AND lm.mandate_status=%(status)s
                AND lusg.id = %(user_source_id)s
            ) as has_mandate
        """
        params = {"status": MandateStatus.SUCCESS, "user_source_id": user_source_id}
        result = BankMapper().sql_execute_fetch_one(sql, params, to_dict=True)
        return result.get("has_mandate", False) if result else False
