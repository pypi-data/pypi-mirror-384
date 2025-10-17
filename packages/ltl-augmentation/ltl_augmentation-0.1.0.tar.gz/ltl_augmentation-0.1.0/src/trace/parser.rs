use std::collections::HashMap;

use crate::{
    formula::atomic_proposition::AtomicProposition,
    sequence::{NormalizedSequence, Sequence},
    sets::interval::Interval,
    trace::Trace,
    truth_values::Kleene,
};

peg::parser! {
    pub grammar kleene_trace_parser() for str {
        pub rule trace() -> Trace<Kleene>
            = aps:atomic_propositions() "\n" time_steps:time_steps() _ {?
                if time_steps.iter().all(|ts| ts.len() == aps.len()) {
                    let mut values = HashMap::new();
                    for (time, vals) in time_steps.into_iter().enumerate() {
                        let int = Interval::singleton(time as u32);
                        for (ap, value) in aps.iter().zip(vals) {
                            values.entry(ap.clone()).or_insert_with(|| NormalizedSequence::uniform(Kleene::Unknown)).set(&int, value);
                        }
                    }
                    Ok(Trace::from(values))
                } else {
                    Err("Number of atomic propositions and time steps do not match")
                }
            }

        rule atomic_propositions() -> Vec<AtomicProposition>
            = aps:(atomic_proposition() **<1,> " ") { aps }

        rule time_steps() -> Vec<Vec<Kleene>>
            = time_steps:(time_step() ** "\n") { time_steps }

        rule time_step() -> Vec<Kleene>
            = values:(kleene_value() **<1,> " ") { values }

        rule kleene_value() -> Kleene
            = "T" { Kleene::True }
            / "F" { Kleene::False }
            / "U" { Kleene::Unknown }

        rule atomic_proposition() -> AtomicProposition
            = name:$(['a'..='z' | 'A'..='Z' | '0'..='9'] ['a'..='z' | 'A'..='Z' | '0'..='9' | '_']*) parameter:$("(" ['a'..='z' | 'A'..='Z' | '0'..='9' | '_']* ")")? {
                match parameter {
                    Some(param) => AtomicProposition::with_parameter(name, param),
                    None => AtomicProposition::new(name),
                }
            }

        rule _ = quiet!{[' ' | '\n' | '\t']*}
    }
}

#[cfg(test)]
mod tests {
    use rstest::*;

    use super::*;

    #[rstest]
    fn test_parser() {
        let trace = kleene_trace_parser::trace("a b c\nT F U\nT F F\n").unwrap();
        assert_eq!(
            trace,
            Trace::from(HashMap::from_iter([
                (
                    AtomicProposition::new("a"),
                    NormalizedSequence::indicator(
                        &Interval::bounded(0, 1),
                        Kleene::True,
                        Kleene::Unknown
                    )
                ),
                (
                    AtomicProposition::new("b"),
                    NormalizedSequence::indicator(
                        &Interval::bounded(0, 1),
                        Kleene::False,
                        Kleene::Unknown
                    )
                ),
                (
                    AtomicProposition::new("c"),
                    NormalizedSequence::indicator(
                        &Interval::singleton(1),
                        Kleene::False,
                        Kleene::Unknown
                    )
                ),
            ]))
        );
    }
}
