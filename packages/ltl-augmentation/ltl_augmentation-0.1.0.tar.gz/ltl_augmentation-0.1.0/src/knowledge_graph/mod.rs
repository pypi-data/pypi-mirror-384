use std::collections::{HashMap, HashSet};

use crate::formula::atomic_proposition::AtomicProposition;
use crate::formula::literal::Literal;
use crate::truth_values::Kleene;
use complexity_functions::{ComplexityFunction, DefaultComplexityFunction};
use equivalence_class::EquivalenceClass;
use itertools::iproduct;
use petgraph::{
    algo::{condensation, floyd_warshall},
    graph::{DiGraph, NodeIndex},
};

pub mod complexity_functions;
mod equivalence_class;

#[derive(Debug, Clone)]
pub struct KnowledgeGraph<C = DefaultComplexityFunction> {
    graph: DiGraph<EquivalenceClass<C>, ()>,
    node_map: HashMap<Literal, NodeIndex>,
}

impl<C: ComplexityFunction> KnowledgeGraph<C> {
    pub fn new() -> Self {
        let mut knowledge_graph = KnowledgeGraph {
            graph: DiGraph::new(),
            node_map: HashMap::new(),
        };
        // This will automatically add False as well
        knowledge_graph.add_literal_if_not_exists(Literal::True);
        knowledge_graph
    }

    pub fn class_of(&self, literal: &Literal) -> Option<&HashSet<Literal>> {
        Some(&self.equivalence_class_of(literal)?.class)
    }

    pub fn representative_of(&self, literal: &Literal) -> Option<&Literal> {
        Some(&self.equivalence_class_of(literal)?.representative)
    }

    fn equivalence_class_of(&self, literal: &Literal) -> Option<&EquivalenceClass<C>> {
        self.node_map.get(literal).map(|idx| &self.graph[*idx])
    }

    pub fn implying_representatives<'a>(&'a self, literal: &'a Literal) -> HashSet<&'a Literal> {
        if let Some(idx) = self.node_map.get(literal) {
            self.graph
                .neighbors_directed(*idx, petgraph::Direction::Incoming)
                .map(|neighbor| &self.graph[neighbor].representative)
                .collect()
        } else {
            HashSet::from([literal])
        }
    }

    pub fn add_true_literal(&mut self, literal: Literal) {
        let ff_idx = self.node_map[&Literal::False];
        self.graph[ff_idx].insert(literal.clone().negated());
        self.node_map.insert(literal.clone().negated(), ff_idx);

        let tt_idx = self.node_map[&Literal::True];
        self.graph[tt_idx].insert(literal.clone());
        self.node_map.insert(literal, tt_idx);
    }

    pub fn add_false_literal(&mut self, literal: Literal) {
        self.add_true_literal(literal.negated());
    }

    pub fn add_implication(&mut self, precondition: Literal, consequence: Literal) {
        if matches!(precondition, Literal::True) || matches!(consequence, Literal::False) {
            self.add_equivalence(precondition, consequence);
            return;
        }
        self.add_implication_inner(precondition, consequence);
    }

    fn add_implication_inner(&mut self, precondition: Literal, consequence: Literal) {
        let (pre_pos_idx, pre_neg_idx) = self.add_literal_if_not_exists(precondition);
        let (con_pos_idx, con_neg_idx) = self.add_literal_if_not_exists(consequence);
        self.graph.update_edge(pre_pos_idx, con_pos_idx, ());
        self.graph.update_edge(con_neg_idx, pre_neg_idx, ());
    }

    pub fn add_equivalence(&mut self, lhs: Literal, rhs: Literal) {
        match (self.node_map.get(&lhs), self.node_map.get(&rhs)) {
            // If only one literal exists in the graph, add the other one to the same node
            (Some(lhs_idx), None) => {
                self.graph[*lhs_idx].insert(rhs.clone());
                self.node_map.insert(rhs.clone(), *lhs_idx);

                let lhs_negated = lhs.negated();
                let rhs_negated = rhs.clone().negated();
                let lhs_neg_idx = self.node_map[&lhs_negated];
                self.graph[lhs_neg_idx].insert(rhs_negated.clone());
                self.node_map.insert(rhs_negated, lhs_neg_idx);
            }
            (None, Some(_)) => {
                self.add_equivalence(rhs, lhs);
            }
            // If none of the literals exist in the graph, create a new node with both
            (None, None) => {
                let (pos_idx, neg_idx) = self.add_literal_if_not_exists(lhs);
                self.graph[pos_idx].insert(rhs.clone());
                self.node_map.insert(rhs.clone(), pos_idx);
                self.graph[neg_idx].insert(rhs.clone().negated());
                self.node_map.insert(rhs.negated(), neg_idx);
            }
            // If both literals exist in the graph, add the implications as edges to be merged later
            (Some(_), Some(_)) => {
                self.add_implication_inner(lhs.clone(), rhs.clone());
                self.add_implication_inner(rhs, lhs);
            }
        }
    }

    fn add_literal_if_not_exists(&mut self, literal: Literal) -> (NodeIndex, NodeIndex) {
        let negated = literal.clone().negated();
        match (self.node_map.get(&literal), self.node_map.get(&negated)) {
            (Some(idx_pos), Some(idx_neg)) => (*idx_pos, *idx_neg),
            (None, None) => {
                let idx_pos = self.graph.add_node(EquivalenceClass::from(literal.clone()));
                self.node_map.insert(literal, idx_pos);

                let idx_neg = self.graph.add_node(EquivalenceClass::from(negated.clone()));
                self.node_map.insert(negated, idx_neg);

                (idx_pos, idx_neg)
            }
            _ => unreachable!("The negation of a node must always exist if the node exists"),
        }
    }

    pub fn complete_graph(&mut self) {
        // All contrapositive edges are already added, so we only need to add transitive edges
        let transitive_closure = floyd_warshall(&self.graph, |_| 1)
            .expect("All edge weights should be positive, so there cannot be a negative cycle");
        for (src, dst) in iproduct!(self.graph.node_indices(), self.graph.node_indices()) {
            if transitive_closure
                .get(&(src, dst))
                .is_some_and(|&dist| dist < i32::MAX)
            {
                self.graph.update_edge(src, dst, ());
            }
        }
    }

    pub fn condense_graph(mut self) -> Self {
        // Compute condensation of the graph, but the result has a vector of sets as nodes instead of a single set
        let condensed_vecs = condensation(self.graph, true);

        // Combine the sets in the nodes to a single set
        let mut condensed =
            DiGraph::with_capacity(condensed_vecs.node_count(), condensed_vecs.edge_count());
        let (nodes, edges) = condensed_vecs.into_nodes_edges();
        let mut new_node_idxs = vec![NodeIndex::default(); nodes.len()];
        for (idx, node) in nodes.into_iter().enumerate() {
            let literals = node
                .weight
                .into_iter()
                .reduce(|mut acc, e| {
                    acc.extend(e);
                    acc
                })
                .expect("SCC should not be empty");
            let new_idx = condensed.add_node(literals);
            new_node_idxs[idx] = new_idx;
            condensed[new_idx].iter().for_each(|literal| {
                *self.node_map.get_mut(literal).unwrap() = new_idx;
            });
        }

        // Copy the edges to the new graph
        for edge in edges {
            let src = new_node_idxs[edge.source().index()];
            let dst = new_node_idxs[edge.target().index()];
            condensed.update_edge(src, dst, ());
        }

        KnowledgeGraph {
            graph: condensed,
            node_map: self.node_map,
        }
    }

    pub fn collect_aps(&self) -> HashSet<AtomicProposition> {
        self.graph
            .node_indices()
            .flat_map(|idx| {
                self.graph[idx]
                    .class
                    .iter()
                    .filter_map(|literal| match literal {
                        // It is not necessary to include the negated literals, since always both are present
                        Literal::Positive(ap) => Some(ap.clone()),
                        _ => None,
                    })
            })
            .collect()
    }

    pub fn get_kleene_evaluation(&self, ap: &AtomicProposition) -> Kleene {
        let representative = self.representative_of(&Literal::Positive(ap.clone()));
        if let Some(representative) = representative {
            if matches!(representative, Literal::True) {
                Kleene::True
            } else if matches!(representative, Literal::False) {
                Kleene::False
            } else {
                Kleene::Unknown
            }
        } else {
            Kleene::Unknown
        }
    }

    pub fn dot(&self) -> String
    where
        C: std::fmt::Debug,
    {
        format!("{:?}", petgraph::dot::Dot::new(&self.graph))
    }
}

impl Default for KnowledgeGraph {
    fn default() -> Self {
        Self::new()
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub enum KnowledgeGraphEdge {
    IsTrue(Literal),
    IsFalse(Literal),
    Implication(Literal, Literal),
    Equivalence(Literal, Literal),
}

impl FromIterator<KnowledgeGraphEdge> for KnowledgeGraph {
    fn from_iter<T: IntoIterator<Item = KnowledgeGraphEdge>>(iter: T) -> Self {
        let mut kg = KnowledgeGraph::new();
        for edge in iter {
            match edge {
                KnowledgeGraphEdge::IsTrue(literal) => kg.add_true_literal(literal),
                KnowledgeGraphEdge::IsFalse(literal) => kg.add_false_literal(literal),
                KnowledgeGraphEdge::Implication(precondition, consequence) => {
                    kg.add_implication(precondition, consequence)
                }
                KnowledgeGraphEdge::Equivalence(lhs, rhs) => kg.add_equivalence(lhs, rhs),
            }
        }
        kg
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    use rstest::*;

    #[fixture]
    fn literals() -> [Literal; 5] {
        let a = Literal::Positive(AtomicProposition::new("a"));
        let b = Literal::Positive(AtomicProposition::new("b"));
        let c = Literal::Positive(AtomicProposition::new("c"));
        let d = Literal::Positive(AtomicProposition::new("d"));
        let e = Literal::Positive(AtomicProposition::new("e"));
        [a, b, c, d, e]
    }

    #[rstest]
    fn test_add_true_literal(literals: [Literal; 5]) {
        let [a, b, ..] = literals;
        let mut kg: KnowledgeGraph<DefaultComplexityFunction> = KnowledgeGraph::new();
        kg.add_true_literal(a.clone());
        kg.add_true_literal(b.clone());
        assert_eq!(kg.graph.node_count(), 2);
        assert_eq!(kg.graph.edge_count(), 0);
        assert_eq!(
            kg.class_of(&a).unwrap(),
            &[a.clone(), b.clone(), Literal::True].into()
        );
        assert_eq!(kg.representative_of(&a).unwrap(), &Literal::True);
        assert_eq!(
            kg.class_of(&a.clone().negated()).unwrap(),
            &[a.clone().negated(), b.clone().negated(), Literal::False].into()
        );
        assert_eq!(
            kg.representative_of(&a.clone().negated()).unwrap(),
            &Literal::False
        );
    }

    #[rstest]
    fn test_condense_graph(literals: [Literal; 5]) {
        let [a, b, c, d, e] = literals;
        let kg = KnowledgeGraph::from_iter([
            KnowledgeGraphEdge::Implication(a.clone(), b.clone()),
            KnowledgeGraphEdge::Implication(b.clone(), c.clone().negated()),
            KnowledgeGraphEdge::Implication(a.clone().negated(), c.clone()),
            KnowledgeGraphEdge::Implication(d.clone(), Literal::False),
            KnowledgeGraphEdge::Implication(e.clone(), b.clone()),
        ]);

        let mut condensed = kg.condense_graph();
        condensed.complete_graph();

        assert_eq!(condensed.graph.node_count(), 6);
        assert_eq!(
            condensed.class_of(&a).unwrap(),
            &[a.clone(), b.clone(), c.clone().negated()].into()
        );
        assert_eq!(
            condensed.class_of(&d).unwrap(),
            &[d.clone(), Literal::False].into()
        );
        assert_eq!(condensed.class_of(&e).unwrap(), &[e.clone()].into());
        assert_eq!(condensed.graph.edge_count(), 2 + 6);
        assert!(condensed
            .graph
            .find_edge(condensed.node_map[&e], condensed.node_map[&a])
            .is_some());
        assert!(condensed
            .graph
            .find_edge(
                condensed.node_map[&a.clone().negated()],
                condensed.node_map[&e.clone().negated()]
            )
            .is_some());
    }
}
