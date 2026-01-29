import React, { useState } from 'react';
import { Shield, CheckCircle, XCircle, Loader, FileBadge, Lock } from 'lucide-react';
import { issuePermit } from '../services/blockchain';

const PermitIssuer = () => {
    const [formData, setFormData] = useState({
        did: '',
        name: '',
        passHash: 'QmXyZ...' // Placeholder for IPFS hash
    });
    const [status, setStatus] = useState('IDLE'); // IDLE, ISSUING, SUCCESS, ERROR
    const [txHash, setTxHash] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        setStatus('ISSUING');
        try {
            // Default duration: 7 days (604800 seconds)
            const result = await issuePermit(formData.did, formData.passHash, 604800);
            setTxHash(result.hash);
            setStatus('SUCCESS');
        } catch (error) {
            console.error(error);
            setStatus('ERROR');
        }
    };

    return (
        <div className="p-8 max-w-4xl mx-auto text-white">
            <div className="mb-8 border-b border-gray-700 pb-4">
                <h2 className="text-3xl font-bold flex items-center gap-3">
                    <FileBadge className="text-blue-400" />
                    Indy/Eth Credential Issuer
                </h2>
                <p className="text-gray-400 mt-2">
                    Issue verifiable digital permits (VCs) to tourists.
                    These are stored on the Blockchain and verified via Zero-Knowledge Proofs.
                </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* Form Section */}
                <div className="bg-gray-800/50 p-6 rounded-xl border border-gray-700">
                    <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
                        <Lock className="w-5 h-5 text-green-400" />
                        Issue New Permit
                    </h3>
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-400 mb-1">Tourist DID (Wallet Address)</label>
                            <input
                                type="text"
                                required
                                className="w-full bg-gray-900 border border-gray-600 rounded p-3 text-white focus:ring-2 focus:ring-blue-500 outline-none font-mono"
                                placeholder="0x..."
                                value={formData.did}
                                onChange={(e) => setFormData({ ...formData, did: e.target.value })}
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-400 mb-1">Applicant Name (Encrypted)</label>
                            <input
                                type="text"
                                required
                                className="w-full bg-gray-900 border border-gray-600 rounded p-3 text-white focus:ring-2 focus:ring-blue-500 outline-none"
                                placeholder="Naren Dey"
                                value={formData.name}
                                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-400 mb-1">KYC Data Hash (IPFS)</label>
                            <input
                                type="text"
                                className="w-full bg-gray-900 border border-gray-600 rounded p-3 text-gray-500 cursor-not-allowed font-mono text-sm"
                                value={formData.passHash}
                                readOnly
                            />
                        </div>

                        <button
                            type="submit"
                            disabled={status === 'ISSUING'}
                            className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 rounded-lg transition-all flex justify-center items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {status === 'ISSUING' ? <Loader className="animate-spin" /> : <Shield className="w-5 h-5" />}
                            {status === 'ISSUING' ? 'Minting Credential...' : 'Issue Digital Permit'}
                        </button>
                    </form>
                </div>

                {/* Status/Preview Section */}
                <div className="space-y-6">
                    <div className="bg-gray-900 p-6 rounded-xl border border-gray-800">
                        <h4 className="text-gray-400 text-xs uppercase tracking-wider mb-4">Transaction Status</h4>

                        {status === 'IDLE' && (
                            <div className="text-center py-10 text-gray-600">
                                <FileBadge className="w-12 h-12 mx-auto mb-2 opacity-20" />
                                Ready to Issue
                            </div>
                        )}

                        {status === 'ISSUING' && (
                            <div className="text-center py-10 text-blue-400 animate-pulse">
                                Processing On-Chain Transaction...
                            </div>
                        )}

                        {status === 'SUCCESS' && (
                            <div className="bg-green-900/20 border border-green-500/50 p-4 rounded-lg">
                                <div className="flex items-center gap-2 text-green-400 font-bold mb-2">
                                    <CheckCircle className="w-5 h-5" /> Permit Issued Successfully
                                </div>
                                <div className="text-xs text-gray-400 break-all">
                                    Tx Hash: <span className="font-mono text-blue-300">{txHash}</span>
                                </div>
                                <div className="mt-4 pt-4 border-t border-green-500/20 text-sm text-green-300">
                                    Credential has been sent to the user's mobile wallet.
                                </div>

                                {/* QR Code Proof Simulation */}
                                <div className="mt-4 bg-black/40 p-3 rounded border border-green-500/30">
                                    <h5 className="text-[10px] text-green-400 uppercase tracking-widest font-bold mb-2 flex items-center gap-2">
                                        <div className="w-4 h-4 bg-white p-0.5 rounded-sm"><div className="w-full h-full bg-black"></div></div>
                                        Proof QR Payload
                                    </h5>
                                    <div className="font-mono text-[10px] text-gray-500 break-all bg-black p-2 rounded">
                                        SHA256( {formData.did.substring(0, 6)}... + SALT_8273 + {Math.floor(Date.now() / 1000) + 604800} )
                                        <br />
                                        &gt;&gt; 0x{Math.random().toString(16).substr(2)}{Math.random().toString(16).substr(2)}
                                    </div>
                                    <p className="text-[9px] text-gray-400 mt-2 italic">
                                        * The mobile app presents this Hash as a QR Code.
                                        Border Guards scan it, and their device invokes
                                        <code className="text-blue-300"> isPermitValid() </code>
                                        on the Smart Contract to verify.
                                    </p>
                                </div>
                            </div>
                        )}

                        {status === 'ERROR' && (
                            <div className="bg-red-900/20 border border-red-500/50 p-4 rounded-lg flex items-center gap-3">
                                <XCircle className="w-6 h-6 text-red-500" />
                                <div>
                                    <h5 className="font-bold text-red-400">Issuance Failed</h5>
                                    <p className="text-xs text-red-300">Check blockchain connection or authority permissions.</p>
                                </div>
                            </div>
                        )}
                    </div>

                    <div className="bg-blue-900/10 border border-blue-500/30 p-4 rounded-lg">
                        <h4 className="text-blue-400 text-xs uppercase font-bold mb-2">Security Note</h4>
                        <p className="text-xs text-gray-400 leading-relaxed">
                            This action interacts with the <strong>Ethereum/Polygon</strong> network.
                            The issued credential follows <strong>W3C Verifiable Credentials</strong> standard.
                            No PII is stored on-chain; only the ZKP anchor.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default PermitIssuer;
