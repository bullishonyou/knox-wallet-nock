from flask import Flask, render_template, request, jsonify, session
from cli_integration import NockchainWalletCLI, NockchainCLIError, nicks_to_nock, nock_to_nicks, parse_list_active_addresses
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


@app.route("/transactions")
def transactions():
    """View transactions page."""
    return render_template("transactions.html")


@app.route("/api/transactions")
def api_transactions():
    """Get all transactions (notes) for the active wallet."""
    try:
        # Get active address using list-active-addresses
        try:
            active_addresses_output = cli._run_command("list-active-addresses")
            active_data = parse_list_active_addresses(active_addresses_output)
            active_address = active_data.get("address", "")
        except:
            # Fallback to list-master-addresses
            addresses_data = cli.list_master_addresses()
            active_address = addresses_data.get("active_address", "")
        
        if not active_address:
            return jsonify({
                "success": False,
                "error": "No active wallet found"
            }), 400
        
        # Get notes for the active address only
        notes_data = cli.list_notes_by_address(active_address)
        
        return jsonify({
            "success": True,
            "address": active_address,
            "total_balance_nock": notes_data.get("total_balance_nock", 0),
            "total_balance_nicks": notes_data.get("total_balance_nicks", 0),
            "notes": notes_data.get("notes", [])
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
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
    """Get active wallet address and balance using show-balance."""
    try:
        # Get active address first
        addresses_data = cli.list_master_addresses()
        active_address = addresses_data.get("active_address", "")
        
        if not active_address:
            return jsonify({
                "success": False,
                "error": "No active wallet found"
            }), 400
        
        # Get balance from show-balance command
        balance_info = cli.show_balance()
        
        return jsonify({
            "success": True,
            "address": active_address,
            "balance_nock": balance_info.get("balance_nock", 0),
            "balance_nicks": balance_info.get("balance_nicks", 0),
            "block_height": balance_info.get("block_height", ""),
            "num_notes": balance_info.get("num_notes", 0),
            "version": balance_info.get("version", "")
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/refresh-balance", methods=["POST"])
def api_refresh_balance():
    """Refresh the balance for the active wallet."""
    try:
        active_address = cli.get_active_master_address()
        if not active_address:
            return jsonify({
                "success": False,
                "error": "No active wallet found to refresh balance."
            }), 400

        # Get fresh balance from show-balance
        balance_info = cli.show_balance()

        return jsonify({
            "success": True,
            "address": active_address,
            "balance_nock": balance_info.get("balance_nock", 0),
            "balance_nicks": balance_info.get("balance_nicks", 0),
            "block_height": balance_info.get("block_height", ""),
            "num_notes": balance_info.get("num_notes", 0)
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
