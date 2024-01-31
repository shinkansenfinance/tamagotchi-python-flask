from .app import db
from shinkansen.payouts import PayoutMessage, PayoutTransaction
from shinkansen.payins import PayinMessage, PayinTransaction
from shinkansen.responses import ResponseMessage, PayoutResponse, PayinResponse


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
    def currency(self):
        return self.transaction.currency

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
    def description(self):
        return self.transaction.description

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


class PersistedSingleTransactionPayinMessage(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    shinkansen_transaction_id = db.Column(db.String(36))
    content = db.Column(db.Text())
    signature = db.Column(db.Text())
    response_content = db.Column(db.Text())
    response_signature = db.Column(db.Text())

    def __repr__(self) -> str:
        return "<Payin %r>" % self.content

    def __init__(
        self, message: PayinMessage, signature: str, shinkansen_transaction_id: str
    ) -> None:
        super().__init__()
        self.id = message.id
        self.content = message.as_json()
        self.signature = signature
        self.shinkansen_transaction_id = shinkansen_transaction_id

    @property
    def message(self) -> PayinMessage:
        return PayinMessage.from_json(self.content)

    @property
    def status(self) -> str:
        return (
            self.response.shinkansen_transaction_status if self.response else "pending"
        )

    @property
    def response_status(self) -> str:
        return self.response.response_status if self.response else None

    @property
    def transaction(self) -> PayinTransaction:
        return self.message.transactions[0]

    @property
    def transaction_id(self) -> str:
        return self.transaction.transaction_id

    @property
    def amount(self):
        return f"{int(self.transaction.amount):,}".replace(",", ".")

    @property
    def currency(self):
        return self.transaction.currency

    @property
    def creation_date(self):
        return self.message.header.creation_date.replace("T", " ")

    @property
    def description(self):
        return self.transaction.description

    @property
    def response(self) -> PayinResponse:
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
