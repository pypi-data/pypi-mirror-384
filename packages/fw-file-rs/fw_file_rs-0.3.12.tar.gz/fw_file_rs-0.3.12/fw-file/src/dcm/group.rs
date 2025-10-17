use std::collections::BTreeMap;
use std::collections::HashMap;

use crate::dcm::DicomValue;

const DEFAULT_GROUP_BY_TAGS: &[&str] = &["StudyInstanceUID", "SeriesInstanceUID"];

pub struct DCMGroup {
    pub paths: Vec<String>,
    pub is_localizer: bool,
}

pub fn group_series(
    path_header_pairs: &[(String, HashMap<String, DicomValue>)],
    group_by_tags: Option<&[&str]>,
    split_localizer_flag: bool,
) -> Vec<DCMGroup> {
    let group_by_tags = group_by_tags
        .as_ref()
        .filter(|v| !v.is_empty())
        .unwrap_or(&DEFAULT_GROUP_BY_TAGS);

    let mut groups: Vec<DCMGroup> = vec![];

    for group in split_by_unique_tags(path_header_pairs, group_by_tags) {
        let has_instance_numbers = group.iter().all(|(_, m)| m.get("InstanceNumber").is_some());

        if split_localizer_flag && has_instance_numbers {
            let mut sorted_group = group.clone();
            sorted_group.sort_by_key(|(_, m)| {
                m.get("InstanceNumber")
                    .map(|v| match v {
                        DicomValue::Int(s) => s.clone(),
                        _ => 0,
                    })
                    .unwrap_or(0)
            });

            let scorers: Vec<Box<dyn Fn(&[HashMap<String, DicomValue>]) -> (Vec<i64>, i64)>> = vec![
                Box::new(|f| score_by_euclidean(f, "ImageOrientationPatient", 30)),
                Box::new(|f| score_by_euclidean(f, "ImagePositionPatient", 30)),
                Box::new(|f| score_by_unique_tag(f, &vec!["Rows".into(), "Columns".into()], 30)),
            ];

            let (series, localizer) = split_localizer(&sorted_group, scorers);
            groups.push(DCMGroup {
                paths: series.iter().map(|(path, _)| path.clone()).collect(),
                is_localizer: false,
            });
            if !localizer.is_empty() {
                groups.push(DCMGroup {
                    paths: localizer.iter().map(|(path, _)| path.clone()).collect(),
                    is_localizer: true,
                });
            }
        } else {
            groups.push(DCMGroup {
                paths: group.iter().map(|(path, _)| path.clone()).collect(),
                is_localizer: false,
            });
        }
    }

    groups
}

fn split_by_unique_tags(
    path_header_pairs: &[(String, HashMap<String, DicomValue>)],
    tags: &[&str],
) -> Vec<Vec<(String, HashMap<String, DicomValue>)>> {
    let mut groups: BTreeMap<Vec<String>, Vec<(String, HashMap<String, DicomValue>)>> =
        BTreeMap::new();

    for (path, meta) in path_header_pairs {
        let key = tag_key(meta, tags);
        groups
            .entry(key)
            .or_default()
            .push((path.clone(), meta.clone()));
    }

    groups.into_values().collect()
}

fn tag_key(meta: &HashMap<String, DicomValue>, tags: &[&str]) -> Vec<String> {
    let mut result: Vec<String> = Vec::new();
    for tag in tags {
        match meta.get(*tag) {
            Some(value) => result.push(value.to_string()),
            None => result.push("".to_string()),
        }
    }
    result
}

fn euclidean(va: &[f64], vb: &[f64]) -> f64 {
    va.iter()
        .zip(vb.iter())
        .map(|(a, b)| (a - b).powi(2))
        .sum::<f64>()
        .sqrt()
}

fn parse_f64_list(tag: &DicomValue) -> Option<Vec<f64>> {
    match tag {
        DicomValue::Ints(vals) => Some(vals.iter().map(|&v| v as f64).collect()),
        DicomValue::Floats(vals) => Some(vals.clone()),
        _ => None,
    }
}

fn score_by_euclidean(
    path_header_pairs: &[HashMap<String, DicomValue>],
    tag: &str,
    decision_val: i64,
) -> (Vec<i64>, i64) {
    let mut scores = vec![0; path_header_pairs.len()];

    let vectors: Vec<_> = path_header_pairs
        .iter()
        .filter_map(|m| m.get(tag))
        .filter_map(parse_f64_list)
        .collect();

    if vectors.len() != path_header_pairs.len() || vectors.len() < 2 {
        return (scores, decision_val);
    }

    let mut distances = vec![0.0; vectors.len()];
    for i in 0..(vectors.len() - 1) {
        distances[i] = euclidean(&vectors[i], &vectors[i + 1]);
    }

    let mean = distances.iter().sum::<f64>() / distances.len() as f64;
    let std =
        (distances.iter().map(|d| (d - mean).powi(2)).sum::<f64>() / distances.len() as f64).sqrt();

    let threshold = 0.01;
    let mut split_flags = vec![0; path_header_pairs.len()];
    for (i, d) in distances.iter().enumerate() {
        let p = halfnorm_sf((*d - mean).abs(), std);
        if p < threshold {
            for j in (i + 1)..split_flags.len() {
                split_flags[j] += 1;
            }
        }
    }

    let flags_mod_2: Vec<i64> = split_flags.iter().map(|f| f % 2).collect();
    let (main_group, _) = [0, 1]
        .iter()
        .map(|&g| (g, flags_mod_2.iter().filter(|&&x| x == g).count()))
        .max_by_key(|x| x.1)
        .unwrap();

    for (i, &flag) in flags_mod_2.iter().enumerate() {
        if flag != main_group {
            scores[i] = decision_val;
        }
    }

    (scores, decision_val)
}

fn score_by_unique_tag(
    files: &[HashMap<String, DicomValue>],
    tags: &[&str],
    decision_val: i64,
) -> (Vec<i64>, i64) {
    let mut keys = vec![];
    for file in files {
        let key = tag_key(file, tags);
        keys.push(key);
    }

    let mut counts = HashMap::new();
    for key in &keys {
        *counts.entry(key.clone()).or_insert(0) += 1;
    }

    let primary_key = counts
        .iter()
        .max_by_key(|entry| entry.1)
        .map(|(k, _)| k)
        .unwrap();
    let scores = keys
        .into_iter()
        .map(|k| if k == *primary_key { 0 } else { decision_val })
        .collect();
    (scores, decision_val)
}

fn halfnorm_sf(x: f64, std: f64) -> f64 {
    if std <= 0.0 {
        1.0
    } else {
        erfc(x / (std * 2f64.sqrt()))
    }
}

#[rustfmt::skip]
fn erf(x: f64) -> f64 {
    let t = 1.0 / (1.0 + 0.5 * x.abs());
    let tau = t * (-x*x - 1.26551223 +
        t*(1.00002368 +
        t*(0.37409196 +
        t*(0.09678418 +
        t*(-0.18628806 +
        t*(0.27886807 +
        t*(-1.13520398 +
        t*(1.48851587 +
        t*(-0.82215223 +
        t*0.17087277))))))))).exp();
    if x >= 0.0 { 1.0 - tau } else { tau - 1.0 }
}

fn erfc(x: f64) -> f64 {
    1.0 - erf(x)
}

fn split_localizer(
    path_header_pairs: &[(String, HashMap<String, DicomValue>)],
    scorers: Vec<Box<dyn Fn(&[HashMap<String, DicomValue>]) -> (Vec<i64>, i64)>>,
) -> (
    Vec<(String, HashMap<String, DicomValue>)>,
    Vec<(String, HashMap<String, DicomValue>)>,
) {
    let mut total_scores = vec![0; path_header_pairs.len()];
    let mut total_weight = 0;

    for scorer in scorers {
        let (scores, weight) = scorer(
            &path_header_pairs
                .iter()
                .map(|(_, m)| m.clone())
                .collect::<Vec<_>>(),
        );
        for (i, s) in scores.iter().enumerate() {
            total_scores[i] += s;
        }
        total_weight += weight;
    }

    let threshold = 0.5;
    let mut main = vec![];
    let mut localizer = vec![];

    for (i, score) in total_scores.iter().enumerate() {
        let norm = if total_weight != 0 {
            *score as f64 / total_weight as f64
        } else {
            0.0
        };
        if norm < threshold {
            main.push(path_header_pairs[i].clone());
        } else {
            localizer.push(path_header_pairs[i].clone());
        }
    }

    (main, localizer)
}
