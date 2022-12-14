import re
from typing import Optional, Tuple
from flask import render_template, redirect, request, flash, abort
from shinkansen.responses import ResponseMessage
from shinkansen.common import SHINKANSEN, MAIN_BANKS, ACCOUNT_TYPES
from shinkansen.payouts import (
    PayoutMessage,
    PayoutMessageHeader,
    PayoutTransaction,
    PayoutCreditor,
    FinancialInstitution,
    PersonId,
    CLP,
)
from .app import app, db
from .models import PersistedSingleTransactionPayoutMessage
from .tester import TestSuite, run_new_suite, finish_suite
from .shinkansen import (
    TAMAGOTCHI,
    TAMAGOTCHI_ACCOUNT,
    TAMAGOTCHI_API_KEY,
    TAMAGOTCHI_CERTIFICATE,
    TAMAGOTCHI_CERTIFICATE_PRIVATE_KEY,
    SHINKANSEN_CERTIFICATES,
    TAMAGOTCHI_MAX_AMOUNT,
    SHINKANSEN_BASE_URL,
)


def force_rut_format(raw_rut: str) -> str:
    rut = re.sub(r"[^\dkK]+", "", raw_rut)
    return rut[:-1] + "-" + rut[-1]


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
        base_url=SHINKANSEN_BASE_URL,
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
        banks=banks(),
        account_types=ACCOUNT_TYPES,
        max_amount=TAMAGOTCHI_MAX_AMOUNT,
    )


def banks():
    list = MAIN_BANKS["CL"]
    list["SIMULATED_BANK"] = "Simulated Bank"
    return list


def response_message_from_request(request) -> ResponseMessage:
    try:
        json_data = request.get_data(as_text=True)
        app.logger.info("message received: %s", json_data)
        return ResponseMessage.from_json(json_data)
    except Exception as e:
        app.logger.error(f"Error parsing message: {e}")
        abort(400, "Error parsing message")


def signature_from_request(request) -> str:
    if "Shinkansen-JWS-Signature" not in request.headers:
        app.logger.error("Missing signature")
        abort(400, "Missing Shinkansen-JWS-Signature header")
    signature = request.headers["Shinkansen-JWS-Signature"]
    app.logger.info("signature: %s", signature)
    return signature


def verify_signature(message: ResponseMessage, signature: str):
    try:
        message.verify(signature, SHINKANSEN_CERTIFICATES, SHINKANSEN, TAMAGOTCHI)
    except Exception as e:
        app.logger.error(f"Error verifying signature: {e}")
        abort(400, "Error verifying signature")


def persisted_message_for_shinkansen_transaction_id(
    shinkansen_transaction_id: str,
) -> Optional[PersistedSingleTransactionPayoutMessage]:
    return PersistedSingleTransactionPayoutMessage.query.filter_by(
        shinkansen_transaction_id=shinkansen_transaction_id
    ).first()


@app.post("/shinkansen/messages/")
def post_shinkansen_message():
    message = response_message_from_request(request)
    signature = signature_from_request(request)
    verify_signature(message, signature)
    for response in message.responses:
        persisted_message = persisted_message_for_shinkansen_transaction_id(
            response.shinkansen_transaction_id
        )
        if persisted_message:
            persisted_message.response_content = message.original_json
            persisted_message.response_signature = signature
        else:
            if TestSuite.current():
                TestSuite.current().add_tester_response(response)
            else:
                app.logger.error(
                    "Received response for unknown transaction: %s",
                    response.shinkansen_transaction_id,
                )
    db.session.commit()
    return ("", 200)


# Extra endpoints for testing purposes
@app.get("/tester/")
def show_tester():
    current_suite = TestSuite.current()
    if current_suite:
        transactions_with_responses = current_suite.transactions_with_responses()
        n_transactions_sent = len(current_suite.transactions())
        shinkansen_messages = current_suite.shinkansen_messages()
        n_responses_received = len(transactions_with_responses)
    else:
        transactions_with_responses = {}
        n_transactions_sent = 0
        shinkansen_messages = []
        n_responses_received = 0
    return render_template(
        "tester.html",
        current_suite=current_suite,
        transactions_with_responses=transactions_with_responses,
        shinkansen_messages=shinkansen_messages,
        n_transactions_sent=n_transactions_sent,
        n_responses_received=n_responses_received,
    )


@app.post("/tester/start")
def start_tester():
    run_new_suite()
    return redirect("/tester/")


@app.post("/tester/stop")
def stop_tester():
    finish_suite()
    return redirect("/tester/")
