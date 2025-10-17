use std::{borrow::Borrow, fmt};

use crate::saldo_entry::SaldoId;

#[derive(Debug, Clone, Hash, PartialEq, Eq, PartialOrd, Ord)]
pub struct SaldoLemgramId(String);

impl fmt::Display for SaldoLemgramId {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(&self.0)
    }
}

impl Borrow<String> for SaldoLemgramId {
    fn borrow(&self) -> &String {
        &self.0
    }
}

impl SaldoLemgramId {
    pub fn new(s: impl Into<String>) -> Self {
        Self(s.into())
    }

    pub fn as_str(&self) -> &str {
        self.0.as_str()
    }
}

#[derive(Debug, Clone, Hash, PartialEq, Eq)]
pub struct SaldoLemgram {
    id: SaldoLemgramId,
    pos: String,
    para: Option<String>,
    wf: String,
    entries: Vec<SaldoId>,
}

impl SaldoLemgram {
    pub fn new(id: SaldoLemgramId, pos: String, para: Option<String>, wf: String) -> Self {
        Self {
            id,
            pos,
            para,
            wf,
            entries: Vec::new(),
        }
    }
    pub fn pos(&self) -> &str {
        self.pos.as_str()
    }
    pub fn add_entry(&mut self, saldo_id: &SaldoId) {
        self.entries.push(saldo_id.clone());
    }
}
