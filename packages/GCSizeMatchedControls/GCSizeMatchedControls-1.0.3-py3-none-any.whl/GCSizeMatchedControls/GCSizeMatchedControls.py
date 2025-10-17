#!/usr/bin/env python3
import os
import sys
import argparse
import pandas as pd
import numpy as np
import pysam
from pybedtools import BedTool

# ---- version ----
dir = os.path.dirname(os.path.abspath(__file__))
version_py = os.path.join(dir, "_version.py")
if os.path.exists(version_py):
    exec(open(version_py).read())   # defines __version__
else:
    __version__ = "1.0.0"

# ----------------- Utilities -----------------

def read_bed_into_df(bed_file):
    """
    Read BED (at least 3 cols) into a DataFrame with columns: chrom, start, end.
    Keeps order. Filters malformed rows.
    """
    bt = BedTool(bed_file)
    df = bt.to_dataframe(names=["chrom", "start", "end"], usecols=[0,1,2])
    # ensure integers and valid intervals
    df = df[(df["end"] > df["start"])].copy()
    df["start"] = df["start"].astype(int)
    df["end"] = df["end"].astype(int)
    return df

def fasta_chrom_sizes(fasta_path):
    """
    Get chromosome sizes from FASTA index via pysam.
    """
    fa = pysam.FastaFile(fasta_path)
    chroms = fa.references
    sizes = fa.lengths
    return fa, dict(zip(chroms, sizes))

def seq_gc_fraction(seq):
    """
    GC fraction computed over A/C/G/T only (Ns ignored).
    Returns 0.0 if no A/C/G/T present.
    """
    s = seq.upper()
    atgc = sum(s.count(x) for x in ("A", "C", "G", "T"))
    if atgc == 0:
        return 0.0
    gc = s.count("G") + s.count("C")
    return gc / atgc

def compute_gc_for_df(df, fa):
    """
    Compute GC fractions for each interval in df using pysam FastaFile.
    Returns a numpy array of GC values.
    """
    gcs = np.empty(len(df), dtype=float)
    for i, row in df.iterrows():
        seq = fa.fetch(row["chrom"], int(row["start"]), int(row["end"]))
        gcs[i] = seq_gc_fraction(seq)
    return gcs

def freedman_diaconis_edges(values, max_bins=60):
    """
    Compute GC bin edges via Freedman–Diaconis rule (data-driven).
    If IQR=0, fall back to unique values (capped by max_bins).
    """
    x = np.asarray(values, dtype=float)
    if x.size == 0:
        return np.array([0.0, 1.0])
    q1, q3 = np.percentile(x, [25, 75])
    iqr = q3 - q1
    if iqr <= 0:
        uniq = np.unique(np.round(x, 6))
        k = min(len(uniq), max_bins)
        eps = 1e-9
        return np.linspace(x.min() - eps, x.max() + eps, max(k,1) + 1)
    h = 2 * iqr * (x.size ** (-1/3))
    if h <= 0:
        h = (x.max() - x.min()) / max(1, min(max_bins, int(round(np.sqrt(x.size)))))
    k = int(np.ceil((x.max() - x.min()) / h)) if h > 0 else 1
    k = max(1, min(k, max_bins))
    lo = min(0.0, x.min())
    hi = max(1.0, x.max())
    return np.linspace(lo, hi, k + 1)

def assign_bin(val, edges):
    """
    Return bin index i such that edges[i] <= val < edges[i+1],
    using right-inclusive last bin.
    """
    i = np.searchsorted(edges, val, side="right") - 1
    if i < 0:
        i = 0
    if i >= len(edges) - 1:
        i = len(edges) - 2
    return int(i)

# ---- Overlap index (targets & optional blacklist) ----

def build_interval_index(df):
    """
    Per-chrom sorted starts/ends for quick overlap checks.
    Returns dict chrom -> (starts[], ends[])
    """
    idx = {}
    for chrom, sub in df.groupby("chrom"):
        s = np.asarray(sub["start"].values, dtype=np.int64)
        e = np.asarray(sub["end"].values, dtype=np.int64)
        order = np.argsort(s, kind="mergesort")
        idx[chrom] = (s[order], e[order])
    return idx

def overlaps_any(chrom, start, end, index):
    """
    Return True if [start,end) overlaps any interval in index for chrom.
    """
    if chrom not in index:
        return False
    starts, ends = index[chrom]
    # binary search to neighborhood
    i = np.searchsorted(starts, start, side="left")
    for j in (i-1, i, i+1):
        if 0 <= j < len(starts):
            if not (end <= starts[j] or start >= ends[j]):
                return True
    return False

# ---- Sampling helpers ----

def prepare_chrom_sampler(chrom_sizes, L):
    """
    Prepare cumulative weights proportional to (size - L) for each chrom.
    """
    chroms, weights = [], []
    for c, sz in chrom_sizes.items():
        w = max(sz - L, 0)
        if w > 0:
            chroms.append(c)
            weights.append(w)
    if not weights:
        raise ValueError(f"No chromosome has space for length {L}.")
    cum = np.cumsum(weights, dtype=np.int64)
    return chroms, cum, int(cum[-1])

def sample_chrom_and_start(rng, chroms, cum, total, chrom_sizes, L):
    """
    Weighted by chrom length, then uniform start in [0, size-L].
    """
    r = rng.integers(0, total)
    i = int(np.searchsorted(cum, r, side="right"))
    chrom = chroms[i]
    limit = chrom_sizes[chrom] - L
    start = int(rng.integers(0, max(1, limit + 1)))
    return chrom, start

# ----------------- Core Logic -----------------

def GCSizeMatchedControls(bed_path, fasta_path, output_path,
                          blacklist_path=None, seed=1, max_tries=20000,
                          same_chrom=False):
    """
    Generate 1:1 size- and GC-bin–matched controls for every target in BED.
    - Size bin = exact target length
    - GC bin = data-driven from target GC (Freedman–Diaconis)
    - Each control used only once
    - Controls do NOT overlap targets (and optional blacklist if provided)
    - If same_chrom=True, controls are drawn from the same chromosome as targets.
    """
    # load inputs
    targets_df = read_bed_into_df(bed_path)
    fa, chrom_sizes = fasta_chrom_sizes(fasta_path)

    mask = targets_df["chrom"].isin(chrom_sizes.keys())
    targets_df = targets_df[mask].copy()
    if targets_df.empty:
        raise SystemExit("No targets remain after filtering by FASTA contigs.")

    targets_df["end"] = targets_df.apply(
        lambda r: min(int(r["end"]), int(chrom_sizes[r["chrom"]])), axis=1
    )
    targets_df = targets_df[targets_df["end"] > targets_df["start"]].copy()
    targets_df["length"] = targets_df["end"] - targets_df["start"]

    # compute target GC
    tgt_gc = compute_gc_for_df(targets_df, fa)

    # GC bins
    gc_edges = freedman_diaconis_edges(tgt_gc, max_bins=60)
    tgt_bins = np.array([assign_bin(g, gc_edges) for g in tgt_gc], dtype=int)

    # build overlap indices
    target_index = build_interval_index(targets_df[["chrom","start","end"]])
    blacklist_index = {}
    if blacklist_path:
        bl_df = read_bed_into_df(blacklist_path)
        blacklist_index = build_interval_index(bl_df)

    # samplers
    unique_lengths = sorted(targets_df["length"].unique().tolist())
    samplers = {}
    for L in unique_lengths:
        samplers[L] = prepare_chrom_sampler(chrom_sizes, int(L))

    # RNG
    rng = np.random.default_rng(seed)
    order = np.arange(len(targets_df))
    rng.shuffle(order)

    controls = [None] * len(targets_df)
    used = set()

    for k, i in enumerate(order):
        row = targets_df.iloc[i]
        L = int(row["length"])
        bin_i = int(tgt_bins[i])

        # Same chromosome sampling if requested
        if same_chrom:
            chroms = [row["chrom"]]
            cum = np.array([chrom_sizes[row["chrom"]] - L], dtype=np.int64)
            total = int(cum[-1])
        else:
            chroms, cum, total = samplers[L]

        found = None
        for _ in range(max_tries):
            chrom, start = sample_chrom_and_start(rng, chroms, cum, total, chrom_sizes, L)
            end = start + L
            key = (chrom, start, end)
            if key in used:
                continue
            if overlaps_any(chrom, start, end, target_index):
                continue
            if blacklist_index and overlaps_any(chrom, start, end, blacklist_index):
                continue
            seq = fa.fetch(chrom, start, end)
            gc = seq_gc_fraction(seq)
            if assign_bin(gc, gc_edges) != bin_i:
                continue
            found = key
            break

        if found is None:
            raise SystemExit(
                f"Failed to find control for target #{i} "
                f"(len={L}, gc_bin={bin_i}) after {max_tries} tries. "
                f"Consider relaxing constraints or removing --same-chrom."
            )
        controls[i] = found
        used.add(found)

    with open(output_path, "w") as out:
        for c in controls:
            out.write(f"{c[0]}\t{c[1]}\t{c[2]}\n")

# ----------------- CLI -----------------

def main():
    parser = argparse.ArgumentParser(
        description="Randomly select 1:1 size- and GC-bin–matched genomic control regions."
    )
    parser.add_argument('-i', '--bed', required=True, help='Input target BED.')
    parser.add_argument('-f', '--fasta', required=True, help='Genome FASTA (indexed).')
    parser.add_argument('-o', '--output', required=True, help='Output BED for controls.')
    parser.add_argument('-b', '--blacklist', default=None, help='Optional blacklist BED to avoid.')
    parser.add_argument('-s', '--seed', type=int, default=1, help='Random seed (default: 1).')
    parser.add_argument('-t', '--max-tries', type=int, default=20000, help='Max attempts per target (default: 20000).')
    parser.add_argument('--same-chrom', action='store_true',
                        help='If set, controls are selected from the same chromosome as each target.')
    parser.add_argument("-V", "--version", action="version",
                        version="GCSizeMatchedControls {}".format(__version__),
                        help="Print version and exit")
    args = parser.parse_args()

    print('###Parameters:')
    print(args)
    print('###Parameters')

    GCSizeMatchedControls(
        bed_path=args.bed,
        fasta_path=args.fasta,
        output_path=args.output,
        blacklist_path=args.blacklist,
        seed=args.seed,
        max_tries=args.max_tries,
        same_chrom=args.same_chrom
    )
