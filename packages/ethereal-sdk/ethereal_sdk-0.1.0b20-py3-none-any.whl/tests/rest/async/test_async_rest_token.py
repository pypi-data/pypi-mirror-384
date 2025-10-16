"""Pure async tests for token operations."""

import pytest
from ethereal.rest.util import ensure_bytes32_hex

DEFAULT_DESTINATION_ENDPOINT = 0


@pytest.mark.asyncio
async def test_prepare_withdraw_token(async_rc_ro, network):
    subaccounts = await async_rc_ro.list_subaccounts(sender=async_rc_ro.chain.address)
    sub = subaccounts[0]
    tokens = await async_rc_ro.list_tokens()
    if not tokens:
        pytest.skip("No tokens available for testing")
    token = tokens[0]
    destination_endpoint = DEFAULT_DESTINATION_ENDPOINT
    destination_address = async_rc_ro.chain.address
    dto = await async_rc_ro.prepare_withdraw_token(
        subaccount=sub.name,
        token=token.address,
        amount=100000,
        account=async_rc_ro.chain.address,
        destination_address=destination_address,
        destination_endpoint=destination_endpoint,
    )
    assert (
        isinstance(dto, async_rc_ro._models.InitiateWithdrawDto)
        and dto.data.token == token.address
        and dto.data.subaccount == sub.name
        and dto.data.amount == 100000
        and dto.data.account == async_rc_ro.chain.address
        and dto.signature == ""
        and dto.data.lz_destination_address == ensure_bytes32_hex(destination_address)
        and dto.data.lz_destination_eid.value == destination_endpoint
    )


@pytest.mark.asyncio
async def test_prepare_and_sign_withdraw_token(async_rc, network):
    subaccounts = await async_rc.list_subaccounts(sender=async_rc.chain.address)
    sub = subaccounts[0]
    token = (await async_rc.list_tokens())[0]
    destination_address = async_rc.chain.address
    dto = await async_rc.prepare_withdraw_token(
        subaccount=sub.name,
        token=token.address,
        amount=100000,
        account=async_rc.chain.address,
        destination_address=destination_address,
        destination_endpoint=DEFAULT_DESTINATION_ENDPOINT,
    )
    signed = await async_rc.sign_withdraw_token(dto)
    assert (
        isinstance(signed, async_rc._models.InitiateWithdrawDto)
        and signed.signature != ""
    )


@pytest.mark.asyncio
async def test_prepare_with_automatic_signing(async_rc, network):
    subaccounts = await async_rc.list_subaccounts(sender=async_rc.chain.address)
    sub = subaccounts[0]
    token = (await async_rc.list_tokens())[0]
    destination_address = async_rc.chain.address
    dto = await async_rc.prepare_withdraw_token(
        subaccount=sub.name,
        token=token.address,
        amount=100000,
        account=async_rc.chain.address,
        include_signature=True,
        destination_address=destination_address,
        destination_endpoint=DEFAULT_DESTINATION_ENDPOINT,
    )
    assert isinstance(dto, async_rc._models.InitiateWithdrawDto) and dto.signature != ""


@pytest.mark.asyncio
async def test_prepare_withdraw_token_with_custom_nonce(async_rc_ro, network):
    subaccounts = await async_rc_ro.list_subaccounts(sender=async_rc_ro.chain.address)
    sub = subaccounts[0]
    tokens = await async_rc_ro.list_tokens()
    if not tokens:
        pytest.skip("No tokens available for testing")
    token = tokens[0]
    nonce = "123456789"
    destination_address = async_rc_ro.chain.address
    dto = await async_rc_ro.prepare_withdraw_token(
        subaccount=sub.name,
        token=token.address,
        amount=100000,
        account=async_rc_ro.chain.address,
        destination_address=destination_address,
        destination_endpoint=DEFAULT_DESTINATION_ENDPOINT,
        nonce=nonce,
    )
    assert (
        isinstance(dto, async_rc_ro._models.InitiateWithdrawDto)
        and dto.data.nonce == nonce
    )


@pytest.mark.asyncio
async def test_prepare_withdraw_token_with_custom_signed_at(async_rc_ro, network):
    subaccounts = await async_rc_ro.list_subaccounts(sender=async_rc_ro.chain.address)
    sub = subaccounts[0]
    token = (await async_rc_ro.list_tokens())[0]
    ts = 1620000000
    destination_address = async_rc_ro.chain.address
    dto = await async_rc_ro.prepare_withdraw_token(
        subaccount=sub.name,
        token=token.address,
        amount=100000,
        account=async_rc_ro.chain.address,
        destination_address=destination_address,
        destination_endpoint=DEFAULT_DESTINATION_ENDPOINT,
        signed_at=ts,
    )
    assert (
        isinstance(dto, async_rc_ro._models.InitiateWithdrawDto)
        and dto.data.signed_at == ts
    )


@pytest.mark.asyncio
async def test_prepare_withdraw_token_with_custom_destination(async_rc_ro, network):
    subaccounts = await async_rc_ro.list_subaccounts(sender=async_rc_ro.chain.address)
    sub = subaccounts[0]
    tokens = await async_rc_ro.list_tokens()
    if not tokens:
        pytest.skip("No tokens available for testing")
    token = tokens[0]
    destination_address = async_rc_ro.chain.address
    destination_endpoint = 10422
    dto = await async_rc_ro.prepare_withdraw_token(
        subaccount=sub.name,
        token=token.address,
        amount=100000,
        account=async_rc_ro.chain.address,
        destination_address=destination_address,
        destination_endpoint=destination_endpoint,
    )
    assert (
        isinstance(dto, async_rc_ro._models.InitiateWithdrawDto)
        and dto.data.token == token.address
        and dto.data.subaccount == sub.name
        and dto.data.amount == 100000
        and dto.data.account == async_rc_ro.chain.address
        and dto.signature == ""
        and dto.data.lz_destination_address == ensure_bytes32_hex(destination_address)
        and dto.data.lz_destination_eid.value == destination_endpoint
    )


@pytest.mark.skip(reason="This test actually submits a withdrawal request")
@pytest.mark.asyncio
async def test_prepare_sign_submit_withdraw_token(async_rc, network):
    subaccounts = await async_rc.list_subaccounts(sender=async_rc.chain.address)
    sub = subaccounts[0]
    tokens = await async_rc.list_tokens()
    token = next((t for t in tokens if t.name == "USD"))
    destination_address = async_rc.chain.address
    dto = await async_rc.prepare_withdraw_token(
        subaccount=sub.name,
        token=token.address,
        amount=5,
        account=async_rc.chain.address,
        destination_address=destination_address,
        destination_endpoint=DEFAULT_DESTINATION_ENDPOINT,
    )
    signed = await async_rc.sign_withdraw_token(dto)
    result = await async_rc.withdraw_token(signed, token_id=token.id)
    assert (
        isinstance(result, async_rc._models.WithdrawDto)
        and result.token == token.address
        and result.subaccount == sub.name
    )


@pytest.mark.skip(reason="This test actually submits a withdrawal request")
@pytest.mark.asyncio
async def test_prepare_sign_submit_withdraw_token_one_step(async_rc, network):
    subaccounts = await async_rc.list_subaccounts(sender=async_rc.chain.address)
    sub = subaccounts[0]
    tokens = await async_rc.list_tokens()
    token = next((t for t in tokens if t.name == "USD"))
    destination_address = async_rc.chain.address
    dto = await async_rc.prepare_withdraw_token(
        subaccount=sub.name,
        token=token.address,
        amount=50,
        account=async_rc.chain.address,
        include_signature=True,
        destination_address=destination_address,
        destination_endpoint=DEFAULT_DESTINATION_ENDPOINT,
    )
    result = await async_rc.withdraw_token(dto, token_id=token.id)
    assert (
        isinstance(result, async_rc._models.WithdrawDto)
        and result.token == token.address
        and result.subaccount == sub.name
    )
