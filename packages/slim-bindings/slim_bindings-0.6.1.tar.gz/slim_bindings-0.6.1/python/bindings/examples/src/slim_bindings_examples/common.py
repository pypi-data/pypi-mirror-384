# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0
"""
Shared helper utilities for the slim_bindings CLI examples.

This module centralizes:
  * Pretty-print / color formatting helpers
  * Identity (auth) helper constructors (shared secret / JWT / JWKS)
  * Command-line option decoration (Click integration)
  * Convenience coroutine for constructing and connecting a local Slim app

The heavy inline commenting is intentional: it is meant to teach newcomers
exactly what each step does, line by line.
"""

import base64  # Used to decode base64-encoded JWKS content (when provided).
import json  # Used for parsing JWKS JSON and dynamic option values.

import click  # CLI option parsing & command composition library.

import slim_bindings  # The Python bindings package we are demonstrating.


class color:
    """ANSI escape sequences for terminal styling."""

    PURPLE = "\033[95m"
    CYAN = "\033[96m"
    DARKCYAN = "\033[36m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"


def format_message(message1: str, message2: str = "") -> str:
    """
    Format a message for display with bold/cyan prefix column and optional suffix.

    Args:
        message1: Primary label (left column, capitalized & padded).
        message2: Optional trailing description/value.

    Returns:
        A colorized string ready to print.
    """
    # Capitalize the first message, pad to 45 chars, inject color & style codes.
    return f"{color.BOLD}{color.CYAN}{message1.capitalize():<45}{color.END}{message2}"


def format_message_print(message1: str, message2: str = "") -> None:
    """
    Print a formatted message using format_message().

    Provided as a thin convenience wrapper to keep example code concise.
    """
    print(format_message(message1, message2))


def split_id(id: str) -> slim_bindings.PyName:
    """
    Split an ID of form organization/namespace/application (or channel).

    Args:
        id: String in the canonical 'org/namespace/app-or-stream' format.

    Raises:
        ValueError: If the id cannot be split into exactly three segments.

    Returns:
        PyName: Constructed identity object.
    """
    try:
        organization, namespace, app = id.split("/")
    except ValueError as e:
        print("Error: IDs must be in the format organization/namespace/app-or-stream.")
        raise e

    return slim_bindings.PyName(organization, namespace, app)


def shared_secret_identity(identity: str, secret: str):
    """
    Create a provider & verifier pair for shared-secret (symmetric) authentication.

    Args:
        identity: Logical identity string (often same as PyName string form).
        secret: Shared secret used to sign / verify tokens (not for production).

    Returns:
        (provider, verifier): Tuple of PyIdentityProvider & PyIdentityVerifier.
    """
    provider = slim_bindings.PyIdentityProvider.SharedSecret(  # type: ignore
        identity=identity, shared_secret=secret
    )
    verifier = slim_bindings.PyIdentityVerifier.SharedSecret(  # type: ignore
        identity=identity, shared_secret=secret
    )
    return provider, verifier


def jwt_identity(
    jwt_path: str,
    spire_bundle_path: str,
    iss: str | None = None,
    sub: str | None = None,
    aud: list[str] | None = None,
):
    """
    Construct a static-JWT provider and JWT verifier from file inputs.

    Process:
      1. Read a JSON structure containing (base64-encoded) JWKS data (a SPIRE
         bundle with a JWKs for each trust domain).
      2. Take all items from the bundle and base64‑decode its
         value to obtain a JWKS JSON string and create a new JWKS JSON containing all keys
         from all trust domains.
      3. Create a StaticJwt identity provider pointing at a local JWT file.
      4. Wrap the JWKS JSON as PyKey with RS256 & JWKS format.
      5. Build a Jwt verifier using the JWKS-derived public key.

    Args:
        jwt_path: Path to a file containing a (static) JWT token.
        spire_bundle_path: Path (relative or absolute) to a SPIRE (or similar) bundle JSON
                  whose first entry’s value is a base64-encoded JWKS.
        iss: Optional issuer claim to enforce.
        sub: Optional subject claim to enforce.
        aud: Optional audience list.

    Returns:
        (provider, verifier): Configured PyIdentityProvider & PyIdentityVerifier.
    """
    print(f"Using SPIRE bundle file: {spire_bundle_path}")

    # Read raw file content (outer JSON containing base64).
    with open(spire_bundle_path) as sb:
        spire_bundle_string = sb.read()

    # Parse as JSON (expects a dict-like structure).
    spire_bundle = json.loads(spire_bundle_string)

    # Extract all values, base64 decode them, and combine all keys into one JWKS.
    all_keys = []
    for trust_domain, v in spire_bundle.items():
        print(f"Processing trust domain: {trust_domain}")
        try:
            decoded_jwks = base64.b64decode(v)
            jwks_json = json.loads(decoded_jwks)

            # Extract keys from this trust domain's JWKS and add to our combined list
            if "keys" in jwks_json:
                all_keys.extend(jwks_json["keys"])
                print(f"  Added {len(jwks_json['keys'])} keys from {trust_domain}")
            else:
                print(f"  Warning: No 'keys' found in JWKS for {trust_domain}")
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as e:
            raise RuntimeError(
                f"Failed to process trust domain {trust_domain}: {e}"
            ) from e

    # Create combined JWKS with all keys from all trust domains
    spire_jwks = json.dumps({"keys": all_keys})
    print(
        f"Combined JWKS contains {len(all_keys)} total keys from {len(spire_bundle)} trust domains"
    )

    # Static provider returns the same token each request (demo usage).
    provider = slim_bindings.PyIdentityProvider.StaticJwt(  # type: ignore
        path=jwt_path,
    )

    # Wrap decoded JWKS JSON string into a PyKey for the verifier.
    pykey = slim_bindings.PyKey(
        algorithm=slim_bindings.PyAlgorithm.RS256,  # Hard-coded for example clarity.
        format=slim_bindings.PyKeyFormat.Jwks,
        key=slim_bindings.PyKeyData.Content(content=spire_jwks),  # type: ignore
    )

    # Build verifier. We nest audience list in list to preserve shape.
    verifier = slim_bindings.PyIdentityVerifier.Jwt(  # type: ignore
        public_key=pykey,
        issuer=iss,
        audience=[aud],
        subject=sub,
    )

    return provider, verifier


class DictParamType(click.ParamType):
    """
    Custom Click parameter type that interprets string input as JSON.

    Accepts:
      * Pre-parsed dict (returned unchanged)
      * JSON string (parsed & returned)
    Raises a Click usage error if parsing fails.
    """

    name = "dict"

    def convert(self, value, param, ctx):
        # If already a dict (e.g. default value), return it unchanged.
        if isinstance(value, dict):
            return value
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            self.fail(f"{value} is not valid JSON", param, ctx)


def common_options(function):
    """
    Decorator stacking all shared CLI options for example commands.

    It:
      * Registers the function as a Click command.
      * Adds identity / connection / auth flags.
      * Returns the wrapped function (Click handles invocation).
    """
    function = click.command(context_settings={"auto_envvar_prefix": "SLIM"})(function)

    # Local identity (required).
    function = click.option(
        "--local",
        type=str,
        required=True,
        help="Local ID in the format organization/namespace/application",
    )(function)

    # Remote identity (optional) used for routing or topics.
    function = click.option(
        "--remote",
        type=str,
        help="Remote ID in the format organization/namespace/application-or-stream",
    )(function)

    # Slim connection parameters (JSON or env var expansion).
    function = click.option(
        "--slim",
        default={
            "endpoint": "http://127.0.0.1:46357",
            "tls": {
                "insecure": True,
            },
        },
        type=DictParamType(),
        help="slim connection parameters",
    )(function)

    # Flag to enable OTEL tracing (no-op if collector unreachable).
    function = click.option(
        "--enable-opentelemetry",
        is_flag=True,
        help="Enable OpenTelemetry tracing",
    )(function)

    # Shared secret for symmetric auth (dev/demo only).
    function = click.option(
        "--shared-secret",
        type=str,
        help="Shared secret for authentication. Don't use this in production.",
        default="secret",
    )(function)

    # JWT token path (static token case).
    function = click.option(
        "--jwt",
        type=str,
        help="JWT token for authentication.",
    )(function)

    # JWKS / key bundle path.
    function = click.option(
        "--spire-trust-bundle",
        type=str,
        help="SPIRE trust bundle for authentication.",
    )(function)

    # Audience to assert for JWT verification.
    function = click.option(
        "--audience",
        type=str,
        help="Audience for the JWT.",
    )(function)

    # Invite multiple participants to a group session.
    function = click.option(
        "--invites",
        type=str,
        multiple=True,
        help="Invite other participants to the group session. Can be specified multiple times.",
    )(function)

    # Enable MLS (group security) on session creation.
    function = click.option(
        "--enable-mls",
        is_flag=True,
        help="Enable MLS (Message Layer Security) for the session.",
    )(function)

    return function


async def create_local_app(
    local: str,
    slim: dict,
    remote: str | None = None,
    enable_opentelemetry: bool = False,
    shared_secret: str = "secret",
    jwt: str | None = None,
    spire_trust_bundle: str | None = None,
    audience: list[str] | None = None,
):
    """
    Build and connect a Slim application instance given user CLI parameters.

    Resolution precedence for auth:
      1. If jwt + bundle + audience provided -> JWT/JWKS flow.
      2. Else -> shared secret (must be provided, raises if missing).

    Args:
        local: Local identity string (org/ns/app).
        slim: Dict of connection parameters (endpoint, tls flags, etc.).
        remote: Optional remote identity (unused here, reserved for future).
        enable_opentelemetry: Enable OTEL tracing export.
        shared_secret: Symmetric secret for shared-secret mode.
        jwt: Path to static JWT token (for StaticJwt provider).
        spire_trust_bundle: Path to a spire trust bundle file (containing the JWKs for each trust domain).
        audience: Audience list for JWT verification.

    Returns:
        Slim: Connected high-level Slim instance.
    """
    # Initialize tracing (synchronous init; not awaited as binding returns immediately).
    slim_bindings.init_tracing(
        {
            "log_level": "info",
            "opentelemetry": {
                "enabled": enable_opentelemetry,
                "grpc": {
                    "endpoint": "http://localhost:4317",
                },
            },
        }
    )

    # Derive identity provider & verifier using JWT/JWKS if all pieces supplied.
    if jwt and spire_trust_bundle and audience:
        print("Using JWT + JWKS authentication.")
        provider, verifier = jwt_identity(
            jwt,
            spire_trust_bundle,
            aud=audience,
        )
    else:
        print(
            "Warning: Falling back to shared-secret authentication. Don't use this in production!"
        )
        # Fall back to shared secret (dev-friendly default).
        provider, verifier = shared_secret_identity(
            identity=local,
            secret=shared_secret,
        )

    # Convert local identifier to a strongly typed PyName.
    local_name = split_id(local)

    # Instantiate Slim (async constructor prepares underlying PyService).
    local_app = await slim_bindings.Slim.new(local_name, provider, verifier)

    # Provide feedback to user (instance numeric id).
    format_message_print(f"{local_app.id_str}", "Created app")

    # Establish outbound connection using provided parameters.
    _ = await local_app.connect(slim)

    # Confirm endpoint connectivity.
    format_message_print(f"{local_app.id_str}", f"Connected to {slim['endpoint']}")

    return local_app
