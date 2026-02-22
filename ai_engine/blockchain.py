"""
SentimentFi — Blockchain Module
=================================
Web3.py interface for interacting with the SentimentOracle contract on Monad Testnet.
Loads ABI from Hardhat compilation artifacts automatically.

⚠️ MONAD REQUIREMENT: All transactions use gasPrice >= 100 gwei.
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from web3 import Web3

# Explicitly load .env from the project root (one level above ai_engine/)
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

MONAD_RPC_URL = os.getenv("MONAD_RPC_URL", "https://testnet-rpc.monad.xyz")
PRIVATE_KEY = os.getenv("PRIVATE_KEY", "")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS", "")

# Minimum gas price for Monad Testnet (100 gwei)
MIN_GAS_PRICE = Web3.to_wei("100", "gwei")


def _load_abi() -> list:
    """Load the SentimentOracle ABI from Hardhat artifacts."""
    base_dir = Path(__file__).resolve().parent.parent
    artifact_path = (
        base_dir
        / "packages"
        / "hardhat"
        / "artifacts"
        / "contracts"
        / "SentimentOracle.sol"
        / "SentimentOracle.json"
    )

    if not artifact_path.exists():
        raise FileNotFoundError(
            f"Contract artifact not found at {artifact_path}. "
            "Please compile the contract first: cd packages/hardhat && npx hardhat compile"
        )

    with open(artifact_path, "r") as f:
        artifact = json.load(f)

    return artifact["abi"]


def _get_web3() -> Web3:
    """Return a Web3 instance connected to Monad Testnet."""
    w3 = Web3(Web3.HTTPProvider(MONAD_RPC_URL, request_kwargs={"timeout": 10}))
    try:
        # web3.py v7: use eth.block_number instead of deprecated is_connected()
        _ = w3.eth.block_number
    except Exception as e:
        raise ConnectionError(f"Cannot connect to Monad RPC at {MONAD_RPC_URL}: {e}")
    return w3


def _get_contract(w3: Web3):
    """Load the SentimentOracle contract instance."""
    abi = _load_abi()
    address = Web3.to_checksum_address(CONTRACT_ADDRESS)
    return w3.eth.contract(address=address, abi=abi)


def push_onchain(token: str, score: float) -> str:
    """Push a sentiment score onchain. Returns the transaction hash."""
    if not PRIVATE_KEY:
        raise ValueError("PRIVATE_KEY not set in .env")
    if not CONTRACT_ADDRESS:
        raise ValueError("CONTRACT_ADDRESS not set in .env")

    w3 = _get_web3()
    contract = _get_contract(w3)
    account = w3.eth.account.from_key(PRIVATE_KEY)

    score_int = int(score * 100)  # e.g. 0.75 → 75
    nonce = w3.eth.get_transaction_count(account.address)
    tx = contract.functions.updateSentiment(token, score_int).build_transaction(
        {
            "from": account.address,
            "nonce": nonce,
            "gasPrice": MIN_GAS_PRICE,  # 100 gwei — MONAD REQUIREMENT
        }
    )

    gas_estimate = w3.eth.estimate_gas(tx)
    tx["gas"] = gas_estimate
    signed_tx = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

    if receipt["status"] != 1:
        raise RuntimeError(f"Transaction failed! Hash: {tx_hash.hex()}")

    return tx_hash.hex()


def read_sentiment(token: str) -> float:
    """Read the stored sentiment score for a token from the contract."""
    if not CONTRACT_ADDRESS:
        raise ValueError("CONTRACT_ADDRESS not set in .env")

    w3 = _get_web3()
    contract = _get_contract(w3)

    score_int = contract.functions.getSentiment(token).call()
    return score_int / 100.0


def get_explorer_url(tx_hash: str) -> str:
    """Return the Monad testnet explorer URL for a transaction hash."""
    return f"https://testnet.monadexplorer.com/tx/0x{tx_hash.lstrip('0x')}"


def check_connection() -> dict:
    """Return Web3 connection status, chain ID, and latest block."""
    try:
        w3 = Web3(Web3.HTTPProvider(MONAD_RPC_URL, request_kwargs={"timeout": 8}))
        block = w3.eth.block_number
        chain = w3.eth.chain_id
        return {
            "connected": True,
            "chain_id": chain,
            "latest_block": block,
            "rpc_url": MONAD_RPC_URL,
        }
    except Exception as e:
        return {
            "connected": False,
            "error": str(e),
            "rpc_url": MONAD_RPC_URL,
        }
