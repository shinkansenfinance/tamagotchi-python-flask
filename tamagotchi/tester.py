from typing import Iterable, Optional, Iterator
from .app import db, app
from .utils import required_env
from .settings import (
    TAMAGOTCHI,
    TAMAGOTCHI_ACCOUNT,
    SHINKANSEN_BASE_URL,
    TAMAGOTCHI_API_KEY,
    TAMAGOTCHI_CERTIFICATE,
    TAMAGOTCHI_CERTIFICATE_PRIVATE_KEY,
)
import json
from sqlalchemy.orm import relationship
from sqlalchemy import func
from shinkansen.payouts import (
    PayoutMessage,
    PayoutMessageHeader,
    PayoutHttpResponse,
    PayoutTransaction,
    PayoutCreditor,
)
from shinkansen.common import PersonId, FinancialInstitution, CLP, SHINKANSEN
from shinkansen.responses import Response


class TestMessage(db.Model):
    __tablename__ = "test_message"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    description = db.Column(db.Text())
    content = db.Column(db.Text())
    http_response = db.Column(db.Text())
    error_message = db.Column(db.Text())
    transaction_id_mapping = db.Column(db.Text())
    suite_id = db.Column(db.Integer, db.ForeignKey("test_suite.id"))
    suite = relationship("TestSuite", back_populates="messages")


class TestResponse(db.Model):
    __tablename__ = "test_response"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    content = db.Column(db.Text())
    suite_id = db.Column(db.Integer, db.ForeignKey("test_suite.id"))
    suite = relationship("TestSuite", back_populates="responses")


class TestSuite(db.Model):
    __tablename__ = "test_suite"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    messages = relationship("TestMessage", back_populates="suite")
    responses = relationship("TestResponse", back_populates="suite")
    status = db.Column(db.Text())

    @classmethod
    def start_new(cls) -> "TestSuite":
        if cls.current():
            raise RuntimeError("There is already a test suite in progress")
        suite = cls(status="running")
        db.session.add(suite)
        db.session.commit()
        return suite

    @classmethod
    def current(cls) -> Optional["TestSuite"]:
        return db.session.query(cls).filter(cls.status == "running").first()

    def finish(self):
        self.status = "finished"
        db.session.commit()

    def add_tester_response(self, response: Response):
        if self.status != "running":
            raise RuntimeError("Test suite is not in progress")
        self.responses.append(
            TestResponse(content=json.dumps(response, default=lambda o: o.__dict__))
        )
        db.session.commit()

    def add_tester_message(
        self,
        description: str,
        message: PayoutMessage,
        http_response: PayoutHttpResponse,
        error_message: str,
    ):
        if self.status != "running":
            raise RuntimeError("Test suite is not in progress")

        self.messages.append(
            TestMessage(
                content=message.as_json(),
                http_response=json.dumps(http_response, default=lambda o: o.__dict__),
                description=description,
                error_message=error_message,
            )
        )
        db.session.commit()

    def shinkansen_messages(self) -> list[PayoutMessage]:
        return [PayoutMessage.from_json(m.content) for m in self.messages]

    def transactions(self) -> list[PayoutTransaction]:
        return [
            tx for message in self.shinkansen_messages() for tx in message.transactions
        ]

    def shinkansen_responses(self) -> list[Response]:
        return [Response.from_json_dict(json.loads(r.content)) for r in self.responses]

    def transactions_with_responses(self) -> dict[PayoutTransaction, Response]:
        # Inefficient, but shouldn't matter for small number of test transactions
        return {
            tx: r
            for tx in self.transactions()
            for r in self.shinkansen_responses()
            if tx.transaction_id == r.transaction_id
        }


def finish_suite():
    suite = TestSuite.current()
    suite.finish()


def creditor_from_colon_separated_string(string: str) -> PayoutCreditor:
    name, rut, bank_id, account_number, account_type, email = string.split(":")
    return PayoutCreditor(
        name=name,
        identification=PersonId("CLID", rut),
        financial_institution=FinancialInstitution(bank_id),
        account=account_number,
        account_type=account_type,
        email=email,
    )


def creditors() -> list[PayoutCreditor]:
    return [
        creditor_from_colon_separated_string(required_env("TESTER_CREDITOR_1")),
        creditor_from_colon_separated_string(required_env("TESTER_CREDITOR_2")),
    ]


def run_new_suite():
    suite = TestSuite.start_new()
    messages = [
        [
            f"One peso single payout {i}-{j}",
            single_payout(creditor, str((i * 500) + (j + 1)), f"Test {i}-{j}"),
        ]
        for i, creditor in enumerate(creditors())
        for j in range(500)
        # ] + [
        #     [f"Few pesos multi payout {i}", few_pesos_multiple_payouts(creditor)]
        #     for i, creditor in enumerate(creditors())
    ] + [
        [f"Too many pesos single payout {i}", too_many_pesos_single_payout(creditor)]
        for i, creditor in enumerate(creditors())
        # ] + [
        #     [f"Mixed creditors", mixed_with_different_creditors(creditors())]
        # ] + [
        #     [f"Lots of payouts {i}", lots_of_one_peso_payouts(creditor)]
        #     for i, creditor in enumerate(creditors())
    ]
    app.logger.warning(f"Running {len(messages)} messages")
    for description, message in messages:
        try:
            error_message = None
            signature, http_response = message.sign_and_send(
                TAMAGOTCHI_CERTIFICATE_PRIVATE_KEY,
                TAMAGOTCHI_CERTIFICATE,
                TAMAGOTCHI_API_KEY,
                base_url=SHINKANSEN_BASE_URL,
            )
        except Exception as e:
            error_message = repr(e)
        suite.add_tester_message(description, message, http_response, error_message)
    app.logger.warning(f"{len(messages)} messages sent")


def execute_tester_message(description: str, message: PayoutMessage):
    try:
        error_message = None
        signature, http_response = message.sign_and_send(
            TAMAGOTCHI_CERTIFICATE_PRIVATE_KEY,
            TAMAGOTCHI_CERTIFICATE,
            TAMAGOTCHI_API_KEY,
            base_url=SHINKANSEN_BASE_URL,
        )
    except Exception as e:
        error_message = repr(e)
    suite = TestSuite.current()
    suite.add_tester_message(description, message, http_response, error_message)


def single_payout(
    creditor: PayoutCreditor, amount: str = None, description: str = None
) -> PayoutMessage:
    return PayoutMessage(
        header=PayoutMessageHeader(sender=TAMAGOTCHI, receiver=SHINKANSEN),
        transactions=[
            PayoutTransaction(
                currency=CLP,
                amount=amount or "1",
                description=description or "Test",
                debtor=TAMAGOTCHI_ACCOUNT,
                creditor=creditor,
            )
        ],
    )


def few_pesos_multiple_payouts(creditor: PayoutCreditor) -> PayoutMessage:
    return PayoutMessage(
        header=PayoutMessageHeader(sender=TAMAGOTCHI, receiver=SHINKANSEN),
        transactions=[
            PayoutTransaction(
                currency=CLP,
                amount="2",
                description="Two pesos with company",
                debtor=TAMAGOTCHI_ACCOUNT,
                creditor=creditor,
            ),
            PayoutTransaction(
                currency=CLP,
                amount="3",
                description="Three pesos with company",
                debtor=TAMAGOTCHI_ACCOUNT,
                creditor=creditor,
            ),
            PayoutTransaction(
                currency=CLP,
                amount="4",
                description="Four pesos with company",
                debtor=TAMAGOTCHI_ACCOUNT,
                creditor=creditor,
            ),
        ],
    )


def too_many_pesos_single_payout(creditor: PayoutCreditor) -> PayoutMessage:
    return PayoutMessage(
        header=PayoutMessageHeader(sender=TAMAGOTCHI, receiver=SHINKANSEN),
        transactions=[
            PayoutTransaction(
                currency=CLP,
                amount="10000000",
                description="Ten million pesos alone",
                debtor=TAMAGOTCHI_ACCOUNT,
                creditor=creditor,
            )
        ],
    )


def mixed_with_different_creditors(
    creditors: Iterable[PayoutCreditor],
) -> PayoutMessage:
    return PayoutMessage(
        header=PayoutMessageHeader(sender=TAMAGOTCHI, receiver=SHINKANSEN),
        transactions=[
            PayoutTransaction(
                currency=CLP,
                amount="3000",
                description="Three thousand pesos mixed creditors",
                debtor=TAMAGOTCHI_ACCOUNT,
                creditor=creditors[0],
            ),
            PayoutTransaction(
                currency=CLP,
                amount="4000",
                description="Four thousand pesos mixed creditors",
                debtor=TAMAGOTCHI_ACCOUNT,
                creditor=creditors[1],
            ),
        ],
    )


def lots_of_one_peso_payouts(creditor: PayoutCreditor):
    n = 100
    return PayoutMessage(
        header=PayoutMessageHeader(sender=TAMAGOTCHI, receiver=SHINKANSEN),
        transactions=[
            PayoutTransaction(
                currency=CLP,
                amount="1",
                description=f"One peso in a long list ({i + 1} of {n}) ",
                debtor=TAMAGOTCHI_ACCOUNT,
                creditor=creditor,
            )
            for i in range(n)
        ],
    )
