from flask import Flask, render_template, request, jsonify, session
from cli_integration import NockchainWalletCLI, NockchainCLIError, nicks_to_nock, nock_to_nicks, parse_balance_csv
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

# Initialize CLI wrapper
cli = NockchainWalletCLI()


@app.route("/")
def index():
    """Home page / Dashboard."""
    try:
        status = cli.get_status()
        context = {
            "node_connected": status["connected"],
            "error": status.get("error"),
            "addresses": status.get("master_addresses", [])
        }
        return render_template("dashboard.html", **context)
    except Exception as e:
        return render_template("dashboard.html", node_connected=False, error=str(e))


@app.route("/api/status")
def api_status():
    """Get wallet and node status."""
    try:
        status = cli.get_status()
        return jsonify({
            "success": True,
            "connected": status["connected"],
            "addresses": status.get("master_addresses", []),
            "error": status.get("error")
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "connected": False
        }), 500


@app.route("/create-wallet")
def create_wallet():
    """Create wallet page."""
    return render_template("create_wallet.html")


@app.route("/api/create-wallet", methods=["POST"])
def api_create_wallet():
    """API endpoint to create a new wallet."""
    try:
        result = cli.generate_keypair()
        return jsonify({
            "success": True,
            "message": "New wallet created!",
            "data": result
        })
    except NockchainCLIError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }), 500


@app.route("/import-wallet")
def import_wallet():
    """Import wallet page."""
    return render_template("import_wallet.html")


@app.route("/api/import-wallet", methods=["POST"])
def api_import_wallet():
    """API endpoint to import a wallet."""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        seed_phrase = data.get("seed_phrase")
        key_file = data.get("key_file")
        version = data.get("version", "1")  # Default to version 1

        if not seed_phrase and not key_file:
            return jsonify({
                "success": False,
                "error": "Please provide either a seed phrase or key file"
            }), 400

        # Validate version - only 0 or 1 allowed
        if version not in ["0", "1", 0, 1]:
            return jsonify({
                "success": False,
                "error": "Invalid version. Version must be 0 or 1."
            }), 400

        result = cli.import_keys(seed_phrase=seed_phrase, key_file=key_file, version=str(version))

        return jsonify({
            "success": result.get("success", True),
            "message": result.get("message", "Wallet imported successfully!"),
            "address": result.get("address", ""),
            "data": result.get("data", {})
        })
    except NockchainCLIError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }), 500


@app.route("/balance")
def balance():
    """View balance page."""
    return render_template("balance.html")


@app.route("/api/balance/<pubkey>")
def api_balance(pubkey):
    """Get balance for a public key from the CSV file, or fetch it if it doesn't exist."""
    try:
        # Parse balance from CSV files
        balance_data = parse_balance_csv(pubkey)
        
        # If no balance data found, try to fetch it from the node
        if balance_data.get("total_balance_nicks", 0) == 0 and not balance_data.get("transactions"):
            try:
                # Fetch latest notes from the node
                cli.list_notes_by_pubkey_csv(pubkey)
                # Parse the newly saved CSV
                balance_data = parse_balance_csv(pubkey)
            except Exception:
                # If fetch fails, just return the empty balance_data
                pass
        
        return jsonify({
            "success": True,
            "pubkey": pubkey,
            "total_balance_nicks": balance_data.get("total_balance_nicks", 0),
            "total_balance_nock": balance_data.get("total_balance_nock", 0),
            "transactions": balance_data.get("transactions", [])
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }), 500


@app.route("/send")
def send():
    """Send transaction page."""
    try:
        addresses = cli.list_active_addresses()
        return render_template("send_transaction.html", addresses=addresses)
    except Exception as e:
        return render_template("send_transaction.html", addresses=[], error=str(e))


@app.route("/manage-wallets")
def manage_wallets():
    """Manage wallets page."""
    return render_template("manage_wallets.html")


@app.route("/api/send-transaction", methods=["POST"])
def api_send_transaction():
    """API endpoint to send a transaction."""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        sender = data.get("sender")
        recipient = data.get("recipient")
        amount_nock = data.get("amount")
        fee_nock = data.get("fee", 0.00001)  # Default small fee

        if not all([sender, recipient, amount_nock]):
            return jsonify({
                "success": False,
                "error": "Missing required fields: sender, recipient, amount"
            }), 400

        # Validate addresses
        if not isinstance(sender, str) or len(sender) < 10:
            return jsonify({"success": False, "error": "Invalid sender address"}), 400

        if not isinstance(recipient, str) or len(recipient) < 10:
            return jsonify({"success": False, "error": "Invalid recipient address"}), 400

        try:
            amount_nicks = nock_to_nicks(float(amount_nock))
            fee_nicks = nock_to_nicks(float(fee_nock))
        except ValueError:
            return jsonify({
                "success": False,
                "error": "Invalid amount or fee format"
            }), 400

        # Create transaction
        tx_result = cli.create_transaction(
            pubkey=sender,
            recipient=recipient,
            amount=amount_nicks,
            fee=fee_nicks
        )

        # Send transaction
        send_result = cli.send_transaction(tx_result)

        return jsonify({
            "success": True,
            "message": "Transaction sent successfully!",
            "data": send_result
        })
    except NockchainCLIError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }), 500


@app.route("/api/addresses")
def api_addresses():
    """Get list of active addresses."""
    try:
        addresses = cli.list_active_addresses()
        return jsonify({
            "success": True,
            "addresses": addresses
        })
    except NockchainCLIError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400


@app.route("/api/active-wallet")
def api_active_wallet():
    """Get active wallet address and balance."""
    try:
        addresses_data = cli.list_master_addresses()
        active_address = addresses_data.get("active_address", "")
        
        if not active_address:
            return jsonify({
                "success": False,
                "error": "No active wallet found"
            }), 400
        
        # Find the active wallet version
        active_version = "1"  # default
        for wallet in addresses_data.get("addresses", []):
            if wallet["address"] == active_address:
                active_version = wallet["version"]
                break
        
        # Check if we can query balance (only v0 addresses support balance queries)
        if active_version == "1":
            return jsonify({
                "success": True,
                "address": active_address,
                "balance_nock": 0,
                "balance_nicks": 0,
                "warning": "Balance queries only work for v0 addresses. This is a v1 address."
            })
        
        # Parse balance from CSV files for v0 addresses
        balance_data = parse_balance_csv(active_address)
        
        return jsonify({
            "success": True,
            "address": active_address,
            "balance_nock": balance_data.get("total_balance_nock", 0),
            "balance_nicks": balance_data.get("total_balance_nicks", 0)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/refresh-balance", methods=["POST"])
def api_refresh_balance():
    """Refresh the balance for the active wallet by fetching new data from the node."""
    try:
        active_address = cli.get_active_master_address()
        if not active_address:
            return jsonify({
                "success": False,
                "error": "No active wallet found to refresh balance."
            }), 400

        # Fetch latest notes from the node
        cli.list_notes_by_pubkey_csv(active_address)
        
        # Parse the newly saved CSV
        balance_data = parse_balance_csv(active_address)

        return jsonify({
            "success": True,
            "address": active_address,
            "balance_nock": balance_data.get("total_balance_nock", 0),
            "balance_nicks": balance_data.get("total_balance_nicks", 0),
            "transactions": balance_data.get("transactions", [])
        })
    except NockchainCLIError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }), 500


@app.route("/api/wallets")
def api_wallets():
    """Get list of all wallets."""
    try:
        addresses_data = cli.list_master_addresses()
        return jsonify({
            "success": True,
            "active_address": addresses_data.get("active_address", ""),
            "wallets": addresses_data.get("addresses", [])
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/set-active-wallet", methods=["POST"])
def api_set_active_wallet():
    """Set the active wallet address."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        address = data.get("address")
        
        if not address:
            return jsonify({
                "success": False,
                "error": "Address is required"
            }), 400
        
        # Set the active wallet
        cli.set_active_master_address(address)
        
        return jsonify({
            "success": True,
            "message": "Active wallet updated successfully!",
            "address": address
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors."""
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors."""
    return jsonify({"error": "Server error"}), 500


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
