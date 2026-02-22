require("dotenv").config({ path: require("path").resolve(__dirname, "../../.env") });
require("dotenv").config();

require("@nomicfoundation/hardhat-ethers");
require("@nomicfoundation/hardhat-chai-matchers");
require("hardhat-gas-reporter");
require("solidity-coverage");
require("@nomicfoundation/hardhat-verify");
require("hardhat-deploy");
require("hardhat-deploy-ethers");

const pk = process.env.PRIVATE_KEY;
const deployerPrivateKey =
  process.env.__RUNTIME_DEPLOYER_PRIVATE_KEY ??
  (pk ? (pk.startsWith("0x") ? pk : `0x${pk}`) : "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80");

const etherscanApiKey = process.env.ETHERSCAN_V2_API_KEY || "DNXJA8RX2Q3VZ4URQIWP7Z68CJXQZSC6AW";
const providerApiKey = process.env.ALCHEMY_API_KEY || "cR4WnXePioePZ5fFrnSiR";

/** @type {import('hardhat/config').HardhatUserConfig} */
const config = {
  solidity: {
    compilers: [
      {
        version: "0.8.20",
        settings: {
          optimizer: { enabled: true, runs: 200 },
        },
      },
    ],
  },
  defaultNetwork: "localhost",
  namedAccounts: {
    deployer: { default: 0 },
  },
  networks: {
    hardhat: {
      forking: {
        url: `https://eth-mainnet.alchemyapi.io/v2/${providerApiKey}`,
        enabled: process.env.MAINNET_FORKING_ENABLED === "true",
      },
    },
    mainnet: { url: "https://mainnet.rpc.buidlguidl.com", accounts: [deployerPrivateKey] },
    sepolia: { url: `https://eth-sepolia.g.alchemy.com/v2/${providerApiKey}`, accounts: [deployerPrivateKey] },
    arbitrum: { url: `https://arb-mainnet.g.alchemy.com/v2/${providerApiKey}`, accounts: [deployerPrivateKey] },
    arbitrumSepolia: { url: `https://arb-sepolia.g.alchemy.com/v2/${providerApiKey}`, accounts: [deployerPrivateKey] },
    optimism: { url: `https://opt-mainnet.g.alchemy.com/v2/${providerApiKey}`, accounts: [deployerPrivateKey] },
    optimismSepolia: { url: `https://opt-sepolia.g.alchemy.com/v2/${providerApiKey}`, accounts: [deployerPrivateKey] },
    polygon: { url: `https://polygon-mainnet.g.alchemy.com/v2/${providerApiKey}`, accounts: [deployerPrivateKey] },
    polygonAmoy: { url: `https://polygon-amoy.g.alchemy.com/v2/${providerApiKey}`, accounts: [deployerPrivateKey] },
    polygonZkEvm: { url: `https://polygonzkevm-mainnet.g.alchemy.com/v2/${providerApiKey}`, accounts: [deployerPrivateKey] },
    polygonZkEvmCardona: { url: `https://polygonzkevm-cardona.g.alchemy.com/v2/${providerApiKey}`, accounts: [deployerPrivateKey] },
    gnosis: { url: "https://rpc.gnosischain.com", accounts: [deployerPrivateKey] },
    chiado: { url: "https://rpc.chiadochain.net", accounts: [deployerPrivateKey] },
    base: { url: "https://mainnet.base.org", accounts: [deployerPrivateKey] },
    baseSepolia: { url: "https://sepolia.base.org", accounts: [deployerPrivateKey] },
    scrollSepolia: { url: "https://sepolia-rpc.scroll.io", accounts: [deployerPrivateKey] },
    scroll: { url: "https://rpc.scroll.io", accounts: [deployerPrivateKey] },
    celo: { url: "https://forno.celo.org", accounts: [deployerPrivateKey] },
    celoSepolia: { url: "https://forno.celo-sepolia.celo-testnet.org/", accounts: [deployerPrivateKey] },
    // MONAD TESTNET — SentimentFi target chain
    monad_testnet: {
      url: process.env.MONAD_RPC_URL || "https://testnet-rpc.monad.xyz",
      accounts: [deployerPrivateKey],
      chainId: 10143,
      gasPrice: 100_000_000_000, // 100 gwei — REQUIRED for Monad
    },
  },
  etherscan: { apiKey: etherscanApiKey },
  verify: { etherscan: { apiKey: etherscanApiKey } },
  sourcify: { enabled: false },
};

module.exports = config;
