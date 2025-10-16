//! The Errors that may occur within the crate.

use thiserror::Error;

pub type Result<T, E = crate::Error> = std::result::Result<T, E>;

#[derive(Error, Debug)]
pub enum Error {
    // Index Errors
    #[error("Failed to build DFA {0}")]
    IndexDfaError(#[from] Box<regex_automata::dfa::dense::BuildError>),
    #[error("Index failed since anchored universal start state doesn't exist")]
    DfaHasNoStartState,
    // Vocabulary Errors
    #[error("EOS token should not be inserted into Vocabulary")]
    EOSTokenDisallowed,
    #[error(transparent)]
    TokenizersError(#[from] tokenizers::Error),
    #[error("Unsupported tokenizer for {model}: {reason}, please open an issue with the full error message: https://github.com/dottxt-ai/outlines-core/issues")]
    UnsupportedTokenizer { model: String, reason: String },
    #[error("Unable to locate EOS token for {model}")]
    UnableToLocateEosTokenId { model: String },
    #[error("Tokenizer is not supported by token processor")]
    UnsupportedByTokenProcessor,
    #[error("Decoder unpacking failed for token processor")]
    DecoderUnpackingFailed,
    #[error("Token processing failed for byte level processor")]
    ByteProcessorFailed,
    #[error("Token processing failed for byte fallback level processor")]
    ByteFallbackProcessorFailed,
    // Json Schema errors
    #[error("serde json error")]
    SerdeJsonError(#[from] serde_json::Error),
    #[error("Unsupported JSON Schema structure {0} \nMake sure it is valid to the JSON Schema specification and check if it's supported by Outlines.\nIf it should be supported, please open an issue.")]
    UnsupportedJsonSchema(Box<serde_json::Value>),
    #[error("'properties' not found or not an object")]
    PropertiesNotFound,
    #[error("'allOf' must be an array")]
    AllOfMustBeAnArray,
    #[error("'anyOf' must be an array")]
    AnyOfMustBeAnArray,
    #[error("'oneOf' must be an array")]
    OneOfMustBeAnArray,
    #[error("'prefixItems' must be an array")]
    PrefixItemsMustBeAnArray,
    #[error("Unsupported data type in enum: {0}")]
    UnsupportedEnumDataType(Box<serde_json::Value>),
    #[error("'enum' must be an array")]
    EnumMustBeAnArray,
    #[error("Unsupported data type in const: {0}")]
    UnsupportedConstDataType(Box<serde_json::Value>),
    #[error("'const' key not found in object")]
    ConstKeyNotFound,
    #[error("'$ref' must be a string")]
    RefMustBeAString,
    #[error("External references are not supported: {0}")]
    ExternalReferencesNotSupported(Box<str>),
    #[error("Invalid reference format: {0}")]
    InvalidReferenceFormat(Box<str>),
    #[error("'type' must be a string or an array of string")]
    TypeMustBeAStringOrArray,
    #[error("Unsupported type: {0}")]
    UnsupportedType(Box<str>),
    #[error("maxLength must be greater than or equal to minLength")]
    MaxBoundError,
    #[error("Format {0} is not supported by Outlines")]
    StringTypeUnsupportedFormat(Box<str>),
    #[error("Invalid reference path: {0}")]
    InvalidRefecencePath(Box<str>),
    #[error("Ref recusion limit reached: {0}")]
    RefRecursionLimitReached(usize),
}

impl Error {
    pub fn is_recursion_limit(&self) -> bool {
        matches!(self, Self::RefRecursionLimitReached(_))
    }
}

#[cfg(feature = "python-bindings")]
impl From<Error> for pyo3::PyErr {
    fn from(e: Error) -> Self {
        use pyo3::exceptions::PyValueError;
        use pyo3::PyErr;
        PyErr::new::<PyValueError, _>(e.to_string())
    }
}
