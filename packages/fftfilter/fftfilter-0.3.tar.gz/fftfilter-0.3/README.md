# FFT-Filter

This package provides an interactive GUI to remove periodic baselines from measurements.
The software can be started by running
```bash
fftfilter
```
in the terminal.

Files can be loaded via drag-and-drop or via the menu.

The data is Fourier tranformed and all Fourier coefficients below a user-selected cutoff are removed before the reverse Fourier transform is performed.

The files are expected to be tab-separated and the first two columns are expected to be the x- and y-data of the measurement.

This procedure is quite effective for removing standing waves (e.g., due to reflections, ...) from measurements.