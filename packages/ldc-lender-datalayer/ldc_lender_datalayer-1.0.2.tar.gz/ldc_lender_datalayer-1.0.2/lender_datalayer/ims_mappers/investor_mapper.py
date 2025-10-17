import ast
import binascii
import json
import logging
import os
from datetime import timedelta

from ..base_datalayer import BaseDataLayer, DataLayerUtils
from ..common.constants import (AccountStatus, AddBankAccountConstant, AddressType, AMLConstants, CampaignType,
                              CashfreeConstant, DocumentConstant, DocumentRemark, ExpiredTransaction, FMISystem,
                              FMITransactionStatus, FMPPInvestmentType, HOFMember, InvestorSource, InvoiceType,
                              KYCConstant, KycServices, MandateConstants, MandateStatus, NameMatchStatus,
                              NotificationStatus, OTLInvestment, PMIConstants, RedisConstants, ReferenceConstant,
                              ReferralDetails, RewardStatus, RMLenderFilterTypes, RMReference, SchemeStatus, SearchKey,
                              STLSchemePriorityOrderValues, TimeZone, TransactionBlockForUser, TransactionConstants,
                              TransactionStatus, TransactionType, UPIMandateStatus, UserGroup, UserGroupSourceStatus)
from ..common.utils.datetime_utils import (get_current_dtm, get_current_time_in_ist, get_todays_date,
                                         get_todays_date_in_ist)
from ..common.utils.encryption_utils import EncryptDecryptAES256
from ..common.utils.shared_utils import mask_aadhar, mask_email, mask_mobile, mask_pan

logger = logging.getLogger("normal")
encryption = EncryptDecryptAES256()


class InvestorMapper(BaseDataLayer):
    def __init__(self, investor_pk=None, user_source_id=None, db_alias="default"):
        super().__init__(db_alias)
        self.investor_pk = investor_pk
        self.user_source_id = user_source_id

    def get_entity_name(self):
        return "IMS_INVESTOR"

    def get_investor_data_by_field(self, column, value, selected_column="*"):
        query = (
            """
                   select """
            + selected_column
            + """
                   from lendenapp_customuser lc
                   where lc."""
            + column
            + """=%(value)s
               """
        )
        params = {"value": value}

        details = self.sql_execute_fetch_all(query, params, to_dict=True)
        return details[0] if details else None

    def get_doc_url_for_user(self, doc_type, user_source_id=None):
        query = "select file from lendenapp_document where user_id=%(user_id)s"
        params = {"user_id": self.investor_pk, "doc_type": doc_type}
        if user_source_id:
            params["user_source_group_id"] = user_source_id
            query += " and user_source_group_id=%(user_source_group_id)s"

        if isinstance(doc_type, tuple):
            query += " and type in %(doc_type)s"
        else:
            query += " and type=%(doc_type)s"

        query += " order by id desc limit 1"
        doc_file = self.sql_execute_fetch_one(query, params, index_result=True)
        # return S3Helper().get_media_url(doc_file) if doc_file else None

    def address_details(self, address_type):
        query = """
            select la.location, la.city, la.state, la.country, la.pin, 
                la.landmark, la.lat_long, la.is_verified, la.stay_type 
            from lendenapp_address la
            inner join lendenapp_customuser_address lca on la.id=lca.address_id
            where lca.customuser_id =%(user_id)s and la.type=%(address_type)s
            order by la.id desc limit 1
        """
        params = {"user_id": self.investor_pk, "address_type": address_type}
        results = self.sql_execute_fetch_all(query, params, to_dict=True)
        return results[0] if results else None

    def bank_details(self, fetch_all=False):
        query = """
            select lba.number, lba.ifsc_code, lba.type,
                lba.name as account_name, lb.name as bank_name,
                lba.purpose
            from lendenapp_bankaccount lba
            inner join lendenapp_bank lb on lba.bank_id = lb.id
            where user_id=%(user_id)s 
            AND lba.is_active = TRUE
        """
        params = {
            "user_id": self.investor_pk,
        }
        if not fetch_all:
            query += " and purpose=%(purpose)s "
            params["purpose"] = AddBankAccountConstant.PRIMARY_PURPOSE

        if self.user_source_id:
            params["user_source_group_id"] = self.user_source_id
            query += " and lba.user_source_group_id=%(user_source_group_id)s"

        results = self.sql_execute_fetch_all(sql=query, params=params, to_dict=True)
        if fetch_all:
            return results
        return results[0] if results else None

    def user_basic_details(self):
        basic_detail_query = """
            select lc.id, lc.user_id, lc.first_name as name, 
            lc.encoded_email as email, lc.encoded_mobile as mobile_number, 
            lc.dob, lc.gender, lc.encoded_pan as pan, 
            lc.encoded_aadhar as aadhar, lc.marital_status, 
            la.balance as account_balance, la.status as account_status
            from lendenapp_customuser lc
            left join lendenapp_account la on la.user_id=lc.id
            where lc.id=%(user_id)s
        """
        params = {"user_id": self.investor_pk}

        if self.user_source_id:
            params["user_source_group_id"] = self.user_source_id
            basic_detail_query += (
                " and la.user_source_group_id=%(user_source_group_id)s"
            )

        basic_details = self.sql_execute_fetch_all(
            basic_detail_query, params, to_dict=True
        )
        if basic_details:
            basic_details = basic_details[0]
            profile_url = self.get_doc_url_for_user(doc_type="profile_picture")
            basic_details["profile_image"] = profile_url
            return basic_details
        return {}

    def pan_details(self, user_source_id, user_details={}):
        pan_image_type = DocumentConstant.PAN_CARD
        pan_image = self.get_doc_url_for_user(
            pan_image_type, user_source_id
        )  # with task_id first
        if not pan_image:
            pan_image = self.get_doc_url_for_user(pan_image_type)

        details = {
            "pan_number": user_details.pop("pan", None),
            "personal_reference_name": user_details.pop(
                "personal_reference_name", None
            ),
            "pan_image": pan_image,
        }
        return details

    def get_all_detail_for_partner(self, source):
        condition = {"lusg.user_id": self.investor_pk, "ls.source_name": source}
        user_source_id = self.get_user_source_data(condition, ["lusg.id"])["id"]
        self.user_source_id = user_source_id
        user_basic_details = self.user_basic_details()
        user_basic_details['mobile_number'] = mask_mobile(
            mobile_number=encryption.decrypt_data(
                user_basic_details['mobile_number']
            ),
            source=source
        )
        user_basic_details["email"] = mask_email(
            email=encryption.decrypt_data(user_basic_details["email"]), source=source
        )
        user_basic_details["pan"] = mask_pan(
            pan=encryption.decrypt_data(user_basic_details["pan"]), source=source
        )
        user_basic_details["aadhar"] = mask_aadhar(
            aadhar=encryption.decrypt_data(user_basic_details["aadhar"]), source=source
        )
        bank_details = self.bank_details()
        pan_details = self.pan_details(user_source_id, user_basic_details)

        address_details = {
            "permanent_address": self.address_details(
                address_type=AddressType.PERMANENT
            ),
            "communication_address": self.address_details(
                address_type=AddressType.COMMUNICATION
            ),
        }

        user_data = {
            "basic_details": user_basic_details,
            "pan_details": pan_details,
            "bank_details": bank_details,
            "address_details": address_details,
            "user_source_id": user_source_id,
            "user_id": user_basic_details["user_id"],
            "token": self.get_user_token(user_basic_details["id"]),
        }
        return user_data

    def get_user_token(self, investor_pk):
        sql = "SELECT key FROM authtoken_token WHERE user_id=%s"
        token = self.sql_execute_fetch_one(sql, [investor_pk], index_result=True)
        if not token:
            insert_sql = "INSERT INTO authtoken_token(user_id, key, created)\
                VALUES(%(user_id)s, %(key)s, %(created)s) \
                RETURNING key"
            params = {
                "user_id": investor_pk,
                "key": self.generate_token_for_mono(),
                "created": get_current_dtm(),
            }
            token = self.sql_execute_fetch_one(insert_sql, params, index_result=True)

        return token

    def generate_token_for_mono(self):
        return binascii.hexlify(os.urandom(20)).decode()

    @staticmethod
    def get_user_source_data(columns_and_values, selected_column=None):
        if not selected_column:
            selected_column = ["*"]
        selected_columns_str = ", ".join(selected_column)
        conditions = " AND ".join(
            [f"{column} = %s" for column in columns_and_values.keys()]
        )

        sql = f"""
               SELECT {selected_columns_str}
               FROM lendenapp_user_source_group lusg
               JOIN lendenapp_source ls ON ls.id = lusg.source_id
               WHERE {conditions}
        """
        params = tuple(columns_and_values.values())
        return InvestorMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    def get_account_balance_from_pk(self, user_pk=None):
        sql = """
                SELECT
                    balance
                FROM lendenapp_account
                WHERE user_id=%(investor_pk)s
        """
        params = {"investor_pk": self.investor_pk or user_pk}
        if self.user_source_id:
            params["user_source_group_id"] = self.user_source_id
            sql += " and user_source_group_id=%(user_source_group_id)s"

        return self.sql_execute_fetch_one(sql, params, index_result=True)

    def check_if_networth_uploaded(self):
        sql = """
                SELECT
                    file, remark
                FROM lendenapp_document
                WHERE user_id=%(user_pk)s and type=%(type)s
                order by id desc
        """
        params = {
            "user_pk": self.investor_pk,
            "type": DocumentConstant.NETWORTH_CERTIFICATE_TYPE,
        }
        result = self.sql_execute_fetch_all(sql, params, to_dict=True)
        return result[0] if result else None

    def get_referred_id_from_user_pk(self):
        sql = """
            SELECT
                lcr.referred_by_id
            FROM lendenapp_customuser lc, lendenapp_convertedreferral lcr
            WHERE lc.id=lcr.user_id and lc.id=%s LIMIT 1
        """
        return self.sql_execute_fetch_one(sql, [self.investor_pk], index_result=True)

    def get_auth_group_from_user_pk(self, fetch_all=None):
        sql = """
            SELECT
                ag.name
            FROM lendenapp_customuser_groups lcg , auth_group ag
            WHERE lcg.group_id=ag.id and customuser_id=%s;
        """
        if fetch_all:
            return self.sql_execute_fetch_all(sql, [self.investor_pk], to_dict=True)
        return self.sql_execute_fetch_one(sql, [self.investor_pk], index_result=True)

    @staticmethod
    def insert_into_upi_mandate_table(params):
        sql = """
        INSERT INTO 
            lendenapp_userupimandate
        (user_id, mandate_request_id, subscription_description,
         subscription_name, frequency, first_deduction_amount, recurring_count,
         max_amount, recurring_start_dtm, recurring_end_dtm, 
         next_installment_dtm, task_id, mandate_status, scheme_status, 
         created_dtm, updated_dtm)
        VALUES(%(user_id)s, %(mandate_request_id)s, %(subscription_description)s,
              %(subscription_name)s, %(frequency)s, %(first_deduction_amount)s,
              %(recurring_count)s, %(max_amount)s,%(recurring_start_dtm)s, 
              %(recurring_end_dtm)s , %(next_installment_dtm)s, %(task_id)s,
              %(mandate_status)s, %(scheme_status)s, now(), now())
        """
        InvestorMapper().execute_sql(sql, params, return_rows_count=True)

    @staticmethod
    def get_mandate_details_from_mandate_request_id(mandate_request_id):
        sql = """
             SELECT
                mandate_status, first_deduction_amount, mandate_request_id,
                recurring_start_dtm, recurring_end_dtm, next_installment_dtm,
                frequency, scheme_id, max_amount, user_source_group_id, 
                user_id, id, created_dtm, updated_dtm
             FROM  lendenapp_userupimandate
              WHERE mandate_request_id=%s
        """
        return InvestorMapper().sql_execute_fetch_one(
            sql, [mandate_request_id], to_dict=True
        )

    def get_transaction_details(
        self, transaction_id, selected_columns, user_source_id=True, for_update=True
    ):

        selected_columns_str = ", ".join(selected_columns)

        sql = f"""
            SELECT {selected_columns_str}
            FROM lendenapp_transaction lc
            WHERE transaction_id=%(transaction_id)s
        """

        params = {
            "transaction_id": transaction_id,
        }

        if user_source_id:
            sql += """ 
            and user_source_group_id=%(user_source_group_id)s
            """
            params["user_source_group_id"] = self.user_source_id

        if for_update:
            sql += " FOR UPDATE NOWAIT"

        return self.sql_execute_fetch_one(sql, params, to_dict=True)

    def get_account_details(self):
        sql = f"""
            SELECT
                number, status, action, previous_balance,
                action_amount, balance, created_date,
                listed_date, updated_date
            FROM lendenapp_account
            WHERE 
        """
        params = {}
        if self.user_source_id:
            params["user_source_group_id"] = self.user_source_id
            sql += " user_source_group_id=%(user_source_group_id)s"

        elif self.investor_pk:
            params["user_id"] = self.investor_pk
            sql += " user_source_group_id = ANY(SELECT id FROM lendenapp_user_source_group lusg WHERE user_id = %(user_id)s)"

        return self.sql_execute_fetch_one(sql, params, to_dict=True)

    def get_account_balance(self, for_update=False):
        sql = f"""
            SELECT
                balance
            FROM lendenapp_account
            WHERE 
        """
        params = {}
        if self.user_source_id:
            params["user_source_group_id"] = self.user_source_id
            sql += " user_source_group_id=%(user_source_group_id)s"

        elif self.investor_pk:
            params["user_id"] = self.investor_pk
            sql += " user_source_group_id = ANY(SELECT id FROM lendenapp_user_source_group lusg WHERE user_id = %(user_id)s)"

        if for_update:
            sql += " FOR UPDATE NOWAIT"

        params = DataLayerUtils().prepare_sql_params(params)
        return self.sql_execute_fetch_one(sql, params, to_dict=True)

    def get_account_balance_sum(self):
        sql = f"""
            SELECT
                sum(balance) as total_balance
            FROM lendenapp_account
            WHERE 
        """
        params = {}
        if self.user_source_id:
            params["user_source_group_id"] = self.user_source_id
            sql += " user_source_group_id=%(user_source_group_id)s"

        elif self.investor_pk:
            params["user_id"] = self.investor_pk
            sql += " user_source_group_id = ANY(SELECT id FROM lendenapp_user_source_group lusg WHERE user_id = %(user_id)s)"

        params = DataLayerUtils().prepare_sql_params(params)
        return self.sql_execute_fetch_one(sql, params, to_dict=True)

    def get_bank_details_by_user_source_id(
        self, selected_columns, all_result=False, only_primary=False
    ):
        sql = f"""
            SELECT {', '.join(selected_columns)}
            FROM lendenapp_bankaccount lb
            WHERE lb.user_source_group_id = %(user_source_id)s
            AND user_id=%(user_pk)s
            AND is_active = TRUE
        """

        params = {"user_source_id": self.user_source_id, "user_pk": self.investor_pk}

        if only_primary:
            sql += " AND purpose = %(purpose)s "
            params["purpose"] = AddBankAccountConstant.PRIMARY_PURPOSE

        if all_result:
            return self.sql_execute_fetch_all(sql, params, to_dict=True)

        return self.sql_execute_fetch_one(sql, params, to_dict=True)

    def get_account_details_v2(self, selected_cols):
        selected_col_str = ",".join(selected_cols)

        sql = (
            f"SELECT {selected_col_str} FROM lendenapp_account "
            "WHERE user_source_group_id=%(user_source_group_id)s AND "
            "user_id=%(user_pk)s"
        )

        params = {
            "user_source_group_id": self.user_source_id,
            "user_pk": self.investor_pk,
        }

        return self.sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def update_scheme_id_for_mandate_id(mandate_id, scheme_id):
        sql = """
            UPDATE
                lendenapp_userupimandate
            SET scheme_id=%s, scheme_status=true
            WHERE mandate_request_id=%s
        """
        return InvestorMapper().execute_sql(
            sql, [scheme_id, mandate_id], return_rows_count=True
        )

    @staticmethod
    def get_user_source_details(selected_cols, user_id, source):
        selected_col_str = ",".join(selected_cols)
        sql = f"""
        SELECT
            {selected_col_str}
        FROM lendenapp_source ls
        JOIN lendenapp_user_source_group lusg ON ls.id = lusg.source_id
        JOIN lendenapp_customuser lc on lusg.user_id = lc.id
        WHERE lc.user_id=%s and lusg.group_id=%s and ls.source_name=%s
        """

        return InvestorMapper().sql_execute_fetch_one(
            sql, [user_id, UserGroup.LENDER, source]
        )

    def get_maturity_date(self, scheme_id):
        sql = """
            SELECT
            recurring_end_dtm
            FROM lendenapp_userupimandate
            WHERE scheme_id = %(scheme_id)s
            AND user_source_group_id = %(user_source_group_id)s
            """
        return self.sql_execute_fetch_one(
            sql,
            params={
                "scheme_id": scheme_id,
                "user_source_group_id": self.user_source_id,
            },
            index_result=True,
        )

    @staticmethod
    def get_mandate_details_with_mandate_status(mandate_status):
        sql = """
                SELECT
                  scheme_id, mandate_request_id, frequency,
                  first_deduction_amount, scheme_status, created_dtm::DATE,
                  next_installment_dtm::timestamp, remarks, user_id, mandate_status
                FROM lendenapp_userupimandate
                WHERE mandate_status in %(mandate_status)s
            """
        params = {"mandate_status": mandate_status}
        mandate_detail_records = InvestorMapper().sql_execute_fetch_all(
            sql, params, to_dict=True
        )
        return mandate_detail_records

    def insert_user_consent_log(self, params):
        sql = """
            INSERT INTO
                lendenapp_userconsentlog
            (consent_type, consent_value, remark, user_id,
            user_source_group_id, created_date, updated_date)
            VALUES
            (%(consent_type)s, %(consent_value)s, %(remark)s, %(user_id)s,
            %(user_source_group_id)s, now(), now()) RETURNING id    
        """
        params["user_source_group_id"] = self.user_source_id
        params["user_id"] = self.investor_pk
        return self.execute_sql(sql, params=params, return_rows_count=True)

    @staticmethod
    def update_mandate_status_with_mandate_request_id(
        mandate_request_id, mandate_status
    ):
        sql = """
            UPDATE 
             lendenapp_userupimandate
             SET mandate_status=%s, updated_dtm=now()
        """
        if mandate_status == UPIMandateStatus.REVOKED:
            sql += ", cancel_date = current_date"
        elif mandate_status == UPIMandateStatus.CANCELLED:
            sql += ", cancel_date = current_date"
        elif mandate_status == UPIMandateStatus.PAUSED:
            sql += ", pause_date  = current_date"

        sql += " WHERE mandate_request_id=%s"

        return InvestorMapper().execute_sql(
            sql, [mandate_status, mandate_request_id], return_rows_count=True
        )

    @staticmethod
    def get_first_name_using_user_id(investor_id_list):
        sql = """
            SELECT first_name, user_id FROM lendenapp_customuser 
            WHERE user_id =ANY (%(investor_id_list)s)
        """
        params = {"investor_id_list": investor_id_list}

        params = DataLayerUtils().prepare_sql_params(params)
        first_name = InvestorMapper().sql_execute_fetch_all(sql, params, to_dict=True)
        return first_name

    @staticmethod
    def check_if_type_id_exist(request_id):
        sql = """             
                SELECT id FROM lendenapp_transaction lt
                WHERE type_id = %(request_id)s
                LIMIT 1;
                """
        return InvestorMapper().sql_execute_fetch_one(
            sql, params={"request_id": request_id}, to_dict=True
        )

    def get_field(self, field):
        return self.sql_execute_fetch_one(
            """select """
            + field
            + """ from 
        lendenapp_customuser where id =%(user_pk)s""",
            {"user_pk": self.investor_pk},
            index_result=True,
        )

    def get_user_info_from_dedupe(self, source_group):
        encoded_pan = self.get_field("encoded_pan")
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

    @staticmethod
    def get_address_details(columns_and_values, selected_cols="*"):
        conditions = " AND ".join(
            [f"{column} = %s" for column in columns_and_values.keys()]
        )

        selected_col_str = ",".join(selected_cols)
        sql = f"""
            select {selected_col_str} from  lendenapp_address
            where {conditions}
        """
        params = tuple(columns_and_values.values())

        return InvestorMapper().sql_execute_fetch_all(sql, params, to_dict=True)

    def investor_basic_details(self):
        sql = """                
                SELECT lc.encoded_pan AS pan_number, 
                lc.first_name AS full_name, 
                lc.email_verification AS email_verification, 
                ld.file AS document, ld.type AS type, lc.dob AS dob
                FROM lendenapp_customuser lc
                LEFT JOIN lendenapp_document ld 
                ON lc.id = ld.user_id 
                WHERE ld.user_source_group_id = %(user_source_group_id)s 
                AND (ld.type = 'business_pan_card' OR ld.type = 'pancard')
                """
        params = {"user_source_group_id": self.user_source_id}

        return self.sql_execute_fetch_all(sql, params, to_dict=True)

    @staticmethod
    def get_partneruserconsentlog_data(columns_and_values, selected_columns=["*"]):

        conditions = " AND ".join(
            [f"{column} = %s" for column in columns_and_values.keys()]
        )

        selected_columns_str = ", ".join(selected_columns)

        sql = f"""
                select {selected_columns_str} from lendenapp_partneruserconsentlog lp
                join lendenapp_customuser lc on lc.id = lp.investor_id 
                WHERE {conditions}
            """

        params = tuple(columns_and_values.values())

        return InvestorMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def update_partneruserconsentlog_data(unique_id, key, value):
        query = (
            """
                       UPDATE lendenapp_partneruserconsentlog
                       SET """
            + key
            + """=%(value)s
                       where unique_id = %(unique_id)s;
                       """
        )

        params = {"unique_id": unique_id, "value": value}

        InvestorMapper().execute_sql(query, params)

    def insert_partneruserconsentlog(self, data):

        sql = """insert into lendenapp_partneruserconsentlog (created_date, 
        updated_date, unique_id, details, otp, otp_count, status, 
        otp_expiry_time, investor_id, partner_id, user_source_group_id, 
        consent_type)
        values (now(), now(), %(unique_id)s, %(details)s ,%(otp)s,
        %(otp_count)s, %(status)s, %(otp_expiry_time)s, %(investor_id)s, 
        %(partner_id)s, %(user_source_group_id)s, %(consent_type)s) 
        returning unique_id, otp;"""

        return self.sql_execute_fetch_one(sql, data, to_dict=True)

    def get_mandate_details(self, columns_and_values, selected_columns=["*"]):
        conditions = " AND ".join(
            [f"{column} = %s" for column in columns_and_values.keys()]
        )

        selected_columns_str = ", ".join(selected_columns)

        sql = f"""
                    SELECT {selected_columns_str}
                    FROM lendenapp_userupimandate
                    WHERE {conditions}
                """

        params = tuple(columns_and_values.values())
        return self.sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def insert_into_payment_link(data):
        data["invoice_id"] = data.get("invoice_id", "")
        columns = ", ".join(data.keys())
        values = ", ".join(["%s"] * len(data))

        sql = (
            f"INSERT INTO lendenapp_paymentlink "
            f"({columns}) VALUES ({values}) RETURNING id"
        )

        return InvestorMapper().sql_execute_fetch_one(
            sql, list(data.values()), index_result=True
        )

    def get_reference_details(self, _type):
        sql = """
               select
                    name as full_name,
                    dob as nominee_dob,
                    relation as relationship,
                    type as nominee_type,
                    encoded_mobile as mobile_number,
                    encoded_email as nominee_email,
                    comment
                from
                    lendenapp_reference lr
                where
                user_id = %(user_id)s 
                and type = %(type)s
              """
        params = {
            "user_source_group_id": self.user_source_id,
            "user_id": self.investor_pk,
            "type": _type,
        }
        if self.user_source_id:
            sql += " and user_source_group_id =  %(user_source_group_id)s"

        return self.sql_execute_fetch_one(sql, params, to_dict=True)

    def insert_into_reference(self, request_data):
        current_dtm = get_current_dtm()
        comment = request_data.get("comment")
        sql = """
                         INSERT INTO lendenapp_reference (
                            name, dob, relation, user_id, comment, created_date,
                            updated_date, user_source_group_id, type, 
                            encoded_email, encoded_mobile, email, mobile_number
                            )
                         VALUES (
                        %(name)s, %(dob)s, %(relation)s, %(user_id)s, 
                        %(comment)s, %(created_date)s, %(updated_date)s, 
                        %(user_source_group_id)s, %(type)s, %(encoded_email)s, 
                        %(encoded_mobile)s, %(email)s, %(mobile_number)s
                        )
                      """
        params = {
            "name": request_data.get("full_name"),
            "encoded_email": request_data.get("encoded_email"),
            "dob": request_data.get("nominee_dob"),
            "encoded_mobile": request_data.get("encoded_mobile"),
            "relation": request_data.get("nominee_relation"),
            "user_id": self.investor_pk,
            "comment": str(comment) if comment is not None else None,
            "created_date": current_dtm,
            "updated_date": current_dtm,
            "user_source_group_id": self.user_source_id,
            "type": request_data.get("type"),
            "email": request_data.get("nominee_email"),
            "mobile_number": request_data.get("mobile_number"),
        }
        row_count = self.execute_sql(sql=sql, params=params, return_rows_count=True)
        return row_count

    def update_reference(self, request_data):
        current_dtm = get_current_dtm()
        comment = request_data.get("comment")
        sql = """
                        UPDATE lendenapp_reference
                        SET
                            name = %(name)s,
                            encoded_email = %(encoded_email)s,
                            email = %(email)s,
                            dob = %(dob)s,
                            encoded_mobile = %(encoded_mobile)s,
                            mobile_number = %(mobile_number)s,
                            comment = %(comment)s,
                            updated_date = %(updated_date)s,
                            relation = %(relation)s
                        WHERE 
                            user_id = %(user_id)s and 
                            user_source_group_id = %(user_source_group_id)s and
                            type = %(type)s
                    """
        params = {
            "name": request_data["full_name"],
            "encoded_email": request_data.get("encoded_email"),
            "email": request_data.get("nominee_email"),
            "dob": request_data.get("nominee_dob"),
            "encoded_mobile": request_data.get("encoded_mobile"),
            "mobile_number": request_data.get("mobile_number"),
            "comment": str(comment) if comment is not None else None,
            "updated_date": current_dtm,
            "user_id": self.investor_pk,
            "user_source_group_id": self.user_source_id,
            "type": request_data.get("type"),
            "relation": request_data.get("nominee_relation"),
        }
        row_count = self.execute_sql(sql=sql, params=params, return_rows_count=True)
        return row_count

    @staticmethod
    def get_bank_name_return_id(columns_and_values, selected_columns=["*"]):
        conditions = " AND ".join(
            [f"{column} = %s" for column in columns_and_values.keys()]
        )

        selected_columns_str = ", ".join(selected_columns)

        sql = f"""
                    SELECT {selected_columns_str}
                    FROM lendenapp_bank
                    WHERE {conditions}
                """

        params = tuple(columns_and_values.values())
        return InvestorMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def get_data(
        table_name,
        columns_and_values,
        selected_columns=["*"],
        order_by=None,
        all_result=False,
        for_update=False,
        logical_operator="AND",
        desc_order=False,
        return_value_only=False,
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
            return InvestorMapper().sql_execute_fetch_all(sql, params, to_dict=True)

        if return_value_only:
            return InvestorMapper().sql_execute_fetch_one(
                sql, params, index_result=True
            )

        return InvestorMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def insert_data(table_name, data):
        columns = ", ".join(data.keys())
        values = ", ".join(["%s"] * len(data))

        sql = f"INSERT INTO {table_name} " f"({columns}) VALUES ({values}) RETURNING id"

        return InvestorMapper().sql_execute_fetch_one(
            sql, list(data.values()), index_result=True
        )

    @staticmethod
    def update_data(table_name, data, condition, returning="id"):
        update_data = ", ".join([f"{key} = %({key})s" for key in data.keys()])
        filter_data = " AND ".join([f"{key} = %({key})s" for key in condition.keys()])
        sql = f"""
                        UPDATE {table_name}
                        SET {update_data}
                        WHERE {filter_data}
                        RETURNING {returning};
                    """
        params = {**condition, **data}
        return InvestorMapper().sql_execute_fetch_one(sql, params, index_result=True)

    def get_bank_detail_for_investor(self, selected_columns):
        selected_columns_str = ", ".join(selected_columns)
        sql = f"""SELECT {selected_columns_str} FROM lendenapp_bankaccount lb
            left join lendenapp_bank lb2 on lb2.id = lb.bank_id
            where lb.user_source_group_id = %(user_source_group_id)s
            AND lb.is_active = TRUE
            """
        params = {"user_source_group_id": self.user_source_id}
        return self.sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def get_upi_debit_transaction_details(mandate_id):
        sql = """
            SELECT 
                txn_status, amount, code,
                created_dtm, updated_dtm, execute_request_id
            FROM lendenapp_upimandatetransactionlog
            WHERE mandate_id = %(mandate_id)s
            ORDER BY execute_txn_dtm;
        """
        return InvestorMapper().sql_execute_fetch_all(
            sql, params={"mandate_id": mandate_id}, to_dict=True
        )

    @staticmethod
    def validate_investor_referral_data(
        source, selected_cols, encoded_mobile=None, user_id=None, get_account=False
    ):
        selected_col_str = ",".join(selected_cols)
        sql = f"""
            SELECT {selected_col_str}
            FROM lendenapp_customuser lc
            JOIN lendenapp_user_source_group lusg ON lc.id = lusg.user_id 
            join lendenapp_source ls on lusg.source_id = ls.id
        """

        if get_account:
            sql += """ join lendenapp_account la on la.user_source_group_id = lusg.id"""

        params = {"source": source}
        sql += """ WHERE ls.source_name = %(source)s"""

        if user_id:
            sql += " AND lc.user_id = %(user_id)s"
            params["user_id"] = user_id
        else:
            sql += " AND lc.encoded_mobile = %(encoded_mobile)s"
            params["encoded_mobile"] = encoded_mobile

        return InvestorMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    def update_notification_status(self, notification_ids=None):
        sql = """
            UPDATE lendenapp_notification
            SET status = %(update_status)s, updated_date = %(updated_date)s, 
            click_count = 1
            WHERE user_source_group_id = %(user_source_group_id)s 
            AND to_user_id = %(to_user_id)s
            AND status = %(status)s             
        """
        params = {
            "user_source_group_id": self.user_source_id,
            "to_user_id": self.investor_pk,
            "status": NotificationStatus.UNREAD,
            "update_status": NotificationStatus.READ,
            "updated_date": "now()",
        }
        if notification_ids:
            sql += " AND id =ANY(%(notification_ids)s)"
            params["notification_ids"] = tuple(notification_ids)
        sql += " RETURNING id"

        params = DataLayerUtils().prepare_sql_params(params)
        return self.sql_execute_fetch_all(sql, params, to_dict=True)

    def get_investor_transaction_detail(self):
        sql = """
                SELECT user_source_group_id, status, type
                FROM lendenapp_transaction lt
                WHERE user_source_group_id = %(user_source_group_id)s
                  AND "type" = %(type)s
                  AND status = %(status)s
                
                UNION ALL
                
                SELECT user_source_group_id, status, type
                FROM lendenapp_transaction lt
                WHERE user_source_group_id = %(user_source_group_id)s
                  AND "type" = %(type)s
                  AND transaction_id >= 'LPO'
                  AND transaction_id < 'LPP'
                  AND status =ANY(%(statuses)s);

                """
        params = {
            "user_source_group_id": self.user_source_id,
            "type": TransactionType.ADD_MONEY,
            "statuses": [TransactionStatus.COMPLETED, TransactionStatus.PROCESSING],
            "status": TransactionStatus.SUCCESS,
        }

        params = DataLayerUtils().prepare_sql_params(params)
        return self.sql_execute_fetch_one(sql, params, to_dict=True)

    def get_account_notification(self, status=None):
        """
        Retrieve notifications for a specific user and task.

        :param status: Optional. List of notification statuses to filter.
        :return: List of notifications matching the specified criteria.
        """
        notification_query = """   
            SELECT id, from_user_id, to_user_id, user_source_group_id, message, 
            "type", status, click_count, 
            created_date at time zone %(indian_time)s as created_date
            FROM lendenapp_notification
            WHERE user_source_group_id = %(user_source_group_id)s
            AND to_user_id = %(to_user_id)s
            """

        query_params = {
            "user_source_group_id": self.user_source_id,
            "to_user_id": self.investor_pk,
            "indian_time": TimeZone.indian_time,
        }

        if status:
            notification_query += """ AND status =ANY(%(status)s) """
            query_params.update({"status": tuple(status)})

        query_params = DataLayerUtils().prepare_sql_params(query_params)
        return self.sql_execute_fetch_all(
            notification_query, query_params, to_dict=True
        )

    @staticmethod
    def get_active_task_using_investor_id_and_cp_id(investor_user_id, cp_user_id):

        sql = """
            select lusg.id as user_source_id, lusg.status, lc3.id as cp_user_pk, lc3.user_id cp_user_id,
            lc2.partner_id, lc.first_name, lc.encoded_email, lc.encoded_mobile, lc.user_id,
            lc3.first_name cp_name, lc3.encoded_email cp_email, lc3.encoded_mobile cp_mobile
            from lendenapp_user_source_group lusg  
            join lendenapp_customuser lc on lc.id = lusg.user_id 
            join lendenapp_channelpartner lc2 
            on lc2.id = lusg.channel_partner_id 
            join lendenapp_customuser lc3 on lc2.user_id  = lc3.id 
            where lc.user_id= %(investor_user_id)s 
            and lc3.user_id = %(cp_user_id)s
        """

        params = {"investor_user_id": investor_user_id, "cp_user_id": cp_user_id}

        return InvestorMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def get_ops_user_obj_by_email_and_pass(encoded_email, group_id):
        query = """
                    select lc.id, lc."password", lc.first_name from lendenapp_customuser lc  
                    join lendenapp_customuser_groups lcg on lc.id = lcg.customuser_id 
                    where lcg.group_id = %(group_id)s and lc.encoded_email=%(encoded_email)s;
                    """
        params = {"group_id": group_id, "encoded_email": encoded_email}

        return InvestorMapper().sql_execute_fetch_one(query, params, to_dict=True)

    @staticmethod
    def get_withdrawal_transactions_details(
        withdrawal_transactions, status, transaction_type
    ):
        sql = """
            SELECT lt.id as txn_id_pk, lt.type transaction_type,
            lt.user_source_group_id as txn_user_source_id, lb.ifsc_code, 
            lb.name, lb.number, lb.type, lc.first_name,
            lc.encoded_email, 
            lt.user_source_group_id as transaction_user_source_id, 
            lc.encoded_mobile,
            la.user_source_group_id as account_user_source_id, 
            lb.user_source_group_id as bank_account_user_source_id,
            lc.id, lt.amount, lt.transaction_id
            FROM lendenapp_transaction lt INNER JOIN lendenapp_customuser lc ON
            lt.from_user_id = lc.id
            INNER JOIN lendenapp_account la ON lc.id = la.user_id
            INNER JOIN public.lendenapp_bankaccount lb on la.bank_account_id = lb.id
            WHERE lt.status = %(status)s AND lt.transaction_id = ANY(%(withdrawal_transactions)s) 
            AND lt.type = ANY(%(transaction_type)s)
            AND la.balance >= 0.0 AND la.user_source_group_id = lt.user_source_group_id 
            AND lc.id <> ALL(%(block_user)s)
            AND lb.is_active = TRUE AND lt.date <= NOW();
        """

        params = {
            "withdrawal_transactions": withdrawal_transactions,
            "status": status,
            "transaction_type": transaction_type,
            "block_user": TransactionBlockForUser.user_pk_list,
        }

        params = DataLayerUtils().prepare_sql_params(params)
        return InvestorMapper().sql_execute_fetch_all(sql, params, to_dict=True)

    @staticmethod
    def update_withdrawal_status(remarks_list, batch_reference_number, update_status):
        sql = """
            UPDATE lendenapp_transaction lt
            SET type_id = %(batch_reference_number)s, status = %(update_status)s, 
            updated_date=NOW() WHERE lt.transaction_id =ANY(%(remarks_list)s);
        """
        params = {
            "remarks_list": remarks_list,
            "batch_reference_number": batch_reference_number,
            "update_status": update_status,
        }

        params = DataLayerUtils().prepare_sql_params(params)
        InvestorMapper().execute_sql(sql, params)

    @staticmethod
    def insert_into_withdrawal_summary(
        user_count,
        transaction_sum,
        transaction_count,
        file_name,
        batch_reference_number,
    ):
        sql = """
                insert into lendenapp_withdrawalsummary 
                (transaction_sum, user_count, transaction_count, 
                batch_reference_number, withdrawal_datetime, 
                withdrawal_filename_reference) VALUES (%(transaction_sum)s,
                %(user_count)s, %(transaction_count)s, 
                %(batch_reference_number)s, now(), 
                %(file_name)s);
        """
        params = {
            "user_count": user_count,
            "transaction_sum": transaction_sum,
            "transaction_count": transaction_count,
            "file_name": file_name,
            "batch_reference_number": batch_reference_number,
        }

        InvestorMapper().execute_sql(sql, params)

    @staticmethod
    def check_if_txn_pk_exists(withdrawal_transactions_list, action=None, status=None):
        sql = """
            SELECT DISTINCT lt.transaction_id from lendenapp_transactionaudit wa 
            JOIN lendenapp_transaction lt ON wa.transaction_id = lt.id
            WHERE lt.transaction_id =ANY(%(withdrawal_transactions_list)s)
        """

        params = {"withdrawal_transactions_list": list(withdrawal_transactions_list)}

        if action:
            sql += """ AND action = %(action)s"""
            params["action"] = action

        if status:
            sql += """ AND lt.status=%(status)s"""
            params["status"] = status

        return InvestorMapper().sql_execute_fetch_all(sql, params, to_dict=False)

    def get_latest_cashfree_request_data(self):

        sql = """ select json_request, status, json_response 
                  from lendenapp_thirdpartycashfree 
                  where action = %(action)s 
                  and user_source_group_id = %(user_source_group_id)s 
                  and user_id = %(user_id)s order by id desc limit 1
              """
        params = {
            "action": CashfreeConstant.ACTION["BANK_ACCOUNT"],
            "user_source_group_id": self.user_source_id,
            "user_id": self.investor_pk,
        }

        return self.sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def get_bank_details_and_user_source_id(user_source_ids):

        sql = """ select lb.user_id, lb.number as beneficiary_ac_no, 
                  lb.ifsc_code as beneficiary_ifsc, lb.user_source_group_id,
                  lb.name as lender_name
                  from lendenapp_bankaccount lb
                  where lb.user_source_group_id =ANY(%(user_source_ids)s)
                  AND lb.is_active = TRUE
              """

        params = {"user_source_ids": user_source_ids}

        params = DataLayerUtils().prepare_sql_params(params)
        return InvestorMapper().sql_execute_fetch_all(sql, params, to_dict=True)

    @staticmethod
    def get_data_from_user_source_id(user_source_id, columns, user_id=None):
        columns_str = ", ".join([f"{column}" for column in columns])

        sql = f"""
            SELECT {columns_str} FROM lendenapp_customuser lc 
            JOIN lendenapp_user_source_group lusg 
            ON lusg.user_id = lc.id
            JOIN lendenapp_source ls 
            ON lusg.source_id = ls.id
            WHERE lusg.id = %(user_source_id)s
        """
        params = {"user_source_id": user_source_id}

        if user_id:
            params["user_id"] = user_id
            sql += " and lc.user_id = %(user_id)s"

        return InvestorMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def get_user_account_data(investor_pk, user_source_id, cp_pk):
        sql = """
        select lc.id, lc.first_name, lc.user_id, la.number, la.balance
        from lendenapp_customuser lc
        left join lendenapp_account la on la.user_id = lc.id
        where (lc.id = %(investor_pk)s 
        and la.user_source_group_id = %(user_source_group_id)s ) or lc.id = %(cp_pk)s
        """

        params = {
            "investor_pk": investor_pk,
            "user_source_group_id": user_source_id,
            "cp_pk": cp_pk,
        }

        return InvestorMapper().sql_execute_fetch_all(sql, params, to_dict=True)

    @staticmethod
    def get_offline_payment_list(partner_code, investor_id, limit_filters):
        sql = """
            SELECT 
                opr.request_id,
                opr.amount AS requested_amount, 
                opr.payment_mode, 
                opr.deposit_date, 
                opr.reference_number,
                opr.status, 
                opr.comment,
                opr.created_date
            FROM lendenapp_offline_payment_request opr
            JOIN lendenapp_user_source_group lusg 
            ON opr.user_source_group_id = lusg.id
            JOIN lendenapp_source ls ON lusg.source_id = ls.id
            WHERE ls.source_name = %(partner_code)s
                AND opr.investor_id = %(investor_id)s
            ORDER BY opr.id
            """

        params = {"partner_code": partner_code, "investor_id": investor_id}

        limit = limit_filters.get("limit")
        offset = limit_filters.get("offset")
        if limit is not None and offset is not None:
            params["limit"] = limit
            params["offset"] = offset
            sql += """ LIMIT %(limit)s OFFSET %(offset)s"""

        return InvestorMapper().sql_execute_fetch_all(sql, params, to_dict=True)

    @staticmethod
    def get_all_data(
        table_name, selected_columns=["*"], order_by=None, single_col=False
    ):
        selected_columns_str = ", ".join(selected_columns)

        sql = f"""
                    SELECT {selected_columns_str}
                    FROM {table_name}
               """

        if order_by:
            sql += """ ORDER BY """ + order_by

        if single_col:
            return InvestorMapper().sql_execute_fetch_all(
                sql, {}, fetch_single_column=True
            )

        return InvestorMapper().sql_execute_fetch_all(sql, {}, to_dict=True)

    @staticmethod
    def get_data_from_transaction_ids(transaction_ids, transaction_types, status):
        sql = """
                select la.*, lt.amount, lt.transaction_id 
                from lendenapp_transaction lt
                join lendenapp_account la 
                on la.user_source_group_id = lt.user_source_group_id
                where lt.transaction_id=ANY(%(transaction_ids)s)
                and lt.type =ANY(%(transaction_types)s)
                and lt.status = %(status)s;
              """

        params = {
            "transaction_ids": tuple(transaction_ids),
            "transaction_types": tuple(transaction_types),
            "status": status,
        }

        params = DataLayerUtils().prepare_sql_params(params)
        return InvestorMapper().sql_execute_fetch_all(sql, params, to_dict=True)

    def bulk_update_transaction_status(self, transaction_id_list, status, remark=None):
        sql = """
                update lendenapp_transaction
                set status=%(status)s, updated_date=%(updated_date)s
                """

        if remark:
            sql += ", remark=%(remark)s"

        sql += " where transaction_id =ANY(%(transaction_ids)s)"

        params = {
            "transaction_ids": tuple(transaction_id_list),
            "status": status,
            "updated_date": get_current_time_in_ist(dtm_format="%Y-%m-%d %H:%M:%S"),
            "status_date": get_todays_date_in_ist(),
        }

        if remark:
            params["remark"] = remark

        params = DataLayerUtils().prepare_sql_params(params)
        self.execute_sql(sql, params)

    @staticmethod
    def get_user_data(user_id, source, partner_id=None):
        sql = f"""
                SELECT 
                    lusg.id as user_source_id, lc.id as user_pk, lc3.encoded_mobile as cp_mobile,
                    lc3.first_name as cp_name, lc.first_name as investor_name,
                    lc3.id as cp_user_pk
                FROM lendenapp_customuser lc
                JOIN lendenapp_user_source_group lusg ON lusg.user_id = lc.id
                JOIN lendenapp_source ls ON lusg.source_id = ls.id
                LEFT JOIN lendenapp_channelpartner lc2 
                ON lusg.channel_partner_id = lc2.id
                LEFT JOIN lendenapp_customuser lc3
                ON lc2.user_id = lc3.id
                
                """

        conditions = """
                        where lc.user_id = %(user_id)s
                        and ls.source_name = %(source_name)s 
                    """

        params = {"user_id": user_id, "source_name": source}

        if partner_id:
            params["partner_id"] = partner_id
            conditions += " and lc2.partner_id = %(partner_id)s"

        sql += conditions

        return InvestorMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def get_investment_details_by_scheme_id(investor_id, scheme_id):
        sql = """
            select lt.description, lt.amount, lc2.partner_id, 
            lc.encoded_email as email, lc.first_name, ls.source_name as source,
            lc2.user_id as cp_pk, lusg.id as user_source_id,
            lc.is_family_member
            from lendenapp_customuser lc
            join lendenapp_user_source_group lusg on lc.id = lusg.user_id
            join lendenapp_transaction lt on lt.user_source_group_id = lusg.id
            left join lendenapp_channelpartner lc2
            on lc2.id = lusg.channel_partner_id 
            join lendenapp_source ls on lusg.source_id = ls.id
            where lc.user_id = %(investor_id)s and lt.type =ANY(%(type)s)
            and lt.description ~ %(scheme_id)s;
        """

        params = {
            "investor_id": investor_id,
            "scheme_id": scheme_id,
            "type": [
                TransactionType.FMPP_INVESTMENT,
                TransactionType.MANUAL_LENDING,
                TransactionType.AUTO_LENDING,
            ],
        }

        params = DataLayerUtils().prepare_sql_params(params)
        return InvestorMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def insert_multiple_data(table_name, data_list):
        # Assuming all dictionaries in data_list have the same keys
        columns = ", ".join(data_list[0].keys())
        values_template = ", ".join(["%s"] * len(data_list[0]))

        sql = f"INSERT INTO {table_name} ({columns}) VALUES "
        placeholders = ", ".join([f"({values_template})"] * len(data_list))

        sql += placeholders
        flat_values = [value for data in data_list for value in data.values()]
        return InvestorMapper().execute_sql(
            sql, params=flat_values, return_rows_count=True
        )

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

        return InvestorMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def get_source_and_task_from_transaction_id(transaction_id, selected_columns=["*"]):
        selected_columns_str = ", ".join(selected_columns)

        sql = f"""
            SELECT {selected_columns_str}
            FROM lendenapp_transaction ltr JOIN 
            lendenapp_user_source_group lusg ON 
            ltr.user_source_group_id = lusg.id
            JOIN lendenapp_source ls ON lusg.source_id = ls.id 
            WHERE ltr.transaction_id=%(transaction_id)s;
        """

        params = {"transaction_id": transaction_id}

        return InvestorMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def user_with_group_name(condition, selected_column=None):
        if not selected_column:
            selected_column = ["*"]
        selected_columns_str = ", ".join(selected_column)

        sql = f"""
            select {selected_columns_str} from lendenapp_customuser_groups lcg 
            join auth_group ag on lcg.group_id = ag.id 
            where ag."name" = ANY(%(group_name)s) and lcg.customuser_id = %(user_pk)s
        """
        params = DataLayerUtils().prepare_sql_params(condition)
        return InvestorMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def get_customuser_data(
        columns_and_values, selected_column=None, logical_operator="AND"
    ):
        if not selected_column:
            selected_column = ["*"]
        selected_columns_str = ", ".join(selected_column)

        conditions = f" {logical_operator} ".join(
            [f"{column} = %s" for column in columns_and_values.keys()]
        )

        sql = f"""
            select {selected_columns_str} from lendenapp_customuser lc
            join lendenapp_customuser_groups lcg on lcg.customuser_id = lc.id 
            join auth_group ag on lcg.group_id = ag.id 
            where {conditions}
        """
        params = tuple(columns_and_values.values())
        return InvestorMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    def fetch_investor_count(self, search, search_query_type):
        sql = f"""
            Select count(lusg.id)
            from lendenapp_customuser lc
            join lendenapp_user_source_group lusg on lc.id = lusg.user_id
            WHERE lusg.group_id = %(group_id)s
        """
        params = {"group_id": UserGroup.LENDER}

        if search:
            sql += f" and {self.dashboard_search_sql_query(params, search, search_query_type)}"

        return self.sql_execute_fetch_one(sql, params, index_result=True)

    def fetch_investor_details(self, data):
        sql = f"""
            select lc2.partner_id, ls.source_name as partner_code,
            lc3.first_name as cp_name, lc.user_id, 
            lc.first_name, lc.gender, lc.encoded_mobile as mobile_number, lc.encoded_email as email, 
            lc.dob, lc.encoded_pan as pan, lc.type, 
            lc.gross_annual_income, 
            la2.user_source_group_id, lt.checklist, 
            la2.created_date::date, la2.balance, la2.status, 
            la2.listed_date, la2.number
            from lendenapp_user_source_group lusg 
            join lendenapp_account la2 on lusg.id = la2.user_source_group_id 
            join lendenapp_task lt on lt.user_source_group_id = lusg.id
            join lendenapp_source ls on ls.id = lusg.source_id 
            join lendenapp_customuser lc on lc.id = lusg.user_id
            left join lendenapp_channelpartner lc2 on 
            lc2.id = lusg.channel_partner_id  
            left join lendenapp_customuser lc3 on lc3.id = lc2.user_id 
            WHERE lusg.group_id = %(group)s 
            """

        params = {"group": UserGroup.LENDER}

        search = data.get("search")
        search_query_type = data.get("search_query_type")

        if search:
            sql += f" and {self.dashboard_search_sql_query(params, search, search_query_type)}"

        if not data["is_download"]:
            params["limit"] = data["limit"]
            params["offset"] = data["offset"]
            sql += " LIMIT %(limit)s OFFSET %(offset)s"

        return self.sql_execute_fetch_all(sql, params, to_dict=True)

    @staticmethod
    def fetch_scheme_and_mandate_details(
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
            return InvestorMapper().sql_execute_fetch_all(sql, params, to_dict=True)

        return InvestorMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    def fetch_blocked_balance_for_investor(self, investment_type=None):
        sql = """
            SELECT
                sum(amount) blocked_balance
            FROM lendenapp_schemeinfo lsi
            INNER JOIN lendenapp_user_source_group lusg ON lusg.id = lsi.user_source_group_id
            WHERE lusg.user_id=%(user_pk)s and lsi.status=%(status)s  
        """

        params = {"status": SchemeStatus.INITIATED, "user_pk": self.investor_pk}

        if investment_type:
            params["investment_type"] = investment_type
            sql += " and lsi.investment_type=%(investment_type)s"

        return self.sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def get_investor_details(data, selected_columns=None):
        if not selected_columns:
            selected_columns = ["*"]

        selected_col_str = ",".join(selected_columns)

        sql = f"""
            SELECT
                {selected_col_str}
            FROM lendenapp_user_source_group lusg
            JOIN lendenapp_source ls ON ls.id = lusg.source_id
            JOIN lendenapp_customuser lc ON lc.id = lusg.user_id
            LEFT JOIN lendenapp_channelpartner cp ON cp.id = lusg.channel_partner_id
        """
        params = {
            "user_id": data["user_id"],
            "group_id": UserGroup.LENDER,
        }

        if not data["is_active"]:
            sql += (
                " WHERE lc.user_id = %(user_id)s "
                "AND lusg.group_id = %(group_id)s "
                "AND lusg.status <> %(status)s"
            )
            params["status"] = UserGroupSourceStatus.CLOSED
            return InvestorMapper().sql_execute_fetch_all(sql, params, to_dict=True)

        else:
            sql += (
                " WHERE lc.user_id = %(user_id)s "
                "AND lusg.id = %(user_source_group_id)s "
                "AND lusg.group_id = %(group_id)s "
                "AND lusg.status <> %(status)s"
            )
            params["user_source_group_id"] = data["user_source_id"]
            params["status"] = UserGroupSourceStatus.ACTIVE

            return InvestorMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def get_user_and_bank_detail(columns_and_values, selected_column=None):
        if not selected_column:
            selected_column = ["*"]
        selected_columns_str = ", ".join(selected_column)

        conditions = f" AND ".join(
            [f"{column} = %s" for column in columns_and_values.keys()]
        )

        sql = f"""
            select {selected_columns_str} 
            from lendenapp_bankaccount lb
            join lendenapp_customuser lc on lc.id = lb.user_id 
            where {conditions}
        """

        params = tuple(columns_and_values.values())
        return InvestorMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def fetch_user_source_group_info(user_source_group_id):
        sql = """ 
            SELECT lusg.user_id, ls.source_name as name, lc.user_id as cp_user_pk
            FROM lendenapp_user_source_group lusg
            JOIN lendenapp_source ls ON ls.id = lusg.source_id
            left join lendenapp_channelpartner lc on lc.id = lusg.channel_partner_id
            where lusg.id = %(user_source_group_id)s
        """

        param = {"user_source_group_id": user_source_group_id}

        return InvestorMapper().sql_execute_fetch_one(sql, param, to_dict=True)

    @staticmethod
    def update_mandate_status(mandate_tracker_id, mandate_status, updated_status):

        sql = f"""
            UPDATE lendenapp_mandate
            SET mandate_status = %(status)s,
                updated_date = now()
            WHERE mandate_tracker_id = %(mandate_tracker_id)s
            AND mandate_status = %(mandate_status)s
            RETURNING id;
        """

        params = {
            "status": updated_status,
            "mandate_tracker_id": mandate_tracker_id,
            "mandate_status": mandate_status,
        }

        return InvestorMapper().sql_execute_fetch_one(sql, params, index_result=True)

    @staticmethod
    def update_data_v2(
        table_name, data, condition, returning="id", fetch_one_dict=False
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
        if fetch_one_dict:
            return InvestorMapper().sql_execute_fetch_one(sql, params, to_dict=True)
        return InvestorMapper().sql_execute_fetch_one(sql, params, index_result=True)

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
        return InvestorMapper().sql_execute_fetch_one(sql, params, index_result=True)

    def get_investor_and_cp_data(self):
        sql = """
                SELECT lc.first_name AS investor_name, lc.encoded_email,
                lc3.first_name AS cp_name, lc2.partner_id, lc.encoded_mobile, 
                lc3.user_id as cp_user_id, lc3.id as cp_pk, ls.source_name,
                lc3.encoded_email as cp_email, lc.id as user_pk, lc.user_id, 
                lc3.encoded_mobile as cp_mobile, lusg.id as user_source_id,
                lc.is_family_member
                FROM lendenapp_user_source_group lusg
                JOIN lendenapp_customuser lc ON lc.id = lusg.user_id
                JOIN lendenapp_source ls ON ls.id = lusg.source_id
                LEFT JOIN lendenapp_channelpartner lc2 
                ON lc2.id = lusg.channel_partner_id 
                LEFT JOIN lendenapp_customuser lc3 ON lc3.id = lc2.user_id
                WHERE lusg.id = %(user_source_id)s
            """

        params = {"user_source_id": self.user_source_id}

        return self.sql_execute_fetch_one(sql, params, to_dict=True)

    def get_user_balance_and_cp_name(self):
        sql = """
                SELECT la.balance, lc.first_name 
                FROM lendenapp_account la
                JOIN lendenapp_user_source_group lusg 
                ON la.user_source_group_id = lusg.id
                JOIN lendenapp_channelpartner lcp 
                ON lusg.channel_partner_id = lcp.id
                JOIN lendenapp_customuser lc ON lcp.user_id = lc.id
                WHERE lusg.id = %(user_source_id)s
              """

        params = {"user_source_id": self.user_source_id}

        return self.sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def update_scheme_data_for_tracker_id(tracker_id, data):
        sql = """
                UPDATE
                    lendenapp_otl_scheme_tracker
                SET loan_count=%(loan_count)s,
                amount_per_loan=%(amount_per_loan)s, updated_date=now()
                WHERE id=%(tracker_id)s
            """

        params = {
            "tracker_id": tracker_id,
            "loan_count": data["actual_loan_count"],
            "amount_per_loan": data["amount_per_loan"],
        }
        return InvestorMapper().execute_sql(sql, params, return_rows_count=True)

    @staticmethod
    def get_otl_schemes_from_loan_mapping(tracker_id, repayment_frequency):
        sql = """
                SELECT loan_id, loan_roi, ldc_score, loan_tenure::integer, borrower_name, 
                    %(repayment_frequency)s as repayment_frequency,
                    loan_amount, lent_amount as lending_amount, %(loan_tenure_type)s as loan_tenure_type
                FROM lendenapp_otl_scheme_loan_mapping
                WHERE otl_tracker_id=%(tracker_id)s and is_available = TRUE 
                and is_selected = TRUE and created_date > %(yesterday)s
                ORDER BY id
                """

        params = {
            "tracker_id": tracker_id,
            "loan_tenure_type": OTLInvestment.OTL_LOAN_TENURE_TYPE,
            "yesterday": get_current_dtm() - timedelta(days=1),
            "repayment_frequency": repayment_frequency,
        }
        return InvestorMapper().sql_execute_fetch_all(sql, params, to_dict=True)

    def get_tracking_data(self, scheme_id="", investment_type=None, for_update=False):
        sql = """                
                SELECT id , scheme_id , status, lending_amount, tenure, 
                    loan_tenure, preference_id, loan_count, batch_number,
                    transaction_id, amount_per_loan, COALESCE(product_type, 'MONTHLY') as product_type,
                    priority_order, prioritization_dtm, last_notification_dtm, next_notification, notification_count
                    FROM lendenapp_otl_scheme_tracker
                    WHERE is_latest = TRUE
                    AND user_source_group_id = %(user_source_id)s
                """

        params = {"user_source_id": self.user_source_id}

        if scheme_id:
            if for_update:
                sql += """ AND scheme_id = %(scheme_id)s FOR UPDATE NOWAIT;"""
            else:
                sql += """ AND scheme_id = %(scheme_id)s;"""
            params["scheme_id"] = scheme_id
        elif investment_type:
            sql += """ 
                    AND investment_type = %(investment_type)s 
                    AND status = 'INITIATED'
                    AND transaction_id is null;
                """
            params["investment_type"] = investment_type
        else:
            sql += """ 
                        AND status = 'INITIATED'
                        AND transaction_id is null
                    """

        return InvestorMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    def get_otl_scheme_info_data(self, scheme_id):
        sql = """                
                SELECT id , status, investment_type, 
                       tenure, amount
                FROM lendenapp_schemeinfo 
                WHERE user_source_group_id = %(user_source_id)s
                AND scheme_id = %(scheme_id)s
            """

        params = {"user_source_id": self.user_source_id, "scheme_id": scheme_id}

        return self.sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def generate_tracking_records(params):
        insert_sql = """
            INSERT INTO public.lendenapp_otl_scheme_tracker
            (scheme_id, batch_number, created_date, updated_date, is_latest, user_source_group_id, 
            preference_id, tenure, status, lending_amount, loan_tenure, transaction_id, 
            to_be_notified, notification_type, amount_per_loan, 
            investment_type, product_type, priority_order, prioritization_dtm, last_notification_dtm, next_notification, notification_count)
            VALUES(%(scheme_id)s, %(batch_number)s, now(), now(), true,  %(user_source_id)s, 
            %(preference_id)s, %(tenure)s, 'INITIATED', %(investment_amount)s, 
            %(loan_tenure)s, %(transaction_id)s, %(to_be_notified)s, %(notification_type)s,
             %(amount_per_loan)s, %(investment_type)s, %(product_type)s, %(priority_order)s, %(prioritization_dtm)s, %(last_notification_dtm)s, %(next_notification)s, %(notification_count)s) returning id ;
        """

        return InvestorMapper().sql_execute_fetch_one(
            insert_sql, params, index_result=True
        )

    @staticmethod
    def expire_otl_tracker_batch(scheme_id):

        sql = """
                update lendenapp_otl_scheme_tracker
                    set is_latest = false, status= 'EXPIRED', updated_date = now()
                    WHERE scheme_id = %(scheme_id)s and status = 'INITIATED';     
                """
        params = {"scheme_id": scheme_id}

        return InvestorMapper().execute_sql(sql, params, return_rows_count=True)

    @staticmethod
    def create_investment_transaction(params):
        sql = """
                       INSERT INTO lendenapp_transaction
                       (transaction_id, type, amount, date, from_user_id, 
                       user_source_group_id, to_user_id, status, status_date,
                       created_date, updated_date, description, type_id) 
                       VALUES (%(transaction_id)s, %(type)s, %(amount)s,
                        %(date)s, %(from_user_id)s, %(user_source_group_id)s, 
                        %(to_user_id)s, %(status)s, %(status_date)s,
                        %(created_date)s, %(updated_date)s, %(description)s, 
                        %(type_id)s) returning id;
                   """
        return InvestorMapper().sql_execute_fetch_one(sql, params, index_result=True)

    @staticmethod
    def dashboard_search_sql_query(params, search, search_query_type):
        search_query_map = {
            SearchKey.USER_ID: "lc.user_id = %(search)s",
            SearchKey.MOBILE_NO: "lc.encoded_mobile = %(search)s",
            SearchKey.EMAIL: "lc.encoded_email = %(search)s",
            SearchKey.PAN: "lc.encoded_pan = %(search)s",
        }

        params["search"] = search
        return search_query_map.get(search_query_type, "")

    @staticmethod
    def fetch_lender_for_refund(to_date, limit, offset):
        sql = """
         select lost.id,lc.user_id ,lc.mobile_number ,ls.source_name ,
         lost.scheme_id,lost.created_date ,lost.user_source_group_id,
         lost.status , lost.lending_amount,lost.transaction_id,lost.tenure,
         lost.loan_tenure from 
         lendenapp_otl_scheme_tracker lost join lendenapp_user_source_group lusg 
         on lusg.id=lost.user_source_group_id 
         join lendenapp_source ls on lusg.source_id =ls.id
         join lendenapp_customuser lc on lc.id = lusg.user_id 
         where is_latest 
         and lost.status =%(status_type)s 
         AND %(date)s - INTERVAL '1 days' >= (SELECT (MIN(lt.created_date) at TIME zone 'Asia/Kolkata')::date
         FROM lendenapp_otl_scheme_tracker lt
         WHERE lt.scheme_id = lost.scheme_id)
         """
        if limit:
            sql += " LIMIT %(limit)s"
        if offset:
            sql += " OFFSET %(offset)s"

        params = {
            "status_type": TransactionStatus.INITIATED,
            "date": to_date if to_date else get_todays_date_in_ist(),
            "limit": limit,
            "offset": offset,
        }

        return InvestorMapper().sql_execute_fetch_all(sql, params, to_dict=True)

    @staticmethod
    def update_otl_scheme_tracker(scheme_tracker_id):
        sql = """
         UPDATE lendenapp_otl_scheme_tracker
         SET status =%(status)s,
         to_be_notified = %(to_be_notified)s,
         updated_date = now()
         where id = %(scheme_tracker_id)s
         RETURNING transaction_id;
         """
        params = {
            "status": TransactionStatus.EXPIRED,
            "to_be_notified": ExpiredTransaction.FALSE,
            "scheme_tracker_id": scheme_tracker_id,
        }

        return InvestorMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def update_transaction(transaction_id):
        sql = """
             UPDATE lendenapp_transaction lt
             SET status = %(status)s,
             updated_date = now(),
             rejection_reason = %(reason)s
             WHERE lt.id =%(transaction_id)s
             AND lt.status = %(lt_status)s
             Returning id;
         """

        params = {
            "status": TransactionStatus.FAILED,
            "transaction_id": transaction_id,
            "lt_status": TransactionStatus.SCHEDULED,
            "reason": TransactionConstants.REJECTION_REASON["REFUND_OTL"],
        }

        result = InvestorMapper().sql_execute_fetch_one(sql, params, to_dict=True)
        return result

    @staticmethod
    def validate_scheme_tracker_id(scheme_tracker_ids, is_unblock):
        sql = """SELECT lost.id,lost.status as status,lost.scheme_id as scheme_id,
         lost.lending_amount as amount, lost.investment_type,
         ls.source_name as source,
         lusg.id as user_source_group_id,
         lusg.user_id as user_pk
         FROM lendenapp_otl_scheme_tracker lost 
         join lendenapp_user_source_group lusg
         on lost.user_source_group_id =lusg.id 
         join lendenapp_source ls on lusg.source_id =ls.id
         WHERE lost.id =ANY(%(scheme_tracker_id)s)
         AND is_latest
        """

        params = {"scheme_tracker_id": tuple(scheme_tracker_ids)}

        if not is_unblock:
            sql += """
            AND (CURRENT_TIMESTAMP at TIME zone 'Asia/Kolkata')::date - interval '1 days' >= (
            select (MIN(lt.created_date) at TIME zone 'Asia/Kolkata')::date
            from lendenapp_otl_scheme_tracker lt
            where lt.scheme_id = lost.scheme_id)
            """

        params = DataLayerUtils().prepare_sql_params(params)
        result = InvestorMapper().sql_execute_fetch_all(sql, params, to_dict=True)
        failed_ids = []
        # If result is not empty, process each record
        if result:
            failed_ids = [
                data["id"]
                for data in result
                if data["status"] in ("EXPIRED", "SUCCESS")
            ]
            result = [
                data for data in result if data["status"] not in ("EXPIRED", "SUCCESS")
            ]
        else:
            return failed_ids, result

        return failed_ids, result

    @staticmethod
    def update_schemeinfo(scheme_id, transaction_id):
        sql = """
                 update lendenapp_schemeinfo 
                 set status= %(status)s,
                 updated_date = now()
                 where scheme_id =%(scheme_id)s 
                 and transaction_id = %(transaction_id)s
                 and status = %(transaction_status)s
                 Returning id, created_date;
         """
        params = {
            "status": TransactionStatus.CANCELLED,
            "scheme_id": scheme_id,
            "transaction_id": transaction_id,
            "transaction_status": TransactionStatus.INITIATED,
        }
        return InvestorMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def fetch_otl_scheme_data(
        investor_source_id,
        limit,
        offset,
        investment_type=(
            FMPPInvestmentType.ONE_TIME_LENDING,
            FMPPInvestmentType.MEDIUM_TERM_LENDING,
        ),
    ):

        sql = f"""
                WITH total_count_cte AS (
                    SELECT COUNT(*) AS total_count
                    FROM lendenapp_schemeinfo
                    WHERE user_source_group_id = %(investor_source_id)s
                    AND investment_type=ANY(%(investment_type)s)
                    AND status = ANY(%(status)s)
                )
                SELECT
                    lsi.scheme_id, lsi.tenure, lsi.preference_id,
                    lsi.created_date::date AS created_date, lsi.amount,
                    lost.loan_tenure,
                    (SELECT lt.created_date::date
                     FROM lendenapp_transaction lt
                     WHERE lt.reversal_txn_id = lsi.transaction_id) AS refund_date,
                    CASE
                        WHEN lsi.status = 'INITIATED' THEN 'PENDING'
                        ELSE lsi.status
                    END AS status,
                    CASE
                        WHEN lsi.transaction_id is NULL THEN False
                        ELSE True
                    END AS blocked_amount,
                    tc.total_count,
                    lsi.investment_type,
                    COALESCE(lost.product_type, 'MONTHLY') as product_type 
                FROM lendenapp_schemeinfo lsi JOIN lendenapp_otl_scheme_tracker 
                lost on lsi.scheme_id=lost.scheme_id
                CROSS JOIN total_count_cte tc
                WHERE lsi.user_source_group_id = %(investor_source_id)s
                  AND lsi.investment_type =ANY(%(investment_type)s)
                  AND lsi.status = ANY(%(status)s)
                  AND lost.is_latest=True
                ORDER BY lsi.created_date DESC
                LIMIT %(limit)s OFFSET %(offset)s
            """

        params = {
            "status": [TransactionStatus.CANCELLED, TransactionStatus.INITIATED],
            "investment_type": investment_type,
            "investor_source_id": investor_source_id,
            "limit": limit,
            "offset": offset,
        }

        prepared_params = DataLayerUtils().prepare_sql_params(params)
        return InvestorMapper().sql_execute_fetch_all(
            sql, prepared_params, to_dict=True
        )

    @staticmethod
    def get_data_for_redirection_link(scheme_id):
        sql = """
                SELECT 
                    lc.user_id as investor_id, lc.encoded_mobile, lc.first_name,
                    lc.encoded_email as lender_email, lusg.id as user_source_id, 
                    lc.id as user_pk, ls.source_name, lc3.user_id as cp_user_id, 
                    lc3.id as cp_pk, lc3.encoded_email as cp_email, 
                    lost.scheme_id, lost.batch_number, lc3.first_name as cp_name,
                    lost.user_source_group_id, lost.preference_id, lost.tenure, 
                    lost.loan_tenure, lost.lending_amount as investment_amount, 
                    lc2.partner_id as partner_id, lost.status as tracker_status,
                    lost.investment_type, lost.id as tracker_id, lost.priority_order,
                    lc.is_family_member
                FROM 
                    lendenapp_otl_scheme_tracker lost
                JOIN 
                    lendenapp_user_source_group lusg 
                    ON lusg.id = lost.user_source_group_id
                JOIN 
                    lendenapp_source ls ON ls.id = lusg.source_id
                JOIN 
                    lendenapp_customuser lc ON lc.id = lusg.user_id 
                LEFT JOIN 
                    lendenapp_channelpartner lc2
                    ON lusg.channel_partner_id = lc2.id
                LEFT JOIN 
                    lendenapp_customuser lc3 ON lc3.id = lc2.user_id
                WHERE 
                    lost.scheme_id = %(scheme_id)s
                    AND is_latest
        """

        params = {"scheme_id": scheme_id}

        return InvestorMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def get_pending_aml_data():
        sql = """
            WITH RankedEntries AS (
                SELECT
                    lc.user_id,
                    lc.ucic_code,
                    CASE WHEN la2.status = 'LISTED' THEN 'EXISTING USER'
                    ELSE 'NEW USER' END AS account_status,
                    lc.encoded_pan AS pan,
                    lu2.poi_name,
                    lu2.poa_name,
                    lb."number" AS account_number,
                    la.name_score,
                    la.dob_score,
                    la.pan_score,
                    la.address_score,
                    la.matched_name,
                    la.matched_dob,
                    la.matched_pan,
                    la.matched_address,
                    la.match_status,
                    lu.overall_is_pep,
                    lu.aml_category AS overall_match_status,
                    lu.user_source_group_id,
                    lu.aml_tracking_id,
                    ls.source_name AS source,
                    la.entity_source,
                    lu.tracking_id as kyc_tracking_id,
                    ROW_NUMBER() OVER (
                        PARTITION BY lu.user_source_group_id, la.entity_source
                        ORDER BY la.pan_score DESC, la.name_score DESC, la.id DESC
                    ) AS rn
                FROM
                    lendenapp_customuser lc
                JOIN
                    lendenapp_userkyctracker lu ON lu.user_id = lc.id
                LEFT JOIN
                    lendenapp_userkyc lu2 ON lu2.tracking_id = lu.tracking_id AND lu2.service_type = %(service_type)s
                JOIN
                    lendenapp_bankaccount lb ON lb.user_source_group_id = lu.user_source_group_id
                JOIN
                    lendenapp_account la2 on la2.user_source_group_id = lu.user_source_group_id
                JOIN
                    lendenapp_user_source_group lusg ON lusg.id = lu.user_source_group_id
                JOIN
                    lendenapp_source ls ON ls.id = lusg.source_id
                JOIN
                    lendenapp_aml la ON la.tracking_id = lu.aml_tracking_id
                WHERE
                    lu.is_latest_kyc
                    AND lu.status = %(kyc_status)s
                    AND lu.aml_status = %(aml_status)s
            )
            SELECT
                user_id,
                ucic_code,
                pan,
                poi_name,
                poa_name,
                account_number,
                name_score,
                dob_score,
                pan_score,
                address_score,
                matched_name,
                matched_dob,
                matched_pan,
                matched_address,
                match_status,
                overall_is_pep,
                overall_match_status,
                user_source_group_id,
                aml_tracking_id,
                source,
                entity_source,
                kyc_tracking_id,
                account_status
            FROM
                RankedEntries
            WHERE
                rn = 1;
        """
        params = {
            "kyc_status": KYCConstant.SUCCESS,
            "aml_status": AMLConstants.IN_REVIEW,
            "service_type": KycServices.NAME_MATCH,
        }

        return InvestorMapper().sql_execute_fetch_all(sql, params, to_dict=True)

    @staticmethod
    def get_aml_tracker_data(aml_tracking_id, user_source_group_id, user_id):
        sql = """
                select lc.encoded_email as email, lc.first_name, lc.dob,
                lc.encoded_mobile as mobile_number, lc.encoded_pan as pan, 
                lc.id as user_pk, lu.id, lu.aml_status, lu.aml_category, 
                ls.source_name, lc2.user_id as cp_user_pk, lc.type, lc.is_family_member
                from lendenapp_userkyctracker lu 
                join lendenapp_customuser lc on lu.user_id = lc.id
                join lendenapp_user_source_group lusg on lusg.id = lu.user_source_group_id
                left join lendenapp_channelpartner lc2 on lc2.id = lusg.channel_partner_id
                join lendenapp_source ls on ls.id = lusg.source_id
                where lu.aml_tracking_id = %(aml_tracking_id)s 
                and lu.user_source_group_id = %(user_source_group_id)s 
                and lu.status = %(status)s and lu.is_latest_kyc 
                and lc.user_id = %(user_id)s
                """

        params = {
            "aml_tracking_id": aml_tracking_id,
            "user_source_group_id": user_source_group_id,
            "status": KYCConstant.SUCCESS,
            "user_id": user_id,
        }

        return InvestorMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    def get_loans_data(self, tracker_data):
        sql = """
                SELECT loslm.loan_id, loslm.otl_tracker_id, loslm.loan_roi,
                loslm.ldc_score, loslm.loan_amount, loslm.loan_tenure, 
                loslm.borrower_name
                FROM lendenapp_otl_scheme_loan_mapping loslm
                WHERE loslm.otl_tracker_id = %(tracker_id)s 
                AND loslm.created_date > %(yesterday)s
                AND loslm.is_available = TRUE;
            """

        params = {
            "tracker_id": tracker_data["id"],
            "yesterday": get_current_dtm() - timedelta(days=1),
        }

        return self.sql_execute_fetch_all(sql, params, to_dict=True)

    def get_max_id_from_table(self, table_name):
        sql = f"""
                SELECT max(id) from {table_name}
            """

        return self.sql_execute_fetch_one(sql, params={}, to_dict=True)

    def get_mandate_and_bank_details(self, selected_columns=None):
        if not selected_columns:
            selected_columns = ["*"]
        selected_col_str = ",".join(selected_columns)
        sql = f"""
                SELECT {selected_col_str} 
                FROM lendenapp_bankaccount lb 
                JOIN lendenapp_mandate lm ON lb.mandate_id = lm.id
                JOIN lendenapp_mandatetracker lm2 ON lm2.id = lm.mandate_tracker_id
                WHERE lb.user_source_group_id = %(user_source_id)s 
                AND lb.is_active;
            """

        params = {
            "user_source_id": self.user_source_id,
        }

        return self.sql_execute_fetch_one(sql, params, to_dict=True)

    def expire_pending_payment_link(
        self, payment_gateway=PMIConstants.NACH, expiration_days=None
    ):
        sql = """
                UPDATE lendenapp_paymentlink 
                SET status = 'EXPIRED'
                WHERE status = 'PENDING' 
                AND user_source_group_id = %(user_source_id)s 
                AND payment_gateway = %(payment_gateway)s
            """

        params = {
            "user_source_id": self.user_source_id,
            "payment_gateway": payment_gateway,
        }

        if expiration_days:
            sql += f" AND created_date < NOW() - INTERVAL '{expiration_days} DAY'"

        return self.execute_sql(sql, params, return_rows_count=True)

    @staticmethod
    def get_personal_detail(encoded_email=None, encoded_mobile=None):
        sql = """                
                SELECT id, encoded_mobile, encoded_email
                    FROM lendenapp_customuser
                    WHERE
                """

        params = {}

        if encoded_email and encoded_mobile:
            sql += """ encoded_email = %(encoded_email)s or encoded_mobile = %(encoded_mobile)s"""
            params["encoded_email"] = encoded_email
            params["encoded_mobile"] = encoded_mobile

        elif encoded_mobile:
            sql += """ encoded_mobile = %(encoded_mobile)s"""
            params["encoded_mobile"] = encoded_mobile

        elif encoded_email:
            sql += """ encoded_email = %(encoded_email)s"""
            params["encoded_email"] = encoded_email

        else:
            return []

        return InvestorMapper().sql_execute_fetch_all(sql, params, to_dict=True)

    @staticmethod
    def update_is_valid_account(user_source_group_id):
        # Note: Accounts being updated to "valid" must also exist in the account table.
        condition = (
            "WHERE lba.user_source_group_id=ANY(%(user_source_group_id)s)"
            if isinstance(user_source_group_id, (list, tuple))
            else "WHERE lba.user_source_group_id = %(user_source_group_id)s"
        )

        sql = f"""
            UPDATE lendenapp_bankaccount lba
            SET is_valid_account = %(valid_account)s, updated_date = NOW()
            {condition}
            AND lba.is_active = %(valid_account)s
            AND lba.purpose=%(purpose)s;
        """

        params = {
            "user_source_group_id": (
                tuple(user_source_group_id)
                if isinstance(user_source_group_id, (list, tuple))
                else user_source_group_id
            ),
            "valid_account": True,
            "purpose": AddBankAccountConstant.PRIMARY_PURPOSE,
        }

        params = DataLayerUtils().prepare_sql_params(params)
        InvestorMapper().execute_sql(sql, params)

    @staticmethod
    def fetch_customuser_pk_from_user_source_id_list(user_source_group_id_list):
        sql = """
                SELECT user_id FROM lendenapp_user_source_group 
                WHERE id =ANY(%(user_source_group_id_list)s);
            """

        params = {
            "user_source_group_id_list": user_source_group_id_list,
        }

        params = DataLayerUtils().prepare_sql_params(params)
        return InvestorMapper().sql_execute_fetch_all(sql, params, to_dict=True)

    @staticmethod
    def update_is_valid_pan(user_pk_list):
        where_condition = (
            "WHERE lc.id = ANY(%(user_pk_list)s)"
            if isinstance(user_pk_list, (list, tuple))
            else "WHERE lc.id = %(user_pk_list)s"
        )

        sql = f"""
            UPDATE lendenapp_customuser lc
            SET is_valid_pan = %(valid_pan)s, modified_date = NOW()
            {where_condition};
        """

        params = {
            "user_pk_list": (
                tuple(user_pk_list)
                if isinstance(user_pk_list, (list, tuple))
                else user_pk_list
            ),
            "valid_pan": True,
        }
        params = DataLayerUtils().prepare_sql_params(params)
        InvestorMapper().execute_sql(sql, params)

    @staticmethod
    def get_analytical_data(key):
        sql = f"""
                SELECT value
                FROM lendenapp_analytical_data lad
                WHERE key = %(key)s order by id desc;
            """

        params = {"key": key}

        return InvestorMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def insert_failed_scheme_in_tracker(params):
        sql = """
        INSERT INTO lendenapp_otl_scheme_tracker 
            (scheme_id, loan_count, transaction_id, status, investment_type, batch_number, user_source_group_id) 
        VALUES 
            (%s, %s, 
             (SELECT id FROM lendenapp_transaction WHERE transaction_id = %s), 
             %s, %s, %s, %s)
        RETURNING id;
        """
        return InvestorMapper().sql_execute_fetch_one(
            sql, list(params.values()), index_result=True
        )

    @staticmethod
    def mark_loans_unavailable(failed_loan_ids, tracker_id):
        sql = """
        UPDATE lendenapp_otl_scheme_loan_mapping
        SET is_available = False
        WHERE loan_id=ANY(%(failed_loan_ids)s)
        and otl_tracker_id = %(tracker_id)s
        and created_date > %(yesterday)s
        """
        params = {
            "failed_loan_ids": list(failed_loan_ids),
            "tracker_id": tracker_id,
            "yesterday": get_current_dtm() - timedelta(days=1),
        }

        params = DataLayerUtils().prepare_sql_params(params)
        return InvestorMapper().execute_sql(sql, params=params, return_rows_count=True)

    @staticmethod
    def fetch_withdrawal_transactions(transaction_id_list):
        sql = f"""
                SELECT transaction_id FROM lendenapp_transaction
                WHERE transaction_id =ANY(%(transaction_id_list)s) and
                status = %(status)s AND type= ANY(%(type)s)
            """

        params = {
            "transaction_id_list": transaction_id_list,
            "status": TransactionStatus.SCHEDULED,
            "type": [TransactionType.WITHDRAWAL_TRANSACTION_TYPE],
        }

        params = DataLayerUtils().prepare_sql_params(params)
        return InvestorMapper().sql_execute_fetch_all(sql, params, to_dict=True)

    @staticmethod
    def put_withdrawal_transactions_on_hold(transaction_id_list, days_to_hold):
        sql = f"""
                UPDATE lendenapp_transaction
                SET date = NOW() + interval '{days_to_hold} days',
                updated_date = NOW()
                WHERE transaction_id=ANY(%(transaction_id_list)s)
        """

        params = {"transaction_id_list": transaction_id_list}

        params = DataLayerUtils().prepare_sql_params(params)
        InvestorMapper().execute_sql(sql, params)

    @staticmethod
    def get_add_money_stuck_transactions(
        transaction_status,
        limit=None,
        offset=None,
        transaction_id=None,
        from_date=None,
        to_date=None,
    ):
        sql = """
            SELECT lt.transaction_id, lt2.transaction_id AS reversal_txn_id,
            la.number AS lenz_number, 
            lc.user_id as investor_id, lst.amount, lt.status as transaction_status,
            lba.number AS system_linked_bank_account, 
            lst.add_money_account AS source_account_number, lc.pan AS pan_number, 
            lst.add_money_account_holder AS source_account_name, 
            lst.add_money_ifsc_code AS source_ifsc_code, 
            lba.name AS penny_drop_name, NULL as pan_image,
            lst.add_money_bank_name AS source_bank_name,
            la.user_source_group_id, 
            TO_CHAR(lt.created_date AT TIME ZONE 'Asia/Kolkata', 'DD Mon YYYY HH24:MI:SS') as created_date 
            FROM lendenapp_snorkel_stuck_transaction lst JOIN 
            lendenapp_transaction lt ON lst.remarks=lt.transaction_id
            LEFT JOIN lendenapp_transaction lt2 ON lt2.reversal_txn_id = lt.id
            JOIN public.lendenapp_account la ON 
            la.user_source_group_id=lt.user_source_group_id
            JOIN lendenapp_customuser lc ON la.user_id = lc.id
            JOIN lendenapp_bankaccount lba ON 
            la.user_source_group_id = lba.user_source_group_id
            WHERE la.bank_account_id = lba.id AND lt.type=%(transaction_type)s 
            AND lt.status= ANY(%(transaction_status)s) AND lba.is_active=True 
            AND lst.type=%(transaction_type)s 
            AND lst.status = ANY(%(transaction_status)s)
        """

        params = {
            "transaction_type": TransactionType.ADD_MONEY,
            "transaction_status": transaction_status,
        }

        if from_date and to_date:
            sql += (
                """ AND Date(lt.created_date) BETWEEN %(from_date)s AND %(to_date)s"""
            )
            params["from_date"] = from_date
            params["to_date"] = to_date

        if transaction_id:
            sql += """ AND lst.remarks = %(transaction_id)s"""
            params["transaction_id"] = transaction_id
        else:
            # If txn_id = ABC and limit = 5 and offset = 5 and txn_id is in
            # offset 0-4 then it doesn't provide txn_id hence limit offset
            # in else statement
            sql += """ LIMIT %(limit)s OFFSET %(offset)s"""
            params["limit"] = limit
            params["offset"] = offset

        params = DataLayerUtils().prepare_sql_params(params)

        return InvestorMapper().sql_execute_fetch_all(sql, params, to_dict=True)

    @staticmethod
    def fetch_add_money_stuck_transaction_details(transaction_id_list):
        sql = """
            SELECT la.user_source_group_id, lt.id AS transaction_pk, la.user_id, 
            lst.amount, lc.first_name AS lender_name, ls.source_name,
            lc2.first_name AS cp_name, lt.transaction_id, lc.encoded_email,
            lst.add_money_ifsc_code as source_ifsc, la.balance,
            lst.add_money_account as source_account, lc.user_id as investor_id,
            lst.add_money_account_holder as source_account_holder_name,
            lc.is_family_member
            FROM lendenapp_snorkel_stuck_transaction lst JOIN 
            lendenapp_transaction lt ON lst.remarks=lt.transaction_id
            JOIN lendenapp_account la ON 
            lt.user_source_group_id = la.user_source_group_id
            JOIN lendenapp_bankaccount lba ON 
            la.user_source_group_id = lba.user_source_group_id
            JOIN lendenapp_user_source_group lusg ON lusg.id=lt.user_source_group_id
            JOIN lendenapp_source ls ON ls.id=lusg.source_id
            JOIN lendenapp_customuser lc ON lc.id=lusg.user_id
            LEFT JOIN lendenapp_channelpartner lcp ON lusg.channel_partner_id=lcp.id
            LEFT JOIN lendenapp_customuser lc2 ON lc2.id=lcp.user_id
            WHERE la.bank_account_id = lba.id AND lt.type=%(transaction_type)s 
            AND lt.status=%(transaction_status)s
            AND lst.status=%(transaction_status)s AND 
            lba.is_active=True AND lt.transaction_id=ANY(%(transaction_id_list)s)
        """

        params = {
            "transaction_type": TransactionType.ADD_MONEY,
            "transaction_status": TransactionStatus.HOLD,
            "transaction_id_list": transaction_id_list,
        }

        params = DataLayerUtils().prepare_sql_params(params)
        return InvestorMapper().sql_execute_fetch_all(sql, params, to_dict=True)

    @staticmethod
    def update_transaction_status(
        table_name, status, transaction_id_list, column_name, rejection_reason=None
    ):
        sql = f"UPDATE {table_name} SET status = %(status)s, updated_date = NOW()"
        params = {"status": status}

        if rejection_reason is not None:
            sql += ", rejection_reason = %(rejection_reason)s"
            params["rejection_reason"] = rejection_reason

        sql += f" WHERE {column_name} = ANY(%(transaction_ids)s)"
        params["transaction_ids"] = transaction_id_list

        params = DataLayerUtils().prepare_sql_params(params)
        return InvestorMapper().execute_sql(sql, params, return_rows_count=True)

    def fetch_lending_amount_from_cohort(self):
        sql = """
            select 
                lcc.config_values::json
            from lendenapp_user_cohort_mapping lcm
            join lendenapp_cohort_purpose lcp on lcp.id = lcm.purpose_id
            join lendenapp_cohort_config lcc on lcc.id = lcm.config_id
             where lcm.user_source_group_id = %(user_source_group_id)s 
             and lcp.name = 'ml_min_lending_amount'
             and lcc.is_enabled and lcp.is_enabled;
        """

        params = {"user_source_group_id": self.user_source_id}

        return self.sql_execute_fetch_one(sql, params, index_result=True)

    @staticmethod
    def get_failed_name_match_data(data):
        sql = """
        select 
            distinct lc.user_id, lu.tracking_id, lc.first_name, 
            lu2.poi_name, lu2.poa_name, lu.user_source_group_id,
            (lu.created_date at TIME zone 'Asia/Kolkata')::date as created_date,
            ls.source_name partner_code, lcp.partner_id,
            '' as pan_image, '' as aadhar_image_front, '' as aadhar_image_back
        FROM lendenapp_userkyctracker lu
        JOIN lendenapp_userkyc lu2 ON lu.user_source_group_id = lu2.user_source_group_id 
            and lu.tracking_id = lu2.tracking_id 
        JOIN lendenapp_customuser lc ON lc.id = lu.user_id 
        JOIN lendenapp_user_source_group lusg ON lusg.id = lu.user_source_group_id
        JOIN lendenapp_source ls ON ls.id = lusg.source_id
        LEFT JOIN lendenapp_channelpartner lcp ON lcp.id = lusg.channel_partner_id
        WHERE 
            lu.is_latest_kyc and lu2.service_type = %(service_type)s 
            and lu.name_match_status = %(name_match_status)s
            and lu.status <> %(fail_status)s
        """
        if data.get("search"):
            sql += " AND lc.user_id = %(search)s "
        if data.get("limit") and data.get("offset") is not None:
            sql += " ORDER BY created_date desc LIMIT %(limit)s OFFSET %(offset)s "
        params = {
            "service_type": KycServices.NAME_MATCH,
            "name_match_status": NameMatchStatus.IN_REVIEW,
            "limit": data.get("limit"),
            "offset": data.get("offset"),
            "search": data.get("search"),
            "fail_status": KYCConstant.FAILED,
        }
        return InvestorMapper().sql_execute_fetch_all(sql, params, to_dict=True)

    @staticmethod
    def get_cohort_data(purpose_name, cohort_category):
        sql = """
            select lcp.name as purpose_name,lcc.id as cohort_id,
            cohort_category,weightage,lcc.is_enabled,config_values::json,
            lcc.created_at
            from lendenapp_cohort_config lcc 
            join lendenapp_cohort_purpose lcp 
            on lcc.purpose_id = lcp.id 
            where lcc.cohort_category = %(cohort_category)s
            and lcp.name = %(purpose_name)s
            and lcp.add_cohort = true
            and lcc.modify_cohort = true ; 
        """
        params = {
            "cohort_category": cohort_category,
            "purpose_name": purpose_name,
        }
        return InvestorMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def insert_cohort_data(data):
        sql = """
            INSERT INTO lendenapp_cohort_config
            (purpose_id, cohort_category, weightage, config_values, is_enabled)
            SELECT lcp.id, %(cohort_category)s, %(weightage)s, %(config_values)s, 
            %(is_enabled)s
            FROM lendenapp_cohort_purpose lcp
            WHERE lcp.name = %(purpose_name)s
            AND lcp.add_cohort = TRUE 
            RETURNING id;
        """
        params = {
            "purpose_name": data.get("purpose_name"),
            "cohort_category": data.get("cohort_category"),
            "weightage": data.get("weightage"),
            "config_values": (
                json.dumps(data["config_values"]) if data.get("config_values") else None
            ),
            "is_enabled": data.get("is_enabled"),
        }
        return InvestorMapper().sql_execute_fetch_one(sql, params, index_result=True)

    @staticmethod
    def update_cohort_data(data):
        sql = """
            UPDATE lendenapp_cohort_config lcc
            SET weightage = %(weightage)s,
                config_values = %(config_values)s,
                is_enabled = %(is_enabled)s
            FROM lendenapp_cohort_purpose lcp
            WHERE lcc.id = %(cohort_id)s
            AND lcp.add_cohort = TRUE
            RETURNING lcc.id;
        """
        params = {
            "weightage": data.get("weightage"),
            "config_values": (
                json.dumps(data["config_values"]) if data.get("config_values") else None
            ),
            "is_enabled": data.get("is_enabled"),
            "cohort_id": data.get("cohort_id"),
        }
        return InvestorMapper().sql_execute_fetch_one(sql, params, index_result=True)

    @staticmethod
    def get_purpose_and_config():
        sql = """
            select lcc.id as cohort_id,lcp.name as purpose_name,
            lcp.is_enabled as purpose_is_enabled,
            cohort_category , weightage , 
            lcc.is_enabled as cohort_is_enabled,
            config_values::json
            from lendenapp_cohort_purpose lcp 
            left join lendenapp_cohort_config lcc 
            on lcc.purpose_id =lcp.id 
            where lcp.add_cohort = true 
            and lcc.modify_cohort = true 
            order by lcp.id desc;
        """
        return InvestorMapper().sql_execute_fetch_all(sql, params={}, to_dict=True)

    @staticmethod
    def get_config_data(purpose_name):
        sql = """
            select lcp.name as purpose_name, lcc.id as config_id, 
            cohort_category,
            weightage,lcc.is_enabled,config_values::json
            from lendenapp_cohort_purpose lcp 
            join lendenapp_cohort_config lcc 
            on lcc.purpose_id = lcp.id 
            where lcp.name = %(purpose_name)s
            and lcp.add_cohort = true 
            and lcc.modify_cohort = true
            order by lcp.id desc;
        """

        params = {"purpose_name": purpose_name}
        return InvestorMapper().sql_execute_fetch_all(sql, params, to_dict=True)

    @staticmethod
    def check_cohort_exists(purpose_name, cohort_category):
        sql = """
            SELECT EXISTS(
                SELECT 1
                FROM lendenapp_cohort_purpose lcp
                JOIN lendenapp_cohort_config lcc
                ON lcc.purpose_id = lcp.id
                WHERE lcp.name = %(purpose_name)s
                AND lcp.add_cohort = TRUE
                AND lcc.modify_cohort = TRUE
                AND lcc.cohort_category = %(cohort_category)s
            );
        """
        params = {"purpose_name": purpose_name, "cohort_category": cohort_category}
        return InvestorMapper().sql_execute_fetch_one(sql, params, index_result=True)

    def fetch_referee_data(self, limit, offset):
        sql = """
            SELECT 
                lc.first_name, lc.encoded_mobile as mobile_number, 
                false AS is_signed_up, 
                false AS is_listed,
                false as is_reward_credited,
                false as is_lent_money,
                case WHEN lr.status = %(referral_status)s THEN %(send_reminder)s 
                    ELSE lr.status::TEXT
                END as status,
		    	case WHEN lr.status = %(referral_status)s THEN %(reward_not_earned)s
                    WHEN lr.status = %(ineligible_status)s THEN %(ineligible_text)s
		    	     ELSE %(reward_earned)s
		        END AS info_text,
		        (CASE WHEN lr.reminder_date IS NOT NULL AND lr.reminder_date = CURRENT_DATE THEN true 
                     ELSE false 
                END) AS reminder_sent,
		        lusg.id as user_source_id
            FROM lendenapp_reward lr 
            join lendenapp_campaign lc2 on lc2.id = lr.campaign_id
            JOIN lendenapp_user_source_group lusg ON lusg.id = lr.related_user_source_group_id
            JOIN lendenapp_customuser lc ON lc.id = lusg.user_id
            JOIN lendenapp_account la ON la.user_source_group_id = lusg.id
            where lr.user_source_group_id = %(user_source_group_id)s
            and lr.user_source_group_id != lr.related_user_source_group_id
            and lc2.type = %(campaign_type)s order by lr.id desc
            LIMIT %(limit)s OFFSET %(offset)s;
        """

        params = {
            "user_source_group_id": self.user_source_id,
            "referral_status": RewardStatus.PENDING,
            "reward_earned": ReferralDetails.REWARD_EARNED_TEXT,
            "reward_not_earned": ReferralDetails.REWARD_NOT_EARNED_TEXT,
            "send_reminder": ReferralDetails.SEND_REMINDER,
            "campaign_type": CampaignType.REFERRAL,
            "limit": limit,
            "offset": offset,
            "ineligible_status": RewardStatus.INELIGIBLE,
            "ineligible_text": ReferralDetails.INELIGIBLE_TEXT,
        }

        return self.sql_execute_fetch_all(sql, params, to_dict=True)

    def fetch_referee_count(self):
        sql = """
            SELECT 
            COUNT(*) AS total_count,
            COUNT(CASE WHEN lr.status = 'COMPLETED' THEN 1 END) AS total_converted,
            COALESCE((
                SELECT 
                    lcw.available_amount + lcw.redeemed_amount - lcw.expired_amount
                FROM lendenapp_campaign_wallet lcw
                WHERE lcw.user_source_group_id = %(user_source_group_id)s
            ), 0) AS your_earning
            FROM lendenapp_reward lr 
            JOIN lendenapp_campaign lc2 ON lc2.id = lr.campaign_id
            WHERE lr.user_source_group_id = %(user_source_group_id)s
            AND lr.user_source_group_id != lr.related_user_source_group_id
            AND lc2.type = %(campaign_type)s;
        """

        params = {
            "user_source_group_id": self.user_source_id,
            "campaign_type": CampaignType.REFERRAL,
        }

        return self.sql_execute_fetch_one(sql, params, to_dict=True)

    def save_borrower_preferences(self, data):
        sql = """
            INSERT INTO lendenapp_filters_and_sort_logs (filters, sort_by, "limit", 
            "offset", user_source_group_id)
            VALUES (%s, %s, %s, %s, %s)
        """
        params = (
            data.get("filters") or "",
            data.get("sort_by") or "",
            data.get("limit") or 0,
            data.get("offset") or 0,
            self.user_source_id,
        )
        return self.execute_sql(sql, params, return_rows_count=True)

    @staticmethod
    def get_max_id_from_partitioned_table(table_name, partition_key):
        yesterday = get_current_dtm() - timedelta(days=1)
        sql = f"""
            SELECT MAX(id) FROM {table_name}
            WHERE {partition_key} > '{yesterday}'
        """
        return InvestorMapper().sql_execute_fetch_one(sql, [], to_dict=True)["max"] or 0

    @staticmethod
    def get_fmi_withdrawal_transaction_data(
        transaction_id, for_update=False, status=TransactionStatus.SCHEDULED
    ):
        sql = """
            SELECT lt.id as transaction_pk, lt.type as transaction_type, lt.transaction_id,lt.status,
            lt.user_source_group_id, lb.ifsc_code,lb.id as bank_pk,
            lb.number as account_number, lb.type, lc.first_name as name,
            lc.encoded_email as email, lc.is_family_member,
            lc.id as user_id, lt.amount, ls.source_name,
            COALESCE(fw.withdrawal_retry_count, 0) AS withdrawal_retry_count,
            COALESCE(fw.has_ip_status, false) AS has_ip_status
            FROM lendenapp_transaction lt 
            join lendenapp_user_source_group lusg on lusg.id = lt.user_source_group_id
            join lendenapp_source ls on ls.id = lusg.source_id
            JOIN lendenapp_customuser lc ON lusg.user_id = lc.id
            JOIN lendenapp_account la ON lusg.id = la.user_source_group_id
            JOIN lendenapp_bankaccount lb on la.bank_account_id = lb.id
            LEFT JOIN (
                SELECT 
                    transaction_id,
                    COUNT(CASE WHEN message_code IS NOT NULL THEN 1 END) AS withdrawal_retry_count,
                    BOOL_OR(status = ANY(%(fmi_status)s)) AS fmi_status,
                    BOOL_OR(status = %(fmi_in_progress)s) AS has_ip_status
                FROM lendenapp_fmi_withdrawals 
                WHERE transaction_id = ANY(%(withdrawal_transactions)s)
                GROUP BY transaction_id
            ) fw ON fw.transaction_id = lt.transaction_id
            WHERE lt.transaction_id = ANY(%(withdrawal_transactions)s)
            and la.status = %(account_status)s
            AND (
                lt.status = %(status)s 
                OR (lt.status = %(in_progress)s AND fw.fmi_status = true)
            )
            AND lt.type = ANY(%(transaction_type)s)
            AND la.balance >= 0.0 
            AND lc.id <> ALL(%(block_user)s)
            AND lb.is_active AND lt.date <= NOW()
            AND lt.amount >= %(amount)s
            AND lb.purpose= %(purpose)s
        """

        if for_update:
            sql += "FOR UPDATE OF lt NOWAIT"

        params = {
            "withdrawal_transactions": transaction_id,
            "block_user": TransactionBlockForUser.withdrawal_block,
            "status": status,
            "transaction_type": TransactionType.WITHDRAWAL_TRANSACTION_TYPE,
            "amount": FMISystem.MIN_AMOUNT,
            "purpose": AddBankAccountConstant.PRIMARY_PURPOSE,
            "account_status": AccountStatus.LISTED,
            "fmi_status": (
                FMITransactionStatus.IN_PROGRESS,
                FMITransactionStatus.FAILED,
            ),
            "in_progress": TransactionStatus.IN_PROGRESS,
            "fmi_in_progress": FMITransactionStatus.IN_PROGRESS,
        }

        params = DataLayerUtils().prepare_sql_params(params)
        return InvestorMapper().sql_execute_fetch_all(sql, params, to_dict=True)

    @staticmethod
    def update_fmi_transaction_status(
        transaction,
        update_status,
        success_data=None,
        rejection_data=None,
        status_date=None,
        bank_pk=None,
    ):
        sql = """
            UPDATE lendenapp_transaction lt
            SET status = %(update_status)s,
            updated_date = NOW(),status_date = %(todays_date)s
        """

        params = {
            "transaction": transaction,
            "update_status": update_status,
            "todays_date": get_todays_date() if not status_date else status_date,
        }

        set_clauses = []

        if rejection_data:
            set_clauses.append("rejection_reason = %(rejection_reason)s")
            set_clauses.append("utr_no = %(utr)s")
            params["rejection_reason"] = rejection_data["rejection_reason"]
            params["utr"] = rejection_data.get("utr", "")

        if success_data:
            set_clauses.append("utr_no = %(utr)s")
            params["utr"] = success_data.get("utr", "")

        if bank_pk:
            set_clauses.append("bank_account_id = %(bank_pk)s")
            params["bank_pk"] = bank_pk

        if set_clauses:
            sql += ", " + ", ".join(set_clauses)

        sql += " WHERE lt.transaction_id = %(transaction)s"

        InvestorMapper().execute_sql(sql, params)

    @staticmethod
    def get_fmi_callback_data(transaction_id, fmi_transaction_id):
        sql = """
            SELECT lt.id as transaction_pk,lt.type as transaction_type,lt.transaction_id ,
            lt.user_source_group_id,lc.first_name as name,lc.encoded_email as email,
            lt.created_date, lt.description, cp.user_id cp_user_pk,
            lt.amount,lusg.user_id,ls.source_name, lfw.id as fmi_pk, lfw.status as fmi_status,
            lc.user_id as investor_id, lb.number as account_number, lc.is_family_member
            FROM lendenapp_transaction lt
            join lendenapp_user_source_group lusg on lusg.id = lt.user_source_group_id
            join lendenapp_fmi_withdrawals lfw on lfw.transaction_id = lt.transaction_id
            join lendenapp_customuser lc on lc.id = lusg.user_id
            join lendenapp_source ls on lusg.source_id = ls.id
            join lendenapp_bankaccount lb on lt.bank_account_id = lb.id
            left join lendenapp_channelpartner cp on cp.id = lusg.channel_partner_id
            WHERE lt.transaction_id = %(withdrawal_transactions)s
            AND lfw.fmi_txn_id =%(fmi_transaction_id)s
            AND lusg.user_id <> ALL(%(block_user)s)
            AND lt.date <= NOW()
            AND lt.status <> ALL(%(status)s)
            AND lfw.status IS NOT NULL AND lfw.status <> %(fmi_status)s
            FOR UPDATE OF lt, lfw NOWAIT
        """

        params = {
            "withdrawal_transactions": transaction_id,
            "block_user": tuple(TransactionBlockForUser.user_pk_list),
            "status": [TransactionStatus.SUCCESS, TransactionStatus.FAILED],
            "fmi_status": FMITransactionStatus.FAILED,
            "fmi_transaction_id": fmi_transaction_id,
        }

        params = DataLayerUtils().prepare_sql_params(params)
        return InvestorMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def get_account_validation_status(user_source_group_ids):
        sql = """
                 SELECT 
                    lc.id as user_id,
                    lb.user_source_group_id
                FROM 
                    lendenapp_customuser lc
                JOIN lendenapp_bankaccount lb ON lc.id = lb.user_id
                join lendenapp_account  la on la.bank_account_id = lb.id
                WHERE  lb.is_active and lb.purpose=%(purpose)s 
                 and (lb.is_valid_account = false OR lc.is_valid_pan = false)
                AND lb.user_source_group_id =ANY(%(user_source_group_id)s)       
            """

        params = {
            "user_source_group_id": user_source_group_ids,
            "purpose": AddBankAccountConstant.PRIMARY_PURPOSE,
        }

        result = InvestorMapper().sql_execute_fetch_all(sql, params, to_dict=True)
        if not result:
            return [], []

        # Extract both lists in a single loop
        user_source_group_ids = []
        user_ids = []

        for row in result:
            user_source_group_ids.append(row["user_source_group_id"])
            user_ids.append(row["user_id"])

        return user_source_group_ids, user_ids

    @staticmethod
    def fetch_user_account_source_data(user_source_id):
        sql = """
            select la.status, ls.source_name ,
            lc.first_name as cp_name, ls.source_full_name
            from lendenapp_user_source_group lusg
            join lendenapp_account la on la.user_source_group_id = lusg.id
            left join lendenapp_channelpartner lcp 
                on lcp.id = lusg.channel_partner_id
            left join lendenapp_customuser lc on lc.id = lcp.user_id
            join lendenapp_source ls on ls.id = lusg.source_id
            where lusg.id = %(user_source_id)s
        """

        params = {"user_source_id": user_source_id}

        return InvestorMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def get_investor_details_v2(
        columns_and_values,
        selected_columns=None,
        all_result=False,
        logical_operator="AND",
    ):
        if not selected_columns:
            selected_columns = ["*"]
        selected_col_str = ",".join(selected_columns)

        conditions = []
        params = {}
        param_count = 1

        for column, value in columns_and_values.items():
            param_name = f"param_{param_count}"
            if isinstance(value, (list, tuple)):
                conditions.append(f"{column} = ANY(%({param_name})s)")
                # Ensure single values are converted to lists
                params[param_name] = list(value) if isinstance(value, tuple) else value
            else:
                conditions.append(f"{column} = %({param_name})s")
                params[param_name] = value
            param_count += 1

        conditions_str = f" {logical_operator} ".join(conditions)

        sql = f"""
            SELECT
                {selected_col_str}
            FROM lendenapp_user_source_group lusg
            JOIN lendenapp_source ls ON ls.id = lusg.source_id
            JOIN lendenapp_customuser lc ON lc.id = lusg.user_id
            JOIN lendenapp_account la ON la.user_source_group_id = lusg.id
            LEFT JOIN lendenapp_channelpartner cp ON cp.id = lusg.channel_partner_id
            LEFT JOIN lendenapp_customuser lc2 ON lc2.id = cp.user_id
            WHERE {conditions_str}
        """

        if all_result:
            return InvestorMapper().sql_execute_fetch_all(sql, params, to_dict=True)

        return InvestorMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def bulk_update_data(table_name, data_fields, condition_fields, data_values):
        """
        Bulk updates data in the database using the provided data_map.

        Args:
            table_name (str): Name of the table.
            data_fields (list): List of column names to be updated.
            condition (list): List of condition column names for WHERE clause.
            data_values (list of tuples): Each tuple contains data_fields values + condition_fields values

        Example:
            data_fields = ['status', 'number', 'listed_date', 'updated_date', 'user_source_group_id']
            condition_fields = ['id']
            data_values = [
                ('LISTED', 'LENZ123', date_obj, datetime_obj, 236575),
                ...
            ]
        Returns:
            None
        """
        set_clause = ", ".join([f"{field} = %s" for field in data_fields])
        filter_clause = " AND ".join([f"{field} = %s" for field in condition_fields])

        update_query = f""" 
            UPDATE {table_name} 
            SET {set_clause}
            WHERE {filter_clause};
        """
        return InvestorMapper().sql_execute_bulk_update(update_query, data_values)

    @staticmethod
    def upsert_application_config(params):
        set_data = ", ".join(
            [
                f'"{key}" = EXCLUDED."{key}"'
                for key in params.keys()
                if key not in ["config_key", "source_id"]
            ]
        )

        sql = f"""
            INSERT INTO lendenapp_application_config (config_key, config_value, source_id, description)
            VALUES (%(config_key)s, %(config_value)s, %(source_id)s, %(description)s)
            ON CONFLICT (config_key, source_id)
            DO UPDATE SET {set_data}
            RETURNING id;
        """

        return InvestorMapper().sql_execute_fetch_one(sql, params, index_result=True)

    @staticmethod
    def get_cohort_mapping(purpose_name, limit, offset, user_id=None):
        sql = """
            select lucm.id, lcp.name as purpose_name, lc.user_id, 
            lc.first_name, 
            lc.encoded_email, lc.encoded_mobile, lucm.user_source_group_id , 
            lcc.cohort_category
            from lendenapp_cohort_purpose lcp 
            join lendenapp_cohort_config lcc 
            on lcc.purpose_id = lcp.id 
            join lendenapp_user_cohort_mapping lucm 
            on lucm.config_id = lcc.id
            join lendenapp_user_source_group lusg 
            on lucm.user_source_group_id = lusg.id 
            join lendenapp_customuser lc 
            on lusg.user_id = lc.id 
            where lcp.name = %(purpose_name)s
            and lcp.is_enabled = true 
            and lcp.add_cohort = true 
            and lcc.is_enabled = true 
            and lcc.modify_cohort = true
        """

        params = {"purpose_name": purpose_name, "limit": limit, "offset": offset}

        if user_id:
            sql += """
            and lc.user_id = %(user_id)s
            """
            params["user_id"] = user_id

        sql += """
            order by lucm.id desc
            limit %(limit)s offset %(offset)s;
        """

        return InvestorMapper().sql_execute_fetch_all(sql, params, to_dict=True)

    @staticmethod
    def get_purpose_and_cohort(purpose_name, updated_cohort_category):
        sql = """
            select lcp.id as purpose_id, lcc.id as cohort_id 
            from lendenapp_cohort_config lcc 
            join lendenapp_cohort_purpose lcp 
            on lcc.purpose_id = lcp.id 
            where lcp.name = %(purpose_name)s 
            and lcc.cohort_category = %(updated_cohort_category)s
            and lcp.is_enabled = true 
            and lcp.add_cohort = true 
            and lcc.is_enabled = true 
            and lcc.modify_cohort = true;
        """

        params = {
            "purpose_name": purpose_name,
            "updated_cohort_category": updated_cohort_category,
        }
        return InvestorMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def update_user_cohort_mapping(purpose_id, mapping_ids, updated_cohort_category):
        sql = """
            UPDATE lendenapp_user_cohort_mapping
            SET config_id = %(updated_cohort_category)s,
            updated_at = CURRENT_TIMESTAMP
            WHERE id=ANY(%(mapping_ids)s)
            and purpose_id = %(purpose_id)s
            RETURNING user_source_group_id;
        """

        params = {
            "purpose_id": purpose_id,
            "mapping_ids": mapping_ids,
            "updated_cohort_category": updated_cohort_category,
        }

        params = DataLayerUtils().prepare_sql_params(params)
        return InvestorMapper().sql_execute_fetch_all(sql, params, to_dict=True)

    @staticmethod
    def get_current_user_cohort(purpose_name, mapping_ids):
        sql = """
            select lucm.user_source_group_id, lcc.cohort_category
            from lendenapp_user_cohort_mapping lucm 
            join lendenapp_cohort_config lcc 
            on lucm.config_id = lcc.id 
            join lendenapp_cohort_purpose lcp 
            ON lcp.id = lcc.purpose_id 
            where lucm.id=ANY(%(mapping_ids)s)
            and lcc.is_enabled = true
            and lcp.is_enabled = true
            and lcp.name = %(purpose_name)s;
        """

        params = {
            "purpose_name": purpose_name,
            "mapping_ids": mapping_ids,
        }

        params = DataLayerUtils().prepare_sql_params(params)
        return InvestorMapper().sql_execute_fetch_all(sql, params, to_dict=True)

    @staticmethod
    def get_cp_rm_details(user_id):
        sql = """
                SELECT lc.first_name as cp_name, lc.encoded_email as cp_email,
                lr.name as rm_name, lr.encoded_email as rm_email
                FROM lendenapp_customuser lc
                LEFT JOIN lendenapp_reference lr ON lr.user_id = lc.id 
                AND relation = %(rm_relation)s 
                WHERE lc.user_id = %(user_id)s
                """

        params = {"user_id": user_id, "rm_relation": ReferenceConstant.RELATION_RM}

        return InvestorMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def get_aml_data_from_user_source_id(user_source_id):
        sql = """
            SELECT lu.aml_status, lcp.user_id as cp_user_pk, 
            lc.first_name as cp_name, lc2.first_name as lender_name, 
            lc.encoded_email as cp_email, lc2.encoded_email as lender_email
            FROM lendenapp_userkyctracker lu
            JOIN lendenapp_user_source_group lusg 
            ON lusg.id = lu.user_source_group_id
            JOIN lendenapp_channelpartner lcp 
            ON lcp.id = lusg.channel_partner_id
            JOIN lendenapp_customuser lc ON lcp.user_id = lc.id
            JOIN lendenapp_customuser lc2 on lusg.user_id = lc2.id
            where lu.user_source_group_id = %(user_source_id)s 
            AND lu.is_latest_kyc
        """

        params = {"user_source_id": user_source_id}

        return InvestorMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def update_account_status_based_on_user_source_id(
        user_source_id, number, account_status
    ):
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
            "user_source_group_id": user_source_id,
            "account_status": account_status,
            "listed_date": get_todays_date_in_ist(),
            "number": number,
            "open_status": AccountStatus.OPEN,
        }
        return InvestorMapper().sql_execute_fetch_one(sql, params, index_result=True)

    @staticmethod
    def get_check_list(user_source_id, user_pk, is_cp=False):
        query = """select checklist from lendenapp_task lt where """
        query += (
            "created_by_id = %(user_pk)s"
            if is_cp
            else "user_source_group_id = %(user_source_group_id)s"
        )

        params = {"user_source_group_id": user_source_id, "user_pk": user_pk}
        try:
            result = InvestorMapper().sql_execute_fetch_one(query, params, index_result=True)
            if isinstance(result, str):
                return ast.literal_eval(result)
            return result
        
        except Exception as e:
            return {}

    @staticmethod
    def get_kyc_tracking_data(user_source_id):
        sql = """
        select lusg.user_id, lu.tracking_id, 
        lu.status, ls.source_name
        from lendenapp_user_source_group lusg
        join lendenapp_source ls on ls.id = lusg.source_id
        left join lendenapp_userkyctracker lu
        on lu.user_source_group_id = lusg.id
        and lu.is_latest_kyc
        where lusg.id = %(user_source_id)s
        """

        params = {"user_source_id": user_source_id}
        return InvestorMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def get_user_kyc_and_address_data(tracking_id, user_id):
        sql = """    
                select lc.id as user_id, lc.first_name, lc.dob, 
                lc.encoded_pan as pan, ls.source_name as source,
                la.pin as pin, la.country as country, 
                la.location as location, lusg.id as user_source_group_id,
                lt.id as task_id,la.id as address_id,lusg.group_id
                from lendenapp_customuser lc
                join lendenapp_userkyctracker lu on lu.user_id = lc.id
                join lendenapp_task lt on lt.user_source_group_id = lu.user_source_group_id
                left join lendenapp_address la on la.user_source_group_id = lu.user_source_group_id
                left join lendenapp_user_source_group lusg on lusg.id = lu.user_source_group_id
                left join lendenapp_source ls on ls.id = lusg.source_id
                where lu.status=%(status)s and lu.is_latest_kyc and 
                lu.kyc_source=%(kyc_source)s and 
                lu.tracking_id = %(tracking_id)s and lc.user_id = %(user_id)s
        """

        params = {
            "tracking_id": tracking_id,
            "user_id": user_id,
            "status": KYCConstant.SUCCESS,
            "kyc_source": KYCConstant.MANUAL,
        }

        return InvestorMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def insert_campaign_wallet_data(user_source_group_id, amount=0):
        sql = """
                INSERT INTO lendenapp_campaign_wallet (user_source_group_id, total_amount, available_amount)
                SELECT %(user_source_group_id)s, %(amount)s, %(amount)s
                WHERE NOT EXISTS (
                    SELECT 1 FROM lendenapp_campaign_wallet WHERE user_source_group_id = %(user_source_group_id)s
                ) RETURNING id;
        """
        params = {"user_source_group_id": user_source_group_id, "amount": amount}
        return InvestorMapper().sql_execute_fetch_one(sql, params, index_result=True)

    @staticmethod
    def get_pending_reward_data(data):
        sql = """
                select id, amount, user_source_group_id from lendenapp_reward
                where related_user_source_group_id = %(user_source_group_id)s 
                and status = %(pending_status)s and campaign_id = %(campaign_id)s
                and (expiry_date > CURRENT_DATE OR expiry_date IS NULL);
            """

        params = {
            "user_source_group_id": data["user_source_group_id"],
            "pending_status": RewardStatus.PENDING,
            "campaign_id": data["campaign_id"],
        }

        return InvestorMapper().sql_execute_fetch_all(sql, params, to_dict=True)

    @staticmethod
    def update_campaign_wallet_data(user_source_group_ids, amount):
        sql = """
                update lendenapp_campaign_wallet
                set total_amount = total_amount + %(amount)s, 
                available_amount = available_amount + %(amount)s, updated_date = now()
                where user_source_group_id = ANY(%(user_source_group_ids)s) 
                returning id;
            """

        params = {"user_source_group_ids": user_source_group_ids, "amount": amount}
        params = DataLayerUtils().prepare_sql_params(params)
        return InvestorMapper().sql_execute_fetch_one(sql, params, index_result=True)

    @staticmethod
    def get_idle_fund_in_review_transactions(
        limit=None, offset=None, transaction_ids=None, from_date=None, to_date=None
    ):
        sql = """
            SELECT lt.id as txn_pk, lt.type transaction_type,
            lb.ifsc_code, 
            lb.name, lb.number, lb.type, lc.first_name,
            lc.encoded_email as email, 
            lt.user_source_group_id as user_source_id, 
            lc.encoded_mobile as mobile_number,
            lc.id as user_pk, lt.amount, lt.transaction_id,
            lfw.failure_reason, ls.source_name as source
            FROM lendenapp_transaction lt 
            JOIN lendenapp_fmi_withdrawals lfw on 
			lt.user_source_group_id = lfw.user_source_group_id and 
			concat(REGEXP_REPLACE(lt.transaction_id, '_03$', '') , '_02') = lfw.transaction_id
            JOIN lendenapp_user_source_group lusg on 
            lt.user_source_group_id = lusg.id 
            join lendenapp_customuser lc on 
            lusg.user_id = lc.id
            INNER JOIN lendenapp_account la ON la.user_source_group_id  = lusg.id
            INNER JOIN lendenapp_bankaccount lb on la.bank_account_id = lb.id
            INNER JOIN lendenapp_source ls on lusg.source_id = ls.id
            WHERE lc.id <> ALL(%(block_user)s)
            AND lb.is_active = TRUE
            AND lt.status = %(status)s
            AND lfw.status = %(previous_status)s
        """

        params = {
            "block_user": tuple(TransactionBlockForUser.user_pk_list),
            "limit": limit,
            "offset": offset,
            "status": TransactionStatus.IN_REVIEW,
            "previous_status": FMITransactionStatus.FAILED,
        }

        if from_date and to_date:
            sql += (
                """ AND Date(lt.created_date) BETWEEN %(from_date)s AND %(to_date)s"""
            )
            params["from_date"] = from_date
            params["to_date"] = to_date

        if transaction_ids:
            sql += """ AND lt.transaction_id = %(transaction_ids)s"""
            params["transaction_ids"] = transaction_ids

        sql += """ LIMIT %(limit)s OFFSET %(offset)s"""

        params = DataLayerUtils().prepare_sql_params(params)
        return InvestorMapper().sql_execute_fetch_all(sql, params, to_dict=True)

    def check_gst_data_exists(self, from_date, to_date, invoice_type):
        params = {"user_id": self.investor_pk}
        conditions = "user_id = %(user_id)s"

        if invoice_type == InvoiceType.INDIVIDUAL:
            conditions += " AND transaction_date = %(transaction_date)s"
            params["transaction_date"] = from_date

        else:
            conditions += " AND transaction_date between %(from_date)s and %(to_date)s"
            params["from_date"] = from_date
            params["to_date"] = to_date

        sql = f"""
                select id from lendenapp_user_gst
                where {conditions}
                """

        return self.sql_execute_fetch_one(sql, params, to_dict=True)

    def insert_staff_log(self, data):
        return self.insert_data(table_name="lendenapp_cp_staff_log", data=data)

    @staticmethod
    def lending_amount(user_source_id, type):
        sql = """
                select amount from lendenapp_transaction lt where
                type = ANY(%(types)s) and status = %(status)s
                and user_source_group_id = %(user_source_id)s
                ORDER BY created_date DESC
                LIMIT 1
        """
        params = {
            "types": type,
            "status": TransactionStatus.COMPLETED,
            "user_source_id": user_source_id,
        }
        params = DataLayerUtils().prepare_sql_params(params)
        return InvestorMapper().sql_execute_fetch_one(sql, params, index_result=True)

    @staticmethod
    def fetch_rm_lender_details(data):
        sql = f"""
            SELECT 
                lc.user_id, lc.first_name, lc.encoded_email as email, lc.encoded_mobile as mobile_number, 
                CASE 
                    WHEN lr.id IS NOT NULL THEN true ELSE false 
                END AS assigned_rm, lusg.id as user_source_id,
                lr.name AS rm_name, lr.encoded_email AS rm_email, lr.encoded_mobile AS rm_mobile
            FROM lendenapp_user_source_group lusg 
            JOIN lendenapp_source ls ON ls.id = lusg.source_id AND ls.source_name = %(source_name)s
            JOIN lendenapp_customuser lc ON lc.id = lusg.user_id
            LEFT JOIN lendenapp_reference lr ON lr.user_source_group_id = lusg.id
            WHERE true
        """
        params = {
            "source_name": InvestorSource.LDC,
            "limit": data["limit"],
            "offset": data["offset"],
        }
        search = data.get("search")
        search_query_type = data.get("search_query_type")

        if search:
            search_query_map = {
                SearchKey.USER_ID: "lc.user_id = %(search)s",
                SearchKey.MOBILE_NO: "lr.encoded_mobile = %(search)s",
                SearchKey.EMAIL: "lr.encoded_email = %(search)s",
            }

            params["search"] = search
            sql += f" and {search_query_map.get(search_query_type, '')}"

        if data.get("filter_type") == RMLenderFilterTypes.ASSIGNED_RM:
            sql += " and lr.id IS NOT NULL"
        elif data.get("filter_type") == RMLenderFilterTypes.UNASSIGNED_RM:
            sql += " and lr.id IS NULL"

        sql += " LIMIT %(limit)s OFFSET %(offset)s"

        return InvestorMapper().sql_execute_fetch_all(sql, params, to_dict=True)

    @staticmethod
    def fail_nach_transactions(transaction_id):
        sql = """
              update lendenapp_transaction
              set status=%(status)s, \
                  updated_date=%(updated_date)s,
                  status_date=%(status_date)s,
                  rejection_reason=%(rejection_reason)s
              where transaction_id = %(transaction_id)s \
              and status = %(scheduled_status)s
              returning id;
              """

        params = {
            "scheduled_status": TransactionStatus.SCHEDULED,
            "transaction_id": transaction_id,
            "status": TransactionStatus.FAILED,
            "updated_date": get_current_dtm(),
            "status_date": get_todays_date_in_ist(),
            "rejection_reason": MandateConstants.CANCEL_MANDATE_REMARK,
        }

        return InvestorMapper().sql_execute_fetch_one(sql, params, index_result=True)

    def fail_nach_presentation(self, txn_id):
        """
        Update NACH presentation with raw SQL including expiry_time check
        """
        sql = """
              UPDATE lendenapp_nach_presentation
              SET status = %(status)s,
                  remarks = %(remarks)s,
                  updated_date = %(updated_date)s
              WHERE transaction_id = %(transaction_id)s
                AND status = %(current_status)s
                AND product_type = %(product_type)s
                AND user_source_group_id = %(user_source_group_id)s
                AND %(current_dtm)s < expiry_time RETURNING id;
              """

        params = {
            "status": MandateStatus.FAILED,
            "remarks": MandateConstants.CANCEL_MANDATE_REMARK,
            "updated_date": get_current_dtm(),
            "transaction_id": txn_id,
            "current_status": MandateStatus.INITIATED,
            "product_type": MandateConstants.NACH_ADD_MONEY,
            "user_source_group_id": self.user_source_id,
            "current_dtm": get_current_dtm(),
        }

        return self.sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def get_lender_detail(mobile_number, email, partner_code, partner_id):
        sql = """
                select lusg.id as user_source_group_id, lc.id as user_pk
                from lendenapp_customuser lc
                join lendenapp_user_source_group lusg on lusg.user_id = lc.id
                join lendenapp_source ls on lusg.source_id = ls.id 
            """

        params = {"source": partner_code}

        if partner_id:
            sql += """ join lendenapp_channelpartner lc2 on lusg.channel_partner_id = lc2.id
                    where ls.source_name = %(source)s and lc2.partner_id = %(partner_id)s """
            params["partner_id"] = partner_id

        else:
            sql += """ where ls.source_name = %(source)s """

        if mobile_number:
            params["encoded_mobile"] = mobile_number
            sql += " and lc.encoded_mobile = %(encoded_mobile)s "
        if email:
            params["encoded_email"] = email
            sql += " and lc.encoded_email = %(encoded_email)s "

        return InvestorMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def get_pending_scheme_supply_status():
        try:
            sql = """
                    SELECT ls.created_date::date as created_date, ls.tenure,
                        CASE WHEN lusg.source_id = 7 THEN 'RETAIL' ELSE 'CP' END AS channel,
                        SUM(ls.amount) as amount,
                        COUNT(ls.*) as count
                    FROM lendenapp_schemeinfo ls
                            JOIN lendenapp_user_source_group lusg ON ls.user_source_group_id = lusg.id
                    WHERE ls.status = 'INITIATED' AND ls.investment_type = ANY(ARRAY['ONE_TIME_LENDING', 'MEDIUM_TERM_LENDING'])
                    GROUP BY ls.created_date::date, ls.tenure, channel
                    ORDER BY ls.created_date::date;
            """
            return InvestorMapper().sql_execute_fetch_all(sql, {}, to_dict=True)
        except Exception as e:
            logger.error(f"Error in get_pending_scheme_supply_status: {e}")
            return None

    @staticmethod
    def get_priortised_scheme_supply_status():
        try:
            sql = """
                    SELECT ls.created_date::date as created_date, ls.tenure,
                        CASE WHEN lusg.source_id = 7 THEN 'RETAIL' ELSE 'CP' END AS channel,
                        SUM(ls.amount) as amount,
                        COUNT(ls.*) as count
                    FROM lendenapp_schemeinfo ls
                        JOIN lendenapp_otl_scheme_tracker lost ON lost.scheme_id = ls.scheme_id AND lost.is_latest
                        JOIN lendenapp_user_source_group lusg ON ls.user_source_group_id = lusg.id
                    WHERE ls.status = 'INITIATED' AND ls.investment_type = ANY(ARRAY['ONE_TIME_LENDING', 'MEDIUM_TERM_LENDING'])
                    AND lost.priority_order = %(priority_order)s
                    GROUP BY ls.created_date::date, ls.tenure, channel
                    ORDER BY ls.created_date::date;
            """
            params = {
                "priority_order": STLSchemePriorityOrderValues.ALLOW_COMPLETE_SCHEME_CREATION
            }
            return InvestorMapper().sql_execute_fetch_all(sql, params, to_dict=True)
        except Exception as e:
            logger.error(f"Error in get_priortised_scheme_supply_status: {e}")
            return None

    @staticmethod
    def get_success_scheme_status():
        try:
            sql = """
                    SELECT ls.created_date::date as created_date, ls.tenure,
                        CASE WHEN lusg.source_id = 7 THEN 'RETAIL' ELSE 'CP' END AS channel,
                        SUM(ls.amount) as amount,
                        COUNT(ls.*) as count
                    FROM lendenapp_schemeinfo ls
                            JOIN lendenapp_user_source_group lusg ON ls.user_source_group_id = lusg.id
                    WHERE ls.status = 'SUCCESS' AND ls.investment_type = ANY(ARRAY['ONE_TIME_LENDING', 'MEDIUM_TERM_LENDING'])
                    AND ls.updated_date::date = CURRENT_DATE 
                    GROUP BY ls.created_date::date, ls.tenure, channel;   
            """
            return InvestorMapper().sql_execute_fetch_all(sql, {}, to_dict=True)
        except Exception as e:
            logger.error(f"Error in get_success_scheme_status: {e}")
            return None

    @staticmethod
    def get_pending_supply_scheme_details(
        limit, offset, investment_type=None, tenure=None
    ):
        try:
            sql = """
                SELECT ls.scheme_id,
                    ls.created_date::date as created_date,
                    lc.user_id as lender_user_id,
                    lc.first_name as lender_name,
                    ls.amount,
                    ls.tenure,
                    CASE WHEN ls2.source_name = %(source_name)s THEN 'RETAIL' ELSE 'CP' END AS source,
                    lc3.first_name as cp_name,
                    CASE WHEN ls2.source_name = %(source_name)s THEN lr2.name ELSE lr.name END AS rm_name,
                    la.city,
                    la.state,
                    CASE WHEN lost.priority_order = 0 THEN TRUE ELSE FALSE END AS priortize,
                    TO_CHAR(lost.prioritization_dtm AT TIME ZONE 'Asia/Kolkata', 'YYYY-MM-DD HH12:MI AM') AS prioritization_dtm,
                    lost.next_notification,
                    lost.notification_count,
                    TO_CHAR(lost.last_notification_dtm AT TIME ZONE 'Asia/Kolkata', 'YYYY-MM-DD HH12:MI AM') AS last_notification_dtm,
                    lost.notification_status, 
                    lost.amount_per_loan,
                    lost.product_type,
                    lost.preference_id
                FROM lendenapp_schemeinfo ls
                    JOIN lendenapp_otl_scheme_tracker lost ON lost.scheme_id = ls.scheme_id AND lost.is_latest
                    JOIN lendenapp_user_source_group lusg ON ls.user_source_group_id = lusg.id
                    JOIN lendenapp_source ls2 ON ls2.id = lusg.source_id
                    JOIN lendenapp_customuser lc ON lusg.user_id = lc.id
                    LEFT JOIN lendenapp_channelpartner lc2 ON lusg.channel_partner_id = lc2.id
                    LEFT JOIN lendenapp_customuser lc3 ON lc2.user_id = lc3.id
                    LEFT JOIN lendenapp_reference lr ON lr.user_id = lc3.id and lr.relation = 'RM'
                    LEFT JOIN lendenapp_reference lr2 ON lr2.user_id = lc.id and lr2.relation = 'RM'
                    LEFT JOIN LATERAL (
                            SELECT la.state, la.city
                            FROM lendenapp_address la
                            WHERE la.user_source_group_id = lusg.id
                              AND la.type = 'COMMUNICATION'
                            ORDER BY la.id DESC
                            LIMIT 1
                        ) la ON true
                WHERE ls.status = 'INITIATED'
            """
            params = {
                "limit": limit,
                "offset": offset,
                "source_name": InvestorSource.LDC,
            }
            if investment_type is not None:
                sql += " AND ls.investment_type = %(investment_type)s"
                params["investment_type"] = investment_type
            else:
                sql += " AND ls.investment_type = ANY(ARRAY['ONE_TIME_LENDING', 'MEDIUM_TERM_LENDING'])"

            if tenure is not None:
                sql += " AND ls.tenure = %(tenure)s"
                params["tenure"] = tenure
            sql += " ORDER BY ls.id LIMIT %(limit)s OFFSET %(offset)s;"
            return InvestorMapper().sql_execute_fetch_all(sql, params, to_dict=True)
        except Exception as e:
            logger.error(f"Error in get_pending_scheme_supply_details: {e}")
            return None

    @staticmethod
    def update_stl_scheme_notify_status(scheme_ids):
        try:
            sql = """
                UPDATE lendenapp_otl_scheme_tracker
                SET notification_status = 'PROCESSING'
                WHERE scheme_id = ANY(%(scheme_ids)s) 
                AND status = 'INITIATED' 
                AND is_latest = TRUE
                RETURNING scheme_id;
            """
            return InvestorMapper().sql_execute_fetch_all(
                sql, {"scheme_ids": scheme_ids}, to_dict=True
            )
        except Exception as e:
            logger.error(f"Error in update_stl_scheme_notify_status: {e}")
            return None

    @staticmethod
    def get_otl_scheme_list():
        try:
            sql = """
                SELECT ls.scheme_id,
                    ls.created_date::date as created_date,
                    ls.amount,
                    ls.tenure,
                    CASE WHEN lusg.source_id = 7 THEN 'RETAIL' ELSE 'CP' END AS source,
                    ls.preference_id,
                    lost.status
                FROM lendenapp_schemeinfo ls
                        JOIN lendenapp_otl_scheme_tracker lost ON lost.scheme_id = ls.scheme_id AND lost.is_latest
                        JOIN lendenapp_user_source_group lusg ON ls.user_source_group_id = lusg.id
                WHERE lost.updated_date >= now() - interval '3 hours'
                ;
            """
            return InvestorMapper().sql_execute_fetch_all(sql, {}, to_dict=True)
        except Exception as e:
            logger.error(f"Error in get_otl_scheme_list: {e}")
            return None

    @staticmethod
    def de_prioritize_stl_scheme(scheme_ids):
        try:
            sql = """
                UPDATE lendenapp_otl_scheme_tracker
                SET priority_order = 1
                WHERE scheme_id = ANY(%(scheme_ids)s) 
                AND status = 'INITIATED' 
                AND is_latest = TRUE
                AND priority_order = 0
                RETURNING scheme_id;
            """
            return InvestorMapper().sql_execute_fetch_all(
                sql, {"scheme_ids": scheme_ids}, to_dict=True
            )
        except Exception as e:
            logger.error(f"Error in de_prioritize_stl_scheme: {e}")
            return None

    @staticmethod
    def get_mnrl_status(user_pk, is_cp=False):
        if is_cp:
            sql = """
            SELECT lc.mnrl_status, lr.encoded_email as rm_email
            FROM lendenapp_customuser lc 
            LEFT JOIN lendenapp_reference lr
            ON lc.id = lr.user_id and lr.relation = %(RM)s
            WHERE lc.id = %(user_pk)s
            """
        else:
            sql = """
            SELECT lc.mnrl_status
            FROM lendenapp_customuser lc 
            WHERE lc.id = %(user_pk)s
            """

        params = {"user_pk": user_pk, "RM": RMReference.RELATION_RM}

        return InvestorMapper().sql_execute_fetch_one(sql, params, to_dict=True)

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
            "user_id": self.investor_pk,
            "investment_type": investment_type,
            "from_date": from_date,
            "to_date": to_date,
        }

        return self.sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def check_scheme_data(scheme_id, tenure):
        sql = """
                SELECT amount, created_date::DATE FROM lendenapp_schemeinfo
                WHERE scheme_id = %(scheme_id)s 
                AND status = %(status)s 
                AND tenure = %(tenure)s;
            """

        params = {
            "scheme_id": scheme_id,
            "status": TransactionStatus.INITIATED,
            "tenure": tenure,
        }

        return InvestorMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def get_ml_filter_and_sort_config():
        sql = """
            SELECT config_value::json FROM
            lendenapp_application_config
            WHERE config_key = %(config_key)s
            AND config_type = %(config_type)s
            ;
        """

        params = {
            "config_key": RedisConstants.ML_FILTER_AND_SORT,
            "config_type": RedisConstants.ML_FILTER_AND_SORT,
        }

        return InvestorMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def fetch_success_repayment_data(user_source_group_id, transaction_id):
        sql = """
            select lsrd.type as txn_type, lt.user_source_group_id, lt.status_date,
                   ROUND(SUM(lsrd.principal), 2) AS principal, 
                   ROUND(SUM(lsrd.interest), 2) AS interest, 
                   ROUND(SUM(lsrd.debit_amount), 2) AS total_amount
            from lendenapp_transaction lt  
            join lendenapp_scheme_repayment_details lsrd 
                on lt.id = lsrd.withdrawal_transaction_id
            join lendenapp_user_source_group lusg
                on lt.user_source_group_id = lusg.id
            join lendenapp_source ls
                on ls.id = lusg.source_id
            where lt.user_source_group_id = %(user_source_group_id)s
                AND lt.transaction_id = %(transaction_id)s
                AND lt.type = ANY(%(txn_type)s)
                AND (
                    (ls.source_name = %(ldc_source)s AND lt.status = %(processing_status)s) OR
                    (ls.source_name = ANY(%(cp_source)s) AND lt.status = %(processing_status)s)
                  )
            group by lt.user_source_group_id, lsrd.type, lt.status_date
        """
        params = {
            "processing_status": TransactionStatus.PROCESSING,
            "txn_type": [
                TransactionType.SHORT_TERM_LENDING_AUTO_WITHDRAWAL,
                TransactionType.MANUAL_LENDING_AUTO_WITHDRAWAL,
                TransactionType.MEDIUM_TERM_LENDING_AUTO_WITHDRAWAL,
                TransactionType.REPAYMENT_AUTO_WITHDRAWAL,
                TransactionType.LUMPSUM_AUTO_WITHDRAWAL,
            ],
            "ldc_source": InvestorSource.LDC,
            "cp_source": [InvestorSource.LCP, InvestorSource.MCP],
            "user_source_group_id": user_source_group_id,
            "transaction_id": transaction_id,
        }

        return InvestorMapper().sql_execute_fetch_all(sql, params, to_dict=True)

    @staticmethod
    def get_cp_detail(user_source_id, selected_columns=None):
        if not selected_columns:
            selected_columns = ["*"]

        selected_columns_str = ", ".join(selected_columns)

        sql = f""" 
                select {selected_columns_str} 
                from lendenapp_user_source_group lusg 
                join lendenapp_source ls ON lusg.source_id = ls.id 
                join lendenapp_channelpartner lc ON lc.id = lusg.channel_partner_id 
                join lendenapp_customuser lc2 ON lc2.id = lc.user_id 
                WHERE lusg.id = %(user_source_id)s and ls.source_name = ANY(%(source)s) 
            """
        params = {
            "user_source_id": user_source_id,
            "source": [InvestorSource.LCP, InvestorSource.MCP],
        }
        return InvestorMapper().sql_execute_fetch_one(sql, params, to_dict=True)

    def get_lender_data(self):
        sql = """
            SELECT first_name,encoded_mobile as mobile_number, ucic_code,
            encoded_email as email,user_id, encoded_pan,dob,email_verification
            FROM lendenapp_customuser
            WHERE id=%(user_id)s
        """
        params = {"user_id": self.investor_pk}
        return self.sql_execute_fetch_one(sql, params, to_dict=True)

    @staticmethod
    def pending_networth_certificate_list(limit, offset):
        sql = """
            SELECT 
            ld.file,
            lc3.first_name,
            lc3.encoded_pan pan,
            ld.remark, 
            ld.fiscal_year,
            ld.created_date,
            ld.id as document_id,
            lc3.user_id,
            CASE 
                WHEN lusg.channel_partner_id IS NULL THEN 'RETAIL' 
                ELSE 'CP' 
            END AS SOURCE,
            lc2.encoded_mobile as cp_mobile
            FROM lendenapp_document ld
            JOIN lendenapp_user_source_group lusg ON lusg.id = ld.user_source_group_id
            JOIN lendenapp_customuser lc3 on lc3.id = lusg.user_id
            LEFT JOIN lendenapp_channelpartner lc ON lc.id = lusg.channel_partner_id
            LEFT JOIN lendenapp_customuser lc2 ON lc2.id = lc.user_id
            WHERE ld.type = %(networth_certificate)s
            AND ld.remark = %(submitted)s
            ORDER by ld.created_date desc
            LIMIT %(limit)s OFFSET %(offset)s;
        """

        params = {
            "submitted": DocumentRemark.SUBMITTED,
            "networth_certificate": DocumentConstant.SIGNED_NETWORTH_CERTIFICATE,
            "limit": limit,
            "offset": offset,
        }

        return InvestorMapper().sql_execute_fetch_all(sql, params, to_dict=True)

    def get_head_of_family_data(self, selected_columns):
        selected_columns_str = ", ".join(selected_columns)
        sql = f"""
            SELECT {selected_columns_str}
            FROM lendenapp_customuser lc
            JOIN lendenapp_reference lr ON lr.user_id = lc.id
            WHERE lr.user_source_group_id = %(user_source_id)s
            AND lc.is_active = %(active_status)s
            AND lr.type = %(type)s
        """
        params = {
            "user_source_id": self.user_source_id,
            "type": HOFMember.REFERENCE_TYPE,
            "active_status": True,
        }
        return self.sql_execute_fetch_one(sql, params, to_dict=True)

    def check_account_termination_eligibility(self):
        sql = """
            SELECT
                la.balance, la.status AS account_status,
                lusg.status AS activity_status, lusg.expiry_date,
                MAX(lsi.id) FILTER (WHERE lsi.id IS NOT NULL) AS initiated_scheme_ids,
                MAX(ltr.id) FILTER (WHERE ltr.id IS NOT NULL) AS relevant_transaction_id
            FROM
                lendenapp_user_source_group lusg
            JOIN
                lendenapp_account la ON lusg.id = la.user_source_group_id
            LEFT JOIN
                lendenapp_schemeinfo lsi ON lusg.id = lsi.user_source_group_id 
                AND lsi.status = %(scheme_info_status)s
            LEFT JOIN
                lendenapp_transaction ltr ON lusg.id = ltr.user_source_group_id 
                AND ltr.status = ANY(%(transaction_type)s)
            WHERE
                lusg.id = %(user_source_group_id)s
            GROUP BY
                la.balance, la.status, lusg.status, lusg.id
        """
        params = {
            "user_source_group_id": self.user_source_id,
            "scheme_info_status": TransactionStatus.INITIATED,
            "transaction_type": [
                TransactionStatus.SCHEDULED,
                TransactionStatus.PROCESSING,
                TransactionStatus.PENDING,
                TransactionStatus.ON_HOLD,
                TransactionStatus.IN_REVIEW,
                TransactionStatus.HOLD,
                TransactionStatus.CREATED,
            ],
        }
        return self.sql_execute_fetch_one(sql, params, to_dict=True)

    def get_lock_on_txn(self, transaction_ids, status):
        sql = """
            SELECT id
                FROM lendenapp_transaction lt
                WHERE lt.transaction_id =ANY (%(transaction_id)s)
                AND lt.status = ANY(%(txn_status)s)
                FOR UPDATE OF lt NOWAIT
            """

        params = {"transaction_id": transaction_ids, "txn_status": status}
        return self.execute_sql(sql, params, return_rows_count=True)

    def fetch_user_details_from_user_source_id(self, user_source_id):
        sql = """
            select lc.* from lendenapp_customuser lc
            join lendenapp_user_source_group lusg 
            on lusg.user_id=lc.id
            join lendenapp_source ls on ls.id=lusg.source_id
            where lusg.id=%(user_source_group_id)s 
        """

        params = {"user_source_group_id": user_source_id}

        return self.sql_execute_fetch_one(sql, params, to_dict=True)
