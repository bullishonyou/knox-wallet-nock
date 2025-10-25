# KNOX - Nockchain Web Wallet

🔐 **An open-source GUI web wallet for Nockchain**

KNOX is a simple web-based wallet application that makes it easy to create wallets, manage keys, check balances, and send transactions on the Nockchain network—all from your browser.

**DONATIONS**:
(v1) 5pL9VpymCfL5f5SCSkqDpHXY5C3QSD8Zm4vnPiZYJz4zUU1zZCU8KAg

---

## 📋 Quick Start (5 Minutes)

### Prerequisites

Before you begin, you need:

1. **Python 3.9 or higher** - [Download here](https://www.python.org/downloads/)
2. **Nockchain CLI tools** - Follow the [Nockchain setup guide](https://github.com/zorp-corp/nockchain)
3. **A running Nockchain node** - Start this before using KNOX to show updated balances and send transactions.
(!!! You you are on macOS you don't need to run a node)

### Installation Steps

#### Step 1: Clone the Repository

```bash
git clone https://github.com/bullishonyou/knox-wallet-nock.git
cd knox-wallet-nock
```

#### Step 2: Create a Python Virtual Environment

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

#### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

#### Step 4: Start the Application

```bash
python app.py
```

You should see:
```
* Running on http://127.0.0.1:5000
```

**Open your browser to:** `http://localhost:5000`

---

## 🎯 Features

| Feature | Description |
|---------|-------------|
| 🔑 **Create Wallet** | Generate a new wallet with secure keypair |
| 📥 **Import Wallet** | Import existing wallet using seed phrase or private key |
| 💰 **Check Balance** | View your balance and full transaction history |
| 📤 **Send Transaction** | Send NOCK to other addresses |
| 📊 **Manage Wallets** | View all your wallets in one place |

---

## 📖 How to Use KNOX

### 1. Create a New Wallet

1. Go to **Create Wallet** in the menu
2. Click **Generate New Wallet**
3. You'll see your wallet info in copyable boxes:
   - **Address** (public address)
   - **Private Key** (keep secret!)
   - **Public Key**
   - **Seed Phrase** (backup for recovery)
   - **Version** (0 or 1)

⚠️ **IMPORTANT:** Save your **Private Key** and **Seed Phrase** somewhere safe. You cannot recover your wallet without them!

### 2. Import an Existing Wallet

1. Go to **Import Wallet** in the menu
2. Choose your import method:
   - **Seed Phrase**: Enter your seed phrase (space-separated words)
   - **Extended Private Key**: Enter your private key
3. Select the wallet version (0 or 1)
4. Click **Import Wallet**
5. Your wallet is now active!

### 3. Send a Transaction

**Note:** Only available if you are running a synced node.

1. Go to **Send** in the menu
2. Select your wallet (sender)
3. Enter the recipient's address
4. Enter the amount in NOCK
5. Set transaction fee (default: 0.00001 NOCK)
6. Click **Send Transaction**

✅ Transaction sent! The blockchain will confirm it.

### 4. Manage Multiple Wallets

1. Go to **Manage Wallets** in the menu
2. See all your wallets (address, version, active status)
3. Click on an inactive wallet to set it as active wallet
4. Your dashboard will update automatically

---

## 📁 Project Structure

```
knox-wallet-nock/
├── app.py                    # Flask web server & API
├── cli_integration.py        # Nockchain CLI wrapper
├── requirements.txt          # Python packages
├── README.md                 # This file
├── templates/                # Web pages
│   ├── base.html            # Navigation header
│   ├── dashboard.html       # Home page
│   ├── create_wallet.html   # Create wallet page
│   ├── import_wallet.html   # Import wallet page
│   ├── transactions.html    # Transactions history page
│   ├── manage_wallets.html  # All wallets page
│   └── send_transaction.html # Send TX page
└── static/                  # CSS & JavaScript
    ├── css/style.css        # Dark theme styles
    └── js/app.js           # Helper functions
```

---

## 🔧 Configuration

### Change Node Settings

Edit `cli_integration.py` to use a different node:

```python
cli = NockchainWalletCLI(
    private_grpc_port=5555,           # Your local node port
    public_grpc_addr="https://nockchain-api.zorp.io"  # Fallback server
)
```

### Environment Variables

Create a `.env` file to customize Flask settings:

```env
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
FLASK_DEBUG=True
```

---

## 🆘 Troubleshooting

### "nockchain-wallet not found"

The `nockchain-wallet` CLI is not installed or not in your PATH.

**Solution:** Install Nockchain from the [official repository](https://github.com/zorp-corp/nockchain)

```bash
# Verify installation
nockchain-wallet --version
```

### "Cannot connect to node"

Your Nockchain node is not running or not reachable.

**Solution:** Start your Nockchain node in your /nockchain folder:

```bash
bash ./scripts/run_nockchain_node.sh
```

### "Balance shows zero but I have coins"

Your node is probably not synced.

**Solution:** Wait for your node to be synced with the latest block. You can find a .jam file [here](https://syncflash.site/) and run:

```bash
  nockchain --state-jam <latest-jam-downloaded>
```

### "Transaction failed"

Several possible reasons:

- ❌ **Invalid address**: Copy-paste the full recipient address
- ❌ **Insufficient balance**: Balance must cover amount + fee
- ❌ **Node not synced**: Wait for your node to sync to latest block
- ❌ **Fee too low**: Try increasing the fee

---

## 💾 Wallet Data

KNOX stores wallet data through the `nockchain-wallet` CLI. Your keys are stored in:

```
~/nockchain/
```

**Backup Important:** Always backup this folder to recover your wallets!

---

## 🔒 Security Tips

✅ **DO:**
- Save your seed phrase and private key offline
- Run the node locally for maximum security
- Keep your Python environment up to date

❌ **DON'T:**
- Share your private key or seed phrase with anyone
- Save keys in email or cloud storage
- Use KNOX on untrusted computers
- Send money to unverified addresses

---

## 📚 API Reference

For developers integrating with KNOX:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/status` | GET | Get wallet status |
| `/api/create-wallet` | POST | Create new wallet |
| `/api/import-wallet` | POST | Import wallet |
| `/api/balance/<address>` | GET | Get balance & transactions |
| `/api/wallets` | GET | List all wallets |
| `/api/active-wallet` | GET | Get active wallet |
| `/api/refresh-balance` | POST | Fetch fresh balance |
| `/api/set-active-wallet` | POST | Change active wallet |

---


## 🤝 Contributing

We welcome contributions!

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Commit: `git commit -m 'Add my feature'`
5. Push: `git push origin feature/my-feature`
6. Open a Pull Request

---

## 📞 Support & Resources

- **KNOX Community**: [Telegram](https://t.me/knoxcommunity)
- **Nockchain Docs**: [github.com/zorp-corp/nockchain](https://github.com/zorp-corp/nockchain)
- **Issues**: [GitHub Issues](https://github.com/bullishonyou/knox-wallet-nock/issues)

---

## 📄 License

MIT License - See LICENSE file for details

---

**KNOX** - Making Nockchain wallets accessible to everyone 🚀
