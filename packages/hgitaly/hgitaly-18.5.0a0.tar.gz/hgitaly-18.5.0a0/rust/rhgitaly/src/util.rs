// Copyright 2023 Georges Racinet <georges.racinet@octobus.net>
//
// This software may be used and distributed according to the terms of the
// GNU General Public License version 2 or any later version.
// SPDX-License-Identifier: GPL-2.0-or-later
//! Common utilities
use std::borrow::Cow;
use std::io;

/// Convert `NotFound` I/O error to `None`
///
/// To be used when a file missing is logically equivalent to empty high level contents.
pub fn io_error_not_found_as_none<T>(res: io::Result<T>) -> io::Result<Option<T>> {
    match res {
        Ok(t) => Ok(Some(t)),
        Err(e) => {
            if e.kind() == io::ErrorKind::NotFound {
                Ok(None)
            } else {
                Err(e)
            }
        }
    }
}

/// Return the common subpath as a subslice of `first` and the index after which the remainder
/// starts in `second`.
#[allow(clippy::needless_lifetimes)] // for clarity and to prevent refactoring bugs
pub fn common_subpath_split<'a, 'b>(first: &'a [u8], second: &'b [u8]) -> (&'a [u8], usize) {
    // position of the latest slash in `first` after the common subpath, if any.
    let mut latest_slash: Option<usize> = None;

    let mut fit = first.iter();
    let mut sit = second.iter();
    let mut i: usize = 0;

    loop {
        match fit.next() {
            Some(fc) => match sit.next() {
                None => {
                    if *fc == b'/' {
                        latest_slash = Some(i);
                    } else {
                        break;
                    }
                }
                Some(sc) => {
                    if *fc != *sc {
                        break;
                    }
                    if *fc == b'/' {
                        latest_slash = Some(i);
                    }
                    i += 1;
                }
            },
            None => match sit.next() {
                None => {
                    return (first, first.len());
                }
                Some(sc) => {
                    if *sc == b'/' {
                        return (first, first.len() + 1);
                    } else {
                        break;
                    }
                }
            },
        }
    }

    match latest_slash {
        None => (&[], 0),
        Some(ls) => (&first[..ls], ls + 1),
    }
}

/// Convert a slice of bytes strings to a vector of Strings
///
/// This is useful for logging
pub fn bytes_strings_as_str(bytes_strings: &[Vec<u8>]) -> Vec<Cow<'_, str>> {
    bytes_strings
        .iter()
        .map(|pat| String::from_utf8_lossy(pat))
        .collect()
}

macro_rules! tracing_span_id {
    () => {{
        let span = tracing::Span::current();
        span.record("span_id", span.id().map_or(0, |id| id.into_u64()));
    }};
}

// make visible to other modules
pub(crate) use tracing_span_id;

#[cfg(test)]
mod tests {

    use super::*;

    #[test]
    fn test_common_subpath_split() {
        assert_eq!(common_subpath_split(b"foo/a", b"bar"), (b"".as_ref(), 0));
        assert_eq!(common_subpath_split(b"bar", b"foo/a"), (b"".as_ref(), 0));
        assert_eq!(
            common_subpath_split(b"foo/a", b"foo/b"),
            (b"foo".as_ref(), 4)
        );
        assert_eq!(common_subpath_split(b"foo/a", b"foox/a"), (b"".as_ref(), 0));
        assert_eq!(common_subpath_split(b"foox/a", b"foo/a"), (b"".as_ref(), 0));
        assert_eq!(
            common_subpath_split(b"foo/a/", b"foo/a/b"),
            (b"foo/a".as_ref(), 6)
        );
        assert_eq!(
            common_subpath_split(b"foo/a", b"foo/a/b"),
            (b"foo/a".as_ref(), 6)
        );
        assert_eq!(
            common_subpath_split(b"foo/a/b", b"foo/a"),
            (b"foo/a".as_ref(), 6)
        );
        assert_eq!(
            common_subpath_split(b"foo/a/b/c", b"foo/a/d/e"),
            (b"foo/a".as_ref(), 6)
        );
        assert_eq!(common_subpath_split(b"", b"foo/a"), (b"".as_ref(), 0));
        assert_eq!(common_subpath_split(b"foo/a", b""), (b"".as_ref(), 0));
    }
}
