use std::env;
use std::fs::File;
use std::io::{Error, ErrorKind, Read};
use std::path::Path;

use build_const::ConstWriter;

const LICENSES_CACHE: &str = "../dependencies/licenses_data/cache.zstd";
const SPDX_DATA: &str = "../dependencies/spdx-license-list-data/json/details";

fn build_constants() -> Result<(), Box<dyn std::error::Error>> {
    // use `for_build` in `build.rs`
    let mut consts = ConstWriter::for_build("constants")?.finish_dependencies();
    let mut version = String::new();
    File::open("../../hgitaly/VERSION")?.read_to_string(&mut version)?;

    // Add a value that is a result of "complex" calculations
    consts.add_value("HGITALY_VERSION", "&str", version.trim());
    Ok(())
}

fn build_licenses_cache() -> Result<(), Box<dyn std::error::Error>> {
    let cache_path = Path::new(LICENSES_CACHE);
    if cache_path.exists() {
        println!("cargo:warning=askalono cache file already exists; not re-building");
        return Ok(());
    }

    if let Some(parent) = cache_path.parent() {
        std::fs::create_dir_all(parent).map_err(|e| {
            Error::new(
                ErrorKind::Other,
                format!(
                    "Could not ensure parent directory of '{}': {}",
                    SPDX_DATA, e
                ),
            )
        })?;
    }

    let store_texts = env::var("CARGO_FEATURE_DIAGNOSTICS").is_ok();

    let mut store = askalono::Store::new();
    store
        .load_spdx(Path::new(SPDX_DATA), store_texts)
        .map_err(|e| {
            Error::new(
                ErrorKind::Other,
                format!(
                    "Could not create an askalono store from SPDX data \
                     expected at '{}': {}",
                    SPDX_DATA, e
                ),
            )
        })?;
    let mut cache = File::create(LICENSES_CACHE)?;
    Ok(store.to_cache(&mut cache)?)
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    build_constants()?;
    build_licenses_cache()?;
    tonic_build::configure()
        .build_server(true)
        .out_dir("src/generated")
        .protoc_arg("--experimental_allow_proto3_optional")
        .generate_default_stubs(true)
        .compile(
            &[
                "../../protos/analysis.proto",
                "../../protos/blob.proto",
                "../../protos/commit.proto",
                "../../protos/diff.proto",
                "../../protos/mercurial-aux-git.proto",
                "../../protos/mercurial-changeset.proto",
                "../../protos/mercurial-operations.proto",
                "../../protos/mercurial-repository.proto",
                "../../protos/ref.proto",
                "../../protos/remote.proto",
                "../../protos/operations.proto",
                "../../protos/repository.proto",
                "../../protos/server.proto",
            ],
            &[
                // include paths
                "../../protos",
                "../dependencies/proto",
            ],
        )
        .unwrap();
    Ok(())
}
