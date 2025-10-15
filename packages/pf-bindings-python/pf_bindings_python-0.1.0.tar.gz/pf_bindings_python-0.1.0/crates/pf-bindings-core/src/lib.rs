use pf_core::ffi::{pf_core_register_gdp_package, pf_core_verify_bet};
use std::ffi::CString;

#[derive(thiserror::Error, Debug)]
pub enum BindingError {
    #[error("ffi: {0}")]
    Ffi(String),
    #[error("invalid utf8")]
    Utf8(#[from] std::ffi::NulError),
}

pub type Result<T> = std::result::Result<T, BindingError>;

pub fn verify_bet(receipt_json: &str, transcript_json: &str) -> Result<()> {
    let receipt_c = CString::new(receipt_json)?;
    let transcript_c = CString::new(transcript_json)?;
    let status = pf_core_verify_bet(receipt_c.as_ptr(), transcript_c.as_ptr());
    if status == 0 {
        Ok(())
    } else {
        Err(BindingError::Ffi(last_error_message()))
    }
}

pub fn register_gdp_package(bytes: &[u8]) -> Result<()> {
    let status = pf_core_register_gdp_package(bytes.as_ptr(), bytes.len());
    if status == 0 {
        Ok(())
    } else {
        Err(BindingError::Ffi(last_error_message()))
    }
}

fn last_error_message() -> String {
    let ptr = pf_core::ffi::pf_core_last_error_message();
    if ptr.is_null() {
        "unknown error".into()
    } else {
        unsafe { std::ffi::CStr::from_ptr(ptr).to_string_lossy().into_owned() }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn invalid_payload_yields_error() {
        let err = verify_bet("{}", "{}");
        assert!(err.is_err());
    }
}
