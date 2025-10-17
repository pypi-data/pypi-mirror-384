"""
Data models for Excel row representations.

This module contains dataclasses that represent the structure of Excel rows
for invoice header and line item data.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from datetime import date


@dataclass
class InvoiceHeaderRow:
    """
    Data model representing a single row in the 'Fejléc adatok' (Header Data) sheet.
    
    Contains all invoice-level information including seller/buyer details,
    financial totals, and metadata.
    """
    
    # Basic invoice information
    invoice_number: Optional[str] = None  # Számla sorszáma
    invoice_issue_date: Optional[date] = None  # Számla kelte
    fulfillment_date: Optional[date] = None  # Teljesítés dátuma
    invoice_currency: Optional[str] = None  # Számla pénzneme
    exchange_rate: Optional[Decimal] = None  # Alkalmazott árfolyam
    
    # Seller information
    seller_tax_number_main: Optional[str] = None  # Eladó adószáma (törzsszám)
    seller_tax_number_vat: Optional[str] = None  # Eladó adószáma (ÁFA-kód)
    seller_tax_number_county: Optional[str] = None  # Eladó adószáma (megyekód)
    seller_name: Optional[str] = None  # Eladó neve
    seller_country_code: Optional[str] = None  # Eladó országkódja
    seller_postal_code: Optional[str] = None  # Eladó irányítószáma
    seller_city: Optional[str] = None  # Eladó települése
    seller_address_detail: Optional[str] = None  # Eladó többi címadata
    
    # Buyer information
    buyer_tax_number_main: Optional[str] = None  # Vevő adószáma (törzsszám)
    buyer_tax_number_vat: Optional[str] = None  # Vevő adószáma (ÁFA-kód)
    buyer_tax_number_county: Optional[str] = None  # Vevő adószáma (megyekód)
    buyer_name: Optional[str] = None  # Vevő neve
    buyer_vat_status: Optional[str] = None  # Vevő státusza
    buyer_community_vat_number: Optional[str] = None  # Vevő közösségi adószáma
    buyer_third_country_tax_number: Optional[str] = None  # Vevő harmadik országbeli adószáma
    buyer_country_code: Optional[str] = None  # Vevő országkódja
    buyer_postal_code: Optional[str] = None  # Vevő irányítószáma
    buyer_city: Optional[str] = None  # Vevő települése
    buyer_address_detail: Optional[str] = None  # Vevő többi címadata
    
    # Modification information
    original_invoice_number: Optional[str] = None  # Eredeti számla száma
    modification_date: Optional[date] = None  # Módosító okirat kelte
    modification_index: Optional[int] = None  # Módosítás sorszáma
    
    # Financial amounts
    net_amount_original: Optional[Decimal] = None  # Számla nettó összege (a számla pénznemében)
    net_amount_huf: Optional[Decimal] = None  # Számla nettó összege (forintban)
    vat_amount_original: Optional[Decimal] = None  # Számla ÁFA összege (a számla pénznemében)
    vat_amount_huf: Optional[Decimal] = None  # Számla ÁFA összege (forintban)
    gross_amount_original: Optional[Decimal] = None  # Számla bruttó összege (a számla pénznemében)
    gross_amount_huf: Optional[Decimal] = None  # Számla bruttó összege (forintban)
    
    # Payment information
    payment_due_date: Optional[date] = None  # Fizetési határidő
    payment_method: Optional[str] = None  # Fizetési mód
    
    # Special flags and indicators
    small_business_indicator: Optional[bool] = None  # Kisadózó jelölése
    cash_accounting_indicator: Optional[bool] = None  # Pénzforgalmi elszámolás jelölése
    invoice_category: Optional[str] = None  # Számla típusa
    completeness_indicator: Optional[bool] = None  # Az adatszolgáltatás maga a számla


@dataclass
class InvoiceLineRow:
    """
    Data model representing a single row in the 'Tétel adatok' (Line Item Data) sheet.
    
    Contains line-level information for products/services on an invoice.
    """
    
    # Reference information
    invoice_number: Optional[str] = None  # Számla sorszáma
    buyer_tax_number_main: Optional[str] = None  # Vevő adószáma (törzsszám)
    buyer_name: Optional[str] = None  # Vevő neve
    seller_tax_number_main: Optional[str] = None  # Eladó adószáma (törzsszám)
    seller_name: Optional[str] = None  # Eladó neve
    
    # Line item identification
    line_number: Optional[int] = None  # Tétel sorszáma
    modified_line_number: Optional[int] = None  # Módosítással érintett tétel sorszáma
    line_modification_type: Optional[str] = None  # Módosítás jellege
    
    # Product/service information
    description: Optional[str] = None  # Megnevezés
    quantity: Optional[Decimal] = None  # Mennyiség
    unit_of_measure: Optional[str] = None  # Mennyiségi egység
    unit_price: Optional[Decimal] = None  # Egységár
    
    # Financial amounts
    net_amount_original: Optional[Decimal] = None  # Nettó összeg (a számla pénznemében)
    net_amount_huf: Optional[Decimal] = None  # Nettó összeg (forintban)
    
    # VAT information
    vat_rate: Optional[Decimal] = None  # Adó mértéke
    vat_exemption_indicator: Optional[bool] = None  # Áfamentesség jelölés
    vat_exemption_case: Optional[str] = None  # Áfamentesség esete
    vat_exemption_reason: Optional[str] = None  # Áfamentesség leírása
    
    # Out of scope VAT
    out_of_scope_indicator: Optional[bool] = None  # ÁFA törvény hatályán kívüli jelölés
    out_of_scope_case: Optional[str] = None  # ÁFA törvény hatályon kívüliségének esete
    out_of_scope_reason: Optional[str] = None  # ÁFA törvény hatályon kívüliségének leírása
    
    # Tax deviation
    tax_base_deviation_case: Optional[str] = None  # Adóalap és felszámított adó eltérésének esete
    different_tax_rate_content: Optional[str] = None  # Eltérő adóalap és felszámított adó adómérték, adótartalom
    
    # Reverse charge and margin scheme
    domestic_reverse_charge_indicator: Optional[bool] = None  # Belföldi fordított adózás jelölés
    margin_scheme_with_vat: Optional[bool] = None  # Áthárított adót tartalmazó különbözet szerinti adózás
    margin_scheme_without_vat: Optional[bool] = None  # Áthárított adót nem tartalmazó különbözet szerinti adózás
    margin_scheme_indicator: Optional[str] = None  # Különbözet szerinti adózás
    
    # VAT amounts
    vat_amount_original: Optional[Decimal] = None  # ÁFA összeg (a számla pénznemében)
    vat_amount_huf: Optional[Decimal] = None  # ÁFA összeg (forintban)
    gross_amount_original: Optional[Decimal] = None  # Bruttó összeg (a számla pénznemében)
    gross_amount_huf: Optional[Decimal] = None  # Bruttó összeg (forintban)
    
    # Additional information
    vat_content: Optional[str] = None  # ÁFA tartalom
    advance_payment_indicator: Optional[bool] = None  # Előleg jelleg jelölése
    line_exchange_rate: Optional[Decimal] = None  # Tétel árfolyam
    line_fulfillment_date: Optional[date] = None  # Tétel teljesítés dátuma
    no_vat_charge_indicator: Optional[bool] = None  # Nincs felszámított áfa az áfa törvény 17. § alapján