import time
from decimal import Decimal
from typing import List, Optional
from enum import Enum

from ethereal.constants import API_PREFIX
from ethereal.models.rest import (
    TokenDto,
    WithdrawDto,
    TransferDto,
    InitiateWithdrawDto,
)
from ethereal.rest.util import ensure_bytes32_hex, generate_nonce


class LayerZeroEndpointId(Enum):
    NONE = 0
    ETHEREAL_TESTNET = 10422
    ARBITRUM_SEPOLIA = 40231


async def list_tokens(
    self,
    **kwargs,
) -> List[TokenDto]:
    """Lists all supported tokens.

    Other Parameters:
        order (str, optional): Sort order, 'asc' or 'desc'. Optional.
        limit (float, optional): Maximum number of results to return. Optional.
        cursor (str, optional): Pagination cursor for fetching the next page. Optional.
        order_by (str, optional): Field to order by (e.g., 'createdAt'). Optional.
        **kwargs: Additional request parameters accepted by the API. Optional.

    Returns:
        List[TokenDto]: Token metadata.
    """
    res = await self.get_validated(
        url_path=f"{API_PREFIX}/token",
        request_model=self._models.V1TokenGetParametersQuery,
        response_model=self._models.PageOfTokensDtos,
        **kwargs,
    )
    data = [
        self._models.TokenDto(**model.model_dump(by_alias=True)) for model in res.data
    ]
    return data


async def get_token(
    self,
    id: str,
    **kwargs,
) -> TokenDto:
    """Gets a specific token by ID.

    Args:
        id (str): UUID for the token. Required.

    Other Parameters:
        **kwargs: Additional request parameters accepted by the API. Optional.

    Returns:
        TokenDto: Token metadata.
    """
    endpoint = f"{API_PREFIX}/token/{id}"
    res = await self.get(endpoint, **kwargs)
    return self._models.TokenDto(**res)


async def list_token_withdraws(
    self,
    **kwargs,
) -> List[WithdrawDto]:
    """Lists token withdrawals for a subaccount.

    Args:
        subaccount_id (str): UUID of the subaccount. Required.

    Other Parameters:
        order (str, optional): Sort order, 'asc' or 'desc'. Optional.
        limit (float, optional): Maximum number of results to return. Optional.
        cursor (str, optional): Pagination cursor for fetching the next page. Optional.
        order_by (str, optional): Field to order by (e.g., 'createdAt'). Optional.
        **kwargs: Additional request parameters accepted by the API. Optional.

    Returns:
        List[WithdrawDto]: Withdrawal records for the subaccount.
    """
    res = await self.get_validated(
        url_path=f"{API_PREFIX}/token/withdraw",
        request_model=self._models.V1TokenWithdrawGetParametersQuery,
        response_model=self._models.PageOfWithdrawDtos,
        **kwargs,
    )
    data = [
        self._models.WithdrawDto(**model.model_dump(by_alias=True))
        for model in res.data
    ]
    return data


async def list_token_transfers(
    self,
    **kwargs,
) -> List[TransferDto]:
    """Lists token transfers for a subaccount.

    Args:
        subaccount_id (str): UUID of the subaccount. Required.

    Other Parameters:
        order (str, optional): Sort order, 'asc' or 'desc'. Optional.
        limit (float, optional): Maximum number of results to return. Optional.
        cursor (str, optional): Pagination cursor for fetching the next page. Optional.
        order_by (str, optional): Field to order by (e.g., 'createdAt'). Optional.
        **kwargs: Additional request parameters accepted by the API. Optional.

    Returns:
        List[TransferDto]: Transfer records for the subaccount.
    """
    res = await self.get_validated(
        url_path=f"{API_PREFIX}/token/transfer",
        request_model=self._models.V1TokenTransferGetParametersQuery,
        response_model=self._models.PageOfTransfersDtos,
        **kwargs,
    )
    data = [
        self._models.TransferDto(**model.model_dump(by_alias=True))
        for model in res.data
    ]
    return data


async def prepare_withdraw_token(
    self,
    subaccount: str,
    token: str,
    amount: int,
    account: str,
    destination_address: str,
    destination_endpoint: int,
    include_signature: bool = False,
    nonce: Optional[str] = None,
    signed_at: Optional[int] = None,
) -> InitiateWithdrawDto:
    """Prepares a token withdrawal request, optionally including a signature.

    Args:
        subaccount (str): Hex-encoded subaccount name. Required.
        token (str): Token contract address or identifier. Required.
        amount (int): Amount to withdraw (token base units). Required.
        account (str): Recipient address. Required.
        destination_address (str): LayerZero destination address (hex string or bytes; automatically left-padded to bytes32).
        destination_endpoint (int): LayerZero destination endpoint ID.
        include_signature (bool): If True, sign the payload immediately. Optional.
        nonce (str, optional): Custom nonce for signing. Defaults to a generated nonce.
        signed_at (int, optional): Seconds since epoch for the signature timestamp.

    Returns:
        InitiateWithdrawDto: Prepared (and optionally signed) withdrawal payload.
    """
    nonce = nonce or generate_nonce()
    signed_at = signed_at or int(time.time())
    lz_destination_id = self._models.LzDestinationEid(destination_endpoint)

    data = {
        "account": account,
        "subaccount": subaccount,
        "token": token,
        "amount": amount,
        "nonce": nonce,
        "signedAt": signed_at,
        "lzDestinationAddress": ensure_bytes32_hex(destination_address),
        "lzDestinationEid": lz_destination_id,
    }
    data_model = self._models.InitiateWithdrawDtoData.model_validate(data)
    dto = self._models.InitiateWithdrawDto.model_validate(
        {"data": data_model.model_dump(mode="json", by_alias=True), "signature": ""}
    )
    if include_signature:
        dto = await self.sign_withdraw_token(dto)
    return dto


async def sign_withdraw_token(
    self,
    withdraw_dto: InitiateWithdrawDto,
    private_key: Optional[str] = None,
) -> InitiateWithdrawDto:
    """Signs the token withdrawal payload using EIP-712.

    Args:
        withdraw_dto (InitiateWithdrawDto): Prepared withdrawal payload. Required.
        private_key (str, optional): Private key override. Defaults to the client's chain key.

    Returns:
        InitiateWithdrawDto: The same DTO with signature populated.

    Raises:
        ValueError: If no chain client or private key is available.
    """
    if not hasattr(self, "chain") or not self.chain:
        raise ValueError("No chain client available for signing")
    if not private_key and not self.chain.private_key:
        raise ValueError("No private key available for signing")
    elif not private_key:
        private_key = self.chain.private_key

    # Prepare the message for signing
    message = withdraw_dto.data.model_dump(by_alias=True, mode="json")
    message["amount"] = int(Decimal(str(message["amount"])) * Decimal(1e9))
    message["signedAt"] = int(message["signedAt"])

    destination_address = message["lzDestinationAddress"]
    destination_eid = int(message["lzDestinationEid"])

    message["destinationAddress"] = destination_address
    message["destinationEndpointId"] = destination_eid

    primary_type = "InitiateWithdraw"
    domain = self.rpc_config.domain.model_dump(mode="json", by_alias=True)
    types = self.chain.get_signature_types(self.rpc_config, primary_type)
    withdraw_dto.signature = self.chain.sign_message(
        private_key, domain, types, primary_type, message
    )
    return withdraw_dto


async def withdraw_token(
    self,
    dto: InitiateWithdrawDto,
    token_id: str,
    **kwargs,
) -> WithdrawDto:
    """Submits a prepared and signed token withdrawal request.

    Args:
        dto (InitiateWithdrawDto): Prepared and signed withdrawal payload. Required.
        token_id (str): Token ID for the withdraw route parameter. Required.

    Other Parameters:
        **kwargs: Additional request parameters accepted by the API. Optional.

    Returns:
        WithdrawDto: Withdrawal record created by the API.
    """
    endpoint = f"{API_PREFIX}/token/{token_id}/withdraw"
    res = await self.post(
        endpoint,
        data=dto.model_dump(mode="json", by_alias=True, exclude_none=True),
        **kwargs,
    )
    return self._models.WithdrawDto.model_validate(res)
