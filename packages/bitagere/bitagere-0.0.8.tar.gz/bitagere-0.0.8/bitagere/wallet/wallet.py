# Placeholder for wallet management (storing/loading keypairs, etc.)
import getpass  # For securely getting passphrase
import json
import logging
import os

from .keypair import Keypair

# Default wallet directory, can be overridden by Wallet instance
DEFAULT_WALLET_DIR = os.path.expanduser("~/.bitagere/wallets")
WALLET_DIR = DEFAULT_WALLET_DIR

logger = logging.getLogger(__name__)


class Wallet:
    def __init__(
        self, name: str, keypair: Keypair | None = None, wallet_dir: str | None = None
    ):
        self.name = name
        self.wallet_dir = wallet_dir if wallet_dir else DEFAULT_WALLET_DIR
        self.path = os.path.join(self.wallet_dir, f"{name}.json")
        self.keypair = keypair  # This keypair might be unlocked or locked (if loaded from encrypted JSON)

    def save(self, passphrase: str, overwrite: bool = False) -> bool:
        """Saves the wallet (keypair) to an encrypted JSON file."""
        if not self.keypair:
            logger.warning("Wallet '%s': no keypair to save.", self.name)
            return False

        # Ensure wallet_dir exists
        os.makedirs(self.wallet_dir, exist_ok=True)

        if os.path.exists(self.path) and not overwrite:
            logger.warning(
                "Wallet '%s': file %s already exists. Use overwrite=True to replace.",
                self.name,
                self.path,
            )
            return (
                False  # Signal that save failed due to existing file and no overwrite
            )

        try:
            encrypted_data = self.keypair.export_to_encrypted_json(
                passphrase, name=self.name
            )
            with open(self.path, "w") as f:
                json.dump(encrypted_data, f, indent=4)
            logger.info(
                "Wallet '%s': saved encrypted wallet to %s.", self.name, self.path
            )
            return True
        except Exception as e:
            logger.error(
                "Wallet '%s': error saving wallet to %s: %s",
                self.name,
                self.path,
                e,
                exc_info=True,
            )
            return False

    @classmethod
    def load(
        cls, name: str, passphrase: str | None, wallet_dir: str | None = None
    ) -> "Wallet | None":
        """Loads a wallet from an encrypted JSON file.

        If ``passphrase`` is ``None`` the user will be prompted via ``getpass``.
        """
        current_wallet_dir = wallet_dir if wallet_dir else DEFAULT_WALLET_DIR
        path = os.path.join(current_wallet_dir, f"{name}.json")
        if not os.path.exists(path):
            logger.warning("Wallet '%s': file %s not found.", name, path)
            return None
        try:
            with open(path, "r") as f:
                encrypted_data = json.load(f)

            effective_passphrase = passphrase
            if effective_passphrase is None:
                effective_passphrase = getpass.getpass(
                    f"Enter passphrase to decrypt wallet '{name}': "
                )

            keypair = Keypair.create_from_encrypted_json(
                encrypted_data, effective_passphrase
            )
            logger.info(
                "Wallet '%s': loaded and decrypted wallet from %s.", name, path
            )
            # Pass wallet_dir to the constructor if it was provided to load
            return cls(name=name, keypair=keypair, wallet_dir=wallet_dir)
        except Exception as e:
            # Catching specific exceptions like incorrect passphrase might be useful here
            logger.error(
                "Wallet '%s': error loading from %s. Check passphrase or file integrity. %s",
                name,
                path,
                e,
                exc_info=True,
            )
            return None

    @classmethod
    def create_new_wallet(
        cls, name: str, overwrite: bool = False, wallet_dir: str | None = None
    ) -> tuple["Wallet | None", str | None]:
        """Creates a new wallet, prompts for passphrase, saves it encrypted, and returns the wallet and mnemonic."""
        current_wallet_dir = wallet_dir if wallet_dir else DEFAULT_WALLET_DIR
        wallet_path = os.path.join(current_wallet_dir, f"{name}.json")

        if os.path.exists(wallet_path) and not overwrite:
            # print(f"Wallet: Wallet with name '{name}' already exists in {current_wallet_dir}. Use --overwrite to replace it.")
            # The CLI test for no-overwrite expects the command to handle this.
            # Return (None, None) to signal this specific failure (already exists, no overwrite).
            return None, None

        # if os.path.exists(wallet_path) and overwrite:
        # print(f"Wallet: Overwriting existing wallet '{name}' in {current_wallet_dir}.")

        try:
            keypair = Keypair.generate()  # Generates KP and mnemonic
            mnemonic = keypair.mnemonic

            if not mnemonic:
                logger.error("Wallet '%s': mnemonic generation failed.", name)
                return None, None

            passphrase = getpass.getpass(
                f"Enter passphrase to encrypt wallet '{name}': "
            )
            passphrase_confirm = getpass.getpass("Confirm passphrase: ")

            if passphrase != passphrase_confirm:
                logger.error(
                    "Wallet '%s': passphrases do not match. Wallet not saved.", name
                )
                return None, mnemonic

            wallet = cls(name=name, keypair=keypair, wallet_dir=wallet_dir)
            if not wallet.save(passphrase, overwrite=overwrite):
                logger.error(
                    "Wallet '%s': failed to save new wallet to %s.",
                    name,
                    wallet.path,
                )
                return None, mnemonic

            logger.info(
                "Wallet '%s': created new wallet at %s.", name, wallet.path
            )
            return wallet, mnemonic

        except Exception as e:
            logger.error(
                "Wallet '%s': unexpected error during creation: %s",
                name,
                e,
                exc_info=True,
            )
            return None, None

    @classmethod
    def wallet_exists(cls, name: str, wallet_dir: str | None = None) -> bool:
        """Checks if a wallet file with the given name exists."""
        current_wallet_dir = wallet_dir if wallet_dir else DEFAULT_WALLET_DIR
        wallet_path = os.path.join(current_wallet_dir, f"{name}.json")
        return os.path.exists(wallet_path)

    @classmethod
    def list_wallets(cls, wallet_dir: str | None = None) -> list[str]:
        """Lists all saved wallet names."""
        current_wallet_dir = wallet_dir if wallet_dir else DEFAULT_WALLET_DIR
        if not os.path.exists(current_wallet_dir):
            return []
        return [
            f.replace(".json", "")
            for f in os.listdir(current_wallet_dir)
            if f.endswith(".json")
        ]

    @classmethod
    def import_wallet_from_mnemonic(
        cls,
        name: str,
        mnemonic: str,
        overwrite: bool = False,
        wallet_dir: str | None = None,
    ) -> "Wallet | None":
        """Imports a wallet from a mnemonic string, prompts for passphrase, and saves it encrypted."""
        current_wallet_dir = wallet_dir if wallet_dir else DEFAULT_WALLET_DIR
        if not overwrite and os.path.exists(
            os.path.join(current_wallet_dir, f"{name}.json")
        ):
            logger.warning(
                "Wallet '%s': already exists in %s. Use overwrite=True to replace.",
                name,
                current_wallet_dir,
            )
            return None
        try:
            keypair = Keypair.create_from_mnemonic(mnemonic)

            passphrase = getpass.getpass(
                f"Enter passphrase to encrypt imported wallet '{name}': "
            )
            passphrase_confirm = getpass.getpass("Confirm passphrase: ")

            if passphrase != passphrase_confirm:
                logger.error(
                    "Wallet '%s': passphrases do not match. Wallet not saved.", name
                )
                return None

            wallet = cls(
                name=name, keypair=keypair, wallet_dir=wallet_dir
            )  # Pass wallet_dir
            if wallet.save(passphrase, overwrite=overwrite):
                logger.info(
                    "Wallet '%s': imported wallet with address %s into %s.",
                    name,
                    keypair.ss58_address,
                    wallet.wallet_dir,
                )
                return wallet
            else:
                logger.error("Wallet '%s': failed to save imported wallet.", name)
                return None
        except Exception as e:
            logger.error(
                "Wallet '%s': error importing from mnemonic: %s",
                name,
                e,
                exc_info=True,
            )
            return None

    def get_address(self) -> str | None:
        """Returns the SS58 address of the wallet's keypair."""
        if self.keypair:
            return self.keypair.ss58_address
        return None

    def get_public_key(self) -> str | None:
        """Returns the public key (hex) of the wallet's keypair."""
        if self.keypair and self.keypair.public_key:
            return self.keypair.public_key.hex()
        return None

    def get_mnemonic(self) -> str | None:
        """
        Returns the mnemonic of the wallet's keypair, IF it was just generated or imported
        and not yet reloaded from an encrypted store (as mnemonics are not stored in encrypted JSON).
        """
        if self.keypair and hasattr(self.keypair, "mnemonic") and self.keypair.mnemonic:
            return self.keypair.mnemonic
        # print(f"Wallet: Mnemonic not available for wallet '{self.name}'. It might have been loaded from encrypted store or created from seed.")
        return None

    def unlock_keypair(self, passphrase: str) -> bool:
        """
        Attempts to unlock the keypair if it was loaded from an encrypted JSON.
        This typically means re-creating the substrate keypair object with the passphrase.
        This method is more conceptual for this structure, as `load` already requires the passphrase.
        If a keypair is needed for signing, and it was loaded, it should already be unlocked.
        However, if we want to re-verify a passphrase or if the keypair was somehow stored "locked",
        this could be implemented.

        For now, this method assumes that if self.keypair exists and was loaded via `Wallet.load`,
        it's already effectively "unlocked" for use by `self.keypair.sign()`.
        If the keypair was from `create_from_encrypted_json`, it's ready.
        If it was from `generate` or `create_from_mnemonic`, it's also ready.
        The `substrateinterface.Keypair` itself handles the decryption internally when created
        from encrypted JSON with a passphrase.
        """
        if not self.keypair:
            logger.warning("Wallet '%s': no keypair to unlock.", self.name)
            return False

        # Attempt to re-create/validate by trying to access a sensitive operation or re-load
        # This is a bit of a conceptual placeholder. The actual unlocking happens in Keypair.create_from_encrypted_json
        # or when SubstrateKeypair.sign is called on a keypair derived from encrypted JSON.
        # We can try to re-export and see if it works, as a way to validate passphrase.
        try:
            # This is not a true unlock, but a validation.
            # A true unlock would involve re-instantiating the keypair if it were held in a locked state.
            self.keypair.export_to_encrypted_json(
                passphrase, name=self.name
            )  # Try a sensitive operation
            logger.info(
                "Wallet '%s': passphrase validation succeeded.", self.name
            )
            return True
        except Exception as e:
            logger.error(
                "Wallet '%s': passphrase incorrect or validation failed: %s",
                self.name,
                e,
            )
            return False

# Additional wallet management utilities can be added below.
