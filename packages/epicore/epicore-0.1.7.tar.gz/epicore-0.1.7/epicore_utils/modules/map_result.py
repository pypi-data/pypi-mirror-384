"""
Assigns each peptide in the evidence files its core epitopes, the total intensity of that core epitope and the relative core intensity. 
"""
import warnings
import pandas as pd
import numpy as np
warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning)
import re
import os 
from itertools import repeat
import logging
import time
logger = logging.getLogger(__name__)

def read_entire_id_output(id_output: str) -> pd.DataFrame:
    """Read in the entire evidence file.
    
    Args:
        id_output: The string of the path to the evidence file.
    
    Returns:
        A pandas dataframe containing the evidence file.

    Raises:
        Exception: If the file type of the provided evidence file is not 
            supported.
    """
    # determine the file type
    ext = os.path.splitext(id_output)[1]
    if ext == '.csv':
        peptides_df = pd.read_csv(id_output, delimiter=',')
    elif ext == '.tsv':
        peptides_df = pd.read_csv(id_output, delimiter='\t')
    elif ext == '.xlsx':
        peptides_df = pd.read_excel(id_output)
    else:
        raise Exception('The file type of your evidence file is not supported. Please use an evidence file that has one of the following file types: csv, tsv, xlsx')
    return peptides_df

def aggregate_series(series: pd.Series, delimiter: str):
    """Aggregate the series.

    Args:
        series: A pandas series.
    
    Returns:
        A aggregated version of the pandas series. If all elements of the
        series are the same, only the first element is returned. If the 
        elements differ from each other a list of all elements is returned
        as a string.
    """
    series = series.fillna('nan')
    if series.name in  ['start', 'end', 'whole_epitopes_all', 'consensus_epitopes_all', 'proteome_occurrence', 'core_epitopes_intensity_all', 'relative_core_intensity_all']:
        return delimiter.join(series)
    elif len(set(series)) == 1:
        return series.iloc[0]
    else:
        return delimiter.join(series)


def map_pep_core(evidence_file: str, protein_df: pd.DataFrame, seq_column: str, protacc_column: str, start_column: str, end_column: str, intensity_column: str, delimiter: str, mod_pattern: str, proteome_dict: dict[str,str]) -> pd.DataFrame:
    """Map computed consensus epitope groups to the input evidence_file.
    
    Args:
        evidence_file: The string of the path to the evidence file.
        protein_df: A pandas dataframe containing one protein per row.
        seq_column: The string of the header of the column containing 
            peptide sequence information in the evidence file.
        protacc_column: The string of the header of the column containing 
            protein accession information in the evidence file.
        start_column: The string of the header of the column containing the 
            start positions of peptides in proteins.
        end_column: The string of the header of the column containing the end 
            position of peptides in proteins.
        intensity_column: The string of the header of the column containing 
            intensity information in the evidence file.
        delimiter: The delimiter that separates multiple entries in one column 
            in the evidence file.
        mod_pattern: A comma separated string with delimiters for peptide
            modifications

    Returns:
        The evidence_file with four additional columns containing the whole and 
        core sequence and total and relative intensity of each consensus 
        epitope group, to which the peptide of the row belongs.

    Raises:
        Exception: If the mappings are contradictory.
    """

    # read in entire evidence file
    evidence_file_df = read_entire_id_output(evidence_file)
    in_cols = evidence_file_df.columns.values
    if intensity_column:
        protein_df = protein_df[['sequence', 'accession', 'start', 'end', 'intensity', 'whole_epitopes_all','consensus_epitopes_all', 'core_epitopes_intensity_all', 'relative_core_intensity_all', 'proteome_occurrence', 'peptide_index']]
    else:
        protein_df = protein_df[['sequence', 'accession', 'start', 'end', 'whole_epitopes_all','consensus_epitopes_all', 'proteome_occurrence', 'peptide_index']]

    # reformat protein_df so every peptide sequence is represented by one row
    if intensity_column:
        protein_df = protein_df.explode(['sequence', 'start', 'end', 'intensity', 'whole_epitopes_all','consensus_epitopes_all', 'core_epitopes_intensity_all', 'relative_core_intensity_all', 'proteome_occurrence', 'peptide_index'])
    else: 
        protein_df = protein_df.explode(['sequence', 'start', 'end', 'whole_epitopes_all','consensus_epitopes_all', 'proteome_occurrence', 'peptide_index'])

    # reformat evidence file so each protein accession is represented by one row
    evidence_file_df[protacc_column] = evidence_file_df[protacc_column].str.split(delimiter)
    evidence_file_df = evidence_file_df.explode([protacc_column])
    evidence_merge_cols = [seq_column,protacc_column, 'index']
    if intensity_column:
        evidence_merge_cols.append(intensity_column)
    protein_merge_cols = ['sequence', 'accession', 'peptide_index']
    if 'intensity' in protein_df.columns:
        protein_merge_cols.append('intensity')

    # merge protein and evidence df to map each core epitope to the peptides that contribute to it 
    drop_cols = ['index', 'peptide_index']
    evidence_file_df = evidence_file_df.reset_index().merge(protein_df, left_on=evidence_merge_cols, right_on=protein_merge_cols)  
    if seq_column != 'sequence':
        drop_cols.append('sequence')
    if protacc_column != 'accession':
        drop_cols.append('accession')
    if intensity_column != 'intensity' and intensity_column:
        drop_cols.append('intensity')
    evidence_file_df = evidence_file_df[evidence_file_df.columns.drop(list(evidence_file_df.filter(regex='.*_x')))]
    evidence_file_df.columns = evidence_file_df.columns.str.replace(r'_y$','', regex=True)
    evidence_file_df = evidence_file_df.drop(drop_cols, axis=1)

    # group the rows which belong to the same peptide in the evidence file
    ev_cols = ['whole_epitopes_all', 'consensus_epitopes_all', protacc_column, 'proteome_occurrence']
    if intensity_column:
        ev_cols.append(intensity_column)
        ev_cols.append('core_epitopes_intensity_all')
        ev_cols.append('relative_core_intensity_all')
    evidence_file_df[ev_cols] = evidence_file_df[ev_cols].astype(str)
    group_cols = [col for col in evidence_file_df.columns if col not in [protacc_column, 'start', 'end', 'whole_epitopes_all','consensus_epitopes_all', 'core_epitopes_intensity_all', 'relative_core_intensity_all', 'proteome_occurrence']]
    evidence_file_df[group_cols] = evidence_file_df[group_cols].astype(str)
    grouped_evidence_file_df = evidence_file_df.fillna('nan').groupby([col for col in evidence_file_df.columns if col in group_cols], as_index=False).agg(lambda col: aggregate_series(col,delimiter))                                                                                                           

    # sort the dataframe columns so they match the input order
    out_cols = list(in_cols) + [col for col in grouped_evidence_file_df.columns.values if col not in in_cols]
    grouped_evidence_file_df = grouped_evidence_file_df[out_cols].rename(columns={'whole_epitopes_all':'entire_epitope_sequence','consensus_epitopes_all':'core_epitope_sequence'})
    if intensity_column:
        grouped_evidence_file_df = grouped_evidence_file_df.rename(columns={'core_epitopes_intensity_all':'consensus_epitope_intensity','relative_core_intensity_all':'relative_consensus_epitope_intensity' })
    return grouped_evidence_file_df

def gen_epitope_df(protein_df: pd.DataFrame) -> pd.DataFrame:
    """Generate dataframe that has one epitope per row.

    Args:
        protein_df: A pandas dataframe containing one protein per row.

    Returns:
        A reordered version of protein_df were each row stores one epitope.
    """
    # include intensity columns if present
    if ('core_epitopes_intensity' not in protein_df.columns) and ('relative_core_intensity' not in protein_df.columns):
        cols = ['whole_epitopes', 'consensus_epitopes','landscape', 'grouped_peptides_sequence']
    else:
        cols = ['whole_epitopes', 'consensus_epitopes','landscape', 'grouped_peptides_sequence', 'relative_core_intensity', 'core_epitopes_intensity']

    cols_acc = cols + ['accession']

    # separate each epitope in one row
    protein_df_long = protein_df.explode(cols)
    protein_df_long = protein_df_long.astype(str)
    epitopes_grouped_df = protein_df_long[cols_acc].groupby(cols)
    epitopes_grouped_df = epitopes_grouped_df.agg({'accession':lambda x:','.join(x)}).reset_index()
    
    logger.info(f'{len(epitopes_grouped_df)} unique epitopes were computed.')

    return epitopes_grouped_df
