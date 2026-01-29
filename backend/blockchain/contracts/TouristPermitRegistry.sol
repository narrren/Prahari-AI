// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title TouristPermitRegistry
 * @dev Manages decentralized identity permissions for tourists in the NER region.
 * Implements a basic Self-Sovereign Identity (SSI) registry pattern.
 * SECURITY: Access control restricts permit issuance to designated authorities.
 */
contract TouristPermitRegistry {
    
    // Role definitions
    address public authority;

    // Struct to hold permit details
    struct Permit {
        bool isValid;
        uint256 issueDate;
        uint256 expiryDate;
        string dataHash; // IPFS hash or hash of the private data (ZKP verification anchor)
    }

    // Mapping from Tourist Wallet Address (DID) to their Permit
    mapping(address => Permit) private permits;

    // Events for audit trails (Immutable logging)
    event PermitIssued(address indexed tourist, uint256 issueDate, uint256 expiryDate);
    event PermitRevoked(address indexed tourist, uint256 revokeDate);
    event AuthorityTransferred(address indexed previousAuthority, address indexed newAuthority);

    // Modifier to restrict access to the Government Authority
    modifier onlyAuthority() {
        require(msg.sender == authority, "Security Alert: Unauthorized Access Attempt.");
        _;
    }

    constructor() {
        authority = msg.sender; // Deployer is the initial Authority
    }

    /**
     * @notice Issues a new travel permit to a tourist.
     * @param _tourist The wallet address (DID) of the tourist.
     * @param _dataHash Hash of the off-chain secure data (KYC, ZKP proof).
     * @param _durationSeconds Validity duration in seconds.
     */
    function issuePermit(address _tourist, string calldata _dataHash, uint256 _durationSeconds) external onlyAuthority {
        require(_tourist != address(0), "Invalid address");
        
        permits[_tourist] = Permit({
            isValid: true,
            issueDate: block.timestamp,
            expiryDate: block.timestamp + _durationSeconds,
            dataHash: _dataHash
        });

        emit PermitIssued(_tourist, block.timestamp, block.timestamp + _durationSeconds);
    }

    /**
     * @notice PRIMARY VERIFICATION FUNCTION (The "Success" Feature)
     * @dev Checks if a tourist has a valid, non-expired permit.
     * Implements "Time-Locked" logic: Automatically fails if block.timestamp > expiryDate.
     * @param _tourist The wallet address to verify.
     * @return isValidParam True if permit is active, authorized, and within the valid time window.
     */
    function isPermitValid(address _tourist) external view returns (bool) {
        Permit memory p = permits[_tourist];
        
        // 1. Check Existence & Revocation status
        if (!p.isValid) {
            return false;
        }
        
        // 2. Time-Lock Check (Automatic Expiration)
        // The blockchain timestamp serves as the immutable time source.
        if (block.timestamp > p.expiryDate) {
            return false;
        }
        
        return true;
    }

    /**
     * @notice Revokes a permit in case of violation or emergency.
     * @param _tourist The wallet address to revoke.
     */
    function revokePermit(address _tourist) external onlyAuthority {
        require(permits[_tourist].isValid, "No active permit found");
        permits[_tourist].isValid = false;
        emit PermitRevoked(_tourist, block.timestamp);
    }

    /**
     * @notice Transfers the authority role to a new address.
     * @param _newAuthority Address of the new authority.
     */
    function transferAuthority(address _newAuthority) external onlyAuthority {
        require(_newAuthority != address(0), "Invalid authority address");
        emit AuthorityTransferred(authority, _newAuthority);
        authority = _newAuthority;
    }
}
