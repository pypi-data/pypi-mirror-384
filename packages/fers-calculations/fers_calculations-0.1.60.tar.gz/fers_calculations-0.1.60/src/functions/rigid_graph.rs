// src/functions/rigid_graph.rs

use std::collections::HashMap;

use crate::models::members::enums::MemberType;
use crate::models::members::memberset::MemberSet;

#[derive(Clone, Copy, Debug)]
pub struct RigidEdge {
    pub master: u32,        // node a
    pub slave: u32,         // node b
    pub r: (f64, f64, f64), // x_b - x_a
}

#[derive(Debug)]
pub struct RigidGraph {
    parent: HashMap<u32, (u32, (f64, f64, f64))>, // slave -> (master, r)
    edges: Vec<RigidEdge>,
}

impl RigidGraph {
    pub fn build(member_sets: &[MemberSet]) -> Result<Self, String> {
        let mut parent: HashMap<u32, (u32, (f64, f64, f64))> = HashMap::new();
        let mut edges: Vec<RigidEdge> = Vec::new();

        for set in member_sets {
            for m in &set.members {
                if !matches!(m.member_type, MemberType::Rigid) {
                    continue;
                }

                let a = m.start_node.id;
                let b = m.end_node.id;
                let r = (
                    m.end_node.X - m.start_node.X,
                    m.end_node.Y - m.start_node.Y,
                    m.end_node.Z - m.start_node.Z,
                );

                let l2 = r.0 * r.0 + r.1 * r.1 + r.2 * r.2;
                if l2 < 1.0e-24 {
                    return Err(format!("Rigid member {} has zero length.", m.id));
                }

                if parent.contains_key(&b) {
                    return Err(format!("Node {} is slave in multiple rigid links.", b));
                }

                // cycle detection: does a depend on b?
                let mut p = a;
                let mut guard = 0usize;
                while let Some(&(pp, _)) = parent.get(&p) {
                    if pp == b {
                        return Err(format!("Rigid cycle detected involving node {}.", b));
                    }
                    p = pp;
                    guard += 1;
                    if guard > 100000 {
                        return Err("Rigid chain too long (suspected loop).".to_string());
                    }
                }

                parent.insert(b, (a, r));
                edges.push(RigidEdge {
                    master: a,
                    slave: b,
                    r,
                });
            }
        }

        Ok(Self { parent, edges })
    }

    fn depth_of(&self, node: u32) -> usize {
        let mut d = 0usize;
        let mut p = node;
        while let Some(&(pp, _)) = self.parent.get(&p) {
            d += 1;
            p = pp;
        }
        d
    }

    /// Edges sorted so that masters are processed before their slaves (useful for building S).
    pub fn edges_sorted_master_first(&self) -> Vec<RigidEdge> {
        let mut e = self.edges.clone();
        e.sort_by_key(|edge| self.depth_of(edge.master));
        e
    }

    /// Edges sorted deepest slave first (useful for roll-up aggregation).
    pub fn edges_sorted_child_first(&self) -> Vec<RigidEdge> {
        let mut e = self.edges.clone();
        e.sort_by_key(|edge| std::cmp::Reverse(self.depth_of(edge.slave)));
        e
    }

    pub fn parent_map(&self) -> &HashMap<u32, (u32, (f64, f64, f64))> {
        &self.parent
    }
}
