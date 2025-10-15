from substrateinterface import Keypair as SubstrateKeypair, KeypairType
import json


class Keypair:
    def __init__(self, substrate_keypair: SubstrateKeypair, mnemonic: str = None):
        """
        Initializes a Keypair object.

        Args:
            substrate_keypair: The underlying SubstrateKeypair object.
            mnemonic: (Optional) The mnemonic phrase, stored temporarily if the keypair
                      was generated from it. Not persisted in encrypted JSON.
        """
        self._keypair = substrate_keypair
        self.public_key = self._keypair.public_key
        # private_key is not directly stored as an attribute in the same way,
        # as access to it is managed by the SubstrateKeypair object itself,
        # especially when dealing with encrypted keypairs.
        self.ss58_address = self._keypair.ss58_address
        self.mnemonic = mnemonic  # Store temporarily if provided

    @property
    def substrate_kp(self) -> SubstrateKeypair:
        return self._keypair

    @property
    def crypto_type(self):
        """Delegates crypto_type to the underlying SubstrateKeypair."""
        if not self._keypair:
            raise ValueError(
                "Keypair is not properly initialized with a SubstrateKeypair."
            )
        # The underlying SubstrateKeypair should always have crypto_type if properly initialized.
        # If it's missing, an AttributeError will be raised here, pointing to an issue
        # with the SubstrateKeypair instance itself.
        return self._keypair.crypto_type

    def sign(self, message: bytes) -> bytes:
        """
        Signs a message using the keypair's private key.
        The SubstrateKeypair object handles unlocking if it was loaded from encrypted JSON.
        """
        if not self._keypair:
            raise ValueError("Keypair is not initialized.")
        # SubstrateKeypair.sign will handle if private key is available (e.g. after decryption)
        return self._keypair.sign(message)

    @classmethod
    def generate(cls) -> "Keypair":
        """Generates a new SR25519 keypair and its mnemonic."""
        mnemonic = SubstrateKeypair.generate_mnemonic()
        substrate_kp = SubstrateKeypair.create_from_mnemonic(
            mnemonic, crypto_type=KeypairType.SR25519
        )
        return cls(substrate_keypair=substrate_kp, mnemonic=mnemonic)

    @classmethod
    def create_from_mnemonic(cls, mnemonic: str) -> "Keypair":
        """
        Creates a Keypair from a mnemonic phrase.
        The returned Keypair object is not encrypted yet.
        """
        substrate_kp = SubstrateKeypair.create_from_mnemonic(
            mnemonic, crypto_type=KeypairType.SR25519
        )
        return cls(substrate_keypair=substrate_kp, mnemonic=mnemonic)

    @classmethod
    def create_from_seed(cls, seed_hex: str) -> "Keypair":
        """
        Creates a Keypair from a seed hex string.
        The returned Keypair object is not encrypted yet.
        """
        substrate_kp = SubstrateKeypair.create_from_seed(
            seed_hex, crypto_type=KeypairType.SR25519
        )
        # Note: seed_hex itself is not stored as it's less common to recover from than mnemonic
        # and not part of the standard encrypted JSON.
        return cls(substrate_keypair=substrate_kp)

    def export_to_encrypted_json(self, passphrase: str, name: str = None) -> dict:
        """
        Exports the keypair to an encrypted JSON dictionary compatible with PolkadotJS.
        The mnemonic is NOT stored in this encrypted format.
        """
        if not self._keypair:
            raise ValueError("Keypair is not initialized.")

        # Use the ss58_address as the default name if none is provided
        keypair_name = name if name else self.ss58_address

        # The export_to_encrypted_json method of substrateinterface.Keypair
        # returns a dictionary, not a JSON string.
        encrypted_data = self._keypair.export_to_encrypted_json(
            passphrase, name=keypair_name
        )
        return encrypted_data

    @classmethod
    def create_from_encrypted_json(cls, json_data: dict, passphrase: str) -> "Keypair":
        """
        Creates a Keypair from an encrypted JSON dictionary (PolkadotJS format) and a passphrase.
        """
        # The create_from_encrypted_json method of substrateinterface.Keypair
        # expects a dictionary (parsed JSON), not a JSON string.
        # The crypto_type is determined from the JSON file itself.
        substrate_kp = SubstrateKeypair.create_from_encrypted_json(
            json_data, passphrase
        )
        # Mnemonic is not available from encrypted JSON
        return cls(substrate_keypair=substrate_kp, mnemonic=None)
