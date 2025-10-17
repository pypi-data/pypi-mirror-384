// Copyright AGNTCY Contributors (https://github.com/agntcy)
// SPDX-License-Identifier: Apache-2.0

use std::sync::Arc;

use rustls::{
    ClientConfig as RustlsClientConfig, DigitallySignedStruct, Error, RootCertStore,
    SignatureScheme,
    client::{
        ResolvesClientCert,
        danger::{HandshakeSignatureValid, ServerCertVerified, ServerCertVerifier},
    },
    sign::CertifiedKey,
    version::{TLS12, TLS13},
};
use rustls_pki_types::{CertificateDer, ServerName, UnixTime};
use schemars::JsonSchema;
use serde;
use serde::{Deserialize, Serialize};
use tracing::warn;

use super::common::{Config, ConfigError, RustlsConfigLoader};
use crate::{
    component::configuration::{Configuration, ConfigurationError},
    tls::common::{StaticCertResolver, WatcherCertResolver},
};

#[derive(Debug, Serialize, Deserialize, PartialEq, Clone, JsonSchema)]
pub struct TlsClientConfig {
    /// The Config struct
    #[serde(flatten, default)]
    pub config: Config,

    /// In gRPC and HTTP when set to true, this is used to disable the client transport security.
    /// (optional, default false)
    #[serde(default = "default_insecure")]
    pub insecure: bool,

    /// InsecureSkipVerify will enable TLS but not verify the server certificate.
    #[serde(default = "default_insecure_skip_verify")]
    pub insecure_skip_verify: bool,
}

impl Default for TlsClientConfig {
    fn default() -> Self {
        TlsClientConfig {
            config: Config::default(),
            insecure: default_insecure(),
            insecure_skip_verify: default_insecure_skip_verify(),
        }
    }
}

fn default_insecure() -> bool {
    false
}

fn default_insecure_skip_verify() -> bool {
    false
}

// Cert verifier that skips verification
// Implement a no-op verifier if needed for insecure connections
#[derive(Debug)]
struct NoVerifier;

impl ServerCertVerifier for NoVerifier {
    fn verify_server_cert(
        &self,
        _: &CertificateDer<'_>,
        _: &[CertificateDer<'_>],
        _: &ServerName<'_>,
        _: &[u8],
        _: UnixTime,
    ) -> Result<ServerCertVerified, Error> {
        warn!("Skipping server cert verification");
        Ok(ServerCertVerified::assertion())
    }

    fn verify_tls12_signature(
        &self,
        _: &[u8],
        _: &CertificateDer<'_>,
        _: &DigitallySignedStruct,
    ) -> Result<HandshakeSignatureValid, Error> {
        warn!("Skipping server cert verification - TLS 1.2");
        Ok(HandshakeSignatureValid::assertion())
    }

    fn verify_tls13_signature(
        &self,
        _: &[u8],
        _: &CertificateDer<'_>,
        _: &DigitallySignedStruct,
    ) -> Result<HandshakeSignatureValid, Error> {
        warn!("Skipping server cert verification - TLS 1.3");
        Ok(HandshakeSignatureValid::assertion())
    }

    fn supported_verify_schemes(&self) -> Vec<SignatureScheme> {
        vec![
            SignatureScheme::RSA_PKCS1_SHA1,
            SignatureScheme::ECDSA_SHA1_Legacy,
            SignatureScheme::RSA_PKCS1_SHA256,
            SignatureScheme::ECDSA_NISTP256_SHA256,
            SignatureScheme::RSA_PKCS1_SHA384,
            SignatureScheme::ECDSA_NISTP384_SHA384,
            SignatureScheme::RSA_PKCS1_SHA512,
            SignatureScheme::ECDSA_NISTP521_SHA512,
            SignatureScheme::RSA_PSS_SHA256,
            SignatureScheme::RSA_PSS_SHA384,
            SignatureScheme::RSA_PSS_SHA512,
            SignatureScheme::ED25519,
            SignatureScheme::ED448,
        ]
    }
}

impl ResolvesClientCert for super::common::WatcherCertResolver {
    fn resolve(
        &self,
        _root_hint_subjects: &[&[u8]],
        _sigschemes: &[SignatureScheme],
    ) -> Option<Arc<CertifiedKey>> {
        Some(self.cert.read().clone())
    }

    fn has_certs(&self) -> bool {
        true
    }
}

impl ResolvesClientCert for super::common::StaticCertResolver {
    fn resolve(
        &self,
        _root_hint_subjects: &[&[u8]],
        _sigschemes: &[SignatureScheme],
    ) -> Option<Arc<CertifiedKey>> {
        Some(self.cert.clone())
    }

    fn has_certs(&self) -> bool {
        true
    }
}

// methods for ClientConfig to create a RustlsClientConfig from the config
impl TlsClientConfig {
    /// Create a new TlsClientConfig
    pub fn new() -> Self {
        TlsClientConfig::default()
    }

    pub fn insecure() -> Self {
        TlsClientConfig {
            insecure: true,
            ..Default::default()
        }
    }

    /// Set insecure (disable certificate verification)
    pub fn with_insecure_skip_verify(self, insecure_skip_verify: bool) -> Self {
        TlsClientConfig {
            insecure_skip_verify,
            ..self
        }
    }

    /// Set insecure (disable TLS)
    pub fn with_insecure(self, insecure: bool) -> Self {
        TlsClientConfig { insecure, ..self }
    }

    /// Set the CA file
    pub fn with_ca_file(self, ca_file: &str) -> Self {
        TlsClientConfig {
            config: self.config.with_ca_file(ca_file),
            ..self
        }
    }

    /// Set the CA pem
    pub fn with_ca_pem(self, ca_pem: &str) -> Self {
        TlsClientConfig {
            config: self.config.with_ca_pem(ca_pem),
            ..self
        }
    }

    /// Set if include system CA certs pool
    pub fn with_include_system_ca_certs_pool(self, include_system_ca_certs_pool: bool) -> Self {
        TlsClientConfig {
            config: self
                .config
                .with_include_system_ca_certs_pool(include_system_ca_certs_pool),
            ..self
        }
    }

    /// Set the cert file (for client auth)
    pub fn with_cert_file(self, cert_file: &str) -> Self {
        TlsClientConfig {
            config: self.config.with_cert_file(cert_file),
            ..self
        }
    }

    /// Set the cert pem (for client auth)
    pub fn with_cert_pem(self, cert_pem: &str) -> Self {
        TlsClientConfig {
            config: self.config.with_cert_pem(cert_pem),
            ..self
        }
    }

    /// Set the key file (for client auth)
    pub fn with_key_file(self, key_file: &str) -> Self {
        TlsClientConfig {
            config: self.config.with_key_file(key_file),
            ..self
        }
    }

    /// Set the key pem (for client auth)
    pub fn with_key_pem(self, key_pem: &str) -> Self {
        TlsClientConfig {
            config: self.config.with_key_pem(key_pem),
            ..self
        }
    }

    /// Set the TLS version
    pub fn with_tls_version(self, tls_version: &str) -> Self {
        TlsClientConfig {
            config: self.config.with_tls_version(tls_version),
            ..self
        }
    }

    /// Set the reload interval
    pub fn with_reload_interval(self, reload_interval: Option<std::time::Duration>) -> Self {
        TlsClientConfig {
            config: self.config.with_reload_interval(reload_interval),
            ..self
        }
    }

    fn load_rustls_client_config(
        &self,
        root_store: RootCertStore,
    ) -> Result<RustlsClientConfig, ConfigError> {
        use ConfigError::*;

        // Check TLS version
        let tls_version = match self.config.tls_version.as_str() {
            "tls1.2" => &TLS12,
            "tls1.3" => &TLS13,
            _ => {
                // return an error if the tls version is invalid
                return Err(InvalidTlsVersion(self.config.tls_version.clone()));
            }
        };

        // create a client ConfigBuilder
        let config_builder = RustlsClientConfig::builder_with_protocol_versions(&[tls_version])
            .with_root_certificates(root_store);

        // Check if enable client auth or not
        match (
            self.config.has_cert_file() && self.config.has_key_file(),
            self.config.has_cert_pem() && self.config.has_key_pem(),
        ) {
            (true, true) => {
                // If both cert_file and cert_pem are set, return an error
                Err(CannotUseBoth("cert".to_string()))
            }
            (false, false) => {
                // If no client auth, return the config with client auth disabled
                Ok(config_builder.with_no_client_auth())
            }
            (true, false) => {
                // Create a custom Certificate provider that watches for changes in the certificate or the key file
                let cert_resolver = WatcherCertResolver::new(
                    self.config.key_file.as_ref().unwrap(),
                    self.config.cert_file.as_ref().unwrap(),
                    config_builder.crypto_provider(),
                )?;

                Ok(config_builder.with_client_cert_resolver(Arc::new(cert_resolver)))
            }
            (false, true) => {
                let cert_resolver = StaticCertResolver::new(
                    self.config.key_pem.as_ref().unwrap(),
                    self.config.cert_pem.as_ref().unwrap(),
                    config_builder.crypto_provider(),
                )?;
                Ok(config_builder.with_client_cert_resolver(Arc::new(cert_resolver)))
            }
        }
    }
}

// trait implementation
impl RustlsConfigLoader<RustlsClientConfig> for TlsClientConfig {
    fn load_rustls_config(&self) -> Result<Option<RustlsClientConfig>, ConfigError> {
        if self.insecure && !self.config.has_ca() {
            return Ok(None);
        }

        let root_store = self.config.load_ca_cert_pool()?;
        let mut client_config = self.load_rustls_client_config(root_store)?;

        // Set unsecure stuff
        if self.insecure_skip_verify {
            client_config
                .dangerous()
                .set_certificate_verifier(Arc::new(NoVerifier));
        }

        Ok(Some(client_config))
    }
}

impl Configuration for TlsClientConfig {
    fn validate(&self) -> Result<(), ConfigurationError> {
        // TODO(msardara): validate the configuration
        Ok(())
    }
}
