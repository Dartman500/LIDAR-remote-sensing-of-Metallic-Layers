# =============================================================================
# LIDAR Data Processor - Configuration
# =============================================================================

# Column range for data reading
START_COL = 141
END_COL   = 540

# Altitude range (km)
ALT_MIN = 75
ALT_MAX = 110

# Density thresholds
DENSITY_MIN        = 20
DENSITY_MAX_NA     = 15000
DENSITY_MAX_K      = 1000
DENSITY_GLOBAL_MAX = 50000

# Timezone offset (LT = UT - offset)
UT_OFFSET = 3

# Plot settings
FIGURE_DPI    = 150
FIGURE_SIZE   = (6, 5)
HSPACE        = 0.3

# Default color map
CMAP = "jet"
