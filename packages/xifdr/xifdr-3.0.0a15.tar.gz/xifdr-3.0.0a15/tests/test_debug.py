import logging
import numpy as np
import polars as pl
import pytest
from xifdr import boosting, fdr

from xifdr.fdr import single_fdr, full_fdr
from xifdr.boosting import boost

logging.basicConfig(level=logging.DEBUG)

@pytest.mark.slow
def test_boosting():
    df_rescored = pl.read_csv(
        '/Users/falk/Downloads/51394_rescored.csv',
        infer_schema_length=10000
    )
    df_fdr_standard = fdr.full_fdr(
        df_rescored.filter(
            ~pl.col('sequence_p1').str.replace_all('[^A-Z]', '').str.contains(
                pl.col('sequence_p2').str.replace_all('[^A-Z]', '')
            )
        ).select(
            score=pl.col('rescore'),
            sequence_p1=pl.col('sequence_p1'),
            sequence_p2=pl.col('sequence_p2'),
            start_pos_p1=pl.col('start_pos_p1'),
            start_pos_p2=pl.col('start_pos_p2'),
            link_pos_p1=pl.col('link_pos_p1'),
            link_pos_p2=pl.col('link_pos_p2'),
            protein_p1=pl.col('protein_p1'),
            protein_p2=pl.col('protein_p2'),
            decoy_p1=pl.col('decoy_p1'),
            decoy_p2=pl.col('decoy_p2'),
            coverage_p1=pl.col('unique_peak_conservative_coverage_p1'),
            coverage_p2=pl.col('unique_peak_conservative_coverage_p2'),
            charge=pl.col('precursor_charge'),
            fdr_group=pl.col('fdr_group'),
        ),
        csm_fdr=0.5,
        pep_fdr=1.00,
        prot_fdr=1.00,
        link_fdr=0.05,
        ppi_fdr=1.00,
        filter_back=False
    )
    res_betw = [
        df_fdr_standard[k].filter(
            pl.col('decoy_class')=='between'
        )
        for k in df_fdr_standard.keys()
        if k != 'prot'
    ]
    pass

def test_single_grouped_fdr():
    df_standard = pl.read_parquet('/Users/falk/Downloads/myec_kojak.parquet')
    df_standard = df_standard.sort('Score', descending=True)
    df_standard = df_standard.with_columns(
        standard_fdr=fdr.single_grouped_fdr(
            df_standard.with_columns(
                score=pl.col('Score'),
            )
        )
    )
    pass