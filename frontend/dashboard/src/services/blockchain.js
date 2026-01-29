import { ethers } from 'ethers';

// Ganache Default
const RPC_URL = "http://localhost:8545";

// You would update this after deployment
export const CONTRACT_ADDRESS = "0x0000000000000000000000000000000000000000";

// Human-Readable ABI for TouristPermitRegistry
const ABI = [
    "function issuePermit(address _tourist, string _dataHash, uint256 _durationSeconds) external",
    "function verifyPermit(address _tourist) external view returns (bool)",
    "function revokePermit(address _tourist) external",
    "event PermitIssued(address indexed tourist, uint256 issueDate, uint256 expiryDate)"
];

export const getProvider = () => {
    return new ethers.JsonRpcProvider(RPC_URL);
};

export const getSigner = async (provider) => {
    // In a browser with Metamask, you'd use browser provider.
    // For this local demo with Ganache, we might need a private key or just use the provider's default signer if it exposes one (unlocked accounts).
    // Localhost providers often have unlocked accounts (index 0).
    const signer = await provider.getSigner(0);
    return signer;
};

export const getContract = async () => {
    const provider = getProvider();
    const signer = await getSigner(provider);
    return new ethers.Contract(CONTRACT_ADDRESS, ABI, signer);
};

export const issuePermit = async (touristAddress, dataHash, durationSeconds) => {
    console.log(`Issuing permit to ${touristAddress}...`);
    // Simulation Mode if contract not deployed
    if (CONTRACT_ADDRESS === "0x0000000000000000000000000000000000000000") {
        console.warn("Using Mock Implementation - Contract not deployed");
        await new Promise(r => setTimeout(r, 2000)); // Fake network delay
        return { hash: "0xMockTransactionHash" + Math.random().toString(16).substr(2) };
    }

    try {
        const contract = await getContract();
        const tx = await contract.issuePermit(touristAddress, dataHash, durationSeconds);
        await tx.wait();
        return tx;
    } catch (error) {
        console.error("Blockchain Error:", error);
        throw error;
    }
};
