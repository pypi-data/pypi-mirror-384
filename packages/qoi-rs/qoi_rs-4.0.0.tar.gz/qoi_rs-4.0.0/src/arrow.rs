use arrow_array::{Array, FixedSizeListArray, UInt8Array};
use pyo3::PyResult;
use pyo3::exceptions::{PyAssertionError, PyTypeError, PyValueError};
use pyo3_arrow::PyArray;

#[inline]
pub fn py_array_to_slice(array: &PyArray) -> PyResult<&[u8]> {
    match array.field().data_type() {
        arrow_schema::DataType::UInt8 => {
            match array.array().as_any().downcast_ref::<UInt8Array>() {
                Some(value) => Ok(value.values().as_ref()),
                None => Err(PyAssertionError::new_err("unable to cast u8 array")),
            }
        }
        arrow_schema::DataType::FixedSizeList(field, size) => match size {
            3 | 4 => match field.data_type() {
                arrow_schema::DataType::UInt8 => {
                    match array.array().as_any().downcast_ref::<FixedSizeListArray>() {
                        Some(value) => {
                            if value.value_offset(1) != *size {
                                Err(PyAssertionError::new_err(
                                    "second element has invalid offset",
                                ))
                            } else if let Some(value) =
                                value.values().as_any().downcast_ref::<UInt8Array>()
                            {
                                Ok(value.values().as_ref())
                            } else {
                                Err(PyAssertionError::new_err("should be unreachable"))
                            }
                        }
                        None => Err(PyAssertionError::new_err("unable to cast u8 array")),
                    }
                }
                inner_type => Err(PyTypeError::new_err(format!(
                    "invalid inner list item type: {inner_type}"
                ))),
            },
            size => Err(PyValueError::new_err(format!(
                "invalid inner list length: {size}"
            ))),
        },
        data_type => Err(PyTypeError::new_err(format!(
            "invalid list item type: {data_type}"
        ))),
    }
}

#[inline]
pub fn pixel_count(array: &PyArray) -> Option<usize> {
    match array.field().data_type() {
        arrow_schema::DataType::FixedSizeList(_, _) => Some(array.array().len()),
        _ => None,
    }
}

pub struct ImageData<'a> {
    bands: Vec<merde::CowStr<'a>>,
}

impl<'a> ImageData<'a> {
    #[inline]
    pub fn bands(&self) -> &[merde::CowStr<'a>] {
        &self.bands
    }

    #[inline]
    pub fn try_get_source_channels(&self) -> PyResult<qoi::SourceChannels> {
        let bands = self.bands();

        use qoi::SourceChannels::*;

        match bands {
            [a, b, c] => match [&**a, &**b, &**c] {
                ["R", "G", "B"] => return Ok(Rgb),
                ["B", "G", "R"] => return Ok(Bgr),
                _ => (),
            },
            [a, b, c, d] => match [&**a, &**b, &**c, &**d] {
                ["R", "G", "B", "X"] => return Ok(Rgbx),
                ["R", "G", "B", "A"] => return Ok(Rgba),
                ["B", "G", "R", "A"] => return Ok(Bgra),
                ["B", "G", "R", "X"] => return Ok(Bgrx),
                ["X", "B", "G", "R"] => return Ok(Xbgr),
                ["A", "B", "G", "R"] => return Ok(Abgr),
                ["A", "R", "G", "B"] => return Ok(Argb),
                ["X", "R", "G", "B"] => return Ok(Xrgb),
                _ => (),
            },
            _ => (),
        }

        Err(PyValueError::new_err(format!("Unknown bands: {bands:?}")))
    }
}

merde::derive! {
    impl (Deserialize) for struct ImageData<'a> { bands }
}

#[inline]
pub fn parse_pillow_array<'a>(pillow: &'a PyArray) -> PyResult<ImageData<'a>> {
    match pillow.field().data_type() {
        arrow_schema::DataType::FixedSizeList(field, _) => {
            let image_json_meta = field
                .metadata()
                .get("image")
                .ok_or_else(|| PyValueError::new_err("No image key in arrow metadata"))?;
            merde::json::from_str(image_json_meta)
                .map_err(|err| PyValueError::new_err(format!("Invalid arrow metadata: {err:?}")))
        }
        _ => Err(PyTypeError::new_err(
            "Expected FixedSizeList arrow data structure",
        )),
    }
}
