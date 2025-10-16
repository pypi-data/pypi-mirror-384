"""Pure sync tests for token operations."""

import pytest

from ethereal.rest.util import ensure_bytes32_hex

DEFAULT_DESTINATION_ENDPOINT = 0


def test_prepare_withdraw_token(rc_ro, network):
    subaccounts = rc_ro.list_subaccounts(sender=rc_ro.chain.address)
    sub = subaccounts[0]
    tokens = rc_ro.list_tokens()
    if not tokens:
        pytest.skip("No tokens available for testing")
    token = tokens[0]
    destination_endpoint = DEFAULT_DESTINATION_ENDPOINT
    destination_address = rc_ro.chain.address
    dto = rc_ro.prepare_withdraw_token(
        subaccount=sub.name,
        token=token.address,
        amount=100000,
        account=rc_ro.chain.address,
        destination_address=destination_address,
        destination_endpoint=destination_endpoint,
    )
    assert (
        isinstance(dto, rc_ro._models.InitiateWithdrawDto)
        and dto.data.token == token.address
        and dto.data.subaccount == sub.name
        and dto.data.amount == 100000
        and dto.data.account == rc_ro.chain.address
        and dto.signature == ""
        and dto.data.lz_destination_address == ensure_bytes32_hex(destination_address)
        and dto.data.lz_destination_eid.value == destination_endpoint
    )


def test_prepare_and_sign_withdraw_token(rc, network):
    subaccounts = rc.list_subaccounts(sender=rc.chain.address)
    sub = subaccounts[0]
    token = rc.list_tokens()[0]
    destination_address = rc.chain.address
    dto = rc.prepare_withdraw_token(
        subaccount=sub.name,
        token=token.address,
        amount=100000,
        account=rc.chain.address,
        destination_address=destination_address,
        destination_endpoint=DEFAULT_DESTINATION_ENDPOINT,
    )
    signed = rc.sign_withdraw_token(dto)
    assert isinstance(signed, rc._models.InitiateWithdrawDto) and signed.signature != ""


def test_prepare_with_automatic_signing(rc, network):
    subaccounts = rc.list_subaccounts(sender=rc.chain.address)
    sub = subaccounts[0]
    token = rc.list_tokens()[0]
    destination_address = rc.chain.address
    dto = rc.prepare_withdraw_token(
        subaccount=sub.name,
        token=token.address,
        amount=100000,
        account=rc.chain.address,
        include_signature=True,
        destination_address=destination_address,
        destination_endpoint=DEFAULT_DESTINATION_ENDPOINT,
    )
    assert isinstance(dto, rc._models.InitiateWithdrawDto) and dto.signature != ""


def test_prepare_withdraw_token_with_custom_nonce(rc_ro, network):
    subaccounts = rc_ro.list_subaccounts(sender=rc_ro.chain.address)
    sub = subaccounts[0]
    tokens = rc_ro.list_tokens()
    if not tokens:
        pytest.skip("No tokens available for testing")
    token = tokens[0]
    nonce = "123456789"
    destination_address = rc_ro.chain.address
    dto = rc_ro.prepare_withdraw_token(
        subaccount=sub.name,
        token=token.address,
        amount=100000,
        account=rc_ro.chain.address,
        destination_address=destination_address,
        destination_endpoint=DEFAULT_DESTINATION_ENDPOINT,
        nonce=nonce,
    )
    assert (
        isinstance(dto, rc_ro._models.InitiateWithdrawDto) and dto.data.nonce == nonce
    )


def test_prepare_withdraw_token_with_custom_signed_at(rc_ro, network):
    subaccounts = rc_ro.list_subaccounts(sender=rc_ro.chain.address)
    sub = subaccounts[0]
    token = rc_ro.list_tokens()[0]
    ts = 1620000000
    destination_address = rc_ro.chain.address
    dto = rc_ro.prepare_withdraw_token(
        subaccount=sub.name,
        token=token.address,
        amount=100000,
        account=rc_ro.chain.address,
        destination_address=destination_address,
        destination_endpoint=DEFAULT_DESTINATION_ENDPOINT,
        signed_at=ts,
    )
    assert (
        isinstance(dto, rc_ro._models.InitiateWithdrawDto) and dto.data.signed_at == ts
    )


def test_prepare_withdraw_token_with_custom_destination(rc_ro, network):
    subaccounts = rc_ro.list_subaccounts(sender=rc_ro.chain.address)
    sub = subaccounts[0]
    tokens = rc_ro.list_tokens()
    if not tokens:
        pytest.skip("No tokens available for testing")
    token = tokens[0]
    destination_address = rc_ro.chain.address
    destination_endpoint = 10422
    dto = rc_ro.prepare_withdraw_token(
        subaccount=sub.name,
        token=token.address,
        amount=100000,
        account=rc_ro.chain.address,
        destination_address=destination_address,
        destination_endpoint=destination_endpoint,
    )
    assert (
        isinstance(dto, rc_ro._models.InitiateWithdrawDto)
        and dto.data.token == token.address
        and dto.data.subaccount == sub.name
        and dto.data.amount == 100000
        and dto.data.account == rc_ro.chain.address
        and dto.signature == ""
        and dto.data.lz_destination_address == ensure_bytes32_hex(destination_address)
        and dto.data.lz_destination_eid.value == destination_endpoint
    )


@pytest.mark.skip(reason="This test actually submits a withdrawal request")
def test_prepare_sign_submit_withdraw_token(rc, network):
    subaccounts = rc.list_subaccounts(sender=rc.chain.address)
    sub = subaccounts[0]
    tokens = rc.list_tokens()
    token = next((t for t in tokens if t.name == "USD"))
    destination_address = rc.chain.address
    dto = rc.prepare_withdraw_token(
        subaccount=sub.name,
        token=token.address,
        amount=5,
        account=rc.chain.address,
        destination_address=destination_address,
        destination_endpoint=DEFAULT_DESTINATION_ENDPOINT,
    )
    signed = rc.sign_withdraw_token(dto)
    result = rc.withdraw_token(signed, token_id=token.id)
    assert (
        isinstance(result, rc._models.WithdrawDto)
        and result.token == token.address
        and result.subaccount == sub.name
    )


@pytest.mark.skip(reason="This test actually submits a withdrawal request")
def test_prepare_sign_submit_withdraw_token_one_step(rc, network):
    subaccounts = rc.list_subaccounts(sender=rc.chain.address)
    sub = subaccounts[0]
    tokens = rc.list_tokens()
    token = next((t for t in tokens if t.name == "USD"))
    destination_address = rc.chain.address
    dto = rc.prepare_withdraw_token(
        subaccount=sub.name,
        token=token.address,
        amount=50,
        account=rc.chain.address,
        include_signature=True,
        destination_address=destination_address,
        destination_endpoint=DEFAULT_DESTINATION_ENDPOINT,
    )
    result = rc.withdraw_token(dto, token_id=token.id)
    assert (
        isinstance(result, rc._models.WithdrawDto)
        and result.token == token.address
        and result.subaccount == sub.name
    )
