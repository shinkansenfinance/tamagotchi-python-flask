import os, re, click
from flask import Flask, render_template, redirect, request, flash, abort
from flask_sqlalchemy import SQLAlchemy
from shinkansen.payouts import (
    PayoutMessage,
    PayoutMessageHeader,
    PayoutTransaction,
    PayoutCreditor,
    PayoutDebtor,
    FinancialInstitution,
    PersonId,
    MAIN_BANKS,
    ACCOUNT_TYPES,
    CURRENT_ACCOUNT,
    SHINKANSEN,
    CLP,
)
from shinkansen.responses import ResponseMessage, PayoutResponse
from shinkansen import jws

TAMAGOTCHI = FinancialInstitution(os.getenv("TAMAGOTCHI_SENDER", "TAMAGOTCHI"))
BICE = FinancialInstitution("BANCO_BICE_CL")
TAMAGOTCHI_ACCOUNT = PayoutDebtor(
    name=os.getenv("TAMAGOTCHI_LEGAL_NAME", "Fictional Tamagotchi SpA"),
    identification=PersonId("CLID", os.getenv("TAMAGOTCHI_RUT", "11111111-1")),
    financial_institution=BICE,
    account=os.getenv("TAMAGOTCHI_ACCOUNT_NUMBER", "4242424242424242"),
    account_type=CURRENT_ACCOUNT,
    email=os.getenv("TAMAGOTCHI_EMAIL", "team@shinkansen.cl"),
)


def required_env(key):
    if key not in os.environ:
        raise RuntimeError(f"Required {key} variable not present in environment")
    return os.environ[key]


TAMAGOTCHI_API_KEY = required_env("TAMAGOTCHI_API_KEY")
TAMAGOTCHI_CERTIFICATE = jws.certificate_from_pem_bytes(
    required_env("TAMAGOTCHI_CERTIFICATE").encode("UTF-8")
)
TAMAGOTCHI_CERTIFICATE_PRIVATE_KEY = jws.private_key_from_pem_bytes(
    required_env("TAMAGOTCHI_CERTIFICATE_PRIVATE_KEY").encode("UTF-8")
)
TAMAGOTCHI_API_KEY = required_env("TAMAGOTCHI_API_KEY")

SHINKANSEN_CERTIFICATE_1 = required_env("SHINKANSEN_CERTIFICATE_1")
SHINKANSEN_CERTIFICATE_2 = os.getenv("SHINKANSEN_CERTIFICATE_2")

SHINKANSEN_CERTIFICATES = [
    jws.certificate_from_pem_bytes(c.encode("UTF-8"))
    for c in [SHINKANSEN_CERTIFICATE_1, SHINKANSEN_CERTIFICATE_2]
    if c is not None
]

TAMAGOTCHI_MAX_AMOUNT = os.getenv("TAMAGOTCHI_MAX_AMOUNT")


def force_rut_format(raw_rut: str) -> str:
    rut = re.sub(r"[^\dkK]+", "", raw_rut)
    return rut[:-1] + "-" + rut[-1]


def transaction_from_form_input(form: dict) -> PayoutTransaction:
    amount = re.sub(r"[^\d]+", "", form["amount"])
    description = form["description"]
    if TAMAGOTCHI_MAX_AMOUNT and int(amount) > int(TAMAGOTCHI_MAX_AMOUNT):
        amount = TAMAGOTCHI_MAX_AMOUNT
    return PayoutTransaction(
        currency=CLP,
        amount=amount,
        description=description,
        debtor=TAMAGOTCHI_ACCOUNT,
        creditor=creditor_from_form_input(form),
    )


def creditor_from_form_input(form: dict) -> PayoutCreditor:
    name = form["name"]
    rut = force_rut_format(form["rut"])
    email = form["email"]
    bank_id = form["bank_id"]
    account_number = form["account_number"]
    account_type = form["account_type"]
    return PayoutCreditor(
        name=name,
        identification=PersonId("CLID", rut),
        financial_institution=FinancialInstitution(bank_id),
        account=account_number,
        account_type=account_type,
        email=email,
    )


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{app.instance_path}/db.sqlite"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = required_env("FLASK_SECRET_KEY")
db = SQLAlchemy(app)


class PersistedSingleTransactionPayoutMessage(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    shinkansen_transaction_id = db.Column(db.String(36))
    content = db.Column(db.Text())
    signature = db.Column(db.Text())
    response_content = db.Column(db.Text())
    response_signature = db.Column(db.Text())

    def __repr__(self) -> str:
        return "<Payout %r>" % self.content

    def __init__(
        self, message: PayoutMessage, signature: str, shinkansen_transaction_id: str
    ) -> None:
        super().__init__()
        self.id = message.id
        self.content = message.as_json()
        self.signature = signature
        self.shinkansen_transaction_id = shinkansen_transaction_id

    @property
    def message(self) -> PayoutMessage:
        return PayoutMessage.from_json(self.content)

    @property
    def status(self) -> str:
        return (
            self.response.shinkansen_transaction_status if self.response else "pending"
        )

    @property
    def response_status(self) -> str:
        return self.response.response_status if self.response else None

    @property
    def transaction(self) -> PayoutTransaction:
        return self.message.transactions[0]

    @property
    def transaction_id(self) -> str:
        return self.transaction.transaction_id

    @property
    def amount(self):
        return f"{int(self.transaction.amount):,}".replace(",", ".")

    @property
    def creation_date(self):
        return self.message.header.creation_date.replace("T", " ")

    @property
    def destination_name(self):
        return self.transaction.creditor.name

    @property
    def destination_rut(self):
        return self.transaction.creditor.identification.id

    @property
    def destination_email(self):
        return self.transaction.creditor.email

    @property
    def destination_bank(self):
        return self.transaction.creditor.financial_institution.fin_id

    @property
    def destination_account(self):
        return self.transaction.creditor.account

    @property
    def destination_account_type(self):
        return self.transaction.creditor.account_type

    @property
    def response(self) -> PayoutResponse:
        if self.response_content is None:
            return None
        response_message = ResponseMessage.from_json(self.response_content)
        # We have a full response message which might contain responses for
        # multiple transactions. We only care about the response for the
        # transaction id we sent.
        return next(
            r
            for r in response_message.responses
            if r.shinkansen_transaction_id == self.shinkansen_transaction_id
        )


def new_header() -> PayoutMessageHeader:
    return PayoutMessageHeader(sender=TAMAGOTCHI, receiver=SHINKANSEN)


@app.get("/")
def index():
    return redirect("/payouts/")


@app.get("/payouts/")
def payouts():
    return render_template(
        "payouts.html", payouts=PersistedSingleTransactionPayoutMessage.query.all()
    )


@app.post("/payouts/")
def post_payout():
    single_payout_message = PayoutMessage(
        header=new_header(), transactions=[transaction_from_form_input(request.form)]
    )
    signature, response = single_payout_message.sign_and_send(
        TAMAGOTCHI_CERTIFICATE_PRIVATE_KEY,
        TAMAGOTCHI_CERTIFICATE,
        TAMAGOTCHI_API_KEY,
        base_url="https://testing.shinkansen.finance/v1",
    )
    if response.http_status_code in (200, 409):
        shinkansen_transaction_id = response.transaction_ids[
            single_payout_message.transactions[0].transaction_id
        ]
        persisted_payout = PersistedSingleTransactionPayoutMessage(
            message=single_payout_message,
            signature=signature,
            shinkansen_transaction_id=shinkansen_transaction_id,
        )
        db.session.add(persisted_payout)
        db.session.commit()
    else:
        flash(
            "Error al enviar payout a Shinkansen: "
            f"HTTP Status: {response.http_status_code}."
            f"Errors: {response.errors}.",
            "error",
        )
    return redirect("/payouts/")


@app.get("/payouts/<id>")
def payout(id: str):
    return render_template(
        "payout.html", payout=PersistedSingleTransactionPayoutMessage.query.get(id)
    )


@app.get("/payouts/new")
def new_payout():
    return render_template(
        "new_payout.html",
        banks=MAIN_BANKS["CL"],
        account_types=ACCOUNT_TYPES,
        max_amount=TAMAGOTCHI_MAX_AMOUNT,
    )


@app.post("/shinkansen/messages/")
def post_shinkansen_message():
    try:
        json_data = request.get_data(as_text=True)
        app.logger.info("message received: %s", json_data)
        message = ResponseMessage.from_json(json_data)
    except Exception as e:
        logging.error(f"Error parsing message: {e}")
        abort(400, "Error parsing message")

    if "Shinkansen-JWS-Signature" not in request.headers:
        logging.error("Missing signature")
        abort(400, "Missing Shinkansen-JWS-Signature header")

    signature = request.headers["Shinkansen-JWS-Signature"]
    app.logger.info("signature: %s", json_data)

    try:
        message.verify(signature, SHINKANSEN_CERTIFICATES, SHINKANSEN, TAMAGOTCHI)
    except Exception as e:
        logging.error(f"Error verifying signature: {e}")
        abort(400, "Error verifying signature")
    for response in message.responses:
        PersistedSingleTransactionPayoutMessage.query.filter_by(
            shinkansen_transaction_id=response.shinkansen_transaction_id
        ).update(
            {
                "response_content": json_data,
                "response_signature": signature,
            }
        )
    db.session.commit()
    return ("", 200)


@app.cli.add_command
@click.command("init-db")
def init_db():
    db.create_all()
    click.echo(f'Initialized the database: {app.config["SQLALCHEMY_DATABASE_URI"]}')
