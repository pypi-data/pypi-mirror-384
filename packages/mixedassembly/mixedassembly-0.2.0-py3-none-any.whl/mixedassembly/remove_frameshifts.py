#!/usr/bin/env python3
"""
remove_frameshifts module
"""

from typing import List
import sys
import argparse
from Bio import AlignIO, SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

def run(aln_path, ref_idx, cons_idx, min_gap, pad, out_fa):
    aln = AlignIO.read(aln_path, "fasta")
    ref  = str(aln[ref_idx].seq).upper()
    cons = str(aln[cons_idx].seq).upper()

    out = []
    i = 0
    L = len(ref)

    while i < L:
        r, c = ref[i], cons[i]
        if r == '-':
            # insertion relative to ref -> skip
            i += 1
            continue

        if c != '-':
            # normal base
            out.append(c if c in "ACGTN" else 'N')
            i += 1
            continue

        # c == '-' -> deletion in consensus vs ref
        j = i
        while j < L and ref[j] != '-' and cons[j] == '-':
            j += 1
        gap_len = j - i

        if gap_len % 3 != 0:
            # priority: if NOT multiple of 3 -> always N
            left = max(0, len(out) - pad)
            out = out[:left] + ['N'] * (len(out) - left)
            out.extend(['N'] * (gap_len + pad))
        elif gap_len >= min_gap:
            # multiple of 3 but long -> N with pad
            left = max(0, len(out) - pad)
            out = out[:left] + ['N'] * (len(out) - left)
            out.extend(['N'] * (gap_len + pad))
        else:
            # multiple of 3 and short -> simple Ns
            out.extend(['N'] * gap_len)

        i = j

    seq = ''.join(out)
    rec = SeqRecord(
        Seq(seq),
        id="consensus_masked",
        description=f"mask: gaps not multiple of 3 or >= {min_gap}, pad={pad}"
    )
    SeqIO.write([rec], out_fa, "fasta")

def main(argv: List[str] = None) -> int:
    ap = argparse.ArgumentParser(description="Mask gaps not multiple of 3 or long gaps in consensus vs reference")
    ap.add_argument("--aln", required=True, help="MSA FASTA (includes ref and consensus)")
    ap.add_argument("--ref-index", type=int, default=0, help="Index of the reference in the MSA (default 0)")
    ap.add_argument("--cons-index", type=int, default=1, help="Index of the consensus in the MSA (default 1)")
    ap.add_argument("--min-gap", type=int, default=15, help="Minimum gap length to mask aggressively (default 15)")
    ap.add_argument("--pad", type=int, default=0, help="Extra padding of Ns around the gap (default 0)")
    ap.add_argument("--out", required=True, help="Output FASTA")
    argv = argv if argv is not None else sys.argv[1:]
    args = ap.parse_args(argv)
    run(args.aln, args.ref_index, args.cons_index, args.min_gap, args.pad, args.out)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
