use std::{
    fs::File,
    io::{BufRead, BufReader},
};

use process_corpus::LemmaToken;

#[test]
fn test_lemma_tokens() -> eyre::Result<()> {
    let reader = BufReader::new(File::open("assets/testing/example1.in.txt")?);
    let actual: Vec<LemmaToken> = reader
        .lines()
        .map(|line| LemmaToken::parse_line(&line.unwrap()))
        .collect();

    insta::assert_debug_snapshot!(actual);
    Ok(())
}
