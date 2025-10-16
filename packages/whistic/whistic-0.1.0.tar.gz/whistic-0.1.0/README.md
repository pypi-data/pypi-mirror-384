# Whistic SDK

A Python SDK to interface with the Whistic API for vendor management and third-party risk management operations.

## Installation

### From PyPI (Recommended)

```bash
pip install whistic
```

### From Source

```bash
git clone https://github.com/massyn/whistic.git
cd whistic
pip install -e .
```

## Requirements

* Python 3.7 or higher
* Create an [API Key](https://whistichelp.zendesk.com/hc/en-us/articles/14823790530071-API-Key-Creation) on the Whistic platform

## Quick Start

### Environment Setup

The Whistic SDK requires authentication via an API token. You must provide this token through the `WHISTIC_TOKEN` environment variable.

**Method 1: Environment Variable (Linux/macOS)**
```bash
export WHISTIC_TOKEN=your_api_token_here
```

**Method 2: Environment Variable (Windows)**
```cmd
set WHISTIC_TOKEN=your_api_token_here
```

**Method 3: .env File (Recommended for development)**

Create a `.env` file in your project root directory:
```
WHISTIC_TOKEN=your_api_token_here
```

The SDK will automatically load this file when you call `load_dotenv()` in your Python code (as shown in the examples below).

**Important Notes:**
- Never commit your `.env` file or API tokens to version control
- Add `.env` to your `.gitignore` file
- The API token is required for all SDK operations - the client will fail to initialize without it

### Basic Usage

```python
from whistic_sdk import Whistic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize the client
client = Whistic()

# List all vendors
vendors = client.vendors.list()
print(f"Found {len(vendors)} vendors")

# Get detailed information for all vendors (parallel processing)
detailed_vendors = client.vendors.describe()

# Get a specific vendor
vendor_id = vendors[0]['identifier']
vendor_details = client.vendors.get(vendor_id)

# Update a vendor
client.vendors.update(vendor_id, {
    "name": "Updated Vendor Name",
    "description": "Updated description"
})

# Create a new vendor
new_vendor_data = {
    "name": "New Vendor",
    "description": "A new vendor",
    # ... other vendor fields
}
client.vendors.new(new_vendor_data)

# Get vendor by domain
vendor_by_domain = client.vendors.domain("example.com")
if vendor_by_domain:
    print(f"Found vendor: {vendor_by_domain.get('name', 'Unknown')}")

# Get vendor intake form
intake_form = client.vendor_intake_form.get()
print(f"Intake form has {len(intake_form.get('sections', []))} sections")

# Display the form structure with field names
client.vendor_intake_form.show()
```

## Advanced Usage

### Custom Configuration

```python
from whistic_sdk import Whistic

# Configure with custom settings
client = Whistic(max_workers=10)  # Increase parallel processing workers
```

### Batch Operations

```python
# Process all vendors in parallel
all_vendors = client.vendors.describe()

# Filter and update multiple vendors
for vendor in all_vendors:
    if vendor.get('status') == 'pending':
        client.vendors.update(vendor['identifier'], {
            'status': 'active'
        })
```

### Vendor Intake Form

```python
from whistic_sdk.vendorintakeform import VendorFormValidationError

# Get the vendor intake form structure
intake_form = client.vendor_intake_form.get()

if intake_form:
    print(f"Form identifier: {intake_form.get('identifier', 'N/A')}")
    print(f"Number of sections: {len(intake_form.get('sections', []))}")

    # Display section information
    for section in intake_form.get('sections', []):
        print(f"Section: {section.get('title', 'Unnamed')}")
        for column in section.get('columns', []):
            questions = column.get('questions', [])
            print(f"  Questions: {len(questions)}")

# Display the form structure for easy reference
# This prints all field names in "Section:Question" format
client.vendor_intake_form.show()

# Submit a new vendor intake form
# Field names use the format "Section:Question"
vendor_data = {
    "Vendor Information:Vendor URL": "example-vendor.com",
    "Vendor Information:Vendor Name": "Example Vendor Inc.",
    "Vendor Information:Product / Service Name": "Cloud Security Platform",
    "Vendor Information:Write a description of the vendor / service": "A comprehensive security solution",
    "Vendor Information:First Name": "John",
    "Vendor Information:Last Name": "Smith",
    "Vendor Information:Email Address": "john.smith@example-vendor.com",
    "Vendor Information:Job Title": "Security Manager",
    "Primary Business Owner Information:First Name": "Jane",
    "Primary Business Owner Information:Last Name": "Doe",
    "Primary Business Owner Information:Email Address": "jane.doe@yourcompany.com"
    # ... add other required fields in "Section:Question" format
}

# Submit the vendor intake form (validates all required fields)
try:
    success = client.vendor_intake_form.vendor_intake(vendor_data)
    if success:
        print("Vendor intake form submitted successfully!")
except VendorFormValidationError as e:
    print(f"Form validation failed: {e}")
```

### Error Handling

```python
import logging

# Enable debug logging to see API calls
logging.basicConfig(level=logging.DEBUG)

try:
    vendor = client.vendors.get('non-existent-id')
except Exception as e:
    print(f"Error fetching vendor: {e}")
```

## API Reference

### Whistic Class

The main client class for interacting with the Whistic API.

#### Constructor
- `Whistic(max_workers=5)`: Initialize client with optional max workers for parallel processing

#### Properties
- `vendors`: Access to vendor management operations
- `vendor_intake_form`: Access to vendor intake form operations

### Vendors Class

Handles all vendor-related operations.

#### Methods

- **`list()`**: Get paginated list of all vendor identifiers
  - Returns: List of vendor objects with basic information

- **`describe()`**: Get detailed information for all vendors using parallel processing
  - Returns: List of complete vendor objects with all details

- **`get(vendor_id)`**: Fetch detailed information for a specific vendor
  - Parameters: `vendor_id` (str) - The vendor identifier
  - Returns: Complete vendor object or None if not found

- **`update(vendor_id, data)`**: Update vendor information
  - Parameters: 
    - `vendor_id` (str) - The vendor identifier
    - `data` (dict) - Dictionary with fields to update
  - Note: Uses deep merge to preserve existing data

- **`new(data)`**: Create a new vendor
  - Parameters: `data` (dict) - Complete vendor data structure

- **`domain(domain)`**: Retrieve vendor details by domain name
  - Parameters: `domain` (str) - The domain name to search for
  - Returns: Vendor object if found, or None if not found

### VendorIntakeForm Class

Handles vendor intake form operations.

#### Methods

- **`get()`**: Retrieve the vendor intake form structure
  - Returns: Complete intake form object with sections, columns, and questions, or None if not found
  - The form contains all the questions and structure that vendors see during onboarding
  - Includes metadata like identifiers, answer options, and required fields

- **`show()`**: Display the form structure for reference
  - Prints all field names in "Section:Question" format to the console
  - Useful for understanding the form structure and field names needed for submission
  - No return value - outputs directly to console

- **`vendor_intake(data)`**: Submit a new vendor intake form
  - Parameters:
    - `data` (dict) - Dictionary containing form field values using "Section:Question" format as keys
  - Returns: Boolean indicating success (True) or failure (False) of submission
  - Raises: `VendorFormValidationError` if required fields are missing or invalid
  - Validates required fields and answer options before submission
  - Automatically formats data into proper API submission structure
  - Creates custom attributes from fields not in the standard vendor creation payload
  - Example: `client.vendor_intake_form.vendor_intake({"Vendor Information:Vendor URL": "example.com", "Vendor Information:Vendor Name": "Example Inc."})`

## Features

- **Automatic Pagination**: Handles API pagination automatically
- **Parallel Processing**: Concurrent API calls for better performance
- **Rate Limiting**: Built-in retry logic with exponential backoff
- **Deep Merge Updates**: Safely update vendor data without losing existing fields
- **Colored Logging**: Enhanced console output for debugging
- **Environment Variable Support**: Secure token management

## Error Handling

The SDK includes comprehensive error handling:

- **Rate Limiting**: Automatic retry with exponential backoff for 429 responses
- **Request Timeouts**: 30-second timeout on all API calls
- **Connection Errors**: Graceful handling of network issues
- **API Errors**: Detailed error logging with response codes and messages

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Reference

* [Whistic API Documentation](https://public.whistic.com/swagger-ui/index.html)
* [API Key Creation Guide](https://whistichelp.zendesk.com/hc/en-us/articles/14823790530071-API-Key-Creation)
