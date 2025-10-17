#[derive(Debug, clap::Parser)]
#[command(version, author = "Språkbanken Text at Göteborg university",about, long_about=None)]
#[command(propagate_version = true)]
pub struct Args {
    // /// load saldo from this file
    // #[arg(long)]
    // pub saldo: Option<String>,
    /// app-name to use
    #[command(subcommand)]
    pub app_name: AppNames,
    /// Format of the output
    #[arg(long)]
    pub format: Format,
    // /// Should MWEs be split?
    // #[arg(long)]
    // pub split_mwes: bool,
    // /// Should Compounds be split?
    // #[arg(long, default_value_t = true)]
    // pub split_compounds: bool,
    /// The size of each batch
    #[arg(long, default_value_t = 1)]
    pub batch_size: usize,
    // /// evalLemmas
    // #[arg(long)]
    // pub eval_lemmas: Option<String>,
    // /// evalKey
    // #[arg(long)]
    // pub eval_key: Option<String>,
    // /// forLemma
    // #[arg(long)]
    // pub for_lemma: Option<String>,
    /// The maximum sense
    #[arg(long, default_value_t = u32::MAX as usize)]
    pub max_sen: usize,
    /// Verbosity
    #[arg(short, long, action = clap::ArgAction::Count)]
    pub verbose: u8,
}

#[derive(Debug, clap::Subcommand)]
pub enum AppNames {
    VectorWSD {
        #[arg(long)]
        decay: bool,
        #[arg(long, default_value_t = 0.0)]
        s1_prior: f32,
        #[arg(long)]
        context_width: usize,
        #[arg(long)]
        sv_file: String,
        #[arg(long)]
        cv_file: String,
    },
}

#[derive(Debug, Clone, Copy, Default, PartialEq, clap::ValueEnum)]
pub enum Format {
    #[default]
    Sbxml,
    Tab,
    Eval,
}
