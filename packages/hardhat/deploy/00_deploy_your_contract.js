/**
 * Deploys the YourContract contract.
 * @param {import('hardhat-deploy/types').HardhatRuntimeEnvironment} hre
 */
async function deployYourContract(hre) {
  const { deployer } = await hre.getNamedAccounts();
  const { deploy } = hre.deployments;

  await deploy("YourContract", {
    from: deployer,
    args: [deployer],
    log: true,
    autoMine: true,
  });

  const yourContract = await hre.ethers.getContract("YourContract", deployer);
  console.log("👋 Initial greeting:", await yourContract.greeting());
}

module.exports = deployYourContract;
module.exports.tags = ["YourContract"];
