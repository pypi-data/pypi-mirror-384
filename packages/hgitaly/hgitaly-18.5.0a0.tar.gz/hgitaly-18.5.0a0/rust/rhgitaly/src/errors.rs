use prost::{
    bytes::{Bytes, BytesMut},
    Message, Name,
};
use prost_types::Any;
use tonic::{Code, Status};
use tonic_types::pb;

const HGITALY_ISSUES_URL: &str = "https://foss.heptapod.net/heptapod/hgitaly/-/issues";

pub fn unimplemented_with_issue(issue: u16) -> Status {
    Status::unimplemented(format!(
        "Not implemented. Tracking issue: {HGITALY_ISSUES_URL}/{issue}"
    ))
}

/// Copied over from tonic-types because it is private
///
/// TODO ask upstream if it can be made public
fn gen_details_bytes(code: Code, message: &str, details: Vec<Any>) -> Bytes {
    let status = pb::Status {
        code: code as i32,
        message: message.to_owned(),
        details,
    };

    let mut buf = BytesMut::with_capacity(status.encoded_len());

    // Should never panic since `buf` is initialized with sufficient capacity
    status.encode(&mut buf).unwrap();

    buf.freeze()
}

/// Provide a [`Status`] with a structured error.
///
/// This is to be used on the service-level error type, as opposed to the inner error types that
/// are defined in `errors.proto` and make up the field(s) of the service error type.
///
/// Service callers will typically have to implement the [`Name`] trait, which amounts to
/// defining the `PACKAGE` and `NAME` constants.
/// This is a bit simpler than copyning over the (private) `ToAny` trait of `tonic_types`,
/// but we might come back to it if the latter became public.
pub fn status_with_structured_error<E: Name>(code: Code, message: &str, error: E) -> Status {
    // Any.to_msg is not usable because it gives a URL starting with a /, and that
    // is not what Gitaly provides.
    let as_any = Any {
        type_url: format!("type.googleapis.com/{}.{}", E::PACKAGE, E::NAME),
        value: error.encode_to_vec(),
    };
    Status::with_details(
        code,
        message,
        gen_details_bytes(code, message, vec![as_any]),
    )
}

/// This module provides helpers about the error message types defined in `errors.proto`, for
/// use in instantiation of concrete errors at the service level.
///
/// It should be expanded with more cases as needed.
///
/// ## Features
///
/// ### Enum convenience alias.
///
/// The paths of enums defined in the message types is usually convoluted and cannot be
/// shortened without aliasing by an import. We reexpose them in this module, with just enough
/// aliasing to avoid naming collisions.
///
/// A prime example is [`PathErrorType`].
///
/// ### Factory traits
///
/// These traits are to be implemented on service-level structured error types (which typically
/// are enums). Synopsis:
///
/// ```text
/// pub trait FromSomeError {
///   fn from_some_error(err: SomeError);
///
///   fn some_error(...) -> Self { // blanket implementation using `from_some_error()` }
/// ```
///
/// Service-level code is expected to implement the trait and then probably only use the
/// blanket `some_error` associated function.
///
/// New traits should follow the same namings: putting the emphasis on the method to be
/// implemented is fairly common, but in this case the main advantage is to avoid a naming
/// collision with the error type itself (`SomeError` in the example above). Such collisions
/// are not blockers, as callers can use explicit paths or aliasing, but the point is to make
/// life easier for callers, hence any reducing of the burden is good to be taken.
///
/// [`FromResolveRevisionError`] is a prime example for simple inner error types with scalar
/// fields only.
///
/// [`FromPathError`] is a prime example for inner error types with enum fields, adding the
/// conversion to numeric value to the small conveniences for the callers.
pub mod error_messages {
    pub use crate::gitaly::path_error::ErrorType as PathErrorType;
    use crate::gitaly::{
        PathError, PathNotFoundError, ReferenceNotFoundError, ResolveRevisionError,
    };

    pub trait FromPathError: Sized {
        fn from_path_error(err: PathError) -> Self;

        fn path_error(path: Vec<u8>, err_type: PathErrorType) -> Self {
            Self::from_path_error(PathError {
                path,
                error_type: err_type as i32,
            })
        }
    }

    pub trait FromPathNotFoundError: Sized {
        fn from_path_not_found_error(err: PathNotFoundError) -> Self;

        fn path_not_found_error(path: Vec<u8>) -> Self {
            Self::from_path_not_found_error(PathNotFoundError { path })
        }
    }

    pub trait FromResolveRevisionError: Sized {
        fn from_resolve_revision_error(err: ResolveRevisionError) -> Self;

        fn resolve_revision_error(revision: Vec<u8>) -> Self {
            Self::from_resolve_revision_error(ResolveRevisionError { revision })
        }
    }

    pub trait FromReferenceNotFoundError: Sized {
        fn from_reference_not_found_error(err: ReferenceNotFoundError) -> Self;

        fn reference_not_found_error(reference_name: Vec<u8>) -> Self {
            Self::from_reference_not_found_error(ReferenceNotFoundError { reference_name })
        }
    }
}

pub use error_messages::*;
