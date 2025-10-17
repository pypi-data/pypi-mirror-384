// src/limits.rs

use crate::models::fers::fers::FERS;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum LicenseTier {
    Free,
    Premium,
}

#[derive(Debug, Clone)]
pub struct LimitPolicy {
    pub license_tier: LicenseTier,
    pub max_members_free: usize,
    pub max_members_premium: usize,
}

impl LimitPolicy {
    pub fn free() -> Self {
        Self {
            license_tier: LicenseTier::Free,
            max_members_free: 100,
            max_members_premium: 10_000,
        }
    }

    pub fn premium() -> Self {
        Self {
            license_tier: LicenseTier::Premium,
            max_members_free: 100,
            max_members_premium: 10_000,
        }
    }

    pub fn with_tier(license_tier: LicenseTier) -> Self {
        let mut base = Self::free();
        base.license_tier = license_tier;
        base
    }

    pub fn allowed_max_members(&self) -> usize {
        match self.license_tier {
            LicenseTier::Free => self.max_members_free,
            LicenseTier::Premium => self.max_members_premium,
        }
    }
}

/// Enforce global limits (e.g., member count) for a given FERS and policy.
pub fn enforce_limits(fers: &FERS, policy: &LimitPolicy) -> Result<(), String> {
    let count = fers.get_member_count();
    let max_allowed = policy.allowed_max_members();

    if count > max_allowed {
        return Err(format!(
            "Number of members ({}) exceeds allowed maximum of {}",
            count, max_allowed
        ));
    }

    Ok(())
}
