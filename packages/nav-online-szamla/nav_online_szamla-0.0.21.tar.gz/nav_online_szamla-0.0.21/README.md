# NAV Online Számla Python Client

A Python client library for the Hungarian NAV (National Tax and Customs Administration) Online Invoice API.

**⚠️ This project is currently in progress and not yet production-ready. Use at your own risk.**

## Installation

```bash
pip install nav-online-szamla
```

## Usage

```python
from nav_online_szamla import (
    NavOnlineInvoiceClient, NavCredentials, 
    InvoiceDirection, QueryInvoiceDigestRequest, 
    MandatoryQueryParams, InvoiceQueryParams, DateTimeRange
)
from datetime import datetime

# Create credentials
credentials = NavCredentials(
    login="your_nav_login",
    password="your_nav_password", 
    signer_key="your_signer_key",
    tax_number="your_tax_number"
)

# Create API request
request = QueryInvoiceDigestRequest(
    page=1,
    invoice_direction=InvoiceDirection.OUTBOUND,
    invoice_query_params=InvoiceQueryParams(
        mandatory_query_params=MandatoryQueryParams(
            ins_date=DateTimeRange(
                date_time_from="2024-01-01T00:00:00.000Z",
                date_time_to="2024-01-31T23:59:59.999Z"
            )
        )
    )
)

# Query invoices
with NavOnlineInvoiceClient() as client:
    try:
        response = client.query_invoice_digest(credentials, request)
        
        for digest in response.invoice_digests:
            print(f"Invoice: {digest.invoice_number}")
            print(f"Supplier: {digest.supplier_tax_number}")
            print(f"Amount: {digest.invoice_net_amount}")
        
    except Exception as e:
        print(f"Error: {e}")
```

## Contributing

We welcome contributions! Here's how you can help:

1. **Create a branch** from main for your feature or fix
2. **Make your changes** with clear, descriptive commit messages
3. **Add tests** for any new functionality
4. **Ensure all tests pass** by running the test suite
5. **Submit a Pull Request** with a clear description of your changes

### Development Guidelines

- Follow existing code style and patterns
- Write clear docstrings for new functions/classes
- Update README if adding new features
- Handle XML namespace inconsistencies properly (see existing code)

## License

This project is licensed under the MIT License.