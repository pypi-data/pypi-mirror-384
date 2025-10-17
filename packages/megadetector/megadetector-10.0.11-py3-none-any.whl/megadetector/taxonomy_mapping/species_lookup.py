"""

species_lookup.py

Look up species names (common or scientific) in the GBIF and iNaturalist
taxonomies.

Run initialize_taxonomy_lookup() before calling any other function.

"""

#%% Constants and imports

import argparse
import pickle
import shutil
import zipfile
import sys
import os

from collections import defaultdict
from itertools import compress
from tqdm import tqdm
from typing import Any, Dict, List, Mapping, Sequence, Set

import pandas as pd
import numpy as np

from megadetector.utils import url_utils

taxonomy_download_dir = os.path.expanduser('~/taxonomy')

taxonomy_urls = {
    'GBIF': 'https://hosted-datasets.gbif.org/datasets/backbone/current/backbone.zip',
    'iNaturalist': 'https://www.inaturalist.org/taxa/inaturalist-taxonomy.dwca.zip'
}

files_to_unzip = {
    'GBIF': ['Taxon.tsv', 'VernacularName.tsv'],
    'iNaturalist': ['taxa.csv','VernacularNames-english.csv']
}

# As of 2025.06.24:
#
# GBIF: 950MB zipped, 2.3GB of relevant content unzipped
# iNat: 71MB zipped, 415MB of relevant content unzipped

os.makedirs(taxonomy_download_dir, exist_ok=True)
for taxonomy_name in taxonomy_urls:
    taxonomy_dir = os.path.join(taxonomy_download_dir, taxonomy_name)
    os.makedirs(taxonomy_dir, exist_ok=True)

serialized_structures_file = os.path.join(taxonomy_download_dir,
                                          'serialized_taxonomies.p')

# These are un-initialized globals that must be initialized by
# the initialize_taxonomy_lookup() function below.
inat_taxonomy = None # : pd.DataFrame
gbif_taxonomy = None # : pd.DataFrame
gbif_common_mapping = None # : pd.DataFrame
inat_taxon_id_to_row = None # : Dict[np.int64, int]
gbif_taxon_id_to_row = None # : Dict[np.int64, int]
inat_taxon_id_to_vernacular = None # : Dict[np.int64, Set[str]]
inat_vernacular_to_taxon_id = None # : Dict[str, np.int64]
inat_taxon_id_to_scientific = None # : Dict[np.int64, Set[str]]
inat_scientific_to_taxon_id = None # : Dict[str, np.int64]
gbif_taxon_id_to_vernacular = None # : Dict[np.int64, Set[str]]
gbif_vernacular_to_taxon_id = None # : Dict[str, np.int64]
gbif_taxon_id_to_scientific = None # : Dict[np.int64, Set[str]]
gbif_scientific_to_taxon_id = None # : Dict[str, np.int64]


#%% Functions

# Initialization function

def initialize_taxonomy_lookup(force_init=False):
    """
    Initialize this module by doing the following:

    * Downloads and unzips the current GBIF and iNat taxonomies if necessary
      (only unzips what's necessary, but does not delete the original zipfiles)
    * Builds a bunch of dictionaries and tables to facilitate lookup
    * Serializes those tables via pickle
    * Skips all of the above if the serialized pickle file already exists

    Args:
        force_init (bool, optional): force re-download and parsing of the source .zip files,
            even if the cached .p file already exists
    """

    #%%

    global inat_taxonomy,\
        gbif_taxonomy,\
        gbif_common_mapping,\
        inat_taxon_id_to_row,\
        gbif_taxon_id_to_row,\
        inat_taxon_id_to_vernacular,\
        inat_vernacular_to_taxon_id,\
        inat_taxon_id_to_scientific,\
        inat_scientific_to_taxon_id,\
        gbif_taxon_id_to_vernacular,\
        gbif_vernacular_to_taxon_id,\
        gbif_taxon_id_to_scientific,\
        gbif_scientific_to_taxon_id


    #%% Load serialized taxonomy info if we've already saved it

    if (not force_init) and (inat_taxonomy is not None):
        print('Skipping taxonomy re-init')
        return

    if (not force_init) and (os.path.isfile(serialized_structures_file)):

        print(f'De-serializing taxonomy data from {serialized_structures_file}')

        with open(serialized_structures_file, 'rb') as f:
            structures_to_serialize = pickle.load(f)

        inat_taxonomy,\
        gbif_taxonomy,\
        gbif_common_mapping,\
        inat_taxon_id_to_row,\
        gbif_taxon_id_to_row,\
        inat_taxon_id_to_vernacular,\
        inat_vernacular_to_taxon_id,\
        inat_taxon_id_to_scientific,\
        inat_scientific_to_taxon_id,\
        gbif_taxon_id_to_vernacular,\
        gbif_vernacular_to_taxon_id,\
        gbif_taxon_id_to_scientific,\
        gbif_scientific_to_taxon_id = structures_to_serialize

        return


    #%% Download and unzip taxonomy files

    # taxonomy_name = list(taxonomy_urls.items())[0][0]; zip_url = list(taxonomy_urls.items())[0][1]
    for taxonomy_name, zip_url in taxonomy_urls.items():

        need_to_download = False

        if force_init:
            need_to_download = True

        # Don't download the zipfile if we've already unzipped what we need
        for fn in files_to_unzip[taxonomy_name]:
            target_file = os.path.join(
                taxonomy_download_dir, taxonomy_name, fn)
            if not os.path.isfile(target_file):
                need_to_download = True
                break
        if not need_to_download:
            print(f'Bypassing download of {taxonomy_name}, all files available')
            continue

        zipfile_path = os.path.join(
            taxonomy_download_dir, zip_url.split('/')[-1])

        # Bypasses download if the file exists already (unless force_init is set)
        url_utils.download_url(
            zip_url, os.path.join(zipfile_path),
            progress_updater=url_utils.DownloadProgressBar(),
            verbose=True,force_download=force_init)

        # Unzip the files we need
        files_we_need = files_to_unzip[taxonomy_name]

        with zipfile.ZipFile(zipfile_path, 'r') as zipH:

            for fn in files_we_need:
                print('Unzipping {}'.format(fn))
                target_file = os.path.join(
                    taxonomy_download_dir, taxonomy_name, os.path.basename(fn))

                if (not force_init) and (os.path.isfile(target_file)):
                    print(f'Bypassing unzip of {target_file}, file exists')
                else:
                    os.makedirs(os.path.basename(target_file),exist_ok=True)
                    with zipH.open(fn) as zf, open(target_file, 'wb') as f:
                        shutil.copyfileobj(zf, f)

            # ...for each file that we need from this zipfile

    # ...for each taxonomy


    #%% Create dataframes from each of the taxonomy/vernacular files

    # Load iNat taxonomy
    inat_taxonomy_file = os.path.join(taxonomy_download_dir, 'iNaturalist', 'taxa.csv')
    print('Loading iNat taxonomy from {}'.format(inat_taxonomy_file))
    inat_taxonomy = pd.read_csv(inat_taxonomy_file)
    inat_taxonomy['scientificName'] = inat_taxonomy['scientificName'].fillna('').str.strip()

    # Delete columns we won't use.  The "taxonID" column is a non-int version of "ID"
    inat_taxonomy = inat_taxonomy.drop(['identifier', 'taxonID', 'modified', 'references'], axis=1)

    # The "parentNameUsageID" column in inat_taxonomy is a URL, like:
    #
    # https://www.inaturalist.org/taxa/71262
    #
    # Convert this column to be integer-valued, using only the last token of the URL
    inat_taxonomy['parentNameUsageID'] = \
        inat_taxonomy['parentNameUsageID'].str.split('/').str[-1].fillna(0).astype(int)

    # Rename the "id" column to "taxonID"
    inat_taxonomy = inat_taxonomy.rename(columns={'id': 'taxonID'})

    assert 'id' not in inat_taxonomy.columns
    assert 'taxonID' in inat_taxonomy.columns

    # Load iNat common name mapping
    inat_common_mapping_file = os.path.join(taxonomy_download_dir, 'iNaturalist', 'VernacularNames-english.csv')
    inat_common_mapping = pd.read_csv(inat_common_mapping_file)
    inat_common_mapping['vernacularName'] = inat_common_mapping['vernacularName'].fillna('').str.strip()

    inat_common_mapping = inat_common_mapping.drop(['language','locality','countryCode',
                                                    'source','lexicon','contributor','created'], axis=1)
    assert 'id' in inat_common_mapping.columns
    assert 'taxonID' not in inat_common_mapping.columns
    assert 'vernacularName' in inat_common_mapping.columns

    # Load GBIF taxonomy
    gbif_taxonomy_file = os.path.join(taxonomy_download_dir, 'GBIF', 'Taxon.tsv')
    print('Loading GBIF taxonomy from {}'.format(gbif_taxonomy_file))
    gbif_taxonomy = pd.read_csv(gbif_taxonomy_file, sep='\t', encoding='utf-8',on_bad_lines='warn')
    gbif_taxonomy['scientificName'] = gbif_taxonomy['scientificName'].fillna('').str.strip()
    gbif_taxonomy['canonicalName'] = gbif_taxonomy['canonicalName'].fillna('').str.strip()
    gbif_taxonomy['parentNameUsageID'] = gbif_taxonomy['parentNameUsageID'].fillna(-1).astype(int)

    # Remove questionable rows from the GBIF taxonomy
    gbif_taxonomy = gbif_taxonomy[~gbif_taxonomy['taxonomicStatus'].isin(['doubtful', 'misapplied'])]
    gbif_taxonomy = gbif_taxonomy.reset_index()

    gbif_taxonomy = gbif_taxonomy.drop(['datasetID','acceptedNameUsageID','originalNameUsageID',
                                        'scientificNameAuthorship','nameAccordingTo','namePublishedIn',
                                        'taxonomicStatus','nomenclaturalStatus','taxonRemarks'], axis=1)

    assert 'taxonID' in gbif_taxonomy.columns
    assert 'scientificName' in gbif_taxonomy.columns

    # Load GBIF common name mapping
    gbif_common_mapping = pd.read_csv(os.path.join(
        taxonomy_download_dir, 'GBIF', 'VernacularName.tsv'), sep='\t')
    gbif_common_mapping['vernacularName'] = gbif_common_mapping['vernacularName'].fillna('').str.strip()

    # Only keep English mappings
    gbif_common_mapping = gbif_common_mapping.loc[gbif_common_mapping['language'] == 'en']
    gbif_common_mapping = gbif_common_mapping.reset_index()

    gbif_common_mapping = gbif_common_mapping.drop(['language','country','countryCode','sex',
                                                    'lifeStage','source'],axis=1)

    assert 'taxonID' in gbif_common_mapping.columns
    assert 'vernacularName' in gbif_common_mapping.columns


    # Convert everything to lowercase

    def convert_df_to_lowercase(df):
        df = df.applymap(lambda s: s.lower() if isinstance(s, str) else s)
        return df

    inat_taxonomy = convert_df_to_lowercase(inat_taxonomy)
    gbif_taxonomy = convert_df_to_lowercase(gbif_taxonomy)
    gbif_common_mapping = convert_df_to_lowercase(gbif_common_mapping)
    inat_common_mapping = convert_df_to_lowercase(inat_common_mapping)


    ##%% For each taxonomy table, create a mapping from taxon IDs to rows

    inat_taxon_id_to_row = {}
    gbif_taxon_id_to_row = {}

    print('Building iNat taxonID --> row table')
    for i_row, row in tqdm(inat_taxonomy.iterrows(), total=len(inat_taxonomy)):
        taxon_id = row['taxonID']
        assert isinstance(taxon_id, int)
        inat_taxon_id_to_row[taxon_id] = i_row

    print('Building GBIF taxonID --> row table')
    for i_row, row in tqdm(gbif_taxonomy.iterrows(), total=len(gbif_taxonomy)):
        taxon_id = row['taxonID']
        assert isinstance(taxon_id, int)
        gbif_taxon_id_to_row[taxon_id] = i_row


    ##%% Create name mapping dictionaries

    inat_taxon_id_to_vernacular = defaultdict(set)
    inat_vernacular_to_taxon_id = defaultdict(set)
    inat_taxon_id_to_scientific = defaultdict(set)
    inat_scientific_to_taxon_id = defaultdict(set)

    gbif_taxon_id_to_vernacular = defaultdict(set)
    gbif_vernacular_to_taxon_id = defaultdict(set)
    gbif_taxon_id_to_scientific = defaultdict(set)
    gbif_scientific_to_taxon_id = defaultdict(set)


    # Build iNat dictionaries

    print('Building lookup dictionaries for iNat taxonomy')

    # iNat Scientific name mapping

    for i_row, row in tqdm(inat_taxonomy.iterrows(), total=len(inat_taxonomy)):

        taxon_id = row['taxonID']
        assert isinstance(taxon_id,int)

        scientific_name = row['scientificName']
        assert len(scientific_name) > 0

        inat_taxon_id_to_scientific[taxon_id].add(scientific_name)
        inat_scientific_to_taxon_id[scientific_name].add(taxon_id)

    # iNat common name mapping

    inat_taxon_ids_in_vernacular_file_but_not_in_taxa_file = set()

    for i_row, row in tqdm(inat_common_mapping.iterrows(), total=len(inat_common_mapping)):

        taxon_id = row['id']
        assert isinstance(taxon_id,int)

        # This should never happen; we will assert() this at the end of the loop
        if taxon_id not in inat_taxon_id_to_scientific:
            inat_taxon_ids_in_vernacular_file_but_not_in_taxa_file.add(taxon_id)
            continue

        vernacular_name = row['vernacularName']

        assert len(vernacular_name) > 0
        inat_taxon_id_to_vernacular[taxon_id].add(vernacular_name)
        inat_vernacular_to_taxon_id[vernacular_name].add(taxon_id)

    assert len(inat_taxon_ids_in_vernacular_file_but_not_in_taxa_file) == 0


    ##%% Build GBIF dictionaries

    print('Building lookup dictionaries for GBIF taxonomy')

    # GBIF scientific name mapping

    for i_row, row in tqdm(gbif_taxonomy.iterrows(), total=len(gbif_taxonomy)):

        taxon_id = row['taxonID']
        assert isinstance(taxon_id,int)

        # The "canonical name" is the Latin name; the "scientific name"
        # column includes other information.  For example:
        #
        # "scientificName": Schizophoria impressa (Hall, 1843)
        # "canonicalName": Schizophoria impressa
        #
        # Also see:
        #
        # http://globalnames.org/docs/glossary/

        scientific_name = row['canonicalName']

        # This only seems to happen for really esoteric species that aren't
        # likely to apply to our problems, but doing this for completeness.
        if len(scientific_name) == 0:
            scientific_name = row['scientificName']

        assert len(scientific_name) > 0
        gbif_taxon_id_to_scientific[taxon_id].add(scientific_name)
        gbif_scientific_to_taxon_id[scientific_name].add(taxon_id)

    # GBIF common name mapping

    gbif_taxon_ids_in_vernacular_file_but_not_in_taxa_file = set()

    for i_row, row in tqdm(gbif_common_mapping.iterrows(), total=len(gbif_common_mapping)):

        taxon_id = row['taxonID']
        assert isinstance(taxon_id,int)

        # Don't include taxon IDs that were removed from the master table
        if taxon_id not in gbif_taxon_id_to_scientific:
            gbif_taxon_ids_in_vernacular_file_but_not_in_taxa_file.add(taxon_id)
            continue

        vernacular_name = row['vernacularName']

        assert len(vernacular_name) > 0
        gbif_taxon_id_to_vernacular[taxon_id].add(vernacular_name)
        gbif_vernacular_to_taxon_id[vernacular_name].add(taxon_id)

    print('Finished GBIF common --> scientific mapping, failed to map {} of {} taxon IDs'.format(
        len(gbif_taxon_ids_in_vernacular_file_but_not_in_taxa_file),
        len(gbif_common_mapping)
    ))


    ##%% Save everything to file

    structures_to_serialize = [
        inat_taxonomy,
        gbif_taxonomy,
        gbif_common_mapping,
        inat_taxon_id_to_row,
        gbif_taxon_id_to_row,
        inat_taxon_id_to_vernacular,
        inat_vernacular_to_taxon_id,
        inat_taxon_id_to_scientific,
        inat_scientific_to_taxon_id,
        gbif_taxon_id_to_vernacular,
        gbif_vernacular_to_taxon_id,
        gbif_taxon_id_to_scientific,
        gbif_scientific_to_taxon_id
    ]

    print('Serializing to {}...'.format(serialized_structures_file), end='')
    if not os.path.isfile(serialized_structures_file):
        with open(serialized_structures_file, 'wb') as p:
            pickle.dump(structures_to_serialize, p)
    print('...done')


    #%%

# ...def initialize_taxonomy_lookup(...)


def get_scientific_name_from_row(r):
    """
    r: a dataframe that's really a row in one of our taxonomy tables
    """

    if 'canonicalName' in r and len(r['canonicalName']) > 0:
        scientific_name = r['canonicalName']
    else:
        scientific_name = r['scientificName']
    return scientific_name


def taxonomy_row_to_string(r):
    """
    r: a dataframe that's really a row in one of our taxonomy tables
    """

    if 'vernacularName' in r:
        common_string = ' (' + r['vernacularName'] + ')'
    else:
        common_string = ''
    scientific_name = get_scientific_name_from_row(r)

    return r['taxonRank'] + ' ' + scientific_name + common_string


def traverse_taxonomy(matching_rownums: Sequence[int],
                      taxon_id_to_row: Mapping[str, int],
                      taxon_id_to_vernacular: Mapping[str, Set[str]],
                      taxonomy: pd.DataFrame,
                      source_name: str,
                      query: str) -> List[Dict[str, Any]]:
    """
    Given a data frame that's a set of rows from one of our taxonomy tables,
    walks the taxonomy hierarchy from each row to put together a full taxonomy
    tree, then prunes redundant trees (e.g. if we had separate hits for a
    species and the genus that contains that species.)

    Returns a list of dicts:
    [
      {
        'source': 'inat' or 'gbif',
        'taxonomy': [(taxon_id, taxon_rank, scientific_name, [common names])]
      },
      ...
    ]
    """

    # list of dicts: {'source': source_name, 'taxonomy': match_details}
    matching_trees: List[Dict[str, Any]] = []

    # i_match = 0
    for i_match in matching_rownums:

        # list of (taxon_id, taxonRank, scientific name, [vernacular names])
        # corresponding to an exact match and its parents
        match_details = []
        current_row = taxonomy.iloc[i_match]

        # Walk taxonomy hierarchy
        while True:

            taxon_id = current_row['taxonID']
            # sort for determinism
            vernacular_names = sorted(taxon_id_to_vernacular[taxon_id])
            match_details.append((taxon_id, current_row['taxonRank'],
                                  get_scientific_name_from_row(current_row),
                                  vernacular_names))

            if np.isnan(current_row['parentNameUsageID']):
                break
            parent_taxon_id = current_row['parentNameUsageID'].astype('int64')
            if parent_taxon_id not in taxon_id_to_row:
                # This can happen because we remove questionable rows from the
                # GBIF taxonomy
                # print(f'Warning: no row exists for parent_taxon_id {parent_taxon_id},' + \
                #      f'child taxon_id: {taxon_id}, query: {query}')
                break
            i_parent_row = taxon_id_to_row[parent_taxon_id]
            current_row = taxonomy.iloc[i_parent_row]

            # The GBIF taxonomy contains unranked entries
            if current_row['taxonRank'] == 'unranked':
                break

        # ...while there is taxonomy left to walk

        matching_trees.append({'source': source_name,
                               'taxonomy': match_details})

    # ...for each match

    # Remove redundant matches
    b_valid_tree = [True] * len(matching_rownums)
    # i_tree_a = 0; tree_a = matching_trees[i_tree_a]
    for i_tree_a, tree_a in enumerate(matching_trees):

        tree_a_primary_taxon_id = tree_a['taxonomy'][0][0]

        # i_tree_b = 1; tree_b = matching_trees[i_tree_b]
        for i_tree_b, tree_b in enumerate(matching_trees):

            if i_tree_a == i_tree_b:
                continue

            # If tree a's primary taxon ID is inside tree b, discard tree a
            #
            # taxonomy_level_b = tree_b['taxonomy'][0]
            for taxonomy_level_b in tree_b['taxonomy']:
                if tree_a_primary_taxon_id == taxonomy_level_b[0]:
                    b_valid_tree[i_tree_a] = False
                    break

            # ...for each level in taxonomy B

        # ...for each tree (inner)

    # ...for each tree (outer)

    matching_trees = list(compress(matching_trees, b_valid_tree))
    return matching_trees

# ...def traverse_taxonomy()


def get_taxonomic_info(query: str) -> List[Dict[str, Any]]:
    """
    Main entry point: get taxonomic matches from both taxonomies for [query],
    which may be a scientific or common name.
    """

    query = query.strip().lower()
    # print("Finding taxonomy information for: {0}".format(query))

    inat_taxon_ids = set()
    if query in inat_scientific_to_taxon_id:
        inat_taxon_ids |= inat_scientific_to_taxon_id[query]
    if query in inat_vernacular_to_taxon_id:
        inat_taxon_ids |= inat_vernacular_to_taxon_id[query]

    # In GBIF, some queries hit for both common and scientific, make sure we end
    # up with unique inputs
    gbif_taxon_ids = set()
    if query in gbif_scientific_to_taxon_id:
        gbif_taxon_ids |= gbif_scientific_to_taxon_id[query]
    if query in gbif_vernacular_to_taxon_id:
        gbif_taxon_ids |= gbif_vernacular_to_taxon_id[query]

    # If the species is not found in either taxonomy, return None
    if (len(inat_taxon_ids) == 0) and (len(gbif_taxon_ids) == 0):
        return []

    # Both GBIF and iNat have a 1-to-1 mapping between taxon_id and row number
    inat_row_indices = [inat_taxon_id_to_row[i] for i in inat_taxon_ids]
    gbif_row_indices = [gbif_taxon_id_to_row[i] for i in gbif_taxon_ids]

    # Walk both taxonomies
    inat_matching_trees = traverse_taxonomy(
        inat_row_indices, inat_taxon_id_to_row, inat_taxon_id_to_vernacular,
        inat_taxonomy, 'inat', query)
    gbif_matching_trees = traverse_taxonomy(
        gbif_row_indices, gbif_taxon_id_to_row, gbif_taxon_id_to_vernacular,
        gbif_taxonomy, 'gbif', query)

    return gbif_matching_trees + inat_matching_trees

# ...def get_taxonomic_info()


def print_taxonomy_matches(matches, verbose=False):
    """
    Console-friendly printing function to make nicely-indentend trees
    """

    # m = matches[0]
    for m in matches:

        source = m['source']

        # For example: [(9761484, 'species', 'anas platyrhynchos')]
        for i_taxonomy_level in range(0, len(m['taxonomy'])):
            taxonomy_level_info = m['taxonomy'][i_taxonomy_level]
            taxonomy_level = taxonomy_level_info[1]
            name = taxonomy_level_info[2]
            common = taxonomy_level_info[3]

            if i_taxonomy_level > 0:
                print('\t',end='')

            print('{} {} ({})'.format(taxonomy_level, name, common), end='')

            if i_taxonomy_level == 0:
                print(' ({})'.format(source))
            else:
                print('')

            if not verbose:
                break

        # ...for each taxonomy level

    # ...for each match

# ...def print_taxonomy_matches()


#%% Taxonomy functions that make subjective judgements

import unicodedata
import re

def slugify(value: Any, allow_unicode: bool = False) -> str:
    """
    From:
    https://github.com/django/django/blob/master/django/utils/text.py

    Convert to ASCII if 'allow_unicode' is False. Convert spaces to hyphens.
    Remove characters that aren't alphanumerics, underscores, or hyphens.
    Convert to lowercase. Also strip leading and trailing whitespace.
    """

    value = str(value)
    value = unicodedata.normalize('NFKC', value)
    if not allow_unicode:
        value = value.encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value.lower()).strip()
    return re.sub(r'[-\s]+', '-', value)


class TaxonomicMatch:

    def __init__(self, scientific_name, common_name, taxonomic_level, source,
                 taxonomy_string, match):
        self.scientific_name = scientific_name
        self.common_name = common_name
        self.taxonomic_level = taxonomic_level
        self.source = source
        self.taxonomy_string = taxonomy_string
        self.match = match

    def __repr__(self):
        return ('TaxonomicMatch('
            f'scientific_name={self.scientific_name}, '
            f'common_name={self.common_name}, '
            f'taxonomic_level={self.taxonomic_level}, '
            f'source={self.source}')


hyphenated_terms = ['crowned', 'backed', 'throated', 'tailed', 'headed', 'cheeked',
                    'ruffed', 'browed', 'eating', 'striped', 'shanked',
                    'fronted', 'bellied', 'spotted', 'eared', 'collared', 'breasted',
                    'necked']

def pop_levels(m, n_levels=1):
    """
    Remove [n_levels] levels from the bottom of the TaxonomicMatch object m, typically used to remove
    silly subgenera.
    """

    v = eval(m.taxonomy_string)
    assert v[0][1] == m.taxonomic_level
    assert v[0][2] == m.scientific_name
    popped_v = v[n_levels:]
    taxonomic_level = popped_v[0][1]
    scientific_name = popped_v[0][2]
    common_name = popped_v[0][3]
    if len(common_name) == 0:
        common_name = ''
    else:
        common_name = common_name[0]
    taxonomy_string = str(popped_v)
    source = m.source
    return TaxonomicMatch(scientific_name=scientific_name,
                          common_name=common_name,
                          taxonomic_level=taxonomic_level,
                          source=source,
                          taxonomy_string=taxonomy_string,
                          match=None)

# ...def pop_levels(...)


def get_preferred_taxonomic_match(query: str, taxonomy_preference = 'inat', retry=True) -> TaxonomicMatch:
    """
    Wrapper for _get_preferred_taxonomic_match, but expressing a variety of heuristics
    and preferences that are specific to our scenario.

    Args:
        query (str): The common or scientific name we want to look up
        taxonomy_preference (str, optional): 'inat' or 'gbif'
        retry (bool, optional): if the initial lookup fails, should we try heuristic
            substitutions, e.g. replacing "_" with " ", or "spp" with "species"?

    Returns:
        TaxonomicMatch: the best taxonomic match, or None
    """

    m,query = _get_preferred_taxonomic_match(query=query,taxonomy_preference=taxonomy_preference)
    if (len(m.scientific_name) > 0) or (not retry):
        return m

    for s in hyphenated_terms:
        query = query.replace(' ' + s,'-' + s)
    m,query = _get_preferred_taxonomic_match(query=query,taxonomy_preference=taxonomy_preference)

    if (len(m.scientific_name) > 0) or (not retry):
        return m

    query = query.replace(' species','')
    query = query.replace(' order','')
    query = query.replace(' genus','')
    query = query.replace(' family','')
    query = query.replace(' subfamily','')
    m,query = _get_preferred_taxonomic_match(query=query,taxonomy_preference=taxonomy_preference)

    return m


def validate_and_convert(data):
    """
    Recursively validates that all elements in the nested structure are only
    tuples, lists, ints, or np.int64, and converts np.int64 to int.

    Args:
        data: The nested structure to validate and convert

    Returns:
        The validated and converted structure

    Raises:
        TypeError: If an invalid type is encountered
    """

    if isinstance(data, np.int64):
        return int(data)
    elif isinstance(data, int) or isinstance(data, str):
        return data
    elif isinstance(data, (list, tuple)):
        # Process lists and tuples recursively
        container_type = type(data)
        return container_type(validate_and_convert(item) for item in data)
    else:
        raise TypeError(f"Invalid type encountered: {type(data).__name__}. "
                        f"Only int, np.int64, list, and tuple are allowed.")

# ...def validate_and_convert(...)


def _get_preferred_taxonomic_match(query: str, taxonomy_preference = 'inat') -> TaxonomicMatch:

    query = query.lower().strip().replace('_', ' ')
    query = query.replace('unidentified','')
    query = query.replace('unknown','')
    if query.endswith(' sp'):
        query = query.replace(' sp','')
    if query.endswith(' group'):
        query = query.replace(' group','')

    query = query.strip()

    # query = 'person'
    matches = get_taxonomic_info(query)

    # Do we have an iNat match?
    inat_matches = [m for m in matches if m['source'] == 'inat']
    gbif_matches = [m for m in matches if m['source'] == 'gbif']

    # print_taxonomy_matches(inat_matches, verbose=True)
    # print_taxonomy_matches(gbif_matches, verbose=True)

    scientific_name = ''
    common_name = ''
    taxonomic_level = ''
    match = ''
    source = ''
    taxonomy_string = ''

    n_inat_matches = len(inat_matches)
    n_gbif_matches = len(gbif_matches)

    selected_matches = None

    assert taxonomy_preference in ['gbif','inat'],\
        'Unrecognized taxonomy preference: {}'.format(taxonomy_preference)

    if n_inat_matches > 0 and taxonomy_preference == 'inat':
        selected_matches = 'inat'
    elif n_gbif_matches > 0:
        selected_matches = 'gbif'

    if selected_matches == 'inat':

        i_match = 0

        if len(inat_matches) > 1:
            # print('Warning: multiple iNat matches for {}'.format(query))

            # Prefer chordates... most of the names that aren't what we want
            # are esoteric insects, like a moth called "cheetah"
            #
            # If we can't find a chordate, just take the first match.
            #
            # i_test_match = 0
            for i_test_match, match in enumerate(inat_matches):
                found_vertebrate = False
                taxonomy = match['taxonomy']
                for taxonomy_level in taxonomy:
                    taxon_rank = taxonomy_level[1]
                    scientific_name = taxonomy_level[2]
                    if taxon_rank == 'phylum' and scientific_name == 'chordata':
                        i_match = i_test_match
                        found_vertebrate = True
                        break
                if found_vertebrate:
                    break

        match = inat_matches[i_match]['taxonomy']

        # This is (taxonID, taxonLevel, scientific, [list of common])
        lowest_level = match[0]
        taxonomic_level = lowest_level[1]
        scientific_name = lowest_level[2]
        assert len(scientific_name) > 0
        common_names = lowest_level[3]
        if len(common_names) > 1:
            # print(f'Warning: multiple iNat common names for {query}')
            # Default to returning the query
            if query in common_names:
                common_name = query
            else:
                common_name = common_names[0]
        elif len(common_names) > 0:
            common_name = common_names[0]

        # print(f'Matched iNat {query} to {scientific_name},{common_name}')
        source = 'inat'

    # ...if we had iNat matches

    # If we either prefer GBIF or didn't have iNat matches
    #
    # Code is deliberately redundant here; I'm expecting some subtleties in how
    # handle GBIF and iNat.
    elif selected_matches == 'gbif':

        i_match = 0

        if len(gbif_matches) > 1:
            # print('Warning: multiple GBIF matches for {}'.format(query))

            # Prefer chordates... most of the names that aren't what we want
            # are esoteric insects, like a moth called "cheetah"
            #
            # If we can't find a chordate, just take the first match.
            #
            # i_test_match = 0
            for i_test_match, match in enumerate(gbif_matches):
                found_vertebrate = False
                taxonomy = match['taxonomy']
                for taxonomy_level in taxonomy:
                    taxon_rank = taxonomy_level[1]
                    scientific_name = taxonomy_level[2]
                    if taxon_rank == 'phylum' and scientific_name == 'chordata':
                        i_match = i_test_match
                        found_vertebrate = True
                        break
                if found_vertebrate:
                    break

        match = gbif_matches[i_match]['taxonomy']

        # This is (taxonID, taxonLevel, scientific, [list of common])
        lowest_level = match[0]
        taxonomic_level = lowest_level[1]
        scientific_name = lowest_level[2]
        assert len(scientific_name) > 0

        common_names = lowest_level[3]
        if len(common_names) > 1:
            # print(f'Warning: multiple GBIF common names for {query}')
            # Default to returning the query
            if query in common_names:
                common_name = query
            else:
                common_name = common_names[0]
        elif len(common_names) > 0:
            common_name = common_names[0]

        source = 'gbif'

    # ...if we needed to look in the GBIF taxonomy

    # Convert np.int64's to ints
    if match is not None:
        match = validate_and_convert(match)

    taxonomy_string = str(match)

    m = TaxonomicMatch(scientific_name, common_name, taxonomic_level, source,
                        taxonomy_string, match)

    if (m.taxonomic_level == 'subgenus' and \
        match[1][1] == 'genus' and \
        match[1][2] == m.scientific_name):
        print('Removing redundant subgenus {}'.format(scientific_name))
        m = pop_levels(m,1)

    return m,query

# ...def _get_preferred_taxonomic_match()


#%% Interactive drivers and debug

if False:

    #%% Initialization

    initialize_taxonomy_lookup()


    #%% Taxonomic lookup

    # query = 'lion'
    query = 'xenoperdix'
    matches = get_taxonomic_info(query)
    # print(matches)

    print_taxonomy_matches(matches,verbose=True)

    print('\n\n')

    # Print the taxonomy in the taxonomy spreadsheet format
    assert matches[1]['source'] == 'inat'
    t = str(matches[1]['taxonomy'])
    print(t)
    import clipboard; clipboard.copy(t)


    #%% Directly access the taxonomy tables

    taxon_ids = gbif_vernacular_to_taxon_id['lion']
    for taxon_id in taxon_ids:
        i_row = gbif_taxon_id_to_row[taxon_id]
        print(taxonomy_row_to_string(gbif_taxonomy.iloc[i_row]))


#%% Command-line driver

def main(): # noqa

    # Read command line inputs (absolute path)
    parser = argparse.ArgumentParser()
    parser.add_argument('input_file')

    if len(sys.argv[1:]) == 0:
        parser.print_help()
        parser.exit()

    args = parser.parse_args()
    input_file = args.input_file

    initialize_taxonomy_lookup()

    # Read the tokens from the input text file
    with open(input_file, 'r') as f:
        tokens = f.readlines()

    # Loop through each token and get scientific name
    for token in tokens:
        token = token.strip().lower()
        matches = get_taxonomic_info(token)
        print_taxonomy_matches(matches)

if __name__ == '__main__':
    main()
