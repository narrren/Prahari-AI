// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title TouristPermitRegistry
 * @dev Manages decentralized digital IDs and permits for the North East Region.
 */
contract TouristPermitRegistry {
    
    address public governmentAuthority;

    struct Permit {
        bytes32 identityHash; // SHA-256 hash of (Aadhaar/Passport + Secret Salt)
        uint256 issueDate;
        uint256 expiryDate;
        bool isActive;
        bool emergencyFlag;   // Triggered by AI if tourist is missing
    }

    // Mapping of Tourist Wallet Address (DID) to their Permit
    mapping(address => Permit) public permits;
    
    // Mapping to authorize specific Police/Tourism nodes to issue permits
    mapping(address => bool) public authorizedIssuers;

    event PermitIssued(address indexed tourist, uint256 expiry);
    event PermitRevoked(address indexed tourist);
    event EmergencyAlert(address indexed tourist, string reason);

    modifier onlyAuthority() {
        require(msg.sender == governmentAuthority || authorizedIssuers[msg.sender], "Not authorized");
        _;
    }

    constructor() {
        governmentAuthority = msg.sender;
        authorizedIssuers[msg.sender] = true;
    }

    /**
     * @dev Authorize a new police outpost or check-post to issue permits.
     */
    function authorizeIssuer(address _issuer) external {
        require(msg.sender == governmentAuthority, "Only MoDoNER can authorize");
        authorizedIssuers[_issuer] = true;
    }

    /**
     * @dev Issue a new Digital Permit.
     * @param _tourist The wallet address (DID) of the tourist.
     * @param _idHash The hashed PII of the tourist.
     * @param _duration Days the permit is valid for.
     */
    function issuePermit(address _tourist, bytes32 _idHash, uint256 _duration) external onlyAuthority {
        uint256 expiry = block.timestamp + (_duration * 1 days);
        
        permits[_tourist] = Permit({
            identityHash: _idHash,
            issueDate: block.timestamp,
            expiryDate: expiry,
            isActive: true,
            emergencyFlag: false
        });

        emit PermitIssued(_tourist, expiry);
    }

    /**
     * @dev AI Anomaly Engine calls this via a bridge if a tourist is flagged.
     */
    function setEmergencyFlag(address _tourist, bool _status) external onlyAuthority {
        permits[_tourist].emergencyFlag = _status;
        if(_status) {
            emit EmergencyAlert(_tourist, "AI_ANOMALY_DETECTED");
        }
    }

    /**
     * @dev Verification check for border guards or the Sentinel Dashboard.
     */
    function isPermitValid(address _tourist) public view returns (bool) {
        Permit memory p = permits[_tourist];
        return (p.isActive && block.timestamp <= p.expiryDate);
    }

    /**
     * @dev Revoke permit for security reasons.
     */
    function revokePermit(address _tourist) external onlyAuthority {
        permits[_tourist].isActive = false;
        emit PermitRevoked(_tourist);
    }
}
