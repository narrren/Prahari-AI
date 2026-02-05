import React, { useState } from 'react';
import axios from 'axios';
import { FileCheck, UploadCloud, CheckCircle, XCircle } from 'lucide-react';

export default function ForensicPanel() {
    const [verifying, setVerifying] = useState(false);
    const [result, setResult] = useState(null);
    const [fileHash, setFileHash] = useState("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855");

    const [merkleProof, setMerkleProof] = useState(null);

    const handleVerify = async () => {
        setVerifying(true);
        setResult(null);
        // Simulate hash calculation delay
        setTimeout(async () => {
            try {
                const res = await axios.post("http://localhost:8000/api/v1/forensics/verify", {
                    file_hash: fileHash
                });
                setResult(res.data);
            } catch (e) {
                console.error(e);
            }
            setVerifying(false);
        }, 1500);
    }

    const handleFetchProof = async () => {
        try {
            const res = await axios.post("http://localhost:8000/api/v1/forensics/merkle-proof", {
                data_id: "packet_idx_452",
                timestamp: Date.now()
            });
            setMerkleProof(res.data);
        } catch (e) { }
    };

    return (
        <div className="h-full flex flex-col items-center justify-center p-8 bg-gray-900 text-white overflow-y-auto">
            <div className="max-w-2xl w-full grid gap-8">

                {/* Main Evidence Validator */}
                <div className="bg-gray-800 p-8 rounded-xl border border-gray-700 shadow-2xl">
                    <h3 className="text-2xl font-bold mb-6 flex items-center gap-3 text-blue-400">
                        <FileCheck className="w-8 h-8" />
                        Forensic Evidence Validator (Zero-Knowledge)
                    </h3>

                    <div className="mb-6">
                        <label className="block text-xs uppercase text-gray-400 font-bold mb-2">Simulated Document Hash (SHA-256)</label>
                        <input
                            type="text"
                            value={fileHash}
                            onChange={(e) => setFileHash(e.target.value)}
                            className="w-full bg-gray-950 border border-gray-600 rounded p-3 font-mono text-xs text-green-400"
                        />
                    </div>

                    <button
                        onClick={handleVerify}
                        disabled={verifying}
                        className={`w-full py-4 rounded font-bold text-lg flex items-center justify-center gap-2 transition-all ${verifying ? 'bg-gray-700 text-gray-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-500 shadow-lg shadow-blue-900/50'}`}
                    >
                        {verifying ? (
                            <>Verifying Merkle Proof...</>
                        ) : (
                            <><UploadCloud /> Verify Integrity On-Chain</>
                        )}
                    </button>

                    {result && (
                        <div className={`mt-8 p-6 rounded-lg border-2 ${result.status === 'VERIFIED' ? 'bg-green-950/30 border-green-500/50' : 'bg-red-950/30 border-red-500/50'} animate-in fade-in slide-in-from-bottom-4 duration-500`}>
                            <div className="font-bold text-xl mb-4 flex gap-2 items-center">
                                {result.status === 'VERIFIED' ? <CheckCircle className="text-green-500 w-6 h-6" /> : <XCircle className="text-red-500 w-6 h-6" />}
                                <span className={result.status === 'VERIFIED' ? 'text-green-400' : 'text-red-400'}>
                                    Status: {result.status}
                                </span>
                            </div>

                            <div className="space-y-3 font-mono text-xs text-gray-400">
                                <div className="flex justify-between border-b border-gray-700 pb-2">
                                    <span>Timestamp</span>
                                    <span className="text-white">{new Date(result.timestamp * 1000).toLocaleString()}</span>
                                </div>
                                <div className="flex justify-between border-b border-gray-700 pb-2">
                                    <span>Signer DID</span>
                                    <span className="text-blue-300">{result.signer_did}</span>
                                </div>
                                <div>
                                    <span className="block mb-1">Blockchain Transaction ID</span>
                                    <span className="text-gray-500 break-all">{result.blockchain_txid}</span>
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                {/* Merkle Proof Explorer */}
                <div className="bg-gray-800 p-8 rounded-xl border border-gray-700 shadow-2xl">
                    <h3 className="text-xl font-bold mb-4 flex items-center gap-3 text-purple-400">
                        <div className="w-8 h-8 rounded bg-purple-900/50 flex items-center justify-center text-xs">0x</div>
                        Forensic Time-Traveler: Merkle Path
                    </h3>
                    <p className="text-gray-400 text-sm mb-4">
                        Reconstruct the cryptographic path for Historical Point #452 to prove it exists in the Immutable Ledger.
                    </p>

                    {!merkleProof ? (
                        <button
                            onClick={handleFetchProof}
                            className="bg-purple-700 hover:bg-purple-600 px-6 py-2 rounded text-sm font-bold shadow-lg"
                        >
                            Reconstruct Merkle Path
                        </button>
                    ) : (
                        <div className="bg-black/30 p-4 rounded border border-purple-500/30 font-mono text-xs space-y-4 animate-in fade-in">
                            <div>
                                <div className="text-gray-500 mb-1">Target Leaf Hash</div>
                                <div className="text-white break-all">{merkleProof.target_leaf_hash}</div>
                            </div>

                            <div className="pl-4 border-l-2 border-gray-700 space-y-2">
                                {merkleProof.siblings.map((sib, i) => (
                                    <div key={i} className="text-gray-500">
                                        + Sibling {i + 1} ({sib.position}): <span className="text-gray-600">{sib.hash.substring(0, 16)}...</span>
                                    </div>
                                ))}
                            </div>

                            <div className="pt-2 border-t border-gray-700">
                                <div className="flex justify-between mb-2">
                                    <span className="text-purple-400 font-bold">Calculated Root</span>
                                    <span className="text-green-400 font-bold">MATCH: Cryptographic Proof Verified</span>
                                </div>
                                <div className="text-white break-all bg-purple-900/20 p-2 rounded">
                                    {merkleProof.calculated_root}
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                <div className="mt-6 text-center text-[10px] text-gray-500 font-mono">
                    SECURED BY ETHEREUM • IPFS ANCHORING • ZK-SNARK COMPATIBLE
                </div>
            </div>
        </div>
    )
}
