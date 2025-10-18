# Viral Mixed Assembly tool

This repository provides tools to:

1. **Run a mixed assembly pipeline (`run_mixed_assembly.py`)** that merges **mapping** and **ABACAS** consensus sequences, applies quality control at the sliding-window level, and restores **mapping consensus**-specific insertions relative to the reference.  
2. **Build empirical priors (`build_priors.py`)** from large multiple-sequence alignments, used later to evaluate windows during mixed assembly.  
3. **Remove frameshifts from an alignment with the reference (`remove_frameshifts.py`)**
4. **Provide supporting functions** via **utils** scripts.

---
### Installation

```bash
pip install mixedassembly
```
---

### CLI usage 
```bash
# Create priors
mixedassembly build-priors --input sequences.fasta --ref REF_ID --output priors.parquet

# Run mixed assembly
mixedassembly run-mixed-assembly --input alignment.aln --ref REF_ID --prior priors.parquet --output_dir results

# Correct frameshifts
mixedassembly remove-frameshifts --aln consensus.aln --out corrected.fasta

```

---

## 🚀 Main Script: run_mixed_assembly.py

This is the entrypoint of the tool. It creates a *mixed consensus sequence* by combining mapping consensus and ABACAS output, both aligned to a reference sequence, but only after performing quality control (QC) at the window level.  

### 🔑 Inputs

- `--input` → path to an alignment file (`.aln`) containing at least:  
  - the **reference sequence**  
  - the **mapping consensus sequence**  
  - the **ABACAS consensus sequence**  

- `--ref` → ID of the reference sequence in the alignment.  

- `--prior` → path to a priors table (`.parquet`) generated with `build_priors.py`.  

- `--output_dir` → directory to save the results.  

---

### 🧪 Workflow

1. **Filter alignment by reference coordinates** → all sequences are trimmed to the reference coordinate system.  
2. **Create overlapping windows** → sliding windows across the genome (size and overlap defined in the priors file).  
3. **Window QC** →  
   - Check if ABACAS window is more informative than mapping consensus, and if it passes some basic qc assumptions (<50 Ns,only 1 or 2 "fragments")
   - For each valid window,[compute the normalized negative log-likelihood (nLL)](readme_2.md#-methodology-build_priorspy) of the ABACAS sequence against the prior distribution. Thus, evaluating how rare is the substitution pattern in the window compared to the prior information.  
   - Compare to the `nLL_p95` threshold in the priors table.  
   - If ABACAS passes QC → keep ABACAS bases for that window.  
   - Otherwise → keep mapping consensus bases.  
4. **Consensus construction** → merge windows into a full consensus sequence.  
5. **Insertion restoration** → insertions that MAPPING had relative to the reference (lost when filtering by reference coordinates) are reinserted into the final consensus.  
6. **QC reporting** → compute coverage, substitutions, and insertion metrics comparing the final mixed consensus to MAPPING.  

---

### 📦 Outputs

The script produces **three files** inside `--output_dir`:

1. **Mixed consensus FASTA**  
   - File: `<basename>-MIX_ASSEMBLY.fasta`  
   - Contains the final consensus sequence after merging and reinserting insertions.  

2. **Window QC trace (CSV)**  
   - File: `windows_trace.csv`  
   - One row per window, recording:  
     - `start`, `end` → genomic coordinates.  
     - `MISSING_MAPPING`, `MISSING_ABACAS` → counts of missing bases.  
     - `ABACAS_MORE_INFO` → whether ABACAS has fewer missing bases than MAPPING.  
     - `ABACAS_FRAGMENTS` → fragmentation level of ABACAS in this window (keep: 0 < n fragments < 3 ).  
     - `WINDOW_PRIOR_nLL_p95` → threshold from priors.  
     - `WINDOW_SCORE_nLL` → score of ABACAS in this window.  
     - `WINDOW_QC_PASSED` → True/False decision.  

3. **Consensus QC summary (JSON)**  
   - File: `qc.json`  
   - Provides overall metrics comparing the MAPPING consensus and the mixed consensus:  
     - `MAPPING_COVERAGE` → % of genome covered in MAPPING.  
     - `MIXED_COVERAGE` → % of genome covered in mixed consensus.  
     - `MAPPING_SUBSTITUTIONS` → substitutions vs. reference in MAPPING.  
     - `MIXED_SUBSTITUTIONS` → substitutions vs. reference in mixed consensus.  
     - `EXPECTED_SUBSTITUTIONS` → expected number of substitutions, extrapolated from mapping.  
     - `OBS-EXP_SUBSTITUTIONS` → difference between observed and expected substitutions.  
     - `N_INSERTIONS` → number of insertions added back.  
     - `TOTAL_INSERTIONS_LENGTH` → total inserted length.  
     - `INSERTIONS` → list of insertions with their coordinates.  

---

### ▶️ Example run

----
python run_mixed_assembly.py \
  --input /path/to/250694-RSVWGS.aln \
  --ref RSV_BD \
  --prior /path/to/RSVBD_win100_ovlp50_priors.parquet \
  --output_dir results
----

This will generate:  

- `results/250694-RSVWGS-MIX_ASSEMBLY.fasta`  
- `results/windows_trace.csv`  
- `results/qc.json`  

---

## 🛠 Script: build_priors.py

This script creates **empirical priors** (overlapped windows) from a large multiple sequence alignment.  
These priors are later used by `run_mixed_assembly.py` to evaluate windows.

### 🔑 Inputs

- `-i / --input` → aligned FASTA file with multiple sequences.  
- `-r / --ref` → ID of the reference sequence.  
- `-o / --output` → output file (`.parquet`).  
- `--win` → window size (default: 100).  
- `--overlap` → overlap size (default: 10).  

### ▶️ Example run

----
python build_priors.py \
  -i alignment.fasta \
  -r ReferenceID \
  -o priors.parquet \
  --win 100 \
  --overlap 10
----

### 📦 Output

A `.parquet` file with one row per window, containing:  

- `start`, `end` → window coordinates.  
- `nLL_p95`, `nLL_p99` → empirical thresholds.  
- `profile` → base probability distributions for each position in the window.  

## 🧮 Methodology (build_priors.py)

### 1. Probability distributions per position

For each window of size `W` bases (e.g., `W = 100`), and for each position `j` within that window, we compute the probability of observing each nucleotide:

![P_j(b)](https://latex.codecogs.com/png.latex?P_j(b)=\frac{c_j(b)+\alpha}{\sum_{x\in\{A,C,G,T\}}(c_j(x)+\alpha)})

Where:  
- ![c_j(b)](https://latex.codecogs.com/png.latex?c_j(b)) = number of sequences with base ![b](https://latex.codecogs.com/png.latex?b) at position ![j](https://latex.codecogs.com/png.latex?j).  
- ![\alpha](https://latex.codecogs.com/png.latex?\alpha) = pseudocount (Laplace smoothing, default ![\alpha=1](https://latex.codecogs.com/png.latex?\alpha=1)) to avoid zero probabilities.  
- Bases `N` are ignored in the counts.  

This gives a **per-position categorical distribution**.

---

### 2. Log-likelihood of a sequence in a window

Given a query sequence ![Q](https://latex.codecogs.com/png.latex?Q), we compute its probability under the window profile.  
For each valid (non-`N`) position ![j](https://latex.codecogs.com/png.latex?j) with observed base ![q_j](https://latex.codecogs.com/png.latex?q_j):

![logL](https://latex.codecogs.com/png.latex?\log%20L(Q\mid%20\text{window})=\sum_{j=1}^{W}\log%20P_j(q_j))

The **normalized negative log-likelihood (nLL)** is:

![nLL](https://latex.codecogs.com/png.latex?\text{nLL}(Q)=-\frac{1}{N_{\text{valid}}}\sum_{j=1}^{W}\log%20P_j(q_j))

Where:  
- ![N_valid](https://latex.codecogs.com/png.latex?N_{\text{valid}}) = number of positions in the window where ![Q](https://latex.codecogs.com/png.latex?Q) has a non-`N` base.  

Smaller nLL values indicate sequences more likely under the empirical profile.


### 3. Empirical priors

To characterize "normal variation" for each window:

1. Score **all sequences** from the alignment against the window profile.  
2. Collect the distribution of nLL values.  
3. Extract percentiles (e.g., 95th and 99th) to serve as thresholds.  

Thus, for each window we store:  
- The **distribution (profile)**.  
- Empirical thresholds: `nLL_p95` and `nLL_p99`.  

A new sequence can later be compared:  
- If `nLL < nLL_p95` → typical.  
- If `nLL > nLL_p99` → unusually variable, possibly unreliable region.

---

---

## � Supporting utils

Several utility scripts provide reusable functions for both processes:  

- **utils.py** → basic alignment and scoring functions:  
  - `load_alignment`, `extract_ref_positions`, `sliding_windows`, `score_window`.  

- **utils_mixed_assembly.py** → additional helpers for mixed assembly:  
  - missingness and fragmentation counts,  
  - insertion handling,  
  - QC calculations,  
  - consensus merging,  
  - window evaluation wrapper.  

These modular functions keep the pipeline clean and reusable.

---

## 🧹 Script: remove_frameshifts.py

This script is used to **detect and mask problematic gaps** in a consensus sequence aligned against a reference.  
*Frameshifts* appear when deletions are not multiples of 3 or when gaps are too long, which can shift the reading frame.  

The algorithm replaces those regions with **Ns** (and optionally adds padding on the sides), preventing errors in downstream analyses.

### 🔑 Inputs
- `--aln` → MSA FASTA file (must include reference and consensus).  
- `--ref-index` → index of the reference in the alignment (default: `0`).  
- `--cons-index` → index of the consensus in the alignment (default: `1`).  
- `--min-gap` → minimum gap length (multiple of 3) that triggers aggressive masking (default: `15`).  
- `--pad` → number of additional bases to mask around the gap (default: `0`).  
- `--out` → output FASTA file with the corrected consensus.  

### 📦 Output
- FASTA file with the **masked consensus** → long gaps or gaps not multiple of 3 are replaced by Ns.  

---

### ▶️ Example run

Assume we have an alignment `example.aln.fasta` with two sequences:  
- index `0`: reference  
- index `1`: preliminary consensus  

```bash
python remove_frameshifts.py \
  --aln example.aln.fasta \
  --ref-index 0 \
  --cons-index 1 \
  --min-gap 12 \
  --pad 0 \
  --out consensus_fixed.fasta
  ```

#### 🔍 Example input (simplified):

**Reference**  
ATGGCTTACG CTGGA   CTG

**Preliminary consensus**  
ATGGCTTACG-TGGA------G

Here we see:  
- A deletion of **1 bases** → not a multiple of 3 → potential frameshift.  
- A deletion of **6 bases** → a multiple of 3 and < min gap → leave gap.  

#### 📤 Output (`consensus_fixed.fasta`):

>consensus_masked
ATGGCTTACGNTGGA---G

Thus, frameshifts are corrected by masking with Ns, preserving the reading frame validity.

