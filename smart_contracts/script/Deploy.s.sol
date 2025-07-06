// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import "../src/AskWorld.sol";

contract DeployScript is Script {
    AskWorld public askWorld;
    
    // Deployment addresses
    address public deployer;
    address public initialAIValidator;
    
    // Environment variables
    uint256 public deployerPrivateKey;
    string public rpcUrl;
    
    function setUp() public {
        // Get deployment configuration from environment
        deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        rpcUrl = vm.envString("RPC_URL");
        
        // Set deployer address from private key
        deployer = vm.addr(deployerPrivateKey);
        
        // Set initial AI validator (can be same as deployer or different)
        initialAIValidator = vm.envOr("INITIAL_AI_VALIDATOR", deployer);
        
        console.log("Deployment Configuration:");
        console.log("Deployer:", deployer);
        console.log("Initial AI Validator:", initialAIValidator);
        console.log("RPC URL:", rpcUrl);
    }

    function run() public {
        console.log("Starting AskWorld deployment...");
        
        // Start broadcasting transactions
        vm.startBroadcast(deployerPrivateKey);
        
        // Deploy the contract
        askWorld = new AskWorld();
        
        console.log("AskWorld deployed at:", address(askWorld));
        
        // Add initial AI validator if different from deployer
        if (initialAIValidator != deployer) {
            askWorld.owner_addAIValidator(initialAIValidator);
            console.log("Added initial AI validator:", initialAIValidator);
        }
        
        // Stop broadcasting
        vm.stopBroadcast();
        
        console.log("Deployment completed successfully!");
        console.log("Contract address:", address(askWorld));
        console.log("Owner:", askWorld.owner());
        console.log("Initial AI Validator is validator:", askWorld.isAIValidator(initialAIValidator));
        
        // Display deployment info
        _displayDeploymentInfo();
    }
    
    function _displayDeploymentInfo() internal {
        console.log("Deployment Info:");
        console.log("================");
        console.log("Contract: AskWorld");
        console.log("Address:", address(askWorld));
        console.log("Deployer:", deployer);
        console.log("Owner:", askWorld.owner());
        console.log("Initial AI Validator:", initialAIValidator);
        console.log("Network:", rpcUrl);
        console.log("Block:", block.number);
        console.log("Timestamp:", block.timestamp);
        console.log("========================");
    }
}

// Additional deployment script for testing
contract DeployTestScript is Script {
    AskWorld public askWorld;
    
    function run() public {
        console.log("Deploying AskWorld for testing...");
        
        // Get deployer address from private key
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address deployer = vm.addr(deployerPrivateKey);
        
        // Deploy with default settings for testing
        askWorld = new AskWorld();
        
        console.log("AskWorld deployed at:", address(askWorld));
        console.log("Owner:", askWorld.owner());
        
        // Add deployer as AI validator for testing
        askWorld.owner_addAIValidator(deployer);
        console.log("Added deployer as AI validator for testing");
    }
} 