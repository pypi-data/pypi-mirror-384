use std::io;

use process_corpus::{self, LemmaToken};
use saldo::SaldoLexicon;

use crate::SourceFormat;

pub trait WSDApplication {
    fn disambiguate_text(
        &self,
        text: Vec<Vec<LemmaToken>>,
    ) -> Vec<(Vec<LemmaToken>, Vec<Option<Vec<f32>>>)> {
        let mut out = Vec::with_capacity(text.len());
        for sen in text {
            out.push(self.disambiguate_sentence(sen));
        }
        out
    }
    fn disambiguate_sentence(
        &self,
        lts: Vec<LemmaToken>,
    ) -> (Vec<LemmaToken>, Vec<Option<Vec<f32>>>) {
        let mut disamb = Vec::with_capacity(lts.len());
        for i in 0..lts.len() {
            disamb.push(self.disambiguate(&lts, i));
        }
        (lts, disamb)
    }
    fn disambiguate(&self, lts: &[LemmaToken], i: usize) -> Option<Vec<f32>>;
}

pub type SharedWSDApplication = Box<dyn WSDApplication>;

pub fn evaluate(_wsd: impl WSDApplication, _eval_lemmas_file: &str, _eval_key_file: &str) {
    todo!("evaluate is not yet supported")
}

impl WSDApplication for SharedWSDApplication {
    fn disambiguate(&self, lts: &[LemmaToken], i: usize) -> Option<Vec<f32>> {
        self.as_ref().disambiguate(lts, i)
    }
}

pub fn read_sentences(
    reader: &mut dyn io::BufRead,
    _saldo: Option<&SaldoLexicon>,
    sbxml: bool,
    batch_size: usize,
    _split_mwes: bool,
    _split_compounds: bool,
) -> io::Result<Vec<Vec<LemmaToken>>> {
    let mut out = Vec::new();
    while out.len() < batch_size {
        if sbxml {
            todo!("sbxml format is not yet supported")
        } else {
            let lts = match process_corpus::read_lemma_tokens(reader)? {
                Some(lts) => lts,
                None => return Ok(out),
            };
            out.push(lts);
        }
    }
    Ok(out)
}

#[derive(Debug, Copy, Clone)]
pub struct DisambiguateOptions {
    pub batch_size: usize,
    pub max_sen: usize,
}

impl Default for DisambiguateOptions {
    fn default() -> Self {
        Self {
            batch_size: 1,
            max_sen: u32::MAX as usize,
        }
    }
}
pub fn disambiguate_sentences(
    wsd: impl WSDApplication,
    reader: &mut dyn io::BufRead,
    out: &mut dyn io::Write,
    f: &dyn SourceFormat,
    DisambiguateOptions {
        batch_size,
        max_sen,
    }: DisambiguateOptions,
) -> io::Result<()> {
    let mut total_sentences = 0;
    let mut next_print = 100000;

    loop {
        let text = f.read_sentences(
            reader,
            // saldo.as_ref(),
            // args.sbxml,
            batch_size,
            // args.split_mwes,
            // args.split_compounds,
        )?;
        // log::trace!(&text);
        if text.is_empty() {
            break;
        }
        total_sentences += text.len();
        if total_sentences > next_print {
            log::info!("{}", next_print);
            next_print += 100000;
        }

        // if !args.for_lemma.is_none() {
        //     todo!("forLemma not supported yet");
        // } else {
        let result = wsd.disambiguate_text(text);
        for p in result {
            for i in 0..p.0.len() {
                write!(out, "{}\t", &p.0[i])?;
                match &p.1[i] {
                    None => writeln!(out, "_")?,
                    Some(scores) => writeln!(out, "{}", join_to_string(scores))?,
                }
            }
            writeln!(out,)?;
        }

        if total_sentences >= max_sen {
            break;
        }
    }
    // }

    // if !args.for_lemma.is_none() {
    //     todo!("printRatios(ratios)");
    // }
    Ok(())
}
fn join_to_string(vs: &[f32]) -> String {
    if vs.is_empty() {
        return String::new();
    }
    let mut out = String::with_capacity(vs.len() * 2);
    out.push_str(&vs[0].to_string());
    for v in &vs[1..] {
        out.push_str(&format!("|{}", v));
    }
    out
}
