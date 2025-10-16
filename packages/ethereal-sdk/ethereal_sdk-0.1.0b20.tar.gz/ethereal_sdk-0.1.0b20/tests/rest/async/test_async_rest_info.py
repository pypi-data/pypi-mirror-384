"""Pure async tests for REST info endpoints."""

import pytest
from typing import List
from pydantic import BaseModel


@pytest.mark.asyncio
async def test_rest_subaccounts(async_rc):
    subs = await async_rc.list_subaccounts(sender=async_rc.chain.address)
    assert isinstance(subs, List)
    assert all(isinstance(sa, BaseModel) for sa in subs)


@pytest.mark.asyncio
async def test_rest_subaccount(async_rc):
    subs = await async_rc.list_subaccounts(sender=async_rc.chain.address)
    sub = await async_rc.get_subaccount(subs[0].id)
    assert isinstance(sub, BaseModel)


@pytest.mark.asyncio
async def test_rest_rpc_config(async_rc):
    cfg = await async_rc.get_rpc_config()
    assert isinstance(cfg, BaseModel)


@pytest.mark.asyncio
async def test_rest_products(async_rc):
    products = await async_rc.list_products()
    assert isinstance(products, List)
    assert all(isinstance(p, BaseModel) for p in products)


@pytest.mark.asyncio
async def test_rest_tokens(async_rc):
    tokens = await async_rc.list_tokens()
    assert isinstance(tokens, List)
    assert all(isinstance(t, BaseModel) for t in tokens)


@pytest.mark.asyncio
async def test_rest_market_prices(async_rc):
    products = await async_rc.list_products()
    if products:
        prices = await async_rc.list_market_prices(product_ids=[products[0].id])
        assert isinstance(prices, List)
        assert all(isinstance(p, BaseModel) for p in prices)
