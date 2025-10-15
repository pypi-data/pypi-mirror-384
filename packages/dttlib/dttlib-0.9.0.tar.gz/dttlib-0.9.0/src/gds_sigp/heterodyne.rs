use crate::__BindgenComplex;
use pipelines::complex::c128;

pub fn mix_down(x: &[f64], step_s: f64, time_offset_s: f64, mix_freq_hz: f64) -> Vec<c128> {
    let n = x.len();
    let y = Vec::with_capacity(n);
    unsafe {
        crate::dInterleavedMixdown(
            x.as_ptr(),
            y.as_slice().as_ptr() as *mut __BindgenComplex<f64>,
            n as i32,
            time_offset_s,
            step_s,
            mix_freq_hz,
        )
    };
    y
}
