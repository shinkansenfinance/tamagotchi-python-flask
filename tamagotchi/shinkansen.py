import os
from .utils import required_env
from shinkansen import jws
from shinkansen.payouts import (
    PayoutDebtor,
    FinancialInstitution,
    PersonId,
    CURRENT_ACCOUNT,
)

TAMAGOTCHI = FinancialInstitution(os.getenv("TAMAGOTCHI_SENDER", "TAMAGOTCHI"))
TAMAGOTCHI_FI = FinancialInstitution(os.getenv("TAMAGOTCHI_FI", "BANCO_BICE_CL"))
TAMAGOTCHI_CLID = os.getenv(
    "TAMAGOTCHI_CLID", os.getenv("TAMAGOTCHI_RUT", "11111111-1")
)
TAMAGOTCHI_MXRFC = os.getenv("TAMAGOTCHI_MXRFC", "XAXX010101000")
TAMAGOTCHI_CONIT = os.getenv("TAMAGITCHI_CONIT", "123456789")
TAMAGOTCHI_LEGAL_NAME = os.getenv("TAMAGOTCHI_LEGAL_NAME", "Fictional Tamagotchi")
TAMAGOTCHI_ACCOUNT_NUMBER_CLP = os.getenv(
    "TAMAGOTCHI_ACCOUNT_NUMBER_CLP",
    os.getenv("TAMAGOTCHI_ACCOUNT_NUMBER", "4242424242424242"),
)
TAMAGOTCHI_ACCOUNT_NUMBER_COP = os.getenv(
    "TAMAGOTCHI_ACCOUNT_NUMBER_COP", "4242424242424242"
)
TAMAGOTCHI_ACCOUNT_NUMBER_MXN = os.getenv(
    "TAMAGOTCHI_ACCOUNT_NUMBER_MXN", "4242424242424242"
)
TAMAGOTCHI_EMAIL = os.getenv("TAMAGOTCHI_EMAIL", "team@shinkansen.cl")

TAMAGOTCHI_ACCOUNT = PayoutDebtor(
    name=TAMAGOTCHI_LEGAL_NAME,
    identification=PersonId("CLID", TAMAGOTCHI_CLID),
    financial_institution=TAMAGOTCHI_FI,
    account=TAMAGOTCHI_ACCOUNT_NUMBER_CLP,
    account_type=CURRENT_ACCOUNT,
    email=TAMAGOTCHI_EMAIL,
)

TAMAGOTCHI_ACCOUNTS = {
    "CLP": TAMAGOTCHI_ACCOUNT,
    "COP": PayoutDebtor(
        name=TAMAGOTCHI_LEGAL_NAME,
        identification=PersonId("CONIT", TAMAGOTCHI_CONIT),
        financial_institution=TAMAGOTCHI_FI,
        account=TAMAGOTCHI_ACCOUNT_NUMBER_COP,
        account_type=CURRENT_ACCOUNT,
        email=TAMAGOTCHI_EMAIL,
    ),
    "MXN": PayoutDebtor(
        name=TAMAGOTCHI_LEGAL_NAME,
        identification=PersonId("MXRFC", TAMAGOTCHI_MXRFC),
        financial_institution=TAMAGOTCHI_FI,
        account=TAMAGOTCHI_ACCOUNT_NUMBER_MXN,
        account_type=CURRENT_ACCOUNT,
        email=TAMAGOTCHI_EMAIL,
    ),
}

TAMAGOTCHI_API_KEY = required_env("TAMAGOTCHI_API_KEY")
TAMAGOTCHI_CERTIFICATE = jws.certificate_from_pem_bytes(
    required_env("TAMAGOTCHI_CERTIFICATE").encode("UTF-8")
)
TAMAGOTCHI_CERTIFICATE_PRIVATE_KEY = jws.private_key_from_pem_bytes(
    required_env("TAMAGOTCHI_CERTIFICATE_PRIVATE_KEY").encode("UTF-8")
)
SHINKANSEN_CERTIFICATE_1 = required_env("SHINKANSEN_CERTIFICATE_1")
SHINKANSEN_CERTIFICATE_2 = os.getenv("SHINKANSEN_CERTIFICATE_2")
SHINKANSEN_CERTIFICATES = [
    jws.certificate_from_pem_bytes(c.encode("UTF-8"))
    for c in [SHINKANSEN_CERTIFICATE_1, SHINKANSEN_CERTIFICATE_2]
    if c is not None
]
TAMAGOTCHI_MAX_AMOUNT = os.getenv("TAMAGOTCHI_MAX_AMOUNT")

SHINKANSEN_API_HOST = os.getenv("SHINKANSEN_API_HOST", "dev.shinkansen.finance")
SHINKANSEN_BASE_URL = f"https://{SHINKANSEN_API_HOST}/v1"
