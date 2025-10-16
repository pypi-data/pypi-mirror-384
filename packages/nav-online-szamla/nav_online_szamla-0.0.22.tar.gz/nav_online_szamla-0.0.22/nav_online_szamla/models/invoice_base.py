from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

__NAMESPACE__ = "http://schemas.nav.gov.hu/OSA/3.0/base"


@dataclass
class DetailedAddressType:
    """
    Részletes címadatok Detailed address data.

    :ivar country_code: Az országkód ISO 3166 alpha-2 szabvány szerint
        ISO 3166 alpha-2 country code
    :ivar region: Tartomány kódja (amennyiben értelmezhető az adott
        országban) az ISO 3166-2 alpha 2 szabvány szerint ISO 3166
        alpha-2 province code (if appropriate in a given country)
    :ivar postal_code: Irányítószám (amennyiben nem értelmezhető, 0000
        értékkel kell kitölteni) ZIP code (If can not be interpreted,
        need to be filled "0000")
    :ivar city: Település Settlement
    :ivar street_name: Közterület neve Name of public place
    :ivar public_place_category: Közterület jellege Category of public
        place
    :ivar number: Házszám House number
    :ivar building: Épület Building
    :ivar staircase: Lépcsőház Staircase
    :ivar floor: Emelet Floor
    :ivar door: Ajtó Door number
    :ivar lot_number: Helyrajzi szám Lot number
    """

    country_code: Optional[str] = field(
        default=None,
        metadata={
            "name": "countryCode",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/base",
            "required": True,
            "min_length": 1,
            "max_length": 2,
            "length": 2,
            "pattern": r"[A-Z]{2}",
        },
    )
    region: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/base",
            "min_length": 1,
            "max_length": 50,
            "pattern": r".*[^\s].*",
        },
    )
    postal_code: Optional[str] = field(
        default=None,
        metadata={
            "name": "postalCode",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/base",
            "required": True,
            "min_length": 3,
            "max_length": 10,
            "pattern": r"[A-Z0-9][A-Z0-9\s\-]{1,8}[A-Z0-9]",
        },
    )
    city: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/base",
            "required": True,
            "min_length": 1,
            "max_length": 255,
            "pattern": r".*[^\s].*",
        },
    )
    street_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "streetName",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/base",
            "required": True,
            "min_length": 1,
            "max_length": 255,
            "pattern": r".*[^\s].*",
        },
    )
    public_place_category: Optional[str] = field(
        default=None,
        metadata={
            "name": "publicPlaceCategory",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/base",
            "required": True,
            "min_length": 1,
            "max_length": 50,
            "pattern": r".*[^\s].*",
        },
    )
    number: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/base",
            "min_length": 1,
            "max_length": 50,
            "pattern": r".*[^\s].*",
        },
    )
    building: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/base",
            "min_length": 1,
            "max_length": 50,
            "pattern": r".*[^\s].*",
        },
    )
    staircase: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/base",
            "min_length": 1,
            "max_length": 50,
            "pattern": r".*[^\s].*",
        },
    )
    floor: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/base",
            "min_length": 1,
            "max_length": 50,
            "pattern": r".*[^\s].*",
        },
    )
    door: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/base",
            "min_length": 1,
            "max_length": 50,
            "pattern": r".*[^\s].*",
        },
    )
    lot_number: Optional[str] = field(
        default=None,
        metadata={
            "name": "lotNumber",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/base",
            "min_length": 1,
            "max_length": 50,
            "pattern": r".*[^\s].*",
        },
    )


class InvoiceAppearanceType(Enum):
    """
    Számla megjelenési formája típus Form of appearance of the invoice type.

    :cvar PAPER: Papír alapú számla Invoice issued on paper
    :cvar ELECTRONIC: Elektronikus formában előállított, nem EDI számla
        Electronic invoice (non-EDI)
    :cvar EDI: EDI számla EDI invoice
    :cvar UNKNOWN: A szoftver nem képes azonosítani vagy a kiállításkor
        nem ismert The software cannot be identify the form of
        appearance of the invoice or it is unknown at the time of issue
    """

    PAPER = "PAPER"
    ELECTRONIC = "ELECTRONIC"
    EDI = "EDI"
    UNKNOWN = "UNKNOWN"


class InvoiceCategoryType(Enum):
    """
    A számla típusa Type of invoice.

    :cvar NORMAL: Normál (nem egyszerűsített és nem gyűjtő) számla
        Normal (not simplified and not aggregate) invoice
    :cvar SIMPLIFIED: Egyszerűsített számla Simplified invoice
    :cvar AGGREGATE: Gyűjtőszámla Aggregate invoice
    """

    NORMAL = "NORMAL"
    SIMPLIFIED = "SIMPLIFIED"
    AGGREGATE = "AGGREGATE"


class PaymentMethodType(Enum):
    """
    Fizetés módja Method of payment.

    :cvar TRANSFER: Banki átutalás Bank transfer
    :cvar CASH: Készpénz Cash
    :cvar CARD: Bankkártya, hitelkártya, egyéb készpénz helyettesítő
        eszköz Debit card, credit card, other cash-substitute payment
        instrument
    :cvar VOUCHER: Utalvány, váltó, egyéb pénzhelyettesítő eszköz
        Voucher, bill of exchange, other non-cash payment instrument
    :cvar OTHER: Egyéb Other
    """

    TRANSFER = "TRANSFER"
    CASH = "CASH"
    CARD = "CARD"
    VOUCHER = "VOUCHER"
    OTHER = "OTHER"


@dataclass
class SimpleAddressType:
    """
    Egyszerű címtípus Simple address type.

    :ivar country_code: Az országkód az ISO 3166 alpha-2 szabvány
        szerint ISO 3166 alpha-2 country code
    :ivar region: Tartomány kódja (amennyiben értelmezhető az adott
        országban) az ISO 3166-2 alpha 2 szabvány szerint ISO 3166
        alpha-2 province code (if appropriate in a given country)
    :ivar postal_code: Irányítószám (amennyiben nem értelmezhető, 0000
        értékkel kell kitölteni) ZIP code (If can not be interpreted,
        need to be filled "0000")
    :ivar city: Település Settlement
    :ivar additional_address_detail: További címadatok (pl. közterület
        neve és jellege, házszám, emelet, ajtó, helyrajzi szám, stb.)
        Further address data (name and type of public place, house
        number, floor, door, lot number, etc.)
    """

    country_code: Optional[str] = field(
        default=None,
        metadata={
            "name": "countryCode",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/base",
            "required": True,
            "min_length": 1,
            "max_length": 2,
            "length": 2,
            "pattern": r"[A-Z]{2}",
        },
    )
    region: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/base",
            "min_length": 1,
            "max_length": 50,
            "pattern": r".*[^\s].*",
        },
    )
    postal_code: Optional[str] = field(
        default=None,
        metadata={
            "name": "postalCode",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/base",
            "required": True,
            "min_length": 3,
            "max_length": 10,
            "pattern": r"[A-Z0-9][A-Z0-9\s\-]{1,8}[A-Z0-9]",
        },
    )
    city: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/base",
            "required": True,
            "min_length": 1,
            "max_length": 255,
            "pattern": r".*[^\s].*",
        },
    )
    additional_address_detail: Optional[str] = field(
        default=None,
        metadata={
            "name": "additionalAddressDetail",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/base",
            "required": True,
            "min_length": 1,
            "max_length": 255,
            "pattern": r".*[^\s].*",
        },
    )


@dataclass
class TaxNumberType:
    """
    Adószám típus Tax number type.

    :ivar taxpayer_id: Az adóalany adó törzsszáma. Csoportos adóalany
        esetén csoportazonosító szám Core tax number of the taxable
        person. In case of group taxation arrangement the group
        identification number
    :ivar vat_code: ÁFA kód az adóalanyiság típusának jelzésére. Egy
        számjegy VAT code to indicate taxation type of the taxpayer. One
        digit
    :ivar county_code: Megyekód, két számjegy County code, two digits
    """

    taxpayer_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "taxpayerId",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/base",
            "required": True,
            "min_length": 1,
            "max_length": 8,
            "length": 8,
            "pattern": r"[0-9]{8}",
        },
    )
    vat_code: Optional[str] = field(
        default=None,
        metadata={
            "name": "vatCode",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/base",
            "min_length": 1,
            "max_length": 2,
            "length": 1,
            "pattern": r"[1-5]{1}",
        },
    )
    county_code: Optional[str] = field(
        default=None,
        metadata={
            "name": "countyCode",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/base",
            "min_length": 1,
            "max_length": 2,
            "length": 2,
            "pattern": r"[0-9]{2}",
        },
    )


@dataclass
class AddressType:
    """
    Cím típus, amely vagy egyszerű, vagy részletes címet tartalmaz Format of
    address that includes either a simple or a detailed address.

    :ivar simple_address: Egyszerű cím Simple address
    :ivar detailed_address: Részletes cím Detailed address
    """

    simple_address: Optional[SimpleAddressType] = field(
        default=None,
        metadata={
            "name": "simpleAddress",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/base",
        },
    )
    detailed_address: Optional[DetailedAddressType] = field(
        default=None,
        metadata={
            "name": "detailedAddress",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/base",
        },
    )
