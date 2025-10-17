from django.conf import settings


class GroupName:
    LENDER = "LENDER"
    MCP = "MASTER CHANNEL PARTNER"


class UserGroupSourceStatus:
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"


class AccountStatus:
    LISTED = "LISTED"
    OPEN = "OPEN"


class UserGroup:
    MCP = 39
    CP = 37
    LENDER = 6
    BORROWER = 5


class AddressType:
    PERMANENT = "PERMANENT"
    COMMUNICATION = "COMMUNICATION"


class AddressConstants:
    COMMUNICATION_TYPE = "COMMUNICATION"
    PERMANENT_TYPE = "PERMANENT"


class DateFormat:
    YEAR_MONTH_DAY = "%Y-%m-%d"


class ServerType:
    PRODUCTION = "PRODUCTION"
    DEVELOPMENT = "DEVELOPMENT"


class TimeZone:
    indian_time = "Asia/Kolkata"


class DashboardFilterTypes:
    ALL = "all"
    ALL_CP = "all_cp"
    SELF = "self"
    CP_USER_ID = "cp_user_id"


class InvestorSource:
    LDC = "LDC"
    LCP = "LCP"
    MCP = "MCP"


class AddBankAccountConstant:
    PRIMARY_PURPOSE = "PRIMARY"
    SECONDARY_PURPOSE = "SECONDARY"


class ChecklistStep:
    LIVE_KYC = "LIVE KYC"


class KMIServices:
    INITIATE_KYC = "INITIATE KYC"


class DocumentConstant:
    SIGNED_NETWORTH_CERTIFICATE = "signed_networth_certificate"
    TERMS_AND_CONDITIONS = "TERMS AND CONDITIONS"
    AUTHORIZATION_LETTER = "authorization_letter"
    LENDER_AGREEMENT = "lender_agreement"
    PHOTOGRAPH = "photograph"
    DIGITAL_CERTIFICATE = "fmpp_digital_certificate"
    NETWORTH_CERTIFICATE_TYPE = "signed_networth_certificate"
    AADHAR_CARD_FRONT_BOTTOM = "aadhaar_front_bottom"
    BROKERAGE_INVOICE = "brokerage_invoice"
    PAN_CARD = "pan_card"
    RELATIONSHIP = "relationship"


class DocumentRemark:
    SUBMITTED = "SUBMITTED"


class KmiCallBackStatus:
    INITIATED = "INITIATED"


class FMPPInvestmentType:
    MANUAL_LENDING = "MANUAL_LENDING"
    AUTO_LENDING = "AUTO_LENDING"
    ONE_TIME_LENDING = "ONE_TIME_LENDING"
    MEDIUM_TERM_LENDING = "MEDIUM_TERM_LENDING"


class TransactionStatus:
    SUCCESS = "SUCCESS"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    PENDING = "PENDING"
    FAIL = "FAIL"
    SCHEDULED = "SCHEDULED"
    IN_REVIEW = "IN REVIEW"
    EXPIRED = "EXPIRED"
    INITIATED = "INITIATED"
    HOLD = "HOLD"
    CREATED = "CREATED"
    ON_HOLD = "ON HOLD"
    IN_PROGRESS = "IN PROGRESS"


class NotificationStatus:
    READ = "READ"
    UNREAD = "UNREAD"


class CKYCServiceType:
    NAME_MATCH = "NAME_MATCH"


class KYCConstant:
    FAILED = "FAILED"
    IN_PROGRESS = "IN_PROGRESS"
    INITIATED = "INITIATED"
    SUCCESS = "SUCCESS"
    PENDING = "PENDING"
    RISK_HIGH = "HIGH"
    MANUAL = "MANUAL"


class CashFreeConstants:
    ESIGN = "ESIGN"
    SUCCESS = "SUCCESS"
    BANK_ACCOUNT = "BANK ACCOUNT"
    VALID = "VALID"


class KycServices:
    NAME_MATCH = "NAME_MATCH"


class ConsentData:
    LDC_kyc_consent_data = {
        "consent_type": "Verify_your_Identity",
        "remark": "I authorize the company to fetch my KYC details via Central "
        "KYC (CKYC) Registry.",
    }
    politically_exposed = {
        "consent_type": "Politically_exposed",
        "remark": "Are you a politically exposed person?",
    }


class KYCSource:
    MANUAL_SOURCE = "MANUAL"


class ReferenceConstant:
    TYPE_RM = "REFERRED_BY"
    RELATION_RM = "RM"
    TYPE_COMPANY_DETAILS = "COMPANY_DETAILS"


class RMReference:
    RELATION_RM = "RM"


class MandateConstants:
    CANCEL_MANDATE_REMARK = "Mandate Cancelled"
    NACH_ADD_MONEY = "NACH_ADD_MONEY"


class NachStatus:
    NOT_INITIATED = "NOT INITIATED"
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"


class MandateStatus:
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    INITIATED = "INITIATED"


class NMIConstants:
    CANCEL_MANDATE_REMARK = "Mandate Cancelled"


class SchemeStatus:
    INITIATED = "INITIATED"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    PENDING = "PENDING"
    ALL = "ALL"
    

class ReportFilterType:
    ALL = 'all'


class ReportFilterKey:
    SCHEME_MATURITY = "SCHEME MATURITY"
    INACTIVITY_WITHDRAWAL = "INACTIVITY WITHDRAWAL"


class InvestorSourceId:
    LCP = '3'
    MCP = '8'


class TransactionType:
    FMPP_INVESTMENT = "FMPP INVESTMENT"
    MANUAL_LENDING = "MANUAL LENDING"
    AUTO_LENDING = "AUTO LENDING"
    SHORT_TERM_LENDING = "SHORT TERM LENDING"
    WITHDRAW_MONEY = "WITHDRAW MONEY"
    ADD_MONEY = "ADD MONEY"
    MANUAL_LENDING_AUTO_WITHDRAWAL = "MANUAL LENDING AUTO WITHDRAWAL"
    LUMPSUM_AUTO_WITHDRAWAL = "LUMPSUM AUTO WITHDRAWAL"
    SHORT_TERM_LENDING_AUTO_WITHDRAWAL = "SHORT TERM LENDING AUTO WITHDRAWAL"
    MEDIUM_TERM_LENDING_AUTO_WITHDRAWAL = "MEDIUM TERM LENDING AUTO WITHDRAWAL"
    AUTO_LENDING_REPAYMENT_WITHDRAWAL = "AUTO LENDING REPAYMENT WITHDRAWAL"
    MIP_AUTO_WITHDRAWAL = "MIP AUTO WITHDRAWAL"
    FMPP_REDEMPTION = "FMPP REDEMPTION"
    AUTO_LENDING_REPAYMENT_ADD_MONEY = "AUTO LENDING REPAYMENT ADD MONEY"
    IDLE_FUND_WITHDRAWAL = "IDLE FUND WITHDRAWAL"
    REPAYMENT_AUTO_WITHDRAWAL = "REPAYMENT AUTO WITHDRAWAL"
    FMPP_REPAYMENT_WITHDRAWAL = "FMPP REPAYMENT WITHDRAWAL"
    WITHDRAWAL_TRANSACTION_TYPE = [
        'WITHDRAW MONEY',
        'MANUAL LENDING AUTO WITHDRAWAL',
        'MIP AUTO WITHDRAWAL',
        'SHORT TERM LENDING AUTO WITHDRAWAL',
        'LUMPSUM AUTO WITHDRAWAL',
        'MEDIUM TERM LENDING AUTO WITHDRAWAL',
        'AUTO LENDING REPAYMENT WITHDRAWAL',
        'LUMPSUM REFUND',
        'SHORT TERM LENDING REFUND',
        'MANUAL LENDING REFUND',
        'MEDIUM TERM LENDING REFUND',
        'CANCELLED LOAN REFUND',
        'IDLE FUND WITHDRAWAL',
        'REVENUE TRANSFER',
        'REPAYMENT AUTO WITHDRAWAL',
        'REJECTED LOAN REFUND',
        'FMPP REPAYMENT WITHDRAWAL'
    ]


class AppRating:
    SUBMITTED = "SUBMITTED"
    SKIPPED = "SKIPPED"
    USER = "USER"
    SCHEME = "SCHEME"


class RPDStatus:
    SUCCESS = "SUCCESS"


class SearchKey:
    USER_ID = "USER_ID"
    EMAIL = "EMAIL"
    MOBILE_NO = "MOBILE_NO"
    PAN = "PAN"


class AMLConstants:
    IN_REVIEW = "IN_REVIEW"


class NameMatchStatus:
    IN_REVIEW = "IN_REVIEW"


class SortConstant:
    FMPP = "fmpps"
    VALUE_OF_INVESTMENT = "value_of_investment"
    CREATED_DATE = "created_date"
    BALANCE = "balance"
    DESC = "desc"


class SummaryType:
    CMC = "CMC"


class DashboardInvestorFilter:
    PROFILE_NOT_COMPLETED = "PROFILE_NOT_COMPLETED"
    INACTIVE_WITH_ZERO_AUM = "INACTIVE_WITH_ZERO_AUM"


class PMIConstants:
    NACH = "NACH"


class DummyUserConstant:
    DUMMY_USER_ID = settings.DUMMY_USER_ID


class TransactionBlockForUser:
    user_pk_list = [
        782405,
        1054975,
        2982945,
        6745866,
        8110318,
        14906656,
        14905035,
        15351488,
        15363924,
    ]

    withdrawal_block = [
        782405,
        1054975,
        2982945,
        6745866,
        8110318,
        14906656,
        14905035,
        15351488,
        15363924,
    ]


class ReferralDetails:
    NO_REFERRAL_TEXT = "🚀 No referrals yet! Start sharing & earn ₹100 cash reward every time a friend lends!"
    REWARD_EARNED_TEXT = "You have earned cashback"
    REWARD_NOT_EARNED_TEXT = "Minimum lending not done yet"
    SEND_REMINDER = "SEND_REMINDER"
    INELIGIBLE_TEXT = "First lending amount was below ₹1000"


class CampaignType:
    REFERRAL = "referral"


class RewardStatus:
    COMPLETED = "COMPLETED"
    PENDING = "PENDING"
    INELIGIBLE = "INELIGIBLE"


class RMLenderFilterTypes:
    ASSIGNED_RM = "assigned_rm"
    UNASSIGNED_RM = "unassigned_rm"


class TransactionConstants:
    REJECTION_REASON = {"REFUND_OTL": "Loans were not available"}


class OfflinePaymentStatus:
    IN_REVIEW = "IN-REVIEW"
    PROCESSING = "PROCESSING"


class CashfreeConstant:
    ACTION = {
        "BANK_ACCOUNT": "BANK ACCOUNT",
    }


class InvoiceType:
    INDIVIDUAL = "INDIVIDUAL"


class RedisConstants:
    ML_FILTER_AND_SORT = "MLFilterAndSort"


class OTLInvestment:
    OTL_LOAN_TENURE_TYPE = " Month(s)"


class SchemeInfoListStatus:
    ALL = "ALL"
    SUCCESS = "SUCCESS"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class CPPaymentTypes:
    NACH = "NACH"


class CancellationExpiryBuffer:
    INTERVAL_ONE_DAY = "1 day"


class ProductFormConstants:
    PRODUCT_FORM = "PRODUCT_FORM"
    FORM = "FORM"


class STLSchemePriorityOrderValues:
    ALLOW_COMPLETE_SCHEME_CREATION = 0


class FMITransactionStatus:
    FAILED = "F"
    IN_PROGRESS = "IP"


class FMISystem:
    MIN_AMOUNT = 1


class UPIMandateStatus:
    PAUSED = "PAUSED"
    CANCELLED = "CANCELLED"
    REVOKED = "REVOKED"


class ExpiredTransaction:
    FALSE = "FALSE"


class HOFMember:
    REFERENCE_TYPE = "FAMILY_MEMBER"


class MaskingConstants:
    EMAIL = {
        'masking_char': '*',
        'masking_format': 'MASK_BETWEEN'
    }
    PAN = {
        'masking_char': 'X',
        'masking_format': 'MASK_LEFT'
    }
    MOBILE = {
        'masking_char': 'X',
        'masking_format': 'MASK_LEFT'
    }
    AADHAR = {
        'masking_char': 'X',
        'masking_format': 'MASK_LEFT'
    }
    MASK_BETWEEN = 'MASK_BETWEEN'
    MASK_LEFT = 'MASK_LEFT'
    MASK_RIGHT = 'MASK_RIGHT'
    MASK_SOURCE_LIST = settings.MASK_SOURCE_LIST


class BankVerificationStatus:
    APPROVED = 'APPROVED'
    PENDING = 'PENDING'
    REJECTED = 'REJECTED'