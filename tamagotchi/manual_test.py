from .settings import (
    TAMAGOTCHI_ACCOUNTS,
    TAMAGOTCHI,
    SHINKANSEN_BASE_URL,
    TAMAGOTCHI_CERTIFICATE_PRIVATE_KEY,
    TAMAGOTCHI_CERTIFICATE,
    TAMAGOTCHI_API_KEY,
    TAMAGOTCHI_MANUAL_TEST_TARGETS,
)
from shinkansen.payouts import PayoutMessage, PayoutTransaction, PayoutCreditor
from shinkansen.common import (
    CLP,
    SHINKANSEN,
    MessageHeader,
    PersonId,
    FinancialInstitution,
)
from itertools import count

debtor = TAMAGOTCHI_ACCOUNTS[CLP]


def messages(repetitions=1):
    counter = count(1)
    for amount in ("1",) * repetitions:
        for destination in TAMAGOTCHI_MANUAL_TEST_TARGETS.split("\n"):
            name, rut, account, bank, account_type = destination.split(",")
            i = next(counter)
            creditor = PayoutCreditor(
                name=name,
                identification=PersonId("CLID", rut),
                financial_institution=FinancialInstitution(bank),
                account=account,
                account_type=account_type,
                email="administracion@shinkansen.finance",
            )
            transaction = PayoutTransaction(
                currency=CLP,
                amount=amount,
                description=f"Test {i} CLP {amount} a {rut}",
                creditor=creditor,
                debtor=debtor,
            )
            message = PayoutMessage(
                header=MessageHeader(sender=TAMAGOTCHI, receiver=SHINKANSEN),
                transactions=[transaction],
            )
            yield message


def send(message):
    return message.sign_and_send(
        TAMAGOTCHI_CERTIFICATE_PRIVATE_KEY,
        TAMAGOTCHI_CERTIFICATE,
        TAMAGOTCHI_API_KEY,
        base_url=SHINKANSEN_BASE_URL,
    )


def send_in_sequence(messages):
    messages = list(messages)  # Make sure we don't waste time generating the messages
    for message in messages:
        print(send(message))


def send_in_parallel(messages):
    from multiprocessing import Pool
    from multiprocessing import cpu_count

    # Avoid too agressive parallelism by limiting to cpu number.
    # TODO: Use asyncio instead of multiprocessing
    with Pool(cpu_count()) as p:
        print(p.map(send, messages))


if __name__ == "__main__":
    import sys

    repetitions = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    send_in_sequence(messages(repetitions))
