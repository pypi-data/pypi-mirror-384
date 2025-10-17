use std::{
    fs, io,
    path::{Path, PathBuf},
};

use hashbrown::HashMap;
use parser_callback::SaldoParserCallback;

use crate::{
    saldo_entry::{SaldoEntry, SaldoId},
    shared::xml_reader::XmlReader,
};

mod parser_callback;

#[derive(Debug, Clone)]
pub struct SaldoLexicon {
    entries: HashMap<SaldoId, SaldoEntry>,
}

pub const PRIM: &str = "PRIM..1";

#[derive(Debug, thiserror::Error, miette::Diagnostic)]
pub enum SaldoLexiconError {
    #[error("no mfid for {0}")]
    NoMfidForEntry(SaldoId),
    #[error("did not find mfid {0}")]
    NoSuchMfid(String),
    #[error("Failed to open file '{path}'")]
    FailedToOpenFile { path: PathBuf, source: io::Error },
}
impl SaldoLexicon {
    pub fn new(filename: impl AsRef<Path>) -> Result<Self, SaldoLexiconError> {
        log::debug!("Reading dictionary ...");
        let file =
            fs::File::open(&filename).map_err(|source| SaldoLexiconError::FailedToOpenFile {
                path: filename.as_ref().into(),
                source,
            })?;
        let file_ext = filename
            .as_ref()
            .extension()
            .map(|ext| ext.to_string_lossy());
        log::trace!("File extension: '{:?}'", &file_ext);
        let reader = if file_ext.as_deref() == Some("gz") {
            log::debug!("reading gzip file");
            let decoder = Box::new(flate2::read::GzDecoder::new(file)) as Box<dyn io::Read>;
            io::BufReader::new(decoder)
        } else {
            let file = Box::new(file) as Box<dyn io::Read>;
            io::BufReader::new(file)
        };
        let content_handler = SaldoParserCallback::new();
        let mut reader = XmlReader::new(reader, content_handler);
        reader.parse();
        log::debug!(" Done.");
        let SaldoParserCallback {
            all_entries,
            mut entries,
            mfids,
            pfids,
            ..
        } = reader.into_inner();
        log::debug!("Building graph ...");
        for entry_id in all_entries {
            // let Some(e_id) = mfids.get(e.read().unwrap().get_id() {

            //     }
            if let Some(mfid) = mfids.get(&entry_id) {
                if let Some(mf) = entries.get_mut(mfid) {
                    mf.add_inv_mf(entry_id.clone());
                } else {
                    return Err(SaldoLexiconError::NoSuchMfid(mfid.into()));
                }
                if let Some(e) = entries.get_mut(&entry_id) {
                    e.set_mf(SaldoId::new(mfid));
                }
            } else {
                if entry_id.as_str() != PRIM {
                    return Err(SaldoLexiconError::NoMfidForEntry(entry_id));
                }
            }
            if let Some(pfid_set) = pfids.get(&entry_id) {
                for pfid in pfid_set {
                    if pfid != PRIM {
                        if let Some(pf) = entries.get_mut(pfid) {
                            pf.add_inv_pf(entry_id.clone());
                        } else {
                            return Err(SaldoLexiconError::NoSuchMfid(pfid.into()));
                        }
                        if let Some(e) = entries.get_mut(&entry_id) {
                            e.add_pf(SaldoId::new(pfid));
                        }
                    }
                }
            }
        }
        log::info!("full size: {}", entries.len());
        log::info!(" Done.");
        Ok(Self { entries })
    }
}
