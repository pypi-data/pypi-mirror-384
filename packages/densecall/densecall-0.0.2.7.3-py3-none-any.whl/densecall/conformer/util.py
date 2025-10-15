import numpy as np
import array


def format_mm_ml_tags(seq, poss, probs, mod_bases, can_base, strand: str = "+"):
    """Format MM and ML tags for BAM output. See
    https://samtools.github.io/hts-specs/SAMtags.pdf for format details.

    Args:
        seq (str): read-centric read sequence. For reference-anchored calls
            this should be the reverse complement sequence.
        poss (list): positions relative to seq
        probs (np.array): probabilities for modified bases
        mod_bases (list): modified base single letter codes
        can_base (str): canonical base
        strand (bool): should be '+' for SEQ-oriented strand and '-' if
            complement strand

    Returns:
        MM string tag and ML array tag
    """

    # initialize dict with all called mods to make sure all called mods are
    # shown in resulting tags
    per_mod_probs = dict((mod_base, []) for mod_base in mod_bases)
    for pos, mod_probs in sorted(zip(poss, probs)):
        # mod_probs is set to None if invalid sequence is encountered or too
        # few events are found around a mod
        if mod_probs is None:
            continue
        for mod_prob, mod_base in zip(mod_probs, mod_bases):
            per_mod_probs[mod_base].append((pos, mod_prob))

    mm_tag, ml_tag = "", array.array("B")
    for mod_base, pos_probs in per_mod_probs.items():
        if len(pos_probs) == 0:
            continue
        mod_poss, probs = zip(*sorted(pos_probs))

        # compute modified base positions relative to the running total of the
        # associated canonical base
        can_base_mod_poss = (
            np.cumsum([1 if b == can_base else 0 for b in seq])[
                np.array(mod_poss)
            ]
            - 1
        )
        mod_gaps = ",".join(
            map(str, np.diff(np.insert(can_base_mod_poss, 0, -1)) - 1)
        )

        mm_tag += f"{can_base}{strand}{mod_base}?,{mod_gaps};"
        # extract mod scores and scale to 0-255 range
        scaled_probs = np.floor(np.array(probs) * 256)
        # last interval includes prob=1
        scaled_probs[scaled_probs == 256] = 255
        ml_tag.extend(scaled_probs.astype(np.uint8))

    #return "MM:Z:"+mm_tag, "ML:B:C,"+','.join(map(str, ml_tag))
    return mm_tag, ml_tag


