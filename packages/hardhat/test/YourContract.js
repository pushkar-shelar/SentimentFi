const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("YourContract", function () {
  let yourContract;

  before(async () => {
    const [owner] = await ethers.getSigners();
    const YourContractFactory = await ethers.getContractFactory("YourContract");
    yourContract = await YourContractFactory.deploy(owner.address);
    await yourContract.waitForDeployment();
  });

  describe("Deployment", function () {
    it("Should have the right message on deploy", async function () {
      expect(await yourContract.greeting()).to.equal("Building Unstoppable Apps!!!");
    });

    it("Should allow setting a new message", async function () {
      const newGreeting = "Learn Scaffold-ETH 2! :)";
      await yourContract.setGreeting(newGreeting);
      expect(await yourContract.greeting()).to.equal(newGreeting);
    });
  });
});
