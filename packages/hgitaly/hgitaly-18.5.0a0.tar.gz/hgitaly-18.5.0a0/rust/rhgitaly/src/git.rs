// Copyright 2023 Georges Racinet <georges.racinet@octobus.net>
//
// This software may be used and distributed according to the terms of the
// GNU General Public License version 2 or any later version.
//
// SPDX-License-Identifier: GPL-2.0-or-later
//! Git specific things, mostly constants.
use lazy_static::lazy_static;
use regex::bytes::Regex;

// Not sure about these, maybe bytes variants would turn out to be more useful
pub const ZERO_SHA_1: &str = "0000000000000000000000000000000000000000";
pub const NULL_COMMIT_ID: &str = ZERO_SHA_1;
pub const NULL_BLOB_OID: &str = ZERO_SHA_1;

// from `sha1-file.c` in Git 2.28 sources
// we're not dealing for now with the fact that there will be
// two kinds of OIDs with SHA-1 and SHA-256 soon.

// The Git tree object hash that corresponds to an empty tree (directory)
pub const EMPTY_TREE_OID: &str = "4b825dc642cb6eb9a060e54bf8d69288fbee4904";

// The Git blob object hash that corresponds to an empty blob (file)
pub const EMPTY_BLOB_OID: &str = "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391";

pub const OBJECT_MODE_DOES_NOT_EXIST: i32 = 0; // see, e.g, ChangedPaths in diff.proto
pub const OBJECT_MODE_LINK: i32 = 0o120000; // symlink to file or directory
pub const OBJECT_MODE_EXECUTABLE: i32 = 0o100755; // for blobs only
pub const OBJECT_MODE_NON_EXECUTABLE: i32 = 0o100644; // for blobs only
pub const OBJECT_MODE_TREE: i32 = 0o40000;

pub trait GitPathSpec {
    fn matches(&self, other: &[u8]) -> bool;
    fn matches_root(&self) -> bool;
}

pub struct GitLiteralPathSpec<'a> {
    path: &'a [u8],
    path_len: usize,
    has_trailing_slash: bool,
}

impl<'a> GitLiteralPathSpec<'a> {
    pub fn new(path: &'a [u8]) -> Self {
        Self {
            path,
            path_len: path.len(),
            has_trailing_slash: *path.last().unwrap_or(&b'.') == b'/',
        }
    }
}

impl GitPathSpec for GitLiteralPathSpec<'_> {
    fn matches(&self, other: &[u8]) -> bool {
        other.starts_with(self.path)
            && (self.has_trailing_slash
                || other.len() == self.path_len
                || other[self.path_len] == b'/')
    }

    fn matches_root(&self) -> bool {
        let path = self.path;
        path.is_empty() || path == b"." || path == b"/" || path == b"./"
    }
}

pub struct GitWildcardPathSpec<'a> {
    split_spec: Vec<&'a [u8]>,
}

impl<'a> GitWildcardPathSpec<'a> {
    pub fn new(pathspec: &'a [u8]) -> Self {
        Self {
            split_spec: pathspec.split(|c| *c == b'/').collect(),
        }
    }
}

fn question_mark_match(input: &[u8], spec: &[u8]) -> bool {
    let mut inp_iter = input.iter();

    for sc in spec.iter() {
        if *sc == b'?' {
            if inp_iter.next().is_none() {
                return false;
            }
        } else if inp_iter.next() != Some(sc) {
            return false;
        }
    }
    true
}

fn locate_with_question_mark<'a>(input: &'a [u8], spec: &[u8]) -> Option<&'a [u8]> {
    let mut to_check = input;
    let slen = spec.len();
    while to_check.len() >= slen {
        if question_mark_match(to_check, spec) {
            return Some(&to_check[slen..]);
        }
        to_check = &to_check[1..];
    }
    None
}

/// Reimplementation of glibc's fnmatch(1) in the simple case without options that we need
///
/// It implements wildcard matching (question mark and star), and matches forward slashes
/// inconditionally.
fn fnmatch(input: &[u8], spec: &[u8]) -> bool {
    let split_star = spec.split(|c| *c == b'*');
    let mut to_match = input;
    let mut first = true;
    for part in split_star {
        if first {
            first = false;
            if question_mark_match(to_match, part) {
                to_match = &to_match[part.len()..];
                continue;
            } else {
                return false;
            }
        } else if part.is_empty() {
            // we had a "**"
            continue;
        }
        match locate_with_question_mark(to_match, part) {
            None => {
                return false;
            }
            Some(rem) => {
                to_match = rem;
            }
        }
    }
    true
}

impl GitPathSpec for GitWildcardPathSpec<'_> {
    fn matches(&self, other: &[u8]) -> bool {
        let mut split_input = other.splitn(self.split_spec.len(), |c| *c == b'/');

        for i in 0..self.split_spec.len() - 1 {
            let spec_segment = self.split_spec[i];
            if let Some(input_segment) = split_input.next() {
                if !spec_segment.is_empty() && !fnmatch(input_segment, spec_segment) {
                    return false;
                }
            } else {
                // there are less segments in input than in spec
                return false;
            }
        }

        // condition on last segment
        let last_spec = self.split_spec.last().expect("A split is never empty");
        if let Some(last_input) = split_input.last() {
            // TODO, there should be simpler way to express "up to the first slash"
            last_spec.is_empty()
                || fnmatch(last_input, last_spec)
                || fnmatch(
                    last_input
                        .splitn(2, |c| *c == b'/')
                        .next()
                        .expect("A split is never empty"),
                    last_spec,
                )
        } else {
            // there is exactly one segment less in input than in spec
            false
        }
    }

    fn matches_root(&self) -> bool {
        match self.split_spec.len() {
            0 => true,
            1 => self.split_spec[0] == b".",
            2 => {
                self.split_spec[1].is_empty()
                    && (self.split_spec[0].is_empty() || self.split_spec[0] == b".")
            }
            _ => false,
        }
    }
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum GitRevSpec<'a> {
    Revision(&'a [u8]),
    Exclusion(&'a [u8], &'a [u8]),     // a..b
    SymDifference(&'a [u8], &'a [u8]), // a...b
}

lazy_static! {
    static ref REVSPEC_RANGES_RX: Regex = Regex::new(r"(.*?)([.]{2,3})(.*)").unwrap();
}

impl<'a> GitRevSpec<'a> {
    pub fn parse(revspec: &'a [u8]) -> Self {
        match REVSPEC_RANGES_RX.captures(revspec) {
            None => Self::Revision(revspec),
            Some(caps) => {
                // Cannot use `&caps[i]` because the Index trait signature considers it
                // to be a borrow of `caps`
                let first = caps
                    .get(1)
                    .expect("Regex matching should have capture group")
                    .into();
                let sep: &[u8] = caps
                    .get(2)
                    .expect("Regex matching should have capture group")
                    .into();
                let second = caps
                    .get(3)
                    .expect("Regex matching should have capture group")
                    .into();
                if sep.len() == 2 {
                    Self::Exclusion(first, second)
                } else {
                    Self::SymDifference(first, second)
                }
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_question_mark_match() {
        assert!(question_mark_match(b"", b""));
        assert!(question_mark_match(b"foo", b"foo"));
        assert!(question_mark_match(b"foo", b"f?o"));
        assert!(!question_mark_match(b"foo", b"f?a"));
        assert!(question_mark_match(b"fooa", b"f?o"));
    }

    #[test]
    fn test_fnmatch() {
        assert!(fnmatch(b"ab", b"ab"));
        assert!(fnmatch(b"foo", b"f?o"));
        assert!(fnmatch(b"foo", b"*o"));
        assert!(!fnmatch(b"foo", b"*a"));
        assert!(fnmatch(b"sub/dir/ab", b"sub/dir"))
    }

    #[test]
    /// Same tests as in Python implementation
    fn test_git_wildcard_path_spec() {
        // Example from the glossary about wildcards matching slashes::
        let pathspec = GitWildcardPathSpec::new(b"Documentation/*.jpg");
        assert!(pathspec.matches(b"Documentation/chapter_1/figure_1.jpg"));

        // Before the last slash, wildcards do not match slashes
        let pathspec = GitWildcardPathSpec::new(b"*/figure_1.jpg");
        assert!(!pathspec.matches(b"Documentation/chapter_1/figure_1.jpg"));
        assert!(!pathspec.matches(b"figure_1.jpg"));
        assert!(pathspec.matches(b"Documentation/figure_1.jpg"));

        // Trailing slash subtleties
        let pathspec = GitWildcardPathSpec::new(b"Documentation/");
        assert!(!pathspec.matches(b"Documentation"));
        assert!(pathspec.matches(b"Documentation/foo"));

        // Implicit directory prefix (not mentioned in gitglossary(7) but still
        // true and checkable with all commands, including `git log` and `git add`)::
        let pathspec = GitWildcardPathSpec::new(b"Documentation/foo");
        assert!(pathspec.matches(b"Documentation/foo/bar"));
        let pathspec = GitWildcardPathSpec::new(b"Documentation");
        assert!(pathspec.matches(b"Documentation"));
        assert!(pathspec.matches(b"Documentation/foo"));
        assert!(pathspec.matches(b"Documentation/foo/bar"));
        let pathspec = GitWildcardPathSpec::new(b"Doc*");
        assert!(pathspec.matches(b"Documentation/foo"));
        assert!(pathspec.matches(b"Documentation/foo/bar"));
    }

    #[test]
    /// Same tests as in Python implementation
    fn test_revspec_parse() {
        assert_eq!(GitRevSpec::parse(b"main"), GitRevSpec::Revision(b"main"));
        assert_eq!(
            GitRevSpec::parse(b"main..feature"),
            GitRevSpec::Exclusion(b"main", b"feature")
        );
        assert_eq!(
            GitRevSpec::parse(b"main...feature"),
            GitRevSpec::SymDifference(b"main", b"feature")
        );
    }
}
