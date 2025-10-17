pub mod context;
pub mod deid;
pub mod group;
pub mod meta;
pub mod parse;
pub mod utils;

use pyo3::prelude::*;

pub fn register(py: Python<'_>, parent: &Bound<'_, PyModule>) -> PyResult<()> {
    let m = PyModule::new(py, "dcm")?;
    let sys_modules = py.import("sys")?.getattr("modules")?;
    sys_modules.set_item("fw_file_rs.dcm", &m)?;
    m.add_function(wrap_pyfunction!(parse::parse_header, &m)?)?;
    m.add_function(wrap_pyfunction!(meta::get_fw_meta, &m)?)?;
    m.add_function(wrap_pyfunction!(utils::read_until_pixels, &m)?)?;
    m.add_function(wrap_pyfunction!(group::group_series, &m)?)?;
    m.add_function(wrap_pyfunction!(utils::create_dcm_as_bytes, &m)?)?;
    m.add_class::<context::Context>()?;
    m.add_class::<deid::DeidProfile>()?;
    parent.add_submodule(&m)?;
    Ok(())
}
