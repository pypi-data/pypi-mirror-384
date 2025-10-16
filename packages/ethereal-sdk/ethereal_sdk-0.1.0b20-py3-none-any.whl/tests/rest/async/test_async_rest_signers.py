"""Pure async tests for linking and revoking signers."""

import pytest
from eth_account import Account


@pytest.mark.skip(
    reason="Linked signers are rate limited; running repeatedly may fail."
)
@pytest.mark.asyncio
async def test_link_and_revoke_signer(async_rc, async_subaccount, network):
    sname = async_subaccount.name
    sid_any = async_subaccount.id
    account = Account.create()
    link = await async_rc.prepare_linked_signer(
        sender=async_rc.chain.address,
        signer=account.address,
        subaccount=sname,
        subaccount_id=sid_any,
    )
    link = await async_rc.sign_linked_signer(
        link, private_key=async_rc.chain.private_key, signer_private_key=account.key
    )
    res = await async_rc.link_linked_signer(dto=link)
    assert isinstance(res, async_rc._models.SignerDto) and res.signer == account.address
    revoke = await async_rc.prepare_revoke_linked_signer(
        sender=async_rc.chain.address,
        signer=account.address,
        subaccount=sname,
        subaccount_id=sid_any,
    )
    revoke = await async_rc.sign_revoke_linked_signer(revoke)
    rev_res = await async_rc.revoke_linked_signer(dto=revoke)
    assert isinstance(rev_res, async_rc._models.RevokeLinkedSignerDto)


@pytest.mark.asyncio
async def test_prepare_linked_signer(async_rc_ro, async_subaccount, network):
    sname = async_subaccount.name
    sid_any = async_subaccount.id
    account = Account.create()
    link = await async_rc_ro.prepare_linked_signer(
        sender=async_rc_ro.chain.address,
        signer=account.address,
        subaccount=sname,
        subaccount_id=sid_any,
    )
    assert isinstance(link, async_rc_ro._models.LinkSignerDto)
    typed = async_rc_ro._models.LinkSignerDtoData.model_validate(
        link.data.model_dump(by_alias=True)
    )
    assert link.signature == "" and link.signer_signature == ""
    assert (
        typed.sender == async_rc_ro.chain.address
        and typed.signer == account.address
        and typed.subaccount_id == sid_any
    )


@pytest.mark.asyncio
async def test_prepare_and_sign_linked_signer_sender(
    async_rc, async_subaccount, network
):
    sname = async_subaccount.name
    sid_any = async_subaccount.id
    account = Account.create()
    link = await async_rc.prepare_linked_signer(
        sender=async_rc.chain.address,
        signer=account.address,
        subaccount=sname,
        subaccount_id=sid_any,
    )
    link = await async_rc.sign_linked_signer(
        link, private_key=async_rc.chain.private_key
    )
    assert (
        isinstance(link, async_rc._models.LinkSignerDto)
        and link.signature != ""
        and link.signer_signature == ""
    )


@pytest.mark.asyncio
async def test_prepare_and_sign_linked_signer_signer(
    async_rc_ro, async_subaccount, network
):
    sname = async_subaccount.name
    sid_any = async_subaccount.id
    account = Account.create()
    link = await async_rc_ro.prepare_linked_signer(
        sender=async_rc_ro.chain.address,
        signer=account.address,
        subaccount=sname,
        subaccount_id=sid_any,
    )
    link = await async_rc_ro.sign_linked_signer(link, signer_private_key=account.key)
    assert (
        isinstance(link, async_rc_ro._models.LinkSignerDto)
        and link.signature == ""
        and link.signer_signature != ""
    )


@pytest.mark.asyncio
async def test_prepare_and_sign_linked_signer_both(async_rc, async_subaccount, network):
    sname = async_subaccount.name
    sid_any = async_subaccount.id
    account = Account.create()
    link = await async_rc.prepare_linked_signer(
        sender=async_rc.chain.address,
        signer=account.address,
        subaccount=sname,
        subaccount_id=sid_any,
    )
    link = await async_rc.sign_linked_signer(
        link, private_key=async_rc.chain.private_key
    )
    link = await async_rc.sign_linked_signer(link, signer_private_key=account.key)
    assert (
        isinstance(link, async_rc._models.LinkSignerDto)
        and link.signature != ""
        and link.signer_signature != ""
        and link.signature != link.signer_signature
    )


@pytest.mark.asyncio
async def test_prepare_revoke_linked_signer(async_rc_ro, async_subaccount, network):
    sname = async_subaccount.name
    sid_any = async_subaccount.id
    account = Account.create()
    revoke = await async_rc_ro.prepare_revoke_linked_signer(
        sender=async_rc_ro.chain.address,
        signer=account.address,
        subaccount=sname,
        subaccount_id=sid_any,
    )
    assert isinstance(revoke, async_rc_ro._models.RevokeLinkedSignerDto)
    assert (
        revoke.data.sender == async_rc_ro.chain.address
        and revoke.data.signer == account.address
        and revoke.data.subaccount_id == sid_any
        and revoke.signature == ""
    )


@pytest.mark.asyncio
async def test_prepare_and_sign_revoke_linked_signer(
    async_rc, async_subaccount, network
):
    sname = async_subaccount.name
    sid_any = async_subaccount.id
    account = Account.create()
    revoke = await async_rc.prepare_revoke_linked_signer(
        sender=async_rc.chain.address,
        signer=account.address,
        subaccount=sname,
        subaccount_id=sid_any,
    )
    revoke = await async_rc.sign_revoke_linked_signer(revoke)
    assert (
        isinstance(revoke, async_rc._models.RevokeLinkedSignerDto)
        and revoke.signature != ""
    )
