from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Optional

from nav_online_szamla.models.invoice_base import (
    AddressType,
    InvoiceAppearanceType,
    InvoiceCategoryType,
    PaymentMethodType,
    SimpleAddressType,
    TaxNumberType,
)

__NAMESPACE__ = "http://schemas.nav.gov.hu/OSA/3.0/data"


@dataclass
class AdditionalDataType:
    """
    További adat leírására szolgáló típus Type for additional data description.

    :ivar data_name: Az adatmező egyedi azonosítója Unique
        identification of the data field
    :ivar data_description: Az adatmező tartalmának szöveges leírása
        Description of content of the data field
    :ivar data_value: Az adat értéke Value of the data
    """

    data_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "dataName",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "min_length": 1,
            "max_length": 255,
            "pattern": r"[A-Z][0-9]{5}[_][_A-Z0-9]{1,249}",
        },
    )
    data_description: Optional[str] = field(
        default=None,
        metadata={
            "name": "dataDescription",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "min_length": 1,
            "max_length": 255,
            "pattern": r".*[^\s].*",
        },
    )
    data_value: Optional[str] = field(
        default=None,
        metadata={
            "name": "dataValue",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "min_length": 1,
            "max_length": 512,
            "pattern": r".*[^\s].*",
        },
    )


@dataclass
class AdvancePaymentDataType:
    """
    Előlegfizetéshez kapcsolódó adatok Advance payment related data.

    :ivar advance_original_invoice: Az előlegszámlának a sorszáma,
        amelyben az előlegfizetés történt Invoice number containing the
        advance payment
    :ivar advance_payment_date: Az előleg fizetésének dátuma Payment
        date of the advance
    :ivar advance_exchange_rate: Az előlegfizetés során alkalmazott
        árfolyam Applied exchange rate of the advance
    """

    advance_original_invoice: Optional[str] = field(
        default=None,
        metadata={
            "name": "advanceOriginalInvoice",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "min_length": 1,
            "max_length": 50,
            "pattern": r".*[^\s].*",
        },
    )
    advance_payment_date: Optional[str] = field(
        default=None,
        metadata={
            "name": "advancePaymentDate",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "min_inclusive": "2010-01-01",
            "pattern": r"\d{4}-\d{2}-\d{2}",
        },
    )
    advance_exchange_rate: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "advanceExchangeRate",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "min_exclusive": Decimal("0"),
            "total_digits": 14,
            "fraction_digits": 6,
        },
    )


@dataclass
class AggregateInvoiceLineDataType:
    """
    A gyűjtő számlára vonatkozó speciális adatokat tartalmazó típus Field type
    including aggregate invoice special data.

    :ivar line_exchange_rate: A tételhez tartozó árfolyam, 1 (egy)
        egységre vonatkoztatva. Csak külföldi pénznemben kiállított
        gyűjtő számla esetén kitöltendő The exchange rate applied to the
        item, pertaining to 1 (one) unit. This should be filled in only
        if an aggregate invoice in foreign currency is issued
    :ivar line_delivery_date: Gyűjtőszámla esetén az adott tétel
        teljesítési dátuma Delivery date of the given item in the case
        of an aggregate invoice
    """

    line_exchange_rate: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "lineExchangeRate",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "min_exclusive": Decimal("0"),
            "total_digits": 14,
            "fraction_digits": 6,
        },
    )
    line_delivery_date: Optional[str] = field(
        default=None,
        metadata={
            "name": "lineDeliveryDate",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "min_inclusive": "2010-01-01",
            "pattern": r"\d{4}-\d{2}-\d{2}",
        },
    )


@dataclass
class AircraftType:
    """
    Légi közlekedési eszköz Aircraft.

    :ivar take_off_weight: Felszállási tömeg kilogrammban Take-off
        weight in kilogram
    :ivar air_cargo: Értéke true ha a jármű az ÁFA tv. 259.§ 25. c)
        szerinti kivétel alá tartozik The value is true if the means of
        transport is exempt from VAT as per section 259 [25] (c)
    :ivar operation_hours: Repült órák száma Number of aviated hours
    """

    take_off_weight: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "takeOffWeight",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "total_digits": 22,
            "fraction_digits": 10,
        },
    )
    air_cargo: Optional[bool] = field(
        default=None,
        metadata={
            "name": "airCargo",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
        },
    )
    operation_hours: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "operationHours",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "total_digits": 22,
            "fraction_digits": 10,
        },
    )


@dataclass
class ContractNumbersType:
    """
    Szerződésszámok Contract numbers.

    :ivar contract_number: Szerződésszám Contract number
    """

    contract_number: list[str] = field(
        default_factory=list,
        metadata={
            "name": "contractNumber",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "min_occurs": 1,
            "min_length": 1,
            "max_length": 100,
            "pattern": r".*[^\s].*",
        },
    )


@dataclass
class CostCentersType:
    """
    Költséghelyek Cost centers.

    :ivar cost_center: Költséghely Cost center
    """

    cost_center: list[str] = field(
        default_factory=list,
        metadata={
            "name": "costCenter",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "min_occurs": 1,
            "min_length": 1,
            "max_length": 100,
            "pattern": r".*[^\s].*",
        },
    )


@dataclass
class CustomerCompanyCodesType:
    """
    A vevő vállalati kódjai Company codes of the customer.

    :ivar customer_company_code: A vevő vállalati kódja Company code of
        the customer
    """

    customer_company_code: list[str] = field(
        default_factory=list,
        metadata={
            "name": "customerCompanyCode",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "min_occurs": 1,
            "min_length": 1,
            "max_length": 100,
            "pattern": r".*[^\s].*",
        },
    )


class CustomerVatStatusType(Enum):
    """
    Vevő ÁFA szerinti státusz típusa Customers status type by VAT.

    :cvar DOMESTIC: Belföldi ÁFA alany Domestic VAT subject
    :cvar OTHER: Egyéb (belföldi nem ÁFA alany, nem természetes személy,
        külföldi ÁFA alany és külföldi nem ÁFA alany, nem természetes
        személy) Other (domestic non-VAT subject, non-natural person,
        foreign VAT subject and foreign non-VAT subject, non-natural
        person)
    :cvar PRIVATE_PERSON: Nem ÁFA alany (belföldi vagy külföldi)
        természetes személy Non-VAT subject (domestic or foreign)
        natural person
    """

    DOMESTIC = "DOMESTIC"
    OTHER = "OTHER"
    PRIVATE_PERSON = "PRIVATE_PERSON"


@dataclass
class DealerCodesType:
    """
    Beszállító kódok Dealer codes.

    :ivar dealer_code: Beszállító kód Dealer code
    """

    dealer_code: list[str] = field(
        default_factory=list,
        metadata={
            "name": "dealerCode",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "min_occurs": 1,
            "min_length": 1,
            "max_length": 100,
            "pattern": r".*[^\s].*",
        },
    )


@dataclass
class DeliveryNotesType:
    """
    Szállítólevél számok Delivery notes.

    :ivar delivery_note: Szállítólevél szám Delivery note
    """

    delivery_note: list[str] = field(
        default_factory=list,
        metadata={
            "name": "deliveryNote",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "min_occurs": 1,
            "min_length": 1,
            "max_length": 100,
            "pattern": r".*[^\s].*",
        },
    )


@dataclass
class DetailedReasonType:
    """
    Mentesség, kivétel részletes indokolása Detailed justification of exemption.

    :ivar case: Az eset leírása kóddal Case notation with code
    :ivar reason: Az eset leírása szöveggel Case notation with text
    """

    case: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "min_length": 1,
            "max_length": 50,
            "pattern": r".*[^\s].*",
        },
    )
    reason: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "min_length": 1,
            "max_length": 200,
            "pattern": r".*[^\s].*",
        },
    )


@dataclass
class DiscountDataType:
    """
    Árengedmény adatok Discount data.

    :ivar discount_description: Az árengedmény leírása Description of
        the discount
    :ivar discount_value: Tételhez tartozó árengedmény összege a számla
        pénznemében, ha az egységár nem tartalmazza Total amount of
        discount per item expressed in the currency of the invoice if
        not included in the unit price
    :ivar discount_rate: Tételhez tartozó árengedmény aránya, ha az
        egységár nem tartalmazza Rate of discount per item expressed in
        the currency of the invoice if not included in the unit price
    """

    discount_description: Optional[str] = field(
        default=None,
        metadata={
            "name": "discountDescription",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "min_length": 1,
            "max_length": 255,
            "pattern": r".*[^\s].*",
        },
    )
    discount_value: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "discountValue",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "total_digits": 18,
            "fraction_digits": 2,
        },
    )
    discount_rate: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "discountRate",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "min_inclusive": Decimal("0"),
            "max_inclusive": Decimal("1"),
            "total_digits": 5,
            "fraction_digits": 4,
        },
    )


@dataclass
class EkaerIdsType:
    """
    EKÁER azonosító(k) EKAER ID-s.

    :ivar ekaer_id: EKÁER azonosító EKAER numbers; EKAER stands for
        Electronic Trade and Transport Control System
    """

    ekaer_id: list[str] = field(
        default_factory=list,
        metadata={
            "name": "ekaerId",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "min_occurs": 1,
            "min_length": 1,
            "max_length": 15,
            "pattern": r"[E]{1}[0-9]{6}[0-9A-F]{8}",
        },
    )


@dataclass
class GeneralLedgerAccountNumbersType:
    """
    Főkönyvi számlaszámok General ledger account numbers.

    :ivar general_ledger_account_number: Főkönyvi számlaszám General
        ledger account number
    """

    general_ledger_account_number: list[str] = field(
        default_factory=list,
        metadata={
            "name": "generalLedgerAccountNumber",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "min_occurs": 1,
            "min_length": 1,
            "max_length": 100,
            "pattern": r".*[^\s].*",
        },
    )


@dataclass
class GlnNumbersType:
    """
    Globális helyazonosító számok Global location numbers.

    :ivar gln_number: Globális helyazonosító szám Global location number
    """

    gln_number: list[str] = field(
        default_factory=list,
        metadata={
            "name": "glnNumber",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "min_occurs": 1,
            "min_length": 1,
            "max_length": 100,
            "pattern": r".*[^\s].*",
        },
    )


@dataclass
class InvoiceReferenceType:
    """
    A módosítás vagy érvénytelenítés hivatkozási adatai Modification or
    cancellation reference data.

    :ivar original_invoice_number: Az eredeti számla sorszáma, melyre a
        módosítás vonatkozik  - ÁFA tv. 170. § (1) c) Sequence number of
        the original invoice, on which the modification occurs - section
        170 (1) c) of the VAT law
    :ivar modify_without_master: Annak jelzése, hogy a módosítás olyan
        alapszámlára hivatkozik, amelyről nem történt és nem is fog
        történni adatszolgáltatás Indicates whether the modification
        references to an original invoice which is not and will not be
        exchanged
    :ivar modification_index: A számlára vonatkozó módosító okirat
        egyedi sorszáma The unique sequence number referring to the
        original invoice
    """

    original_invoice_number: Optional[str] = field(
        default=None,
        metadata={
            "name": "originalInvoiceNumber",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "min_length": 1,
            "max_length": 50,
            "pattern": r".*[^\s].*",
        },
    )
    modify_without_master: Optional[bool] = field(
        default=None,
        metadata={
            "name": "modifyWithoutMaster",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
        },
    )
    modification_index: Optional[int] = field(
        default=None,
        metadata={
            "name": "modificationIndex",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "min_inclusive": 1,
        },
    )


@dataclass
class ItemNumbersType:
    """
    Cikkszámok Item numbers.

    :ivar item_number: Cikkszám Item number
    """

    item_number: list[str] = field(
        default_factory=list,
        metadata={
            "name": "itemNumber",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "min_occurs": 1,
            "min_length": 1,
            "max_length": 100,
            "pattern": r".*[^\s].*",
        },
    )


@dataclass
class LineGrossAmountDataType:
    """
    Tétel bruttó adatok Line gross data.

    :ivar line_gross_amount_normal: Tétel bruttó értéke a számla
        pénznemében. ÁFA tartalmú különbözeti adózás esetén az
        ellenérték. Gross amount of the item expressed in the currency
        of the invoice. In case of margin scheme taxation containing
        VAT, the amount of consideration expressed in the currency of
        the invoice.
    :ivar line_gross_amount_normal_huf: Tétel bruttó értéke forintban
        Gross amount of the item expressed in HUF
    """

    line_gross_amount_normal: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "lineGrossAmountNormal",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "total_digits": 18,
            "fraction_digits": 2,
        },
    )
    line_gross_amount_normal_huf: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "lineGrossAmountNormalHUF",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "total_digits": 18,
            "fraction_digits": 2,
        },
    )


class LineNatureIndicatorType(Enum):
    """
    Adott tételsor termékértékesítés vagy szolgáltatás nyújtás jellegének jelzése
    Indication of the nature of the supply of goods or services on a given line.

    :cvar PRODUCT: Termékértékesítés Supply of goods
    :cvar SERVICE: Szolgáltatás nyújtás Supply of services
    :cvar OTHER: Egyéb, nem besorolható Other, non-qualifiable
    """

    PRODUCT = "PRODUCT"
    SERVICE = "SERVICE"
    OTHER = "OTHER"


@dataclass
class LineNetAmountDataType:
    """
    Tétel nettó adatok Line net data.

    :ivar line_net_amount: Tétel nettó összege a számla pénznemében. ÁFA
        tartalmú különbözeti adózás esetén az ellenérték áfa összegével
        csökkentett értéke a számla pénznemében. Net amount of the item
        expressed in the currency of the invoice. In case of margin
        scheme taxation containing VAT, the amount of consideration
        reduced with the amount of VAT, expressed in the currency of the
        invoice.
    :ivar line_net_amount_huf: Tétel nettó összege forintban. ÁFA
        tartalmú különbözeti adózás esetén az ellenérték áfa összegével
        csökkentett értéke forintban. Net amount of the item expressed
        in HUF. Net amount of the item expressed in the currency of the
        invoice. In case of margin scheme taxation containing VAT, the
        amount of consideration reduced with the amount of VAT,
        expressed in HUF.
    """

    line_net_amount: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "lineNetAmount",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "total_digits": 18,
            "fraction_digits": 2,
        },
    )
    line_net_amount_huf: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "lineNetAmountHUF",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "total_digits": 18,
            "fraction_digits": 2,
        },
    )


class LineOperationType(Enum):
    """
    A számlatétel módosítás típusa Invoice line modification type.
    """

    CREATE = "CREATE"
    MODIFY = "MODIFY"


@dataclass
class LineVatDataType:
    """
    Tétel ÁFA adatok Line VAT data.

    :ivar line_vat_amount: Tétel ÁFA összege a számla pénznemében VAT
        amount of the item expressed in the currency of the invoice
    :ivar line_vat_amount_huf: Tétel ÁFA összege forintban VAT amount of
        the item expressed in HUF
    """

    line_vat_amount: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "lineVatAmount",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "total_digits": 18,
            "fraction_digits": 2,
        },
    )
    line_vat_amount_huf: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "lineVatAmountHUF",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "total_digits": 18,
            "fraction_digits": 2,
        },
    )


class MarginSchemeType(Enum):
    """
    Különbözet szerinti szabályozás típus Field type for inputting margin-scheme
    taxation.

    :cvar TRAVEL_AGENCY: Utazási irodák Travel agencies
    :cvar SECOND_HAND: Használt cikkek Second-hand goods
    :cvar ARTWORK: Műalkotások Works of art
    :cvar ANTIQUES: Gyűjteménydarabok és régiségek Collector’s items and
        antiques
    """

    TRAVEL_AGENCY = "TRAVEL_AGENCY"
    SECOND_HAND = "SECOND_HAND"
    ARTWORK = "ARTWORK"
    ANTIQUES = "ANTIQUES"


@dataclass
class MaterialNumbersType:
    """
    Anyagszámok Material numbers.

    :ivar material_number: Anyagszám Material number
    """

    material_number: list[str] = field(
        default_factory=list,
        metadata={
            "name": "materialNumber",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "min_occurs": 1,
            "min_length": 1,
            "max_length": 100,
            "pattern": r".*[^\s].*",
        },
    )


@dataclass
class OrderNumbersType:
    """
    Megrendelésszámok Order numbers.

    :ivar order_number: Megrendelésszám Order number
    """

    order_number: list[str] = field(
        default_factory=list,
        metadata={
            "name": "orderNumber",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "min_occurs": 1,
            "min_length": 1,
            "max_length": 100,
            "pattern": r".*[^\s].*",
        },
    )


class ProductCodeCategoryType(Enum):
    """
    A termékkód fajtájának jelölésére szolgáló típus The type used to mark the kind
    of product code.

    :cvar VTSZ: Vámtarifa szám VTSZ Customs tariff number CTN
    :cvar SZJ: Szolgáltatás jegyzék szám SZJ Business service list
        number BSL
    :cvar KN: KN kód (Kombinált Nómenklatúra, 2658/87/EGK rendelet I.
        melléklete) CN code (Combined Nomenclature, 2658/87/ECC Annex I)
    :cvar AHK: A Jövedéki törvény (2016. évi LXVIII. tv) szerinti e-TKO
        adminisztratív hivatkozási kódja AHK Administrative reference
        code of e-TKO defined in the Act LXVIII of 2016 on Excise Duties
    :cvar CSK: A termék 343/2011. (XII. 29) Korm. rendelet 1. sz.
        melléklet A) cím szerinti csomagolószer-katalógus kódja (CsK
        kód) Packaging product catalogue code of the product according
        to the Title A) in the Schedule No.1 of the Government Decree
        No. 343/2011. (XII. 29.)
    :cvar KT: A termék 343/2011. (XII. 29) Korm. rendelet 1. sz.
        melléklet B) cím szerinti környezetvédelmi termékkódja (Kt kód)
        Environmental protection product code of the product according
        to the Title B) in the Schedule No.1 of the Government Decree
        No. 343/2011. (XII. 29.)
    :cvar EJ: Építményjegyzék szám Classification of Inventory of
        Construction
    :cvar TESZOR: A Termékek és Szolgáltatások Osztályozási Rendszere
        (TESZOR) szerinti termékkód - 451/2008/EK rendelet Product code
        according to the TESZOR (Hungarian Classification of Goods and
        Services), Classification of Product by Activity, CPA -
        regulation 451/2008/EC
    :cvar OWN: A vállalkozás által képzett termékkód The own product
        code of the enterprise
    :cvar OTHER: Egyéb termékkód Other product code
    """

    VTSZ = "VTSZ"
    SZJ = "SZJ"
    KN = "KN"
    AHK = "AHK"
    CSK = "CSK"
    KT = "KT"
    EJ = "EJ"
    TESZOR = "TESZOR"
    OWN = "OWN"
    OTHER = "OTHER"


class ProductFeeMeasuringUnitType(Enum):
    """
    Díjtétel egység típus Unit of the rate type.

    :cvar DARAB: Darab Piece
    :cvar KG: Kilogramm Kilogram
    """

    DARAB = "DARAB"
    KG = "KG"


class ProductFeeOperationType(Enum):
    """
    Termékdíj összesítés típus Product fee summary type.

    :cvar REFUND: Visszaigénylés Refund
    :cvar DEPOSIT: Raktárba szállítás Deposit
    """

    REFUND = "REFUND"
    DEPOSIT = "DEPOSIT"


class ProductStreamType(Enum):
    """
    Termékáram típus Product stream.

    :cvar BATTERY: Akkumulátor Battery
    :cvar PACKAGING: Csomagolószer Packaging products
    :cvar OTHER_PETROL: Egyéb kőolajtermék Other petroleum product
    :cvar ELECTRONIC: Az elektromos, elektronikai berendezés The
        electric appliance, electronic equipment
    :cvar TIRE: Gumiabroncs Tire
    :cvar COMMERCIAL: Reklámhordozó papír Commercial printing paper
    :cvar PLASTIC: Az egyéb műanyag termék Other plastic product
    :cvar OTHER_CHEMICAL: Egyéb vegyipari termék Other chemical product
    :cvar PAPER: Irodai papír Paper stationery
    """

    BATTERY = "BATTERY"
    PACKAGING = "PACKAGING"
    OTHER_PETROL = "OTHER_PETROL"
    ELECTRONIC = "ELECTRONIC"
    TIRE = "TIRE"
    COMMERCIAL = "COMMERCIAL"
    PLASTIC = "PLASTIC"
    OTHER_CHEMICAL = "OTHER_CHEMICAL"
    PAPER = "PAPER"


@dataclass
class ProjectNumbersType:
    """
    Projektszámok Project numbers.

    :ivar project_number: Projektszám Project number
    """

    project_number: list[str] = field(
        default_factory=list,
        metadata={
            "name": "projectNumber",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "min_occurs": 1,
            "min_length": 1,
            "max_length": 100,
            "pattern": r".*[^\s].*",
        },
    )


@dataclass
class ReferencesToOtherLinesType:
    """
    Hivatkozások kapcsolódó tételekre, ha ez az ÁFA törvény alapján szükséges
    References to connected items if it is necessary according to VAT law.

    :ivar reference_to_other_line: Hivatkozások kapcsolódó tételekre, ha
        ez az ÁFA törvény alapján szükséges References to connected
        items if it is necessary according to VAT law
    """

    reference_to_other_line: list[int] = field(
        default_factory=list,
        metadata={
            "name": "referenceToOtherLine",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "min_occurs": 1,
            "min_inclusive": 1,
            "total_digits": 20,
        },
    )


@dataclass
class ShippingDatesType:
    """
    Szállítási dátumok Shipping dates.

    :ivar shipping_date: Szállítási dátum Shipping date
    """

    shipping_date: list[str] = field(
        default_factory=list,
        metadata={
            "name": "shippingDate",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "min_occurs": 1,
            "min_length": 1,
            "max_length": 100,
            "pattern": r".*[^\s].*",
        },
    )


@dataclass
class SummaryGrossDataType:
    """
    A számla összesítő bruttó adatai Gross data of the invoice summary.

    :ivar invoice_gross_amount: A számla bruttó összege a számla
        pénznemében Gross amount of the invoice expressed in the
        currency of the invoice
    :ivar invoice_gross_amount_huf: A számla bruttó összege forintban
        Gross amount of the invoice expressed in HUF
    """

    invoice_gross_amount: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "invoiceGrossAmount",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "total_digits": 18,
            "fraction_digits": 2,
        },
    )
    invoice_gross_amount_huf: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "invoiceGrossAmountHUF",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "total_digits": 18,
            "fraction_digits": 2,
        },
    )


@dataclass
class SupplierCompanyCodesType:
    """
    Az eladó vállalati kódjai Company codes of the supplier.

    :ivar supplier_company_code: Az eladó vállalati kódja Company code
        of the supplier
    """

    supplier_company_code: list[str] = field(
        default_factory=list,
        metadata={
            "name": "supplierCompanyCode",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "min_occurs": 1,
            "min_length": 1,
            "max_length": 100,
            "pattern": r".*[^\s].*",
        },
    )


class TakeoverType(Enum):
    """
    Az átvállalás adatait tartalmazó típus Field type for data of takeover.

    :cvar VALUE_01: A 2011. évi LXXXV. tv. 14. § (4) bekezdés szerint az
        eladó (első belföldi forgalomba hozó) vállalja át a vevő
        termékdíj-kötelezettségét The supplier takes over buyer’s
        product fee liability on the basis of Paragraph (4), Section 14
        of the Act LXXXV of 2011
    :cvar VALUE_02_AA: A 2011. évi LXXXV. tv. 14. § (5) aa) alpontja
        szerint a vevő szerződés alapján átvállalja az eladó termékdíj-
        kötelezettségét On the basis of contract, the buyer takes over
        supplier’s product fee liability on the basis of sub-point aa),
        Paragraph (5), Section 14 of the Act LXXXV of 2011
    :cvar VALUE_02_AB:
    :cvar VALUE_02_B:
    :cvar VALUE_02_C:
    :cvar VALUE_02_D:
    :cvar VALUE_02_EA:
    :cvar VALUE_02_EB:
    :cvar VALUE_02_FA:
    :cvar VALUE_02_FB:
    :cvar VALUE_02_GA:
    :cvar VALUE_02_GB:
    """

    VALUE_01 = "01"
    VALUE_02_AA = "02_aa"
    VALUE_02_AB = "02_ab"
    VALUE_02_B = "02_b"
    VALUE_02_C = "02_c"
    VALUE_02_D = "02_d"
    VALUE_02_EA = "02_ea"
    VALUE_02_EB = "02_eb"
    VALUE_02_FA = "02_fa"
    VALUE_02_FB = "02_fb"
    VALUE_02_GA = "02_ga"
    VALUE_02_GB = "02_gb"


class UnitOfMeasureType(Enum):
    """
    Mennyiség egység típus Unit of measure type.

    :cvar PIECE: Darab Piece
    :cvar KILOGRAM: Kilogramm Kilogram
    :cvar TON: Metrikus tonna Metric ton
    :cvar KWH: Kilowatt óra Kilowatt hour
    :cvar DAY: Nap Day
    :cvar HOUR: Óra Hour
    :cvar MINUTE: Perc Minute
    :cvar MONTH: Hónap Month
    :cvar LITER: Liter Liter
    :cvar KILOMETER: Kilométer Kilometer
    :cvar CUBIC_METER: Köbméter Cubic meter
    :cvar METER: Méter Meter
    :cvar LINEAR_METER: Folyóméter Linear meter
    :cvar CARTON: Karton Carton
    :cvar PACK: Csomag Pack
    :cvar OWN: Saját mennyiségi egység megnevezés Own unit of measure
    """

    PIECE = "PIECE"
    KILOGRAM = "KILOGRAM"
    TON = "TON"
    KWH = "KWH"
    DAY = "DAY"
    HOUR = "HOUR"
    MINUTE = "MINUTE"
    MONTH = "MONTH"
    LITER = "LITER"
    KILOMETER = "KILOMETER"
    CUBIC_METER = "CUBIC_METER"
    METER = "METER"
    LINEAR_METER = "LINEAR_METER"
    CARTON = "CARTON"
    PACK = "PACK"
    OWN = "OWN"


@dataclass
class VatAmountMismatchType:
    """
    Adóalap és felszámított adó eltérésének adatai Data of mismatching tax base and
    levied tax.

    :ivar vat_rate: Adómérték, adótartalom VAT rate, VAT content
    :ivar case: Az eset leírása kóddal Case notation with code
    """

    vat_rate: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "vatRate",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "min_inclusive": Decimal("0"),
            "max_inclusive": Decimal("1"),
            "total_digits": 5,
            "fraction_digits": 4,
        },
    )
    case: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "min_length": 1,
            "max_length": 50,
            "pattern": r".*[^\s].*",
        },
    )


@dataclass
class VatRateGrossDataType:
    """
    Adott adómértékhez tartozó bruttó adatok Gross data of given tax rate.

    :ivar vat_rate_gross_amount: Az adott adómértékhez tartozó
        értékesítés vagy szolgáltatásnyújtás bruttó összege a számla
        pénznemében Gross amount of sales or service delivery under a
        given tax rate expressed in the currency of the invoice
    :ivar vat_rate_gross_amount_huf: Az adott adómértékhez tartozó
        értékesítés vagy szolgáltatásnyújtás bruttó összege forintban
        Gross amount of sales or service delivery under a given tax rate
        expressed in HUF
    """

    vat_rate_gross_amount: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "vatRateGrossAmount",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "total_digits": 18,
            "fraction_digits": 2,
        },
    )
    vat_rate_gross_amount_huf: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "vatRateGrossAmountHUF",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "total_digits": 18,
            "fraction_digits": 2,
        },
    )


@dataclass
class VatRateNetDataType:
    """
    Adott adómértékhez tartozó nettó adatok Net data of given tax rate.

    :ivar vat_rate_net_amount: Az adott adómértékhez tartozó értékesítés
        vagy szolgáltatásnyújtás nettó összege a számla pénznemében Net
        amount of sales or service delivery under a given tax rate
        expressed in the currency of the invoice
    :ivar vat_rate_net_amount_huf: Az adott adómértékhez tartozó
        értékesítés vagy szolgáltatásnyújtás nettó összege forintban Net
        amount of sales or service delivery under a given tax rate
        expressed in HUF
    """

    vat_rate_net_amount: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "vatRateNetAmount",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "total_digits": 18,
            "fraction_digits": 2,
        },
    )
    vat_rate_net_amount_huf: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "vatRateNetAmountHUF",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "total_digits": 18,
            "fraction_digits": 2,
        },
    )


@dataclass
class VatRateVatDataType:
    """
    Adott adómértékhez tartozó ÁFA adatok VAT data of given tax rate.

    :ivar vat_rate_vat_amount: Az adott adómértékhez tartozó értékesítés
        vagy szolgáltatásnyújtás ÁFA összege a számla pénznemében VAT
        amount of sales or service delivery under a given tax rate
        expressed in the currency of the invoice
    :ivar vat_rate_vat_amount_huf: Az adott adómértékhez tartozó
        értékesítés vagy szolgáltatásnyújtás ÁFA összege forintban VAT
        amount of sales or service delivery under a given tax rate
        expressed in HUF
    """

    vat_rate_vat_amount: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "vatRateVatAmount",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "total_digits": 18,
            "fraction_digits": 2,
        },
    )
    vat_rate_vat_amount_huf: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "vatRateVatAmountHUF",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "total_digits": 18,
            "fraction_digits": 2,
        },
    )


@dataclass
class VehicleType:
    """
    Szárazföldi közlekedési eszköz további adatai Other data in relation to
    motorised land vehicle.

    :ivar engine_capacity: Hengerűrtartalom köbcentiméterben Engine
        capacity in cubic centimetre
    :ivar engine_power: Teljesítmény kW-ban Engine power in kW
    :ivar kms: Futott kilométerek száma Travelled distance in km
    """

    engine_capacity: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "engineCapacity",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "total_digits": 22,
            "fraction_digits": 10,
        },
    )
    engine_power: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "enginePower",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "total_digits": 22,
            "fraction_digits": 10,
        },
    )
    kms: Optional[Decimal] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "total_digits": 22,
            "fraction_digits": 10,
        },
    )


@dataclass
class VesselType:
    """
    Vízi jármű adatai Data of vessel.

    :ivar length: Hajó hossza méterben Length of hull in metre
    :ivar activity_referred: Értéke true, ha a jármű az ÁFA tv. 259.§
        25. b) szerinti kivétel alá tartozik The value is true if the
        means of transport is exempt from VAT as per section 259 [25]
        (b)
    :ivar sailed_hours: Hajózott órák száma Number of sailed hours
    """

    length: Optional[Decimal] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "total_digits": 22,
            "fraction_digits": 10,
        },
    )
    activity_referred: Optional[bool] = field(
        default=None,
        metadata={
            "name": "activityReferred",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
        },
    )
    sailed_hours: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "sailedHours",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "total_digits": 22,
            "fraction_digits": 10,
        },
    )


@dataclass
class AdvanceDataType:
    """
    Előleghez kapcsolódó adatok Advance related data.

    :ivar advance_indicator: Értéke true, ha a számla tétel előleg
        jellegű The value is true if the invoice item is a kind of
        advance charge
    :ivar advance_payment_data: Előleg fizetéshez kapcsolódó adatok
        Advance payment related data
    """

    advance_indicator: Optional[bool] = field(
        default=None,
        metadata={
            "name": "advanceIndicator",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
        },
    )
    advance_payment_data: Optional[AdvancePaymentDataType] = field(
        default=None,
        metadata={
            "name": "advancePaymentData",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )


@dataclass
class ConventionalInvoiceInfoType:
    """
    A számlafeldolgozást segítő, egyezményesen nevesített egyéb adatok Other
    conventionally named data to assist in invoice processing.

    :ivar order_numbers: Megrendelésszám(ok) Order numbers
    :ivar delivery_notes: Szállítólevél szám(ok) Delivery notes
    :ivar shipping_dates: Szállítási dátum(ok) Shipping dates
    :ivar contract_numbers: Szerződésszám(ok) Contract numbers
    :ivar supplier_company_codes: Az eladó vállalati kódja(i) Company
        codes of the supplier
    :ivar customer_company_codes: A vevő vállalati kódja(i) Company
        codes of the customer
    :ivar dealer_codes: Beszállító kód(ok) Dealer codes
    :ivar cost_centers: Költséghely(ek) Cost centers
    :ivar project_numbers: Projektszám(ok) Project numbers
    :ivar general_ledger_account_numbers: Főkönyvi számlaszám(ok)
        General ledger account numbers
    :ivar gln_numbers_supplier: Kiállítói globális helyazonosító
        szám(ok) Supplier's global location numbers
    :ivar gln_numbers_customer: Vevői globális helyazonosító szám(ok)
        Customer's global location numbers
    :ivar material_numbers: Anyagszám(ok) Material numbers
    :ivar item_numbers: Cikkszám(ok) Item number(s)
    :ivar ekaer_ids: EKÁER azonosító(k) EKAER ID-s
    """

    order_numbers: Optional[OrderNumbersType] = field(
        default=None,
        metadata={
            "name": "orderNumbers",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )
    delivery_notes: Optional[DeliveryNotesType] = field(
        default=None,
        metadata={
            "name": "deliveryNotes",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )
    shipping_dates: Optional[ShippingDatesType] = field(
        default=None,
        metadata={
            "name": "shippingDates",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )
    contract_numbers: Optional[ContractNumbersType] = field(
        default=None,
        metadata={
            "name": "contractNumbers",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )
    supplier_company_codes: Optional[SupplierCompanyCodesType] = field(
        default=None,
        metadata={
            "name": "supplierCompanyCodes",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )
    customer_company_codes: Optional[CustomerCompanyCodesType] = field(
        default=None,
        metadata={
            "name": "customerCompanyCodes",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )
    dealer_codes: Optional[DealerCodesType] = field(
        default=None,
        metadata={
            "name": "dealerCodes",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )
    cost_centers: Optional[CostCentersType] = field(
        default=None,
        metadata={
            "name": "costCenters",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )
    project_numbers: Optional[ProjectNumbersType] = field(
        default=None,
        metadata={
            "name": "projectNumbers",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )
    general_ledger_account_numbers: Optional[
        GeneralLedgerAccountNumbersType
    ] = field(
        default=None,
        metadata={
            "name": "generalLedgerAccountNumbers",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )
    gln_numbers_supplier: Optional[GlnNumbersType] = field(
        default=None,
        metadata={
            "name": "glnNumbersSupplier",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )
    gln_numbers_customer: Optional[GlnNumbersType] = field(
        default=None,
        metadata={
            "name": "glnNumbersCustomer",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )
    material_numbers: Optional[MaterialNumbersType] = field(
        default=None,
        metadata={
            "name": "materialNumbers",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )
    item_numbers: Optional[ItemNumbersType] = field(
        default=None,
        metadata={
            "name": "itemNumbers",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )
    ekaer_ids: Optional[EkaerIdsType] = field(
        default=None,
        metadata={
            "name": "ekaerIds",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )


@dataclass
class CustomerDeclarationType:
    """
    Ha az eladó a vevő nyilatkozata alapján mentesül a termékdíj megfizetése alól,
    akkor az érintett termékáram Should the supplier, based on statement given by
    the purchaser, be exempted from paying product fee, then the product stream
    affected.

    :ivar product_stream: Termékáram Product stream
    :ivar product_fee_weight: Termékdíj köteles termék tömege
        kilogrammban Weight of product fee obliged product in kilogram
    """

    product_stream: Optional[ProductStreamType] = field(
        default=None,
        metadata={
            "name": "productStream",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
        },
    )
    product_fee_weight: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "productFeeWeight",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "total_digits": 22,
            "fraction_digits": 10,
        },
    )


@dataclass
class CustomerTaxNumberType(TaxNumberType):
    """Adószám, amely alatt a számlán szereplő termékbeszerzés vagy szolgáltatás
    igénybevétele történt.

    Lehet csoportazonosító szám is Tax number or group identification
    number, under which the purchase of goods or services is done

    :ivar group_member_tax_number: Csoport tag adószáma, ha a
        termékbeszerzés vagy szolgáltatás igénybevétele csoportazonosító
        szám alatt történt Tax number of group member, when the purchase
        of goods or services is done under group identification number
    """

    group_member_tax_number: Optional[TaxNumberType] = field(
        default=None,
        metadata={
            "name": "groupMemberTaxNumber",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )


@dataclass
class DieselOilPurchaseType:
    """Gázolaj adózottan történő beszerzésének adatai – 45/2016 (XI.

    29.) NGM rendelet 75. § (1) a) Data of gas oil acquisition after
    taxation – point a), paragraph (1) of Section 75 of the NGM Decree
    No. 45/2016. (XI. 29.)

    :ivar purchase_location: Gázolaj beszerzés helye Place of purchase
        of the gas oil
    :ivar purchase_date: Gázolaj beszerzés dátuma Date of purchase of
        gas oil
    :ivar vehicle_registration_number: Kereskedelmi jármű forgalmi
        rendszáma (csak betűk és számok) Registration number of vehicle
        (letters and numbers only)
    :ivar diesel_oil_quantity: Gépi bérmunka-szolgáltatás során
        felhasznált gázolaj mennyisége literben – Jöt. 117. § (2)
        Fordítandó helyett: Quantity of diesel oil used for contract
        work and machinery hire service in liter – Act LXVIII of 2016 on
        Excise Tax section 117 (2)
    """

    purchase_location: Optional[SimpleAddressType] = field(
        default=None,
        metadata={
            "name": "purchaseLocation",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
        },
    )
    purchase_date: Optional[str] = field(
        default=None,
        metadata={
            "name": "purchaseDate",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "min_inclusive": "2010-01-01",
            "pattern": r"\d{4}-\d{2}-\d{2}",
        },
    )
    vehicle_registration_number: Optional[str] = field(
        default=None,
        metadata={
            "name": "vehicleRegistrationNumber",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "min_length": 2,
            "max_length": 30,
            "pattern": r"[A-Z0-9ÖŐÜŰ]{2,30}",
        },
    )
    diesel_oil_quantity: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "dieselOilQuantity",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "total_digits": 22,
            "fraction_digits": 10,
        },
    )


@dataclass
class FiscalRepresentativeType:
    """
    A pénzügyi képviselő adatai Fiscal representative data.

    :ivar fiscal_representative_tax_number: A pénzügyi képviselő
        adószáma Tax number of the fiscal representative
    :ivar fiscal_representative_name: A pénzügyi képviselő neve Name of
        the fiscal representative
    :ivar fiscal_representative_address: Pénzügyi képviselő címe Address
        of the fiscal representative
    :ivar fiscal_representative_bank_account_number: Pénzügyi képviselő
        által a számla kibocsátó (eladó) számára megnyitott bankszámla
        bankszámlaszáma Bank account number opened by the fiscal
        representative for the issuer of the invoice (supplier)
    """

    fiscal_representative_tax_number: Optional[TaxNumberType] = field(
        default=None,
        metadata={
            "name": "fiscalRepresentativeTaxNumber",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
        },
    )
    fiscal_representative_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "fiscalRepresentativeName",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "min_length": 1,
            "max_length": 512,
            "pattern": r".*[^\s].*",
        },
    )
    fiscal_representative_address: Optional[AddressType] = field(
        default=None,
        metadata={
            "name": "fiscalRepresentativeAddress",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
        },
    )
    fiscal_representative_bank_account_number: Optional[str] = field(
        default=None,
        metadata={
            "name": "fiscalRepresentativeBankAccountNumber",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "min_length": 15,
            "max_length": 34,
            "pattern": r"[0-9]{8}[-][0-9]{8}[-][0-9]{8}|[0-9]{8}[-][0-9]{8}|[A-Z]{2}[0-9]{2}[0-9A-Za-z]{11,30}",
        },
    )


@dataclass
class LineModificationReferenceType:
    """
    Módosításról történő adatszolgáltatás esetén a tételsor módosítás jellegének
    jelölése Marking the goal of modification of the line (in the case of data
    supply about changes/updates only)

    :ivar line_number_reference: Az eredeti számla módosítással érintett
        tételének sorszáma (lineNumber). Új tétel létrehozása esetén az
        új tétel sorszáma, a meglévő tételsorok számozásának
        folytatásaként Line number of the original invoice, which the
        modification occurs with. In case of create operation the tag
        shall contain the new line number, as a sequential increment of
        the the existing lines set
    :ivar line_operation: A számlatétel módosításának jellege Line
        modification type
    """

    line_number_reference: Optional[int] = field(
        default=None,
        metadata={
            "name": "lineNumberReference",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "min_inclusive": 1,
            "total_digits": 20,
        },
    )
    line_operation: Optional[LineOperationType] = field(
        default=None,
        metadata={
            "name": "lineOperation",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
        },
    )


@dataclass
class NewTransportMeanType:
    """Új közlekedési eszköz értékesítés ÁFA tv.

    89 § ill. 169 § o)
    Supply of new means of transport - section 89 § and 169 (o) of the VAT law

    :ivar brand: Gyártmány/típus Product / type
    :ivar serial_num: Alvázszám/gyári szám/Gyártási szám Chassis number
        / serial number / product number
    :ivar engine_num: Motorszám Engine number
    :ivar first_entry_into_service: Első forgalomba helyezés időpontja
        First entry into service
    :ivar vehicle: Szárazföldi közlekedési eszköz további adatai Other
        data in relation to motorised land vehicle
    :ivar vessel: Vízi jármű adatai Data of vessel
    :ivar aircraft: Légi közlekedési eszköz Aircraft
    """

    brand: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "min_length": 1,
            "max_length": 50,
            "pattern": r".*[^\s].*",
        },
    )
    serial_num: Optional[str] = field(
        default=None,
        metadata={
            "name": "serialNum",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "min_length": 1,
            "max_length": 255,
            "pattern": r".*[^\s].*",
        },
    )
    engine_num: Optional[str] = field(
        default=None,
        metadata={
            "name": "engineNum",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "min_length": 1,
            "max_length": 255,
            "pattern": r".*[^\s].*",
        },
    )
    first_entry_into_service: Optional[str] = field(
        default=None,
        metadata={
            "name": "firstEntryIntoService",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "min_inclusive": "2010-01-01",
            "pattern": r"\d{4}-\d{2}-\d{2}",
        },
    )
    vehicle: Optional[VehicleType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )
    vessel: Optional[VesselType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )
    aircraft: Optional[AircraftType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )


@dataclass
class PaymentEvidenceDocumentDataType:
    """A termékdíj bevallását igazoló dokumentum adatai a 2011.

    évi LXXXV. tv. 13. § (3) szerint és a 25. § (3) szerint Data of the
    document verifying the declaration submitted on the product fee
    according to the Paragraph (3), Section 13 and the Paragraph (3)
    Section 25 of the Act LXXXV of 2011

    :ivar evidence_document_no: Számla sorszáma vagy egyéb okirat
        azonosító száma Sequential number of the invoice, or other
        document considered as such
    :ivar evidence_document_date: Számla kelte Date of issue of the
        invoice
    :ivar obligated_name: Kötelezett neve Name of obligator
    :ivar obligated_address: Kötelezett címe Address of obligator
    :ivar obligated_tax_number: A kötelezett adószáma Tax number of
        obligated
    """

    evidence_document_no: Optional[str] = field(
        default=None,
        metadata={
            "name": "evidenceDocumentNo",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "min_length": 1,
            "max_length": 50,
            "pattern": r".*[^\s].*",
        },
    )
    evidence_document_date: Optional[str] = field(
        default=None,
        metadata={
            "name": "evidenceDocumentDate",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "min_inclusive": "2010-01-01",
            "pattern": r"\d{4}-\d{2}-\d{2}",
        },
    )
    obligated_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "obligatedName",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "min_length": 1,
            "max_length": 255,
            "pattern": r".*[^\s].*",
        },
    )
    obligated_address: Optional[AddressType] = field(
        default=None,
        metadata={
            "name": "obligatedAddress",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
        },
    )
    obligated_tax_number: Optional[TaxNumberType] = field(
        default=None,
        metadata={
            "name": "obligatedTaxNumber",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
        },
    )


@dataclass
class ProductCodeType:
    """
    Különböző termék- vagy szolgáltatáskódokat tartalmazó típus Field type
    including the different product and service codes.

    :ivar product_code_category: A termékkód fajtájának (pl. VTSZ, CsK,
        stb.) jelölése The kind of product code (f. ex. VTSZ, CsK, etc.)
    :ivar product_code_value: A termékkód értéke nem saját termékkód
        esetén The value of (not own) product code
    :ivar product_code_own_value: Saját termékkód értéke Own product
        code value
    """

    product_code_category: Optional[ProductCodeCategoryType] = field(
        default=None,
        metadata={
            "name": "productCodeCategory",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
        },
    )
    product_code_value: Optional[str] = field(
        default=None,
        metadata={
            "name": "productCodeValue",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "min_length": 2,
            "max_length": 30,
            "pattern": r"[A-Z0-9]{2,30}",
        },
    )
    product_code_own_value: Optional[str] = field(
        default=None,
        metadata={
            "name": "productCodeOwnValue",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "min_length": 1,
            "max_length": 255,
            "pattern": r".*[^\s].*",
        },
    )


@dataclass
class ProductFeeTakeoverDataType:
    """
    A környezetvédelmi termékdíj kötelezettség átvállalásával kapcsolatos adatok
    Data in connection with takeover of environmental protection product fee.

    :ivar takeover_reason: Az átvállalás iránya és jogszabályi alapja
        Direction and legal base of takeover
    :ivar takeover_amount: Az átvállalt termékdíj összege forintban, ha
        a vevő vállalja át az eladó termékdíj-kötelezettségét Amount in
        Hungarian forints of the product fee taken over if the purchaser
        takes over the supplier’s product fee liability
    """

    takeover_reason: Optional[TakeoverType] = field(
        default=None,
        metadata={
            "name": "takeoverReason",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
        },
    )
    takeover_amount: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "takeoverAmount",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "total_digits": 18,
            "fraction_digits": 2,
        },
    )


@dataclass
class SupplierInfoType:
    """
    A szállító (eladó) adatai Invoice supplier (seller) data.

    :ivar supplier_tax_number: Belföldi adószám vagy csoportazonosító
        szám Tax number or group identification number
    :ivar group_member_tax_number: Csoport tag adószáma, ha a
        termékbeszerzés vagy szolgáltatás nyújtása csoportazonosító szám
        alatt történt Tax number of group member, when the supply of
        goods or services is done under group identification number
    :ivar community_vat_number: Közösségi adószám Community tax number
    :ivar supplier_name: Az eladó (szállító) neve Name of the seller
        (supplier)
    :ivar supplier_address: Az eladó (szállító) címe Address of the
        seller (supplier)
    :ivar supplier_bank_account_number: Az eladó (szállító)
        bankszámlaszáma Bank account number of the seller (supplier)
    :ivar individual_exemption: Értéke true, amennyiben az eladó
        (szállító) alanyi ÁFA mentes Value is true if the seller
        (supplier) is individually exempted from VAT
    :ivar excise_licence_num: Az eladó adóraktári engedélyének vagy
        jövedéki engedélyének száma (2016. évi LXVIII. tv.) Number of
        supplier’s tax warehouse license or excise license (Act LXVIII
        of 2016)
    """

    supplier_tax_number: Optional[TaxNumberType] = field(
        default=None,
        metadata={
            "name": "supplierTaxNumber",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
        },
    )
    group_member_tax_number: Optional[TaxNumberType] = field(
        default=None,
        metadata={
            "name": "groupMemberTaxNumber",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )
    community_vat_number: Optional[str] = field(
        default=None,
        metadata={
            "name": "communityVatNumber",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "min_length": 4,
            "max_length": 15,
            "pattern": r"[A-Z]{2}[0-9A-Z]{2,13}",
        },
    )
    supplier_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "supplierName",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "min_length": 1,
            "max_length": 512,
            "pattern": r".*[^\s].*",
        },
    )
    supplier_address: Optional[AddressType] = field(
        default=None,
        metadata={
            "name": "supplierAddress",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
        },
    )
    supplier_bank_account_number: Optional[str] = field(
        default=None,
        metadata={
            "name": "supplierBankAccountNumber",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "min_length": 15,
            "max_length": 34,
            "pattern": r"[0-9]{8}[-][0-9]{8}[-][0-9]{8}|[0-9]{8}[-][0-9]{8}|[A-Z]{2}[0-9]{2}[0-9A-Za-z]{11,30}",
        },
    )
    individual_exemption: Optional[bool] = field(
        default=None,
        metadata={
            "name": "individualExemption",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )
    excise_licence_num: Optional[str] = field(
        default=None,
        metadata={
            "name": "exciseLicenceNum",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "min_length": 1,
            "max_length": 50,
            "pattern": r".*[^\s].*",
        },
    )


@dataclass
class VatRateType:
    """
    Az adómérték vagy az adómentes értékesítés jelölése Marking tax rate or tax
    exempt supply.

    :ivar vat_percentage: Az alkalmazott adó mértéke - ÁFA tv. 169. § j)
        Applied tax rate - section 169 (j) of the VAT law
    :ivar vat_content: ÁFA tartalom egyszerűsített számla esetén VAT
        content in case of simplified invoice
    :ivar vat_exemption: Az adómentesség jelölése - ÁFA tv. 169. § m)
        Marking tax exemption -  section 169 (m) of the VAT law
    :ivar vat_out_of_scope: Az ÁFA törvény hatályán kívüli Out of scope
        of the VAT law
    :ivar vat_domestic_reverse_charge: A belföldi fordított adózás
        jelölése - ÁFA tv. 142. § Marking the national is reverse charge
        taxation - section 142 of the VAT law
    :ivar margin_scheme_indicator: Különbözet szerinti szabályozás
        jelölése - ÁFA tv. 169. § p) q) Marking the margin-scheme
        taxation as per section 169 (p)(q)
    :ivar vat_amount_mismatch: Adóalap és felszámított adó eltérésének
        esetei Different cases of mismatching tax base and levied tax
    :ivar no_vat_charge: Nincs felszámított áfa a 17. § alapján No VAT
        charged under Section 17
    """

    vat_percentage: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "vatPercentage",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "min_inclusive": Decimal("0"),
            "max_inclusive": Decimal("1"),
            "total_digits": 5,
            "fraction_digits": 4,
        },
    )
    vat_content: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "vatContent",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "min_inclusive": Decimal("0"),
            "max_inclusive": Decimal("1"),
            "total_digits": 5,
            "fraction_digits": 4,
        },
    )
    vat_exemption: Optional[DetailedReasonType] = field(
        default=None,
        metadata={
            "name": "vatExemption",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )
    vat_out_of_scope: Optional[DetailedReasonType] = field(
        default=None,
        metadata={
            "name": "vatOutOfScope",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )
    vat_domestic_reverse_charge: bool = field(
        init=False,
        default=True,
        metadata={
            "name": "vatDomesticReverseCharge",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )
    margin_scheme_indicator: Optional[MarginSchemeType] = field(
        default=None,
        metadata={
            "name": "marginSchemeIndicator",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )
    vat_amount_mismatch: Optional[VatAmountMismatchType] = field(
        default=None,
        metadata={
            "name": "vatAmountMismatch",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )
    no_vat_charge: bool = field(
        init=False,
        default=True,
        metadata={
            "name": "noVatCharge",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )


@dataclass
class CustomerVatDataType:
    """
    A vevő ÁFA alanyisági adatai VAT subjectivity data of the customer.

    :ivar customer_tax_number: Belföldi adószám, amely alatt a számlán
        szereplő termékbeszerzés vagy szolgáltatás igénybevétele
        történt. Lehet csoportazonosító szám is Domestic tax number or
        group identification number, under which the purchase of goods
        or services is done
    :ivar community_vat_number: Közösségi adószám Community tax number
    :ivar third_state_tax_id: Harmadik országbeli adóazonosító Third
        state tax identification number
    """

    customer_tax_number: Optional[CustomerTaxNumberType] = field(
        default=None,
        metadata={
            "name": "customerTaxNumber",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )
    community_vat_number: Optional[str] = field(
        default=None,
        metadata={
            "name": "communityVatNumber",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "min_length": 4,
            "max_length": 15,
            "pattern": r"[A-Z]{2}[0-9A-Z]{2,13}",
        },
    )
    third_state_tax_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "thirdStateTaxId",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "min_length": 1,
            "max_length": 50,
            "pattern": r".*[^\s].*",
        },
    )


@dataclass
class InvoiceDetailType:
    """
    Számla részletező adatok Invoice detail data.

    :ivar invoice_category: A számla típusa, módosító okirat esetén az
        eredeti számla típusa Type of invoice. In case of modification
        document the type of original invoice
    :ivar invoice_delivery_date: Teljesítés dátuma (ha nem szerepel a
        számlán, akkor azonos a számla keltével) - ÁFA tv. 169. § g)
        Delivery date (if this field does not exist on the invoice, the
        date of the invoice should be considered as such) - section 169
        (g) of the VAT law
    :ivar invoice_delivery_period_start: Amennyiben a számla egy
        időszakra vonatkozik, akkor az időszak első napja The first day
        of the delivery, if the invoice delivery is a period
    :ivar invoice_delivery_period_end: Amennyiben a számla egy időszakra
        vonatkozik, akkor az időszak utolsó napja The last day of the
        delivery, if the invoice delivery is a period
    :ivar invoice_accounting_delivery_date: Számviteli teljesítés
        dátuma. Időszak esetén az időszak utolsó napja Date of
        accounting accomplishment. In the event of a period, the last
        day of the period
    :ivar periodical_settlement: Annak jelzése, ha a felek a
        termékértékesítés, szolgáltatás nyújtás során időszakonkénti
        elszámolásban vagy fizetésben állapodnak meg, vagy a
        termékértékesítés, szolgáltatás nyújtás ellenértékét
        meghatározott időpontra állapítják meg. Indicates where by
        agreement of the parties it gives rise to successive statements
        of account or successive payments relating to the supply of
        goods, or the supply of services, or if the consideration agreed
        upon for such goods and/or services applies to specific periods.
    :ivar small_business_indicator: Kisadózó jelzése Marking of low tax-
        bracket enterprise
    :ivar currency_code: A számla pénzneme az ISO 4217 szabvány szerint
        ISO 4217 currency code on the invoice
    :ivar exchange_rate: HUF-tól különböző pénznem esetén az alkalmazott
        árfolyam: egy egység értéke HUF-ban In case any currency is used
        other than HUF, the applied exchange rate should be mentioned: 1
        unit of the foreign currency expressed in HUF
    :ivar utility_settlement_indicator: Közmű elszámoló számla jelölése
        (2013.évi CLXXXVIII törvény szerinti elszámoló számla) Marking
        the fact of utility settlement invoice (invoice according to Act
        CLXXXVIII of 2013)
    :ivar self_billing_indicator: Önszámlázás jelölése (önszámlázás
        esetén true) Marking the fact of self-billing (in the case of
        self-billing the value is true)
    :ivar payment_method: Fizetés módja Method of payment
    :ivar payment_date: Fizetési határidő Deadline for payment
    :ivar cash_accounting_indicator: Pénzforgalmi elszámolás jelölése,
        ha az szerepel a számlán - ÁFA tv. 169. § h). Értéke true
        pénzforgalmi elszámolás esetén Marking the fact of cash
        accounting if this is indicated on the invoice - section 169 (h)
        of the VAT law. The value is true in case of cash accounting
    :ivar invoice_appearance: A számla vagy módosító okirat megjelenési
        formája Form of appearance of the invoice or modification
        document
    :ivar conventional_invoice_info: A számlafeldolgozást segítő,
        egyezményesen nevesített egyéb adatok Other conventionally named
        data to assist in invoice processing
    :ivar additional_invoice_data: A számlára vonatkozó egyéb adat Other
        data in relation to the invoice
    """

    invoice_category: Optional[InvoiceCategoryType] = field(
        default=None,
        metadata={
            "name": "invoiceCategory",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
        },
    )
    invoice_delivery_date: Optional[str] = field(
        default=None,
        metadata={
            "name": "invoiceDeliveryDate",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "min_inclusive": "2010-01-01",
            "pattern": r"\d{4}-\d{2}-\d{2}",
        },
    )
    invoice_delivery_period_start: Optional[str] = field(
        default=None,
        metadata={
            "name": "invoiceDeliveryPeriodStart",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "min_inclusive": "2010-01-01",
            "pattern": r"\d{4}-\d{2}-\d{2}",
        },
    )
    invoice_delivery_period_end: Optional[str] = field(
        default=None,
        metadata={
            "name": "invoiceDeliveryPeriodEnd",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "min_inclusive": "2010-01-01",
            "pattern": r"\d{4}-\d{2}-\d{2}",
        },
    )
    invoice_accounting_delivery_date: Optional[str] = field(
        default=None,
        metadata={
            "name": "invoiceAccountingDeliveryDate",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "min_inclusive": "2010-01-01",
            "pattern": r"\d{4}-\d{2}-\d{2}",
        },
    )
    periodical_settlement: Optional[bool] = field(
        default=None,
        metadata={
            "name": "periodicalSettlement",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )
    small_business_indicator: Optional[bool] = field(
        default=None,
        metadata={
            "name": "smallBusinessIndicator",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )
    currency_code: Optional[str] = field(
        default=None,
        metadata={
            "name": "currencyCode",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "min_length": 1,
            "max_length": 4,
            "length": 3,
            "pattern": r"[A-Z]{3}",
        },
    )
    exchange_rate: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "exchangeRate",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "min_exclusive": Decimal("0"),
            "total_digits": 14,
            "fraction_digits": 6,
        },
    )
    utility_settlement_indicator: Optional[bool] = field(
        default=None,
        metadata={
            "name": "utilitySettlementIndicator",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )
    self_billing_indicator: Optional[bool] = field(
        default=None,
        metadata={
            "name": "selfBillingIndicator",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )
    payment_method: Optional[PaymentMethodType] = field(
        default=None,
        metadata={
            "name": "paymentMethod",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )
    payment_date: Optional[str] = field(
        default=None,
        metadata={
            "name": "paymentDate",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "min_inclusive": "2010-01-01",
            "pattern": r"\d{4}-\d{2}-\d{2}",
        },
    )
    cash_accounting_indicator: Optional[bool] = field(
        default=None,
        metadata={
            "name": "cashAccountingIndicator",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )
    invoice_appearance: Optional[InvoiceAppearanceType] = field(
        default=None,
        metadata={
            "name": "invoiceAppearance",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
        },
    )
    conventional_invoice_info: Optional[ConventionalInvoiceInfoType] = field(
        default=None,
        metadata={
            "name": "conventionalInvoiceInfo",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )
    additional_invoice_data: list[AdditionalDataType] = field(
        default_factory=list,
        metadata={
            "name": "additionalInvoiceData",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )


@dataclass
class LineAmountsNormalType:
    """
    Normál vagy gyűjtő számla esetén kitöltendő tétel érték adatok Item value data
    to be completed in case of normal or aggregate invoice.

    :ivar line_net_amount_data: Tétel nettó adatok Line net data
    :ivar line_vat_rate: Adómérték vagy adómentesség jelölése Tax rate
        or tax exemption marking
    :ivar line_vat_data: Tétel ÁFA adatok Line VAT data
    :ivar line_gross_amount_data: Tétel bruttó adatok Line gross data
    """

    line_net_amount_data: Optional[LineNetAmountDataType] = field(
        default=None,
        metadata={
            "name": "lineNetAmountData",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
        },
    )
    line_vat_rate: Optional[VatRateType] = field(
        default=None,
        metadata={
            "name": "lineVatRate",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
        },
    )
    line_vat_data: Optional[LineVatDataType] = field(
        default=None,
        metadata={
            "name": "lineVatData",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )
    line_gross_amount_data: Optional[LineGrossAmountDataType] = field(
        default=None,
        metadata={
            "name": "lineGrossAmountData",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )


@dataclass
class LineAmountsSimplifiedType:
    """
    Egyszerűsített számla esetén kitöltendő tétel érték adatok Item value data to
    be completed in case of simplified invoice.

    :ivar line_vat_rate: Adómérték vagy adómentesség jelölése Tax rate
        or tax exemption marking
    :ivar line_gross_amount_simplified: Tétel bruttó értéke a számla
        pénznemében Gross amount of the item expressed in the currency
        of the invoice
    :ivar line_gross_amount_simplified_huf: Tétel bruttó értéke
        forintban Gross amount of the item expressed in HUF
    """

    line_vat_rate: Optional[VatRateType] = field(
        default=None,
        metadata={
            "name": "lineVatRate",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
        },
    )
    line_gross_amount_simplified: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "lineGrossAmountSimplified",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "total_digits": 18,
            "fraction_digits": 2,
        },
    )
    line_gross_amount_simplified_huf: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "lineGrossAmountSimplifiedHUF",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "total_digits": 18,
            "fraction_digits": 2,
        },
    )


@dataclass
class ProductCodesType:
    """
    Termékkódok Product codes.

    :ivar product_code: Termékkód Product code
    """

    product_code: list[ProductCodeType] = field(
        default_factory=list,
        metadata={
            "name": "productCode",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "min_occurs": 1,
        },
    )


@dataclass
class ProductFeeClauseType:
    """A környezetvédelmi termékdíjról szóló 2011.

    évi LXXXV. tv. szerinti, tételre vonatkozó záradékok Clauses
    according to the Act LXXXV of 2011 on Environmental Protection
    Product Fee (related to the item)

    :ivar product_fee_takeover_data: A környezetvédelmi termékdíj
        kötelezettség átvállalásával kapcsolatos adatok Data in
        connection with takeover of environmental protection product fee
    :ivar customer_declaration: Ha az eladó a vevő nyilatkozata alapján
        mentesül a termékdíj megfizetése alól, akkor az érintett
        termékáram Should the supplier, based on statement given by the
        purchaser, be exempted from paying product fee, then the product
        stream affected
    """

    product_fee_takeover_data: Optional[ProductFeeTakeoverDataType] = field(
        default=None,
        metadata={
            "name": "productFeeTakeoverData",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )
    customer_declaration: Optional[CustomerDeclarationType] = field(
        default=None,
        metadata={
            "name": "customerDeclaration",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )


@dataclass
class ProductFeeDataType:
    """
    Termékdíj adatok Product charges data.

    :ivar product_fee_code: Termékdíj kód (Kt vagy Csk) Product charges
        code (Kt or Csk code)
    :ivar product_fee_quantity: A termékdíjjal érintett termék
        mennyisége Quantity of product, according to product charge
    :ivar product_fee_measuring_unit: A díjtétel egysége (kg vagy darab)
        Unit of the rate (kg or piece)
    :ivar product_fee_rate: A termékdíj díjtétele (HUF/egység) Product
        fee rate (HUF/unit)
    :ivar product_fee_amount: Termékdíj összege forintban Amount in
        Hungarian forints of the product fee
    """

    product_fee_code: Optional[ProductCodeType] = field(
        default=None,
        metadata={
            "name": "productFeeCode",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
        },
    )
    product_fee_quantity: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "productFeeQuantity",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "total_digits": 22,
            "fraction_digits": 10,
        },
    )
    product_fee_measuring_unit: Optional[ProductFeeMeasuringUnitType] = field(
        default=None,
        metadata={
            "name": "productFeeMeasuringUnit",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
        },
    )
    product_fee_rate: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "productFeeRate",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "total_digits": 18,
            "fraction_digits": 2,
        },
    )
    product_fee_amount: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "productFeeAmount",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "total_digits": 18,
            "fraction_digits": 2,
        },
    )


@dataclass
class SummaryByVatRateType:
    """
    ÁFA mértékek szerinti összesítés Summary according to VAT rates.

    :ivar vat_rate: Adómérték vagy adómentesség jelölése Marking the tax
        rate or the fact of tax exemption
    :ivar vat_rate_net_data: Adott adómértékhez tartozó nettó adatok Net
        data of given tax rate
    :ivar vat_rate_vat_data: Adott adómértékhez tartozó ÁFA adatok VAT
        data of given tax rate
    :ivar vat_rate_gross_data: Adott adómértékhez tartozó bruttó adatok
        Gross data of given tax rate
    """

    vat_rate: Optional[VatRateType] = field(
        default=None,
        metadata={
            "name": "vatRate",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
        },
    )
    vat_rate_net_data: Optional[VatRateNetDataType] = field(
        default=None,
        metadata={
            "name": "vatRateNetData",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
        },
    )
    vat_rate_vat_data: Optional[VatRateVatDataType] = field(
        default=None,
        metadata={
            "name": "vatRateVatData",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
        },
    )
    vat_rate_gross_data: Optional[VatRateGrossDataType] = field(
        default=None,
        metadata={
            "name": "vatRateGrossData",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )


@dataclass
class SummarySimplifiedType:
    """
    Egyszerűsített számla összesítés Calculation of simplified invoice totals.

    :ivar vat_rate: Adómérték vagy adómentesség jelölése Marking the tax
        rate or the fact of tax exemption
    :ivar vat_content_gross_amount: Az adott adótartalomhoz tartozó
        értékesítés vagy szolgáltatásnyújtás bruttó összege a számla
        pénznemében The gross amount of the sale or service for the
        given tax amount in the currency of the invoice
    :ivar vat_content_gross_amount_huf: Az adott adótartalomhoz tartozó
        értékesítés vagy szolgáltatásnyújtás bruttó összege forintban
        The gross amount of the sale or service for the given tax amount
        in HUF
    """

    vat_rate: Optional[VatRateType] = field(
        default=None,
        metadata={
            "name": "vatRate",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
        },
    )
    vat_content_gross_amount: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "vatContentGrossAmount",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "total_digits": 18,
            "fraction_digits": 2,
        },
    )
    vat_content_gross_amount_huf: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "vatContentGrossAmountHUF",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "total_digits": 18,
            "fraction_digits": 2,
        },
    )


@dataclass
class CustomerInfoType:
    """
    A vevő adatai Customer data.

    :ivar customer_vat_status: Vevő ÁFA szerinti státusza Customers
        status by VAT
    :ivar customer_vat_data: A vevő ÁFA alanyisági adatai VAT
        subjectivity data of the customer
    :ivar customer_name: A vevő neve Name of the customer
    :ivar customer_address: A vevő címe Address of the customer
    :ivar customer_bank_account_number: Vevő bankszámlaszáma Bank
        account number of the customer
    """

    customer_vat_status: Optional[CustomerVatStatusType] = field(
        default=None,
        metadata={
            "name": "customerVatStatus",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
        },
    )
    customer_vat_data: Optional[CustomerVatDataType] = field(
        default=None,
        metadata={
            "name": "customerVatData",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )
    customer_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "customerName",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "min_length": 1,
            "max_length": 512,
            "pattern": r".*[^\s].*",
        },
    )
    customer_address: Optional[AddressType] = field(
        default=None,
        metadata={
            "name": "customerAddress",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )
    customer_bank_account_number: Optional[str] = field(
        default=None,
        metadata={
            "name": "customerBankAccountNumber",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "min_length": 15,
            "max_length": 34,
            "pattern": r"[0-9]{8}[-][0-9]{8}[-][0-9]{8}|[0-9]{8}[-][0-9]{8}|[A-Z]{2}[0-9]{2}[0-9A-Za-z]{11,30}",
        },
    )


@dataclass
class LineType:
    """
    A számla tételek (termék vagy szolgáltatás) adatait tartalmazó típus Field type
    including data of invoice items (product or service)

    :ivar line_number: A tétel sorszáma Sequential number of the item
    :ivar line_modification_reference: Módosításról történő
        adatszolgáltatás esetén a tételsor módosítás jellegének jelölése
        Marking the goal of modification of the line (in the case of
        data supply about changes/updates only)
    :ivar references_to_other_lines: Hivatkozások kapcsolódó tételekre,
        ha ez az ÁFA törvény alapján szükséges References to connected
        items if it is necessary according to VAT law
    :ivar advance_data: Előleghez kapcsolódó adatok Advance related data
    :ivar product_codes: Termékkódok Product codes
    :ivar line_expression_indicator: Értéke true, ha a tétel mennyiségi
        egysége természetes mértékegységben kifejezhető The value is
        true if the unit of measure of the invoice item is expressible
        in natural unit
    :ivar line_nature_indicator: Adott tételsor termékértékesítés vagy
        szolgáltatás nyújtás jellegének jelzése Indication of the nature
        of the supply of goods or services on a given line
    :ivar line_description: A termék vagy szolgáltatás megnevezése Name
        / description of the product or service
    :ivar quantity: Mennyiség Quantity
    :ivar unit_of_measure: A számlán szereplő mennyiségi egység
        kanonikus kifejezése az interfész specifikáció szerint Canonical
        representation of the unit of measure of the invoice, according
        to the interface specification
    :ivar unit_of_measure_own: A számlán szereplő mennyiségi egység
        literális kifejezése Literal unit of measure of the invoice
    :ivar unit_price: Egységár a számla pénznemében. Egyszerűsített
        számla esetén bruttó, egyéb esetben nettó egységár Unit price
        expressed in the currency of the invoice In the event of
        simplified invoices gross unit price, in other cases net unit
        price
    :ivar unit_price_huf: Egységár forintban Unit price expressed in HUF
    :ivar line_discount_data: A tételhez tartozó árengedmény adatok
        Discount data in relation to the item
    :ivar line_amounts_normal: Normál (nem egyszerűsített) számla esetén
        (beleértve a gyűjtőszámlát) kitöltendő tétel érték adatok. Item
        value data to be completed in case of normal (not simplified,
        but including aggregated) invoice
    :ivar line_amounts_simplified: Egyszerűsített számla esetén
        kitöltendő tétel érték adatok Item value data to be completed in
        case of simplified invoice
    :ivar intermediated_service: Értéke true ha a tétel közvetített
        szolgáltatás - Számviteli tv. 3.§ (4) 1 The value is true if the
        item is an intermediated service - paragraph (4) 1 of the
        Article 3 of Accounting Act
    :ivar aggregate_invoice_line_data: Gyűjtő számla adatok Aggregate
        invoice data
    :ivar new_transport_mean: Új közlekedési eszköz értékesítés ÁFA tv.
        89 § ill. 169 § o) Supply of new means of transport - section 89
        § and 169 (o) of the VAT law
    :ivar deposit_indicator: Értéke true, ha a tétel betétdíj jellegű
        The value is true if the item is bottle/container deposit
    :ivar obligated_for_product_fee: Értéke true ha a tételt termékdíj
        fizetési kötelezettség terheli The value is true if the item is
        liable to product fee
    :ivar gpcexcise: Földgáz, villamos energia, szén jövedéki adója
        forintban - Jöt. 118. § (2) Excise duty on natural gas,
        electricity and coal in Hungarian forints – paragraph (2),
        Section 118 of the Act on Excise Duties
    :ivar diesel_oil_purchase: Gázolaj adózottan történő beszerzésének
        adatai – 45/2016 (XI. 29.) NGM rendelet 75. § (1) a) Data of gas
        oil acquisition after taxation – point a), paragraph (1) of
        Section 75 of the NGM Decree No. 45/2016. (XI. 29.)
    :ivar neta_declaration: Értéke true, ha a Neta tv-ben meghatározott
        adókötelezettség az adó alanyát terheli. 2011. évi CIII. tv.
        3.§(2) Value is true, if the taxable person is liable for tax
        obligation determined in the Act on Public Health Product Tax
        (Neta tv.). Paragraph (2), Section 3 of the Act CIII of 2011
    :ivar product_fee_clause: A környezetvédelmi termékdíjról szóló
        2011. évi LXXXV. tv. szerinti, tételre vonatkozó záradékok
        Clauses according to the Act LXXXV of 2011 on Environmental
        Protection Product Fee (related to the item)
    :ivar line_product_fee_content: A tétel termékdíj tartalmára
        vonatkozó adatok Data on the content of the line's product
        charge
    :ivar conventional_line_info: A számlafeldolgozást segítő,
        egyezményesen nevesített egyéb adatok Other conventionally named
        data to assist in invoice processing
    :ivar additional_line_data: A termék/szolgáltatás tételhez
        kapcsolódó, további adat Other data in relation to the product /
        service item
    """

    line_number: Optional[int] = field(
        default=None,
        metadata={
            "name": "lineNumber",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "min_inclusive": 1,
            "total_digits": 20,
        },
    )
    line_modification_reference: Optional[LineModificationReferenceType] = (
        field(
            default=None,
            metadata={
                "name": "lineModificationReference",
                "type": "Element",
                "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            },
        )
    )
    references_to_other_lines: Optional[ReferencesToOtherLinesType] = field(
        default=None,
        metadata={
            "name": "referencesToOtherLines",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )
    advance_data: Optional[AdvanceDataType] = field(
        default=None,
        metadata={
            "name": "advanceData",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )
    product_codes: Optional[ProductCodesType] = field(
        default=None,
        metadata={
            "name": "productCodes",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )
    line_expression_indicator: Optional[bool] = field(
        default=None,
        metadata={
            "name": "lineExpressionIndicator",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
        },
    )
    line_nature_indicator: Optional[LineNatureIndicatorType] = field(
        default=None,
        metadata={
            "name": "lineNatureIndicator",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )
    line_description: Optional[str] = field(
        default=None,
        metadata={
            "name": "lineDescription",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "min_length": 1,
            "max_length": 512,
            "pattern": r".*[^\s].*",
        },
    )
    quantity: Optional[Decimal] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "total_digits": 22,
            "fraction_digits": 10,
        },
    )
    unit_of_measure: Optional[UnitOfMeasureType] = field(
        default=None,
        metadata={
            "name": "unitOfMeasure",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )
    unit_of_measure_own: Optional[str] = field(
        default=None,
        metadata={
            "name": "unitOfMeasureOwn",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "min_length": 1,
            "max_length": 50,
            "pattern": r".*[^\s].*",
        },
    )
    unit_price: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "unitPrice",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "total_digits": 22,
            "fraction_digits": 10,
        },
    )
    unit_price_huf: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "unitPriceHUF",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "total_digits": 22,
            "fraction_digits": 10,
        },
    )
    line_discount_data: Optional[DiscountDataType] = field(
        default=None,
        metadata={
            "name": "lineDiscountData",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )
    line_amounts_normal: Optional[LineAmountsNormalType] = field(
        default=None,
        metadata={
            "name": "lineAmountsNormal",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )
    line_amounts_simplified: Optional[LineAmountsSimplifiedType] = field(
        default=None,
        metadata={
            "name": "lineAmountsSimplified",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )
    intermediated_service: Optional[bool] = field(
        default=None,
        metadata={
            "name": "intermediatedService",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )
    aggregate_invoice_line_data: Optional[AggregateInvoiceLineDataType] = (
        field(
            default=None,
            metadata={
                "name": "aggregateInvoiceLineData",
                "type": "Element",
                "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            },
        )
    )
    new_transport_mean: Optional[NewTransportMeanType] = field(
        default=None,
        metadata={
            "name": "newTransportMean",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )
    deposit_indicator: Optional[bool] = field(
        default=None,
        metadata={
            "name": "depositIndicator",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )
    obligated_for_product_fee: Optional[bool] = field(
        default=None,
        metadata={
            "name": "obligatedForProductFee",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )
    gpcexcise: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "GPCExcise",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "total_digits": 18,
            "fraction_digits": 2,
        },
    )
    diesel_oil_purchase: Optional[DieselOilPurchaseType] = field(
        default=None,
        metadata={
            "name": "dieselOilPurchase",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )
    neta_declaration: Optional[bool] = field(
        default=None,
        metadata={
            "name": "netaDeclaration",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )
    product_fee_clause: Optional[ProductFeeClauseType] = field(
        default=None,
        metadata={
            "name": "productFeeClause",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )
    line_product_fee_content: list[ProductFeeDataType] = field(
        default_factory=list,
        metadata={
            "name": "lineProductFeeContent",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )
    conventional_line_info: Optional[ConventionalInvoiceInfoType] = field(
        default=None,
        metadata={
            "name": "conventionalLineInfo",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )
    additional_line_data: list[AdditionalDataType] = field(
        default_factory=list,
        metadata={
            "name": "additionalLineData",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )


@dataclass
class ProductFeeSummaryType:
    """
    Termékdíj összegzés adatok Summary of product charges.

    :ivar product_fee_operation: Annak jelzése, hogy a termékdíj
        összesítés visszaigénylésre (REFUND) vagy raktárba történő
        beszállításra (DEPOSIT) vonatkozik Indicating whether the the
        product fee summary concerns refund or deposit
    :ivar product_fee_data: Termékdíj adatok Product charges data
    :ivar product_charge_sum: Termékdíj összesen Aggregate product
        charges
    :ivar payment_evidence_document_data: A termékdíj bevallását igazoló
        dokumentum adatai a 2011. évi LXXXV. tv. 13. § (3) szerint és a
        25. § (3) szerint Data of the document verifying the declaration
        submitted on the product fee according to the Paragraph (3),
        Section 13 and the Paragraph (3) Section 25 of the Act LXXXV of
        2011
    """

    product_fee_operation: Optional[ProductFeeOperationType] = field(
        default=None,
        metadata={
            "name": "productFeeOperation",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
        },
    )
    product_fee_data: list[ProductFeeDataType] = field(
        default_factory=list,
        metadata={
            "name": "productFeeData",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "min_occurs": 1,
        },
    )
    product_charge_sum: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "productChargeSum",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "total_digits": 18,
            "fraction_digits": 2,
        },
    )
    payment_evidence_document_data: Optional[
        PaymentEvidenceDocumentDataType
    ] = field(
        default=None,
        metadata={
            "name": "paymentEvidenceDocumentData",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )


@dataclass
class SummaryNormalType:
    """
    Számla összesítés (nem egyszerűsített számla esetén) Calculation of invoice
    totals (not simplified invoice)

    :ivar summary_by_vat_rate: Összesítés ÁFA-mérték szerint Calculation
        of invoice totals per VAT rates
    :ivar invoice_net_amount: A számla nettó összege a számla
        pénznemében Net amount of the invoice expressed in the currency
        of the invoice
    :ivar invoice_net_amount_huf: A számla nettó összege forintban Net
        amount of the invoice expressed in HUF
    :ivar invoice_vat_amount: A számla ÁFA összege a számla pénznemében
        VAT amount of the invoice expressed in the currency of the
        invoice
    :ivar invoice_vat_amount_huf: A számla ÁFA összege forintban VAT
        amount of the invoice expressed in HUF
    """

    summary_by_vat_rate: list[SummaryByVatRateType] = field(
        default_factory=list,
        metadata={
            "name": "summaryByVatRate",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "min_occurs": 1,
        },
    )
    invoice_net_amount: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "invoiceNetAmount",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "total_digits": 18,
            "fraction_digits": 2,
        },
    )
    invoice_net_amount_huf: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "invoiceNetAmountHUF",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "total_digits": 18,
            "fraction_digits": 2,
        },
    )
    invoice_vat_amount: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "invoiceVatAmount",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "total_digits": 18,
            "fraction_digits": 2,
        },
    )
    invoice_vat_amount_huf: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "invoiceVatAmountHUF",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "total_digits": 18,
            "fraction_digits": 2,
        },
    )


@dataclass
class InvoiceHeadType:
    """
    Számla fejléc adatai Data in header of invoice.

    :ivar supplier_info: Számla kibocsátó (eladó) adatai Data related to
        the issuer of the invoice (supplier)
    :ivar customer_info: Vevő adatai Data related to the customer
    :ivar fiscal_representative_info: Pénzügyi képviselő adatai Data
        related to the fiscal representative
    :ivar invoice_detail: Számla részletező adatok Invoice detail adata
    """

    supplier_info: Optional[SupplierInfoType] = field(
        default=None,
        metadata={
            "name": "supplierInfo",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
        },
    )
    customer_info: Optional[CustomerInfoType] = field(
        default=None,
        metadata={
            "name": "customerInfo",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )
    fiscal_representative_info: Optional[FiscalRepresentativeType] = field(
        default=None,
        metadata={
            "name": "fiscalRepresentativeInfo",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )
    invoice_detail: Optional[InvoiceDetailType] = field(
        default=None,
        metadata={
            "name": "invoiceDetail",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
        },
    )


@dataclass
class LinesType:
    """
    Termék/szolgáltatás tételek Product / service items.

    :ivar merged_item_indicator: Jelöli, ha az adatszolgáltatás
        méretcsökkentés miatt összevont soradatokat tartalmaz Indicates
        whether the data exchange contains merged line data due to size
        reduction
    :ivar line: Termék/szolgáltatás tétel Product / service item
    """

    merged_item_indicator: Optional[bool] = field(
        default=None,
        metadata={
            "name": "mergedItemIndicator",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
        },
    )
    line: list[LineType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "min_occurs": 1,
        },
    )


@dataclass
class SummaryType:
    """
    Számla összesítés adatai Data of calculation of invoice totals.

    :ivar summary_normal: Számla összesítés (nem egyszerűsített számla
        esetén) Calculation of invoice totals (not simplified invoice)
    :ivar summary_simplified: Egyszerűsített számla összesítés
        Calculation of simplified invoice totals
    :ivar summary_gross_data: A számla összesítő bruttó adatai Gross
        data of the invoice summary
    """

    summary_normal: Optional[SummaryNormalType] = field(
        default=None,
        metadata={
            "name": "summaryNormal",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )
    summary_simplified: list[SummarySimplifiedType] = field(
        default_factory=list,
        metadata={
            "name": "summarySimplified",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )
    summary_gross_data: Optional[SummaryGrossDataType] = field(
        default=None,
        metadata={
            "name": "summaryGrossData",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )


@dataclass
class InvoiceType:
    """
    Egy számla vagy módosító okirat adatai Data of a single invoice or modification
    document.

    :ivar invoice_reference: A módosítás vagy érvénytelenítés adatai
        Modification or cancellation data
    :ivar invoice_head: A számla egészét jellemző adatok Data concerning
        the whole invoice
    :ivar invoice_lines: A számlán szereplő tételek adatai
        Product/service data appearing on the invoice
    :ivar product_fee_summary: Termékdíjjal kapcsolatos összesítő adatok
        Summary data of product charges
    :ivar invoice_summary: Az ÁFA törvény szerinti összesítő adatok
        Summary data according to VAT law
    """

    invoice_reference: Optional[InvoiceReferenceType] = field(
        default=None,
        metadata={
            "name": "invoiceReference",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )
    invoice_head: Optional[InvoiceHeadType] = field(
        default=None,
        metadata={
            "name": "invoiceHead",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
        },
    )
    invoice_lines: Optional[LinesType] = field(
        default=None,
        metadata={
            "name": "invoiceLines",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )
    product_fee_summary: list[ProductFeeSummaryType] = field(
        default_factory=list,
        metadata={
            "name": "productFeeSummary",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "max_occurs": 2,
        },
    )
    invoice_summary: Optional[SummaryType] = field(
        default=None,
        metadata={
            "name": "invoiceSummary",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
        },
    )


@dataclass
class BatchInvoiceType:
    """
    Kötegelt módosító okirat adatai Data of a batch of modification documents.

    :ivar batch_index: A módosító okirat sorszáma a kötegen belül
        Sequence number of the modification document within the batch
    :ivar invoice: Egy számla vagy módosító okirat adatai Data of a
        single invoice or modification document
    """

    batch_index: Optional[int] = field(
        default=None,
        metadata={
            "name": "batchIndex",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "min_inclusive": 1,
        },
    )
    invoice: Optional[InvoiceType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
        },
    )


@dataclass
class InvoiceMainType:
    """
    Számlaadatok leírására szolgáló közös típus A common type to describe invoice
    information.

    :ivar invoice: Egy számla vagy módosító okirat adatai Data of a
        single invoice or modification document
    :ivar batch_invoice: Kötegelt módosító okirat adatai Data of a batch
        of modification documents
    """

    invoice: Optional[InvoiceType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )
    batch_invoice: list[BatchInvoiceType] = field(
        default_factory=list,
        metadata={
            "name": "batchInvoice",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
        },
    )


@dataclass
class InvoiceDataType:
    """
    A számla adatszolgáltatás adatai Invoice exchange data.

    :ivar invoice_number: Számla vagy módosító okirat sorszáma - ÁFA tv.
        169. § b) vagy 170. § (1) bek. b) pont Sequential number of the
        original invoice or modification document - section 169 (b) or
        section 170 (1) b) of the VAT law
    :ivar invoice_issue_date: Számla vagy módosító okirat kelte - ÁFA
        tv. 169. § a), ÁFA tv. 170. § (1) bek. a) Date of issue of the
        invoice or the modification document - section 169 (a) of the
        VAT law, section 170 (1) a) of the VAT law
    :ivar completeness_indicator: Jelöli, ha az adatszolgáltatás maga a
        számla (a számlán nem szerepel több adat) Indicates whether the
        data exchange is identical with the invoice (the invoice does
        not contain any more data)
    :ivar invoice_main: Számlaadatok leírására szolgáló közös típus A
        common type to describe invoice information
    """

    invoice_number: Optional[str] = field(
        default=None,
        metadata={
            "name": "invoiceNumber",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "min_length": 1,
            "max_length": 50,
            "pattern": r".*[^\s].*",
        },
    )
    invoice_issue_date: Optional[str] = field(
        default=None,
        metadata={
            "name": "invoiceIssueDate",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
            "min_inclusive": "2010-01-01",
            "pattern": r"\d{4}-\d{2}-\d{2}",
        },
    )
    completeness_indicator: Optional[bool] = field(
        default=None,
        metadata={
            "name": "completenessIndicator",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
        },
    )
    invoice_main: Optional[InvoiceMainType] = field(
        default=None,
        metadata={
            "name": "invoiceMain",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/data",
            "required": True,
        },
    )


@dataclass
class InvoiceData(InvoiceDataType):
    """
    XML root element, számla vagy módosítás adatait leíró típus, amelyet BASE64
    kódoltan tartalmaz az invoiceApi sémaleíró invoiceData elementje XML root
    element, invoice or modification data type in BASE64 encoding, equivalent with
    the invoiceApi schema definition's invoiceData element.
    """

    class Meta:
        namespace = "http://schemas.nav.gov.hu/OSA/3.0/data"
