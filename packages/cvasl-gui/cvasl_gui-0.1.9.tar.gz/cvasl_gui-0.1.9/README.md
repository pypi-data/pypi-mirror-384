# CVASL-GUI

Cvasl-gui is an open source collaborative Python GUI, built around the CVASL package, for statistical harmonisation of (arterial spin labelling) MRI-derived data and prediction of brain age using shallow machine learning, utilised in 'Multi-cohort, multi-sequence harmonisation for cerebrovascular brain age', https://doi.org/10.1162/IMAG.a.964.

Statistical harmonisation methods include NeuroComBat, CovBat, NeuroHarmonize, OPNested ComBat, AutoComBat, and RELIEF.
Shallow machine learning methods include: ...TODO

Brain age machine learning methods, and the difference between the predicted and the chronological age—the brain age gap (BAG)—can be used to assess deviation from normative ageing trajectories. A larger BAG, therefore, represents a proxy parameter of poorer brain ageing, which is associated with cognitive decline (Biondo et al., 2021; Franke & Gaser, 2019).

This GUI supports the ongoing research at University of Amsterdam Medical Center on brain ageing, but is being built for the entire community of radiology researchers across all university and academic medical centers and beyond.

## References

**NeuroComBat:** Fortin, J.-P. et al. Harmonization of multi-site diffusion tensor imaging data. *Neuroimage* 161, 149–170 (2017).

**CovBat:** Chen, A. A. et al. Mitigating site effects in covariance for machine learning in neuroimaging data. *Hum. Brain Mapp.* 43, 1179–1195 (2022).

**NeuroHarmonize:** Pomponio, R. et al. Harmonization of large MRI datasets for the analysis of brain imaging patterns throughout the lifespan. *Neuroimage* 208, 116450 (2020).

**OPNested ComBat:** Horng, H. et al. Generalized ComBat harmonization methods for radiomic features with multi-modal distributions and multiple batch effects. *Sci. Rep.* 12, 4493 (2022).

**AutoComBat:** Carré, A. et al. AutoComBat: a generic method for harmonizing MRI-based radiomic features. *Sci. Rep.* 12, 12762 (2022).

**RELIEF:** Zhang, R., Oliver, L. D., Voineskos, A. N. & Park, J. Y. RELIEF: A structured multivariate approach for removal of latent inter-scanner effects. *Imaging Neurosci (Camb)* 1, 1–16 (2023).

## Install and run

```bash
pip install cvasl-gui
cvasl-gui
```

## Configuration

The application will look for the following environment variables:

```bash
CVASL_DEBUG_MODE  # True for development, False for production. Debug mode will show the Dash debug console on the page. In production mode, the browser will be automatically opened.
CVASL_PORT        # The port the server runs on, default is 8767
```

## Development

```bash
poetry install
poetry run cvasl-gui
```

### Tests

#TODO

### Building Executable with PyInstaller

To create a standalone executable of the application:

1. Install PyInstaller (already included in dev dependencies):
```bash
poetry install
```

2. Build the executable using the provided script:
```bash
./build.sh
```

Or manually:
```bash
poetry run pyinstaller cvasl-gui.spec
```

3. The executable will be created in `dist/cvasl-gui/`. Run it with:
```bash
cd dist/cvasl-gui
./cvasl-gui
```

**Note:** The build process will:
- Include all necessary assets (CSS files, etc.)
- Bundle Python dependencies
- Create a self-contained application directory
- The executable can be distributed to users without requiring Python installation

**Environment Variables:** The executable supports some of the environment variables as the regular installation (`CVASL_DEBUG_MODE` is forced to False).
