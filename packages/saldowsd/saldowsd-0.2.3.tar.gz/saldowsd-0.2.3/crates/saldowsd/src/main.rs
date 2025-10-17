use std::io;

use clap::Parser;
use log::LevelFilter;
use miette::IntoDiagnostic;
use options::Args;
use wsd_application::{
    SourceFormat, TabFormat, VectorWSD, VectorWSDConfig,
    wsd_application::{DisambiguateOptions, disambiguate_sentences},
};

use crate::options::{AppNames, Format};

mod options;

fn main() -> miette::Result<()> {
    let args = Args::parse();

    configure_logging(args.verbose);

    // let saldo = match &args.saldo {
    //     None => None,
    //     Some(saldo_file) => Some(SaldoLexicon::new(saldo_file)?),
    // };

    // FIXME: use new_as_shared if more apps are included
    let wsd = match args.app_name {
        AppNames::VectorWSD {
            decay,
            s1_prior,
            context_width,
            sv_file,
            cv_file,
        } => VectorWSD::new(
            &sv_file,
            &cv_file,
            VectorWSDConfig {
                decay,
                s1prior: s1_prior,
                context_width,
            },
        )?,
    };
    // let wsd = make_wsd_application(saldo.as_ref(), &args.app_name, &argv)?;

    // FIXME: eval not supported yet
    // if args.format == Format::Eval {
    //     evaluate(wsd, &args.eval_lemmas.unwrap(), &args.eval_key.unwrap());
    //     return Ok(());
    // }

    // FIXME: ratios not supported yet
    // let mut ratios = None;
    // if args.for_lemma.is_some() {
    //     todo!("ratios is not yet supported");
    //     // todo!("ratios = Some(HashMap::new())");
    // }

    let mut stdin = io::stdin().lock();
    let mut stdout = io::stdout().lock();
    let format: Box<dyn SourceFormat> = if args.format == Format::Sbxml {
        todo!("sbxml format is not yet supported");
    } else {
        Box::new(TabFormat::default())
    };
    disambiguate_sentences(
        wsd,
        &mut stdin,
        &mut stdout,
        &format,
        DisambiguateOptions {
            batch_size: args.batch_size,
            max_sen: args.max_sen,
        },
    )
    .into_diagnostic()?;

    // FIXME: ratios not supported yet
    // if args.for_lemma.is_some() {
    //     todo!("printRatios(ratios)");
    // }

    // TODO split into chunks and use thread pool
    Ok(())
}

fn configure_logging(level: u8) {
    let log_level = match level {
        0 => LevelFilter::Error,
        1 => LevelFilter::Warn,
        2 => LevelFilter::Info,
        3 => LevelFilter::Debug,
        _ => LevelFilter::Trace,
    };
    env_logger::builder().filter_level(log_level).init();
}
