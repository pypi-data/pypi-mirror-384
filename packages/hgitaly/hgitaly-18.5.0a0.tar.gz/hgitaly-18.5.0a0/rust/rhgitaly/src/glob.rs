// Mostly taken from hg-core/src/matchers.rs
//
// Copyright 2019 Raphaël Gomès <rgomes@octobus.net>
// Copyright 2024 Georges Racinet <georges.racinet@octobus.net> for the minor adaptations
//
// This software may be used and distributed according to the terms of the
// GNU General Public License version 2 or any later version.
use hg::utils::strings::SliceExt;
use lazy_static::lazy_static;
use regex::bytes::Regex;
use std::io::Write;

lazy_static! {
    static ref RE_ESCAPE: Vec<Vec<u8>> = {
        let mut v: Vec<Vec<u8>> = (0..=255).map(|byte| vec![byte]).collect();
        let to_escape = b"()[]{}?*+-|^$\\.&~#\t\n\r\x0b\x0c";
        for byte in to_escape {
            v[*byte as usize].insert(0, b'\\');
        }
        v
    };
}

/// These are matched in order
const GLOB_REPLACEMENTS: &[(&[u8], &[u8])] =
    &[(b"*/", b"(?:.*/)?"), (b"*", b".*"), (b"", b"[^/]*")];

/// Transforms a glob pattern into a regex
///
/// TODO for HGitaly we do not want the general expressions
/// such as brackets (curly or not)
pub fn glob_to_regex_bytes_pattern(pat: &[u8]) -> Vec<u8> {
    let mut input = pat;
    let mut res: Vec<u8> = vec![];
    let mut group_depth = 0;

    while let Some((c, rest)) = input.split_first() {
        input = rest;

        match c {
            b'*' => {
                for (source, repl) in GLOB_REPLACEMENTS {
                    if let Some(rest) = input.drop_prefix(source) {
                        input = rest;
                        res.extend(*repl);
                        break;
                    }
                }
            }
            b'?' => res.extend(b"."),
            b'[' => {
                match input.iter().skip(1).position(|b| *b == b']') {
                    None => res.extend(b"\\["),
                    Some(end) => {
                        // Account for the one we skipped
                        let end = end + 1;

                        res.extend(b"[");

                        for (i, b) in input[..end].iter().enumerate() {
                            if *b == b'!' && i == 0 {
                                res.extend(b"^")
                            } else if *b == b'^' && i == 0 {
                                res.extend(b"\\^")
                            } else if *b == b'\\' {
                                res.extend(b"\\\\")
                            } else {
                                res.push(*b)
                            }
                        }
                        res.extend(b"]");
                        input = &input[end + 1..];
                    }
                }
            }
            b'{' => {
                group_depth += 1;
                res.extend(b"(?:")
            }
            b'}' if group_depth > 0 => {
                group_depth -= 1;
                res.extend(b")");
            }
            b',' if group_depth > 0 => res.extend(b"|"),
            b'\\' => {
                let c = {
                    if let Some((c, rest)) = input.split_first() {
                        input = rest;
                        c
                    } else {
                        c
                    }
                };
                res.extend(&RE_ESCAPE[*c as usize])
            }
            _ => res.extend(&RE_ESCAPE[*c as usize]),
        }
    }
    res
}

/// Convert a glob pattern into a regular expression
///
/// Taken from [`hg::matchers::re_matcher`] with the following changes:
///
///   - we don't need the multithread optimizations, hence to enclose with thread-locals
///     in `hg::matchers::RegexMatcher`.
///   - we don't need huge regexps, as the main use case in RHGitaly is `fnmatch` on path segments.
#[allow(rustdoc::broken_intra_doc_links)]
pub fn glob_to_regex(pat: &[u8]) -> Regex {
    let rx_pat = glob_to_regex_bytes_pattern(pat);
    // The `regex` crate adds `.*` to the start and end of expressions if there
    // are no anchors, so add the start anchor.
    bytes_regex_build(&rx_pat, vec![b'^', b'(', b'?', b':'], b")")
        .expect("Glob pattern conversion should be a valid regex")
}

/// Build a [`Regex`] from pattern bytes, escaping all non 7-bit ASCII characters
///
/// Parameters:
///
/// - `escaped_bytes` is the internal accumulator that will be used. Allows preallocation, and
///   more importantly, prefilling with a start sequence.
/// - `trailer` is bytes to append once the conversion is done. Typical use case would be to
///    match an opening parenthesis in the prefill passed in `escaped_bytes`.
pub fn bytes_regex_build(
    pattern: &[u8],
    mut escaped_bytes: Vec<u8>,
    trailer: &[u8],
) -> Result<Regex, regex::Error> {
    for byte in pattern {
        if *byte > 127 {
            write!(escaped_bytes, "\\x{:x}", *byte).unwrap();
        } else {
            escaped_bytes.push(*byte);
        }
    }
    escaped_bytes.extend_from_slice(trailer);

    // Avoid the cost of UTF8 checking
    //
    // # Safety
    // This is safe because we escaped all non-ASCII bytes.
    let pattern_string = unsafe { String::from_utf8_unchecked(escaped_bytes) };
    regex::bytes::RegexBuilder::new(&pattern_string)
        .unicode(false)
        .build()
}

/// Same as `regex::escape_into`, for bytes strings
///
/// We can have some trouble if Regex meta-characters can happen in multi-bytes encodings,
/// without the end-user meaning to (cannot happen with UTF-8 because each byte of non ascii
/// code point is >127).
fn bytes_regex_escape_into(lit: &[u8], buf: &mut Vec<u8>) {
    for c in lit {
        if let Some(ch) = char::from_u32(*c as u32) {
            if regex_syntax::is_meta_character(ch) {
                buf.push(b'\\');
            }
        }
        buf.push(*c);
    }
}

fn star_pattern_to_regex_into(pat: &[u8], buf: &mut Vec<u8>) {
    let mut peekable_split = pat.split(|b| *b == b'*').peekable();
    while let Some(part) = peekable_split.next() {
        bytes_regex_escape_into(part, buf);
        if peekable_split.peek().is_some() {
            buf.extend_from_slice(b".*?");
        }
    }
}

/// Build a [`Regex`] from a pattern where the only recognized wildcard is `*`
///
/// This is used in some GitLab matching logic, and is strictly stricted than glob and fnmatch
pub fn star_pattern_to_regex(pat: &[u8]) -> Regex {
    // Making room for two wildcards. One is frequent, two happens, three will trigger reallocation.
    let mut replaced = Vec::with_capacity(pat.len() + 4);
    replaced.push(b'^');
    star_pattern_to_regex_into(pat, &mut replaced);
    replaced.push(b'$');
    // capacity: with any luck we don't need to escape anything
    bytes_regex_build(&replaced, Vec::with_capacity(replaced.len()), b"")
        .expect("Star pattern conversion should be a valid regex")
}

/// Same as [`star_pattern_to_regex`] for several patterns, with an implicit OR logic connector
pub fn star_patterns_to_regex(pats: &[Vec<u8>]) -> Regex {
    let tot_len: usize = pats.iter().map(|p| p.len()).sum();
    let mut replaced = Vec::with_capacity(tot_len + 5 * pats.len() + 2);
    replaced.push(b'^');
    let mut peekable = pats.iter().peekable();
    while let Some(pat) = peekable.next() {
        replaced.push(b'(');
        star_pattern_to_regex_into(pat, &mut replaced);
        replaced.push(b')');
        if peekable.peek().is_some() {
            replaced.push(b'|');
        }
    }
    replaced.push(b'$');
    bytes_regex_build(&replaced, Vec::with_capacity(replaced.len()), b"")
        .expect("Star pattern conversion should be a valid regex")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_star_pattern_to_regex() {
        let rx = star_pattern_to_regex(b"branch/*");
        assert_eq!(rx.as_str(), "^branch/.*?$");

        let rx = star_pattern_to_regex(b"topic/*/foo");
        assert_eq!(rx.as_str(), "^topic/.*?/foo$");

        let rx = star_pattern_to_regex(b"topic/*/foo*");
        assert_eq!(rx.as_str(), "^topic/.*?/foo.*?$");

        let rx = star_pattern_to_regex(b"[*]");
        assert_eq!(rx.as_str(), r"^\[.*?\]$");
    }

    #[test]
    fn test_star_patterns_to_regex() {
        let rx = star_patterns_to_regex(&vec![b"branch/*".to_vec(), b"topic/*/foo".to_vec()]);
        assert_eq!(rx.as_str(), "^(branch/.*?)|(topic/.*?/foo)$");
    }
}
