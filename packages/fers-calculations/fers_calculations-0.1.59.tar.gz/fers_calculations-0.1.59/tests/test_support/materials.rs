#[derive(Clone, Copy)]
pub struct Steel {
    pub e_mod: f64,
    pub name: &'static str,
}

pub fn build_steel_s235() -> Steel {
    Steel {
        e_mod: 210e9,
        name: "S235",
    }
}
