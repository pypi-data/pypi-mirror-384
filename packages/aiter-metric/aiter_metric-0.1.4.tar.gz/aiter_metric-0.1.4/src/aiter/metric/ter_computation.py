import pandas as pd
from sacrebleu.metrics import TER

from tqdm import tqdm

def compute_ter(ter, ref, hyp):
    return ter.sentence_score(hyp, [ref]).score

def compute_scores(df, version):
    ter = TER(no_punct=True)
    code_version = version["CODE_VERSION"]
    mask = df['corrected_hypothesis'].notna()
    if mask.any():
        for idx in tqdm(df[mask].index, desc="Calcul des scores TER"):
            df.at[idx, 'score'] = compute_ter(ter, df.at[idx, 'corrected_hypothesis'], df.at[idx, 'hypothesis'])
            if code_version in ["2", "3"]:
                df.at[idx, 'cor_score'] = compute_ter(ter, df.at[idx, 'corrected_hypothesis'], df.at[idx, 'filtered_hypothesis'])
                df.at[idx, 'ot_score'] = compute_ter(ter, df.at[idx, 'filtered_hypothesis'], df.at[idx, 'hypothesis'])
    else:
        raise ValueError("Run reformulation before computing the TER.")
    return df