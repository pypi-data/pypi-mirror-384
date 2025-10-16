mod arrow;

use pyo3::{exceptions::PyValueError, prelude::*};

#[derive(FromPyObject)]
enum Data {
    Bytes(pyo3_bytes::PyBytes), // should be first!
    Arrow(pyo3_arrow::PyArray),
    Channel3(Vec<(u8, u8, u8)>),
    Channel4(Vec<(u8, u8, u8, u8)>),
}

impl Data {
    #[inline]
    fn as_byte_slice(&self) -> PyResult<&[u8]> {
        #[inline]
        fn bytes<T>(slice: &[T]) -> Option<&[u8]> {
            let len: usize = slice.len().checked_mul(size_of::<T>())?;
            Some(unsafe { std::slice::from_raw_parts(slice.as_ptr() as *const u8, len) })
        }

        const ERROR: &str = "image is too big";

        match self {
            Data::Arrow(array) => crate::arrow::py_array_to_slice(array),
            Data::Bytes(bytes) => Ok(bytes.as_slice()),
            Data::Channel3(pixels) => bytes::<(u8, u8, u8)>(pixels)
                .ok_or(ERROR)
                .map_err(PyValueError::new_err),
            Data::Channel4(pixels) => bytes::<(u8, u8, u8, u8)>(pixels)
                .ok_or(ERROR)
                .map_err(PyValueError::new_err),
        }
    }

    #[inline]
    fn pixel_count(&self) -> Option<usize> {
        match self {
            Data::Arrow(array) => crate::arrow::pixel_count(array),
            Data::Bytes(_) => None,
            Data::Channel3(pixels) => Some(pixels.len()),
            Data::Channel4(pixels) => Some(pixels.len()),
        }
    }
}

#[pymodule]
mod _qoi {
    use std::borrow::Cow;

    use pyo3::exceptions::{PyAssertionError, PyValueError};
    use pyo3::{pyclass, pyfunction, pymethods, Bound, Py, PyAny, PyErr, PyResult, Python};
    use pyo3_arrow::PyArray;
    use qoi::{Channels, ColorSpace, Decoder, Encoder, EncoderBuilder, SourceChannels};

    use crate::Data;
    use crate::arrow::py_array_to_slice;

    const LINEAR: &str = "linear";
    const SRGB: &str = "SRGB";
    const COLOUR_SPACES: [&str; 2] = [LINEAR, SRGB];

    fn to_py_error(error: qoi::Error) -> PyErr {
        match &error {
            qoi::Error::InvalidChannels { .. }
            | qoi::Error::InvalidColorSpace { .. }
            | qoi::Error::InvalidImageDimensions { .. }
            | qoi::Error::InvalidImageLength { .. }
            | qoi::Error::InvalidMagic { .. }
            | qoi::Error::InvalidPadding
            | qoi::Error::UnexpectedBufferEnd => PyValueError::new_err(error.to_string()),
            qoi::Error::OutputBufferTooSmall { .. }
            | qoi::Error::InvalidImageStride { .. }
            | qoi::Error::IoError(_) => PyAssertionError::new_err(error.to_string()),
        }
    }

    #[inline]
    fn parse_raw_channels(channels: &str) -> PyResult<SourceChannels> {
        const COUNT: usize = 10;
        const VALUES: [(&str, SourceChannels); COUNT] = [
            ("Rgb", SourceChannels::Rgb),
            ("Bgr", SourceChannels::Bgr),
            ("Rgba", SourceChannels::Rgba),
            ("Argb", SourceChannels::Argb),
            ("Rgbx", SourceChannels::Rgbx),
            ("Xrgb", SourceChannels::Xrgb),
            ("Bgra", SourceChannels::Bgra),
            ("Abgr", SourceChannels::Abgr),
            ("Bgrx", SourceChannels::Bgrx),
            ("Xbgr", SourceChannels::Xbgr),
        ];

        for (s, value) in VALUES {
            if s.eq_ignore_ascii_case(channels) {
                return Ok(value);
            }
        }

        Err(PyValueError::new_err(format!(
            "invalid channels: {channels:?}"
        )))
    }

    #[inline]
    fn parse_colour_space(colour_space: &str) -> PyResult<ColorSpace> {
        if colour_space.eq_ignore_ascii_case(LINEAR) {
            Ok(ColorSpace::Linear)
        } else if colour_space.eq_ignore_ascii_case(SRGB) {
            Ok(ColorSpace::Srgb)
        } else {
            Err(PyValueError::new_err(format!(
                "invalid colour space, needs to be one of {COLOUR_SPACES:?}"
            )))
        }
    }

    #[inline]
    fn to_python_bytes<'py>(
        py: Python<'py>,
        encoder: Encoder,
    ) -> PyResult<Bound<'py, pyo3::types::PyBytes>> {
        let data = encoder.encode_to_vec().map_err(to_py_error)?;

        Ok(pyo3::types::PyBytes::new(py, &data))
    }

    #[pyfunction]
    #[pyo3(signature = (data, /, *, width, height, colour_space = None, input_channels = None))]
    #[inline]
    fn encode<'py>(
        py: Python<'py>,
        data: Data,
        width: u32,
        height: u32,
        colour_space: Option<&str>,
        input_channels: Option<&str>, // channels
    ) -> PyResult<Bound<'py, pyo3::types::PyBytes>> {
        let builder = {
            let data = data.as_byte_slice()?;

            EncoderBuilder::new(data, width, height)
        };
        let builder = if let Some(input_channels) = input_channels {
            builder.source_channels(parse_raw_channels(input_channels)?)
        } else {
            builder
        };
        let mut encoder = builder.build().map_err(to_py_error)?;

        if let Some(pixel_count) = data.pixel_count()
            && pixel_count != encoder.header().n_pixels()
        {
            return Err(PyValueError::new_err(format!(
                "got {pixel_count} pixels, image can't be {width}x{height}"
            )));
        }

        if let Some(colour_space) = colour_space {
            let colour_space = parse_colour_space(colour_space)?;
            encoder = encoder.with_colorspace(colour_space);
        }

        to_python_bytes(py, encoder)
    }

    #[pyfunction]
    #[pyo3(signature = (pillow_image, /, *, colour_space = None))]
    fn encode_pillow<'py>(
        py: Python<'py>,
        pillow_image: Py<PyAny>,
        colour_space: Option<&str>,
    ) -> PyResult<Bound<'py, pyo3::types::PyBytes>> {
        let data: PyArray = pillow_image.extract(py)?;

        let width = pillow_image.getattr(py, "width")?.extract(py)?;
        let height = pillow_image.getattr(py, "height")?.extract(py)?;

        let metadata = crate::arrow::parse_pillow_array(&data)?;
        let raw_channels = metadata.try_get_source_channels()?;

        let mut encoder = EncoderBuilder::new(py_array_to_slice(&data)?, width, height)
            .source_channels(raw_channels)
            .build()
            .map_err(to_py_error)?;

        if let Some(colour_space) = colour_space {
            let colour_space = parse_colour_space(colour_space)?;
            encoder = encoder.with_colorspace(colour_space);
        }

        to_python_bytes(py, encoder)
    }

    #[pyclass(eq)]
    #[derive(PartialEq)]
    struct Image {
        #[pyo3(get)]
        width: u32,
        #[pyo3(get)]
        height: u32,
        #[pyo3(get)]
        data: Cow<'static, [u8]>,
        channels: Channels,
        colourspace: ColorSpace,
    }

    #[pymethods]
    impl Image {
        #[getter]
        fn mode(&self) -> &'static str {
            match self.channels {
                Channels::Rgb => "RGB",
                Channels::Rgba => "RGBA",
            }
        }

        #[getter]
        fn channels(&self) -> u8 {
            self.channels.as_u8()
        }

        #[getter]
        fn colour_space(&self) -> &'static str {
            match self.colourspace {
                ColorSpace::Linear => LINEAR,
                ColorSpace::Srgb => SRGB,
            }
        }

        fn __repr__(&self) -> PyResult<String> {
            let mode = self.mode();
            let Self { width, height, .. } = self;
            let color_space = self.colour_space();
            let id = self as *const Self;
            Ok(format!(
                "<qoi_rs._qoi.Image colour_space={color_space} mode={mode} size={width}x{height} at {id:?}>"
            ))
        }
    }

    #[pyfunction]
    #[pyo3(signature = (data, /))]
    fn decode(data: pyo3_bytes::PyBytes) -> PyResult<Image> {
        let mut decoder = Decoder::new(&data).map_err(to_py_error)?;

        let header = decoder.header();

        Ok(Image {
            width: header.width,
            height: header.height,
            channels: header.channels,
            colourspace: header.colorspace,
            data: decoder.decode_to_vec().map_err(to_py_error)?.into(),
        })
    }
}
