import os
import re
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from fastapi.security import HTTPBearer, HTTPException as FastAPIHTTPException
import uvicorn

app = FastAPI(title="VAT Validator API", version="1.0.0")
# === BT Builds Standard Middleware (auto-injected) ===
from fastapi.middleware.cors import CORSMiddleware as _BTCors
app.add_middleware(_BTCors, allow_origins=["*"], allow_methods=["*"],
    allow_headers=["*"], expose_headers=["X-RateLimit-Limit","X-RateLimit-Remaining","X-RateLimit-Reset"])

@app.middleware("http")
async def _bt_add_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Powered-By"] = "btbuilds"
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response


security = HTTPBearer()

# Simple in-memory rate limiting
rate_limit_store = {}

def verify_api_key(credentials = Depends(security)):
    api_key = credentials.credentials
    expected_key = os.getenv("API_KEY", "demo-key-change-in-production")
    if api_key != expected_key:
        raise FastAPIHTTPException(status_code=401, detail="Invalid API key")
    return api_key

def check_rate_limit(api_key: str):
    import time
    current_time = time.time()
    if api_key not in rate_limit_store:
        rate_limit_store[api_key] = []
    rate_limit_store[api_key] = [t for t in rate_limit_store[api_key] if current_time - t < 60]
    if len(rate_limit_store[api_key]) >= 100:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    rate_limit_store[api_key].append(current_time)

class VATRequest(BaseModel):
    vat_number: str

class VATResponse(BaseModel):
    vat_number: str
    is_valid: bool
    format_valid: bool
    country_code: str
    normalized: str
    message: str

def normalize_vat(vat: str) -> str:
    """Normalize VAT number: uppercase, remove spaces"""
    return re.sub(r'\s+', '', vat.upper())

def validate_vat_format(vat: str) -> tuple[bool, str]:
    """Validate VAT format without external calls. Returns (is_valid, country_code)"""
    normalized = normalize_vat(vat)
    
    # VAT format patterns by country
    patterns = {
        'AT': r'^ATU\d{8}$',
        'BE': r'^BE0?\d{8,10}$',
        'BG': r'^BG\d{9,10}$',
        'HR': r'^HR\d{11}$',
        'CY': r'^CY\d{9}[A-Z]$',
        'CZ': r'^CZ\d{8,10}$',
        'DK': r'^DK\d{8}$',
        'EE': r'^EE\d{9}$',
        'FI': r'^FI\d{8}$',
        'FR': r'^FR[A-Z0-9]{2}\d{9}$',
        'DE': r'^DE\d{9}$',
        'EL': r'^EL\d{9}$',
        'HU': r'^HU\d{8}$',
        'IE': r'^IE\d[A-Z0-9]{8}$|^IE\d{8}[A-Z]{2}$',
        'IT': r'^IT\d{11}$',
        'LV': r'^LV\d{11}$',
        'LT': r'^LT\d{9}$|^LT\d{12}$',
        'LU': r'^LU\d{8}$',
        'MT': r'^MT\d{8}$',
        'NL': r'^NL\d{9}B\d{2}$',
        'PL': r'^PL\d{10}$',
        'PT': r'^PT\d{9}$',
        'RO': r'^RO\d{2,10}$',
        'SK': r'^SK\d{10}$',
        'SI': r'^SI\d{8}$',
        'ES': r'^ES[a-zA-Z0-9]\d{7}[a-zA-Z0-9]$',
        'SE': r'^SE\d{12}$',
        'XI': r'^XI\d{12}$',  # Northern Ireland
    }
    
    country_code = normalized[:2]
    
    if country_code in patterns:
        if re.match(patterns[country_code], normalized):
            return True, country_code
    
    return False, country_code

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/validate")
def validate_vat(request: VATRequest, api_key: str = Depends(verify_api_key)):
    check_rate_limit(api_key)
    
    normalized = normalize_vat(request.vat_number)
    format_valid, country_code = validate_vat_format(request.vat_number)
    
    if format_valid:
        response = VATResponse(
            vat_number=request.vat_number,
            is_valid=True,
            format_valid=True,
            country_code=country_code,
            normalized=normalized,
            message=f"VAT number format is valid for {country_code}"
        )
    else:
        response = VATResponse(
            vat_number=request.vat_number,
            is_valid=False,
            format_valid=False,
            country_code=country_code,
            normalized=normalized,
            message=f"Invalid VAT number format for {country_code}"
        )
    
    return response

@app.post("/parse")
def parse_vat(request: VATRequest, api_key: str = Depends(verify_api_key)):
    check_rate_limit(api_key)
    
    normalized = normalize_vat(request.vat_number)
    format_valid, country_code = validate_vat_format(request.vat_number)
    
    return {
        "original": request.vat_number,
        "normalized": normalized,
        "country_code": country_code,
        "format_valid": format_valid,
        "length": len(normalized)
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

try:
    from mangum import Mangum
    handler = Mangum(app, lifespan="off")
except ImportError:
    pass
