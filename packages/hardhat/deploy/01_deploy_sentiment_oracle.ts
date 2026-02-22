import { HardhatRuntimeEnvironment } from "hardhat/types";
import { DeployFunction } from "hardhat-deploy/types";

/**
 * Deploys the SentimentOracle contract.
 * No constructor arguments needed — minimal design.
 *
 * Deploy to Monad Testnet:
 *   yarn deploy --network monad_testnet
 *
 * IMPORTANT: Monad requires gasPrice >= 100 gwei (configured in hardhat.config.ts)
 */
const deploySentimentOracle: DeployFunction = async function (hre: HardhatRuntimeEnvironment) {
  const { deployer } = await hre.getNamedAccounts();
  const { deploy } = hre.deployments;

  await deploy("SentimentOracle", {
    from: deployer,
    args: [],
    log: true,
    autoMine: true,
  });

  console.log("✅ SentimentOracle deployed successfully!");
};

export default deploySentimentOracle;

deploySentimentOracle.tags = ["SentimentOracle"];
