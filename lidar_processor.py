# =============================================================================
# LIDAR Data Processor
# Description : Reads, processes, and plots Na/K LIDAR density data.
# Author     : Frank Chingarandi
# Python      : >= 3.8
# =============================================================================

# ── Standard Library ─────────────────────────────────────────────────────────
import os
import re
import glob
import sys
import warnings
from pathlib import Path

# ── Third-Party ──────────────────────────────────────────────────────────────
import numpy  as np
import pandas as pd
import matplotlib
import matplotlib.pyplot            as plt
import matplotlib.tri               as tri
from   matplotlib.ticker            import MultipleLocator

# ── GUI ───────────────────────────────────────────────────────────────────────
import tkinter as tk
from tkinter import filedialog, messagebox

# ── Local ─────────────────────────────────────────────────────────────────────
import config

# =============================================================================
# Suppress Deprecation Warnings
# =============================================================================
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# =============================================================================
# Matplotlib Global Settings
# =============================================================================
def configure_matplotlib() -> None:
    """Apply global matplotlib style and rcParams."""

    matplotlib.rc("font", **{"family": "DejaVu Sans", "weight": "bold", "size": 10})
    matplotlib.rc("text", usetex=True)

    rcparams = {
        "savefig.bbox"            : "tight",
        "figure.figsize"          : (8, 6),
        "figure.titleweight"      : "bold",
        "axes.linewidth"          : 3,
        "axes.titlesize"          : 12,
        "axes.titlepad"           : -15,
        "lines.linewidth"         : 1,
        "contour.negative_linestyle": "solid",
        "xtick.direction"         : "in",
        "ytick.direction"         : "in",
        "xtick.major.width"       : 4,
        "ytick.major.width"       : 2,
        "xtick.minor.width"       : 1,
        "ytick.minor.width"       : 1,
        "ytick.right"             : True,
        "ytick.major.size"        : 9,
        "ytick.minor.size"        : 5,
        "xtick.major.size"        : 9,
        "xtick.minor.size"        : 2,
        "legend.fontsize"         : 14,
        "legend.handlelength"     : 0.4,
        "legend.facecolor"        : "w",
        "legend.framealpha"       : 0,
        "legend.borderpad"        : 0,
        "legend.columnspacing"    : 0.1,
        "legend.title_fontsize"   : 12,
    }
    matplotlib.rcParams.update(rcparams)


# =============================================================================
# GUI Helpers
# =============================================================================
def _build_root() -> tk.Tk:
    """Create a hidden Tkinter root window that stays on top."""
    root = tk.Tk()
    root.withdraw()
    root.call("wm", "attributes", ".", "-topmost", True)
    return root


def select_excel_file() -> str:
    """
    Prompt the user to select an Excel dates file.

    Returns
    -------
    str
        Absolute path to the selected file, or '' if cancelled.
    """
    root = _build_root()
    messagebox.showinfo("LIDAR Processor", "Select the dates Excel file.")
    path = filedialog.askopenfilename(
        title="Select Dates Excel File",
        filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")],
    )
    root.destroy()
    return path


def select_directories() -> list[str]:
    """
    Prompt the user to select Na and K data directories.

    Returns
    -------
    list[str]
        List of two selected directory paths [Na_dir, K_dir].
    """
    dirs: list[str] = []
    labels = ["Na (Sodium)", "K (Potassium)"]

    root = _build_root()
    messagebox.showinfo(
        "LIDAR Processor",
        "You will now select TWO directories:\n  1) Na (Sodium)\n  2) K (Potassium)",
    )
    root.destroy()

    for label in labels:
        root = _build_root()
        path = filedialog.askdirectory(title=f"Select {label} Data Folder")
        root.destroy()
        if not path:
            raise FileNotFoundError(f"No directory selected for {label}. Aborting.")
        dirs.append(path)

    return dirs


def select_output_directory() -> str:
    """
    Prompt the user to select an output directory for saving files.

    Returns
    -------
    str
        Absolute path of the chosen output directory.
    """
    root = _build_root()
    messagebox.showinfo("LIDAR Processor", "Select the OUTPUT directory.")
    path = filedialog.askdirectory(title="Select Output Directory")
    root.destroy()
    if not path:
        raise FileNotFoundError("No output directory selected. Aborting.")
    return path


# =============================================================================
# Date Utilities
# =============================================================================
def generate_months(year: str | int) -> list[str]:
    """
    Generate a list of month strings in *yyyymm* format for a given year.

    Parameters
    ----------
    year : str or int
        Four-digit year, e.g. ``2023``.

    Returns
    -------
    list[str]
        12 strings: ``['202301', '202302', ..., '202312']``.
    """
    return [f"{year}{month:02d}" for month in range(1, 13)]


def build_dates_list(dates: pd.DataFrame) -> list[list[str]]:
    """
    Convert the raw Excel day-number columns into full *yyyymmdd* date strings.

    Parameters
    ----------
    dates : pd.DataFrame
        DataFrame loaded from the Excel file. Column 8 is expected to hold
        comma-separated day numbers for each month.

    Returns
    -------
    list[list[str]]
        Outer list = months; inner list = date strings for that month.
    """
    year   = dates.iloc[:, 8].name          # column header  = year
    months = generate_months(year)

    # Parse comma-separated day numbers from each cell
    lists_of_numbers = [
        [int(x) for x in str(dates.iloc[i, 8]).split(",")]
        for i in range(len(dates))
    ]

    dates_list: list[list[str]] = []
    for sublist, month in zip(lists_of_numbers, months):
        modified = [f"{month}{day:02d}" for day in sublist]
        dates_list.append(modified)

    return dates_list


# =============================================================================
# File Selection
# =============================================================================
def select_and_sort_files(
    directories: list[str],
    string_list: list[str],
) -> list[str]:
    """
    Collect files from *directories* whose names contain any string in
    *string_list*, then sort them by the 8-digit date embedded in the filename.

    Parameters
    ----------
    directories : list[str]
        Paths to search (e.g. [Na_dir, K_dir]).
    string_list : list[str]
        Date strings that must appear in the filename.

    Returns
    -------
    list[str]
        Sorted list of matching absolute file paths.
    """
    selected: list[str] = []

    for directory in directories:
        if not os.path.isdir(directory):
            print(f"[WARNING] Directory not found, skipping: {directory}")
            continue

        for filename in os.listdir(directory):
            if any(s in filename for s in string_list):
                selected.append(os.path.join(directory, filename))

    # Sort by the 8-digit date token in the file path
    selected.sort(
        key=lambda f: match[0]
        if (match := re.findall(r"\D(\d{8})\D", f))
        else f
    )
    return selected


# =============================================================================
# Data Reading & Processing
# =============================================================================
def read_data(file: str, output_folder: str) -> pd.DataFrame:
    """
    Read raw LIDAR data, apply quality-control thresholds, and save a CSV.

    Parameters
    ----------
    file : str
        Path to the whitespace-delimited raw data file.
    output_folder : str
        Directory where the processed CSV will be saved.

    Returns
    -------
    pd.DataFrame
        Cleaned DataFrame with columns ``['UT', 'Density', 'H', 'LT']``.
    """
    date_match = re.findall(r"\D(\d{8})\D", file)
    dye_match  = re.search(r"[NaK]", file)

    if not date_match:
        raise ValueError(f"Cannot extract date from filename: {file}")
    if not dye_match:
        raise ValueError(f"Cannot determine dye (Na/K) from filename: {file}")

    date = date_match[0]
    dye  = dye_match.group(0)

    # ── Load raw columns ──────────────────────────────────────────────────────
    df = pd.read_csv(
        file,
        sep=r"\s+",                          # replaces deprecated delim_whitespace
        usecols=list(range(config.START_COL, config.END_COL)),
        engine="python",
    )

    # Global upper-bound mask
    df[df > config.DENSITY_GLOBAL_MAX] = -100
    df[df.isna()]                       = -100

    # ── Stack columns into long format ────────────────────────────────────────
    frames: list[pd.DataFrame] = []

    for col in df.columns:
        chunk = df[[col]].copy()
        chunk["H"] = float(col)
        chunk      = chunk.reset_index()
        chunk.columns = ["UT", "Density", "H"]

        # Altitude filter
        chunk = chunk[(chunk["H"] > config.ALT_MIN) & (chunk["H"] < config.ALT_MAX)]
        chunk = chunk.drop_duplicates(subset=["H", "Density"])

        # Local time
        chunk["LT"] = chunk["UT"] - config.UT_OFFSET
        frames.append(chunk)

    DF = pd.concat(frames, ignore_index=True)

    # ── Instrument-specific thresholds ───────────────────────────────────────
    if "K" in file:
        DF.loc[DF["Density"] > config.DENSITY_MAX_K, "Density"] = -100

    # General density range
    DF.loc[
        (DF["Density"] < config.DENSITY_MIN) | (DF["Density"] > config.DENSITY_MAX_NA),
        "Density",
    ] = -100

    # Final altitude crop & round
    DF = DF[(DF["H"] > config.ALT_MIN) & (DF["H"] < config.ALT_MAX)].round(2)

    # ── Report ────────────────────────────────────────────────────────────────
    print(f"[INFO] {date} | {dye} | Max Density = {DF['Density'].max():.1f}")

    # ── Save CSV ──────────────────────────────────────────────────────────────
    out_path = os.path.join(output_folder, f"{date}{dye}.csv")
    DF.to_csv(out_path, sep=",", index=False)

    return DF


# =============================================================================
# Plotting
# =============================================================================

# Tick positions and labels for the LT axis
_TICKS       = np.arange(19, 31, 1)
_TICK_LABELS = ["19","20","21","22","23","24","1","2","3","4","5","6"]


def _setup_axes(ax: plt.Axes) -> None:
    """Apply common axis settings (limits, ticks, labels)."""
    ax.set_ylim(config.ALT_MIN + 5, config.ALT_MAX)
    ax.set_xlim(19, 30)
    ax.set_xticks(_TICKS)
    ax.set_xticklabels(_TICK_LABELS)
    ax.xaxis.set_minor_locator(MultipleLocator(0.5))
    ax.set_ylabel("Altitude (km)")


def plot_from_file(
    file_na: str,
    file_k : str,
    output_folder: str,
    vmx  : float = 10_000,
    vmx2 : float = 300,
    vmn  : float = 20,
) -> tuple[float, float]:
    """
    Plot Na and K density profiles side-by-side from a matched file pair.

    Parameters
    ----------
    file_na : str
        Path to the Sodium data file.
    file_k : str
        Path to the Potassium data file.
    output_folder : str
        Directory for saving the output PNG.
    vmx, vmx2, vmn : float
        Colour-scale limits for Na, K, and the shared minimum.

    Returns
    -------
    tuple[float, float]
        (Na_max_density, K_max_density) for the processed day.
    """
    date = re.findall(r"\D(\d{8})\D", file_na)
    date = date[0] if date else "UNKNOWN"

    df_na = read_data(file_na, output_folder)
    df_k  = read_data(file_k,  output_folder)

    fig, axs = plt.subplots(2, figsize=config.FIGURE_SIZE)
    fig.subplots_adjust(hspace=config.HSPACE)

    for ax in axs:
        _setup_axes(ax)

    # ── Na panel ─────────────────────────────────────────────────────────────
    axs[0].set_title(f" (a) Sodium  SJC {date}", weight="bold")
    sc_na = axs[0].scatter(
        df_na["LT"], df_na["H"],
        c    = 1.1 * df_na["Density"],
        cmap = config.CMAP,
        s    = 5,
        vmin = vmn,
        vmax = vmx,
    )
    na_ticks = (
        np.arange(0, vmx + 1_000, 1_000)
        if vmx < 10_000
        else np.arange(0, vmx + 2_000, 2_000)
    )
    clb_na = plt.colorbar(sc_na, ax=axs[0], shrink=1.0, extend="both", ticks=na_ticks)
    clb_na.set_label(
        r"Na (cm$^{-3}$)", rotation=0, y=1.25, labelpad=-20, fontsize=14
    )

    # ── K panel ───────────────────────────────────────────────────────────────
    axs[1].set_title(f" (b) Potassium SJC {date}", weight="bold")
    sc_k = axs[1].scatter(
        df_k["LT"], df_k["H"],
        c    = 1.1 * df_k["Density"],
        cmap = config.CMAP,
        s    = 5,
        vmin = vmn,
        vmax = vmx2,
    )
    clb_k = plt.colorbar(
        sc_k, ax=axs[1], shrink=1.0, extend="both",
        ticks=np.arange(0, vmx2 + 50, 100),
    )
    clb_k.set_label(
        r"K (cm$^{-3}$)", rotation=0, y=1.2, labelpad=-25, fontsize=14
    )

    axs[1].set_xlabel("Local Time (LT)")

    # ── Save ──────────────────────────────────────────────────────────────────
    out_file = os.path.join(output_folder, f"{date}_cont_ldr.png")
    plt.savefig(out_file, dpi=config.FIGURE_DPI)
    plt.show()
    plt.close(fig)

    na_max = df_na["Density"].max()
    k_max  = df_k["Density"].max()
    print(f"[INFO] {date} | Na max = {na_max:.0f} | K max = {k_max:.0f}")

    return na_max, k_max


def plot_from_directory(
    sorted_files: list[str],
    output_folder: str,
    vmx  : float = 10_000,
    vmx2 : float = 300,
    vmn  : float = 20,
) -> list[list[float]]:
    """
    Iterate over sorted file pairs (Na, K) and call :func:`plot_from_file`.

    Parameters
    ----------
    sorted_files : list[str]
        Flat list of files ordered so even indices = Na, odd indices = K.
    output_folder : str
        Output directory for PNGs.
    vmx, vmx2, vmn : float
        Colour-scale limits forwarded to :func:`plot_from_file`.

    Returns
    -------
    list[list[float]]
        [[Na_max, K_max], ...] for every processed pair.
    """
    all_maxs: list[list[float]] = []

    if len(sorted_files) % 2 != 0:
        print("[WARNING] Odd number of files – the last file will be skipped.")

    for i in range(0, len(sorted_files) - 1, 2):
        na_max, k_max = plot_from_file(
            sorted_files[i], sorted_files[i + 1],
            output_folder, vmx, vmx2, vmn,
        )
        all_maxs.append([na_max, k_max])

    return all_maxs


# =============================================================================
# Main Entry Point
# =============================================================================
def main() -> None:
    """
    Main workflow:

    1. User selects the Excel dates file via GUI.
    2. User selects Na and K data directories via GUI.
    3. User selects an output directory via GUI.
    4. Months/dates are generated from the Excel file.
    5. Files are matched, sorted, and plotted in pairs.
    """
    configure_matplotlib()
    plt.close("all")

    # ── 1. Select dates Excel file ────────────────────────────────────────────
    # NOTE: Hard-coded fallback path for development — comment out for release.
    # dates_file = r"C:\Users\simba\My Drive\Papers\Pimenta et al\lidar\Project\dados_para_analise.xlsx"

    dates_file = select_excel_file()
    if not dates_file:
        print("[ERROR] No Excel file selected. Exiting.")
        sys.exit(1)

    dates      = pd.read_excel(dates_file, engine="openpyxl")
    dates_list = build_dates_list(dates)

    # ── 2. Select data directories ────────────────────────────────────────────
    # NOTE: Hard-coded fallback for development — comment out for release.
    # directory_paths = [
    #     r"E:\LIDAR\Density\2020\Na",
    #     r"E:\LIDAR\Density\2020\K",
    # ]

    directory_paths = select_directories()

    # ── 3. Select output directory ────────────────────────────────────────────
    # NOTE: Hard-coded fallback for development — comment out for release.
    # output_folder = r"C:\Users\simba\My Drive\Papers\Pimenta et al\lidar\Project\Data"

    output_folder = select_output_directory()
    os.makedirs(output_folder, exist_ok=True)

    # ── 4. Choose month index and density scale limits ────────────────────────
    # Adjust month_index (0 = Jan … 11 = Dec) and vmax values as needed.
    MONTH_SETTINGS: dict[int, dict] = {
        0 : {"vmx": 10_000, "vmx2": 250},   # January
        1 : {"vmx": 4_000,  "vmx2": 150},   # February
        8 : {"vmx": 5_000,  "vmx2": 300},   # September
        # Add other months with data here
    }

    month_index = 0                          # ← Change as needed (0–11)

    settings    = MONTH_SETTINGS.get(month_index, {"vmx": 5_000, "vmx2": 200})
    string_list = dates_list[month_index]

    print(f"\n[INFO] Processing month index {month_index} | Dates: {string_list}")

    # ── 5. Collect and sort files ─────────────────────────────────────────────
    sorted_files = select_and_sort_files(directory_paths, string_list)

    if not sorted_files:
        print("[WARNING] No matching files found for the selected month.")
        sys.exit(0)

    print(f"[INFO] Found {len(sorted_files)} file(s):")
    for f in sorted_files:
        print(f"       {f}")

    # ── 6. Plot ───────────────────────────────────────────────────────────────
    all_maxs = plot_from_directory(
        sorted_files,
        output_folder,
        vmx  = settings["vmx"],
        vmx2 = settings["vmx2"],
    )

    print("\n[INFO] Daily maxima (Na, K):")
    for pair in all_maxs:
        print(f"       Na = {pair[0]:.0f}  |  K = {pair[1]:.0f}")


# =============================================================================
if __name__ == "__main__":
    main()
