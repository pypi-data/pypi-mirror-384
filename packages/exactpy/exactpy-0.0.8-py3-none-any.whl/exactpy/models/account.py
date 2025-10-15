from datetime import datetime
from typing import List

from exactpy.models import ExactOnlineBaseModel
from exactpy.models.bank_account import BankAccount


class Account(ExactOnlineBaseModel):
    id: str
    accountant: str | None = None
    account_manager: str | None = None
    account_manager_full_name: str | None = None
    account_manager_hid: int
    activity_sector: str | None = None
    activity_sub_sector: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    address_line3: str | None = None
    automatic_process_proposed_entry: bytes | None = None
    bank_accounts: List[BankAccount] = []
    blocked: bool = False
    brin: str | None = None
    bsn: str | None = None
    business_type: str | None = None
    can_drop_ship: bool = False
    chamber_of_commerce: str | None = None
    city: str | None = None
    classification: str | None = None
    classification1: str | None = None
    classification2: str | None = None
    classification3: str | None = None
    classification4: str | None = None
    classification5: str | None = None
    classification6: str | None = None
    classification7: str | None = None
    classification8: str | None = None
    classification_description: str | None = None
    code: str | None = None
    code_at_supplier: str | None = None
    company_size: str | None = None
    consolidation_scenario: bytes | None = None
    controlled_date: datetime | None = None
    cost_center: str | None = None
    cost_center_description: str | None = None
    cost_paid: bytes | None = None
    country: str | None = None
    country_name: str | None = None
    created: datetime | None = None
    creator: str | None = None
    creator_full_name: str | None = None
    credit_line_purchase: float | None = None
    credit_line_sales: float | None = None
    currency: str | None = None
    customer_since: datetime | None = None
    custom_field: str | None = None
    datev_creditor_code: str | None = None
    datev_debtor_code: str | None = None
    delivery_advice: bytes | None = None
    discount_purchase: float | None = None
    discount_sales: float | None = None
    division: int | None = None
    document: str | None = None
    duns_number: str | None = None
    email: str | None = None
    enable_sales_payment_link: bool = False
    end_date: datetime | None = None
    eori_number: str | None = None
    established_date: datetime | None = None
    fax: str | None = None
    gl_account_purchase: str | None = None
    gl_account_sales: str | None = None
    glap: str | None = None
    glar: str | None = None
    gln_number: str | None = None
    has_withholding_tax_sales: bool = False
    ignore_datev_warning_message: bool = False
    incoterm_address_purchase: str | None = None
    incoterm_address_sales: str | None = None
    incoterm_code_purchase: str | None = None
    incoterm_code_sales: str | None = None
    incoterm_version_purchase: int | None = None
    incoterm_version_sales: int | None = None
    intra_stat_area: str | None = None
    intra_stat_delivery_term: str | None = None
    intra_stat_system: str | None = None
    intra_stat_transaction_a: str | None = None
    intra_stat_transaction_b: str | None = None
    intra_stat_transport_method: str | None = None
    invoice_account: str | None = None
    invoice_account_code: str | None = None
    invoice_account_name: str | None = None
    invoice_attachment_type: int
    invoicing_method: int
    is_accountant: bytes | None = None
    is_agency: bytes | None = None
    is_anonymised: bytes | None = None
    is_bank: bool = False
    is_competitor: bytes | None = None
    is_extra_duty: bool = False
    is_mailing: bytes | None = None
    is_member: bool = False
    is_pilot: bool = False
    is_purchase: bool = False
    is_reseller: bool = False
    is_sales: bool = False
    is_supplier: bool = False
    language: str = False
    language_description: str = False
    latitude: float = False
    lead_purpose: str = False
    lead_source: str = False
    logo: bytes | None = None
    logo_file_name: str | None = None
    logo_thumbnail_url: str | None = None
    logo_url: str | None = None
    longitude: float | None = None
    main_contact: str | None = None
    modified: datetime | None = None
    modifier: str | None = None
    modifier_full_name: str | None = None
    name: str | None = None
    oin_number: str | None = None
    parent: str | None = None
    pay_as_you_earn: str | None = None
    payment_condition_purchase: str | None = None
    payment_condition_purchase_description: str | None = None
    payment_condition_sales: str | None = None
    payment_condition_sales_description: str | None = None
    peppol_identifier: str | None = None
    peppol_identifier_type: int
    phone: str | None = None
    phone_extension: str | None = None
    postcode: str | None = None
    price_list: str | None = None
    purchase_currency: str | None = None
    purchase_currency_description: str | None = None
    purchase_lead_days: int
    purchase_vat_code: str | None = None
    purchase_vat_code_description: str | None = None
    recepient_of_commissions: bool = False
    remarks: str | None = None
    reseller: str | None = None
    reseller_code: str | None = None
    reseller_name: str | None = None
    rsin: str | None = None
    sales_currency: str | None = None
    sales_currency_description: str | None = None
    sales_tax_schedule: str | None = None
    sales_tax_schedule_code: str | None = None
    sales_tax_schedule_description: str | None = None
    sales_vat_code: str | None = None
    sales_vat_code_description: str | None = None
    search_code: str | None = None
    security_level: int
    separate_inv_per_subscription: bytes | None = None
    shipping_lead_days: int
    shipping_method: str | None = None
    show_remark_for_sales: bool = False
    start_date: datetime | None = None
    state: str | None = None
    state_name: str | None = None
    status: str | None = None
    status_since: datetime | None = None
    trade_name: str | None = None
    type: str | None = None
    unique_taxpayer_reference: str | None = None
    vat_liability: str | None = None
    vat_number: str | None = None
    website: str | None = None

    @staticmethod
    def all():
        return [
            Account(
                id="1",
                account_manager_hid=0,
                invoice_attachment_type=0,
                invoicing_method=0,
                peppol_identifier_type=0,
                purchase_lead_days=0,
                security_level=0,
                shipping_lead_days=0,
            ),
            Account(
                id="2",
                account_manager_hid=0,
                invoice_attachment_type=0,
                invoicing_method=0,
                peppol_identifier_type=0,
                purchase_lead_days=0,
                security_level=0,
                shipping_lead_days=0,
            ),
        ]
