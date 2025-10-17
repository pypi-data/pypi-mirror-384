use std::{env, fs, io};

use rstest::{fixture, rstest};

use wsd_application::{
    SharedWSDApplication, TabFormat, VectorWSD, VectorWSDConfig,
    wsd_application::{DisambiguateOptions, disambiguate_sentences},
};

#[fixture]
fn sense_model() -> &'static str {
    "assets/sparv-wsd/models/scouse/ALL_512_128_w10_A2_140403_ctx1.bin"
}

#[fixture]
fn context_model() -> &'static str {
    "assets/sparv-wsd/models/scouse/lem_cbow0_s512_w10_NEW2_ctx.bin"
}
#[fixture]
fn vector_wsd(sense_model: &str, context_model: &str) -> SharedWSDApplication {
    println!("sense_model='{}'", sense_model);
    println!("context_model='{}'", context_model);

    VectorWSD::new_as_shared(
        sense_model,
        context_model,
        VectorWSDConfig {
            decay: true,
            s1prior: 1.0,
            context_width: 10,
        },
    )
    .expect("VectorWSD created")
}

#[rstest]
fn test_vector_wsd(vector_wsd: SharedWSDApplication) -> eyre::Result<()> {
    let mut reader = io::BufReader::new(fs::File::open("assets/testing/example1.in.txt")?);
    let mut out = Vec::new();
    disambiguate_sentences(
        vector_wsd,
        &mut reader,
        &mut out,
        &TabFormat::default(),
        DisambiguateOptions::default(),
    )?;

    let actual = String::from_utf8(out)?;
    let actual: Vec<&str> = actual.split('\n').collect();
    insta::assert_debug_snapshot!(actual);
    Ok(())
}
