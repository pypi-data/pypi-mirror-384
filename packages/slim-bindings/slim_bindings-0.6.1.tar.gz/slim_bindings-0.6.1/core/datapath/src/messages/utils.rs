// Copyright AGNTCY Contributors (https://github.com/agntcy)
// SPDX-License-Identifier: Apache-2.0

use std::collections::HashMap;
use std::fmt::Display;

use tracing::debug;

use super::encoder::Name;
use crate::api::{
    Content, MessageType, ProtoMessage, ProtoName, ProtoPublish, ProtoPublishType,
    ProtoSessionType, ProtoSubscribe, ProtoSubscribeType, ProtoUnsubscribe, ProtoUnsubscribeType,
    SessionHeader, SlimHeader,
    proto::dataplane::v1::{OriginalName, SessionMessageType},
};

use thiserror::Error;
use tracing::error;

#[derive(Error, Debug, PartialEq)]
pub enum MessageError {
    #[error("SLIM header not found")]
    SlimHeaderNotFound,
    #[error("source not found")]
    SourceNotFound,
    #[error("destination not found")]
    DestinationNotFound,
    #[error("session header not found")]
    SessionHeaderNotFound,
    #[error("message type not found")]
    MessageTypeNotFound,
    #[error("incoming connection not found")]
    IncomingConnectionNotFound,
}

// Metadata Keys
pub const SLIM_IDENTITY: &str = "SLIM_IDENTITY";

/// ProtoName from Name
impl From<&Name> for ProtoName {
    fn from(name: &Name) -> Self {
        Self {
            component_0: name.components()[0],
            component_1: name.components()[1],
            component_2: name.components()[2],
            component_3: name.components()[3],
        }
    }
}

/// Print message type
impl Display for MessageType {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            MessageType::Publish(_) => write!(f, "publish"),
            MessageType::Subscribe(_) => write!(f, "subscribe"),
            MessageType::Unsubscribe(_) => write!(f, "unsubscribe"),
        }
    }
}

/// Struct grouping the SLIMHeaeder flags for convenience
#[derive(Debug, Clone)]
pub struct SlimHeaderFlags {
    pub fanout: u32,
    pub recv_from: Option<u64>,
    pub forward_to: Option<u64>,
    pub incoming_conn: Option<u64>,
    pub error: Option<bool>,
}

impl Default for SlimHeaderFlags {
    fn default() -> Self {
        Self {
            fanout: 1,
            recv_from: None,
            forward_to: None,
            incoming_conn: None,
            error: None,
        }
    }
}

impl Display for SlimHeaderFlags {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(
            f,
            "fanout: {}, recv_from: {:?}, forward_to: {:?}, incoming_conn: {:?}, error: {:?}",
            self.fanout, self.recv_from, self.forward_to, self.incoming_conn, self.error
        )
    }
}

impl SlimHeaderFlags {
    pub fn new(
        fanout: u32,
        recv_from: Option<u64>,
        forward_to: Option<u64>,
        incoming_conn: Option<u64>,
        error: Option<bool>,
    ) -> Self {
        Self {
            fanout,
            recv_from,
            forward_to,
            incoming_conn,
            error,
        }
    }

    pub fn with_fanout(self, fanout: u32) -> Self {
        Self { fanout, ..self }
    }

    pub fn with_recv_from(self, recv_from: u64) -> Self {
        Self {
            recv_from: Some(recv_from),
            ..self
        }
    }

    pub fn with_forward_to(self, forward_to: u64) -> Self {
        Self {
            forward_to: Some(forward_to),
            ..self
        }
    }

    pub fn with_incoming_conn(self, incoming_conn: u64) -> Self {
        Self {
            incoming_conn: Some(incoming_conn),
            ..self
        }
    }

    pub fn with_error(self, error: bool) -> Self {
        Self {
            error: Some(error),
            ..self
        }
    }
}

/// SLIM Header
/// This header is used to identify the source and destination of the message
/// and to manage the connections used to send and receive the message
impl SlimHeader {
    pub fn new(source: &Name, destination: &Name, flags: Option<SlimHeaderFlags>) -> Self {
        let flags = flags.unwrap_or_default();

        Self {
            source: Some(ProtoName::from(source)),
            destination: Some(ProtoName::from(destination)),
            fanout: flags.fanout,
            recv_from: flags.recv_from,
            forward_to: flags.forward_to,
            incoming_conn: flags.incoming_conn,
            error: flags.error,
        }
    }

    pub fn clear(&mut self) {
        self.recv_from = None;
        self.forward_to = None;
    }

    pub fn get_recv_from(&self) -> Option<u64> {
        self.recv_from
    }

    pub fn get_forward_to(&self) -> Option<u64> {
        self.forward_to
    }

    pub fn get_incoming_conn(&self) -> Option<u64> {
        self.incoming_conn
    }

    pub fn get_error(&self) -> Option<bool> {
        self.error
    }

    pub fn get_source(&self) -> Name {
        match &self.source {
            Some(source) => Name::from(source),
            None => panic!("source not found"),
        }
    }

    pub fn get_dst(&self) -> Name {
        match &self.destination {
            Some(destination) => Name::from(destination),
            None => panic!("destination not found"),
        }
    }

    pub fn set_source(&mut self, source: &Name) {
        self.source = Some(ProtoName::from(source));
    }

    pub fn set_destination(&mut self, dst: &Name) {
        self.destination = Some(ProtoName::from(dst));
    }

    pub fn get_fanout(&self) -> u32 {
        self.fanout
    }

    pub fn set_recv_from(&mut self, recv_from: Option<u64>) {
        self.recv_from = recv_from;
    }

    pub fn set_forward_to(&mut self, forward_to: Option<u64>) {
        self.forward_to = forward_to;
    }

    pub fn set_error(&mut self, error: Option<bool>) {
        self.error = error;
    }

    pub fn set_incoming_conn(&mut self, incoming_conn: Option<u64>) {
        self.incoming_conn = incoming_conn;
    }

    pub fn set_error_flag(&mut self, error: Option<bool>) {
        self.error = error;
    }

    pub fn set_fanout(&mut self, fanout: u32) {
        self.fanout = fanout;
    }

    // returns the connection to use to process correctly the message
    // first connection is from where we received the packet
    // the second is where to forward the packet if needed
    pub fn get_in_out_connections(&self) -> (u64, Option<u64>) {
        // when calling this function, incoming connection is set
        let incoming = self
            .get_incoming_conn()
            .expect("incoming connection not found");

        if let Some(val) = self.get_recv_from() {
            debug!(
                "received recv_from command, update state on connection {}",
                val
            );
            return (val, None);
        }

        if let Some(val) = self.get_forward_to() {
            debug!(
                "received forward_to command, update state and forward to connection {}",
                val
            );
            return (incoming, Some(val));
        }

        // by default, return the incoming connection and None
        (incoming, None)
    }
}

/// Session Header
/// This header is used to identify the session and the message
/// and to manage session state
impl SessionHeader {
    pub fn new(
        session_type: i32,
        session_message_type: i32,
        session_id: u32,
        message_id: u32,
        source: &Option<Name>,
        destination: &Option<Name>,
    ) -> Self {
        let src = match source {
            Some(name) => name.components_strings().map(|c| OriginalName {
                component_0: c[0].clone(),
                component_1: c[1].clone(),
                component_2: c[2].clone(),
                component_3: name.id(),
            }),
            None => None,
        };

        let dst = match destination {
            Some(name) => name.components_strings().map(|c| OriginalName {
                component_0: c[0].clone(),
                component_1: c[1].clone(),
                component_2: c[2].clone(),
                component_3: name.id(),
            }),
            None => None,
        };

        Self {
            session_type,
            session_message_type,
            session_id,
            message_id,
            source: src,
            destination: dst,
        }
    }

    pub fn get_session_id(&self) -> u32 {
        self.session_id
    }

    pub fn get_message_id(&self) -> u32 {
        self.message_id
    }

    pub fn set_session_id(&mut self, session_id: u32) {
        self.session_id = session_id;
    }

    pub fn set_message_id(&mut self, message_id: u32) {
        self.message_id = message_id;
    }

    pub fn clear(&mut self) {
        self.session_id = 0;
        self.message_id = 0;
    }

    pub fn get_source(&self) -> Option<Name> {
        match &self.source {
            Some(src) => {
                let n = Name::from_strings([
                    src.component_0.clone(),
                    src.component_1.clone(),
                    src.component_2.clone(),
                ])
                .with_id(src.component_3);
                Some(n)
            }
            None => None,
        }
    }

    pub fn set_source(&mut self, source: &Name) {
        let c_opt = source.components_strings();
        if c_opt.is_none() {
            return;
        }

        let c = c_opt.unwrap();

        self.source = Some(OriginalName {
            component_0: c[0].clone(),
            component_1: c[1].clone(),
            component_2: c[2].clone(),
            component_3: source.id(),
        });
    }

    pub fn get_destination(&self) -> Option<Name> {
        match &self.destination {
            Some(src) => {
                let n = Name::from_strings([
                    src.component_0.clone(),
                    src.component_1.clone(),
                    src.component_2.clone(),
                ])
                .with_id(src.component_3);
                Some(n)
            }
            None => None,
        }
    }

    pub fn set_destination(&mut self, destination: &Name) {
        let c_opt = destination.components_strings();
        if c_opt.is_none() {
            return;
        }

        let c = c_opt.unwrap();

        self.destination = Some(OriginalName {
            component_0: c[0].clone(),
            component_1: c[1].clone(),
            component_2: c[2].clone(),
            component_3: destination.id(),
        });
    }
}

/// ProtoSubscribe
/// This message is used to subscribe to a topic
impl ProtoSubscribe {
    pub fn new(source: &Name, dst: &Name, flags: Option<SlimHeaderFlags>) -> Self {
        let header = Some(SlimHeader::new(source, dst, flags));

        ProtoSubscribe {
            header,
            component_0: dst.components_strings().unwrap()[0].clone(),
            component_1: dst.components_strings().unwrap()[1].clone(),
            component_2: dst.components_strings().unwrap()[2].clone(),
        }
    }
}

/// From ProtoMessage to ProtoSubscribe
impl From<ProtoMessage> for ProtoSubscribe {
    fn from(message: ProtoMessage) -> Self {
        match message.message_type {
            Some(ProtoSubscribeType(s)) => s,
            _ => panic!("message type is not subscribe"),
        }
    }
}

/// ProtoUnsubscribe
/// This message is used to unsubscribe from a topic
impl ProtoUnsubscribe {
    pub fn new(source: &Name, dst: &Name, flags: Option<SlimHeaderFlags>) -> Self {
        let header = Some(SlimHeader::new(source, dst, flags));

        ProtoUnsubscribe {
            header,
            component_0: dst.components_strings().unwrap()[0].clone(),
            component_1: dst.components_strings().unwrap()[1].clone(),
            component_2: dst.components_strings().unwrap()[2].clone(),
        }
    }
}

/// From ProtoMessage to ProtoUnsubscribe
impl From<ProtoMessage> for ProtoUnsubscribe {
    fn from(message: ProtoMessage) -> Self {
        match message.message_type {
            Some(ProtoUnsubscribeType(u)) => u,
            _ => panic!("message type is not unsubscribe"),
        }
    }
}

/// ProtoPublish
/// This message is used to publish a message, either to a shared channel or to a specific application
impl ProtoPublish {
    pub fn with_header(
        header: Option<SlimHeader>,
        session: Option<SessionHeader>,
        payload: Option<Content>,
    ) -> Self {
        ProtoPublish {
            header,
            session,
            msg: payload,
        }
    }

    pub fn new(
        source: &Name,
        dst: &Name,
        flags: Option<SlimHeaderFlags>,
        content_type: &str,
        blob: Vec<u8>,
    ) -> Self {
        let slim_header = Some(SlimHeader::new(source, dst, flags));

        let mut session_header = SessionHeader::default();
        session_header.set_source(source);
        session_header.set_destination(dst);

        let msg = Some(Content {
            content_type: content_type.to_string(),
            blob,
        });

        Self::with_header(slim_header, Some(session_header), msg)
    }

    pub fn get_slim_header(&self) -> &SlimHeader {
        self.header.as_ref().unwrap()
    }

    pub fn get_session_header(&self) -> &SessionHeader {
        self.session.as_ref().unwrap()
    }

    pub fn get_slim_header_as_mut(&mut self) -> &mut SlimHeader {
        self.header.as_mut().unwrap()
    }

    pub fn get_session_header_as_mut(&mut self) -> &mut SessionHeader {
        self.session.as_mut().unwrap()
    }

    pub fn get_payload(&self) -> &Content {
        self.msg.as_ref().unwrap()
    }
}

/// From ProtoMessage to ProtoPublish
impl From<ProtoMessage> for ProtoPublish {
    fn from(message: ProtoMessage) -> Self {
        match message.message_type {
            Some(ProtoPublishType(p)) => p,
            _ => panic!("message type is not publish"),
        }
    }
}

/// ProtoMessage
/// This represents a generic message that can be sent over the network
impl ProtoMessage {
    fn new(metadata: HashMap<String, String>, message_type: MessageType) -> Self {
        ProtoMessage {
            metadata,
            message_type: Some(message_type),
        }
    }

    pub fn new_subscribe(source: &Name, dst: &Name, flags: Option<SlimHeaderFlags>) -> Self {
        let subscribe = ProtoSubscribe::new(source, dst, flags);

        Self::new(HashMap::new(), ProtoSubscribeType(subscribe))
    }

    pub fn new_unsubscribe(source: &Name, dst: &Name, flags: Option<SlimHeaderFlags>) -> Self {
        let unsubscribe = ProtoUnsubscribe::new(source, dst, flags);

        Self::new(HashMap::new(), ProtoUnsubscribeType(unsubscribe))
    }

    pub fn new_publish(
        source: &Name,
        dst: &Name,
        flags: Option<SlimHeaderFlags>,
        content_type: &str,
        blob: Vec<u8>,
    ) -> Self {
        let publish = ProtoPublish::new(source, dst, flags, content_type, blob);

        Self::new(HashMap::new(), ProtoPublishType(publish))
    }

    pub fn new_publish_with_headers(
        slim_header: Option<SlimHeader>,
        session_header: Option<SessionHeader>,
        content_type: &str,
        blob: Vec<u8>,
    ) -> Self {
        let publish = ProtoPublish::with_header(
            slim_header,
            session_header,
            Some(Content {
                content_type: content_type.to_string(),
                blob,
            }),
        );

        Self::new(HashMap::new(), ProtoPublishType(publish))
    }

    // validate message
    pub fn validate(&self) -> Result<(), MessageError> {
        // make sure the message type is set
        if self.message_type.is_none() {
            return Err(MessageError::MessageTypeNotFound);
        }

        // make sure SLIM header is set
        if self.try_get_slim_header().is_none() {
            return Err(MessageError::SlimHeaderNotFound);
        }

        // Get SLIM header
        let slim_header = self.get_slim_header();

        // make sure source and destination are set
        if slim_header.source.is_none() {
            return Err(MessageError::SourceNotFound);
        }
        if slim_header.destination.is_none() {
            return Err(MessageError::DestinationNotFound);
        }

        match &self.message_type {
            Some(ProtoPublishType(p)) => {
                // SLIM Header
                if p.header.is_none() {
                    return Err(MessageError::SlimHeaderNotFound);
                }

                // Publish message should have the session header
                if p.session.is_none() {
                    return Err(MessageError::SessionHeaderNotFound);
                }
            }
            Some(ProtoSubscribeType(s)) => {
                if s.header.is_none() {
                    return Err(MessageError::SlimHeaderNotFound);
                }
            }
            Some(ProtoUnsubscribeType(u)) => {
                if u.header.is_none() {
                    return Err(MessageError::SlimHeaderNotFound);
                }
            }
            None => return Err(MessageError::MessageTypeNotFound),
        }

        Ok(())
    }

    // add metadata key in the map assigning the value val
    // if the key exists the value is replaced by val
    pub fn insert_metadata(&mut self, key: String, val: String) {
        self.metadata.insert(key, val);
    }

    // remove metadata key from the map
    pub fn remove_metadata(&mut self, key: &str) -> Option<String> {
        self.metadata.remove(key)
    }

    pub fn contains_metadata(&self, key: &str) -> bool {
        self.metadata.contains_key(key)
    }

    pub fn get_metadata(&self, key: &str) -> Option<&String> {
        self.metadata.get(key)
    }

    pub fn get_metadata_map(&self) -> HashMap<String, String> {
        self.metadata.clone()
    }

    pub fn set_metadata_map(&mut self, map: HashMap<String, String>) {
        for (k, v) in map.iter() {
            self.insert_metadata(k.to_string(), v.to_string());
        }
    }

    pub fn get_slim_header(&self) -> &SlimHeader {
        match &self.message_type {
            Some(ProtoPublishType(publish)) => publish.header.as_ref().unwrap(),
            Some(ProtoSubscribeType(sub)) => sub.header.as_ref().unwrap(),
            Some(ProtoUnsubscribeType(unsub)) => unsub.header.as_ref().unwrap(),
            None => panic!("SLIM header not found"),
        }
    }

    pub fn get_slim_header_mut(&mut self) -> &mut SlimHeader {
        match &mut self.message_type {
            Some(ProtoPublishType(publish)) => publish.header.as_mut().unwrap(),
            Some(ProtoSubscribeType(sub)) => sub.header.as_mut().unwrap(),
            Some(ProtoUnsubscribeType(unsub)) => unsub.header.as_mut().unwrap(),
            None => panic!("SLIM header not found"),
        }
    }

    pub fn try_get_slim_header(&self) -> Option<&SlimHeader> {
        match &self.message_type {
            Some(ProtoPublishType(publish)) => publish.header.as_ref(),
            Some(ProtoSubscribeType(sub)) => sub.header.as_ref(),
            Some(ProtoUnsubscribeType(unsub)) => unsub.header.as_ref(),
            None => None,
        }
    }

    pub fn get_session_header(&self) -> &SessionHeader {
        match &self.message_type {
            Some(ProtoPublishType(publish)) => publish.session.as_ref().unwrap(),
            Some(ProtoSubscribeType(_)) => panic!("session header not found"),
            Some(ProtoUnsubscribeType(_)) => panic!("session header not found"),
            None => panic!("session header not found"),
        }
    }

    pub fn get_session_header_mut(&mut self) -> &mut SessionHeader {
        match &mut self.message_type {
            Some(ProtoPublishType(publish)) => publish.session.as_mut().unwrap(),
            Some(ProtoSubscribeType(_)) => panic!("session header not found"),
            Some(ProtoUnsubscribeType(_)) => panic!("session header not found"),
            None => panic!("session header not found"),
        }
    }

    pub fn try_get_session_header(&self) -> Option<&SessionHeader> {
        match &self.message_type {
            Some(ProtoPublishType(publish)) => publish.session.as_ref(),
            Some(ProtoSubscribeType(_)) => None,
            Some(ProtoUnsubscribeType(_)) => None,
            None => None,
        }
    }

    pub fn try_get_session_header_mut(&mut self) -> Option<&mut SessionHeader> {
        match &mut self.message_type {
            Some(ProtoPublishType(publish)) => publish.session.as_mut(),
            Some(ProtoSubscribeType(_)) => None,
            Some(ProtoUnsubscribeType(_)) => None,
            None => None,
        }
    }

    pub fn get_id(&self) -> u32 {
        self.get_session_header().get_message_id()
    }

    pub fn get_source(&self) -> Name {
        if let Some(ProtoPublishType(pubslih)) = &self.message_type {
            // try to the src dst from the session header
            if let Some(s) = pubslih.get_session_header().get_source() {
                return s;
            }
        }

        // get from slim header
        self.get_slim_header().get_source()
    }

    pub fn get_fanout(&self) -> u32 {
        self.get_slim_header().get_fanout()
    }

    pub fn get_recv_from(&self) -> Option<u64> {
        self.get_slim_header().get_recv_from()
    }

    pub fn get_forward_to(&self) -> Option<u64> {
        self.get_slim_header().get_forward_to()
    }

    pub fn get_error(&self) -> Option<bool> {
        self.get_slim_header().get_error()
    }

    pub fn get_incoming_conn(&self) -> u64 {
        self.get_slim_header().get_incoming_conn().unwrap()
    }

    pub fn try_get_incoming_conn(&self) -> Option<u64> {
        self.get_slim_header().get_incoming_conn()
    }

    pub fn get_dst(&self) -> Name {
        match &self.message_type {
            Some(ProtoPublishType(publish)) => {
                // try to the get dst from the session header
                if let Some(d) = publish.get_session_header().get_destination() {
                    return d;
                }
                // get from the slim header
                self.get_slim_header().get_dst()
            }
            Some(ProtoSubscribeType(subscribe)) => {
                let dst = self.get_slim_header().get_dst();
                // complete name with the original strings
                Name::from_strings([
                    subscribe.component_0.clone(),
                    subscribe.component_1.clone(),
                    subscribe.component_2.clone(),
                ])
                .with_id(dst.id())
            }
            Some(ProtoUnsubscribeType(unsubscribe)) => {
                let dst = self.get_slim_header().get_dst();
                // complete name with the original strings
                Name::from_strings([
                    unsubscribe.component_0.clone(),
                    unsubscribe.component_1.clone(),
                    unsubscribe.component_2.clone(),
                ])
                .with_id(dst.id())
            }
            None => {
                unreachable!("destination not found");
            }
        }
    }

    pub fn get_type(&self) -> &MessageType {
        match &self.message_type {
            Some(t) => t,
            None => panic!("message type not found"),
        }
    }

    pub fn get_payload(&self) -> Option<&Content> {
        match &self.message_type {
            Some(ProtoPublishType(p)) => p.msg.as_ref(),
            Some(ProtoSubscribeType(_)) => panic!("payload not found"),
            Some(ProtoUnsubscribeType(_)) => panic!("payload not found"),
            None => panic!("payload not found"),
        }
    }

    pub fn get_session_message_type(&self) -> SessionMessageType {
        self.get_session_header()
            .session_message_type
            .try_into()
            .unwrap_or_default()
    }

    pub fn clear_slim_header(&mut self) {
        self.get_slim_header_mut().clear();
    }

    pub fn set_recv_from(&mut self, recv_from: Option<u64>) {
        self.get_slim_header_mut().set_recv_from(recv_from);
    }

    pub fn set_forward_to(&mut self, forward_to: Option<u64>) {
        self.get_slim_header_mut().set_forward_to(forward_to);
    }

    pub fn set_error(&mut self, error: Option<bool>) {
        self.get_slim_header_mut().set_error(error);
    }

    pub fn set_fanout(&mut self, fanout: u32) {
        self.get_slim_header_mut().set_fanout(fanout);
    }

    pub fn set_incoming_conn(&mut self, incoming_conn: Option<u64>) {
        self.get_slim_header_mut().set_incoming_conn(incoming_conn);
    }

    pub fn set_error_flag(&mut self, error: Option<bool>) {
        self.get_slim_header_mut().set_error_flag(error);
    }

    pub fn set_session_message_type(&mut self, message_type: SessionMessageType) {
        self.get_session_header_mut()
            .set_session_message_type(message_type);
    }

    pub fn set_session_type(&mut self, session_type: ProtoSessionType) {
        self.get_session_header_mut().set_session_type(session_type);
    }

    pub fn get_session_type(&self) -> ProtoSessionType {
        self.get_session_header().session_type()
    }

    pub fn set_message_id(&mut self, message_id: u32) {
        self.get_session_header_mut().set_message_id(message_id);
    }

    pub fn is_publish(&self) -> bool {
        matches!(self.get_type(), MessageType::Publish(_))
    }

    pub fn is_subscribe(&self) -> bool {
        matches!(self.get_type(), MessageType::Subscribe(_))
    }

    pub fn is_unsubscribe(&self) -> bool {
        matches!(self.get_type(), MessageType::Unsubscribe(_))
    }
}

impl AsRef<ProtoPublish> for ProtoMessage {
    fn as_ref(&self) -> &ProtoPublish {
        match &self.message_type {
            Some(ProtoPublishType(p)) => p,
            _ => panic!("message type is not publish"),
        }
    }
}

#[cfg(test)]
mod tests {
    use crate::{api::proto::dataplane::v1::SessionMessageType, messages::encoder::Name};

    use super::*;

    fn test_subscription_template(
        subscription: bool,
        source: Name,
        dst: Name,
        flags: Option<SlimHeaderFlags>,
    ) {
        let sub = {
            if subscription {
                ProtoMessage::new_subscribe(&source, &dst, flags.clone())
            } else {
                ProtoMessage::new_unsubscribe(&source, &dst, flags.clone())
            }
        };

        let flags = if flags.is_none() {
            Some(SlimHeaderFlags::default())
        } else {
            flags
        };

        assert!(!sub.is_publish());
        assert_eq!(sub.is_subscribe(), subscription);
        assert_eq!(sub.is_unsubscribe(), !subscription);
        assert_eq!(flags.as_ref().unwrap().recv_from, sub.get_recv_from());
        assert_eq!(flags.as_ref().unwrap().forward_to, sub.get_forward_to());
        assert_eq!(None, sub.try_get_incoming_conn());
        assert_eq!(source, sub.get_source());
        let got_name = sub.get_dst();
        assert_eq!(dst, got_name);
    }

    fn test_publish_template(source: Name, dst: Name, flags: Option<SlimHeaderFlags>) {
        let pub_msg = ProtoMessage::new_publish(
            &source,
            &dst,
            flags.clone(),
            "str",
            "this is the content of the message".into(),
        );

        let flags = if flags.is_none() {
            Some(SlimHeaderFlags::default())
        } else {
            flags
        };

        assert!(pub_msg.is_publish());
        assert!(!pub_msg.is_subscribe());
        assert!(!pub_msg.is_unsubscribe());
        assert_eq!(flags.as_ref().unwrap().recv_from, pub_msg.get_recv_from());
        assert_eq!(flags.as_ref().unwrap().forward_to, pub_msg.get_forward_to());
        assert_eq!(None, pub_msg.try_get_incoming_conn());
        assert_eq!(source, pub_msg.get_source());
        let got_name = pub_msg.get_dst();
        assert_eq!(dst, got_name);
        assert_eq!(flags.as_ref().unwrap().fanout, pub_msg.get_fanout());
    }

    #[test]
    fn test_subscription() {
        let source = Name::from_strings(["org", "ns", "type"]).with_id(1);
        let dst = Name::from_strings(["org", "ns", "type"]).with_id(2);

        // simple
        test_subscription_template(true, source.clone(), dst.clone(), None);

        // with name id
        test_subscription_template(true, source.clone(), dst.clone(), None);

        // with recv from
        test_subscription_template(
            true,
            source.clone(),
            dst.clone(),
            Some(SlimHeaderFlags::default().with_recv_from(50)),
        );

        // with forward to
        test_subscription_template(
            true,
            source.clone(),
            dst.clone(),
            Some(SlimHeaderFlags::default().with_forward_to(30)),
        );
    }

    #[test]
    fn test_unsubscription() {
        let source = Name::from_strings(["org", "ns", "type"]).with_id(1);
        let dst = Name::from_strings(["org", "ns", "type"]).with_id(2);

        // simple
        test_subscription_template(false, source.clone(), dst.clone(), None);

        // with name id
        test_subscription_template(false, source.clone(), dst.clone(), None);

        // with recv from
        test_subscription_template(
            false,
            source.clone(),
            dst.clone(),
            Some(SlimHeaderFlags::default().with_recv_from(50)),
        );

        // with forward to
        test_subscription_template(
            false,
            source.clone(),
            dst.clone(),
            Some(SlimHeaderFlags::default().with_forward_to(30)),
        );
    }

    #[test]
    fn test_publish() {
        let source = Name::from_strings(["org", "ns", "type"]).with_id(1);
        let mut dst = Name::from_strings(["org", "ns", "type"]);

        // simple
        test_publish_template(
            source.clone(),
            dst.clone(),
            Some(SlimHeaderFlags::default()),
        );

        // with name id
        dst.set_id(2);
        test_publish_template(
            source.clone(),
            dst.clone(),
            Some(SlimHeaderFlags::default()),
        );
        dst.reset_id();

        // with recv from
        test_publish_template(
            source.clone(),
            dst.clone(),
            Some(SlimHeaderFlags::default().with_recv_from(50)),
        );

        // with forward to
        test_publish_template(
            source.clone(),
            dst.clone(),
            Some(SlimHeaderFlags::default().with_forward_to(30)),
        );

        // with fanout
        test_publish_template(
            source.clone(),
            dst.clone(),
            Some(SlimHeaderFlags::default().with_fanout(2)),
        );
    }

    #[test]
    fn test_conversions() {
        // Name to ProtoName
        let name = Name::from_strings(["org", "ns", "type"]).with_id(1);
        let proto_name = ProtoName::from(&name);

        assert_eq!(proto_name.component_0, name.components()[0]);
        assert_eq!(proto_name.component_1, name.components()[1]);
        assert_eq!(proto_name.component_2, name.components()[2]);
        assert_eq!(proto_name.component_3, name.components()[3]);

        // ProtoName to Name
        let name_from_proto = Name::from(&proto_name);
        assert_eq!(name_from_proto.components()[0], proto_name.component_0);
        assert_eq!(name_from_proto.components()[1], proto_name.component_1);
        assert_eq!(name_from_proto.components()[2], proto_name.component_2);
        assert_eq!(name_from_proto.components()[3], proto_name.component_3);

        // ProtoMessage to ProtoSubscribe
        let dst = Name::from_strings(["org", "ns", "type"]).with_id(1);
        let proto_subscribe = ProtoMessage::new_subscribe(
            &name,
            &dst,
            Some(
                SlimHeaderFlags::default()
                    .with_recv_from(2)
                    .with_forward_to(3),
            ),
        );
        let proto_subscribe = ProtoSubscribe::from(proto_subscribe);
        assert_eq!(proto_subscribe.header.as_ref().unwrap().get_source(), name);
        assert_eq!(proto_subscribe.header.as_ref().unwrap().get_dst(), dst,);

        // ProtoMessage to ProtoUnsubscribe
        let proto_unsubscribe = ProtoMessage::new_unsubscribe(
            &name,
            &dst,
            Some(
                SlimHeaderFlags::default()
                    .with_recv_from(2)
                    .with_forward_to(3),
            ),
        );
        let proto_unsubscribe = ProtoUnsubscribe::from(proto_unsubscribe);
        assert_eq!(
            proto_unsubscribe.header.as_ref().unwrap().get_source(),
            name
        );
        assert_eq!(proto_unsubscribe.header.as_ref().unwrap().get_dst(), dst);

        // ProtoMessage to ProtoPublish
        let proto_publish = ProtoMessage::new_publish(
            &name,
            &dst,
            Some(
                SlimHeaderFlags::default()
                    .with_recv_from(2)
                    .with_forward_to(3),
            ),
            "str",
            "this is the content of the message".into(),
        );
        let proto_publish = ProtoPublish::from(proto_publish);
        assert_eq!(proto_publish.header.as_ref().unwrap().get_source(), name);
        assert_eq!(proto_publish.header.as_ref().unwrap().get_dst(), dst);
    }

    #[test]
    fn test_panic() {
        let source = Name::from_strings(["org", "ns", "type"]).with_id(1);
        let dst = Name::from_strings(["org", "ns", "type"]).with_id(2);

        // panic if SLIM header is not found
        let msg = ProtoMessage::new_subscribe(
            &source,
            &dst,
            Some(
                SlimHeaderFlags::default()
                    .with_recv_from(2)
                    .with_forward_to(3),
            ),
        );

        // let's try to convert it to a unsubscribe
        // this should panic because the message type is not unsubscribe
        let result = std::panic::catch_unwind(|| ProtoUnsubscribe::from(msg.clone()));
        assert!(result.is_err());

        // try to convert to publish
        // this should panic because the message type is not publish
        let result = std::panic::catch_unwind(|| ProtoPublish::from(msg.clone()));
        assert!(result.is_err());

        // finally make sure the conversion to subscribe works
        let result = std::panic::catch_unwind(|| ProtoSubscribe::from(msg));
        assert!(result.is_ok());
    }

    #[test]
    fn test_panic_header() {
        // create a unusual SLIM header
        let header = SlimHeader {
            source: None,
            destination: None,
            fanout: 0,
            recv_from: None,
            forward_to: None,
            incoming_conn: None,
            error: None,
        };

        // the operations to retrieve source and destination should fail with panic
        let result = std::panic::catch_unwind(|| header.get_source());
        assert!(result.is_err());

        let result = std::panic::catch_unwind(|| header.get_dst());
        assert!(result.is_err());

        // The operations to retrieve recv_from and forward_to should not fail with panic
        let result = std::panic::catch_unwind(|| header.get_recv_from());
        assert!(result.is_ok());

        let result = std::panic::catch_unwind(|| header.get_forward_to());
        assert!(result.is_ok());

        // The operations to retrieve incoming_conn should not fail with panic
        let result = std::panic::catch_unwind(|| header.get_incoming_conn());
        assert!(result.is_ok());

        // The operations to retrieve error should not fail with panic
        let result = std::panic::catch_unwind(|| header.get_error());
        assert!(result.is_ok());
    }

    #[test]
    fn test_panic_session_header() {
        // create a unusual session header
        let header = SessionHeader::new(0, 0, 0, 0, &None, &None);

        // the operations to retrieve session_id and message_id should not fail with panic
        let result = std::panic::catch_unwind(|| header.get_session_id());
        assert!(result.is_ok());

        let result = std::panic::catch_unwind(|| header.get_message_id());
        assert!(result.is_ok());
    }

    #[test]
    fn test_panic_proto_message() {
        // create a unusual proto message
        let message = ProtoMessage {
            metadata: HashMap::new(),
            message_type: None,
        };

        // the operation to retrieve the header should fail with panic
        let result = std::panic::catch_unwind(|| message.get_slim_header());
        assert!(result.is_err());

        // the operation to retrieve the message type should fail with panic
        let result = std::panic::catch_unwind(|| message.get_type());
        assert!(result.is_err());

        // all the other ops should fail with panic as well as the header is not set
        let result = std::panic::catch_unwind(|| message.get_source());
        assert!(result.is_err());
        let result = std::panic::catch_unwind(|| message.get_dst());
        assert!(result.is_err());
        let result = std::panic::catch_unwind(|| message.get_recv_from());
        assert!(result.is_err());
        let result = std::panic::catch_unwind(|| message.get_forward_to());
        assert!(result.is_err());
        let result = std::panic::catch_unwind(|| message.get_incoming_conn());
        assert!(result.is_err());
        let result = std::panic::catch_unwind(|| message.get_fanout());
        assert!(result.is_err());
    }

    #[test]
    fn test_service_type_to_int() {
        // Get total number of service types
        let total_service_types = SessionMessageType::ChannelMlsAck as i32;

        for i in 0..total_service_types {
            // int -> ServiceType
            let service_type =
                SessionMessageType::try_from(i).expect("failed to convert int to service type");
            let service_type_int = i32::from(service_type);
            assert_eq!(service_type_int, i32::from(service_type),);
        }

        // Test invalid conversion
        let invalid_service_type = SessionMessageType::try_from(total_service_types + 1);
        assert!(invalid_service_type.is_err());
    }
}
