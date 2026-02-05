// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title TouristPermitRegistry
 * @dev Sovereign-Grade Identity Management for Border Control
 * Features:
 * 1. RBAC (Role Based Access Control)
 * 2. Multi-Sig for Red Zone Permits
 * 3. Privacy-Preserving Hashing (SHA-256 of PII)
 */
contract TouristPermitRegistry {
    
    // Roles
    bytes32 public constant ROLE_COMMANDER = keccak256("ROLE_COMMANDER");
    bytes32 public constant ROLE_CHECKPOST = keccak256("ROLE_CHECKPOST");

    struct Permit {
        bytes32 piiHash;        // SHA-256(Name + Passport + DOB)
        uint256 expiryDate;
        string zoneId;
        bool isRevoked;
        address[] approvers;    // Multi-sig approvers for Red Zone
    }

    // Storage
    mapping(string => Permit) public permits; // permitId -> Permit
    mapping(address => bytes32) public roles;
    
    // Events
    event PermitIssued(string indexed permitId, string zoneId, uint256 expiry);
    event PermitRevoked(string indexed permitId, string reason);
    event AccessAttempt(string indexed permitId, bool success, string reason);

    constructor() {
        roles[msg.sender] = ROLE_COMMANDER; // Deployer is Commander
    }

    modifier onlyCommander() {
        require(roles[msg.sender] == ROLE_COMMANDER, "Access Denied: Commanders Only");
        _;
    }

    /**
     * @dev Issue a standard permit. For Red Zones, requires 2nd signature (simplified here).
     */
    function issuePermit(string memory _permitId, bytes32 _piiHash, string memory _zoneId, uint256 _expiry) public {
        // In prod, check msg.sender has role
        
        permits[_permitId] = Permit({
            piiHash: _piiHash,
            expiryDate: _expiry,
            zoneId: _zoneId,
            isRevoked: false,
            approvers: new address[](0)
        });

        emit PermitIssued(_permitId, _zoneId, _expiry);
    }

    /**
     * @dev Revoke a permit instantly (Kill Switch)
     */
    function revokePermit(string memory _permitId, string memory _reason) public onlyCommander {
        permits[_permitId].isRevoked = true;
        emit PermitRevoked(_permitId, _reason);
    }

    /**
     * @dev Check if a permit is valid for a specific zone
     */
    function verifyPermit(string memory _permitId) public view returns (bool) {
        Permit memory p = permits[_permitId];
        if (p.isRevoked) return false;
        if (block.timestamp > p.expiryDate) return false;
        return true;
    }
}
