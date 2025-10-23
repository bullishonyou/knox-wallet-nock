# KNOX - Quick Start Guide

Get KNOX running in 5 minutes! 🚀

## Prerequisites Checklist

- [ ] Python 3.9+ installed
- [ ] `nockchain-wallet` CLI installed
- [ ] Nockchain node running locally

## Installation (3 steps)

### Step 1: Clone & Setup

```bash
git clone https://github.com/zorp-corp/knox-wallet-nock.git
cd knox-wallet-nock
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Run KNOX

```bash
python app.py
```

Open your browser to: **http://localhost:5000**

## Basic Workflow

### 1️⃣ First Time Setup

1. Navigate to the dashboard
2. Check that your node shows as 🟢 Connected
3. Click **"Create Wallet"** to generate your first wallet
4. **SAVE YOUR SEED PHRASE** somewhere secure!

### 2️⃣ Check Your Balance

1. Click **"Balance"** in the menu
2. Select your address
3. Click **"Check Balance"**
4. View your NOCK balance and transaction history

### 3️⃣ Send NOCK

1. Click **"Send"** in the menu
2. Select your address as the sender
3. Paste the recipient's public address
4. Enter the amount in NOCK
5. Review the summary
6. Click **"Send Transaction"**

## Common Issues & Fixes

### ❌ "nockchain-wallet not found"

```bash
# Check if installed
which nockchain-wallet

# If not found, install nockchain first
# See: https://github.com/zorp-corp/nockchain
```

### ❌ Node shows as disconnected

```bash
# Make sure your node is running
# In another terminal:
nockchain-node

# KNOX will automatically detect it
```

### ❌ "Transaction failed"

- Verify you have enough balance (amount + fee)
- Check the recipient address is valid
- Ensure your node is fully synced

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+C` | Stop the server (in terminal) |

## Need Help?

1. **Check the README**: More detailed info in `/README.md`
2. **Nockchain Docs**: https://github.com/zorp-corp/nockchain
3. **Report Issues**: Open an issue on GitHub

## Next Steps

- ✅ Explore all wallet features
- ✅ Create multiple wallets
- ✅ Practice sending test transactions
- ✅ Read the full README for advanced features

---

**Happy transacting with KNOX! 🔐**
