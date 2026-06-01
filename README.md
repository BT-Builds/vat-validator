# VAT Validator API

FastAPI service that validates EU VAT numbers without external calls.

## Endpoints

### `GET /health`
Health check endpoint - no auth required.

### `POST /validate`
Validate a VAT number format.

**Headers:**
- `Authorization: Bearer <API_KEY>`

**Body:**
```json
{
  "vat_number": "DE276452187"
}
```

**Response:**
```json
{
  "vat_number": "DE276452187",
  "is_valid": true,
  "format_valid": true,
  "country_code": "DE",
  "normalized": "DE276452187",
  "message": "VAT number format is valid for DE"
}
```

### `POST /parse`
Parse a VAT number and get components.

**Same auth as /validate**

**Response:**
```json
{
  "original": "DE 276 452 187",
  "normalized": "DE276452187",
  "country_code": "DE",
  "format_valid": true,
  "length": 11
}
```

## Supported Countries

AT, BE, BG, HR, CY, CZ, DK, EE, FI, FR, DE, EL, HU, IE, IT, LV, LT, LU, MT, NL, PL, PT, RO, SK, SI, ES, SE, XI

## Curl Examples

```bash
# Validate
curl -X POST https://vat-validator.vercel.app/validate \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"vat_number": "DE276452187"}'

# Parse
curl -X POST https://vat-validator.vercel.app/parse \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"vat_number": "FR 40 303 265 044"}'
```

## Monetize

List on RapidAPI for $15/month team plans. Target: e-commerce platforms, accounting software, B2B marketplaces.