// Copyright AGNTCY Contributors (https://github.com/agntcy)
// SPDX-License-Identifier: Apache-2.0

pub mod errors;
#[macro_use]
pub mod service;

pub mod app;

// Third-party crates
pub use slim_datapath::messages::utils::SlimHeaderFlags;

// Local crate
pub use errors::ServiceError;
pub use service::{KIND, Service, ServiceBuilder, ServiceConfiguration};
