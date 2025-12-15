// import_identity.js
// Helper to import an identity from fabric-samples test-network MSP files into the local wallet

const fs = require('fs');
const path = require('path');
const { Wallets, X509WalletMixin } = require('fabric-network');

async function main() {
  const walletPath = process.env.WALLET_PATH || path.join(__dirname, 'wallet');
  const mspPath = process.env.MSP_PATH || path.join(__dirname, '..', 'fabric-samples', 'test-network', 'organizations', 'peerOrganizations', 'org1.example.com', 'users', 'User1@org1.example.com', 'msp');
  const identityLabel = process.env.IDENTITY_LABEL || 'User1@org1.example.com';

  const certPath = path.join(mspPath, 'signcerts', 'cert.pem');
  const keyDir = path.join(mspPath, 'keystore');

  if (!fs.existsSync(certPath)) {
    console.error('Certificate not found at', certPath);
    process.exit(1);
  }

  const keyFiles = fs.readdirSync(keyDir).filter(f => f.endsWith('_sk'));
  if (keyFiles.length === 0) {
    console.error('No private key file found in', keyDir);
    process.exit(1);
  }
  const keyPath = path.join(keyDir, keyFiles[0]);

  const cert = fs.readFileSync(certPath, 'utf8');
  const key = fs.readFileSync(keyPath, 'utf8');

  const wallet = await Wallets.newFileSystemWallet(walletPath);
  // Create X.509 identity
  const identity = {
    credentials: {
      certificate: cert,
      privateKey: key
    },
    mspId: 'Org1MSP',
    type: 'X.509'
  };

  await wallet.put(identityLabel, identity);
  console.log(`Imported identity ${identityLabel} into wallet at ${walletPath}`);
}

main().catch(err => { console.error(err); process.exit(1); });
