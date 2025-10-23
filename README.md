# KNOX - Nockchain Wallet

🔐 A modern, open-source web-based wallet application for the Nockchain protocol.

## Features

- ✅ **Create New Wallets** - Generate new keypairs with secure key management
- 📥 **Import Wallets** - Import existing wallets via seed phrase or key file
- 💰 **View Balance** - Check your balance and transaction history
- 📤 **Send Transactions** - Send NOCK to other addresses with customizable fees

## Requirements

Before installing KNOX, make sure you have:

1. **Python 3.9+** - [Download Python](https://www.python.org/downloads/)
2. **Nockchain CLI** - Install from [Nockchain Repository](https://github.com/zorp-corp/nockchain)
3. **Running Nockchain Node** - A local node must be running for most operations

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/zorp-corp/knox-wallet-nock.git
cd knox-wallet-nock
```

### 2. Create a Virtual Environment (Recommended)

```bash
# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Application

```bash
python app.py
```

The application will start on `http://localhost:5000`

## Usage

### Dashboard

Navigate to the dashboard to:
- Check active address details
- See quick access to main features

### Create Wallet

1. Click "Create Wallet" in the navigation menu
2. Click "Generate New Wallet"
3. Save your private key and seed phrase securely
4. Your new wallet is ready to use

**⚠️ Important:** Always save your private key and seed phrase in a secure location. You cannot recover your wallet without them!

### Import Wallet

1. Click "Import Wallet" in the navigation menu
2. Choose import method:
   - **Seed Phrase**: Paste your seed phrase
   - **Private Key**: Paste your private key
3. Click "Import Wallet"

### Check Balance

1. Click "Balance" in the navigation menu
2. Select your address from the dropdown
3. Click "Check Balance"
4. View your total balance and transaction history

Amounts are displayed in NOCK (1 NOCK = 65536 nicks)

### Send Transaction

1. Click "Send" in the navigation menu
2. Select the sender address
3. Enter the recipient's public address
4. Enter the amount in NOCK
5. Set the transaction fee (default: 0.00001 NOCK)
6. Review the summary
7. Click "Send Transaction"

**Note:** Ensure your wallet has sufficient balance to cover both the amount and fee.

## Configuration

### Node Connection

KNOX automatically connects to the Nockchain node. The default configuration is:

- **Private gRPC Port**: `5555` (for local node connection)
- **Public gRPC Server**: `https://nockchain-api.zorp.io`

To customize these settings, modify the `cli_integration.py` file:

```python
cli = NockchainWalletCLI(
    private_grpc_port=5555,
    public_grpc_addr="https://nockchain-api.zorp.io"
)
```

### Environment Variables

Create a `.env` file to configure:

```env
# Flask configuration
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
FLASK_DEBUG=True
```

## Project Structure

```
knox-wallet-nock/
├── app.py                 # Main Flask application
├── cli_integration.py     # Nockchain CLI wrapper
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── .gitignore            # Git ignore rules
├── templates/            # HTML templates
│   ├── base.html         # Base layout
│   ├── dashboard.html    # Dashboard
│   ├── create_wallet.html
│   ├── import_wallet.html
│   ├── balance.html
│   └── send_transaction.html
└── static/               # Static assets
    ├── css/
    │   └── style.css     # Main stylesheet
    └── js/
        └── app.js        # JavaScript utilities
```

## API Endpoints

### GET `/` 
Dashboard homepage

### GET `/api/status`
Get wallet and node status
```json
{
  "success": true,
  "connected": true,
  "addresses": ["address1", "address2"],
  "error": null
}
```

### POST `/api/create-wallet`
Create a new wallet
```json
{
  "success": true,
  "message": "New wallet created!",
  "data": {...}
}
```

### POST `/api/import-wallet`
Import a wallet
```json
{
  "seed_phrase": "word1 word2 ...",
  "key_file": null
}
```

### GET `/api/balance/<pubkey>`
Get balance for a public key
```json
{
  "success": true,
  "pubkey": "...",
  "total_balance_nicks": 1000000,
  "total_balance_nock": 15.26,
  "transactions": [...]
}
```

### POST `/api/send-transaction`
Send a transaction
```json
{
  "sender": "...",
  "recipient": "...",
  "amount": 1.5,
  "fee": 0.00001
}
```

## Nockchain Integration

KNOX uses the `nockchain-wallet` CLI tool for all wallet operations. Make sure you have the latest version installed:

```bash
# Check nockchain-wallet version
nockchain-wallet --version

# View available commands
nockchain-wallet --help
```

For more information about Nockchain, visit the [official repository](https://github.com/zorp-corp/nockchain).

## Development

### Setting Up Development Environment

```bash
# Install with development dependencies
pip install -r requirements.txt

# Run with debug mode
python app.py
```

### Running Tests

```bash
pytest
```

### Code Style

This project follows PEP 8 guidelines. Format your code with:

```bash
black app.py cli_integration.py
```

## Security Considerations

1. **Private Keys**: Never share your private key or seed phrase
2. **Local Node**: For security, keep your Nockchain node running locally
3. **HTTPS**: In production, always use HTTPS for the web interface
4. **Secret Key**: Change the `SECRET_KEY` in production
5. **Backup**: Regularly backup your wallet files located in `~/.nockchain-wallet/`

## Troubleshooting

### "nockchain-wallet not found"
Make sure nockchain-wallet is installed and in your PATH:
```bash
which nockchain-wallet
```

### "Cannot connect to node"
Ensure your Nockchain node is running:
```bash
# Start the Nockchain node
nockchain-node
```

### "Transaction failed"
- Verify recipient address is valid
- Check that you have sufficient balance for the transaction + fee
- Ensure the node is fully synced

## Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is open source and available under the MIT License. See the LICENSE file for details.

## Support

For issues, questions, or suggestions:

1. Check the [Nockchain documentation](https://github.com/zorp-corp/nockchain)
2. Open an issue on [GitHub Issues](https://github.com/zorp-corp/knox-wallet-nock/issues)
3. Join the Nockchain community

## Credits

- Built with ❤️ for the Nockchain community
- UI inspired by modern wallet applications
- Built with Flask and vanilla JavaScript

---

**KNOX** - Making Nockchain accessible to everyone 🚀
