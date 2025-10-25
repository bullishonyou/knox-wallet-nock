import subprocess
import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any


class NockchainCLIError(Exception):
    """Custom exception for nockchain-wallet CLI errors."""
    pass


def strip_ansi_codes(text: str) -> str:
    """
    Remove ANSI color codes from text.

    Args:
        text: Text with ANSI codes

    Returns:
        Clean text without ANSI codes
    """
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)


def parse_keygen_output(output: str) -> Dict[str, str]:
    """
    Parse nockchain-wallet keygen output and extract wallet information.

    Args:
        output: Raw output from keygen command

    Returns:
        Dictionary with wallet information
    """
    # Strip ANSI codes
    clean_output = strip_ansi_codes(output)

    # Initialize result dictionary
    result = {
        "address": "",
        "private_key": "",
        "public_key": "",
        "seed_phrase": "",
        "version": "",
        "raw_output": clean_output
    }

    # Split by lines
    lines = clean_output.split('\n')

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Skip empty lines and log lines
        if not line or line.startswith("I ") or line.startswith("["):
            i += 1
            continue

        # Parse Address - look for standalone "Address" header
        if line == "Address":
            # Next non-empty line should be the address
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines):
                result["address"] = lines[j].strip()
            i = j
            continue

        # Parse Extended Private Key
        if "Extended Private Key" in line:
            j = i + 1
            private_key_lines = []
            while j < len(lines):
                next_line = lines[j].strip()
                if not next_line or "Extended Public Key" in lines[j]:
                    break
                private_key_lines.append(next_line)
                j += 1
            result["private_key"] = "".join(private_key_lines)
            i = j
            continue

        # Parse Extended Public Key
        if "Extended Public Key" in line:
            j = i + 1
            public_key_lines = []
            while j < len(lines):
                next_line = lines[j].strip()
                if not next_line or "Seed Phrase" in lines[j]:
                    break
                public_key_lines.append(next_line)
                j += 1
            result["public_key"] = "".join(public_key_lines)
            i = j
            continue

        # Parse Seed Phrase
        if "Seed Phrase" in line:
            j = i + 1
            seed_lines = []
            while j < len(lines):
                next_line = lines[j].strip()
                if not next_line or "Version" in lines[j]:
                    break
                # Remove quotes if present
                next_line = next_line.strip("'\"")
                seed_lines.append(next_line)
                j += 1
            result["seed_phrase"] = " ".join(seed_lines)
            i = j
            continue

        # Parse Version (look for "Version" with following line having the number)
        if line.startswith("Version"):
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines):
                version_line = lines[j].strip()
                # Version could be on the same line or next line
                if version_line and version_line[0].isdigit():
                    result["version"] = version_line
            i = j
            continue

        i += 1

    return result


def parse_import_output(output: str) -> Dict[str, str]:
    """
    Parse nockchain-wallet import output and extract wallet information.
    
    New format (after import):
    Master Key (Imported)
    - Address: [ADDRESS]
    - Version: [VERSION]

    Args:
        output: Raw output from import-keys command

    Returns:
        Dictionary with wallet information (address, version)
    """
    # Strip ANSI codes
    clean_output = strip_ansi_codes(output)

    # Initialize result dictionary
    result = {
        "address": "",
        "version": "",
        "raw_output": clean_output
    }

    # Split by lines
    lines = clean_output.split('\n')

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Skip empty lines and log lines
        if not line or line.startswith("I ") or line.startswith("["):
            i += 1
            continue

        # Skip header lines
        if "Master Key (Imported)" in line or "Master Key" in line:
            i += 1
            continue

        # Extract Address
        if line.startswith("- Address:"):
            address = line.split("- Address:", 1)[1].strip()
            if address:
                result["address"] = address

        # Extract Version
        elif line.startswith("- Version:"):
            version = line.split("- Version:", 1)[1].strip()
            if version and version.isdigit():
                result["version"] = version

        i += 1

    return result


def parse_show_master_pubkey_output(output: str) -> Dict[str, str]:
    """
    Parse nockchain-wallet show-master-pubkey output and extract address.
    
    Format:
    - Extended Public Key: zpub... (save for import)
    - Corresponding Address: BLFpYjKk...
    - Version: 1

    Args:
        output: Raw output from show-master-pubkey command

    Returns:
        Dictionary with address and version
    """
    # Strip ANSI codes
    clean_output = strip_ansi_codes(output)

    result = {
        "address": "",
        "extended_public_key": "",
        "version": ""
    }

    lines = clean_output.split('\n')

    for line in lines:
        line = line.strip()

        # Extract Extended Public Key
        if line.startswith("- Extended Public Key:"):
            key = line.replace("- Extended Public Key:", "").strip()
            # Remove "(save for import)" if present
            key = key.replace("(save for import)", "").strip()
            if key:
                result["extended_public_key"] = key

        # Extract Address (format: "- Corresponding Address: BLFp...")
        elif line.startswith("- Corresponding Address:"):
            address = line.replace("- Corresponding Address:", "").strip()
            if address:
                result["address"] = address

        # Extract Version
        elif line.startswith("- Version:"):
            version = line.replace("- Version:", "").strip()
            if version:
                result["version"] = version

    return result


def parse_list_master_addresses(output: str) -> Dict[str, Any]:
    """
    Parse nockchain-wallet list-master-addresses output.
    
    Returns:
        Dictionary with active address and all addresses with versions
    """
    clean_output = strip_ansi_codes(output)
    
    result = {
        "active_address": "",
        "addresses": []
    }
    
    lines = clean_output.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Extract Address
        if line.startswith("- Address:"):
            address_part = line.split("- Address:", 1)[1].strip()
            
            # Collect multi-line addresses
            # If address is empty on first line, collect from next lines
            if not address_part:
                j = i + 1
                address_lines = []
                active_marker_found = False
                
                while j < len(lines):
                    next_line = lines[j].strip()
                    
                    # Stop at version line or separator
                    if next_line.startswith("- Version:") or next_line.startswith("―"):
                        break
                    
                    # Stop at next address
                    if next_line.startswith("- Address:"):
                        break
                    
                    # Check for "(active)" marker on its own line
                    if next_line == "(active)":
                        active_marker_found = True
                        break
                    
                    # Stop at empty lines followed by separator
                    if not next_line:
                        # Check if next non-empty line is a version or separator
                        k = j + 1
                        while k < len(lines) and not lines[k].strip():
                            k += 1
                        if k < len(lines):
                            peek_line = lines[k].strip()
                            if peek_line.startswith("- Version:") or peek_line.startswith("―"):
                                break
                        j += 1
                        continue
                    
                    # Add line to address (this line contains the address part)
                    address_lines.append(next_line)
                    j += 1
                
                address_part = "".join(address_lines)
                
                # If we found (active) marker on separate line, mark it
                if active_marker_found:
                    is_active = True
                else:
                    is_active = False
            else:
                # Check if address is on same line as marker
                is_active = "(active)" in address_part
            
            # Clean the address by removing (active) marker
            address = address_part.replace("(active)", "").strip()
            
            # Also check if the next line is just "(active)" for single-line addresses
            if not is_active and address_part and i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line == "(active)":
                    is_active = True
            
            # Look for version on next non-empty lines (skip separator lines)
            version = "1"  # default
            j = i + 1
            while j < len(lines):
                next_line = lines[j].strip()
                
                # Skip separator lines (em dashes or many dashes)
                if next_line.startswith("―") or (next_line.startswith("-") and not next_line.startswith("- ")):
                    j += 1
                    continue
                
                # Skip empty lines
                if not next_line:
                    j += 1
                    continue
                
                # Found version line
                if next_line.startswith("- Version:"):
                    version = next_line.split("- Version:", 1)[1].strip()
                    break
                
                # If we hit another address or section, stop looking
                if next_line.startswith("- Address:") or next_line.startswith("Master"):
                    break
                
                j += 1
            
            # Only add if we have an address
            if address:
                result["addresses"].append({
                    "address": address,
                    "version": version,
                    "is_active": is_active
                })
                
                if is_active:
                    result["active_address"] = address
        
        i += 1
    
    return result


def parse_list_active_addresses(output: str) -> Dict[str, str]:
    """
    Parse nockchain-wallet list-active-addresses output to get the active address.
    
    Format:
    Addresses -- Signing
    - Address: [ADDRESS]
    - Version: [VERSION]
    [separator line]
    
    Addresses -- Watch only
    No pubkeys found

    Args:
        output: Raw output from list-active-addresses command

    Returns:
        Dictionary with address, version, and type (Signing or Watch only)
    """
    # Strip ANSI codes
    clean_output = strip_ansi_codes(output)

    # Initialize result dictionary
    result = {
        "address": "",
        "version": "",
        "type": "",
        "raw_output": clean_output
    }

    # Split by lines
    lines = clean_output.split('\n')

    current_type = ""
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Skip empty lines and log lines
        if not line or line.startswith("I ") or line.startswith("[") or line.startswith("―"):
            i += 1
            continue

        # Check for section headers
        if "Addresses -- Signing" in line:
            current_type = "Signing"
            i += 1
            continue

        if "Addresses -- Watch only" in line:
            current_type = "Watch only"
            i += 1
            continue

        # Extract Address (only from Signing section)
        if current_type == "Signing" and line.startswith("- Address:"):
            address = line.split("- Address:", 1)[1].strip()
            if address:
                result["address"] = address
                result["type"] = "Signing"

        # Extract Version (only from Signing section)
        elif current_type == "Signing" and line.startswith("- Version:"):
            version = line.split("- Version:", 1)[1].strip()
            if version and version.isdigit():
                result["version"] = version

        i += 1

    return result


def parse_list_notes_by_address(output: str) -> Dict[str, Any]:
    """
    Parse list-notes-by-address output to get transaction notes for a specific address.
    
    Format:
    Wallet Notes for Address 
    [ADDRESS]
    ――――――――――――――――――――――――――
    
    Details
    - Name: [address note_id]
    - Version: [VERSION]
    - Assets: [NICKS]
    - Block Height: [HEIGHT]
    - Source: [SOURCE_ID]
    Lock
    - Required Signatures: 1
    - Signers: [SIGNER_ADDRESS]
    ――――――――――――――――――――――――――

    Args:
        output: Raw output from list-notes-by-address command

    Returns:
        Dictionary with notes list and total balance
    """
    clean_output = strip_ansi_codes(output)
    notes = []
    
    lines = clean_output.split('\n')
    
    current_note = None
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip empty lines, log lines, and separator lines
        if not line or line.startswith("I ") or line.startswith("[") or line.startswith("―"):
            # If we have a current note with all fields, save it
            if current_note and 'source' in current_note:
                notes.append(current_note)
                current_note = None
            i += 1
            continue
        
        # Skip header lines
        if 'Wallet Notes for Address' in line or 'Details' in line or 'Lock' in line or 'Required Signatures' in line or 'Signers' in line:
            i += 1
            continue
        
        # Parse note name
        if line.startswith('- Name:'):
            if current_note and 'source' in current_note:
                notes.append(current_note)
            
            current_note = {}
            # Extract name: "- Name: [address note_id]"
            match = re.search(r'\[(.*?)\]', line)
            if match:
                current_note['name'] = match.group(1)
            i += 1
            continue
        
        # Parse version
        if current_note and line.startswith('- Version:'):
            version_str = line.replace('- Version:', '').strip()
            current_note['version'] = version_str
            i += 1
            continue
        
        # Parse assets
        if current_note and line.startswith('- Assets:'):
            match = re.search(r'(\d+)', line)
            if match:
                assets_nicks = int(match.group(1))
                current_note['assets_nicks'] = assets_nicks
                current_note['assets_nock'] = nicks_to_nock(assets_nicks)
            i += 1
            continue
        
        # Parse block height
        if current_note and line.startswith('- Block Height:'):
            match = re.search(r'(\d+)', line)
            if match:
                current_note['block_height'] = match.group(1)
            i += 1
            continue
        
        # Parse source (transaction ID)
        if current_note and line.startswith('- Source:'):
            source = line.replace('- Source:', '').strip()
            current_note['source'] = source
            i += 1
            continue
        
        i += 1
    
    # Don't forget the last note
    if current_note and 'source' in current_note:
        notes.append(current_note)
    
    # Calculate total balance
    total_nicks = sum(note.get('assets_nicks', 0) for note in notes)
    total_nock = nicks_to_nock(total_nicks)
    
    return {
        "notes": notes,
        "total_balance_nicks": total_nicks,
        "total_balance_nock": total_nock
    }


def parse_list_notes(output: str) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Parse list-notes command output with new format including Version field.
    
    Args:
        output: Raw output from list-notes command
        
    Returns:
        Tuple of (active_address, list of notes)
        Each note contains: name, version, assets, block_height, source
    """
    clean_output = strip_ansi_codes(output)
    notes = []
    current_note = None
    
    lines = clean_output.split('\n')
    
    for line in lines:
        line_stripped = line.strip()
        
        # Skip empty lines and separator lines
        if not line_stripped or line_stripped.startswith('―'):
            if current_note and 'source' in current_note:
                notes.append(current_note)
                current_note = None
            continue
        
        # Skip header lines
        if 'Wallet Notes' in line_stripped or 'Details' in line_stripped or 'Lock' in line_stripped:
            continue
        
        # Parse note name
        if line_stripped.startswith('- Name:'):
            if current_note and 'source' in current_note:
                notes.append(current_note)
            
            current_note = {}
            # Extract name: "- Name: [address note_name]"
            match = re.search(r'\[(.*?)\]', line_stripped)
            if match:
                current_note['name'] = match.group(1)
        
        # Parse version
        elif current_note and line_stripped.startswith('- Version:'):
            version_str = line_stripped.replace('- Version:', '').strip()
            current_note['version'] = version_str
        
        # Parse assets
        elif current_note and line_stripped.startswith('- Assets:'):
            match = re.search(r'(\d+)', line_stripped)
            if match:
                assets_nicks = int(match.group(1))
                current_note['assets_nicks'] = assets_nicks
                current_note['assets_nock'] = nicks_to_nock(assets_nicks)
        
        # Parse block height
        elif current_note and line_stripped.startswith('- Block Height:'):
            match = re.search(r'(\d+)', line_stripped)
            if match:
                current_note['block_height'] = match.group(1)
        
        # Parse source (transaction ID)
        elif current_note and line_stripped.startswith('- Source:'):
            source = line_stripped.replace('- Source:', '').strip()
            current_note['source'] = source
    
    # Don't forget the last note
    if current_note and 'source' in current_note:
        notes.append(current_note)
    
    return notes


def nicks_to_nock(nicks: int) -> float:
    """Convert nicks to NOCK."""
    return nicks / 65536


def nock_to_nicks(nock: float) -> int:
    """Convert NOCK to nicks."""
    return int(nock * 65536)


class NockchainWalletCLI:
    """Wrapper around nockchain-wallet CLI commands."""

    def __init__(self, private_grpc_port: int = 5555, public_grpc_addr: str = "https://nockchain-api.zorp.io"):
        """
        Initialize the CLI wrapper.

        Args:
            private_grpc_port: Port for private gRPC server connection
            public_grpc_addr: Address of public gRPC server
        """
        self.private_grpc_port = private_grpc_port
        self.public_grpc_addr = public_grpc_addr

    def _run_command(self, *args) -> str:
        """
        Run a nockchain-wallet command and return output.

        Args:
            *args: Command arguments to pass to nockchain-wallet

        Returns:
            Command output as string

        Raises:
            NockchainCLIError: If command fails
        """
        cmd = ["nockchain-wallet"] + list(args)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                raise NockchainCLIError(
                    f"Command failed: {' '.join(cmd)}\n"
                    f"Error: {result.stderr}"
                )

            return result.stdout.strip()

        except FileNotFoundError:
            raise NockchainCLIError(
                "nockchain-wallet not found. Please ensure it's installed and in your PATH."
            )
        except subprocess.TimeoutExpired:
            raise NockchainCLIError("Command timed out after 30 seconds.")
        except Exception as e:
            raise NockchainCLIError(f"Unexpected error: {str(e)}")

    def generate_keypair(self) -> Dict[str, str]:
        """
        Generate a new key pair.

        Returns:
            Dictionary with wallet information
        """
        output = self._run_command("keygen")
        # Parse and return structured output
        return parse_keygen_output(output)

    def list_master_addresses(self) -> Dict[str, Any]:
        """
        List all master addresses in the wallet.

        Returns:
            Dictionary with active_address and list of addresses with versions
        """
        output = self._run_command("list-master-addresses")
        return parse_list_master_addresses(output)

    def list_active_addresses(self) -> List[str]:
        """
        List all active addresses under the active master address.

        Returns:
            List of active addresses
        """
        output = self._run_command("list-active-addresses")
        
        # Strip ANSI codes first
        clean_output = strip_ansi_codes(output)
        
        # Parse output to get list of addresses
        # Filter out log lines and empty lines
        addresses = []
        for line in clean_output.split("\n"):
            line = line.strip()
            # Skip empty lines and log lines
            if not line or line.startswith("[") or "kernel:" in line or "nockchain" in line or "I " in line[:3]:
                continue
            addresses.append(line)
        
        return addresses

    def list_notes_by_pubkey(self, pubkey: str) -> str:
        """
        List notes (balance/transactions) for a public key.

        Args:
            pubkey: The public key to query

        Returns:
            Notes information as string
        """
        output = self._run_command("list-notes-by-address", pubkey)
        return output

    def create_transaction(self, pubkey: str, recipient: str, amount: int, fee: int = 1) -> str:
        """
        Create a transaction.

        Args:
            pubkey: Sender's public key
            recipient: Recipient's public key
            amount: Amount in nicks (65536 nicks = 1 NOCK)
            fee: Transaction fee in nicks

        Returns:
            Transaction file path or content
        """
        # This is a placeholder - exact command format depends on nockchain-wallet
        output = self._run_command(
            "create-tx",
            "--from", pubkey,
            "--to", recipient,
            "--amount", str(amount),
            "--fee", str(fee)
        )
        return output

    def send_transaction(self, tx_file: str) -> str:
        """
        Send a transaction.

        Args:
            tx_file: Path to transaction file

        Returns:
            Transaction hash or confirmation
        """
        output = self._run_command("send-tx", tx_file)
        return output

    def show_master_pubkey(self) -> Dict[str, str]:
        """
        Show the master public key.

        Returns:
            Dictionary with master public key and address
        """
        output = self._run_command("show-master-pubkey")
        return parse_show_master_pubkey_output(output)

    def export_master_pubkey(self, output_file: str) -> str:
        """
        Export master public key to a file.

        Args:
            output_file: Path to save the exported key

        Returns:
            Confirmation message
        """
        output = self._run_command("export-master-pubkey", output_file)
        return output

    def import_keys(self, seed_phrase: Optional[str] = None, key_file: Optional[str] = None, version: Optional[str] = None) -> Dict[str, Any]:
        """
        Import keys from seed phrase or file.

        Args:
            seed_phrase: Seed phrase string
            key_file: Path to key file
            version: Version number for seed phrase import (0 or 1)

        Returns:
            Dictionary with import result and wallet info
        
        Raises:
            ValueError: If version is not 0 or 1
        """
        import_result = {
            "success": False,
            "message": "",
            "address": "",
            "version": "",
            "data": {}
        }

        if seed_phrase:
            if not version:
                version = "1"  # Default to version 1
            
            # Validate version - only 0 or 1 allowed
            if version not in ["0", "1", 0, 1]:
                raise ValueError(f"Invalid version '{version}'. Version must be 0 or 1.")
            
            version = str(version)  # Ensure it's a string
            
            # Use --seedphrase flag with proper quoting
            output = self._run_command(
                "import-keys",
                "--seedphrase", seed_phrase,
                "--version", version
            )
            
            # Parse the import output to get address and version
            parsed_data = parse_import_output(output)
            import_result["data"] = parsed_data
            import_result["address"] = parsed_data.get("address", "")
            import_result["version"] = parsed_data.get("version", "")
            import_result["message"] = "Wallet imported successfully!"
            
        elif key_file:
            # Use --file flag for key file imports
            output = self._run_command(
                "import-keys",
                "--file", key_file
            )
            
            # Parse the import output
            parsed_data = parse_import_output(output)
            import_result["data"] = parsed_data
            import_result["message"] = "Wallet imported successfully!"
            
            # For key file imports, the CLI automatically sets it as active
            # So we call list-active-addresses to get the address that was just set
            try:
                active_addresses_output = self._run_command("list-active-addresses")
                active_data = parse_list_active_addresses(active_addresses_output)
                if active_data.get("address"):
                    import_result["address"] = active_data["address"]
                    import_result["version"] = active_data.get("version", "")
            except Exception as e:
                # If we can't get active addresses, use parsed data
                import_result["address"] = parsed_data.get("address", "")
                import_result["version"] = parsed_data.get("version", "")
            
        else:
            raise ValueError("Either seed_phrase or key_file must be provided")

        import_result["success"] = True
        return import_result

    def get_status(self) -> Dict[str, Any]:
        """
        Get wallet and node status.

        Returns:
            Dictionary with status information
        """
        try:
            master_addresses = self.list_master_addresses()
            is_connected = True
            status = {
                "connected": is_connected,
                "master_addresses": master_addresses,
                "error": None
            }
        except NockchainCLIError as e:
            status = {
                "connected": False,
                "master_addresses": [],
                "error": str(e)
            }

        return status

    def get_active_master_address(self) -> str:
        """
        Get the active master address.
        
        Returns:
            The active master address or empty string if none found
        """
        try:
            master_addresses = self.list_master_addresses()
            return master_addresses.get("active_address", "")
        except Exception:
            return ""

    def set_active_master_address(self, address: str) -> str:
        """
        Set the active master address.

        Args:
            address: The address to set as active

        Returns:
            Confirmation message
        """
        output = self._run_command("set-active-master-address", address)
        return output

    def show_balance(self) -> Dict[str, Any]:
        """
        Get wallet balance using show-balance command.
        
        Returns:
            Dictionary with balance info:
            {
                "balance_nicks": int,
                "balance_nock": float,
                "block_height": str,
                "num_notes": int,
                "version": str,
                "block_hash": str
            }
        """
        try:
            output = self._run_command("show-balance")
            clean_output = strip_ansi_codes(output)
            
            result = {
                "balance_nicks": 0,
                "balance_nock": 0.0,
                "block_height": "",
                "num_notes": 0,
                "version": "",
                "block_hash": ""
            }
            
            lines = clean_output.split('\n')
            
            for i, line in enumerate(lines):
                line_stripped = line.strip()
                
                # Parse block height from header line
                if "at height" in line_stripped:
                    # Extract height from "... at height 38.999"
                    match = re.search(r'at height\s+([\d.]+)', line_stripped)
                    if match:
                        result["block_height"] = match.group(1)
                    
                    # Extract block hash
                    match = re.search(r'from block\s+(\S+)\s+at', line_stripped)
                    if match:
                        result["block_hash"] = match.group(1)
                
                # Parse wallet version
                elif "Wallet Version:" in line_stripped:
                    version = line_stripped.replace("- Wallet Version:", "").strip()
                    result["version"] = version
                
                # Parse number of notes
                elif "Number of Notes:" in line_stripped:
                    match = re.search(r'(\d+)', line_stripped)
                    if match:
                        result["num_notes"] = int(match.group(1))
                
                # Parse balance in nicks
                elif "Balance:" in line_stripped:
                    match = re.search(r'(\d+)\s+nicks', line_stripped)
                    if match:
                        balance_nicks = int(match.group(1))
                        result["balance_nicks"] = balance_nicks
                        result["balance_nock"] = nicks_to_nock(balance_nicks)
            
            return result
        except Exception as e:
            raise NockchainCLIError(f"Failed to get balance: {str(e)}")

    def list_notes(self) -> Dict[str, Any]:
        """
        Get all wallet notes with new output format.
        
        Returns:
            Dictionary with:
            {
                "notes": list of note dicts,
                "total_balance_nicks": int,
                "total_balance_nock": float
            }
        """
        try:
            output = self._run_command("list-notes")
            notes = parse_list_notes(output)
            
            # Calculate total balance
            total_nicks = sum(note.get('assets_nicks', 0) for note in notes)
            total_nock = nicks_to_nock(total_nicks)
            
            return {
                "notes": notes,
                "total_balance_nicks": total_nicks,
                "total_balance_nock": total_nock
            }
        except Exception as e:
            raise NockchainCLIError(f"Failed to list notes: {str(e)}")

    def list_notes_by_address(self, address: str) -> Dict[str, Any]:
        """
        Get wallet notes for a specific address.
        
        Args:
            address: The address to get notes for
        
        Returns:
            Dictionary with:
            {
                "notes": list of note dicts,
                "total_balance_nicks": int,
                "total_balance_nock": float
            }
        """
        try:
            output = self._run_command("list-notes-by-address", address)
            return parse_list_notes_by_address(output)
        except Exception as e:
            raise NockchainCLIError(f"Failed to list notes for address: {str(e)}")
