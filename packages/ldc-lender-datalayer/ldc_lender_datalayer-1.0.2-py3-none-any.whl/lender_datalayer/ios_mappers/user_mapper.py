import ast
import logging
from datetime import timedelta

from django.conf import settings

from ..base_datalayer import BaseDataLayer, DataLayerUtils
from ..common.constants import (AccountStatus, AddressConstants, AppRating, ChecklistStep, ConsentData,
                              FMPPInvestmentType, GroupName, HOFMember, InvestorSource, KmiCallBackStatus, KMIServices,
                              KYCConstant, KYCSource, NMIConstants, RMReference, SchemeStatus, ServerType,
                              TransactionStatus, UserGroup, UserGroupSourceStatus)
from ..common.utils.datetime_utils import (get_current_date, get_current_dtm, get_datetime_as_string,
                                         get_todays_date_in_ist)
from ..common.utils.decorators import data_dict_to_string_wrapper
from ..common.utils.encryption_utils import EncryptDecryptAES256
from ..common.utils.random_value_generator_utils import generate_otp_key, generate_token_for_mono

logger = logging.getLogger("normal")
encryption = EncryptDecryptAES256()


class UserMapper(BaseDataLayer):

    def __init__(self, user_pk=None, user_source_id=None, db_alias="default"):
        super().__init__(db_alias)
        self.user_pk = user_pk
        self.user_source_id = user_source_id

    def get_entity_name(self):
        """Return the entity name this mapper handles"""
        return "IOS_USER"

    @staticmethod
    def get_user_credentials(email):
        query = "SELECT id, password, first_name, encoded_email FROM lendenapp_customuser WHERE encoded_email = %(email)s"
        params = {"email": email}
        return UserMapper().sql_execute_fetch_one(query, params, to_dict=True)

    @staticmethod
    def get_auth_groups(user_id):
        query = """select name from auth_group ag 
                    inner join lendenapp_customuser_groups lcg on lcg.group_id = ag.id
                    inner join lendenapp_customuser lc on lc.id = lcg.customuser_id
                    where lc.id = %(user_id)s;"""

        params = {"user_id": user_id}
        all_groups = UserMapper().sql_execute_fetch_all(query, params, to_dict=True)

        return [group["name"] for group in all_groups]

    def get_customuser_type(self):
        return self.sql_execute_fetch_one(
            """select type from lendenapp_customuser
         where id =%(user_pk)s""",
            {"user_pk": self.user_pk},
            index_result=True,
        )

    def get_customuser_pan(self):
        return self.sql_execute_fetch_one(
            """select encoded_pan from 
        lendenapp_customuser where id =%(user_pk)s""",
            {"user_pk": self.user_pk},
            index_result=True,
        )

    def get_customuser_first_name(self):
        return self.sql_execute_fetch_one(
            """select first_name from 
        lendenapp_customuser where id =%(user_pk)s""",
            {"user_pk": self.user_pk},
            index_result=True,
        )

    def get_check_list(self, is_cp=False):
        query = """select checklist from lendenapp_task lt where """
        query += (
            "created_by_id = %(user_pk)s"
            if is_cp
            else "user_source_group_id = %(user_source_group_id)s"
        )

        params = {"user_source_group_id": self.user_source_id, "user_pk": self.user_pk}
        try:
            result = self.sql_execute_fetch_one(query, params, index_result=True)
            if isinstance(result, str):
                return ast.literal_eval(result)
            return result
        except Exception:
            return {}

    def check_if_completed(self, step_name, is_cp=False):
        checklist = self.get_check_list(is_cp)
        if checklist:
            return step_name in checklist.get("completed_steps")
        return False

    def user_with_source_exists(self, params):
        query = """
                    SELECT lc.encoded_mobile, lc.encoded_email, lc.encoded_pan
                    FROM lendenapp_customuser lc
                    INNER JOIN lendenapp_user_source_group lusg 
                        ON lusg.user_id = lc.id
                    INNER JOIN lendenapp_source ls
                        ON ls.id = lusg.source_id
                    WHERE ls.source_name = %(partner_code)s 
                        AND lc.mobile_number = %(mobile_number)s
                """
        return self.sql_execute_fetch_one(query, params, to_dict=True)

    def update_check_list(self, add_step, is_cp=False):
        if add_step == ChecklistStep.LIVE_KYC:
            kyc_tracker_data = self.get_data(
                table_name="lendenapp_userkyctracker",
                columns_and_values={
                    "user_source_group_id": self.user_source_id,
                    "is_latest_kyc": True,
                },
                selected_columns=["id"],
            )
            if kyc_tracker_data:
                updated_data = {
                    "status": KYCConstant.SUCCESS,
                    "next_kyc_date": get_current_date() + timedelta(days=730),
                    "risk_type": KYCConstant.RISK_HIGH,
                    "next_due_diligence_date": (
                        get_current_date() + timedelta(days=180)
                    ),
                }
                self.update_data(
                    table_name="lendenapp_userkyctracker",
                    condition={"id": kyc_tracker_data["id"]},
                    data=updated_data,
                )
            else:
                kyc_data = {
                    "status": KYCConstant.SUCCESS,
                    "kyc_type": ChecklistStep.LIVE_KYC,
                    "kyc_source": KYCSource.MANUAL_SOURCE,
                    "is_latest_kyc": True,
                    "user_source_group_id": self.user_source_id,
                    "user_id": self.user_pk,
                    "next_kyc_date": get_current_date() + timedelta(days=730),
                    "risk_type": KYCConstant.RISK_HIGH,
                    "next_due_diligence_date": (
                        get_current_date() + timedelta(days=180)
                    ),
                }
                self.insert_data(table_name="lendenapp_userkyctracker", data=kyc_data)

        data = self.get_check_list(is_cp)
        if not data:
            data["completed_steps"] = [add_step]
        else:
            data["completed_steps"].append(add_step)
        data["last_updated"] = get_datetime_as_string()
        data["account_status"] = self.get_account_status()

        query = f"""
                    update lendenapp_task set 
                        checklist=%(updated_data)s,
                        updated_date = now()
                    where {
                        "created_by_id=%(user_pk)s" if is_cp 
                        else "user_source_group_id=%(user_source_group_id)s"
                    }
                    RETURNING id
                """

        params = {
            "updated_data": str(data),
            "user_source_group_id": self.user_source_id,
            "user_pk": self.user_pk,
        }
        result = self.sql_execute_fetch_one(query, params, index_result=True)
        if result:
            return True

        return False

    def get_account_status(self):
        sql = """
            SELECT
                status
            FROM lendenapp_account
            WHERE user_source_group_id=%(user_source_group_id)s
            """
        params = {"user_source_group_id": self.user_source_id}
        return self.sql_execute_fetch_one(sql, params, index_result=True)

    def update_user_data(self, user_data):
        encryption.update_encoded_value("pan", user_data, "encoded_pan")
        encryption.update_encoded_value("aadhar", user_data, "encoded_aadhar")

        update_data = [f"{key}=%({key})s" for key in user_data.keys()]
        query = (
            """
              UPDATE public.lendenapp_customuser
              SET """
            + ",".join(update_data)
            + """
              WHERE id=%(user_pk)s
              RETURNING id;
              """
        )
        pk_map = {"user_pk": self.user_pk}
        if self.sql_execute_fetch_one(
            query, {**user_data, **pk_map}, index_result=True
        ):
            return True
        return False

    @staticmethod
    def check_if_pan_exist(encoded_pan, encoded_mobile=None):
        query = (
            "select id, encoded_mobile, encoded_email from lendenapp_customuser "
            "where encoded_pan=%(encoded_pan)s"
        )

        params = {"encoded_pan": encoded_pan}

        if encoded_mobile:
            query += " AND encoded_mobile=%(encoded_mobile)s"
            params["encoded_mobile"] = encoded_mobile

        return UserMapper().sql_execute_fetch_one(query, params, to_dict=True)

    def update_kmi(self, tracking_id, kyc_consent, kyc_status=None):
        query = """INSERT INTO lendenapp_userkyc (user_id, tracking_id, 
                user_source_group_id, user_kyc_consent, service_type,status) 
                VALUES(%(user_id)s, %(tracking_id)s, %(user_source_group_id)s, 
                %(user_kyc_consent)s, %(service_type)s,
                 %(status)s) returning id"""
        params = {
            "user_id": self.user_pk,
            "tracking_id": tracking_id,
            "user_source_group_id": self.user_source_id,
            "user_kyc_consent": kyc_consent,
            "service_type": KMIServices.INITIATE_KYC,
            "status": kyc_status or KmiCallBackStatus.INITIATED,
        }
        if self.execute_sql(query, params, return_rows_count=True):
            return True
        return False

    @staticmethod
    def get_group_id(group_name=GroupName.LENDER):
        sql = "SELECT id FROM auth_group WHERE name=%s"
        return UserMapper().sql_execute_fetch_one(
            sql, [group_name], index_result=True
        )

    def get_user(self, encoded_email=None, encoded_mobile=None):
        sql = """
                select id, user_id, email, pan, mobile_number, encoded_pan, 
                encoded_mobile, encoded_email, is_active, first_name, dob, 
                ucic_code, gross_annual_income, gender,
                email_verification, mnrl_status
                from lendenapp_customuser lc 
                WHERE 
              """
        if self.user_pk:
            params = [self.user_pk]
            sql += "lc.id=%s"
        elif encoded_mobile:
            params = [encoded_mobile]
            sql += "lc.encoded_mobile=%s"
        elif encoded_email:
            params = [encoded_email]
            sql += "lc.encoded_email=%s"
        else:
            logger.exception("Unknown param for get_user")
            raise Exception("Unknown param for get_user")
        return self.sql_execute_fetch_one(sql, params, to_dict=True)

    def insert_into_custom_user(self, user_data):
        columns = ", ".join(user_data.keys())
        values = ", ".join(["%s"] * len(user_data))

        sql = (
            f"INSERT INTO lendenapp_customuser "
            f"({columns}) VALUES ({values}) RETURNING id"
        )

        self.user_pk = self.sql_execute_fetch_one(
            sql, list(user_data.values()), index_result=True
        )
        return self.user_pk

    def insert_user_into_user_group(self, group_name=GroupName.LENDER):
        if group_name == GroupName.LENDER:
            group_id = UserGroup.LENDER
        else:
            group_id = self.get_group_id(group_name=group_name)

        sql = """
            INSERT INTO 
                lendenapp_customuser_groups
                (
                    customuser_id, 
                    group_id
                ) 
            VALUES(%s, %s)
            RETURNING id
            """

        return self.sql_execute_fetch_one(
            sql, [self.user_pk, group_id], index_result=True
        )

    @staticmethod
    def insert_into_task(task_params):
        columns = ", ".join(task_params.keys())
        values = ", ".join(["%s"] * len(task_params))
        sql = (
            "INSERT INTO lendenapp_task " f"({columns}) VALUES ({values}) RETURNING id"
        )

        return UserMapper().sql_execute_fetch_one(
            sql, list(task_params.values()), index_result=True
        )

    @staticmethod
    def insert_into_bank_account(account_data):
        columns = ", ".join(account_data.keys())
        values = ", ".join(["%s"] * len(account_data))

        sql = (
            f"INSERT INTO lendenapp_account "
            f"({columns}) VALUES ({values}) RETURNING id"
        )

        return UserMapper().sql_execute_fetch_one(
            sql, list(account_data.values()), index_result=True
        )

    def get_user_token(self):
        sql = "SELECT key FROM authtoken_token WHERE user_id=%s"
        token = self.sql_execute_fetch_one(sql, [self.user_pk], index_result=True)
        if not token:
            insert_sql = "INSERT INTO authtoken_token(user_id, key, created)\
                VALUES(%(user_id)s, %(key)s, %(created)s) \
                RETURNING key"
            params = {
                "user_id": self.user_pk,
                "key": generate_token_for_mono(),
                "created": get_current_dtm(),
            }
            token = self.sql_execute_fetch_one(insert_sql, params, index_result=True)

        return token

    @staticmethod
    def insert_into_application_info(info):
        columns = ", ".join(info.keys())
        values = ", ".join(["%s"] * len(info))

        sql = (
            f"INSERT INTO lendenapp_applicationinfo "
            f"({columns}) VALUES ({values}) RETURNING id"
        )

        return UserMapper().sql_execute_fetch_one(
            sql, list(info.values()), index_result=True
        )

    @staticmethod
    def insert_timeline(data):
        columns = ", ".join(data.keys())
        values = ", ".join(["%s"] * len(data))

        sql = (
            f"INSERT INTO lendenapp_timeline "
            f"({columns}) VALUES ({values}) RETURNING id"
        )

        return UserMapper().sql_execute_fetch_one(
            sql, list(data.values()), index_result=True
        )

    @staticmethod
    def get_otp_by_mobile_number(mobile_number):
        sql = """
            SELECT key
            FROM lendenapp_userotp
            WHERE mobile_number = %s
        """
        return UserMapper().sql_execute_fetch_one(
            sql, [mobile_number], index_result=True
        )

    @staticmethod
    def create_otp(mobile_number):
        sql = """
            INSERT INTO lendenapp_userotp(mobile_number, key)
            VALUES (%s, %s)
            RETURNING key
        """
        if (
            settings.SERVER_TYPE == ServerType.PRODUCTION
            and mobile_number in settings.BYPASS_ASSETS_LIST
        ):
            params = (mobile_number, "656590")
        else:
            params = (mobile_number, generate_otp_key())
        return UserMapper().sql_execute_fetch_one(sql, params, index_result=True)

    @staticmethod
    def delete_otp_by_mobile_number(mobile_number):
        sql = """
            DELETE
            FROM lendenapp_userotp
            WHERE mobile_number = %(mobile_number)s
        """
        UserMapper().execute_sql(sql=sql, params=[mobile_number])

    @staticmethod
    def is_utility_active(utility_name):
        sql = """
            SELECT is_active 
            FROM lendenapp_utilitypreferences
            WHERE utility_name = %s;
        """
        return UserMapper().sql_execute_fetch_one(
            sql, params=[utility_name], index_result=True
        )

    @staticmethod
    def get_source_id_from_source(source):
        sql = """select id from lendenapp_source ls where 
        source_name =%(source)s """
        return UserMapper().sql_execute_fetch_one(
            sql, {"source": source}, to_dict=True
        )

    @staticmethod
    def check_user_data_exist(user_data):
        sql = """select exists (
                select 1 from lendenapp_customuser lc where 
                encoded_mobile = %(encoded_mobile)s or
                encoded_email = %(encoded_email)s
                )"""

        params = {
            "encoded_mobile": user_data["encoded_mobile"],
            "encoded_email": user_data["encoded_email"],
        }
        return UserMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def validate_pin_code(pincode):
        sql = """select exists (
                select 1 from lendenapp_pincode_state_master lp where 
                pincode =%(pincode)s
                )"""
        result = UserMapper().sql_execute_fetch_one(
            sql, {"pincode": pincode}, index_result=True
        )
        return result

    @staticmethod
    def insert_into_thirdparty_hyperverge(user_data):
        columns = ", ".join(user_data.keys())
        values = ", ".join(["%s"] * len(user_data))

        sql = (
            f"INSERT INTO lendenapp_thirdpartydatahyperverge "
            f"({columns}) VALUES ({values}) RETURNING id"
        )

        return UserMapper().sql_execute_fetch_one(
            sql, list(user_data.values()), index_result=True
        )

    def update_account_status_based_on_user_source_id(self, number, account_status):
        sql = """
            update lendenapp_account set status=%(account_status)s,
            listed_date=%(listed_date)s, 
            number=CASE WHEN number IS NULL THEN %(number)s ELSE number END,
            updated_date=now()
            where user_source_group_id=%(user_source_group_id)s
            and status = %(open_status)s
            returning id
        """
        params = {
            "user_source_group_id": self.user_source_id,
            "account_status": account_status,
            "listed_date": get_todays_date_in_ist(),
            "number": number,
            "open_status": AccountStatus.OPEN,
        }
        return self.sql_execute_fetch_one(sql, params, index_result=True)

    def get_customuser_fields_by_pk(self, fields):
        fields_name = ", ".join(fields)
        query = f"""
                SELECT {fields_name} FROM lendenapp_customuser lc 
                WHERE lc.id = %s"""

        return self.sql_execute_fetch_one(query, [self.user_pk], to_dict=True)

    def get_account_details_checklist(self):
        sql = f""" SELECT la.status, lusg.status as user_activity_status,
            la.number AS account_number, 
            la.balance AS account_balance, 
            la.user_source_group_id, 
            lt.checklist AS check_list, 
            la.bank_account_id, lusg.expiry_date,
            EXISTS (
                SELECT 1 
                FROM lendenapp_transaction txn 
                WHERE txn.type = 'ADD MONEY' and txn.status='SUCCESS'
                AND txn.user_source_group_id = la.user_source_group_id
                LIMIT 1
            ) AS enable_support
        FROM lendenapp_account la
        JOIN lendenapp_task lt ON la.user_source_group_id = lt.user_source_group_id
        JOIN lendenapp_user_source_group lusg on la.user_source_group_id = lusg.id
        WHERE la.user_source_group_id=%(user_source_group_id)s"""

        params = {"user_source_group_id": self.user_source_id}
        return self.sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def get_customuser_fields_by_user_id(fields, user_id):
        fields_name = ", ".join(fields)
        query = f"""
                    SELECT {fields_name} FROM lendenapp_customuser lc 
                    WHERE lc.user_id = %s"""

        return UserMapper().sql_execute_fetch_one(query, [user_id], to_dict=True)

    @staticmethod
    def get_user_basic_info(column, value, selected_columns="*"):
        query = f"""
                SELECT {selected_columns}
                FROM lendenapp_customuser
                WHERE {column} = %(value)s
            """

        params = {"value": value}

        user_data = UserMapper().sql_execute_fetch_one(query, params, to_dict=True)
        return user_data if user_data else None

    def insert_user_consent_log(self, params):
        sql = """
            INSERT INTO
                lendenapp_userconsentlog
            (consent_type, consent_value, remark, user_id,
            user_source_group_id)
            VALUES
            (%(consent_type)s, %(consent_value)s, %(remark)s, %(user_id)s,
            %(user_source_group_id)s) RETURNING id    
        """
        params["user_source_group_id"] = self.user_source_id
        params["user_id"] = self.user_pk
        return self.execute_sql(sql, params=params, return_rows_count=True)

    def update_account_bank_account_id(self, bank_id):
        sql = """
            update lendenapp_account set 
            bank_account_id=%(bank_id)s
            where user_source_group_id=%(user_source_group_id)s;  
        """
        params = {"bank_id": bank_id, "user_source_group_id": self.user_source_id}
        self.execute_sql(sql, params)

    def get_user_group(self):
        sql = """
             select group_id from lendenapp_customuser_groups lcg 
             where customuser_id = %(customuser_id)s; 
            """
        params = {"customuser_id": self.user_pk}
        return self.sql_execute_fetch_one(sql, params, index_result=True)

    def get_user_info_from_dedupe(self, source_group):
        encoded_pan = self.get_customuser_pan()
        pan = encryption.decrypt_data(encoded_pan)
        sql = """
            select ipo.principal_outstanding ,is_networth_uploaded from 
            dedupe.investor_principal_outstanding ipo left join 
            dedupe."user" u on u.id =ipo.user_id  where source_id =%(source)s 
            and pan =%(pan)s
            """
        params = {"pan": pan, "source": source_group}
        result = self.sql_execute_fetch_one(sql, params, to_dict=True)
        if result:
            return result["principal_outstanding"], result["is_networth_uploaded"]
        return 0, False

    def get_user_address(self):
        sql = """
        SELECT location, landmark, pin, city, state, country
        FROM lendenapp_address
        WHERE user_source_group_id = %(user_source_group_id)s 
        AND (type = %(communication_type)s OR type = %(permanent_type)s);
        """

        params = {
            "user_source_group_id": self.user_source_id,
            "communication_type": AddressConstants.COMMUNICATION_TYPE,
            "permanent_type": AddressConstants.PERMANENT_TYPE,
        }

        return self.sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def get_user_details(columns_and_values, selected_cols, fetch_one=False):
        conditions = " AND ".join(
            [f"{column} = %s" for column in columns_and_values.keys()]
        )

        sql = f"""
            SELECT {selected_cols} 
                FROM lendenapp_customuser lc
                left JOIN lendenapp_user_source_group lusg ON lusg.user_id=lc.id
                left JOIN lendenapp_source ls ON ls.id=lusg.source_id
                left JOIN lendenapp_account la on la.user_source_group_id=lusg.id
                left JOIN lendenapp_userkyctracker lukt on lukt.user_source_group_id=lusg.id
                and lukt.status = 'SUCCESS'
                and lukt.is_latest_kyc = true
            WHERE {conditions}
            ORDER BY lusg.created_at;
        """

        params = tuple(columns_and_values.values())

        if fetch_one:
            return UserMapper().sql_execute_fetch_one(sql, params, to_dict=True)

        return UserMapper().sql_execute_fetch_all(sql, params, to_dict=True)

    @staticmethod
    def fetch_customuser_details_configurable(
        selected_columns,
        filter_map,
        logical_operator,
    ):
        """
        selected_columns = ['name', 'mobile', 'email']
        filter_map = {
            'email': 'example@example.com'
            'number': '123456789'
        }
        logical_operator = "and" / "or"
        """
        selected_columns_str = ", ".join(selected_columns)

        filter_conditions = f" {logical_operator} ".join(
            [f"{column} = %({column})s" for column in filter_map.keys()]
        )
        params = {column: value for column, value in filter_map.items()}

        sql = f"""
                SELECT {selected_columns_str} FROM lendenapp_customuser lc
                WHERE {filter_conditions}
            """

        return UserMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    def get_account_details_checklist_v2(self):
        sql = f""" 
                SELECT la.status, la.number as account_number, 
                la.balance as account_balance, la.user_source_group_id, 
                lt.checklist as check_list, lusg.status as user_status 
                FROM lendenapp_account la join lendenapp_task lt 
                ON la.user_source_group_id = lt.user_source_group_id 
                JOIN lendenapp_user_source_group lusg 
                ON lusg.id = la.user_source_group_id      
                WHERE la.user_source_group_id=%(user_source_group_id)s 
            """

        params = {"user_source_group_id": self.user_source_id}
        return self.sql_execute_fetch_one(sql, params, to_dict=True)

    def get_account_notification(self):
        sql = """SELECT status, COUNT(*)
                    FROM lendenapp_notification
                    WHERE user_source_group_id = %(user_source_group_id)s
                    GROUP BY status;
            """
        params = {"user_source_group_id": self.user_source_id}
        return self.sql_execute_fetch_all(sql, params, to_dict=True)

    @staticmethod
    def get_user_task_data_by_mobile_number_cp_id(
        inv_col, inv_val, cp_col, cp_val, selected_columns=None
    ):
        if not selected_columns:
            selected_columns = ["*"]  # Select all columns by default

        selected_columns_str = ", ".join(selected_columns)

        sql = f"""
                select {selected_columns_str} from lendenapp_user_source_group lusg 
                join lendenapp_customuser lc on
                lc.id = lusg.user_id 
                join lendenapp_channelpartner lc2 on
                lc2.id = lusg.channel_partner_id
                join lendenapp_task lt on 
                lt.user_source_group_id = lusg.id
                join lendenapp_source ls on lusg.source_id = ls.id
                where lusg.group_id = %(user_group)s
                and lc.{inv_col} = %(inv_val)s 
                and lc2.{cp_col} = %(cp_val)s
        """
        params = {"inv_val": inv_val, "cp_val": cp_val, "user_group": UserGroup.LENDER}
        return UserMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def get_cp_user(referred_id):
        sql = """
        SELECT source from lendenapp_customuser
        where id = %(referred_id)s;
        """
        params = {"referred_id": referred_id}
        return UserMapper().sql_execute_fetch_one(sql, params, index_result=True)

    @staticmethod
    def insert_into_userkyc_table(kyc_data):
        columns = ", ".join(kyc_data.keys())
        values = ", ".join(["%s"] * len(kyc_data))

        sql = (
            f"INSERT INTO lendenapp_userkyc "
            f"({columns}) VALUES ({values}) RETURNING id"
        )

        return UserMapper().sql_execute_fetch_one(
            sql, list(kyc_data.values()), index_result=True
        )

    @staticmethod
    def insert_into_ckycthirdpartydata(ckycthirdpartydata):
        columns = ", ".join(ckycthirdpartydata.keys())
        values = ", ".join(["%s"] * len(ckycthirdpartydata))

        sql = (
            f"INSERT INTO lendenapp_ckycthirdpartydata "
            f"({columns}) VALUES ({values}) RETURNING id"
        )

        return UserMapper().sql_execute_fetch_one(
            sql, list(ckycthirdpartydata.values()), index_result=True
        )

    @staticmethod
    def get_cp_user_token(cp_id):
        sql = """
                SELECT key FROM authtoken_token at2
                join lendenapp_channelpartner lc on lc.user_id = at2.user_id 
                WHERE lc.partner_id = %s
              """
        token = UserMapper().sql_execute_fetch_one(sql, [cp_id], index_result=True)
        return token

    @staticmethod
    def get_cp_details(cp_user_pk, selected_col="*"):
        selected_col_str = ", ".join(selected_col)
        sql = f"""
               SELECT {selected_col_str} FROM lendenapp_channelpartner 
               WHERE user_id = %s
             """
        token = UserMapper().sql_execute_fetch_one(
            sql, [cp_user_pk], index_result=True
        )
        return token

    def get_user_group_by_user(self):
        sql = """
            SELECT 
                ag.name 
            FROM lendenapp_customuser_groups lcg 
            INNER JOIN auth_group ag ON lcg.group_id=ag.id
            WHERE lcg.customuser_id=%(customuser_id)s
        """
        params = {"customuser_id": self.user_pk}
        return self.sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def get_user_detail(column, value, table, selected_column):
        selected_columns_str = ", ".join(selected_column)
        query = f"""select {selected_columns_str} from {table}
                            where {column} = %(value)s """
        params = {"value": value}
        return UserMapper().sql_execute_fetch_one(query, params, to_dict=True)

    @staticmethod
    def update_address_data(address_data, condition):
        update_data = ", ".join([f"{key} = %({key})s" for key in address_data.keys()])
        filter_data = " AND ".join([f"{key} = %({key})s" for key in condition.keys()])
        sql = f"""
                        UPDATE lendenapp_address
                        SET {update_data}
                        WHERE {filter_data}
                        RETURNING id;
                    """
        params = {**condition, **address_data}
        return UserMapper().sql_execute_fetch_one(sql, params, index_result=True)

    @staticmethod
    def insert_address(address_data):
        columns = ", ".join(address_data.keys())
        values = ", ".join(["%s"] * len(address_data))

        sql = (
            f"INSERT INTO lendenapp_address "
            f"({columns}) VALUES ({values}) RETURNING id"
        )

        return UserMapper().sql_execute_fetch_one(
            sql, list(address_data.values()), index_result=True
        )

    @staticmethod
    def get_details_from_address_table(columns_and_values, selected_columns=["*"]):
        conditions = " AND ".join(
            [f"{column} = %s" for column in columns_and_values.keys()]
        )

        selected_columns_str = ", ".join(selected_columns)

        sql = f"""
                                    SELECT {selected_columns_str}
                                    FROM lendenapp_address
                                    WHERE {conditions}
                                """

        params = tuple(columns_and_values.values())

        return UserMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def update_custom_user(table_name, data, condition):

        update_data = ", ".join([f"{key} = %({key})s" for key in data.keys()])
        filter_data = " AND ".join([f"{key} = %({key})s" for key in condition.keys()])

        sql = f"""
                   UPDATE {table_name}
                   SET {update_data}
                   WHERE {filter_data};
              """
        params = {**condition, **data}
        UserMapper().execute_sql(sql, params)

    @staticmethod
    def get_data(
        table_name,
        columns_and_values,
        selected_columns=["*"],
        logical_operator="AND",
        all_result=False,
        order_by=None,
        desc_order=False,
        for_update=False,
    ):
        conditions = []
        params = {}
        param_count = 1

        for column, value in columns_and_values.items():
            param_name = f"param_{param_count}"
            if isinstance(value, (list, tuple)):
                # Handle array parameters properly
                if any(isinstance(x, (list, tuple)) for x in value):
                    # Nested arrays need special handling
                    conditions.append(f"{column} = ANY(%({param_name})s::text[])")
                else:
                    # Regular arrays
                    conditions.append(f"{column} = ANY(%({param_name})s)")
                params[param_name] = list(value)
            else:
                conditions.append(f"{column} = %({param_name})s")
                params[param_name] = value
            param_count += 1

        conditions_str = f" {logical_operator} ".join(conditions)
        selected_columns_str = ", ".join(selected_columns)

        sql = f"""
            SELECT {selected_columns_str}
            FROM {table_name}
            WHERE {conditions_str}
        """

        if order_by:
            sql += f" ORDER BY {order_by}"
            if desc_order:
                sql += " DESC"
        if for_update:
            sql += " FOR UPDATE NOWAIT "

        if all_result:
            return UserMapper().sql_execute_fetch_all(sql, params, to_dict=True)
        return UserMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def insert_data(table_name, data):
        columns = ", ".join(data.keys())
        values = ", ".join(["%s"] * len(data))

        sql = f"INSERT INTO {table_name} " f"({columns}) VALUES ({values}) RETURNING id"

        return UserMapper().sql_execute_fetch_one(
            sql, list(data.values()), index_result=True
        )

    @staticmethod
    def update_data(table_name, data, condition):
        update_data = ", ".join([f"{key} = %({key})s" for key in data.keys()])
        filter_data = " AND ".join([f"{key} = %({key})s" for key in condition.keys()])
        sql = f"""
                            UPDATE {table_name}
                            SET {update_data}
                            WHERE {filter_data}
                            RETURNING id;
                        """
        params = {**condition, **data}
        return UserMapper().sql_execute_fetch_one(sql, params, index_result=True)

    @staticmethod
    def update_data_v2(
        table_name,
        data,
        condition,
        returning="id",
        fetch_all=False,
        fetch_one_dict=False,
    ):
        update_data = []
        filter_data = []
        params = {}

        # Process SET clause parameters (data)
        for key, value in data.items():
            param_name = f"set_{key}"
            update_data.append(f"{key} = %({param_name})s")
            params[param_name] = value

        # Process WHERE clause parameters (condition)
        for key, value in condition.items():
            param_name = f"where_{key}"
            if isinstance(value, (list, tuple)):
                filter_data.append(f"{key} = ANY(%({param_name})s)")
                # Ensure single values are converted to lists
                params[param_name] = list(value) if isinstance(value, tuple) else value
            else:
                filter_data.append(f"{key} = %({param_name})s")
                params[param_name] = value

        sql = f"""
            UPDATE {table_name}
            SET {', '.join(update_data)}
            WHERE {' AND '.join(filter_data)}
            RETURNING {returning};
        """

        if fetch_all:
            return UserMapper().sql_execute_fetch_all(sql, params, to_dict=True)
        elif fetch_one_dict:
            return UserMapper().sql_execute_fetch_one(sql, params, to_dict=True)

        return UserMapper().sql_execute_fetch_one(sql, params, index_result=True)

    @data_dict_to_string_wrapper("query_conditions", "case_check")
    def get_user_data(self, query_conditions, columns="*", case_check=None):
        columns = ",".join(columns) if columns != "*" else columns
        sql = f"""
                select {columns} from lendenapp_customuser lc 
                where {query_conditions['query_conditions_string']}
            """
        user_data = self.sql_execute_fetch_one(
            sql, params=query_conditions["params"], to_dict=True
        )
        return user_data

    def check_if_lender(self):
        lender_id = UserGroup.LENDER
        sql = """
                select id from lendenapp_customuser_groups lcg  
                where group_id =%(group_id)s and customuser_id=%(user_pk)s 
            """
        params = {"group_id": lender_id, "user_pk": self.user_pk}
        return self.sql_execute_fetch_one(sql, params, index_result=True)

    @staticmethod
    def fetch_thirdparty_cashfree_data(action, user_id, user_source_id, status):
        sql = """
            SELECT json_request, json_response, status FROM 
            lendenapp_thirdpartycashfree WHERE action=%(action)s AND
            user_id=%(user_id)s AND user_source_group_id=%(user_source_id)s 
            AND status=%(status)s 
            ORDER BY id DESC;
        """
        params = {
            "action": action,
            "user_id": user_id,
            "user_source_id": user_source_id,
            "status": status,
        }

        return UserMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def get_user_account_data(investor_pk, user_source_id, cp_user_pk):
        sql = """
                Select lc.id, lc.first_name, lc.user_id, la.number, 
                lc.encoded_mobile,lc.encoded_email
                from lendenapp_customuser lc
                left join lendenapp_account la on la.user_id = lc.id
                where (lc.id = %(investor_pk)s and 
                la.user_source_group_id = %(user_source_group_id)s ) 
                or lc.id = %(cp_user_pk)s
            """
        params = {
            "investor_pk": investor_pk,
            "user_source_group_id": user_source_id,
            "cp_user_pk": cp_user_pk,
        }
        return UserMapper().sql_execute_fetch_all(sql, params, to_dict=True)

    @staticmethod
    def check_borrower_data(encoded_mobile):
        sql = """
                SELECT COUNT(*), 
                bool_or(group_id = %(borrower_id)s) as "is_borrower", lc.id 
                from lendenapp_customuser lc 
                join lendenapp_customuser_groups lcg 
                on lc.id = lcg.customuser_id  
                WHERE lc.encoded_mobile = %(encoded_mobile)s
                group by lc.id;
                """

        params = {"encoded_mobile": encoded_mobile, "borrower_id": UserGroup.BORROWER}

        return UserMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def insert_investor_timeline(lag_data, tc_data):
        sql = f"""
                INSERT INTO lendenapp_timeline (user_id, user_source_group_id, 
                activity, detail, created_date, updated_date)
                VALUES (%s, %s, %s, %s, %s, %s), (%s, %s, %s, %s, %s, %s)
            """
        params = lag_data + tc_data  # concatenate the data tuples
        UserMapper().execute_sql(sql, params)

    def get_cp_mcp_user_source_ids(self):
        sql = """
                 SELECT lusg.id from lendenapp_user_source_group lusg
                 JOIN lendenapp_source ls on lusg.source_id = ls.id
                 WHERE ls.source_name = ANY(%(source_name)s)
                 AND lusg.user_id = %(user_id)s;
            """

        params = {
            "source_name": (InvestorSource.LCP, InvestorSource.MCP),
            "user_id": self.user_pk,
        }

        params = DataLayerUtils().prepare_sql_params(params)
        results = self.sql_execute_fetch_all(sql, params, to_dict=True)
        user_source_ids = [result["id"] for result in results]

        return user_source_ids

    def insert_into_user_kyc(self, data):
        sql = """
                  INSERT INTO lendenapp_userkyc
                    (tracking_id, status, poi_name,
                    poa_name, service_type, user_kyc_consent,
                    user_source_group_id, user_id, event_status, provider, 
                    event_code, status_code)
                  VALUES 
                    (%(tracking_id)s, %(status)s, %(poi_name)s, 
                    %(poa_name)s, %(service_type)s, %(user_kyc_consent)s, 
                    %(user_source_group_id)s, %(user_id)s, %(event_status)s, 
                    %(provider)s, %(event_code)s, %(status_code)s);
            """

        params = {
            "tracking_id": data["tracking_id"],
            "status": data["status"],
            "poi_name": data.get("poi_name"),
            "poa_name": data.get("poa_name"),
            "service_type": data["service_type"],
            "user_kyc_consent": data.get("user_kyc_consent"),
            "user_source_group_id": self.user_source_id,
            "user_id": data["user_id"],
            "event_status": data.get("event_status"),
            "provider": data.get("provider"),
            "event_code": data.get("event_code"),
            "status_code": data.get("status_code"),
        }

        self.execute_sql(sql, params)

    @staticmethod
    def insert_multiple_data(table_name, data_list):
        # Assuming all dictionaries in data_list have the same keys
        columns = ", ".join(data_list[0].keys())
        values_template = ", ".join(["%s"] * len(data_list[0]))

        sql = f"INSERT INTO {table_name} ({columns}) VALUES "
        placeholders = ", ".join([f"({values_template})"] * len(data_list))

        sql += placeholders
        flat_values = [value for data in data_list for value in data.values()]
        return UserMapper().execute_sql(
            sql, params=flat_values, return_rows_count=True
        )

    @staticmethod
    def fetch_user_bank_account_details(columns_and_values):
        # Generate conditions only if columns_and_values is not empty
        if columns_and_values:
            conditions = " AND ".join(
                [f"{column} = %s" for column in columns_and_values]
            )
            # Append the active condition
            conditions = f"({conditions}) AND lba.is_active = True"
        else:
            # Default to only checking if active
            conditions = "lba.is_active = True"

        sql = f"""            
            SELECT lc.user_id, lc.encoded_mobile as mobile_number,
                   lb.name as bank_name,lba.number as account_number,
                    lba.ifsc_code,lba.name as account_holder_name,
                    lba.type as account_type,lc.first_name, 
                    lusg.channel_partner_id, lc.id as investor_pk, 
                    lba.id as bank_account_id
            FROM lendenapp_customuser lc
            INNER JOIN lendenapp_user_source_group lusg on lc.id = lusg.user_id
            INNER JOIN lendenapp_bankaccount lba on 
            lusg.id = lba.user_source_group_id
            INNER JOIN lendenapp_bank lb ON lba.bank_id = lb.id
            WHERE{conditions}
        """

        params = tuple(columns_and_values.values())

        return UserMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def get_mandate_details(columns_and_values):
        conditions = " AND ".join(
            [f"{column} = %s" for column in columns_and_values.keys()]
        )

        sql = f"""
                Select mandate_status, status, mandate_tracker_id,
                expiry_date, scheme_info_id, lm.id, lmt.mandate_reference_id,
                lm.user_source_group_id, lmt.remarks, lm.max_amount, lm.mandate_end_date
                FROM lendenapp_mandatetracker lmt JOIN lendenapp_mandate lm 
                ON lmt.id = lm.mandate_tracker_id
                WHERE {conditions}
            """

        params = tuple(columns_and_values.values())

        return UserMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def get_scheme_account_details(columns_and_values):
        conditions = " AND ".join(
            [f"{column} = %s" for column in columns_and_values.keys()]
        )

        sql = f"""       
                SELECT la.balance, ls.amount,la.user_source_group_id,
                lat.transaction_id,ls2.source_name
                FROM lendenapp_schemeinfo ls JOIN 
                lendenapp_user_source_group lusg ON 
                ls.user_source_group_id = lusg.id
                JOIN lendenapp_source ls2 ON lusg.source_id = ls2.id
                JOIN lendenapp_account la ON la.user_source_group_id = lusg.id
                JOIN lendenapp_transaction lat ON ls.transaction_id = lat.id
                WHERE {conditions}
                """

        params = tuple(columns_and_values.values())

        return UserMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def get_user_source_details(columns_and_values, selected_columns):
        conditions = " AND ".join(
            [f"{column} = %s" for column in columns_and_values.keys()]
        )

        selected_columns_str = ", ".join(selected_columns)

        sql = f"""
                SELECT {selected_columns_str}
                FROM lendenapp_customuser lc JOIN 
                lendenapp_user_source_group lusg ON lc.id = lusg.user_id
                JOIN lendenapp_source ls 
                ON lusg.source_id=ls.id
                WHERE {conditions}
            """

        params = tuple(columns_and_values.values())

        return UserMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def scheme_transaction_details(columns_and_values):
        conditions = " AND ".join(
            [f"{column} = %s" for column in columns_and_values.keys()]
        )

        sql = f"""
                SELECT lsi.tenure, lsi.preference_id, lsi.amount, 
                lsi.investment_type, lt.transaction_id, lsi.scheme_id,
                lt.description 
                FROM lendenapp_schemeinfo lsi JOIN lendenapp_transaction lt 
                ON lsi.transaction_id = lt.id
                WHERE {conditions}
            """

        params = tuple(columns_and_values.values())

        return UserMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def fetch_scheme_and_mandate_details(
        columns_and_values, order_by=None, desc_order=False, all_result=False
    ):

        conditions = " AND ".join(
            [f"{column} = %s" for column in columns_and_values.keys()]
        )

        sql = f"""
                        SELECT lsi.scheme_id
                        FROM lendenapp_schemeinfo lsi JOIN 
                        lendenapp_mandatetracker lmt ON 
                        lsi.id = lmt.scheme_info_id
                        JOIN lendenapp_mandate lm ON 
                        lmt.id = lm.mandate_tracker_id
                        WHERE {conditions}
                """

        params = tuple(columns_and_values.values())

        if order_by:
            sql += """ ORDER BY """ + order_by
            if desc_order:
                sql += " DESC"

        if all_result:
            return UserMapper().sql_execute_fetch_all(sql, params, to_dict=True)

        return UserMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    def get_app_rating_data(self):
        sql = """
                WITH record AS (
                    SELECT lar.id, lar.rating, lar.action_type,
                    BOOL_OR(lar.action = %(action)s) OVER (PARTITION BY la.user_source_group_id) AS is_submitted,
                    BOOL_OR(lar.action_type = %(action_type)s) OVER (PARTITION BY la.user_source_group_id) AS is_scheme_action,
                    (la.status = %(account_status)s) AS is_listed,
                    ROW_NUMBER() OVER (
                    PARTITION BY la.user_source_group_id ORDER BY lar.id DESC
                    ) AS latest_record
                FROM lendenapp_account la
                LEFT JOIN lendenapp_app_rating lar ON la.user_source_group_id = lar.user_source_group_id
                WHERE la.user_source_group_id = %(user_source_group_id)s
                )
                SELECT id, rating, action_type, is_submitted, is_scheme_action, is_listed
                FROM record 
                WHERE latest_record = 1
            """

        params = {
            "user_source_group_id": self.user_source_id,
            "action": AppRating.SUBMITTED,
            "action_type": AppRating.SCHEME,
            "account_status": AccountStatus.LISTED,
        }

        return self.sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def check_data_exists(table_name, columns_and_values, logical_operator="AND"):
        conditions_parts = []
        params = {}

        for column, value in columns_and_values.items():
            if isinstance(value, (list, tuple)):
                conditions_parts.append(f"{column} = ANY(%({column})s)")
                params[column] = value
            else:
                conditions_parts.append(f"{column} = %({column})s")
                params[column] = value

        conditions = f" {logical_operator} ".join(conditions_parts)

        sql = f"""
                SELECT EXISTS (
                    SELECT 1
                    FROM {table_name}
                    WHERE {conditions}
                )
            """

        params = DataLayerUtils().prepare_sql_params(params)
        return UserMapper().sql_execute_fetch_one(sql, params, index_result=True)

    def update_account_status_and_bank_account_id(self, bank_account_id):
        sql = """
                 UPDATE lendenapp_account la 
                 SET bank_account_id = %(bank_account_id)s,
                 updated_date=now()
                 where user_source_group_id = %(user_source_id)s;
            """

        params = {
            "bank_account_id": bank_account_id,
            "user_source_id": self.user_source_id,
        }

        self.execute_sql(sql, params)

    def update_existing_bank_accounts(self, bank_account_id):
        sql = """
                UPDATE lendenapp_bankaccount lba 
                SET is_active = false,
                updated_date = now()
                WHERE user_source_group_id = %(user_source_id)s 
                AND id <> %(bank_account_id)s;
            """
        params = {
            "bank_account_id": bank_account_id,
            "user_source_id": self.user_source_id,
        }
        self.execute_sql(sql, params)

    def get_lender_data(self):
        sql = """
            SELECT first_name,encoded_mobile as mobile_number, ucic_code,
            encoded_email as email, user_id, encoded_pan, dob, 
            email_verification, is_family_member
            FROM lendenapp_customuser
            WHERE id=%(user_id)s
        """
        params = {"user_id": self.user_pk}
        return self.sql_execute_fetch_one(sql, params, to_dict=True)

    def get_lender_consent_data(self):
        sql = """
            select consent_type ,bool(consent_value) from lendenapp_userconsentlog
             where user_source_group_id=%(user_source_id)s
             and consent_type =ANY(%(consent_type)s);
        """
        params = {
            "user_source_id": self.user_source_id,
            "consent_type": (
                ConsentData.politically_exposed["consent_type"],
                ConsentData.LDC_kyc_consent_data["consent_type"],
            ),
        }
        params = DataLayerUtils().prepare_sql_params(params)
        return self.sql_execute_fetch_all(sql, params, to_dict=True)

    def get_address_from_existing_cp(self):
        sql = f"""
                SELECT location as address,city,state,pin as pincode from 
                lendenapp_address la
                join lendenapp_user_source_group lusg
                on lusg.id = la.user_source_group_id 
                join lendenapp_source ls 
                on lusg.source_id = ls.id
                where ls.source_name = ANY(%(source_name)s)
                and lusg.user_id = %(user_id)s
                and la.user_source_group_id <> %(user_source_group_id)s
                limit 1;
            """

        params = {
            "source_name": [InvestorSource.LCP, InvestorSource.MCP],
            "user_id": self.user_pk,
            "user_source_group_id": self.user_source_id,
        }

        # Prepare parameters for PostgreSQL array handling
        prepared_params = DataLayerUtils().prepare_sql_params(params)
        return self.sql_execute_fetch_one(sql, prepared_params, to_dict=True)

    def fetch_blocked_balance_for_investor(self):
        sql = """
            SELECT
                sum(amount) blocked_balance
            FROM lendenapp_schemeinfo lsi
            WHERE lsi.user_source_group_id = %(user_source_id)s AND lsi.status=%(status)s 
        """
        params = {
            "status": SchemeStatus.INITIATED,
            "user_source_id": self.user_source_id,
        }
        return self.sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def get_tracking_id(user_source_group_id):
        sql = """
        select lu.tracking_id,lc.encoded_email as email, lc.first_name, 
        lc.encoded_mobile as mobile_number, lc.type,
        lc.encoded_pan as pan, lc.dob, la.status as account_status, 
        lu.aml_category, lc.is_family_member
        from lendenapp_userkyctracker lu 
        join lendenapp_account la on la.user_source_group_id = lu.user_source_group_id
        join lendenapp_customuser lc on lu.user_id = lc.id
        where lu.user_source_group_id = %(user_source_group_id)s 
        and lu.status =%(status)s and lu.is_latest_kyc
        order by lu.id desc 
        """

        params = {
            "user_source_group_id": user_source_group_id,
            "status": KYCConstant.SUCCESS,
        }

        return UserMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def get_address_details_by_user_id(user_id, address_type, selected_columns=["*"]):
        selected_columns_str = ", ".join(selected_columns)

        sql = f"""
                            SELECT {selected_columns_str}
                            FROM lendenapp_customuser lc 
                            INNER JOIN lendenapp_address la 
                            ON la.user_id=lc.id
                            WHERE lc.user_id=%(user_id)s AND la.type=%(type)s;
                        """

        params = {"user_id": user_id, "type": address_type}

        return UserMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def get_info_from_passcode(mobile):
        sql = """
            SELECT lc.id as user_pk, lc.user_id as user_id,
            lum.user_source_group_id as user_source_id, lc2.partner_id,
            lum.passcode, ls.source_name
            FROM lendenapp_user_metadata lum 
            JOIN lendenapp_user_source_group lusg 
            ON lum.user_source_group_id = lusg.id 
            JOIN lendenapp_source ls
            on ls.id = lusg.source_id
            JOIN lendenapp_customuser lc 
            ON lusg.user_id = lc.id 
            LEFT JOIN lendenapp_channelpartner lc2 
            ON lc2.id = lusg.channel_partner_id 
            WHERE lc.encoded_mobile = %(mobile)s;
            """
        params = {"mobile": mobile}
        return UserMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def fetch_scheme_mandate_details(
        columns_and_values,
        selected_columns,
        order_by=None,
        desc_order=False,
        all_result=False,
    ):

        conditions = " AND ".join(
            [f"{column} = %s" for column in columns_and_values.keys()]
        )

        selected_columns_str = ", ".join(selected_columns)

        sql = f"""
            SELECT {selected_columns_str}
            FROM lendenapp_schemeinfo lsi 
            JOIN lendenapp_mandate lm 
            ON lsi.mandate_id = lm.id
            WHERE {conditions}
        """

        params = tuple(columns_and_values.values())

        if order_by:
            sql += """ ORDER BY """ + order_by
            if desc_order:
                sql += " DESC"

        if all_result:
            return UserMapper().sql_execute_fetch_all(sql, params, to_dict=True)

        return UserMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def fail_nach_transactions(transaction_id_list):
        sql = """
                update lendenapp_transaction
                set status=%(status)s, updated_date=%(updated_date)s, 
                status_date=%(status_date)s, 
                rejection_reason=%(rejection_reason)s
                where id =ANY(%(transaction_ids)s)
              """

        params = {
            "transaction_ids": tuple(transaction_id_list),
            "status": TransactionStatus.FAILED,
            "updated_date": get_current_dtm(),
            "status_date": get_todays_date_in_ist(),
            "rejection_reason": NMIConstants.CANCEL_MANDATE_REMARK,
        }
        params = DataLayerUtils().prepare_sql_params(params)
        UserMapper().execute_sql(sql, params)

    @staticmethod
    def fetch_cohort_config(purpose_name):
        sql = """
            SELECT lc.id, lc.cohort_category, lc.weightage
            FROM lendenapp_cohort_config lc
            INNER JOIN lendenapp_cohort_purpose lp
            ON lc.purpose_id = lp.id
            WHERE lp.name = %(purpose_name)s 
            AND lc.is_enabled = TRUE
            AND lp.is_enabled = TRUE
            AND weightage>0;
        """
        params = {"purpose_name": purpose_name}
        return UserMapper().sql_execute_fetch_all(sql, params, to_dict=True)

    @staticmethod
    def fetch_cohort_mapping_counts(purpose_name):
        sql = """            
            SELECT m.config_id, COUNT(*) AS count
            FROM lendenapp_user_cohort_mapping m
            WHERE m.purpose_id = (SELECT id FROM lendenapp_cohort_purpose WHERE name = %(purpose_name)s)
            GROUP BY m.config_id;
        """
        params = {"purpose_name": purpose_name}
        return UserMapper().sql_execute_fetch_all(sql, params, to_dict=True)

    @staticmethod
    def check_existing_cohort(purpose_name, user_source_group_id):
        sql = """
            SELECT lc.cohort_category
            FROM lendenapp_user_cohort_mapping m
            INNER JOIN lendenapp_cohort_config lc ON m.config_id = lc.id
            INNER JOIN lendenapp_cohort_purpose lp ON m.purpose_id = lp.id
            WHERE lp.name = %(purpose_name)s 
            AND m.user_source_group_id = %(user_source_group_id)s;
        """
        params = {
            "purpose_name": purpose_name,
            "user_source_group_id": user_source_group_id,
        }
        return UserMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def insert_user_cohort_mapping(purpose_name, user_source_group_id, config_id):
        sql = """
            INSERT INTO lendenapp_user_cohort_mapping (purpose_id, 
            user_source_group_id, config_id)
            SELECT id, %(user_source_group_id)s, %(config_id)s 
            FROM lendenapp_cohort_purpose
            WHERE name = %(purpose_name)s;
        """
        params = {
            "purpose_name": purpose_name,
            "user_source_group_id": user_source_group_id,
            "config_id": config_id,
        }
        UserMapper().execute_sql(sql, params)

    @staticmethod
    def get_source_name_from_user_source_id(user_source_group_id):
        sql = """
            select source_name 
            from lendenapp_user_source_group lusg 
            join lendenapp_source ls 
            on lusg.source_id =ls.id
            where lusg.id = %(user_source_group_id)s;
        """
        params = {"user_source_group_id": user_source_group_id}
        return UserMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def fetch_cp_lender_details(columns_and_values, selected_columns):
        conditions = " AND ".join(
            [f"{column} = %s" for column in columns_and_values.keys()]
        )

        selected_columns_str = ", ".join(selected_columns)

        sql = f"""
            SELECT {selected_columns_str}
            FROM lendenapp_user_source_group lusg 
            JOIN lendenapp_customuser lc ON
                lc.id = lusg.user_id 
            JOIN lendenapp_account la ON la.user_source_group_id = lusg.id
            JOIN lendenapp_channelpartner lc2 ON
                lc2.id = lusg.channel_partner_id
            WHERE {conditions}
        """
        params = tuple(columns_and_values.values())

        return UserMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def get_cp_investor_details(
        columns_and_values,
        selected_columns=None,
        all_result=False,
        logical_operator="AND",
    ):
        if not selected_columns:
            selected_columns = ["*"]
        selected_col_str = ",".join(selected_columns)

        conditions = f" {logical_operator} ".join(
            [
                f"{column} {' in' if isinstance(columns_and_values[column], tuple) else ' ='} %s"
                for column in columns_and_values.keys()
            ]
        )

        sql = f"""
            SELECT
                {selected_col_str}
            FROM lendenapp_user_source_group lusg
            JOIN lendenapp_customuser lc ON lc.id = lusg.user_id
            JOIN lendenapp_channelpartner cp ON cp.id = lusg.channel_partner_id
            WHERE {conditions}
        """

        params = tuple(columns_and_values.values())

        if all_result:
            return UserMapper().sql_execute_fetch_all(sql, params, to_dict=True)

        return UserMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    def get_user_rm_data(self):
        sql = f"""
               select name,encoded_email as email,encoded_mobile as mobile from lendenapp_reference lr
               where lr.user_source_group_id = %(user_source_group_id)s and relation = %(relation)s
            """

        params = {
            "user_source_group_id": self.user_source_id,
            "relation": RMReference.RELATION_RM,
        }

        return self.sql_execute_fetch_one(sql, params, to_dict=True)

    def get_investor_and_cp_data(self):
        sql = """
        SELECT lc.first_name AS investor_name, 
        lc.encoded_email, lc.encoded_mobile, 
        lc.is_family_member,
        lc3.first_name AS cp_name, 
        lc3.encoded_email as cp_email,
        lc3.encoded_mobile as cp_mobile,
        lc3.user_id as cp_user_id,
        lr.name as rm_name,
        lr.encoded_email as rm_email
        FROM lendenapp_user_source_group lusg
        JOIN lendenapp_customuser lc ON lc.id = lusg.user_id
        JOIN lendenapp_channelpartner lc2 ON lc2.id = lusg.channel_partner_id 
        JOIN lendenapp_customuser lc3 ON lc3.id = lc2.user_id
        LEFT JOIN lendenapp_reference lr ON lr.user_id = lc3.id 
            AND relation = %(rm_relation)s
        WHERE lusg.id = %(user_source_id)s
        """

        params = {
            "user_source_id": self.user_source_id,
            "rm_relation": RMReference.RELATION_RM,
        }

        return self.sql_execute_fetch_one(sql, params, to_dict=True)

    def get_txn_check_by_type(self, txn_type, status):
        sql = """
            SELECT EXISTS (
                SELECT 1
                FROM lendenapp_transaction lt
                WHERE user_source_group_id = %(user_source_id)s
                  AND type = ANY(%(type)s)
                  AND status = %(status)s
            );
        """

        params = {
            "user_source_id": self.user_source_id,
            "type": txn_type,
            "status": status,
        }

        return self.sql_execute_fetch_one(sql, params, index_result=True)

    def update_app_rating(self, rating_data):
        sql = """
            update lendenapp_app_rating 
            set rating = %(rating)s, action = %(action)s, remark = %(remark)s, 
            screen_name = %(screen_name)s, source = %(source)s, updated_date = now()
            where id = (select id from lendenapp_app_rating lar 
            where user_source_group_id = %(user_source_group_id)s 
            and action = %(skip_action)s order by id desc limit 1) returning id;
        """
        params = {
            "rating": rating_data.get("rating"),
            "action": rating_data["action"],
            "remark": rating_data.get("message"),
            "screen_name": rating_data["screen_name"],
            "source": rating_data["source"],
            "user_source_group_id": self.user_source_id,
            "skip_action": AppRating.SKIPPED,
        }
        return self.sql_execute_fetch_one(sql, params, index_result=True)

    @staticmethod
    def fetch_cp_staff_data(data, cp_active_check=True):
        sql = """
            select 
                lc.first_name as staff_name,
                lc.encoded_email as staff_encoded_email,
                lc.encoded_mobile as staff_encoded_mobile, 
                lc.password as password, 
                lc.user_id as staff_user_id, 
                lc.id as staff_pk,
                lcs.has_edit_access, 
                lcs.is_active as staff_active, 
                lc2.encoded_email, 
                lc2.id as id, 
                lc2.user_id as user_id,
                lc2.is_active
            from lendenapp_cp_staff lcs
            join lendenapp_customuser lc on lc.id = lcs.user_id
            join lendenapp_customuser lc2 on lc2.id = lcs.cp_id
        """

        params = {}
        conditions = []

        if cp_active_check:
            conditions.append("lc2.is_active = true")

        if data.get("encoded_email"):
            conditions.append("lc.encoded_email = %(staff_encoded_email)s")
            params["staff_encoded_email"] = data["encoded_email"]

        if data.get("encoded_mobile"):
            conditions.append("lc.encoded_mobile = %(staff_encoded_mobile)s")
            params["staff_encoded_mobile"] = data["encoded_mobile"]

        if data.get("staff_user_id"):
            conditions.append("lc.user_id = %(staff_user_id)s")
            params["staff_user_id"] = data["staff_user_id"]

        if conditions:
            sql += " where " + " and ".join(conditions)
        return UserMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    def insert_staff_log(self, data):
        return self.insert_data(table_name="lendenapp_cp_staff_log", data=data)

    def insert_personal_info(self, user_data):
        return self.insert_data(
            table_name="lendenapp_users_personal_info", data=user_data
        )

    @staticmethod
    def should_show_rating(rating_id):
        sql = """
                WITH latest_entry AS (
                    SELECT id, created_date::date AS created_date, user_source_group_id
                    FROM lendenapp_app_rating
                    WHERE id = %(rating_id)s
                ),
                monthly_count AS (
                    SELECT COUNT(*) AS entry_count
                    FROM lendenapp_app_rating
                    WHERE action_type = %(action_type)s
                      AND user_source_group_id = (SELECT user_source_group_id FROM latest_entry)
                      AND DATE_TRUNC('month', created_date::date) = DATE_TRUNC('month', (SELECT created_date FROM latest_entry))
                )
                SELECT 
                    CASE 
                        -- Step 1: Latest entry must be > 7 days old
                        WHEN latest_entry.created_date < (CURRENT_DATE - INTERVAL '7 days') THEN
                            -- Step 2: Monthly count must be < 3
                            CASE 
                                WHEN monthly_count.entry_count < 3 THEN TRUE
                                ELSE FALSE
                            END
                        ELSE FALSE
                    END AS should_show_rating
                FROM latest_entry
                CROSS JOIN monthly_count;
                """
        params = {"rating_id": rating_id, "action_type": AppRating.USER}
        return UserMapper().sql_execute_fetch_one(sql, params, index_result=True)

    @staticmethod
    def get_mnrl_status(user_pk, is_cp=False):
        if is_cp:
            sql = """
                  SELECT lc.mnrl_status, lr.encoded_email as rm_email
                  FROM lendenapp_customuser lc
                           LEFT JOIN lendenapp_reference lr
                                     ON lc.id = lr.user_id and lr.relation = %(RM)s
                  WHERE lc.id = %(user_pk)s \
                  """
        else:
            sql = """
                  SELECT lc.mnrl_status
                  FROM lendenapp_customuser lc
                  WHERE lc.id = %(user_pk)s \
                  """

        params = {"user_pk": user_pk, "RM": RMReference.RELATION_RM}

        return UserMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    def get_aggregated_amount_data(self, from_date, to_date, investment_type):
        sql = """
                SELECT
                    COALESCE(SUM(amount), 0) AS total_invested
                FROM
                    lendenapp_schemeinfo lsi
                JOIN lendenapp_user_source_group lusg 
                ON lsi.user_source_group_id = lusg.id
                WHERE
                    lusg.user_id = %(user_id)s
                    AND lsi.status = ANY(%(status)s)
                    AND investment_type = %(investment_type)s
                    AND created_date::DATE between %(from_date)s AND %(to_date)s;
            """

        params = {
            "status": [TransactionStatus.SUCCESS, TransactionStatus.INITIATED],
            "user_id": self.user_pk,
            "investment_type": investment_type,
            "from_date": from_date,
            "to_date": to_date,
        }

        return self.sql_execute_fetch_one(sql, params, to_dict=True)

    def cancel_auto_lending_mandate(self, user_source_id):
        return self.update_data(
            "lendenapp_schemeinfo",
            {"mandate_id": None},
            {
                "user_source_group_id": user_source_id,
                "investment_type": FMPPInvestmentType.AUTO_LENDING,
            },
        )

    def get_reference_family_members(self, selected_columns):

        selected_columns_str = ", ".join(selected_columns)
        sql = f"""
            SELECT {selected_columns_str}
            FROM lendenapp_reference lr
            JOIN lendenapp_user_source_group lusg ON lusg.id = lr.user_source_group_id
            JOIN lendenapp_customuser lc ON lc.id = lusg.user_id
            WHERE lr.type = %(type)s
            AND lusg.status = %(active_status)s
        """
        params = {
            "type": HOFMember.REFERENCE_TYPE,
            "active_status": UserGroupSourceStatus.ACTIVE,
        }

        if self.user_source_id:
            sql += f" AND lr.owner_source_id = %(owner_source_id)s"
            params["owner_source_id"] = self.user_source_id
        elif self.user_pk:
            sql += f" AND lr.user_id = %(user_id)s"
            params["user_id"] = self.user_pk

        return self.sql_execute_fetch_all(sql, params, to_dict=True)

    def get_head_of_family_data(self, selected_columns, user_source_ids=None):
        selected_columns_str = ", ".join(selected_columns)
        sql = f"""
            SELECT {selected_columns_str}
            FROM lendenapp_customuser lc
            JOIN lendenapp_reference lr ON lr.user_id = lc.id
            WHERE 
            lc.is_active = %(active_status)s
            AND lr.type = %(type)s
        """
        params = {
            "user_source_id": self.user_source_id or user_source_ids,
            "type": HOFMember.REFERENCE_TYPE,
            "active_status": True,
        }
        if self.user_source_id:
            sql += f" AND lr.user_source_group_id = %(user_source_id)s"
        elif user_source_ids:
            sql += f" AND lr.user_source_group_id = ANY(%(user_source_id)s)"

        params = DataLayerUtils().prepare_sql_params(params)
        return self.sql_execute_fetch_one(sql, params, to_dict=True)
