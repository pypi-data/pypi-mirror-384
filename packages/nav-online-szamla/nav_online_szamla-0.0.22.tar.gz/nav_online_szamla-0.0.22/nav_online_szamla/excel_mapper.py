CUSTOMER_COLUMNS = {
    'Customer ID / Vevő azonosító': {
        'model_field': 'customer_id',
        'dtype': str
    },
    'Customer name / Vevő neve': {
        'model_field': 'customer_name',
        'dtype': str
    },
    'Customer Country code / Vevő országkód': {
        'model_field': 'country_code',
        'dtype': str
    },
    'Customer ZIP code / Irányítószám': {
        'model_field': 'zip_code',
        'dtype': str
    },
    'City / Település': {
        'model_field': 'city',
        'dtype': str
    },
    'Street name / Utca név': {
        'model_field': 'street_name',
        'dtype': str
    },
    'House number / ház szám': {
        'model_field': 'house_number',
        'dtype': str
    },
    'Customer  VAT number / Vevő adószáma 11111111-1-11': {
        'model_field': 'vat_number',
        'dtype': str
    },
    'EU VAT number/Közösségi adószám': {
        'model_field': 'eu_vat_number',
        'dtype': str
    },
    'Payment method/Fizetési mód': {
        'model_field': 'payment_method',
        'dtype': str
    },
    'Payment term/Hány napos fizetési határidő': {
        'model_field': 'payment_term',
        'dtype': 'Int64'  # Nullable integer
    },
    'E-mail address': {
        'model_field': 'email',
        'dtype': str
    },
    'Type of transactions/Tranzakció típusa': {
        'model_field': 'transaction_type',
        'dtype': str
    }
}

INVOICE_COLUMNS = {
    'Customer ID / Vevő azonosító': {
        'model_field': 'customer_id',
        'dtype': str
    },
    'Internal identifier / Belső azonosító': {
        'model_field': 'internal_identifier',
        'dtype': str
    },
    'Type of invoice / Számla típus': {
        'model_field': 'invoice_type',
        'dtype': str
    },
    'Date of invoice / Számla kelte DD.MM.YYYY': {
        'model_field': 'invoice_date',
        'dtype': str
    },
    'Fulfilment date / Teljesítési dátum DD.MM.YYYY': {
        'model_field': 'fulfillment_date',
        'dtype': str
    },
    'Payment due date / Fizetési határidő': {
        'model_field': 'payment_due_date',
        'dtype': str
    },
    'Foreign currency / Devizanem': {
        'model_field': 'foreign_currency',
        'dtype': str
    },
    'Exchange rate / Árfolyam': {
        'model_field': 'exchange_rate',
        'dtype': str  # Will convert to float later with error handling
    },
    'Date of Exchange rate / Árfolyam dátuma': {
        'model_field': 'exchange_rate_date',
        'dtype': str
    },
    'Comment / Megjegyzés': {
        'model_field': 'comment',
        'dtype': str
    },
    'Félretett számla/Set aside invoice': {
        'model_field': 'set_aside_invoice',
        'dtype': str
    },
    'E-invoice or Paper invoice/ Elektronikus vagy papír számla': {
        'model_field': 'e_invoice_or_paper',
        'dtype': str
    },
    'Item description / Tétel megnevezés': {
        'model_field': 'item_description',
        'dtype': str
    },
    'VAT rate / ÁFA': {
        'model_field': 'vat_rate',
        'dtype': str
    },
    'Gross Value / Bruttó összeg (Adott devizában)': {
        'model_field': 'gross_value',
        'dtype': str  # Will convert to float later with error handling
    },
    'Net Value / Nettó összeg (adott devizában)': {
        'model_field': 'net_value',
        'dtype': str  # Will convert to float later with error handling
    },
    'Quantity / Mennyiség': {
        'model_field': 'quantity',
        'dtype': str  # Will convert to float later with error handling
    },
    'Unit / Mennyiségi egység': {
        'model_field': 'unit',
        'dtype': str
    },
    'Unit price / Egységár': {
        'model_field': 'unit_price',
        'dtype': str  # Will convert to float later with error handling
    },
    'Original and advance invoice / Eredeti  és előleg számla': {
        'model_field': 'original_advance_invoice',
        'dtype': str
    }
}
VALUE_MAPPING = {
    'e_invoice_or_paper': {
        'Paper invoice': '0',
        'E-invoice': '1'
    },
    'set_aside_invoice': {
        'igen': '1',
        'nem': '0'
    },
}