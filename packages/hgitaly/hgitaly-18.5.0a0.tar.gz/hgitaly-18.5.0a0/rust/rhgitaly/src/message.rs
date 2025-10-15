// Copyright 2023 Georges Racinet <georges.racinet@octobus.net>
//
// This software may be used and distributed according to the terms of the
// GNU General Public License version 2 or any later version.
// SPDX-License-Identifier: GPL-2.0-or-later
//! Adapters for common Gitaly / HGitaly messages
use crate::gitaly::{
    get_blobs_request::RevisionPath, CommitAuthor, GetBlobResponse, GetBlobsResponse, GitCommit,
    TreeEntryResponse,
};
use crate::mercurial::ObjectMetadata;
use hg::errors::HgError;
use hg::revlog::changelog::{Changelog, ChangelogEntry, ChangelogRevisionData};
use hg::revlog::{NodePrefix, RevlogError, NULL_REVISION};
use prost_types::Timestamp;
use std::fmt;
use std::str::FromStr;

#[derive(Debug, PartialEq, Eq)]
pub enum TimeStampParseError {
    Empty,
    MissingTimeZone,
    InvalidUtcTime(String),
}

impl fmt::Display for TimeStampParseError {
    // This trait requires `fmt` with this exact signature.
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        // Write strictly the first element into the supplied output
        // stream: `f`. Returns `fmt::Result` which indicates whether the
        // operation succeeded or failed. Note that `write!` uses syntax which
        // is very similar to `println!`.
        match *self {
            Self::Empty => write!(f, "empty timestamp line"),
            Self::MissingTimeZone => write!(f, "timestamp line without a timezone"),
            Self::InvalidUtcTime(ref s) => write!(f, "invalid UTC time in timestamp line: {}", s),
        }
    }
}

/// Parse the timestamp line from changelog data into numbers
///
/// This is meant to be equivalent to the reference Python implementation.
/// See the `_raw_date` and `date` properties of class changelog.changelogrevision in the
/// Python Mercurial reference implementation.
/// In particular the Python implementation converts seconds to `float` (in practice, the data does
/// never seem to contain a fractional part). Using `f64` because `f32` introduces rounding errors.
/// TODO consider version of Mercurial 6.7 when we can use it.
pub fn parse_timestamp_line(line: &[u8]) -> Result<(f64, i32), TimeStampParseError> {
    if line.is_empty() {
        return Err(TimeStampParseError::Empty);
    }
    let mut split = line.splitn(3, |b| *b == b' ');
    let time_str =
        String::from_utf8_lossy(split.next().expect("SplitN always emits at least once"));
    let time = f64::from_str(&time_str)
        .map_err(|e| TimeStampParseError::InvalidUtcTime(format!("{}", e)))?;
    let tz_str = String::from_utf8_lossy(split.next().ok_or(TimeStampParseError::MissingTimeZone)?);
    // according to reference implementation "Various tools did silly things with the timezone"
    // and then it defaults to 0.
    let tz_offset = i32::from_str(&tz_str).unwrap_or(0);
    Ok((time, tz_offset))
}

#[derive(Debug, PartialEq, Eq)]
struct PersonWithEmail {
    person: Vec<u8>,
    email: Option<Vec<u8>>,
}

/// Inspired by the [trim_ascii functions](std::primitite.slice::trim_ascii_end), with the following
///
/// diffenences:
/// - we need to strip also double quotes
/// - we don't care about being `const`
fn trim_person_end(person: &[u8]) -> &[u8] {
    let mut bytes = person;
    while let [rest @ .., last] = bytes {
        if *last == b' ' || *last == b'"' {
            bytes = rest
        } else {
            break;
        }
    }
    bytes
}

fn copy_cleanup_person(person: &[u8]) -> Vec<u8> {
    let trimmed = trim_person_end(person);
    let mut res = Vec::with_capacity(trimmed.len());
    let mut it = trimmed.iter();

    let mut at_start = true;
    while let Some(b) = it.next() {
        let current = *b;
        if at_start && (current == b' ' || current == b'"') {
            continue;
        } else {
            at_start = false
        };

        if current == b'\\' {
            match it.next() {
                None => {
                    res.push(current);
                }
                Some(c) => {
                    let after_backslash = *c;
                    if after_backslash == b'"' {
                        res.push(b'"');
                    } else {
                        res.push(current);
                        res.push(after_backslash);
                    }
                }
            }
        } else {
            res.push(current);
        }
    }
    res
}

fn copy_replace_dot(s: &[u8]) -> Vec<u8> {
    s.iter()
        .map(|b| if *b == b'.' { b' ' } else { *b })
        .collect()
}

/// Parse the full user line, typically in the form "Fullname <email address>"
///
/// This follows the Python reference implementation as `mercurial.utils.stringutil.person()`,
/// itself interpreting the line as per RFC 5322.
fn parse_user_line(line: &[u8]) -> PersonWithEmail {
    let mut at_split = line.splitn(2, |b| *b == b'@');
    let before_at = at_split.next().expect("SplitN always emits at least once");
    match at_split.next() {
        None => PersonWithEmail {
            person: line.into(),
            email: None,
        },
        Some(after_at) => {
            let mut opening_email_split = before_at.splitn(2, |b| *b == b'<');
            let person = copy_cleanup_person(
                opening_email_split
                    .next()
                    .expect("SplitN always emits at least once"),
            );
            match opening_email_split.next() {
                Some(email_before_at) => {
                    let mut email_after_at_split = after_at.splitn(2, |b| *b == b'>');
                    let email_after_at = email_after_at_split.next().expect("SplitN again");
                    match email_after_at_split.next() {
                        Some(_) => {
                            let mut email = email_before_at.to_vec();
                            email.push(b'@');
                            email.extend_from_slice(email_after_at);
                            PersonWithEmail {
                                person,
                                email: Some(email),
                            }
                        }
                        None => PersonWithEmail {
                            person,
                            email: None,
                        },
                    }
                }
                None => PersonWithEmail {
                    person: copy_replace_dot(before_at),
                    email: Some(line.to_vec()),
                },
            }
        }
    }
}

/// Parse ChangelogEntry timestamp line, returning information as expected in Gitaly fields
fn gitaly_timestamp_tz(timestamp_line: &[u8]) -> Result<(Timestamp, String), TimeStampParseError> {
    let (seconds, mut tz) = parse_timestamp_line(timestamp_line)?;

    let tz_sign = if tz <= 0 { '+' } else { '-' };
    if tz <= 0 {
        tz = -tz
    };
    let tz_minutes = tz / 60;
    Ok((
        Timestamp {
            seconds: seconds as i64,
            nanos: 0,
        }, // TODO why not provide nanos, then?
        format!("{}{:02}{:02}", tz_sign, tz_minutes / 60, tz_minutes % 60),
    ))
}

pub fn commit<'changelog>(entry: ChangelogEntry<'changelog>) -> Result<GitCommit, RevlogError> {
    let node_id = format!("{:x}", entry.as_revlog_entry().node());

    let mut parent_ids = Vec::new();
    if let Some(parent) = entry.p1_entry()? {
        parent_ids.push(format!("{:x}", parent.as_revlog_entry().node()));
    }
    if let Some(parent) = entry.p2_entry()? {
        parent_ids.push(format!("{:x}", parent.as_revlog_entry().node()));
    }

    let data: ChangelogRevisionData<'changelog> = entry.data()?;

    let body = data.description();
    // changeset description cannot be empty unless some manual tinkering occurred,
    // but we are still treating it, hence returning an empty subhject in that case.
    let subject = body.splitn(2, |b| *b == b'\n').next().unwrap_or(&[]);

    let author = commit_author(&data)
        .map_err(|e| HgError::corrupted(format!("Changeset {}: {}", node_id, e)))?;

    Ok(GitCommit {
        id: node_id,
        parent_ids,
        subject: subject.to_vec(),
        body: body.to_vec(),
        body_size: body.len() as i64,
        committer: Some(author.clone()),
        author: Some(author),
        ..Default::default()
    })
}

fn commit_author(cr_data: &ChangelogRevisionData) -> Result<CommitAuthor, TimeStampParseError> {
    let person_with_email = parse_user_line(cr_data.user());
    let (ts, tz) = gitaly_timestamp_tz(cr_data.timestamp_line())?;

    Ok(CommitAuthor {
        name: person_with_email.person,
        email: person_with_email.email.unwrap_or_default(),
        date: Some(ts),
        timezone: tz.into(),
    })
}

/// Return the [`GitCommit`] message for a changeset given by Node prefix.
///
/// If the Node prefix resolves to [`NULL_REVISION`], the return value is `Ok(None)`.
pub fn commit_for_node_prefix(
    cl: &Changelog,
    node_prefix: NodePrefix,
) -> Result<Option<GitCommit>, RevlogError> {
    let rev = cl.rev_from_node(node_prefix)?;
    if rev == NULL_REVISION {
        return Ok(None);
    }

    Ok(Some(commit(cl.entry_for_unchecked_rev(rev.into())?)?))
}

/// Return the [`GitCommit`] message for a changeset given by Node prefix, or `None`
///
/// If the Node prefix does not resolve, or resolves to [`NULL_REVISION`],
/// the return value is `Ok(None)`.
pub fn commit_for_node_prefix_or_none(
    cl: &Changelog,
    node_prefix: NodePrefix,
) -> Result<Option<GitCommit>, RevlogError> {
    match commit_for_node_prefix(cl, node_prefix) {
        // TODO discuss upstream: InvalidRevision is incorrect wording:
        // it does represent both invalid input (working dir Node),
        // and not found node prefixes. The latter case justifies our
        // choice.
        // Note that at this stage we cannot tell apart NodePrefix due to
        // caller passing a hash from those read in state files (would be an
        // inconsistency for them not to resolve).
        Err(RevlogError::InvalidRevision(_)) => Ok(None),
        Err(e) => Err(e),
        Ok(r) => Ok(r),
    }
}

/// Common methods to producde blob responses, with or without metadata.
///
/// The usual Gitaly protocol convention when streaming several chunks of data for a single
/// object is to include metadata in the first response only for that object.
///
/// When several objects are streamed, as is, e.g, the case of the `GetBlobs` gRPC method,
/// the presence of metadata tells clients that the stream started treating another object.
pub trait BlobResponseChunk {
    fn with_metadata(chunk: &[u8], md: ObjectMetadata) -> Self;
    fn only_data(chunk: &[u8]) -> Self;
}

impl BlobResponseChunk for GetBlobsResponse {
    fn with_metadata(chunk: &[u8], md: ObjectMetadata) -> Self {
        let rev_path = md
            .revision_path
            .unwrap_or_else(|| (String::new(), Vec::new()));
        GetBlobsResponse {
            data: chunk.to_vec(),
            mode: md.mode,
            revision: rev_path.0,
            path: rev_path.1,
            is_submodule: false,
            oid: md.oid,
            size: md.size,
            r#type: md.obj_type as i32,
        }
    }
    fn only_data(chunk: &[u8]) -> Self {
        GetBlobsResponse {
            data: chunk.to_vec(),
            ..Default::default()
        }
    }
}

impl BlobResponseChunk for GetBlobResponse {
    fn with_metadata(chunk: &[u8], md: ObjectMetadata) -> Self {
        GetBlobResponse {
            data: chunk.to_vec(),
            oid: md.oid,
            size: md.size,
        }
    }
    fn only_data(chunk: &[u8]) -> Self {
        GetBlobResponse {
            data: chunk.to_vec(),
            ..Default::default()
        }
    }
}

impl BlobResponseChunk for TreeEntryResponse {
    fn with_metadata(chunk: &[u8], md: ObjectMetadata) -> Self {
        TreeEntryResponse {
            data: chunk.to_vec(),
            mode: md.mode,
            oid: md.oid,
            size: md.size,
            // TreeEntryResponse.ObjectType and shared.proto's ObjectType
            // do differ by a shift of 1 (because of `UNKNOWN = 0` in the latter)
            r#type: md.obj_type as i32 - 1,
        }
    }
    fn only_data(chunk: &[u8]) -> Self {
        TreeEntryResponse {
            data: chunk.to_vec(),
            ..Default::default()
        }
    }
}

/// Return a suitable empty [`GetBlobsResponse`] for unresolved [`RevisionPath`]
///
/// The protocol specifies that all fields are to be empty, except for `revision` and `path`
/// that are echoes of the request.
pub fn empty_blobs_response(rev_path: RevisionPath) -> GetBlobsResponse {
    GetBlobsResponse {
        revision: rev_path.revision,
        path: rev_path.path,
        ..Default::default()
    }
}

#[cfg(test)]
mod tests {

    use super::*;

    #[test]
    fn test_parse_timestamp_line() {
        assert_eq!(
            parse_timestamp_line(b"1679951671 0").unwrap(),
            (1679951671.0, 0)
        );
        assert_eq!(
            parse_timestamp_line(b"1626786076.0 0").unwrap(),
            (1626786076.0, 0)
        );
        assert_eq!(
            parse_timestamp_line(b"1626786076.0 -7200").unwrap(),
            (1626786076.0, -7200)
        );
        assert_eq!(
            parse_timestamp_line(b"1626786076.0 4500 any other stuff").unwrap(),
            (1626786076.0, 4500)
        );
        assert_eq!(
            parse_timestamp_line(b"16.a 0"),
            Err(TimeStampParseError::InvalidUtcTime(
                "invalid float literal".to_string()
            ))
        );
        assert_eq!(
            parse_timestamp_line(b"1626786076.0"),
            Err(TimeStampParseError::MissingTimeZone),
        );
        assert_eq!(parse_timestamp_line(b""), Err(TimeStampParseError::Empty));
    }

    #[test]
    fn test_gitaly_timestamp_tz() -> Result<(), TimeStampParseError> {
        // full form
        assert_eq!(
            gitaly_timestamp_tz(b"1626786076.0 -7200")?,
            (
                Timestamp {
                    seconds: 1626786076,
                    nanos: 0
                },
                "+0200".to_string()
            )
        );
        // various timezones
        assert_eq!(&gitaly_timestamp_tz(b"0 -1800")?.1, "+0030");
        assert_eq!(&gitaly_timestamp_tz(b"0 5400")?.1, "-0130");
        Ok(())
    }

    /// These are the same examples as in Python's `mercurial.util.stringutil.person`
    #[test]
    fn test_parse_user_line() {
        assert_eq!(
            parse_user_line(b"foo@bar"),
            PersonWithEmail {
                person: b"foo".to_vec(),
                email: Some(b"foo@bar".to_vec())
            }
        );
        assert_eq!(
            parse_user_line(b"Foo Bar <foo@bar>"),
            PersonWithEmail {
                person: b"Foo Bar".to_vec(),
                email: Some(b"foo@bar".to_vec())
            }
        );
        assert_eq!(
            parse_user_line(b"\"Foo \\\"buz\\\" Bar\" <foo@bar>"),
            PersonWithEmail {
                person: b"Foo \"buz\" Bar".to_vec(),
                email: Some(b"foo@bar".to_vec())
            }
        );
        //  The following are invalid, but do exist in real-life
        assert_eq!(
            parse_user_line(b"Foo \"buz\" Bar <foo@bar>"),
            PersonWithEmail {
                person: b"Foo \"buz\" Bar".to_vec(),
                email: Some(b"foo@bar".to_vec())
            }
        );
        assert_eq!(
            parse_user_line(b"\"Foo Bar <foo@bar>"),
            PersonWithEmail {
                person: b"Foo Bar".to_vec(),
                email: Some(b"foo@bar".to_vec())
            }
        );
    }

    #[test]
    fn more_test_parse_user_line() {
        assert_eq!(
            parse_user_line(b"some.foo@bar"),
            PersonWithEmail {
                person: b"some foo".to_vec(),
                email: Some(b"some.foo@bar".to_vec())
            }
        );
    }
}
