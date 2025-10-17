"""
Bank Mapper using BaseDataLayer architecture
Converts the old bank_mapper.py to use the new data layer pattern
"""

from ..base_datalayer import BaseDataLayer
from ..common.constants import AddBankAccountConstant, RPDStatus, BankVerificationStatus
from ..common.utils.datetime_utils import get_current_dtm


class BankMapper(BaseDataLayer):
    """
    Bank Mapper using BaseDataLayer for database operations
    """

    def __init__(self, bank_name=None, db_alias="default"):
        super().__init__(db_alias)
        self.bank_name = bank_name

    def get_entity_name(self):
        """Return the entity name this mapper handles"""
        return "IOS_BANK"

    def get_bank_name_return_id(self):
        bank = {
            "name": self.bank_name
        }
        sql = """select id from lendenapp_bank where name =%(name)s"""
        bank_id = self.sql_execute_fetch_one(sql, bank, index_result=True)

        return bank_id

    @staticmethod
    def add_bank_details(data, is_cashfree=False):
        # Define base columns and values
        columns = [
            '"number"', '"type"', 'ifsc_code', 'bank_id', 'user_id',
            'created_date', 'updated_date', '"name"', 'user_source_group_id',
            'purpose'
        ]

        values = [
            '%(account_number)s', '%(account_type)s', '%(ifsc_code)s',
            '%(bank_id)s',
            '%(user_id)s', '%(created_date)s', '%(updated_date)s',
            '%(full_name)s',
            '%(user_source_group_id)s', '%(purpose)s'
        ]

        # Set timestamp values
        current_time = get_current_dtm()
        data['created_date'] = current_time
        data['updated_date'] = current_time

        # Handle cashfree condition
        if is_cashfree:
            columns.append('cashfree_dtm')
            values.append('%(cashfree_dtm)s')
            data['cashfree_dtm'] = current_time

            columns.append('is_valid_account')
            values.append('%(is_valid_account)s')
            data['is_valid_account'] = True

        if data.get('is_verified') is False:
            columns.append('verification_status')
            values.append('%(verification_status)s')
            data['verification_status'] = BankVerificationStatus.PENDING

        sql = f"""
            INSERT INTO public.lendenapp_bankaccount 
            ({', '.join(columns)}) 
            VALUES 
            ({', '.join(values)}) 
            RETURNING id
        """

        return BankMapper().sql_execute_fetch_one(sql, data, index_result=True)

    @staticmethod
    def update_bank_details(data, is_cashfree=False):
        sql = """
            UPDATE public.lendenapp_bankaccount ba
            SET "type" = %(account_type)s, "name" = %(name)s,
                "number" = %(account_number)s, updated_date = now(),
                ifsc_code = %(ifsc_code)s, bank_id = %(bank_id)s, purpose = %(purpose)s,
                mandate_id = %(mandate_id)s, mandate_status = %(mandate_status)s
        """

        if is_cashfree:
            sql += ", cashfree_dtm = %(cashfree_dtm)s, is_valid_account = %(is_valid_account)s"
            data["cashfree_dtm"] = get_current_dtm()

        sql += """
            FROM lendenapp_account a
            WHERE ba.user_id = %(user_id)s AND ba.id = a.bank_account_id
        """

        if data.get("user_source_group_id"):
            sql += " AND ba.user_source_group_id = %(user_source_group_id)s"

        sql += " RETURNING ba.id"

        return BankMapper().sql_execute_fetch_one(sql, data, index_result=True)

    @staticmethod
    def get_all_banks(search):
        sql = """select name from lendenapp_bank lb"""
        params ={}
        if search:
            sql += """ WHERE name ILIKE %(search)s"""
            params["search"] = "%" + search + "%"
        return BankMapper().sql_execute_fetch_all(sql, params, to_dict=True)

    @staticmethod
    def get_bank_account_details(
            user_source_group_id, user_pk, selected_columns):
        selected_columns_str = ", ".join(selected_columns)

        sql = f"""
                SELECT {selected_columns_str} 
                FROM public.lendenapp_account la
                JOIN public.lendenapp_bankaccount ba 
                ON ba.id =la.bank_account_id
                JOIN public.lendenapp_bank lba ON ba.bank_id = lba.id
                WHERE la.user_source_group_id = %(user_source_group_id)s 
                AND la.user_id=%(user_pk)s
                AND ba.is_active = True;
            """

        data = {
            'user_source_group_id': user_source_group_id,
            'user_pk': user_pk
        }
        return BankMapper().sql_execute_fetch_one(sql, data, to_dict=True)

    @staticmethod
    def check_account_exists(account_number, is_cp=False, ifsc_code=None,exclude_active=False):
        sql = """
                SELECT id, user_id, user_source_group_id, name
                FROM public.lendenapp_bankaccount
                WHERE number = %(account_number)s
            """
        data = {
            'account_number': account_number
        }
        if ifsc_code:
            sql += " AND ifsc_code = %(ifsc_code)s "
            data['ifsc_code'] = ifsc_code

        if not exclude_active:
            sql += " AND is_active = True"

        sql += " ORDER BY id DESC"

        if is_cp:
            return BankMapper().sql_execute_fetch_one(sql, data, to_dict=True)

        return BankMapper().sql_execute_fetch_all(sql, data, to_dict=True)

    @staticmethod
    def get_bank_details(user_id, user_source_id=None, is_mandate=False, mandate_id=None, only_primary=False, fetch_one=False):
        sql = """
               select ifsc_code ,"number" ,lb2."name", type, 
               lb.name as bank_holder, lb.id as bank_account_id, 
               lb.purpose
               """
        if is_mandate:
            sql += """, lb.mandate_id, 
                    coalesce(lb.mandate_status, 'NOT INITIATED') as mandate_status """
        
        sql += """
            from lendenapp_bankaccount lb left join lendenapp_bank lb2 
               on lb.bank_id = lb2.id 
               WHERE user_id = %(user_id)s
               AND lb.is_active = True
            """

        if user_source_id:
            sql += ' AND user_source_group_id = %(user_source_group_id)s'

        if mandate_id:
            sql += ' AND mandate_id = %(mandate_id)s'

        if only_primary:
            sql += ' AND lb.purpose = %(purpose)s'

        params = {
            'user_id': user_id,
            'user_source_group_id': user_source_id,
            'mandate_id': mandate_id,
            'purpose': AddBankAccountConstant.PRIMARY_PURPOSE
        }
        if only_primary or fetch_one:
            return BankMapper().sql_execute_fetch_one(sql, params, to_dict=True)

        return BankMapper().sql_execute_fetch_all(sql, params, to_dict=True)

    @staticmethod
    def add_historical_bank_details(data):
        sql = """INSERT INTO lendenapp_historicalbankaccount (
            id, "name", "number", "type", purpose, ifsc_code, created_date, 
            updated_date, history_date, history_type,
            bank_id, user_id, user_source_group_id) 
            VALUES(%(id)s, %(user_name)s, %(number)s, %(type)s, %(purpose)s, 
            %(ifsc_code)s, now(), now(), now(), '~', %(bank_id)s, 
            %(user_id)s, %(user_source_group_id)s) 
            returning id
        """
        return BankMapper().sql_execute_fetch_one(sql, data, index_result=True)

    def get_or_create_bank(self):
        # Check if the bank already exists, if not, insert and return the ID
        sql = """
            WITH bank_insert AS (
                INSERT INTO lendenapp_bank (name)
                VALUES (%(name)s)
                ON CONFLICT (name) DO NOTHING
                RETURNING id
            )
            SELECT id FROM bank_insert
            UNION
            SELECT id FROM lendenapp_bank WHERE name = %(name)s;
        """

        # Define the bank data to avoid multiple dictionaries
        bank_data = {'name': self.bank_name}

        # Execute query
        bank_id = self.sql_execute_fetch_one(sql, bank_data, index_result=True)

        return bank_id

    @staticmethod
    def get_bank_mandate(columns_and_values, selected_columns=None):
        conditions = f" AND ".join(
            [f"{column} {' = ANY' if isinstance(columns_and_values[column], tuple) else ' ='} %s"for column in columns_and_values.keys()])
        
        if not selected_columns:
            selected_columns = ['*']
        selected_columns_str = ", ".join(selected_columns)

        sql = f"""
            SELECT {selected_columns_str}
            FROM lendenapp_bankaccount lb
            JOIN lendenapp_mandate lm ON lb.mandate_id = lm.id
            WHERE {conditions}
        """
        params = tuple(columns_and_values.values())
        return BankMapper().sql_execute_fetch_one(sql, params, to_dict=True)


    @staticmethod
    def update_all_bank_accounts_to_secondary(user_id, user_source_group_id, bank_id=None):
        sql = """
            UPDATE public.lendenapp_bankaccount
            SET purpose = %(purpose)s,
                updated_date = now()
            WHERE user_id = %(user_id)s
            AND user_source_group_id = %(user_source_group_id)s
        """

        params = {
            'user_id': user_id,
            'user_source_group_id': user_source_group_id,
            'purpose': AddBankAccountConstant.SECONDARY_PURPOSE
        }

        # Add bank_id condition only if it's provided
        if bank_id:
            sql += " AND id <> %(bank_id)s"
            params['bank_id'] = bank_id

        return BankMapper().execute_sql(sql, params)

    @staticmethod
    def count_active_bank_accounts(user_id, user_source_group_id):
        sql = """
            SELECT COUNT(*) as count
            FROM public.lendenapp_bankaccount
            WHERE user_id = %(user_id)s
            AND user_source_group_id = %(user_source_group_id)s
            AND is_active = True
        """
        params = {
            'user_id': user_id,
            'user_source_group_id':user_source_group_id
        }


        result = BankMapper().sql_execute_fetch_one(sql, params, to_dict=True)
        return result['count'] if result else 0

    @staticmethod
    def check_if_mapped_bank(user_source_group_id):
        sql ="""
                SELECT ba.number
                FROM public.lendenapp_bankaccount ba
                JOIN public.lendenapp_account la ON la.bank_account_id = ba.id
                WHERE ba.user_source_group_id = %(user_source_group_id)s
                AND ba.is_active = True;
        """
        params = {
            'user_source_group_id': user_source_group_id
        }
        return BankMapper().sql_execute_fetch_one(sql, params, to_dict=True)


    @staticmethod
    def check_for_rpd_success(user_source_group_id):
        sql ="""
            select rd.verification_id, lb.number,lb.ifsc_code,lb.type,lb.name 
            from reverse_penny_drop rd left join 
           lendenapp_bankaccount lb on rd.bank_account_id=lb.id 
            where rd.status=%(status)s and lb.is_active=false
            and rd.user_source_group_id =%(user_source_group_id)s
            order by rd.id desc
        """
        params={
            'status':RPDStatus.SUCCESS,
            'user_source_group_id':user_source_group_id
        }

        return BankMapper().sql_execute_fetch_one(sql,params, to_dict=True)

    @staticmethod
    def can_cp_update_to_primary(user_source_group_id):
        sql = """
                SELECT CASE 
                    WHEN primary_status_updated_at IS NULL THEN true
                    WHEN primary_status_updated_at::date <= (CURRENT_DATE - INTERVAL '1 days') THEN true
                    ELSE false
                END as update_date
                FROM public.lendenapp_account la
                WHERE la.user_source_group_id = %(user_source_group_id)s
            """
        params = {
            'user_source_group_id': user_source_group_id
        }

        result = BankMapper().sql_execute_fetch_one(sql, params, to_dict=True)
        return result['update_date'] if result else True