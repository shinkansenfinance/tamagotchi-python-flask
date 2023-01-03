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
TAMAGOTCHI_ACCOUNT = PayoutDebtor(
    name=os.getenv("TAMAGOTCHI_LEGAL_NAME", "Fictional Tamagotchi SpA"),
    identification=PersonId("CLID", os.getenv("TAMAGOTCHI_RUT", "11111111-1")),
    financial_institution=TAMAGOTCHI_FI,
    account=os.getenv("TAMAGOTCHI_ACCOUNT_NUMBER", "4242424242424242"),
    account_type=CURRENT_ACCOUNT,
    email=os.getenv("TAMAGOTCHI_EMAIL", "team@shinkansen.cl"),
)
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
