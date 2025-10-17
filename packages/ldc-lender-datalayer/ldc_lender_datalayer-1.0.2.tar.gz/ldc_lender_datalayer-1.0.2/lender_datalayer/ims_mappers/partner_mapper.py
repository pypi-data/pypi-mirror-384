import logging

from ..base_datalayer import BaseDataLayer
from ..common.constants import UserGroup

logger = logging.getLogger("normal")


class PartnerMapper(BaseDataLayer):
    def __init__(self, partner_source=None, db_alias="default"):
        super().__init__(db_alias)
        self.partner_source = partner_source

    def get_entity_name(self):
        return "IMS_PARTNER"

    def get_investors(self):
        sql = """select lc2.user_id  from  lendenapp_customuser 
         lc2 where lc2.source =%(partner_source)s """
        params = {"partner_source": self.partner_source}
        return self.sql_execute_fetch_all(sql, params, to_dict=True)

    @staticmethod
    def get_partner_brokerage_details(user_pk, start_date, end_date):
        sql = """
                SELECT 
                    lc.investor_id, 
                    lc.scheme_reference_number, 
                    lc.scheme_amount, lc.tenure,
                    lc.auto_renew, lc.scheme_type, 
                    lc.created_date, 
                    lb.brokerage_percentage, 
                    lc3.user_id, 
                    lc3.first_name 
                FROM 
                    lendenapp_cpfmpptransaction lc 
                INNER JOIN 
                    lendenapp_cpaumbrokerage lc2 ON lc2.investor_parent_id = 
                    lc.investor_parent_id 
                    AND lc2.from_date::date = lc.created_date::date
                INNER JOIN 
                    lendenapp_brokeragerule lb ON lc2.brokerage_rule_id = lb.id
                INNER JOIN 
                    lendenapp_customuser lc3 ON lc.investor_id=lc3.id
                WHERE 
                    lc.investor_parent_id=%s AND 
                    lc.created_date BETWEEN %s AND %s
            """
        logger.info(f"get_partner_investment_details sql_query-->{sql}")
        logger.info(
            f"get_partner_investment_details sql_parameter-->"
            f"{user_pk}-{start_date}-{end_date}"
        )
        scheme_details = PartnerMapper().sql_execute_fetch_all(
            sql, [user_pk, start_date, end_date], to_dict=True
        )
        return scheme_details

    @staticmethod
    def get_partner_brokerage_summary(partner_pk, start_date, end_date):
        sql = """
            SELECT 
                CONCAT('FMPP_', lc.tenure) AS SCHEME_NAME, 
                lc.tenure AS TENURE_IN_MONTHS, 
                lc.scheme_type AS SCHEME_TYPE, 
                SUM(scheme_amount) AS SCHEME_AMOUNT,
                SUM(brokerage_amount) AS SCHEME_BROKERAGE, 
                lb.brokerage_percentage AS BROKERAGE_PERCENTAGE 
            FROM 
                lendenapp_cpfmpptransaction lc
            INNER JOIN lendenapp_cpaumbrokerage lc2
                ON lc2.investor_parent_id = lc.investor_parent_id
                AND lc2.from_date::date = lc.created_date::date
            INNER JOIN lendenapp_brokeragerule lb
                ON lc2.brokerage_rule_id = lb.id
            WHERE 
                lc.investor_parent_id=%(parent_id)s AND lc.created_date::date 
                BETWEEN %(start_date)s AND %(end_date)s 
            GROUP BY 
                lc.tenure, lc.scheme_type, lb.brokerage_percentage
        """
        params = {
            "parent_id": partner_pk,
            "start_date": start_date,
            "end_date": end_date,
        }
        return PartnerMapper().sql_execute_fetch_all(sql, params=params, to_dict=True)

    @staticmethod
    def previous_month_aum(partner_pk, start_date, end_date):
        sql = """
            SELECT 
            sum(fmpp_investment) as aum
            FROM
            lendenapp_cpaumbrokerage lc
            WHERE
                lc.investor_parent_id=%(parent_id)s and 
                lc.from_date::date 
                BETWEEN %(start_date)s AND %(end_date)s 
        """
        params = {
            "parent_id": partner_pk,
            "start_date": start_date,
            "end_date": end_date,
        }
        return PartnerMapper().sql_execute_fetch_one(sql, params=params, to_dict=True)

    def get_user_token(self, email, mobile_number, pan, investor_id, selected_column):
        query = """
            SELECT {selected_column}
            FROM lendenapp_customuser lc
            LEFT JOIN authtoken_token at ON lc.id = at.user_id
            left join lendenapp_user_source_group lusg 
            on lc.id = lusg.user_id
            left join lendenapp_source ls on ls.id = lusg.source_id
            WHERE ls.source_name = %(source)s
            AND lusg.group_id = %(group_id)s
        """.format(
            selected_column=selected_column
        )

        params = {
            "group_id": UserGroup.LENDER,
            "source": self.partner_source,
            "encoded_email": email,
            "encoded_mobile": mobile_number,
            "encoded_pan": pan,
            "user_id": investor_id,
        }

        conditions = []

        if investor_id:
            conditions.append("lc.user_id = %(user_id)s")
        if mobile_number:
            conditions.append("lc.encoded_mobile = %(encoded_mobile)s")
        if pan:
            conditions.append("lc.encoded_pan = %(encoded_pan)s")
        if email:
            conditions.append("lc.encoded_email = %(encoded_email)s")

        if conditions:
            query += " AND (" + " AND ".join(conditions) + ")"

        result = self.sql_execute_fetch_one(query, params, to_dict=True)
        return result
