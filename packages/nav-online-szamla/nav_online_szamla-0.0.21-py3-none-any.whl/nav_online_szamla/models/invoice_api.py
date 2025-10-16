from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Optional

from xsdata.models.datatype import XmlDateTime

from nav_online_szamla.models.common import (
    BasicRequestType,
    BasicResponseType,
    BusinessResultCodeType,
    CryptoType,
    GeneralErrorHeaderResponseType,
    TechnicalValidationResultType,
)
from nav_online_szamla.models.invoice_base import (
    DetailedAddressType,
    InvoiceAppearanceType,
    InvoiceCategoryType,
    PaymentMethodType,
    TaxNumberType,
)

__NAMESPACE__ = "http://schemas.nav.gov.hu/OSA/3.0/api"


class AnnulmentVerificationStatusType(Enum):
    """
    Technikai érvénytelenítő kérések jóváhagyási státusza Verification status of
    technical annulment requests.

    :cvar NOT_VERIFIABLE: A technikai érvénytelenítés kliens hiba miatt
        nem hagyható jóvá The technical annulment is not verifiable due
        to client error
    :cvar VERIFICATION_PENDING: A technikai érvénytelenítés jóváhagyásra
        vár The technical annulment is awaiting verification
    :cvar VERIFICATION_DONE: A technikai érvénytelenítés jóváhagyásra
        került The technical annulment has been verified
    :cvar VERIFICATION_REJECTED: A technikai érvénytelenítés
        elutasításra került The technical annulment has been rejected
    """

    NOT_VERIFIABLE = "NOT_VERIFIABLE"
    VERIFICATION_PENDING = "VERIFICATION_PENDING"
    VERIFICATION_DONE = "VERIFICATION_DONE"
    VERIFICATION_REJECTED = "VERIFICATION_REJECTED"


@dataclass
class DateIntervalParamType:
    """
    Dátumos számla kereső paraméter Date query params of invoice.

    :ivar date_from: Dátum intervallum nagyobb vagy egyenlő paramétere
        Date interval greater or equals parameter
    :ivar date_to: Dátum intervallum kisebb vagy egyenlő paramétere Date
        interval less or equals parameter
    """

    date_from: Optional[str] = field(
        default=None,
        metadata={
            "name": "dateFrom",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
            "min_inclusive": "2010-01-01",
            "pattern": r"\d{4}-\d{2}-\d{2}",
        },
    )
    date_to: Optional[str] = field(
        default=None,
        metadata={
            "name": "dateTo",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
            "min_inclusive": "2010-01-01",
            "pattern": r"\d{4}-\d{2}-\d{2}",
        },
    )


@dataclass
class DateTimeIntervalParamType:
    """
    Időpontos számla kereső paraméter Datestamp query params of invoice.

    :ivar date_time_from: Időpontos intervallum nagyobb vagy egyenlő
        paramétere UTC idő szerint Datetime interval greater or equals
        parameter
    :ivar date_time_to: Időpontos intervallum kisebb vagy egyenlő
        paramétere UTC idő szerint Datetime interval less or equals
        parameter
    """

    date_time_from: Optional[str] = field(
        default=None,
        metadata={
            "name": "dateTimeFrom",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
            "min_inclusive": "2010-01-01T00:00:00Z",
            "pattern": r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(.\d{1,3})?Z",
        },
    )
    date_time_to: Optional[str] = field(
        default=None,
        metadata={
            "name": "dateTimeTo",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
            "min_inclusive": "2010-01-01T00:00:00Z",
            "pattern": r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(.\d{1,3})?Z",
        },
    )


class IncorporationType(Enum):
    """
    Gazdasági típus Incorporation type.

    :cvar ORGANIZATION: Gazdasági társaság Economical company
    :cvar SELF_EMPLOYED: Egyéni vállalkozó Self employed private
        entrepreneur
    :cvar TAXABLE_PERSON: Adószámos magánszemély Private person with tax
        number
    """

    ORGANIZATION = "ORGANIZATION"
    SELF_EMPLOYED = "SELF_EMPLOYED"
    TAXABLE_PERSON = "TAXABLE_PERSON"


class InvoiceDirectionType(Enum):
    """
    Kimenő vagy bejövő számla keresési paramétere Inbound or outbound invoice query
    parameter.

    :cvar INBOUND: Bejövő (vevő oldali) számla keresési paramétere
        Inbound (customer side) invoice query parameter
    :cvar OUTBOUND: Kimenő (kiállító oldali) számla keresési paramétere
        Outbound (supplier side) invoice query parameter
    """

    INBOUND = "INBOUND"
    OUTBOUND = "OUTBOUND"


@dataclass
class InvoiceReferenceDataType:
    """
    A módosítás vagy érvénytelenítés adatai Modification or cancellation data.

    :ivar original_invoice_number: Az eredeti számla sorszáma, melyre a
        módosítás vonatkozik  - ÁFA tv. 170. § (1) c) Sequence number of
        the original invoice, on which the modification occurs - section
        170 (1) c) of the VAT law
    :ivar modify_without_master: Annak jelzése, hogy a módosítás olyan
        alapszámlára hivatkozik, amelyről nem történt és nem is fog
        történni adatszolgáltatás Indicates whether the modification
        references to an original invoice which is not and will not be
        exchanged
    :ivar modification_timestamp: A módosító okirat készítésének
        időbélyege a forrásrendszerben UTC időben Creation date
        timestamp of the modification document in UTC time
    :ivar modification_index: A számlára vonatkozó módosító okirat
        egyedi sorszáma The unique sequence number referring to the
        original invoice
    """

    original_invoice_number: Optional[str] = field(
        default=None,
        metadata={
            "name": "originalInvoiceNumber",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
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
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
        },
    )
    modification_timestamp: Optional[str] = field(
        default=None,
        metadata={
            "name": "modificationTimestamp",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "min_inclusive": "2010-01-01T00:00:00Z",
            "pattern": r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(.\d{1,3})?Z",
        },
    )
    modification_index: Optional[int] = field(
        default=None,
        metadata={
            "name": "modificationIndex",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "min_inclusive": 1,
        },
    )


class InvoiceStatusType(Enum):
    """
    A számla feldolgozási státusza Processing status of the invoice.

    :cvar RECEIVED: Befogadva Received
    :cvar PROCESSING: Feldolgozás alatt Processing
    :cvar SAVED: Elmentve Saved
    :cvar DONE: Kész Done
    :cvar ABORTED: Kihagyva Aborted
    """

    RECEIVED = "RECEIVED"
    PROCESSING = "PROCESSING"
    SAVED = "SAVED"
    DONE = "DONE"
    ABORTED = "ABORTED"


class ManageAnnulmentOperationType(Enum):
    """
    Technikai érvénytelenítés műveleti típus Technical annulment operation type.

    :cvar ANNUL: Korábbi adatszolgáltatás technikai érvénytelenítése
        Technical annulment of previous exchange
    """

    ANNUL = "ANNUL"


class ManageInvoiceOperationType(Enum):
    """
    Számlaművelet típus Invoice operation type.

    :cvar CREATE: Adatszolgáltatás eredeti számláról Original invoice
        exchange
    :cvar MODIFY: Adatszolgáltatás az eredeti számlát módosító okiratról
        Modification invoice exchange
    :cvar STORNO: Adatszolgáltatás az eredeti számla érvénytelenítéséről
        Exchange concerning invoice invalidation
    """

    CREATE = "CREATE"
    MODIFY = "MODIFY"
    STORNO = "STORNO"


@dataclass
class NewCreatedLinesType:
    """
    A módosító okirat által újként létrehozott számlasorok New invoice lines
    created by the modification document.

    :ivar line_number_interval_start: Számla sor intervallum kezdete
        Invoice line interval start
    :ivar line_number_interval_end: Számla sor intervallum vége
        (inkluzív) Invoice line interval end (inclusive)
    """

    line_number_interval_start: Optional[int] = field(
        default=None,
        metadata={
            "name": "lineNumberIntervalStart",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
            "min_inclusive": 1,
            "total_digits": 20,
        },
    )
    line_number_interval_end: Optional[int] = field(
        default=None,
        metadata={
            "name": "lineNumberIntervalEnd",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
            "min_inclusive": 1,
            "total_digits": 20,
        },
    )


class OriginalRequestVersionType(Enum):
    """
    A lekérdezett számla requestVersion értéke Request version value of the queried
    invoice.
    """

    VALUE_1_0 = "1.0"
    VALUE_1_1 = "1.1"
    VALUE_2_0 = "2.0"
    VALUE_3_0 = "3.0"


@dataclass
class PointerType:
    """
    Feldolgozási kurzor adatok Processing cursor data.

    :ivar tag: Tag hivatkozás Tag reference
    :ivar value: Érték hivatkozás Value reference
    :ivar line: Sorhivatkozás Line reference
    :ivar original_invoice_number: Kötegelt számla művelet esetén az
        eredeti számla sorszáma, melyre a módosítás vonatkozik In case
        of a batch operation, the sequence number of the original
        invoice, on which the modification occurs
    """

    tag: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "min_length": 1,
            "max_length": 1024,
            "pattern": r".*[^\s].*",
        },
    )
    value: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "min_length": 1,
            "max_length": 1024,
            "pattern": r".*[^\s].*",
        },
    )
    line: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "min_inclusive": 1,
            "total_digits": 20,
        },
    )
    original_invoice_number: Optional[str] = field(
        default=None,
        metadata={
            "name": "originalInvoiceNumber",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "min_length": 1,
            "max_length": 50,
            "pattern": r".*[^\s].*",
        },
    )


class QueryOperatorType(Enum):
    """
    Relációs művelet típus Relational operator type.

    :cvar EQ: Egyenlőség Equals
    :cvar GT: Nagyobb mint reláció Greater than relation
    :cvar GTE: Nagyobb vagy egyenlő reláció Greater or equals relation
    :cvar LT: Kisebb mint reláció Less than relation
    :cvar LTE: Kisebb vagy egyenlő reláció Less or equals relation
    """

    EQ = "EQ"
    GT = "GT"
    GTE = "GTE"
    LT = "LT"
    LTE = "LTE"


class RequestStatusType(Enum):
    """
    A kérés feldolgozási státusza Processing status of the request.

    :cvar RECEIVED: Befogadva Received
    :cvar PROCESSING: Feldolgozás alatt Processing
    :cvar SAVED: Elmentve Saved
    :cvar FINISHED: Feldolgozás befejezve Finished processing
    :cvar NOTIFIED: Lekérdezve Notified
    """

    RECEIVED = "RECEIVED"
    PROCESSING = "PROCESSING"
    SAVED = "SAVED"
    FINISHED = "FINISHED"
    NOTIFIED = "NOTIFIED"


class SoftwareOperationType(Enum):
    """
    A számlázóprogram működési típusa (lokális program vagy online számlázó
    szolgáltatás) Billing operation type (local program or online billing service)

    :cvar LOCAL_SOFTWARE: Lokális program Local program
    :cvar ONLINE_SERVICE: Online számlázó szolgáltatás Online billing
        service
    """

    LOCAL_SOFTWARE = "LOCAL_SOFTWARE"
    ONLINE_SERVICE = "ONLINE_SERVICE"


class SourceType(Enum):
    """
    Az adatszolgáltatás forrása Data exchange source.

    :cvar WEB: Webes adatszolgáltatás Web exchange
    :cvar XML: Kézi XML feltöltés Manual XML upload
    :cvar MGM: Gép-gép adatkapcsolati adatszolgáltatás Machine-to-
        machine exchange
    :cvar OPG: Online pénztárgépes adatszolgáltatás Online cash register
        exchange
    :cvar OSZ: NAV online számlázó NTCA online invoicing
    """

    WEB = "WEB"
    XML = "XML"
    MGM = "MGM"
    OPG = "OPG"
    OSZ = "OSZ"


class TaxpayerAddressTypeType(Enum):
    """
    Adózói cím típus Taxpayer address type.

    :cvar HQ: Székhely Headquarter
    :cvar SITE: Telephely Site office
    :cvar BRANCH: Fióktelep Branch office
    """

    HQ = "HQ"
    SITE = "SITE"
    BRANCH = "BRANCH"


@dataclass
class AdditionalQueryParamsType:
    """
    A számla lekérdezés kiegészítő paraméterei Additional params of the invoice
    query.

    :ivar tax_number: A számla kiállítójának vagy vevőjének adószáma (a
        keresési feltétel az invoiceDirection tag értékétől függ) Tax
        number of the supplier or the customer of the invoice (the
        search criteria depends on the value of the invoiceDirection
        tag)
    :ivar group_member_tax_number: A számla kiállítójának vagy vevőjének
        csoport tag adószáma (a keresési feltétel az invoiceDirection
        tag értékétől függ) Tax number of group member of the supplier
        or the customer of the invoice (the search criteria depends on
        the value of the invoiceDirection tag)
    :ivar name: A számla kiállítójának vagy vevőjének keresőparamétere
        szó eleji egyezőségre (a keresési feltétel az invoiceDirection
        tag értékétől függ) Query param of the supplier or the customer
        of the invoice for leading match pattern (the search criteria
        depends on the value of the invoiceDirection tag)
    :ivar invoice_category: A számla típusa Type of invoice
    :ivar payment_method: Fizetés módja Method of payment
    :ivar invoice_appearance: A számla megjelenési formája Form of
        appearance of the invoice
    :ivar source: Az adatszolgáltatás forrása Data exchange source
    :ivar currency: A számla pénzneme Currency of the invoice
    """

    tax_number: Optional[str] = field(
        default=None,
        metadata={
            "name": "taxNumber",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "min_length": 1,
            "max_length": 8,
            "length": 8,
            "pattern": r"[0-9]{8}",
        },
    )
    group_member_tax_number: Optional[str] = field(
        default=None,
        metadata={
            "name": "groupMemberTaxNumber",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "min_length": 1,
            "max_length": 8,
            "length": 8,
            "pattern": r"[0-9]{8}",
        },
    )
    name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "min_length": 5,
            "max_length": 512,
            "pattern": r".*[^\s].*",
        },
    )
    invoice_category: Optional[InvoiceCategoryType] = field(
        default=None,
        metadata={
            "name": "invoiceCategory",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
        },
    )
    payment_method: Optional[PaymentMethodType] = field(
        default=None,
        metadata={
            "name": "paymentMethod",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
        },
    )
    invoice_appearance: Optional[InvoiceAppearanceType] = field(
        default=None,
        metadata={
            "name": "invoiceAppearance",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
        },
    )
    source: Optional[SourceType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
        },
    )
    currency: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "min_length": 1,
            "max_length": 4,
            "length": 3,
            "pattern": r"[A-Z]{3}",
        },
    )


@dataclass
class AnnulmentDataType:
    """
    Technikai érvénytelenítés státusz adatai Status data of technical annulment.

    :ivar annulment_verification_status: Technikai érvénytelenítő
        kérések jóváhagyási státusza Verification status of technical
        annulment requests
    :ivar annulment_decision_date: A technikai érvénytelenítés
        jóváhagyásának vagy elutasításának időpontja UTC időben Date of
        verification or rejection of the technical annulment in UTC time
    :ivar annulment_decision_user: A technikai érvénytelenítést
        jóváhagyó vagy elutasító felhasználó neve Login name of the user
        deciding over the technical annulment's verification or
        rejection
    """

    annulment_verification_status: Optional[
        AnnulmentVerificationStatusType
    ] = field(
        default=None,
        metadata={
            "name": "annulmentVerificationStatus",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
        },
    )
    annulment_decision_date: Optional[str] = field(
        default=None,
        metadata={
            "name": "annulmentDecisionDate",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "min_inclusive": "2010-01-01T00:00:00Z",
            "pattern": r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(.\d{1,3})?Z",
        },
    )
    annulment_decision_user: Optional[str] = field(
        default=None,
        metadata={
            "name": "annulmentDecisionUser",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "min_length": 6,
            "max_length": 15,
            "pattern": r"[a-zA-Z0-9]{6,15}",
        },
    )


@dataclass
class AnnulmentOperationType:
    """
    A kéréshez tartozó technikai érvénytelenítő művelet Technical annulment
    operation of the request.

    :ivar index: A technikai érvénytelenítés sorszáma a kérésen belül
        Sequence number of the technical annulment within the request
    :ivar annulment_operation: A kért technikai érvénytelenítés művelet
        típusa Type of the desired technical annulment operation
    :ivar invoice_annulment: Technikai érvénytelenítés adatok BASE64-ben
        kódolt tartalma Technical annulment data in BASE64 encoded form
    """

    index: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
            "min_inclusive": 1,
            "max_inclusive": 100,
        },
    )
    annulment_operation: Optional[ManageAnnulmentOperationType] = field(
        default=None,
        metadata={
            "name": "annulmentOperation",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
        },
    )
    invoice_annulment: Optional[bytes] = field(
        default=None,
        metadata={
            "name": "invoiceAnnulment",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
            "format": "base64",
        },
    )


@dataclass
class AuditDataType:
    """
    A számla audit adatai Invoice audit data.

    :ivar insdate: A beszúrás időpontja UTC időben Insert date in UTC
        time
    :ivar ins_cus_user: A beszúrást végző technikai felhasználó
        Inserting technical user name
    :ivar source: Az adatszolgáltatás forrása Data exchange source
    :ivar transaction_id: A számla tranzakció azonosítója, ha az gépi
        interfészen került beküldésre Transaction ID of the invoice if
        it was exchanged via M2M interface
    :ivar index: A számla sorszáma a kérésen belül Sequence number of
        the invoice within the request
    :ivar batch_index: A módosító okirat sorszáma a kötegen belül
        Sequence number of the modification document within the batch
    :ivar original_request_version: Az adatszolgáltatás requestVersion
        értéke requestVersion value of the invoice exchange
    """

    insdate: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
            "min_inclusive": "2010-01-01T00:00:00Z",
            "pattern": r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(.\d{1,3})?Z",
        },
    )
    ins_cus_user: Optional[str] = field(
        default=None,
        metadata={
            "name": "insCusUser",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
            "min_length": 6,
            "max_length": 15,
            "pattern": r"[a-zA-Z0-9]{6,15}",
        },
    )
    source: Optional[SourceType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
        },
    )
    transaction_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "transactionId",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "min_length": 1,
            "max_length": 30,
            "pattern": r"[+a-zA-Z0-9_]{1,30}",
        },
    )
    index: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "min_inclusive": 1,
            "max_inclusive": 100,
        },
    )
    batch_index: Optional[int] = field(
        default=None,
        metadata={
            "name": "batchIndex",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "min_inclusive": 1,
        },
    )
    original_request_version: Optional[OriginalRequestVersionType] = field(
        default=None,
        metadata={
            "name": "originalRequestVersion",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
        },
    )


@dataclass
class BusinessValidationResultType:
    """
    Üzleti validációs választípus Business validation response type.

    :ivar validation_result_code: Validációs eredmény Validation result
    :ivar validation_error_code: Validációs hibakód Validation error
        code
    :ivar message: Feldolgozási üzenet Processing message
    :ivar pointer: Feldolgozási kurzor adatok Processing cursor data
    """

    validation_result_code: Optional[BusinessResultCodeType] = field(
        default=None,
        metadata={
            "name": "validationResultCode",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
        },
    )
    validation_error_code: Optional[str] = field(
        default=None,
        metadata={
            "name": "validationErrorCode",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "min_length": 1,
            "max_length": 100,
            "pattern": r".*[^\s].*",
        },
    )
    message: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "min_length": 1,
            "max_length": 512,
            "pattern": r".*[^\s].*",
        },
    )
    pointer: Optional[PointerType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
        },
    )


@dataclass
class InvoiceChainDigestType:
    """
    Számlalánc kivonat adatok Invoice chain digest data.

    :ivar invoice_number: Számla vagy módosító okirat sorszáma - ÁFA tv.
        169. § b) vagy 170. § (1) bek. b) pont Sequential number of the
        original invoice or modification document - section 169 (b) or
        section 170 (1) b) of the VAT law
    :ivar batch_index: A módosító okirat sorszáma a kötegen belül
        Sequence number of the modification document within the batch
    :ivar invoice_operation: Számlaművelet típus Invoice operation type
    :ivar supplier_tax_number: A kibocsátó adószáma The supplier's tax
        number
    :ivar customer_tax_number: A vevő adószáma The buyer's tax number
    :ivar ins_date: A beszúrás időpontja UTC időben Insert date in UTC
        time
    :ivar original_request_version: Az adatszolgáltatás requestVersion
        értéke requestVersion value of the invoice exchange
    """

    invoice_number: Optional[str] = field(
        default=None,
        metadata={
            "name": "invoiceNumber",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
            "min_length": 1,
            "max_length": 50,
            "pattern": r".*[^\s].*",
        },
    )
    batch_index: Optional[int] = field(
        default=None,
        metadata={
            "name": "batchIndex",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "min_inclusive": 1,
        },
    )
    invoice_operation: Optional[ManageInvoiceOperationType] = field(
        default=None,
        metadata={
            "name": "invoiceOperation",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
        },
    )
    supplier_tax_number: Optional[str] = field(
        default=None,
        metadata={
            "name": "supplierTaxNumber",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
            "min_length": 1,
            "max_length": 8,
            "length": 8,
            "pattern": r"[0-9]{8}",
        },
    )
    customer_tax_number: Optional[str] = field(
        default=None,
        metadata={
            "name": "customerTaxNumber",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "min_length": 1,
            "max_length": 8,
            "length": 8,
            "pattern": r"[0-9]{8}",
        },
    )
    ins_date: Optional[str] = field(
        default=None,
        metadata={
            "name": "insDate",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
            "min_inclusive": "2010-01-01T00:00:00Z",
            "pattern": r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(.\d{1,3})?Z",
        },
    )
    original_request_version: Optional[OriginalRequestVersionType] = field(
        default=None,
        metadata={
            "name": "originalRequestVersion",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
        },
    )


@dataclass
class InvoiceChainQueryType:
    """
    Számlalánc kivonat lekérdezés számlaszám paramétere Invoice number param of the
    invoice chain digest query.

    :ivar invoice_number: Számla vagy módosító okirat sorszáma
        Sequential number of the original or modification invoice
    :ivar invoice_direction: Kimenő vagy bejövő számla keresési
        paramétere Inbound or outbound invoice query parameter
    :ivar tax_number: A számla kiállítójának vagy vevőjének adószáma (a
        keresési feltétel az invoiceDirection tag értékétől függ) Tax
        number of the supplier or the customer of the invoice (the
        search criteria depends on the value of the invoiceDirection
        tag)
    """

    invoice_number: Optional[str] = field(
        default=None,
        metadata={
            "name": "invoiceNumber",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
            "min_length": 1,
            "max_length": 50,
            "pattern": r".*[^\s].*",
        },
    )
    invoice_direction: Optional[InvoiceDirectionType] = field(
        default=None,
        metadata={
            "name": "invoiceDirection",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
        },
    )
    tax_number: Optional[str] = field(
        default=None,
        metadata={
            "name": "taxNumber",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "min_length": 1,
            "max_length": 8,
            "length": 8,
            "pattern": r"[0-9]{8}",
        },
    )


@dataclass
class InvoiceDigestType:
    """
    Kivonatos lekérdezési eredmény Digest query result.

    :ivar invoice_number: Számla vagy módosító okirat sorszáma - ÁFA tv.
        169. § b) vagy 170. § (1) bek. b) pont Sequential number of the
        original invoice or modification document - section 169 (b) or
        section 170 (1) b) of the VAT law
    :ivar batch_index: A módosító okirat sorszáma a kötegen belül
        Sequence number of the modification document within the batch
    :ivar invoice_operation: Számlaművelet típus Invoice operation type
    :ivar invoice_category: A számla típusa Type of invoice
    :ivar invoice_issue_date: Számla vagy módosító okirat kiállításának
        dátuma Invoice or modification document issue date
    :ivar supplier_tax_number: A kibocsátó adószáma The supplier's tax
        number
    :ivar supplier_group_member_tax_number: A kibocsátó csoporttag száma
        The supplier's group tax number
    :ivar supplier_name: Az eladó (szállító) neve Name of the seller
        (supplier)
    :ivar customer_tax_number: A vevő adószáma The buyer's tax number
    :ivar customer_group_member_tax_number: A vevő csoporttag száma The
        buyer's group tax number
    :ivar customer_name: A vevő neve Name of the customer
    :ivar payment_method: Fizetés módja Method of payment
    :ivar payment_date: Fizetési határidő Deadline for payment
    :ivar invoice_appearance: A számla megjelenési formája Form of
        appearance of the invoice
    :ivar source: Az adatszolgáltatás forrása Data exchange source
    :ivar invoice_delivery_date: Számla teljesítési dátuma Invoice
        delivery date
    :ivar currency: A számla pénzneme Currency of the invoice
    :ivar invoice_net_amount: A számla nettó összege a számla
        pénznemében Invoice net amount expressed in the currency of the
        invoice
    :ivar invoice_net_amount_huf: A számla nettó összege forintban
        Invoice net amount expressed in HUF
    :ivar invoice_vat_amount: A számla ÁFA összege a számla pénznemében
        Invoice VAT amount expressed in the currency of the invoice
    :ivar invoice_vat_amount_huf: A számla ÁFA összege forintban Invoice
        VAT amount expressed in HUF
    :ivar transaction_id: Az adatszolgáltatás tranzakció azonosítója
        Transaction identifier of the data exchange
    :ivar index: A számla sorszáma a kérésen belül Sequence number of
        the invoice within the request
    :ivar original_invoice_number: Az eredeti számla sorszáma, melyre a
        módosítás vonatkozik Sequence number of the original invoice, on
        which the modification occurs
    :ivar modification_index: A számlára vonatkozó módosító okirat
        egyedi sorszáma The unique sequence number referring to the
        original invoice
    :ivar ins_date: A beszúrás időpontja UTC időben Insert date in UTC
        time
    :ivar completeness_indicator: Jelöli, ha az adatszolgáltatás maga a
        számla (a számlán nem szerepel több adat) Indicates whether the
        data exchange is identical with the invoice (the invoice does
        not contain any more data)
    """

    invoice_number: Optional[str] = field(
        default=None,
        metadata={
            "name": "invoiceNumber",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
            "min_length": 1,
            "max_length": 50,
            "pattern": r".*[^\s].*",
        },
    )
    batch_index: Optional[int] = field(
        default=None,
        metadata={
            "name": "batchIndex",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "min_inclusive": 1,
        },
    )
    invoice_operation: Optional[ManageInvoiceOperationType] = field(
        default=None,
        metadata={
            "name": "invoiceOperation",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
        },
    )
    invoice_category: Optional[InvoiceCategoryType] = field(
        default=None,
        metadata={
            "name": "invoiceCategory",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
        },
    )
    invoice_issue_date: Optional[str] = field(
        default=None,
        metadata={
            "name": "invoiceIssueDate",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
            "min_inclusive": "2010-01-01",
            "pattern": r"\d{4}-\d{2}-\d{2}",
        },
    )
    supplier_tax_number: Optional[str] = field(
        default=None,
        metadata={
            "name": "supplierTaxNumber",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
            "min_length": 1,
            "max_length": 8,
            "length": 8,
            "pattern": r"[0-9]{8}",
        },
    )
    supplier_group_member_tax_number: Optional[str] = field(
        default=None,
        metadata={
            "name": "supplierGroupMemberTaxNumber",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "min_length": 1,
            "max_length": 8,
            "length": 8,
            "pattern": r"[0-9]{8}",
        },
    )
    supplier_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "supplierName",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
            "min_length": 1,
            "max_length": 512,
            "pattern": r".*[^\s].*",
        },
    )
    customer_tax_number: Optional[str] = field(
        default=None,
        metadata={
            "name": "customerTaxNumber",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "min_length": 1,
            "max_length": 8,
            "length": 8,
            "pattern": r"[0-9]{8}",
        },
    )
    customer_group_member_tax_number: Optional[str] = field(
        default=None,
        metadata={
            "name": "customerGroupMemberTaxNumber",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "min_length": 1,
            "max_length": 8,
            "length": 8,
            "pattern": r"[0-9]{8}",
        },
    )
    customer_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "customerName",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "min_length": 1,
            "max_length": 512,
            "pattern": r".*[^\s].*",
        },
    )
    payment_method: Optional[PaymentMethodType] = field(
        default=None,
        metadata={
            "name": "paymentMethod",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
        },
    )
    payment_date: Optional[str] = field(
        default=None,
        metadata={
            "name": "paymentDate",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "min_inclusive": "2010-01-01",
            "pattern": r"\d{4}-\d{2}-\d{2}",
        },
    )
    invoice_appearance: Optional[InvoiceAppearanceType] = field(
        default=None,
        metadata={
            "name": "invoiceAppearance",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
        },
    )
    source: Optional[SourceType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
        },
    )
    invoice_delivery_date: Optional[str] = field(
        default=None,
        metadata={
            "name": "invoiceDeliveryDate",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "min_inclusive": "2010-01-01",
            "pattern": r"\d{4}-\d{2}-\d{2}",
        },
    )
    currency: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "min_length": 1,
            "max_length": 4,
            "length": 3,
            "pattern": r"[A-Z]{3}",
        },
    )
    invoice_net_amount: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "invoiceNetAmount",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "total_digits": 18,
            "fraction_digits": 2,
        },
    )
    invoice_net_amount_huf: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "invoiceNetAmountHUF",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "total_digits": 18,
            "fraction_digits": 2,
        },
    )
    invoice_vat_amount: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "invoiceVatAmount",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "total_digits": 18,
            "fraction_digits": 2,
        },
    )
    invoice_vat_amount_huf: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "invoiceVatAmountHUF",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "total_digits": 18,
            "fraction_digits": 2,
        },
    )
    transaction_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "transactionId",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "min_length": 1,
            "max_length": 30,
            "pattern": r"[+a-zA-Z0-9_]{1,30}",
        },
    )
    index: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "min_inclusive": 1,
            "max_inclusive": 100,
        },
    )
    original_invoice_number: Optional[str] = field(
        default=None,
        metadata={
            "name": "originalInvoiceNumber",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "min_length": 1,
            "max_length": 50,
            "pattern": r".*[^\s].*",
        },
    )
    modification_index: Optional[int] = field(
        default=None,
        metadata={
            "name": "modificationIndex",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "min_inclusive": 1,
        },
    )
    ins_date: Optional[str] = field(
        default=None,
        metadata={
            "name": "insDate",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
            "min_inclusive": "2010-01-01T00:00:00Z",
            "pattern": r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(.\d{1,3})?Z",
        },
    )
    completeness_indicator: Optional[bool] = field(
        default=None,
        metadata={
            "name": "completenessIndicator",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
        },
    )


@dataclass
class InvoiceLinesType:
    """
    A számlán vagy módosító okiraton szereplő tételek kivonatos adatai
    Product/service digest data appearing on the invoice or the modification
    document.

    :ivar max_line_number: A sorok száma közül a legmagasabb, amit a
        számla tartalmaz The highest line number value the invoice
        contains
    :ivar new_created_lines: A módosító okirat által újként létrehozott
        számlasorok New invoice lines created by the modification
        document
    """

    max_line_number: Optional[int] = field(
        default=None,
        metadata={
            "name": "maxLineNumber",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
            "min_inclusive": 1,
            "total_digits": 20,
        },
    )
    new_created_lines: list[NewCreatedLinesType] = field(
        default_factory=list,
        metadata={
            "name": "newCreatedLines",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
        },
    )


@dataclass
class InvoiceNumberQueryType:
    """
    Számla lekérdezés számlaszám paramétere Invoice number param of the Invoice
    query.

    :ivar invoice_number: Számla vagy módosító okirat sorszáma
        Sequential number of the original or modification invoice
    :ivar invoice_direction: Kimenő vagy bejövő számla keresési
        paramétere Inbound or outbound invoice query parameter
    :ivar batch_index: A módosító okirat sorszáma a kötegen belül
        Sequence number of the modification document within the batch
    :ivar supplier_tax_number: Vevő oldali lekérdezés esetén a számla
        kiállítójának adószáma, ha több érvényes számla is megtalálható
        azonos sorszámmal The supplier's tax number in case of querying
        as customer, if the query result found more than one valid
        invoices with the same invoice number
    """

    invoice_number: Optional[str] = field(
        default=None,
        metadata={
            "name": "invoiceNumber",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
            "min_length": 1,
            "max_length": 50,
            "pattern": r".*[^\s].*",
        },
    )
    invoice_direction: Optional[InvoiceDirectionType] = field(
        default=None,
        metadata={
            "name": "invoiceDirection",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
        },
    )
    batch_index: Optional[int] = field(
        default=None,
        metadata={
            "name": "batchIndex",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "min_inclusive": 1,
        },
    )
    supplier_tax_number: Optional[str] = field(
        default=None,
        metadata={
            "name": "supplierTaxNumber",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "min_length": 1,
            "max_length": 8,
            "length": 8,
            "pattern": r"[0-9]{8}",
        },
    )


@dataclass
class InvoiceOperationType:
    """
    A kéréshez tartozó számlaművelet Invoice operation of the request.

    :ivar index: A számla sorszáma a kérésen belül Sequence number of
        the invoice within the request
    :ivar invoice_operation: A kért számla művelet típusa Type of the
        desired invoice operation
    :ivar invoice_data: Számla adatok BASE64-ben kódolt tartalma Invoice
        data in BASE64 encoded form
    :ivar electronic_invoice_hash: Elektronikus számla vagy módosító
        okirat állomány hash lenyomata Electronic invoice or
        modification document file hash value
    """

    index: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
            "min_inclusive": 1,
            "max_inclusive": 100,
        },
    )
    invoice_operation: Optional[ManageInvoiceOperationType] = field(
        default=None,
        metadata={
            "name": "invoiceOperation",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
        },
    )
    invoice_data: Optional[bytes] = field(
        default=None,
        metadata={
            "name": "invoiceData",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
            "format": "base64",
        },
    )
    electronic_invoice_hash: Optional[CryptoType] = field(
        default=None,
        metadata={
            "name": "electronicInvoiceHash",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
        },
    )


@dataclass
class MandatoryQueryParamsType:
    """
    A számla lekérdezés kötelező paraméterei Mandatory params of the invoice query.

    :ivar invoice_issue_date: Számla kiállításának dátumtartománya Date
        range of the invoice issue date
    :ivar ins_date: Számla adatszolgáltatás feldolgozásának időpont
        tartománya UTC idő szerint Datetime range of processing data
        exchange in UTC time
    :ivar original_invoice_number: Az eredeti számla sorszáma, melyre a
        módosítás vonatkozik Sequence number of the original invoice, on
        which the modification occurs
    """

    invoice_issue_date: Optional[DateIntervalParamType] = field(
        default=None,
        metadata={
            "name": "invoiceIssueDate",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
        },
    )
    ins_date: Optional[DateTimeIntervalParamType] = field(
        default=None,
        metadata={
            "name": "insDate",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
        },
    )
    original_invoice_number: Optional[str] = field(
        default=None,
        metadata={
            "name": "originalInvoiceNumber",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "min_length": 1,
            "max_length": 50,
            "pattern": r".*[^\s].*",
        },
    )


@dataclass
class RelationQueryDateType:
    """
    Kereső paraméter dátum értékekhez Query parameter for date values.

    :ivar query_operator: Kereső operátor Query operator
    :ivar query_value: Kereső érték Query value
    """

    query_operator: Optional[QueryOperatorType] = field(
        default=None,
        metadata={
            "name": "queryOperator",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
        },
    )
    query_value: Optional[str] = field(
        default=None,
        metadata={
            "name": "queryValue",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
            "min_inclusive": "2010-01-01",
            "pattern": r"\d{4}-\d{2}-\d{2}",
        },
    )


@dataclass
class RelationQueryMonetaryType:
    """
    Kereső paraméter monetáris értékekhez Query parameter for monetary values.

    :ivar query_operator: Kereső operátor Query operator
    :ivar query_value: Kereső érték Query value
    """

    query_operator: Optional[QueryOperatorType] = field(
        default=None,
        metadata={
            "name": "queryOperator",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
        },
    )
    query_value: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "queryValue",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
            "total_digits": 18,
            "fraction_digits": 2,
        },
    )


@dataclass
class SoftwareType:
    """
    A számlázóprogram adatai Billing software data.

    :ivar software_id: A számlázóprogram azonosítója Billing software ID
    :ivar software_name: A számlázóprogram neve Billing software name
    :ivar software_operation: A számlázóprogram működési típusa (lokális
        program vagy online számlázó szolgáltatás) Billing software
        operation type (local program or online billing service)
    :ivar software_main_version: A számlázóprogram főverziója Billing
        software main version
    :ivar software_dev_name: A számlázóprogram fejlesztőjének neve Name
        of the billing software's developer
    :ivar software_dev_contact: A számlázóprogram fejlesztőjének
        elektronikus elérhetősége Electronic contact of the billing
        software's developer
    :ivar software_dev_country_code: A számlázóprogram fejlesztőjének
        ISO-3166 alpha2 országkódja ISO-3166 alpha2 country code of the
        billing software's developer
    :ivar software_dev_tax_number: A számlázóprogram fejlesztőjének
        adószáma Tax number of the billing software's developer
    """

    software_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "softwareId",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
            "min_length": 1,
            "max_length": 32,
            "length": 18,
            "pattern": r"[0-9A-Z\-]{18}",
        },
    )
    software_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "softwareName",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
            "min_length": 1,
            "max_length": 50,
            "pattern": r".*[^\s].*",
        },
    )
    software_operation: Optional[SoftwareOperationType] = field(
        default=None,
        metadata={
            "name": "softwareOperation",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
        },
    )
    software_main_version: Optional[str] = field(
        default=None,
        metadata={
            "name": "softwareMainVersion",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
            "min_length": 1,
            "max_length": 15,
            "pattern": r".*[^\s].*",
        },
    )
    software_dev_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "softwareDevName",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
            "min_length": 1,
            "max_length": 512,
            "pattern": r".*[^\s].*",
        },
    )
    software_dev_contact: Optional[str] = field(
        default=None,
        metadata={
            "name": "softwareDevContact",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
            "min_length": 1,
            "max_length": 200,
            "pattern": r".*[^\s].*",
        },
    )
    software_dev_country_code: Optional[str] = field(
        default=None,
        metadata={
            "name": "softwareDevCountryCode",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "min_length": 1,
            "max_length": 2,
            "length": 2,
            "pattern": r"[A-Z]{2}",
        },
    )
    software_dev_tax_number: Optional[str] = field(
        default=None,
        metadata={
            "name": "softwareDevTaxNumber",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "min_length": 1,
            "max_length": 50,
            "pattern": r".*[^\s].*",
        },
    )


@dataclass
class TaxpayerAddressItemType:
    """
    Adózói címsor adat Taxpayer address item.

    :ivar taxpayer_address_type: Adózói cím típus Taxpayer address type
    :ivar taxpayer_address: Az adózó címadatai Address data of the
        taxpayer
    """

    taxpayer_address_type: Optional[TaxpayerAddressTypeType] = field(
        default=None,
        metadata={
            "name": "taxpayerAddressType",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
        },
    )
    taxpayer_address: Optional[DetailedAddressType] = field(
        default=None,
        metadata={
            "name": "taxpayerAddress",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
        },
    )


@dataclass
class TransactionQueryParamsType:
    """
    A számla lekérdezés tranzakciós paraméterei Transactional params of the invoice
    query.

    :ivar transaction_id: Az adatszolgáltatás tranzakció azonosítója
        Transaction identifier of the data exchange
    :ivar index: A számla sorszáma a kérésen belül Sequence number of
        the invoice within the request
    :ivar invoice_operation: Számlaművelet típus Invoice operation type
    """

    transaction_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "transactionId",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
            "min_length": 1,
            "max_length": 30,
            "pattern": r"[+a-zA-Z0-9_]{1,30}",
        },
    )
    index: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "min_inclusive": 1,
            "max_inclusive": 100,
        },
    )
    invoice_operation: Optional[ManageInvoiceOperationType] = field(
        default=None,
        metadata={
            "name": "invoiceOperation",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
        },
    )


@dataclass
class TransactionType:
    """
    Tranzakció lekérdezési eredmény Transaction query result.

    :ivar ins_date: A beszúrás időpontja UTC időben Insert date in UTC
        time
    :ivar ins_cus_user: A beszúrást végző felhasználó Inserting user
        name
    :ivar source: Az adatszolgáltatás forrása Data exchange source
    :ivar transaction_id: A számla tranzakció azonosítója Transaction ID
        of the invoice
    :ivar request_status: A kérés feldolgozási státusza Processing
        status of the request
    :ivar technical_annulment: Jelöli ha a tranzakció technikai
        érvénytelenítést tartalmaz Indicates whether the transaction
        contains technical annulment
    :ivar original_request_version: Az adatszolgáltatás requestVersion
        értéke requestVersion value of the invoice exchange
    :ivar item_count: Az adatszolgáltatás tételeinek száma Item count of
        the invoiceExchange
    """

    ins_date: Optional[str] = field(
        default=None,
        metadata={
            "name": "insDate",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
            "min_inclusive": "2010-01-01T00:00:00Z",
            "pattern": r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(.\d{1,3})?Z",
        },
    )
    ins_cus_user: Optional[str] = field(
        default=None,
        metadata={
            "name": "insCusUser",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
            "min_length": 6,
            "max_length": 15,
            "pattern": r"[a-zA-Z0-9]{6,15}",
        },
    )
    source: Optional[SourceType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
        },
    )
    transaction_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "transactionId",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
            "min_length": 1,
            "max_length": 30,
            "pattern": r"[+a-zA-Z0-9_]{1,30}",
        },
    )
    request_status: Optional[RequestStatusType] = field(
        default=None,
        metadata={
            "name": "requestStatus",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
        },
    )
    technical_annulment: Optional[bool] = field(
        default=None,
        metadata={
            "name": "technicalAnnulment",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
        },
    )
    original_request_version: Optional[OriginalRequestVersionType] = field(
        default=None,
        metadata={
            "name": "originalRequestVersion",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
        },
    )
    item_count: Optional[int] = field(
        default=None,
        metadata={
            "name": "itemCount",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
            "min_inclusive": 1,
            "max_inclusive": 100,
        },
    )


@dataclass
class AnnulmentOperationListType:
    """
    A kéréshez tartozó kötegelt technikai érvénytelenítések Batch technical
    annulment operations of the request.

    :ivar annulment_operation: A kéréshez tartozó technikai
        érvénytelenítő művelet Technical annulment operation of the
        request
    """

    annulment_operation: list[AnnulmentOperationType] = field(
        default_factory=list,
        metadata={
            "name": "annulmentOperation",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "min_occurs": 1,
            "max_occurs": 100,
        },
    )


@dataclass
class BasicOnlineInvoiceRequestType(BasicRequestType):
    """
    Online Számla rendszerre specifikus általános kérés adatok Online Invoice
    specific basic request data.

    :ivar software: A számlázóprogram adatai Billing software data
    """

    software: Optional[SoftwareType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
        },
    )


@dataclass
class BasicOnlineInvoiceResponseType(BasicResponseType):
    """
    Online Számla rendszerre specifikus általános válasz adatok Online Invoice
    specific basic response data.

    :ivar software: A számlázóprogram adatai Billing software data
    """

    software: Optional[SoftwareType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
        },
    )


@dataclass
class GeneralErrorResponseType(GeneralErrorHeaderResponseType):
    """
    Online Számla rendszerre specifikus általános hibaválasz típus Online Invoice
    specific general error response type.

    :ivar software: A számlázóprogram adatai Billing software data
    :ivar technical_validation_messages: Technikai validációs üzenetek
        Technical validation messages
    """

    software: Optional[SoftwareType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
        },
    )
    technical_validation_messages: list[TechnicalValidationResultType] = field(
        default_factory=list,
        metadata={
            "name": "technicalValidationMessages",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
        },
    )


@dataclass
class InvoiceChainElementType:
    """
    Számlalánc elem Invoice chain element.

    :ivar invoice_chain_digest: Számlalánc kivonat adatok Invoice chain
        digest data
    :ivar invoice_lines: A számlán vagy módosító okiraton szereplő
        tételek kivonatos adatai Product/service digest data appearing
        on the invoice or the modification document
    :ivar invoice_reference_data: A módosítás vagy érvénytelenítés
        adatai Modification or cancellation data
    """

    invoice_chain_digest: Optional[InvoiceChainDigestType] = field(
        default=None,
        metadata={
            "name": "invoiceChainDigest",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
        },
    )
    invoice_lines: Optional[InvoiceLinesType] = field(
        default=None,
        metadata={
            "name": "invoiceLines",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
        },
    )
    invoice_reference_data: Optional[InvoiceReferenceDataType] = field(
        default=None,
        metadata={
            "name": "invoiceReferenceData",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
        },
    )


@dataclass
class InvoiceDataResultType:
    """
    Számlaszámra történő lekérdezés eredménye Invoice number based query result.

    :ivar invoice_data: Számla adatok BASE64-ben kódolt tartalma Invoice
        data in BASE64 encoded form
    :ivar audit_data: A számla audit adatai Invoice audit data
    :ivar compressed_content_indicator: Jelöli, ha az invoice tartalmát
        a BASE64 dekódolást követően még ki kell tömöríteni az
        olvasáshoz Indicates if the content of the invoice needs to be
        decompressed to be read following the BASE64 decoding
    :ivar electronic_invoice_hash: Elektronikus számla vagy módosító
        okirat állomány hash lenyomata Electronic invoice or
        modification document file hash value
    """

    invoice_data: Optional[bytes] = field(
        default=None,
        metadata={
            "name": "invoiceData",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
            "format": "base64",
        },
    )
    audit_data: Optional[AuditDataType] = field(
        default=None,
        metadata={
            "name": "auditData",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
        },
    )
    compressed_content_indicator: Optional[bool] = field(
        default=None,
        metadata={
            "name": "compressedContentIndicator",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
        },
    )
    electronic_invoice_hash: Optional[CryptoType] = field(
        default=None,
        metadata={
            "name": "electronicInvoiceHash",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
        },
    )


@dataclass
class InvoiceDigestResultType:
    """
    Számla lekérdezési eredmények Invoice query results.

    :ivar current_page: A jelenleg lekérdezett lapszám The currently
        queried page count
    :ivar available_page: A lekérdezés eredménye szerint elérhető utolsó
        lapszám The highest available page count matching the query
    :ivar invoice_digest: Számla kivonat lekérdezési eredmény Invoice
        digest query result
    """

    current_page: Optional[int] = field(
        default=None,
        metadata={
            "name": "currentPage",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
            "min_inclusive": 0,
        },
    )
    available_page: Optional[int] = field(
        default=None,
        metadata={
            "name": "availablePage",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
            "min_inclusive": 0,
        },
    )
    invoice_digest: list[InvoiceDigestType] = field(
        default_factory=list,
        metadata={
            "name": "invoiceDigest",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
        },
    )


@dataclass
class InvoiceOperationListType:
    """
    A kéréshez tartozó kötegelt számlaműveletek Batch invoice operations of the
    request.

    :ivar compressed_content: Tömörített tartalom jelzése a feldolgozási
        folyamat számára Compressed content indicator for the processing
        flow
    :ivar invoice_operation: A kéréshez tartozó számlaművelet Invoice
        operation of the request
    """

    compressed_content: Optional[bool] = field(
        default=None,
        metadata={
            "name": "compressedContent",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
        },
    )
    invoice_operation: list[InvoiceOperationType] = field(
        default_factory=list,
        metadata={
            "name": "invoiceOperation",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "min_occurs": 1,
            "max_occurs": 100,
        },
    )


@dataclass
class ProcessingResultType:
    """
    Számla feldolgozási eredmény Invoice processing result.

    :ivar index: A számla sorszáma a kérésen belül Sequence number of
        the invoice within the request
    :ivar batch_index: A módosító okirat sorszáma a kötegen belül
        Sequence number of the modification document within the batch
    :ivar invoice_status: A számla feldolgozási státusza Processing
        status of the invoice
    :ivar technical_validation_messages: Technikai validációs üzenetek
        Technical validation messages
    :ivar business_validation_messages: Üzleti validációs üzenetek
        Business validation messages
    :ivar compressed_content_indicator: Jelöli, ha az originalRequest
        tartalmát a BASE64 dekódolást követően még ki kell tömöríteni az
        olvasáshoz Indicates if the content of the originalRequest needs
        to be decompressed to be read following the BASE64 decoding
    :ivar original_request: Számla adatok BASE64-ben kódolt tartalma
        Invoice data in BASE64 encoded form
    """

    index: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
            "min_inclusive": 1,
            "max_inclusive": 100,
        },
    )
    batch_index: Optional[int] = field(
        default=None,
        metadata={
            "name": "batchIndex",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "min_inclusive": 1,
        },
    )
    invoice_status: Optional[InvoiceStatusType] = field(
        default=None,
        metadata={
            "name": "invoiceStatus",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
        },
    )
    technical_validation_messages: list[TechnicalValidationResultType] = field(
        default_factory=list,
        metadata={
            "name": "technicalValidationMessages",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
        },
    )
    business_validation_messages: list[BusinessValidationResultType] = field(
        default_factory=list,
        metadata={
            "name": "businessValidationMessages",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
        },
    )
    compressed_content_indicator: Optional[bool] = field(
        default=None,
        metadata={
            "name": "compressedContentIndicator",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
        },
    )
    original_request: Optional[bytes] = field(
        default=None,
        metadata={
            "name": "originalRequest",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "format": "base64",
        },
    )


@dataclass
class RelationalQueryParamsType:
    """
    A számla lekérdezés relációs paraméterei Relational params of the invoice
    query.

    :ivar invoice_delivery: Számla teljesítési dátumának kereső
        paramétere Query parameter of the invoice delivery date
    :ivar payment_date: A számla fizetési határidejének kereső
        paramétere Query parameter of the invoice payment date
    :ivar invoice_net_amount: A számla nettó összeg kereső paramétere a
        számla pénznemében Query parameter of the invoice net amount
        expressed in the currency of the invoice
    :ivar invoice_net_amount_huf: A számla nettó összegének kereső
        paramétere forintban Query parameter of the invoice net amount
        expressed in HUF
    :ivar invoice_vat_amount: A számla ÁFA összegének kereső paramétere
        a számla pénznemében Query parameter of the invoice VAT amount
        expressed in the currency of the invoice
    :ivar invoice_vat_amount_huf: A számla ÁFA összegének kereső
        paramétere forintban Query parameter of the invoice VAT amount
        expressed in HUF
    """

    invoice_delivery: list[RelationQueryDateType] = field(
        default_factory=list,
        metadata={
            "name": "invoiceDelivery",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "max_occurs": 2,
        },
    )
    payment_date: list[RelationQueryDateType] = field(
        default_factory=list,
        metadata={
            "name": "paymentDate",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "max_occurs": 2,
        },
    )
    invoice_net_amount: list[RelationQueryMonetaryType] = field(
        default_factory=list,
        metadata={
            "name": "invoiceNetAmount",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "max_occurs": 2,
        },
    )
    invoice_net_amount_huf: list[RelationQueryMonetaryType] = field(
        default_factory=list,
        metadata={
            "name": "invoiceNetAmountHUF",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "max_occurs": 2,
        },
    )
    invoice_vat_amount: list[RelationQueryMonetaryType] = field(
        default_factory=list,
        metadata={
            "name": "invoiceVatAmount",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "max_occurs": 2,
        },
    )
    invoice_vat_amount_huf: list[RelationQueryMonetaryType] = field(
        default_factory=list,
        metadata={
            "name": "invoiceVatAmountHUF",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "max_occurs": 2,
        },
    )


@dataclass
class TaxpayerAddressListType:
    """
    Adózói cím lista típus Taxpayer address list type.

    :ivar taxpayer_address_item: Adózói címsor adat Taxpayer address
        item
    """

    taxpayer_address_item: list[TaxpayerAddressItemType] = field(
        default_factory=list,
        metadata={
            "name": "taxpayerAddressItem",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "min_occurs": 1,
        },
    )


@dataclass
class TransactionListResultType:
    """
    Tranzakció lekérdezési eredményei Transaction query results.

    :ivar current_page: A jelenleg lekérdezett lapszám The currently
        queried page count
    :ivar available_page: A lekérdezés eredménye szerint elérhető utolsó
        lapszám The highest available page count matching the query
    :ivar transaction: Tranzakció lekérdezési eredmény Transaction query
        result
    """

    current_page: Optional[int] = field(
        default=None,
        metadata={
            "name": "currentPage",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
            "min_inclusive": 0,
        },
    )
    available_page: Optional[int] = field(
        default=None,
        metadata={
            "name": "availablePage",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
            "min_inclusive": 0,
        },
    )
    transaction: list[TransactionType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
        },
    )


@dataclass
class GeneralErrorResponse(GeneralErrorResponseType):
    """
    Online Számla rendszerre specifikus általános hibaválasz Online Invoice
    specific general error response.
    """

    class Meta:
        namespace = "http://schemas.nav.gov.hu/OSA/3.0/api"


@dataclass
class InvoiceChainDigestResultType:
    """
    Számlalánc kivonat lekérdezés eredményei Invoice chain digest query result.

    :ivar current_page: A jelenleg lekérdezett lapszám The currently
        queried page count
    :ivar available_page: A lekérdezés eredménye szerint elérhető utolsó
        lapszám The highest available page count matching the query
    :ivar invoice_chain_element: Számlalánc elem Invoice chain element
    """

    current_page: Optional[int] = field(
        default=None,
        metadata={
            "name": "currentPage",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
            "min_inclusive": 0,
        },
    )
    available_page: Optional[int] = field(
        default=None,
        metadata={
            "name": "availablePage",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
            "min_inclusive": 0,
        },
    )
    invoice_chain_element: list[InvoiceChainElementType] = field(
        default_factory=list,
        metadata={
            "name": "invoiceChainElement",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
        },
    )


@dataclass
class InvoiceQueryParamsType:
    """
    Számla lekérdezési paraméterek Invoice query parameters.

    :ivar mandatory_query_params: A számla lekérdezés kötelező
        paraméterei Mandatory params of the invoice query
    :ivar additional_query_params: A számla lekérdezés kiegészítő
        paraméterei Additional params of the invoice query
    :ivar relational_query_params: A számla lekérdezés relációs
        paraméterei Relational params of the invoice query
    :ivar transaction_query_params: A számla lekérdezés tranzakciós
        paraméterei Transactional params of the invoice query
    """

    mandatory_query_params: Optional[MandatoryQueryParamsType] = field(
        default=None,
        metadata={
            "name": "mandatoryQueryParams",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
        },
    )
    additional_query_params: Optional[AdditionalQueryParamsType] = field(
        default=None,
        metadata={
            "name": "additionalQueryParams",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
        },
    )
    relational_query_params: Optional[RelationalQueryParamsType] = field(
        default=None,
        metadata={
            "name": "relationalQueryParams",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
        },
    )
    transaction_query_params: Optional[TransactionQueryParamsType] = field(
        default=None,
        metadata={
            "name": "transactionQueryParams",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
        },
    )


@dataclass
class ManageAnnulmentRequestType(BasicOnlineInvoiceRequestType):
    """
    A POST /manageAnnulment REST operáció kérés típusa Request type of the POST
    /manageAnnulment REST operation.

    :ivar exchange_token: A tranzakcióhoz kiadott egyedi és dekódolt
        token The decoded unique token issued for the current
        transaction
    :ivar annulment_operations: A kéréshez tartozó kötegelt technikai
        érvénytelenítések Batch technical annulment operations of the
        request
    """

    exchange_token: Optional[str] = field(
        default=None,
        metadata={
            "name": "exchangeToken",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
            "min_length": 1,
            "max_length": 50,
            "pattern": r".*[^\s].*",
        },
    )
    annulment_operations: Optional[AnnulmentOperationListType] = field(
        default=None,
        metadata={
            "name": "annulmentOperations",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
        },
    )


@dataclass
class ManageInvoiceRequestType(BasicOnlineInvoiceRequestType):
    """
    A POST /manageInvoice REST operáció kérés típusa Request type of the POST
    /manageInvoice REST operation.

    :ivar exchange_token: A tranzakcióhoz kiadott egyedi és dekódolt
        token The decoded unique token issued for the current
        transaction
    :ivar invoice_operations: A kéréshez tartozó kötegelt
        számlaműveletek Batch invoice operations of the request
    """

    exchange_token: Optional[str] = field(
        default=None,
        metadata={
            "name": "exchangeToken",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
            "min_length": 1,
            "max_length": 50,
            "pattern": r".*[^\s].*",
        },
    )
    invoice_operations: Optional[InvoiceOperationListType] = field(
        default=None,
        metadata={
            "name": "invoiceOperations",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
        },
    )


@dataclass
class ProcessingResultListType:
    """
    A kéréshez tartozó feldolgozási eredmények Processing results of the request.

    :ivar processing_result: Számla feldolgozási eredmény Invoice
        processing result
    :ivar original_request_version: Az adatszolgáltatás requestVersion
        értéke requestVersion value of the invoice exchange
    :ivar annulment_data: Technikai érvénytelenítés státusz adatai
        Status data of technical annulment
    """

    processing_result: list[ProcessingResultType] = field(
        default_factory=list,
        metadata={
            "name": "processingResult",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "min_occurs": 1,
        },
    )
    original_request_version: Optional[OriginalRequestVersionType] = field(
        default=None,
        metadata={
            "name": "originalRequestVersion",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
        },
    )
    annulment_data: Optional[AnnulmentDataType] = field(
        default=None,
        metadata={
            "name": "annulmentData",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
        },
    )


@dataclass
class QueryInvoiceChainDigestRequestType(BasicOnlineInvoiceRequestType):
    """
    A POST /queryInvoiceChainDigest REST operáció kérés típusa Request type of the
    POST /queryInvoiceChainDigest REST operation.

    :ivar page: A lekérdezni kívánt lap száma The queried page count
    :ivar invoice_chain_query: Számlalánc kivonat lekérdezés számlaszám
        paramétere Invoice number param of the invoice chain digest
        query
    """

    page: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
            "min_inclusive": 1,
        },
    )
    invoice_chain_query: Optional[InvoiceChainQueryType] = field(
        default=None,
        metadata={
            "name": "invoiceChainQuery",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
        },
    )


@dataclass
class QueryInvoiceCheckResponseType(BasicOnlineInvoiceResponseType):
    """
    A POST /queryInvoiceCheck REST operáció válasz típusa Response type of the POST
    /queryInvoiceCheck REST operation.

    :ivar invoice_check_result: Jelöli, ha a lekérdezett számlaszám
        érvényesként szerepel a rendszerben és a lekérdező adószáma
        kiállítóként vagy eladóként szerepel a számlán Indicates whether
        the queried invoice number exists in the system as a valid
        invoice, if the tax number of the querying entity is present on
        the invoice either as supplier or customer
    """

    invoice_check_result: Optional[bool] = field(
        default=None,
        metadata={
            "name": "invoiceCheckResult",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
        },
    )


@dataclass
class QueryInvoiceDataRequestType(BasicOnlineInvoiceRequestType):
    """
    A POST /queryInvoiceData REST operáció kérés típusa Request type of the POST
    /queryInvoiceData REST operation.

    :ivar invoice_number_query: Számla lekérdezés számlaszám paramétere
        Invoice number param of the Invoice query
    """

    invoice_number_query: Optional[InvoiceNumberQueryType] = field(
        default=None,
        metadata={
            "name": "invoiceNumberQuery",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
        },
    )


@dataclass
class QueryInvoiceDataResponseType(BasicOnlineInvoiceResponseType):
    """
    A POST /queryInvoiceData REST operáció válasz típusa Response type of the POST
    /queryInvoiceData REST operation.

    :ivar invoice_data_result: A számla lekérdezés eredménye Invoice
        data query result
    """

    invoice_data_result: Optional[InvoiceDataResultType] = field(
        default=None,
        metadata={
            "name": "invoiceDataResult",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
        },
    )


@dataclass
class QueryInvoiceDigestResponseType(BasicOnlineInvoiceResponseType):
    """
    A POST /queryInvoiceDigest REST operáció válasz típusa Response type of the
    POST /queryInvoiceDigest REST operation.

    :ivar invoice_digest_result: A számla kivonat lekérdezés eredményei
        Invoice digest query results
    """

    invoice_digest_result: Optional[InvoiceDigestResultType] = field(
        default=None,
        metadata={
            "name": "invoiceDigestResult",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
        },
    )


@dataclass
class QueryTaxpayerRequestType(BasicOnlineInvoiceRequestType):
    """
    A POST /queryTaxpayer REST operáció kérés típusa Request type of the POST
    /queryTaxpayer REST operation.

    :ivar tax_number: A lekérdezett adózó adószáma Tax number of the
        queried taxpayer
    """

    tax_number: Optional[str] = field(
        default=None,
        metadata={
            "name": "taxNumber",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
            "min_length": 1,
            "max_length": 8,
            "length": 8,
            "pattern": r"[0-9]{8}",
        },
    )


@dataclass
class QueryTransactionListRequestType(BasicOnlineInvoiceRequestType):
    """
    A POST /queryTransactionList REST operáció kérés típusa Request type of the
    POST /queryTransactionList REST operation.

    :ivar page: A lekérdezni kívánt lap száma The queried page count
    :ivar ins_date: A lekérdezni kívánt tranzakciók kiadásának szerver
        oldali ideje UTC időben The queried transaction's insert date on
        server side in UTC time
    :ivar request_status: A kérés feldolgozási státusza Processing
        status of the request
    """

    page: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
            "min_inclusive": 1,
        },
    )
    ins_date: Optional[DateTimeIntervalParamType] = field(
        default=None,
        metadata={
            "name": "insDate",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
        },
    )
    request_status: Optional[RequestStatusType] = field(
        default=None,
        metadata={
            "name": "requestStatus",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
        },
    )


@dataclass
class QueryTransactionListResponseType(BasicOnlineInvoiceResponseType):
    """
    A POST /queryTransactionList REST operáció válasz típusa Response type of the
    POST /queryTransactionList REST operation.

    :ivar transaction_list_result: Tranzakció lekérdezési eredményei
        Transaction query results
    """

    transaction_list_result: Optional[TransactionListResultType] = field(
        default=None,
        metadata={
            "name": "transactionListResult",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
        },
    )


@dataclass
class QueryTransactionStatusRequestType(BasicOnlineInvoiceRequestType):
    """
    A POST /queryTransactionStatus REST operáció kérés típusa Request type of the
    POST /queryTransactionStatus REST operation.

    :ivar transaction_id: Az adatszolgáltatás tranzakció azonosítója
        Transaction identifier of the data exchange
    :ivar return_original_request: Jelöli, ha a kliens által beküldött
        eredeti tartalmat is vissza kell adni a válaszban Indicates if
        the original client data should also be returned in the response
    """

    transaction_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "transactionId",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
            "min_length": 1,
            "max_length": 30,
            "pattern": r"[+a-zA-Z0-9_]{1,30}",
        },
    )
    return_original_request: Optional[bool] = field(
        default=None,
        metadata={
            "name": "returnOriginalRequest",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
        },
    )


@dataclass
class TaxpayerDataType:
    """
    Az adózó lekérdezés válasz adatai Response data of the taxpayer query.

    :ivar taxpayer_name: Az adózó neve Name of the taxpayer
    :ivar taxpayer_short_name: Az adózó rövidített neve Shortened name
        of the taxpayer
    :ivar tax_number_detail: Az adószám részletes adatai Detailed data
        of the tax number
    :ivar incorporation: Gazdasági típus Incorporation type
    :ivar vat_group_membership: Az adózó ÁFA csoport tagsága VAT group
        membership of the taxpayer
    :ivar taxpayer_address_list: Adózói cím lista típus Taxpayer address
        list type
    """

    taxpayer_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "taxpayerName",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
            "min_length": 1,
            "max_length": 512,
            "pattern": r".*[^\s].*",
        },
    )
    taxpayer_short_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "taxpayerShortName",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "min_length": 1,
            "max_length": 200,
            "pattern": r".*[^\s].*",
        },
    )
    tax_number_detail: Optional[TaxNumberType] = field(
        default=None,
        metadata={
            "name": "taxNumberDetail",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
        },
    )
    incorporation: Optional[IncorporationType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
        },
    )
    vat_group_membership: Optional[str] = field(
        default=None,
        metadata={
            "name": "vatGroupMembership",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "min_length": 1,
            "max_length": 8,
            "length": 8,
            "pattern": r"[0-9]{8}",
        },
    )
    taxpayer_address_list: Optional[TaxpayerAddressListType] = field(
        default=None,
        metadata={
            "name": "taxpayerAddressList",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
        },
    )


@dataclass
class TokenExchangeRequest(BasicOnlineInvoiceRequestType):
    """
    A POST /tokenExchange REST operáció kérésének root elementje Request root
    element of the POST /tokenExchange REST operation.
    """

    class Meta:
        namespace = "http://schemas.nav.gov.hu/OSA/3.0/api"


@dataclass
class TokenExchangeResponseType(BasicOnlineInvoiceResponseType):
    """
    A POST /tokenExchange REST operáció válasz típusa Response type of the POST
    /tokenExchange REST operation.

    :ivar encoded_exchange_token: A kiadott exchange token AES-128 ECB
        algoritmussal kódolt alakja The issued exchange token in AES-128
        ECB encoded form
    :ivar token_validity_from: A kiadott token érvényességének kezdete
        Validity start of the issued exchange token
    :ivar token_validity_to: A kiadott token érvényességének vége
        Validity end of the issued exchange token
    """

    encoded_exchange_token: Optional[bytes] = field(
        default=None,
        metadata={
            "name": "encodedExchangeToken",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
            "format": "base64",
        },
    )
    token_validity_from: Optional[str] = field(
        default=None,
        metadata={
            "name": "tokenValidityFrom",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
            "min_inclusive": "2010-01-01T00:00:00Z",
            "pattern": r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(.\d{1,3})?Z",
        },
    )
    token_validity_to: Optional[str] = field(
        default=None,
        metadata={
            "name": "tokenValidityTo",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
            "min_inclusive": "2010-01-01T00:00:00Z",
            "pattern": r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(.\d{1,3})?Z",
        },
    )


@dataclass
class TransactionResponseType(BasicOnlineInvoiceResponseType):
    """
    A POST /manageInvoice és a POST /manageAnnulment REST operáció közös válasz
    típusa Common response type of the POST /manageInvoice and the POST
    /manageAnnulment REST operation.

    :ivar transaction_id: A kért operáció tranzakció azonosítója
        Transaction identifier of the requested operation
    """

    transaction_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "transactionId",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
            "min_length": 1,
            "max_length": 30,
            "pattern": r"[+a-zA-Z0-9_]{1,30}",
        },
    )


@dataclass
class ManageAnnulmentRequest(ManageAnnulmentRequestType):
    """
    A POST /manageAnnulment REST operáció kérésének root elementje Request root
    element of the POST /manageAnnulment REST operation.
    """

    class Meta:
        namespace = "http://schemas.nav.gov.hu/OSA/3.0/api"


@dataclass
class ManageAnnulmentResponse(TransactionResponseType):
    """
    A POST /manageAnnulment REST operáció válaszának root elementje Response root
    element of the POST /manageAnnulment REST operation.
    """

    class Meta:
        namespace = "http://schemas.nav.gov.hu/OSA/3.0/api"


@dataclass
class ManageInvoiceRequest(ManageInvoiceRequestType):
    """
    A POST /manageInvoice REST operáció kérésének root elementje Request root
    element of the POST /manageInvoice REST operation.
    """

    class Meta:
        namespace = "http://schemas.nav.gov.hu/OSA/3.0/api"


@dataclass
class ManageInvoiceResponse(TransactionResponseType):
    """
    A POST /manageInvoice REST operáció válaszának root elementje Response root
    element of the POST /manageInvoice REST operation.
    """

    class Meta:
        namespace = "http://schemas.nav.gov.hu/OSA/3.0/api"


@dataclass
class QueryInvoiceChainDigestRequest(QueryInvoiceChainDigestRequestType):
    """
    A POST /queryInvoiceChainDigest REST operáció kérésének root elementje Request
    root element of the POST /queryInvoiceChainDigest REST operation.
    """

    class Meta:
        namespace = "http://schemas.nav.gov.hu/OSA/3.0/api"


@dataclass
class QueryInvoiceChainDigestResponseType(BasicOnlineInvoiceResponseType):
    """
    A POST /queryInvoiceChainDigest REST operáció válasz típusa Response type of
    the POST /queryInvoiceChainDigest REST operation.

    :ivar invoice_chain_digest_result: Számlalánc kivonat lekérdezés
        eredményei Invoice chain digest query result
    """

    invoice_chain_digest_result: Optional[InvoiceChainDigestResultType] = (
        field(
            default=None,
            metadata={
                "name": "invoiceChainDigestResult",
                "type": "Element",
                "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
                "required": True,
            },
        )
    )


@dataclass
class QueryInvoiceCheckRequest(QueryInvoiceDataRequestType):
    """
    A POST /queryInvoiceCheck REST operáció kérésének root elementje Request root
    element of the POST /queryInvoiceCheck REST operation.
    """

    class Meta:
        namespace = "http://schemas.nav.gov.hu/OSA/3.0/api"


@dataclass
class QueryInvoiceCheckResponse(QueryInvoiceCheckResponseType):
    """
    A POST /queryInvoiceCheck REST operáció válaszának root elementje Response root
    element of the POST /queryInvoiceCheck REST operation.
    """

    class Meta:
        namespace = "http://schemas.nav.gov.hu/OSA/3.0/api"


@dataclass
class QueryInvoiceDataRequest(QueryInvoiceDataRequestType):
    """
    A POST /queryInvoiceData REST operáció kérésének root elementje Request root
    element of the POST /queryInvoiceData REST operation.
    """

    class Meta:
        namespace = "http://schemas.nav.gov.hu/OSA/3.0/api"


@dataclass
class QueryInvoiceDataResponse(QueryInvoiceDataResponseType):
    """
    A POST /queryInvoiceData REST operáció válaszának root elementje Response root
    element of the POST /queryInvoiceData REST operation.
    """

    class Meta:
        namespace = "http://schemas.nav.gov.hu/OSA/3.0/api"


@dataclass
class QueryInvoiceDigestRequestType(BasicOnlineInvoiceRequestType):
    """
    A POST /queryInvoiceDigest REST operáció kérés típusa Request type of the POST
    /queryInvoiceDigest REST operation.

    :ivar page: A lekérdezni kívánt lap száma The queried page count
    :ivar invoice_direction: Kimenő vagy bejövő számla keresési
        paramétere Inbound or outbound invoice query parameter
    :ivar invoice_query_params: Számla lekérdezési paraméterek Invoice
        query parameters
    """

    page: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
            "min_inclusive": 1,
        },
    )
    invoice_direction: Optional[InvoiceDirectionType] = field(
        default=None,
        metadata={
            "name": "invoiceDirection",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
        },
    )
    invoice_query_params: Optional[InvoiceQueryParamsType] = field(
        default=None,
        metadata={
            "name": "invoiceQueryParams",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
            "required": True,
        },
    )


@dataclass
class QueryInvoiceDigestResponse(QueryInvoiceDigestResponseType):
    """
    A POST /queryInvoiceDigest REST operáció válaszának root elementje Response
    root element of the POST /queryInvoiceDigest REST operation.
    """

    class Meta:
        namespace = "http://schemas.nav.gov.hu/OSA/3.0/api"


@dataclass
class QueryTaxpayerRequest(QueryTaxpayerRequestType):
    """
    A POST /queryTaxpayer REST operáció kérésének root elementje Request root
    element of the POST /queryTaxpayer REST operation.
    """

    class Meta:
        namespace = "http://schemas.nav.gov.hu/OSA/3.0/api"


@dataclass
class QueryTaxpayerResponseType(BasicOnlineInvoiceResponseType):
    """
    A POST /queryTaxpayer REST operáció válasz típusa Response type of the POST
    /queryTaxpayer REST operation.

    :ivar info_date: Az adatok utolsó változásának időpontja Last date
        on which the data was changed
    :ivar taxpayer_validity: Jelzi, hogy a lekérdezett adózó létezik és
        érvényes-e Indicates whether the queried taxpayer is existing
        and valid
    :ivar taxpayer_data: Az adózó lekérdezés válasz adatai Response data
        of the taxpayer query
    """

    info_date: Optional[XmlDateTime] = field(
        default=None,
        metadata={
            "name": "infoDate",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
        },
    )
    taxpayer_validity: Optional[bool] = field(
        default=None,
        metadata={
            "name": "taxpayerValidity",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
        },
    )
    taxpayer_data: Optional[TaxpayerDataType] = field(
        default=None,
        metadata={
            "name": "taxpayerData",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
        },
    )


@dataclass
class QueryTransactionListRequest(QueryTransactionListRequestType):
    """
    A POST /queryTransactionList REST operáció kérésének root elementje Request
    root element of the POST /queryTransactionList REST operation.
    """

    class Meta:
        namespace = "http://schemas.nav.gov.hu/OSA/3.0/api"


@dataclass
class QueryTransactionListResponse(QueryTransactionListResponseType):
    """
    A POST /queryTransactionList REST operáció válaszának root elementje Response
    root element of the POST /queryTransactionList REST operation.
    """

    class Meta:
        namespace = "http://schemas.nav.gov.hu/OSA/3.0/api"


@dataclass
class QueryTransactionStatusRequest(QueryTransactionStatusRequestType):
    """
    A POST /queryTransactionStatus REST operáció kérésének root elementje Request
    root element of the POST /queryTransactionStatus REST operation.
    """

    class Meta:
        namespace = "http://schemas.nav.gov.hu/OSA/3.0/api"


@dataclass
class QueryTransactionStatusResponseType(BasicOnlineInvoiceResponseType):
    """
    A POST /queryTransactionStatus REST operáció válasz típusa Response type of the
    POST /queryTransactionStatus REST operation.

    :ivar processing_results: A kérésben szereplő számlák feldolgozási
        státusza Processing status of the invoices in the request
    """

    processing_results: Optional[ProcessingResultListType] = field(
        default=None,
        metadata={
            "name": "processingResults",
            "type": "Element",
            "namespace": "http://schemas.nav.gov.hu/OSA/3.0/api",
        },
    )


@dataclass
class TokenExchangeResponse(TokenExchangeResponseType):
    """
    A POST /tokenExchange REST operáció válaszának root elementje Response root
    element of the POST /tokenExchange REST operation.
    """

    class Meta:
        namespace = "http://schemas.nav.gov.hu/OSA/3.0/api"


@dataclass
class QueryInvoiceChainDigestResponse(QueryInvoiceChainDigestResponseType):
    """
    A POST /queryInvoiceChainDigest REST operáció válaszának root elementje
    Response root element of the POST /queryInvoiceChainDigest REST operation.
    """

    class Meta:
        namespace = "http://schemas.nav.gov.hu/OSA/3.0/api"


@dataclass
class QueryInvoiceDigestRequest(QueryInvoiceDigestRequestType):
    """
    A POST /queryInvoiceDigest REST operáció válaszának root elementje Response
    root element of the POST /queryInvoiceDigest REST operation.
    """

    class Meta:
        namespace = "http://schemas.nav.gov.hu/OSA/3.0/api"


@dataclass
class QueryTaxpayerResponse(QueryTaxpayerResponseType):
    """
    A POST /queryTaxpayer REST operáció válaszának root elementje Response root
    element of the POST /queryTaxpayer REST operation.
    """

    class Meta:
        namespace = "http://schemas.nav.gov.hu/OSA/3.0/api"


@dataclass
class QueryTransactionStatusResponse(QueryTransactionStatusResponseType):
    """
    A POST /queryTransactionStatus REST operáció válaszának root elementje Response
    root element of the POST /queryTransactionStatus REST operation.
    """

    class Meta:
        namespace = "http://schemas.nav.gov.hu/OSA/3.0/api"
