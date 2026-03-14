## Project Description

This repository contains a Python-based data processing and 
visualization pipeline for resonance-fluorescence LIDAR observations 
of mesospheric metallic layers — specifically Sodium (Na, 589 nm) and 
Potassium (K, 770 nm) — developed by Dr Frank Chingarandi at the LIDAR facility of the 
Instituto Nacional de Pesquisas Espaciais (INPE), São José dos 
Campos, SP, Brazil (23.2°S, 45.9°W).

### Scientific Context

The Mesosphere–Lower Thermosphere (MLT, ~75–110 km altitude) hosts 
thin layers of neutral metal atoms deposited by the continuous 
ablation of incoming meteoric material. These layers serve as natural 
tracers of atmospheric dynamics, tidal waves, gravity waves, and 
photochemical cycles. The INPE LIDAR facility has been observing 
these layers since the early 1990s, generating one of the longest 
continuous records of low-latitude mesospheric metal densities in 
the Southern Hemisphere (Clemesha et al., 1992; Batista et al., 2002).

### What This Code Does

Raw photon-count profiles are read from whitespace-delimited text 
files produced by the INPE LIDAR data-acquisition system. The 
pipeline applies:

  - Instrument-specific quality-control (separate thresholds for 
    Na and K channels)
  - Altitude filtering (75–110 km window)
  - Universal Time to Local Time conversion (UT − 3 h for SJC)
  - Density range masking (removal of noise and saturation artifacts)
  - Export of cleaned profiles to CSV for downstream analysis
  - Generation of side-by-side Na/K density scatter plots as 
    publication-ready PNG figures

### Key Capabilities

  - GUI-driven selection of input files, data directories, and 
    output folders — no hard-coded paths
  - Batch processing of multi-night observation campaigns 
    driven by an Excel schedule file
  - Per-month colour-scale configuration for optimal visualization 
    of seasonal density variations
  - Modular design with all physical and plotting parameters 
    centralised in a single configuration file (config.py)
  - Compatible with Python 3.8 through 3.12

### Instrument

The Na LIDAR transmits ~100–300 mJ pulses at 589.0 nm (Na D₂ line) 
at 10–50 Hz repetition rate and detects resonantly backscattered 
photons using a photomultiplier tube (PMT) behind a narrowband 
interference filter. The K LIDAR operates analogously at 769.9 nm 
(K D₁ line). Absolute number densities are retrieved by 
normalization to molecular Rayleigh backscatter at reference 
altitudes (30–60 km) using the NRLMSISE-00 atmospheric model 
(Picone et al., 2002).

### Typical Output

For each observation night the pipeline produces:
  - YYYYMMDD_cont_ldr.png  →  Two-panel Na/K density scatter plot
  - YYYYMMDDNa.csv         →  Cleaned Na density profile
  - YYYYMMDDК.csv          →  Cleaned K  density profile

### Affiliated Institution

  Instituto Nacional de Pesquisas Espaciais (INPE)
  Aeronomy Division (DAE)
  Av. dos Astronautas, 1758
  São José dos Campos, SP — Brazil
  www.inpe.br

### Primary References

  Clemesha et al. (1992), J. Geophys. Res., 97, 5719–5724.
    https://doi.org/10.1029/91JD03058

  Batista et al. (2002), J. Atmos. Sol.-Terr. Phys., 64, 1485–1493.
    https://doi.org/10.1016/S1364-6826(02)00088-7

  Plane, J. M. C. (2003), Chem. Rev., 103, 4963–4984.
    https://doi.org/10.1021/cr0205309

  Picone et al. (2002), J. Geophys. Res., 107, 1468.
    https://doi.org/10.1029/2002JA009430
