use std::{
    fs,
    io::{self, BufRead},
};

use byteorder::{LittleEndian, ReadBytesExt};
use hashbrown::HashMap;
use ndarray::Array1;

use crate::error::Error;

pub fn read_w2v_file(path: &str, normalize: bool) -> Result<HashMap<String, Array1<f32>>, Error> {
    let file = fs::File::open(path).map_err(|err| Error::open_error(path, err))?;
    let mut reader = io::BufReader::new(file);

    let voc_size = read_number(&mut reader, b' ')?;
    let dim = read_number(&mut reader, b'\n')?;

    // let mut matrix = Array2::zeros((voc_size, dim));
    // let mut words = Vec::with_capacity(voc_size);
    let mut dict = HashMap::with_capacity(voc_size);

    for _idx in 0..voc_size {
        let word = read_string(&mut reader, b' ', false)?;
        let word = word.trim();
        // words.push(word.to_owned());

        // let mut embedding = matrix.index_axis_mut(Axis(0), idx);
        let mut embedding = Array1::zeros((dim,));

        reader
            .read_f32_into::<LittleEndian>(embedding.as_slice_mut().expect("Matrix not contiguous"))
            .map_err(|e| Error::read_error("Cannot read word embedding", e))?;

        if normalize {
            todo!("normalize is not supported yet")
        }
        dict.insert(word.to_owned(), embedding);
    }
    Ok(dict)
}

pub fn read_number(reader: &mut dyn BufRead, delim: u8) -> Result<usize, Error> {
    let field_str = read_string(reader, delim, false)?;
    field_str.parse().map_err(|e| {
        Error::Format(format!(
            "Cannot parse shape component '{}': {}",
            field_str, e
        ))
    })
}

pub fn read_string(reader: &mut dyn BufRead, delim: u8, lossy: bool) -> Result<String, Error> {
    let mut buf = Vec::new();
    reader
        .read_until(delim, &mut buf)
        .map_err(|e| Error::read_error("Cannot read string", e))?;
    buf.pop();

    let s = if lossy {
        String::from_utf8_lossy(&buf).into_owned()
    } else {
        String::from_utf8(buf)
            .map_err(|e| Error::Format(format!("Token contains invalid UTF-8: {}", e)))?
    };

    Ok(s)
}
