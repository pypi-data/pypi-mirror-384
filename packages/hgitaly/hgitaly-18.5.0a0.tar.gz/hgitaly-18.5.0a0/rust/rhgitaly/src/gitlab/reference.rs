// Copyright 2024 Georges Racinet <georges.racinet@octobus.net>
//
// This software may be used and distributed according to the terms of the
// GNU General Public License version 2 or any later version.
// SPDX-License-Identifier: GPL-2.0-or-later

//! Utilities for handling of Git(Lab) references
//!
//! The [`RefPattern`] struct provides matching as in `git-for-each-ref(1)`.
use crate::glob::glob_to_regex;
use regex::bytes::Regex;

pub enum RefPattern<'req> {
    Prefix(&'req [u8]),
    SegmentRegexps(Vec<Regex>),
}

impl<'req> RefPattern<'req> {
    pub fn new(pat: &'req [u8]) -> Self {
        if pat.last().copied() == Some(b'/') {
            return Self::Prefix(pat);
        }

        Self::SegmentRegexps(pat.split(|c| *c == b'/').map(glob_to_regex).collect())
    }

    /// per-segment matching, same as path_match in Python `hgitaly.gitlab_ref` module
    pub fn matches(&self, ref_path: &[u8]) -> bool {
        let mut split_path = ref_path.split(|c| *c == b'/');
        match self {
            Self::Prefix(prefix) => ref_path.starts_with(prefix),
            Self::SegmentRegexps(regexps) => {
                for re in regexps.iter() {
                    match split_path.next() {
                        None => {
                            return false;
                        }
                        Some(path_seg) => {
                            if !re.is_match(path_seg) {
                                return false;
                            }
                        }
                    }
                }
                if split_path.next().is_some() {
                    // pattern has less segments than path
                    return false;
                }
                true
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_glob_patterns() -> () {
        let pat = RefPattern::new(b"refs/heads/branch/br*");
        assert!(pat.matches(b"refs/heads/branch/br1"));
        assert!(!pat.matches(b"refs/heads/branch/default"));

        let pat = RefPattern::new(b"refs/h*s/branch/br*");
        assert!(pat.matches(b"refs/heads/branch/br1"));
        assert!(pat.matches(b"refs/heads/branch/br"));
        assert!(!pat.matches(b"refs/hea/ds/branch/br1"));

        let pat = RefPattern::new(b"refs/heads/br?");
        assert!(pat.matches(b"refs/heads/br1"));
        assert!(!pat.matches(b"refs/heads/br")); // question mark requires a character
        assert!(!pat.matches(b"refs/heads/br1/overflowing")); // per-segment match is not prefixing
    }

    #[test]
    fn test_prefixing_patterns() -> () {
        let pat = RefPattern::new(b"refs/heads/");
        assert!(pat.matches(b"refs/heads/main"));
        assert!(pat.matches(b"refs/heads/branch/default"));
        assert!(!pat.matches(b"refs/tags/1.2.3"));
    }
}
