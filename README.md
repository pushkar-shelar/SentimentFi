# 🟣 SentimentFi

**AI-Powered Onchain Sentiment Oracle on Monad**

SentimentFi pulls live crypto sentiment from Reddit and news feeds, runs it through a local HuggingFace NLP model, and pushes the resulting score onchain to a smart contract deployed on Monad Testnet — all in a single click.

---

## Demo

![SentimentFi UI](https://via.placeholder.com/900x480?text=SentimentFi+Screenshot)

**Live App:** [your-app.streamlit.app](https://your-app.streamlit.app)  
**Contract:** [`0xC678C0b6dCB0999de64786F620817b767f70b685`](https://testnet.monadexplorer.com/address/0xC678C0b6dCB0999de64786F620817b767f70b685) on Monad Testnet

---

## How It Works

```
Reddit + News RSS  →  HuggingFace NLP  →  Score [-1.0, +1.0]  →  SentimentOracle (Monad)
```

1. **Fetch** — Live posts from Reddit (`r/monad`, `r/Bitcoin`, `r/ethereum`) and news headlines from CoinDesk, Decrypt, and CoinGape are pulled in real time (no API keys required).
2. **Analyze** — Texts are passed through `distilbert-base-uncased-finetuned-sst-2-english` locally. Each result is labeled POSITIVE/NEGATIVE with a confidence score, then aggregated into a single float in `[-1.0, +1.0]`.
3. **Push Onchain** — The normalized score is written to the `SentimentOracle` Solidity contract on Monad Testnet via `web3.py`. Gas price is enforced at ≥ 100 gwei per Monad requirements.
4. **Verify** — Any confirmed transaction links directly to the Monad Testnet explorer.

---

## Features

- **No API keys** — Reddit uses the public JSON API; news comes from open RSS feeds
- **Custom search** — Type any query (e.g., "monad testnet") to search Reddit + news on demand
- **Live feed status** — Color-coded indicators show Reddit and news source health
- **Onchain write** — One button pushes the AI score to a verified smart contract
- **Onchain read** — Read back any previously stored score for any token
- **Monad UI Kit theme** — Dark purple design using official Monad brand colors

---

## Stack

| Layer | Technology |
|---|---|
| Smart Contract | Solidity `^0.8.20` — Hardhat on Monad Testnet |
| AI / NLP | HuggingFace Transformers (`distilbert-base-uncased-finetuned-sst-2-english`) |
| Blockchain Client | `web3.py` v7 |
| Data Sources | Reddit public API, CoinDesk / Decrypt / CoinGape RSS |
| Frontend | Streamlit with custom CSS (Monad UI Kit) |

---

## Project Structure

```
SentimentFi/
├── app.py                          # Streamlit frontend
├── ai_engine/
│   ├── sentiment_engine.py         # HuggingFace NLP pipeline
│   ├── data_fetcher.py             # Reddit + news data ingestion
│   └── blockchain.py               # web3.py contract interface
├── packages/
│   └── hardhat/
│       ├── contracts/
│       │   └── SentimentOracle.sol # Smart contract
│       └── hardhat.config.js       # Monad Testnet config
└── .env                            # RPC URL, private key, contract address
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+ (for Hardhat)

### 1. Clone and install

```bash
git clone https://github.com/your-username/SentimentFi.git
cd SentimentFi

python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

pip install streamlit web3 python-dotenv transformers torch pandas
```

### 2. Configure environment

Create a `.env` file in the project root:

```env
MONAD_RPC_URL=https://testnet-rpc.monad.xyz
PRIVATE_KEY=your_wallet_private_key
CONTRACT_ADDRESS=0xC678C0b6dCB0999de64786F620817b767f70b685
```

> **Note:** The contract is already deployed. You only need a Monad Testnet wallet with a small amount of MON for gas.

### 3. Run the app

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501).

---

## Smart Contract

**SentimentOracle.sol** stores a sentiment score (as an integer, scaled ×100) per token symbol.

```solidity
function updateSentiment(string calldata token, int256 score) external onlyOwner
function getSentiment(string calldata token) external view returns (int256)
```

Scores are stored as integers (e.g., `0.75` → `75`, `-0.42` → `-42`) and divided by 100 on read.

**Network:** Monad Testnet  
**Chain ID:** 10143  
**RPC:** `https://testnet-rpc.monad.xyz`  
**Explorer:** [testnet.monadexplorer.com](https://testnet.monadexplorer.com)

To recompile and redeploy:

```bash
cd packages/hardhat
npm install
npx hardhat compile
npx hardhat run scripts/deploy.js --network monad_testnet
```

---

## Deploying the Frontend

### Streamlit Cloud (recommended)

1. Push the repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**
3. Select your repo and set the main file as `app.py`
4. Under **Secrets**, add:
   ```toml
   MONAD_RPC_URL = "https://testnet-rpc.monad.xyz"
   PRIVATE_KEY = "your_private_key"
   CONTRACT_ADDRESS = "0xC678C0b6dCB0999de64786F620817b767f70b685"
   ```
5. Deploy

---

## License

MIT
