mod tab_format;

use std::io;

use process_corpus::LemmaToken;

pub use self::tab_format::TabFormat;

pub trait SourceFormat {
    fn read_sentences(
        &self,
        reader: &mut dyn io::BufRead,
        batch_size: usize,
    ) -> std::io::Result<Vec<Vec<LemmaToken>>>;
}

impl SourceFormat for Box<dyn SourceFormat> {
    fn read_sentences(
        &self,
        reader: &mut dyn io::BufRead,
        batch_size: usize,
    ) -> std::io::Result<Vec<Vec<LemmaToken>>> {
        self.as_ref().read_sentences(reader, batch_size)
    }
}
