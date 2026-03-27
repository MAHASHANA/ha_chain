"""Stellar testnet integration — real blockchain transactions.

Creates funded testnet accounts, records matches on-chain, provides
explorer links for verification.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import requests as _requests
from stellar_sdk import (
    Keypair,
    Network,
    Server,
    TransactionBuilder,
    Asset,
)

logger = logging.getLogger(__name__)

HORIZON_URL = "https://horizon-testnet.stellar.org"
FRIENDBOT_URL = "https://friendbot.stellar.org"
EXPLORER_URL = "https://stellar.expert/explorer/testnet"
NETWORK_PASSPHRASE = Network.TESTNET_NETWORK_PASSPHRASE

# Ha_Chain protocol account (holds fees, signs transactions)
# Generated once, hardcoded for testnet
_PROTOCOL_KP = Keypair.random()
_protocol_funded = False


@dataclass
class StellarWallet:
    public_key: str
    secret_key: str
    explorer_url: str
    funded: bool


@dataclass
class StellarTx:
    tx_hash: str
    explorer_url: str
    source: str
    memo: str
    success: bool


def _get_server() -> Server:
    return Server(horizon_url=HORIZON_URL)


async def fund_account(public_key: str) -> bool:
    """Fund a testnet account via Friendbot (gives 10,000 XLM)."""
    try:
        r = _requests.get(f"{FRIENDBOT_URL}?addr={public_key}", timeout=15)
        return r.status_code == 200
    except Exception as e:
        logger.warning(f"Friendbot failed for {public_key}: {e}")
        return False


async def create_wallet() -> StellarWallet:
    """Create a new Stellar testnet keypair and fund it."""
    kp = Keypair.random()
    funded = await fund_account(kp.public_key)
    return StellarWallet(
        public_key=kp.public_key,
        secret_key=kp.secret,
        explorer_url=f"{EXPLORER_URL}/account/{kp.public_key}",
        funded=funded,
    )


async def ensure_protocol_account() -> str:
    """Ensure the protocol account is funded. Returns public key."""
    global _protocol_funded
    if not _protocol_funded:
        _protocol_funded = await fund_account(_PROTOCOL_KP.public_key)
        logger.info(f"Protocol account: {_PROTOCOL_KP.public_key} funded={_protocol_funded}")
    return _PROTOCOL_KP.public_key


async def record_match_on_chain(
    match_id: str,
    order1_source_currency: str,
    order1_target_currency: str,
    amount_usd: float,
    match_type: str,
    fee: float,
) -> Optional[StellarTx]:
    """Record a match as a Stellar testnet transaction.

    Sends a tiny XLM payment from the protocol account to itself
    with a memo containing the match details. This creates an
    immutable on-chain record that anyone can verify.
    """
    try:
        await ensure_protocol_account()
        server = _get_server()

        # Load protocol account
        account = server.load_account(_PROTOCOL_KP.public_key)

        # Build memo: "HA:MATCH:USD>INR:500.00:direct"
        memo_text = f"HA:{match_type[:3].upper()}:{order1_source_currency}>{order1_target_currency}:{amount_usd}"
        # Stellar memo_text max 28 bytes
        if len(memo_text.encode()) > 28:
            memo_text = memo_text[:28]

        # Build transaction: send 0.01 XLM to self with match memo
        tx = (
            TransactionBuilder(
                source_account=account,
                network_passphrase=NETWORK_PASSPHRASE,
                base_fee=100,
            )
            .append_payment_op(
                destination=_PROTOCOL_KP.public_key,
                asset=Asset.native(),
                amount="0.01",
            )
            .add_text_memo(memo_text)
            .set_timeout(30)
            .build()
        )

        tx.sign(_PROTOCOL_KP)
        response = server.submit_transaction(tx)

        tx_hash = response["hash"]
        logger.info(f"Match {match_id} recorded on Stellar: {tx_hash}")

        return StellarTx(
            tx_hash=tx_hash,
            explorer_url=f"{EXPLORER_URL}/tx/{tx_hash}",
            source=_PROTOCOL_KP.public_key,
            memo=memo_text,
            success=True,
        )

    except Exception as e:
        logger.error(f"Failed to record match {match_id} on Stellar: {e}")
        return StellarTx(
            tx_hash="",
            explorer_url="",
            source=_PROTOCOL_KP.public_key,
            memo="",
            success=False,
        )


async def record_escrow_lock(
    transfer_id: str,
    amount_usd: float,
    sender_key: str,
) -> Optional[StellarTx]:
    """Record an escrow lock event on-chain."""
    try:
        await ensure_protocol_account()
        server = _get_server()
        account = server.load_account(_PROTOCOL_KP.public_key)

        memo_text = f"HA:ESC:LOCK:{amount_usd}"
        if len(memo_text.encode()) > 28:
            memo_text = memo_text[:28]

        tx = (
            TransactionBuilder(
                source_account=account,
                network_passphrase=NETWORK_PASSPHRASE,
                base_fee=100,
            )
            .append_payment_op(
                destination=_PROTOCOL_KP.public_key,
                asset=Asset.native(),
                amount="0.01",
            )
            .add_text_memo(memo_text)
            .set_timeout(30)
            .build()
        )

        tx.sign(_PROTOCOL_KP)
        response = server.submit_transaction(tx)

        return StellarTx(
            tx_hash=response["hash"],
            explorer_url=f"{EXPLORER_URL}/tx/{response['hash']}",
            source=_PROTOCOL_KP.public_key,
            memo=memo_text,
            success=True,
        )
    except Exception as e:
        logger.error(f"Failed to record escrow lock for {transfer_id}: {e}")
        return None


async def record_settlement(
    match_id: str,
    currency: str,
    amount: float,
    payment_method: str,
) -> Optional[StellarTx]:
    """Record a local settlement on-chain."""
    try:
        await ensure_protocol_account()
        server = _get_server()
        account = server.load_account(_PROTOCOL_KP.public_key)

        memo_text = f"HA:PAY:{currency}:{amount}:{payment_method}"
        if len(memo_text.encode()) > 28:
            memo_text = memo_text[:28]

        tx = (
            TransactionBuilder(
                source_account=account,
                network_passphrase=NETWORK_PASSPHRASE,
                base_fee=100,
            )
            .append_payment_op(
                destination=_PROTOCOL_KP.public_key,
                asset=Asset.native(),
                amount="0.01",
            )
            .add_text_memo(memo_text)
            .set_timeout(30)
            .build()
        )

        tx.sign(_PROTOCOL_KP)
        response = server.submit_transaction(tx)

        return StellarTx(
            tx_hash=response["hash"],
            explorer_url=f"{EXPLORER_URL}/tx/{response['hash']}",
            source=_PROTOCOL_KP.public_key,
            memo=memo_text,
            success=True,
        )
    except Exception as e:
        logger.error(f"Failed to record settlement for {match_id}: {e}")
        return None


async def get_protocol_transactions(limit: int = 20) -> list[dict]:
    """Fetch recent transactions from the protocol account."""
    try:
        await ensure_protocol_account()
        server = _get_server()
        txs = (
            server.transactions()
            .for_account(_PROTOCOL_KP.public_key)
            .order(desc=True)
            .limit(limit)
            .call()
        )
        results = []
        for record in txs["_embedded"]["records"]:
            results.append({
                "tx_hash": record["hash"],
                "memo": record.get("memo", ""),
                "created_at": record["created_at"],
                "explorer_url": f"{EXPLORER_URL}/tx/{record['hash']}",
                "fee_charged": record.get("fee_charged", "0"),
                "success": record["successful"],
            })
        return results
    except Exception as e:
        logger.error(f"Failed to fetch protocol transactions: {e}")
        return []
