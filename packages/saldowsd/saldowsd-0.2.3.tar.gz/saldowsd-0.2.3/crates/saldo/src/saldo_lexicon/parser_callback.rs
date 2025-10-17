use hashbrown::{HashMap, HashSet};

use crate::{
    saldo_entry::{SaldoEntry, SaldoEntryBuilder, SaldoId},
    saldo_lemgram::{SaldoLemgram, SaldoLemgramId},
    shared::xml_reader::{AttributeMap, ContentHandler},
};

#[derive(Debug, Clone, Default)]
pub struct SaldoParserCallback {
    pub curr_entry: Option<SaldoEntryBuilder>,
    pub curr_pos: Option<String>,
    pub curr_lemgram_id: Option<String>,
    pub curr_para: Option<String>,
    pub curr_wf: Option<String>,
    pub curr_relation_target: Option<String>,
    pub all_entries: Vec<SaldoId>,
    pub entries: HashMap<SaldoId, SaldoEntry>,
    pub mfids: HashMap<SaldoId, String>,
    pub pfids: HashMap<SaldoId, HashSet<String>>,
    pub lemgrams: HashMap<SaldoLemgramId, SaldoLemgram>,
    pub lemgrams_by_lemma: HashMap<String, SaldoLemgramId>,
}

impl SaldoParserCallback {
    pub fn new() -> Self {
        Self::default()
    }
}

impl ContentHandler for SaldoParserCallback {
    fn start_element(&mut self, name: &[u8], attributes: AttributeMap) {
        match name {
            b"LexicalEntry" => {
                self.curr_entry = Some(SaldoEntryBuilder::default());
            }
            b"Sense" => {
                if let Some(entry) = &mut self.curr_entry {
                    let id = String::from_utf8(attributes.get(&b"id"[..]).unwrap().to_vec())
                        .expect("valid attr");
                    if entry.get_id().is_some() {
                        todo!("handle sense id already exists")
                    }
                    let id = SaldoId::new(id);
                    entry.set_id(id);
                } else {
                    todo!("handle no curr_entry");
                }
            }
            b"SenseRelation" => {
                self.curr_relation_target = Some(
                    String::from_utf8(attributes.get(&b"targets"[..]).unwrap().to_vec())
                        .expect("valid attr"),
                );
            }
            b"feat" => match attributes.get(&b"att"[..]).map(|s| s.as_ref()) {
                Some(b"label") => {
                    if let Some(entry) = &mut self.curr_entry {
                        let Some(entry_id) = entry.get_id() else {
                            todo!("handle sense id is missing")
                        };
                        let Some(curr_relation_target) = self.curr_relation_target.take() else {
                            todo!("handle")
                        };
                        let rel_type =
                            std::str::from_utf8(attributes.get(&b"val"[..]).unwrap().as_ref())
                                .expect("valid attr");
                        if rel_type == "primary" {
                            if self.mfids.contains_key(entry_id) {
                                todo!("handle entry_id = {} already exists", entry_id);
                            }
                            self.mfids.insert(entry_id.clone(), curr_relation_target);
                        } else if rel_type == "secondary" {
                            self.pfids
                                .entry(entry_id.clone())
                                .or_default()
                                .insert(curr_relation_target);
                        }
                    } else {
                        todo!("handle no curr_entry");
                    }
                }
                Some(b"language") => (),
                Some(b"languageCoding") => (),
                Some(b"lemgram") => {
                    self.curr_lemgram_id =
                        Some(String::from_utf8(attributes[&b"val"[..]].to_vec()).unwrap())
                }
                Some(b"paradigm") => {
                    self.curr_para =
                        Some(String::from_utf8(attributes[&b"val"[..]].to_vec()).unwrap())
                }
                Some(b"partOfSpeech") => {
                    self.curr_pos =
                        Some(String::from_utf8(attributes[&b"val"[..]].to_vec()).unwrap())
                }
                Some(b"writtenForm") => {
                    self.curr_wf =
                        Some(String::from_utf8(attributes[&b"val"[..]].to_vec()).unwrap())
                }
                Some(x) => todo!("handle att='{}'", String::from_utf8_lossy(x)),
                None => todo!("handle att is missing"),
            },
            _ => (),
        }
    }
    fn end_element(&mut self, name: &[u8]) {
        match name {
            b"LexicalEntry" => {
                if let Some(entry_builder) = self.curr_entry.take() {
                    match entry_builder.build() {
                        Ok(entry) => {
                            let entry_id = entry.get_id().clone();
                            self.all_entries.push(entry_id.clone());
                            self.entries.insert(entry_id, entry);
                        }
                        Err(err) => todo!("handle error={:?}", err),
                    }
                }
            }
            b"FormRepresentation" => {
                let Some(lemgram_id) = self.curr_lemgram_id.take() else {
                    todo!("missing lemgram_id");
                };
                let lemgram_id = SaldoLemgramId::new(lemgram_id);
                let Some(curr_pos) = self.curr_pos.take() else {
                    todo!("missing pos");
                };
                if let Some(curr_entry) = self.curr_entry.as_mut() {
                    if let Some(sl) = self.lemgrams.get_mut(&lemgram_id) {
                        if sl.pos() != curr_pos {
                            todo!("incompatible POS tags");
                        }
                        curr_entry.add_lemgram(&lemgram_id);
                        if let Some(curr_entry_id) = curr_entry.get_id() {
                            sl.add_entry(curr_entry_id);
                        }
                    } else {
                        let Some(wf) = self.curr_wf.take() else {
                            todo!("no wf: {}", lemgram_id);
                        };
                        let mut sl = SaldoLemgram::new(
                            lemgram_id.clone(),
                            curr_pos,
                            self.curr_para.take(),
                            wf.clone(),
                        );
                        if let Some(curr_entry_id) = curr_entry.get_id() {
                            sl.add_entry(curr_entry_id);
                        }
                        self.lemgrams.insert(lemgram_id.clone(), sl);
                        curr_entry.add_lemgram(&lemgram_id);
                        self.lemgrams_by_lemma.insert(wf, lemgram_id);
                    }
                }
            }
            _ => (),
        }
    }
}
