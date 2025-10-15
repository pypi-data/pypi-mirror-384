import logging  # Added
import ssl
from pathlib import Path  # Added
from typing import Any
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from tenacity import (  # type: ignore
    Retrying,
    RetryError,
    before_sleep_log,
    retry_if_exception_type,
    stop_after_attempt,
    wait_fixed,
)
from substrateinterface import SubstrateInterface as SubstrateLib
from substrateinterface.exceptions import (
    SubstrateRequestException,
    ExtrinsicFailedException,
)
from websocket import WebSocketConnectionClosedException  # type: ignore

from bitagere.wallet.wallet import Wallet
from bitagere.utils.networking import (
    ip_to_int,
    int_to_ip,
    InvalidIPAddressFormat,
)  # Added

# Module-level logger
logger = logging.getLogger("bitagere.interface")

# Default log directory and file
DEFAULT_LOG_DIR = Path.home() / ".bitagere" / "logs"
DEFAULT_LOG_FILE = DEFAULT_LOG_DIR / "interface.log"


class AgereInterface:
    """
    Manages interaction with a Substrate node, including connection handling,
    retries, and submitting signed extrinsics using the bitagere wallet system.
    """

    def __init__(
        self,
        node_url: str = "ws://127.0.0.1:9944",
        max_retries: int = 5,
        retry_delay_seconds: int = 3,
        *,
        ss58_format: int | None = None,
        type_registry_preset: str | None = None,
        type_registry: dict[str, Any] | None = None,
        use_remote_preset: bool = True,
        auto_reconnect: bool = True,
        connection_timeout: int | None = 30,
        websocket_options: dict[str, Any] | None = None,
        ssl_context: ssl.SSLContext | None = None,
        extrinsic_timeout: int = 120,
    ):
        self.node_url = node_url
        self.substrate: SubstrateLib | None = None
        self.max_retries = max_retries
        self.retry_delay_seconds = retry_delay_seconds
        self.ss58_format = ss58_format
        self.type_registry_preset = type_registry_preset
        self.type_registry = type_registry
        self.use_remote_preset = use_remote_preset
        self.auto_reconnect = auto_reconnect
        self.connection_timeout = connection_timeout
        self._user_websocket_options = websocket_options or {}
        self.ssl_context = ssl_context
        self.extrinsic_timeout = extrinsic_timeout
        self._setup_default_logging()  # Added call to setup logging
        # Connection is made lazily or explicitly via connect() or 'with' statement

    def _setup_default_logging(self):  # Added method
        """Sets up default file logging if no handlers are configured for the logger."""
        if not logger.handlers:
            # Set a default level for the logger itself.
            # The application can still override this.
            logger.setLevel(logging.INFO)

            try:
                DEFAULT_LOG_DIR.mkdir(parents=True, exist_ok=True)

                # File Handler
                fh = logging.FileHandler(DEFAULT_LOG_FILE)
                fh.setLevel(logging.INFO)  # Default level for file output
                formatter = logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(module)s.%(funcName)s:%(lineno)d - %(message)s"
                )
                fh.setFormatter(formatter)
                logger.addHandler(fh)
                # logger.info("Default file logging configured to: %s", DEFAULT_LOG_FILE)
            except Exception as e:
                # Fallback to basic console logging if file setup fails
                logging.basicConfig(
                    level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                )
                logger.error(
                    "Failed to set up default file logging for AgereInterface. Falling back to console logging: %s",
                    e,
                    exc_info=True,
                )

    def connect(self) -> bool:
        """
        Establishes a connection to the Substrate node.
        Includes retry logic.
        Returns:
            bool: True if connection is successful, False otherwise.
        """
        if self.substrate:
            try:
                # Quick check if connection is still alive
                # Attempt a lightweight call, e.g., get_chain_head() or get_runtime_version()
                # For now, let's assume if the object exists, we try to proceed,
                # and errors will be caught by actual operations.
                # A more robust check could be self.substrate.get_chain_head()
                # but let's remove the specific problematic call first.
                # self.substrate.get_chain_name() # Removed
                self.substrate.get_chain_head()  # Try a different lightweight call
                # logger.debug("Already connected to %s", self.node_url) # Optional: debug level
                return True
            except (
                WebSocketConnectionClosedException,
                BrokenPipeError,
                ConnectionResetError,
            ):
                logger.warning(
                    "Connection lost, attempting to reconnect.", exc_info=True
                )
                if self.substrate:
                    try:
                        self.substrate.close()
                    except Exception:  # nosec
                        pass
                self.substrate = None
            except Exception as e:
                logger.error(
                    "Unknown error checking existing connection (using get_chain_head): %s",
                    e,
                    exc_info=True,
                )
                if self.substrate:
                    try:
                        self.substrate.close()
                    except Exception:  # nosec
                        pass
                self.substrate = None

        retrying = Retrying(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_fixed(self.retry_delay_seconds),
            retry=retry_if_exception_type(ConnectionError),
            before_sleep=before_sleep_log(logger, logging.DEBUG),
            reraise=True,
        )

        try:
            retrying(self._connect_once)
            logger.info("Successfully connected to %s.", self.node_url)
            return True
        except ssl.SSLCertVerificationError:
            self.substrate = None
            logger.critical(
                "SSL certificate verification failed when connecting to %s.",
                self.node_url,
                exc_info=True,
            )
            if not self.ssl_context:
                logger.info(
                    "Consider providing an ssl_context via AgereInterface(..., ssl_context=...) when working with custom certificates."
                )
            raise
        except RetryError as retry_error:  # Max retries reached
            self.substrate = None
            last_exception = retry_error.last_attempt.exception()
            logger.error(
                "Max retries reached. Failed to connect to %s.",
                self.node_url,
                exc_info=True,
            )
            if last_exception:
                raise ConnectionError(
                    f"Failed to connect to Substrate node at {self.node_url} after {self.max_retries} attempts."
                ) from last_exception
            raise ConnectionError(
                f"Failed to connect to Substrate node at {self.node_url} after {self.max_retries} attempts."
            )

    def _build_ws_options(self) -> dict[str, Any]:
        ws_options = dict(self._user_websocket_options)
        if self.connection_timeout is not None and "timeout" not in ws_options:
            ws_options["timeout"] = self.connection_timeout

        if self.ssl_context is not None:
            current_sslopt = dict(ws_options.get("sslopt", {}))
            current_sslopt.setdefault("ssl_context", self.ssl_context)
            # Mirror SSLContext configuration when possible
            if hasattr(self.ssl_context, "verify_mode"):
                current_sslopt.setdefault("cert_reqs", self.ssl_context.verify_mode)
            if hasattr(self.ssl_context, "check_hostname"):
                current_sslopt.setdefault(
                    "check_hostname", self.ssl_context.check_hostname
                )
            ws_options["sslopt"] = current_sslopt

        return ws_options

    def _build_substrate_kwargs(self) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "url": self.node_url,
            "auto_reconnect": self.auto_reconnect,
            "use_remote_preset": self.use_remote_preset,
        }

        if self.ss58_format is not None:
            kwargs["ss58_format"] = self.ss58_format

        if self.type_registry_preset is not None:
            kwargs["type_registry_preset"] = self.type_registry_preset

        if self.type_registry is not None:
            kwargs["type_registry"] = self.type_registry

        ws_options = self._build_ws_options()
        if ws_options:
            kwargs["ws_options"] = ws_options

        return kwargs

    def _connect_once(self) -> None:
        """Attempt a single connection to the Substrate node."""
        substrate_kwargs = self._build_substrate_kwargs()
        substrate: SubstrateLib | None = None
        try:
            substrate = SubstrateLib(**substrate_kwargs)
            substrate.get_chain_head()
        except ssl.SSLCertVerificationError:
            raise
        except ConnectionError:
            if substrate is not None:
                try:
                    substrate.close()
                except Exception:  # nosec - best effort cleanup
                    pass
            raise
        except Exception as e:
            if substrate is not None:
                try:
                    substrate.close()
                except Exception:  # nosec - best effort cleanup
                    pass
            raise ConnectionError(f"Substrate connection attempt failed: {e}") from e
        else:
            self.substrate = substrate

    def close(self):
        """Closes the connection to the Substrate node."""
        if self.substrate:
            try:
                self.substrate.close()
                logger.info("Connection closed.")
            except Exception as e:
                logger.error("Error while closing connection: %s", e, exc_info=True)
            finally:
                self.substrate = None

    def __enter__(self):
        """Enter context manager, ensures connection."""
        if not self.connect():
            # Log before raising, as the exception might be caught elsewhere
            logger.critical(
                "Failed to connect to Substrate node at %s after multiple retries in __enter__.",
                self.node_url,
            )
            raise ConnectionError(
                f"Failed to connect to Substrate node at {self.node_url} after multiple retries."
            )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager, ensures connection is closed."""
        self.close()

    def is_connected(self) -> bool:
        """Checks if the interface is currently connected."""
        return self.substrate is not None

    def _ensure_connected(self):
        """Ensures there's an active connection, attempting to connect if not."""
        if not self.is_connected():
            if not self.connect():
                logger.error(
                    "Not connected and failed to connect to %s in _ensure_connected.",
                    self.node_url,
                )
                raise ConnectionError(
                    f"AgereInterface: Not connected and failed to connect to {self.node_url}."
                )

    def _substrate_call(self, func_name: str, *args, **kwargs):
        """
        Wrapper for calls to the underlying SubstrateInterface instance.
        Handles automatic reconnection and retries up to max_retries when connection
        level errors (including SSL EOFs) occur.
        """

        retryable_exceptions: tuple[type[BaseException], ...] = (
            WebSocketConnectionClosedException,
            BrokenPipeError,
            ConnectionResetError,
            ssl.SSLError,
        )

        def attempt_call() -> Any:
            try:
                self._ensure_connected()
            except ConnectionError as ensure_error:
                logger.warning(
                    "Failed to ensure connection before '%s': %s",
                    func_name,
                    ensure_error,
                    exc_info=True,
                )
                raise ConnectionError(
                    f"Failed to ensure connection before '{func_name}': {ensure_error}"
                ) from ensure_error

            if not self.substrate:
                msg = "AgereInterface: Substrate object not initialized."
                logger.critical(
                    "Substrate object not initialized in _substrate_call for %s.",
                    func_name,
                )
                raise ConnectionError(msg)

            method_to_call = getattr(self.substrate, func_name)

            try:
                return method_to_call(*args, **kwargs)
            except ssl.SSLCertVerificationError:
                self.close()
                raise
            except retryable_exceptions as err:
                logger.warning(
                    "Connection-level error during '%s': %s",
                    func_name,
                    err,
                    exc_info=True,
                )
                self.close()
                raise ConnectionError(
                    f"Connection-level error during '{func_name}': {err}"
                ) from err
            except (SubstrateRequestException, ExtrinsicFailedException):
                raise
            except Exception as err:
                logger.exception(
                    "Unexpected error during '%s': %s",
                    func_name,
                    err,
                )
                raise

        retrying = Retrying(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_fixed(self.retry_delay_seconds),
            retry=retry_if_exception_type(ConnectionError),
            before_sleep=before_sleep_log(logger, logging.DEBUG),
            reraise=True,
        )

        try:
            return retrying(attempt_call)
        except ssl.SSLCertVerificationError:
            raise
        except RetryError as retry_error:
            last_exception = retry_error.last_attempt.exception()
            error_message = f"AgereInterface: Failed to execute '{func_name}' after {self.max_retries} attempts."
            logger.error(error_message, exc_info=True)
            if last_exception:
                raise ConnectionError(error_message) from last_exception
            raise ConnectionError(error_message)

    def _substrate_call_with_timeout(
        self, func_name: str, timeout: int, *args, **kwargs
    ) -> Any:
        """
        Wrapper for substrate calls that may block indefinitely (like submit_extrinsic).
        Uses ThreadPoolExecutor to enforce a timeout.

        Args:
            func_name: The substrate method name to call
            timeout: Timeout in seconds
            *args, **kwargs: Arguments to pass to the substrate method

        Returns:
            The result from the substrate call

        Raises:
            TimeoutError: If the call exceeds the timeout
            ConnectionError: If connection fails
        """

        def execute_call():
            return self._substrate_call(func_name, *args, **kwargs)

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(execute_call)
            try:
                return future.result(timeout=timeout)
            except FuturesTimeoutError as e:
                logger.error(
                    "Substrate call '%s' timed out after %d seconds",
                    func_name,
                    timeout,
                    exc_info=True,
                )
                # Try to cancel the future, though it may not be effective for blocking I/O
                future.cancel()
                raise TimeoutError(
                    f"Substrate call '{func_name}' timed out after {timeout} seconds"
                ) from e

    def get_chain_info(self) -> dict | None:
        """
        Retrieves basic information about the connected Substrate chain.
        Returns:
            dict | None: A dictionary with chain info, or None on failure.
        """
        try:
            self._ensure_connected()
            if not self.substrate:
                logger.error("Substrate object not initialized in get_chain_info.")
                raise ConnectionError(
                    "AgereInterface: Substrate object not initialized in get_chain_info."
                )

            # Access properties that might trigger init_runtime() if needed
            chain_name = self.substrate.chain
            node_name = self.substrate.name
            node_version = self.substrate.version  # This is node client version

            spec_version = None
            if self.substrate.runtime_config:
                spec_version = self.substrate.runtime_config.active_spec_version_id

            # Get latest block hash using the method call
            latest_block_hash = self._substrate_call("get_chain_head")

            return {
                "chain_name": chain_name,
                "node_name": node_name,
                "node_version": node_version,
                "runtime_spec_version": spec_version,
                "latest_block_hash": latest_block_hash,
            }
        except ConnectionError as e:
            logger.error(
                "Could not get chain info due to connection error: %s", e, exc_info=True
            )
            return None
        except AttributeError as e:
            logger.error("Attribute error getting chain info: %s", e, exc_info=True)
            return None
        except Exception as e:
            logger.exception("Error getting chain info: %s", e)
            return None

    def get_account_balance(
        self, address: str
    ) -> int | None:  # Return type changed to int | None
        """
        Retrieves the 'free' balance for a given SS58 address.
        The user specifically requested only the 'free' balance as an integer.

        Args:
            address: The SS58 address to query.

        Returns:
            int | None: The 'free' balance in the smallest unit, or None on failure.
        """
        try:
            logger.debug("Querying 'free' balance for address: %s", address)
            # self._substrate_call("query", ...) returns a ScaleBytes object from substrateinterface.
            # The actual decoded data is typically in its .value attribute.
            account_info_scale_obj = self._substrate_call(
                "query", module="System", storage_function="Account", params=[address]
            )

            if account_info_scale_obj and hasattr(account_info_scale_obj, "value"):
                account_info_dict = account_info_scale_obj.value
                # Based on user's print and common structure: account_info_dict is like {'data': {'free': ...}}
                if isinstance(account_info_dict, dict) and "data" in account_info_dict:
                    data_dict = account_info_dict["data"]
                    if isinstance(data_dict, dict) and "free" in data_dict:
                        free_balance_value = data_dict["free"]
                        logger.info(
                            "Successfully extracted free balance for %s: %s",
                            address,
                            free_balance_value,
                        )
                        try:
                            return int(free_balance_value)
                        except (ValueError, TypeError) as ve:
                            logger.error(
                                "Could not convert free balance '%s' to int for address %s: %s",
                                free_balance_value,
                                address,
                                ve,
                            )
                            return None
                    else:
                        logger.warning(
                            "Key 'free' not found in data_dict or data_dict is not a dict for %s. data_dict snippet: %s",
                            address,
                            str(data_dict)[:200],
                        )
                else:
                    logger.warning(
                        "'data' key not found in account_info_dict or account_info_dict is not a dict for %s. account_info_dict snippet: %s",
                        address,
                        str(account_info_dict)[:200],
                    )
            else:
                obj_repr_snippet = (
                    str(account_info_scale_obj)[:200]
                    if account_info_scale_obj is not None
                    else "None"
                )
                logger.warning(
                    "account_info_scale_obj is None or has no 'value' attribute for %s. Object snippet: %s",
                    address,
                    obj_repr_snippet,
                )

            return None  # Explicitly return None if extraction fails at any point

        except ConnectionError as e:
            logger.error(
                "Connection error getting balance for %s: %s", address, e, exc_info=True
            )
            return None
        except SubstrateRequestException as e:
            logger.error(
                "Substrate request error getting balance for %s: %s",
                address,
                e,
                exc_info=True,
            )
            return None
        except Exception as e:  # Catch any other unexpected error
            logger.exception(
                "Unexpected error getting 'free' balance for %s: %s", address, e
            )
            return None

    def get_current_block_number(self) -> int | None:
        """
        Retrieves the current block number (height) of the chain.

        Returns:
            int | None: The current block number, or None on failure.
        """
        try:
            logger.debug("Querying current block number...")
            latest_block = self._substrate_call("get_block", block_hash=None)
            if (
                latest_block
                and "header" in latest_block
                and "number" in latest_block["header"]
            ):
                number = latest_block["header"]["number"]
                logger.debug("Current block number: %d", number)
                return int(number)
            logger.warning("Could not determine current block number from get_block().")
            return None
        except ConnectionError as e:
            logger.error(
                "Could not get block number due to connection error: %s",
                e,
                exc_info=True,
            )
            return None
        except Exception as e:
            logger.exception("Error getting current block number: %s", e)
            return None

    def get_block_hash(self, block_number: int | None = None) -> str | None:
        """
        Retrieves the hash of a specific block, or the latest block if no number is provided.

        Args:
            block_number (int | None): The block number to get the hash for.
                                       If None, gets the hash of the latest block.

        Returns:
            str | None: The block hash (hex string), or None on failure.
        """
        try:
            param_name = "block_id"
            if block_number is None:
                logger.debug("Querying latest block hash...")
                b_hash = self._substrate_call("get_block_hash")
            else:
                logger.debug("Querying block hash for block number: %d", block_number)
                b_hash = self._substrate_call(
                    "get_block_hash", **{param_name: block_number}
                )

            if b_hash:
                logger.debug(
                    "Block hash%s: %s",
                    (
                        f" for block {block_number}"
                        if block_number
                        else " for latest block"
                    ),
                    b_hash,
                )
            else:
                logger.warning(
                    "No block hash returned %s.",
                    (
                        f" for block {block_number}"
                        if block_number
                        else " for latest block"
                    ),
                )

            return b_hash
        except ConnectionError as e:
            logger.error(
                "Could not get block hash due to connection error: %s", e, exc_info=True
            )
            return None
        except SubstrateRequestException as e:
            logger.warning(
                "Substrate request error getting block hash: %s", e, exc_info=True
            )  # Warning as it can be a non-existent block
            return None
        except Exception as e:
            logger.exception("Error getting block hash: %s", e)
            return None

    def transfer(
        self,
        wallet_name: str,
        destination_address: str,
        amount: int,  # Amount in the smallest unit (e.g., Planck)
        wait_for_inclusion: bool = True,
        wait_for_finalization: bool = False,
        passphrase: str | None = None,
    ) -> str | None:
        """
        Performs a balance transfer from the specified wallet to a destination address.
        Uses the 'Balances' pallet and 'transfer_keep_alive' call by default.

        Args:
            wallet_name: The name of the wallet to use for signing.
            destination_address: The SS58 address of the recipient.
            amount: The amount to transfer, in the smallest unit of the currency.
            wait_for_inclusion: Wait for the extrinsic to be included in a block.
            wait_for_finalization: Wait for the extrinsic to be finalized.
            passphrase: The passphrase for the wallet. To be passed to submit_signed_extrinsic.

        Returns:
            str | None: The extrinsic hash if successful, or an error message string/None on failure.
        """
        logger.info(
            "Attempting transfer of %d to %s from wallet '%s'.",
            amount,
            destination_address,
            wallet_name,
        )

        # Standard Polkadot/Substrate parameters for transfer
        # Common choices: 'transfer', 'transfer_keep_alive', 'transfer_allow_death'
        # 'transfer_keep_alive' is generally safer as it prevents reaping the sender account if its balance drops below existential deposit.
        module = "Balances"
        call_function = "transfer_keep_alive"

        # The `substrate-interface` library expects the destination address to be in a specific format
        # for some calls. It usually handles SS58 addresses correctly, but if issues arise,
        # one might need to convert it to an AccountId dictionary: {'Id': destination_address}
        # However, for `compose_call` with `transfer_keep_alive`, SS58 string is usually fine.
        params = {
            "dest": destination_address,  # substrate-interface usually expects 'dest' for MultiAddress or AccountId
            "value": amount,
        }

        # For some chains, 'dest' might need to be {'Id': destination_address}
        # For Balances.transfer_keep_alive, it's usually {'dest': {'Id': 'ADDRESS'}, 'value': X}
        # or more simply, the library might handle {'dest': 'ADDRESS', 'value': X}
        # Let's try the simpler version first, as substrate-interface is quite robust.
        # If the node expects a MultiAddress enum, it might be like:
        # params = {
        #     "dest": {'Id': destination_address}, # Forcing AccountId variant of MultiAddress
        #     "value": amount
        # }
        # We will rely on substrate-interface to correctly format `dest` from an SS58 string.

        return self.submit_signed_extrinsic(
            wallet_name=wallet_name,
            module=module,
            call_function=call_function,
            params=params,
            wait_for_inclusion=wait_for_inclusion,
            wait_for_finalization=wait_for_finalization,
            passphrase=passphrase,  # Pass it down
        )

    def submit_signed_extrinsic(
        self,
        wallet_name: str,
        module: str,
        call_function: str,
        params: dict,
        wait_for_inclusion: bool = True,
        wait_for_finalization: bool = False,
        passphrase: str | None = None,
    ) -> str | None:
        """
        Constructs, signs, and submits an extrinsic using a specified wallet.
        The wallet passphrase will be prompted for during wallet loading if not provided.

        Args:
            wallet_name: The name of the wallet to use for signing.
            module: The Substrate module (pallet) name.
            call_function: The call/function name within the module.
            params: A dictionary of parameters for the call.
            wait_for_inclusion: Wait for the extrinsic to be included in a block.
            wait_for_finalization: Wait for the extrinsic to be finalized.
            passphrase: The passphrase for the wallet. If None, getpass will be used by Wallet.load().

        Returns:
            str | None: The extrinsic hash if successful, or an error message string/None on failure.
        """
        logger.info(
            "Attempting to submit extrinsic: %s.%s with params %s using wallet '%s'.",
            module,
            call_function,
            params,
            wallet_name,
        )

        bitagere_wallet_instance = None
        try:
            logger.info("Loading wallet '%s'.", wallet_name)
            # Pass the passphrase to Wallet.load. If it's None, Wallet.load will use getpass.
            # This allows tests to supply the passphrase directly, bypassing getpass mock if needed for this specific call.
            bitagere_wallet_instance = Wallet.load(
                name=wallet_name, passphrase=passphrase
            )

            if not bitagere_wallet_instance:
                msg = f"Failed to load wallet '{wallet_name}'. Ensure it exists and passphrase is correct."
                logger.error(msg)
                return msg

            signer_keypair = bitagere_wallet_instance.keypair
            if not signer_keypair:
                msg = (
                    f"Wallet '{wallet_name}' loaded but contains no valid keypair data."
                )
                logger.error(msg)
                return msg
            logger.info(
                "Wallet '%s' loaded successfully. Signer address: %s",
                wallet_name,
                signer_keypair.ss58_address,
            )

        except Exception as e:
            msg = f"Error loading wallet '{wallet_name}': {e}"
            logger.exception(msg)  # Use logger.exception here
            return msg

        try:
            self._ensure_connected()

            logger.info("Composing call %s.%s...", module, call_function)
            composed_call = self._substrate_call(
                "compose_call",
                call_module=module,
                call_function=call_function,
                call_params=params,
            )
            logger.info("Call composed.")

            logger.info("Creating signed extrinsic...")
            extrinsic = self._substrate_call(
                "create_signed_extrinsic", call=composed_call, keypair=signer_keypair
            )
            logger.info("Signed extrinsic created.")

            logger.info(
                "Submitting extrinsic (wait_for_inclusion=%s, wait_for_finalization=%s)...",
                wait_for_inclusion,
                wait_for_finalization,
            )

            # Use timeout wrapper for submit_extrinsic as it can block indefinitely
            receipt = self._substrate_call_with_timeout(
                "submit_extrinsic",
                self.extrinsic_timeout,
                extrinsic,
                wait_for_inclusion=wait_for_inclusion,
                wait_for_finalization=wait_for_finalization,
            )

            if receipt.is_success:
                success_msg = (
                    f"Extrinsic '{receipt.extrinsic_hash}' submitted successfully."
                )
                logger.info(success_msg)
                return receipt.extrinsic_hash
            else:
                error_msg = f"Extrinsic failed: {receipt.error_message if receipt.error_message else 'No error message provided.'}"
                if (
                    hasattr(receipt, "dispatch_error_details")
                    and receipt.dispatch_error_details
                ):
                    error_msg += f" Details: {receipt.dispatch_error_details}"
                elif hasattr(receipt, "dispatch_error") and receipt.dispatch_error:
                    error_msg += f" Dispatch Error: {receipt.dispatch_error}"

                logger.error(error_msg)
                return error_msg

        except ConnectionError as e:
            err = f"Error: Connection failed during extrinsic submission: {e}"
            logger.error(err, exc_info=True)
            return err
        except TimeoutError as e:
            err = f"Error: Extrinsic submission timed out after {self.extrinsic_timeout} seconds: {e}"
            logger.error(err, exc_info=True)
            return err
        except SubstrateRequestException as e:
            err = f"Error: Substrate request failed during extrinsic submission: {e}"
            logger.error(err, exc_info=True)
            return err
        except ExtrinsicFailedException as e:
            err = f"Error: Extrinsic failed: {e}"
            logger.error(
                err, exc_info=True
            )  # ExtrinsicFailedException is specific, good to log with details
            return err
        except Exception as e:
            err = (
                f"Error: An unexpected error occurred during extrinsic submission: {e}"
            )
            logger.exception(err)  # Use logger.exception for unexpected errors
            return err

    # --- New Agere Specific Methods ---

    def serve_axon(
        self,
        wallet_name: str,
        netuid: int,
        version: int,
        ip_str: str,  # IP address as string e.g. "127.0.0.1"
        port: int,
        ip_type: int,  # Automatically determined if not matching ip_str, or can be validated.
        protocol: int,
        placeholder1: int,
        placeholder2: int,
        passphrase: str | None = None,
        wait_for_inclusion: bool = True,
        wait_for_finalization: bool = False,
    ) -> str | None:
        """
        Registers or updates an Axon's serving information on the Agere network.
        The IP address string is converted to an integer before sending.

        Args:
            wallet_name: The name of the wallet to sign this extrinsic.
            netuid: The unique identifier of the subnetwork.
            version: The version of the axon.
            ip_str: The IP address of the axon as a string (e.g., "192.168.1.1").
            port: The port number of the axon.
            ip_type: The type of IP address (e.g., 4 for IPv4, 6 for IPv6).
            protocol: The protocol used by the axon (e.g., 0 for TCP, 1 for UDP).
            placeholder1: Custom placeholder field 1.
            placeholder2: Custom placeholder field 2.
            passphrase: The passphrase for the wallet.
            wait_for_inclusion: Wait for the extrinsic to be included in a block.
            wait_for_finalization: Wait for the extrinsic to be finalized.

        Returns:
            str | None: The extrinsic hash if successful, or an error message string/None on failure.
        """
        logger.info(
            f"Attempting to serve axon for netuid {netuid} using wallet '{wallet_name}'."
        )

        try:
            ip_as_int = ip_to_int(ip_str)
        except InvalidIPAddressFormat as e:
            logger.error(
                f"Invalid IP address format for serve_axon: {ip_str}. Error: {e}"
            )
            return f"Invalid IP address format: {ip_str}"
        # Optional: Validate ip_type against the derived version from ip_str if needed
        # from bitagere.utils.networking import get_ip_version
        # derived_ip_version = get_ip_version(ip_str)
        # if derived_ip_version != ip_type:
        #     logger.warning(f"Provided ip_type {ip_type} does not match derived version {derived_ip_version} for IP {ip_str}")
        # Decide if this is a hard error or just a warning

        params = {
            "netuid": netuid,
            "version": version,
            "ip": ip_as_int,  # Send IP as integer
            "port": port,
            "ip_type": ip_type,
            "protocol": protocol,
            "placeholder1": placeholder1,
            "placeholder2": placeholder2,
        }

        return self.submit_signed_extrinsic(
            wallet_name=wallet_name,
            module="XAgere",
            call_function="serve_axon",
            params=params,
            passphrase=passphrase,
            wait_for_inclusion=wait_for_inclusion,
            wait_for_finalization=wait_for_finalization,
        )

    def set_weights(
        self,
        wallet_name: str,
        netuid: int,
        dests: list[int],  # List of UIDs
        weights: list[int],  # List of weights (typically u16 or similar, passed as int)
        version_key: int,  # Version key for compatibility
        passphrase: str | None = None,
        wait_for_inclusion: bool = True,
        wait_for_finalization: bool = False,
    ) -> str | None:
        """
        Sets the weights for a neuron on the Agere network.

        Args:
            wallet_name: The name of the wallet to sign this extrinsic.
            netuid: The unique identifier of the subnetwork.
            dests: A list of destination neuron UIDs.
            weights: A list of corresponding weights for each destination UID.
            version_key: A version key for the weights.
            passphrase: The passphrase for the wallet.
            wait_for_inclusion: Wait for the extrinsic to be included in a block.
            wait_for_finalization: Wait for the extrinsic to be finalized.

        Returns:
            str | None: The extrinsic hash if successful, or an error message string/None on failure.
        """
        logger.info(
            f"Attempting to set weights for netuid {netuid} using wallet '{wallet_name}'."
        )

        if len(dests) != len(weights):
            msg = "Error: 'dests' and 'weights' lists must have the same length."
            logger.error(msg)
            return msg

        params = {
            "netuid": netuid,
            "dests": dests,
            "weights": weights,
            "version_key": version_key,
        }

        return self.submit_signed_extrinsic(
            wallet_name=wallet_name,
            module="XAgere",  # Assuming pallet name is Agere
            call_function="set_weights",
            params=params,
            passphrase=passphrase,
            wait_for_inclusion=wait_for_inclusion,
            wait_for_finalization=wait_for_finalization,
        )

    def get_axon_info(self, netuid: int, hotkey_ss58: str) -> dict | None:
        """
        Retrieves axon information for a specific hotkey on a given netuid.
        Assumes the RPC node handles decoding and returns a JSON-like dict.

        Args:
            netuid: The unique identifier of the subnetwork.
            hotkey_ss58: The SS58 address of the hotkey for the axon.

        Returns:
            dict | None: A dictionary containing the axon information, or None on failure.
                         The structure of the dict depends on what the node's RPC returns.
        """
        try:
            logger.debug(
                f"Querying axon info for hotkey {hotkey_ss58} on netuid {netuid}."
            )
            # Assuming the storage item is 'Axons' and it's a map (Netuid, Hotkey) -> AxonInfo
            # The exact module and storage_function name might differ based on your pallet.
            axon_info_scale_obj = self._substrate_call(
                "query",
                module="XAgere",  # Assuming pallet name is Agere
                storage_function="Axons",  # Assuming storage name
                params=[netuid, hotkey_ss58],
            )

            if axon_info_scale_obj and hasattr(axon_info_scale_obj, "value"):
                # Assuming the .value directly contains the decoded dict from RPC
                axon_info_dict = axon_info_scale_obj.value
                logger.info(
                    f"Successfully retrieved axon info for hotkey {hotkey_ss58} on netuid {netuid}."
                )
                return axon_info_dict
            else:
                obj_repr_snippet = (
                    str(axon_info_scale_obj)[:200]
                    if axon_info_scale_obj is not None
                    else "None"
                )
                logger.warning(
                    f"Axon info query for hotkey {hotkey_ss58} on netuid {netuid} returned None or no 'value' attribute. Object snippet: {obj_repr_snippet}"
                )
                return None

        except ConnectionError as e:
            logger.error(
                f"Connection error getting axon info for {hotkey_ss58} on netuid {netuid}: {e}",
                exc_info=True,
            )
            return None
        except SubstrateRequestException as e:
            logger.error(
                f"Substrate request error getting axon info for {hotkey_ss58} on netuid {netuid}: {e}",
                exc_info=True,
            )
            return None
        except Exception as e:
            logger.exception(
                f"Unexpected error getting axon info for {hotkey_ss58} on netuid {netuid}: {e}"
            )
            return None

    def get_all_neurons_info(self, netuid: int) -> list[dict] | None:
        """
        Retrieves information for all neurons in a given netuid using a custom RPC call.
        The axon_info.ip field (integer) is converted back to a string IP.

        Args:
            netuid: The unique identifier of the subnetwork.

        Returns:
            list[dict] | None: A list of dictionaries, where each dictionary represents
                               a neuron's information. Axon IP is converted to string.
                               Returns None on failure or if the RPC call fails.
        """
        try:
            logger.debug(
                f"Querying all neurons info for netuid {netuid} via custom RPC."
            )

            # Ensure the substrate object is available and connected
            self._ensure_connected()
            if not self.substrate:
                logger.error(
                    "Substrate object not initialized in get_all_neurons_info."
                )
                return None

            # Make the custom RPC call
            # The method name 'xagere_getNeurons' is an example based on user input.
            # It might need adjustment if the actual RPC method name is different.
            response: Any = self.substrate.rpc_request(
                method="xagere_getNeurons", params=[netuid]
            )

            if isinstance(response, dict) and "result" in response:
                neurons_data = response["result"]
                if not isinstance(neurons_data, list):
                    logger.error(
                        f"RPC method xagere_getNeurons for netuid {netuid} did not return a list in 'result'. Got: {type(neurons_data)}"
                    )
                    return None

                processed_neurons = []
                for neuron in neurons_data:
                    if (
                        isinstance(neuron, dict)
                        and "axon_info" in neuron
                        and isinstance(neuron["axon_info"], dict)
                    ):
                        axon_info = neuron["axon_info"]
                        if "ip" in axon_info and isinstance(axon_info["ip"], int):
                            try:
                                axon_info["ip_str"] = int_to_ip(
                                    axon_info["ip"]
                                )  # Add a new field for string IP
                            except InvalidIPAddressFormat as e:
                                logger.warning(
                                    f"Could not convert axon IP {axon_info['ip']} to string for neuron {neuron.get('hotkey')}: {e}"
                                )
                                axon_info["ip_str"] = (
                                    str(axon_info["ip"]) + " (conversion_failed)"
                                )  # Keep original int if conversion fails
                        else:
                            logger.debug(
                                f"Neuron {neuron.get('hotkey')} axon_info missing 'ip' or not an int: {axon_info.get('ip')}"
                            )
                    processed_neurons.append(neuron)

                logger.info(
                    f"Successfully retrieved and processed all neurons info for netuid {netuid}."
                )
                return processed_neurons
            else:
                if isinstance(response, dict):
                    error_detail: Any = response.get("error")
                elif response is not None:
                    error_detail = response
                else:
                    error_detail = "No response or no result in response"

                if not isinstance(error_detail, str):
                    error_detail = repr(error_detail)
                logger.warning(
                    f"Failed to get all neurons info for netuid {netuid}. RPC response: {error_detail}"
                )
                return None

        except ConnectionError as e:
            logger.error(
                f"Connection error getting all neurons info for netuid {netuid}: {e}",
                exc_info=True,
            )
            return None
        except (
            SubstrateRequestException
        ) as e:  # This might be raised by rpc_request for some errors
            logger.error(
                f"Substrate request error (RPC) getting all neurons info for netuid {netuid}: {e}",
                exc_info=True,
            )
            return None
        except Exception as e:
            logger.exception(
                f"Unexpected error getting all neurons info for netuid {netuid}: {e}"
            )
            return None
