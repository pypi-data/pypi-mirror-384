from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

__NAMESPACE__ = "http://schemas.nav.gov.hu/OSA/3.0/annul"


class AnnulmentCodeType(Enum):
    """
    Technikai érvénytelenítés kód típusa Technical annulment code type.

    :cvar ERRATIC_DATA: Hibás adattartalom miatti technikai
        érvénytelenítés Technical annulment due to erratic data content
    :cvar ERRATIC_INVOICE_NUMBER: Hibás számlaszám miatti technikai
        érvénytelenítés Technical annulment due to erratic invoice
        number
    :cvar ERRATIC_INVOICE_ISSUE_DATE: Hibás számla kiállítási dátum
        miatti technikai érvénytelenítés Technical annulment due to
        erratic invoice issue date
    :cvar ERRATIC_ELECTRONIC_HASH_VALUE: Hibás elektronikus számla hash
        érték miatti technikai érvénytelenítés Technical annulment due
        to erratic electronic invoice hash value
    """

    ERRATIC_DATA = "ERRATIC_DATA"
    ERRATIC_INVOICE_NUMBER = "ERRATIC_INVOICE_NUMBER"
    ERRATIC_INVOICE_ISSUE_DATE = "ERRATIC_INVOICE_ISSUE_DATE"
    ERRATIC_ELECTRONIC_HASH_VALUE = "ERRATIC_ELECTRONIC_HASH_VALUE"


@dataclass
class InvoiceAnnulmentType:
    """
    Korábbi adatszolgáltatás technikai érvénytelenítésének adatai Data of technical
    annulment concerning previous data exchange.

    :ivar annulment_reference: A technikai érvénytelenítéssel érintett
        számla vagy módosító okirat sorszáma Sequential number of the
        invoice or modification document to be annuled
    :ivar annulment_timestamp: A technikai érvénytelenítés időbélyege a
        forrásrendszerben UTC idő szerint Timestamp of the technical
        annulment in UTC time
    :ivar annulment_code: A technikai érvénytelenítés kódja Technical
        annulment code
    :ivar annulment_reason: A technikai érvénytelenítés oka Technical
        annulment reason
    """

    annulment_reference: Optional[str] = field(
        default=None,
        metadata={
            "name": "annulmentReference",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/annul",
            "required": True,
            "min_length": 1,
            "max_length": 50,
            "pattern": r".*[^\s].*",
        },
    )
    annulment_timestamp: Optional[str] = field(
        default=None,
        metadata={
            "name": "annulmentTimestamp",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/annul",
            "required": True,
            "min_inclusive": "2010-01-01T00:00:00Z",
            "pattern": r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(.\d{1,3})?Z",
        },
    )
    annulment_code: Optional[AnnulmentCodeType] = field(
        default=None,
        metadata={
            "name": "annulmentCode",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/annul",
            "required": True,
        },
    )
    annulment_reason: Optional[str] = field(
        default=None,
        metadata={
            "name": "annulmentReason",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/annul",
            "required": True,
            "min_length": 1,
            "max_length": 1024,
            "pattern": r".*[^\s].*",
        },
    )


@dataclass
class InvoiceAnnulment(InvoiceAnnulmentType):
    """
    XML root element, a technikai érvénytelenítés adatait leíró típus, amelyet
    BASE64 kódoltan tartalmaz az invoiceApi sémaleíró invoiceAnnulment elementje
    XML root element, technical annulment data type in BASE64 encoding, equivalent
    with the invoiceApi schema definition's invoiceAnnulment element.
    """

    class Meta:
        namespace = "http://schemas.nav.gov.hu/OSA/3.0/annul"
