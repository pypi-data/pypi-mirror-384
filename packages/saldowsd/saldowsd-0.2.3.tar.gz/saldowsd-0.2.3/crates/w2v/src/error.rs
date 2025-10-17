use std::io;

/// w2v error
#[non_exhaustive]
#[derive(Debug, thiserror::Error, miette::Diagnostic)]
pub enum Error {
    #[error("Invalid file format {0}")]
    Format(String),

    #[error("Failed open file {path}")]
    Open {
        path: String,
        #[source]
        error: io::Error,
    },
    #[error("{desc}")]
    Read {
        desc: String,
        #[source]
        error: io::Error,
    },
}

impl Error {
    pub fn open_error(path: impl Into<String>, error: io::Error) -> Self {
        Error::Open {
            path: path.into(),
            error,
        }
    }
    pub fn read_error(desc: impl Into<String>, error: io::Error) -> Self {
        Error::Read {
            desc: desc.into(),
            error,
        }
    }
}
