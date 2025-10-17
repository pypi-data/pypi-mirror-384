// SPDX-FileCopyrightText: Copyright (c) 2025 Cisco and/or its affiliates.
// SPDX-License-Identifier: Apache-2.0

// Standard library imports
use std::collections::HashMap;

// Third-party crates
use slim_datapath::{api::ProtoMessage as Message, messages::Name};

pub struct ProducerBuffer {
    capacity: usize,
    next: usize,
    buffer: Vec<Option<Message>>,
    map: HashMap<usize, usize>,
    destination_name: Name,
    destination_id: Option<u64>,
}

impl ProducerBuffer {
    /// Create a buffer with a given capacity
    pub fn with_capacity(capacity: usize) -> Self {
        ProducerBuffer {
            capacity,
            next: 0,
            buffer: vec![None; capacity],
            map: HashMap::new(),
            destination_name: Name::from_strings(["unknown", "unknown", "unknown"]),
            destination_id: None,
        }
    }

    pub fn get_capacity(&self) -> usize {
        self.capacity
    }

    pub fn get_destination_name(&self) -> &Name {
        &self.destination_name
    }

    pub fn get_destination_id(&self) -> Option<u64> {
        self.destination_id
    }

    /// Add message to the buffer.
    /// return true if the insertion completes
    pub fn push(&mut self, msg: Message) -> bool {
        // if map is empty init the destination name
        if self.map.is_empty() {
            self.destination_name = msg.get_dst();
        }

        // get message id
        let id = msg.get_id() as usize;

        // check if the message is already there
        // if yes return
        if self.map.contains_key(&id) {
            return true;
        }

        // remove the message at position next from the map
        // the same message will be overwritten in the buffer
        if let Some(message) = &self.buffer[self.next] {
            let to_remove = message.get_id() as usize;
            self.map.remove(&to_remove);
        }

        // store the new message
        self.buffer[self.next] = Some(msg);
        // store the position of the message in the buffer
        self.map.insert(id, self.next);
        // increase the index to the next element in the buffer
        self.next = (self.next + 1) % self.capacity;
        true
    }

    /// Remove all the elements in the buffer
    pub fn clear(&mut self) {
        self.buffer = vec![None; self.capacity];
        self.next = 0;
        self.map.clear();
    }

    pub fn get(&self, id: usize) -> Option<Message> {
        match self.map.get(&id) {
            None => None,
            Some(index) => self.buffer[*index].clone(),
        }
    }

    pub fn iter(&self) -> impl Iterator<Item = &Message> {
        self.buffer.iter().filter_map(|msg| {
            // If message is Some(msg), it unwraps and return &msg.
            // Skip it otherwise
            msg.as_ref()
        })
    }
}

// tests
#[cfg(test)]
mod tests {
    use super::*;
    use slim_datapath::api::{
        ProtoSessionMessageType as SessionMessageType, ProtoSessionType as SessionType,
        SessionHeader, SlimHeader,
    };
    use slim_datapath::messages::encoder::Name;

    #[test]
    fn test_producer_buffer() {
        let mut buffer = ProducerBuffer::with_capacity(3);

        assert_eq!(buffer.get_capacity(), 3);

        let src = Name::from_strings(["org", "ns", "type"]).with_id(0);
        let name_type = Name::from_strings(["org", "ns", "type"]).with_id(1);

        let slim_header = SlimHeader::new(&src, &name_type, None);

        let h0 = SessionHeader::new(
            SessionType::SessionUnknown.into(),
            SessionMessageType::P2PMsg.into(),
            0,
            0,
            &None,
            &None,
        );
        let h1 = SessionHeader::new(
            SessionType::SessionUnknown.into(),
            SessionMessageType::P2PMsg.into(),
            0,
            1,
            &None,
            &None,
        );
        let h2 = SessionHeader::new(
            SessionType::SessionUnknown.into(),
            SessionMessageType::P2PMsg.into(),
            0,
            2,
            &None,
            &None,
        );
        let h3 = SessionHeader::new(
            SessionType::SessionUnknown.into(),
            SessionMessageType::P2PMsg.into(),
            0,
            3,
            &None,
            &None,
        );
        let h4 = SessionHeader::new(
            SessionType::SessionUnknown.into(),
            SessionMessageType::P2PMsg.into(),
            0,
            4,
            &None,
            &None,
        );

        let p0 = Message::new_publish_with_headers(Some(slim_header), Some(h0), "", vec![]);
        let p1 = Message::new_publish_with_headers(Some(slim_header), Some(h1), "", vec![]);
        let p2 = Message::new_publish_with_headers(Some(slim_header), Some(h2), "", vec![]);
        let p3 = Message::new_publish_with_headers(Some(slim_header), Some(h3), "", vec![]);
        let p4 = Message::new_publish_with_headers(Some(slim_header), Some(h4), "", vec![]);

        assert!(buffer.push(p0.clone()));

        assert_eq!(buffer.get(0).unwrap(), p0);
        assert_eq!(buffer.get(0).unwrap(), p0);
        assert_eq!(buffer.get(0).unwrap(), p0);
        assert_eq!(buffer.get(1), None);

        assert!(buffer.push(p0.clone()));
        assert!(buffer.push(p1.clone()));
        assert!(buffer.push(p2.clone()));

        assert_eq!(buffer.get(0).unwrap(), p0);
        assert_eq!(buffer.get(1).unwrap(), p1);
        assert_eq!(buffer.get(2).unwrap(), p2);
        assert_eq!(buffer.get(3), None);

        // now the buffer is full, add a new element will remote the elem 0
        assert!(buffer.push(p3.clone()));
        assert_eq!(buffer.get(0), None);
        assert_eq!(buffer.get(1).unwrap(), p1);
        assert_eq!(buffer.get(2).unwrap(), p2);
        assert_eq!(buffer.get(3).unwrap(), p3);
        assert_eq!(buffer.get(4), None);

        // now the buffer is full, add a new element will remote the elem 1
        assert!(buffer.push(p4.clone()));
        assert_eq!(buffer.get(0), None);
        assert_eq!(buffer.get(1), None);
        assert_eq!(buffer.get(2).unwrap(), p2);
        assert_eq!(buffer.get(3).unwrap(), p3);
        assert_eq!(buffer.get(4).unwrap(), p4);

        // remove all elements
        buffer.clear();
        assert_eq!(buffer.get(0), None);
        assert_eq!(buffer.get(1), None);
        assert_eq!(buffer.get(2), None);
        assert_eq!(buffer.get(3), None);
        assert_eq!(buffer.get(4), None);

        // add all msgs and check again
        assert!(buffer.push(p0.clone()));
        assert!(buffer.push(p1.clone()));
        assert!(buffer.push(p2.clone()));
        assert!(buffer.push(p3.clone()));
        assert!(buffer.push(p4.clone()));
        assert_eq!(buffer.get(0), None);
        assert_eq!(buffer.get(1), None);
        assert_eq!(buffer.get(2).unwrap(), p2);
        assert_eq!(buffer.get(3).unwrap(), p3);
        assert_eq!(buffer.get(4).unwrap(), p4);
    }

    #[test]
    fn test_iter_producer_buffer() {
        let src = Name::from_strings(["org", "ns", "type"]).with_id(0);
        let name_type = Name::from_strings(["org", "ns", "type"]).with_id(1);

        let slim_header = SlimHeader::new(&src, &name_type, None);
        let h = SessionHeader::new(
            SessionType::SessionUnknown.into(),
            SessionMessageType::P2PMsg.into(),
            0,
            0,
            &None,
            &None,
        );
        let mut p = Message::new_publish_with_headers(Some(slim_header), Some(h), "", vec![]);

        let mut b = ProducerBuffer::with_capacity(30);
        b.push(p.clone()); // add 0
        p.set_message_id(1);
        b.push(p.clone()); // add 1
        p.set_message_id(2);
        b.push(p.clone()); // add 2
        p.set_message_id(5);
        b.push(p.clone()); // add 5
        p.set_message_id(6);
        b.push(p.clone()); // add 6
        p.set_message_id(10);
        b.push(p.clone()); // add 10

        let expected = [0, 1, 2, 5, 6, 10];

        for (i, m) in b.iter().enumerate() {
            assert_eq!(m.get_id(), expected[i]);
        }
    }
}
