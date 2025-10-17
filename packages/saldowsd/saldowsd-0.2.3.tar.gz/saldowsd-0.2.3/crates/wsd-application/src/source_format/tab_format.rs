use process_corpus::{self, LemmaToken};

use super::SourceFormat;

#[derive(Debug, Default)]
pub struct TabFormat {}

impl TabFormat {}

impl SourceFormat for TabFormat {
    fn read_sentences(
        &self,
        reader: &mut dyn std::io::BufRead,
        batch_size: usize,
    ) -> std::io::Result<Vec<Vec<LemmaToken>>> {
        let mut out = Vec::new();
        while out.len() < batch_size {
            match process_corpus::read_lemma_tokens(reader)? {
                Some(lts) => out.push(lts),
                None => return Ok(out),
            };
        }
        Ok(out)
    }
}
