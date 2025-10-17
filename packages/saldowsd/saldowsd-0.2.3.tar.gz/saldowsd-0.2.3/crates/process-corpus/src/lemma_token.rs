use std::fmt;

#[derive(Debug, Clone, Default)]
pub struct LemmaToken {
    possible_senses: Vec<String>,
    possible_lemmas: Vec<String>,
    is_prefix: bool,
    is_suffix: bool,
    // possible_lemgrams: Vec<String>,
}

impl LemmaToken {
    pub fn parse_line(line: &str) -> Self {
        let xs: Vec<&str> = line.split('\t').collect();
        let mut out = Self::default();
        if xs[4] != "_" {
            for s in xs[4].split("|") {
                out.possible_lemmas.push(s.to_string());
            }
        }
        if xs[5] != "_" {
            for s in xs[5].split("|") {
                out.possible_senses.push(s.to_string());
            }
        }
        out
    }
    pub fn possible_senses(&self) -> &[String] {
        &self.possible_senses
    }
    pub fn possible_lemmas(&self) -> &[String] {
        &self.possible_lemmas
    }
}

impl fmt::Display for LemmaToken {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        // if self.nodes.len() == 0 {
        f.write_str("_\t")?;
        // } else {
        // for n in &self.nodes {
        // todo!("n.position");
        // }
        // }
        // // if self.nodes.len() == 0 {
        f.write_str("_\t")?;
        // } else {
        // for n in &self.nodes {
        // todo!("n.word");
        // }
        // }
        if self.is_prefix {
            f.write_str("(pfx)\t")?;
        } else if self.is_suffix {
            f.write_str("(sfx)\t")?;
        } else {
            f.write_str("_\t")?;
        }

        // if self.possible_lemgrams.len() > 0 {
        //     f.write_fmt(format_args!("{}\t",self.possible_lemgrams.join("|")))?;
        // } else {
        f.write_str("_\t")?;
        // }

        if !self.possible_lemmas.is_empty() {
            f.write_fmt(format_args!("{}\t", self.possible_lemmas.join("|")))?;
        } else {
            f.write_str("_\t")?;
        }

        if !self.possible_senses.is_empty() {
            f.write_fmt(format_args!("{}", self.possible_senses.join("|")))?;
        } else {
            f.write_str("_")?;
        }
        Ok(())
    }
}
