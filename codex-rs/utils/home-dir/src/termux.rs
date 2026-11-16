use std::path::PathBuf;

/// Android application ID selected when building Codex for Termux.
pub const APP_PACKAGE: &str = app_package(option_env!("CODEX_TERMUX_APP_PACKAGE"));

/// The fixed app-private files directory for the primary Android user.
pub fn files_dir() -> PathBuf {
    PathBuf::from("/data/data").join(APP_PACKAGE).join("files")
}

const fn app_package(configured: Option<&str>) -> &str {
    let package = match configured {
        Some(package) => package,
        None => "com.termux",
    };
    assert!(
        valid_app_package(package),
        "CODEX_TERMUX_APP_PACKAGE must be a valid Android application ID"
    );
    package
}

const fn valid_app_package(package: &str) -> bool {
    let bytes = package.as_bytes();
    let mut i = 0;
    let mut needs_letter = true;
    let mut has_dot = false;
    while i < bytes.len() {
        let byte = bytes[i];
        if needs_letter {
            if !byte.is_ascii_alphabetic() {
                return false;
            }
            needs_letter = false;
        } else if byte == b'.' {
            has_dot = true;
            needs_letter = true;
        } else if !byte.is_ascii_alphanumeric() && byte != b'_' {
            return false;
        }
        i += 1;
    }
    has_dot && !needs_letter
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn uses_stock_package_by_default_and_accepts_a_custom_package() {
        assert_eq!(app_package(None), "com.termux");
        assert_eq!(app_package(Some("io.cdx")), "io.cdx");
        assert_eq!(
            files_dir(),
            PathBuf::from(format!("/data/data/{APP_PACKAGE}/files"))
        );
    }

    #[test]
    fn rejects_package_names_that_are_not_android_ids() {
        for invalid in [
            "", "single", "io..cdx", "io.cdx.", "../etc", "io/cdx", "io.1cdx",
        ] {
            assert!(!valid_app_package(invalid), "{invalid:?}");
        }
    }
}
