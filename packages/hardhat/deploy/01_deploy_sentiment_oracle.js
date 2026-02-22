/**
 * Deploys the SentimentOracle contract to Monad Testnet.
 *
 * Deploy command:
 *   yarn deploy --network monad_testnet
 *
 * @param {import('hardhat-deploy/types').HardhatRuntimeEnvironment} hre
 */
async function deploySentimentOracle(hre) {
  const { deployer } = await hre.getNamedAccounts();
  const { deploy } = hre.deployments;

  await deploy("SentimentOracle", {
    from: deployer,
    args: [],
    log: true,
    autoMine: true,
  });

  console.log("✅ SentimentOracle deployed successfully!");
}

module.exports = deploySentimentOracle;
module.exports.tags = ["SentimentOracle"];
