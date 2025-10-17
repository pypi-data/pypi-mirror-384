use hashbrown::HashMap;
use miette::{Context, IntoDiagnostic};
use ndarray::Array1;
use w2v::word2vec;

use crate::WSDApplication;

pub struct VectorWSD {
    decay: bool,
    s1prior: f32,
    context_width: usize,
    id_to_vectors: HashMap<String, Array1<f32>>,
    form_to_ctx_vec: HashMap<String, Array1<f32>>,
}

#[derive(Debug, Clone, Default)]
pub struct VectorWSDConfig {
    pub decay: bool,
    pub s1prior: f32,
    pub context_width: usize,
}
impl VectorWSD {
    pub fn new(
        sv_file: &str,
        cv_file: &str,
        VectorWSDConfig {
            decay,
            s1prior,
            context_width,
        }: VectorWSDConfig,
    ) -> miette::Result<Self> {
        let id_to_vectors =
            read_embeddings_from_path(sv_file).wrap_err("Failed to read sense vectors")?;
        let form_to_ctx_vec =
            read_embeddings_from_path(cv_file).wrap_err("Failed to read context vectors")?;
        Ok(Self {
            decay,
            s1prior,
            context_width,
            id_to_vectors,
            form_to_ctx_vec,
        })
    }
    pub fn new_as_shared(
        sv_file: &str,
        cv_file: &str,
        config: VectorWSDConfig,
    ) -> miette::Result<crate::SharedWSDApplication> {
        Ok(Box::new(Self::new(sv_file, cv_file, config)?))
    }

    fn add_s1prior(&self, ps: &[String], out: &mut [f32], svs: &[Option<&Array1<f32>>]) {
        let mut min = i32::MAX;
        for i in 0..out.len() {
            if svs[i].is_none() {
                continue;
            }
            let s = &ps[i];
            let ix = s.rfind("..").expect("a valid lemma_id");
            let id: i32 = s[ix + 2..].parse().unwrap();
            if id < min {
                min = id;
            }
        }
        for i in 0..out.len() {
            if svs[i].is_none() {
                continue;
            }
            let s = &ps[i];
            let ix = s.rfind("..").expect("a valid lemma_id");
            let id: i32 = s[ix + 2..].parse().unwrap();
            if id == min {
                out[i] += self.s1prior;
            }
        }
    }
}

impl WSDApplication for VectorWSD {
    fn disambiguate(&self, lts: &[process_corpus::LemmaToken], i: usize) -> Option<Vec<f32>> {
        let len = lts.len();
        let li = &lts[i];
        log::trace!("Lemma token {}: {:?}", i, li);
        let mut out = vec![0f32; li.possible_senses().len()];
        if out.len() < 2 {
            log::trace!("out shorter than 2, returning None, out={:?}", out);
            return None;
        }
        // let mut svs = vec![vec![]; out.len()];
        let mut svs = Vec::with_capacity(out.len());
        let mut seen_any = false;
        // let (svs, seen) = self.id_to_vectors.embedding_batch(li.possible_senses());
        for poss_sense in li.possible_senses() {
            let v = self.id_to_vectors.get(poss_sense);
            if v.is_some() {
                seen_any = true;
            }
            svs.push(v);
            //     svs[j] = self.id_to_vectors.embedding(&poss_sense);
        }
        if !seen_any {
            log::trace!("Did not found any embeddings for the possible senses. ");
            return None;
        }
        self.add_s1prior(li.possible_senses(), &mut out, &svs);

        let start = 0.max(i - self.context_width);
        let end = (len - 1).min(i + self.context_width);
        for k in start..=end {
            if k == i {
                continue;
            }
            let Some(l) = lts[k].possible_lemmas().first() else {
                continue;
            };
            let Some(cv) = self.form_to_ctx_vec.get(l) else {
                continue;
            };

            let weight = if self.decay {
                let mut weight = (self.context_width - k.abs_diff(i) + 1) as f32;
                weight /= 2.0 * self.context_width as f32;
                weight
            } else {
                0.5f32 / self.context_width as f32
            };

            for j in 0..out.len() {
                let Some(vs) = svs[j] else {
                    continue;
                };
                let sc = vs.dot(cv);
                out[j] += weight * sc;
            }
        }
        normalize_to_probs(&mut out, &svs);
        Some(out)
    }
}

fn normalize_to_probs(out: &mut [f32], svs: &[Option<&Array1<f32>>]) {
    let mut m = f32::NEG_INFINITY;
    for i in 0..out.len() {
        if svs[i].is_none() {
            out[i] = 0f32;
        } else if out[i] > m {
            m = out[i];
        }
    }
    if m == f32::NEG_INFINITY {
        return;
    }
    let mut exp_sum = 0f32;
    for i in 0..out.len() {
        if svs[i].is_some() {
            exp_sum += (out[i] - m).exp();
        }
    }
    let log_exp_sum = exp_sum.ln() + m;
    for i in 0..out.len() {
        if svs[i].is_some() {
            out[i] = (out[i] - log_exp_sum).exp();
        }
    }
}

fn read_embeddings_from_path(path: &str) -> miette::Result<HashMap<String, Array1<f32>>> {
    let embeddings = word2vec::read_w2v_file(path, false)
        .into_diagnostic()
        .wrap_err_with(|| format!("Failed to read w2v file from '{}'", path))?;

    Ok(embeddings)
}
