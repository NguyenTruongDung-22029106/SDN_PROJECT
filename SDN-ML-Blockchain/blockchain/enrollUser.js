/*
  enrollUser.js

  Helper to enroll an admin and register/enroll a user via Fabric CA and store
  the resulting identity in the file system wallet used by the adapter.

  Usage:
    node enrollUser.js ADMIN_NAME ADMIN_PW NEW_USER

  Environment (optional):
    CA_URL - URL to the CA (e.g. https://localhost:7054)
    WALLET_PATH - path to wallet (default: ./wallet)
    MSP_ID - Org MSP ID (default: Org1MSP)
    AFFILIATION - user affiliation (default: org1.department1)
    IDENTITY_LABEL - label for the new user (default: User1@org1.example.com)
*/

const FabricCAServices = require('fabric-ca-client');
const { Wallets } = require('fabric-network');
const fs = require('fs');
const path = require('path');
require('dotenv').config();

async function main() {
  const caURL = process.env.CA_URL || 'https://localhost:7054';
  const walletPath = process.env.WALLET_PATH || path.join(__dirname, 'wallet');
  const mspId = process.env.MSP_ID || 'Org1MSP';
  const affiliation = process.env.AFFILIATION || 'org1.department1';

  const adminName = process.argv[2] || 'admin';
  const adminPass = process.argv[3] || 'adminpw';
  const userId = process.argv[4] || (process.env.IDENTITY_LABEL || 'User1@org1.example.com');

  const ca = new FabricCAServices(caURL, { trustedRoots: [], verify: false });
  const wallet = await Wallets.newFileSystemWallet(walletPath);

  // enroll admin if not present
  const adminIdentity = await wallet.get(adminName);
  if (!adminIdentity) {
    console.log('Enrolling admin...');
    const enrollment = await ca.enroll({ enrollmentID: adminName, enrollmentSecret: adminPass });
    const x509Identity = {
      credentials: { certificate: enrollment.certificate, privateKey: enrollment.key.toBytes() },
      mspId: mspId,
      type: 'X.509'
    };
    await wallet.put(adminName, x509Identity);
    console.log('Admin enrolled and imported to wallet');
  } else {
    console.log('Admin identity already in wallet');
  }

  // register & enroll user
  const userIdentity = await wallet.get(userId);
  if (userIdentity) {
    console.log(`${userId} already exists in the wallet`);
    return;
  }

  // build admin user context from wallet
  const provider = wallet.getProviderRegistry().getProvider((adminIdentity && adminIdentity.type) || 'X.509');
  const adminUser = await provider.getUserContext(adminIdentity, adminName);

  const secret = await ca.register({ affiliation, enrollmentID: userId, role: 'client' }, adminUser);
  const enrollment = await ca.enroll({ enrollmentID: userId, enrollmentSecret: secret });
  const userX509 = {
    credentials: { certificate: enrollment.certificate, privateKey: enrollment.key.toBytes() },
    mspId: mspId,
    type: 'X.509'
  };
  await wallet.put(userId, userX509);
  console.log(`Successfully registered and enrolled user ${userId} and imported it into the wallet`);
}

main().catch(err => { console.error('Failed to enroll user:', err); process.exit(1); });
