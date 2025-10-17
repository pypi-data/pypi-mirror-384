"""

prepare_lila_taxonomy_release.py

Given the private intermediate taxonomy mapping (produced by map_new_lila_datasets.py),
prepare the public (release) taxonomy mapping file.

"""

#%% Imports and constants

import os
import json
import pandas as pd


#%% Prevent execution during infrastructural imports

if False:

    #%% Filenames

    lila_taxonomy_file = 'c:/git/agentmorrisprivate/lila-taxonomy/lila-taxonomy-mapping.csv'
    release_taxonomy_file = os.path.expanduser('~/lila/lila-taxonomy-mapping_release.csv')
    # import clipboard; clipboard.copy(release_taxonomy_file)

    # Created by get_lila_annotation_counts.py... contains counts for each category
    lila_dataset_to_categories_file = os.path.expanduser('~/lila/lila_categories_list/lila_dataset_to_categories.json')

    assert os.path.isfile(lila_dataset_to_categories_file)
    assert os.path.isfile(lila_taxonomy_file)


    #%% Find out which categories are actually used

    df = pd.read_csv(lila_taxonomy_file)

    with open(lila_dataset_to_categories_file,'r') as f:
        lila_dataset_to_categories = json.load(f)

    used_category_mappings = []

    # dataset_name = datasets_to_map[0]
    for dataset_name in lila_dataset_to_categories.keys():

        ds_categories = lila_dataset_to_categories[dataset_name]
        for category in ds_categories:
            category_name = category['name'].lower()
            assert ':' not in category_name
            mapping_name = dataset_name + ':' + category_name
            used_category_mappings.append(mapping_name)

    df['used'] = False

    n_dropped = 0

    # i_row = 0; row = df.iloc[i_row]; row
    for i_row,row in df.iterrows():
        ds_name = row['dataset_name']
        query = row['query']
        mapping_name = ds_name + ':' + query
        if mapping_name in used_category_mappings:
            df.loc[i_row,'used'] = True
        else:
            n_dropped += 1
            print('Dropping unused mapping {}'.format(mapping_name))

    print('Dropping {} of {} mappings'.format(n_dropped,len(df)))

    df = df[df.used]
    df = df.drop('used',axis=1)


    #%% Generate the final output file

    assert not os.path.isfile(release_taxonomy_file), \
        'File {} exists, delete it manually before proceeding'.format(release_taxonomy_file)

    levels_to_include = ['kingdom',
                         'phylum',
                         'subphylum',
                         'superclass',
                         'class',
                         'subclass',
                         'infraclass',
                         'superorder',
                         'order',
                         'suborder',
                         'infraorder',
                         'superfamily',
                         'family',
                         'subfamily',
                         'tribe',
                         'genus',
                         'subgenus',
                         'species',
                         'subspecies',
                         'variety']

    levels_to_exclude = ['stateofmatter',
                         'zoosection',
                         'parvorder',
                         'complex',
                         'epifamily']

    for x in [levels_to_include,levels_to_exclude]:
        assert len(x) == len(set(x))

    for s in levels_to_exclude:
        assert s not in levels_to_include

    known_levels = levels_to_include + levels_to_exclude

    levels_used = set()

    # i_row = 0; row = df.iloc[i_row]; row
    for i_row,row in df.iterrows():

        if not isinstance(row['scientific_name'],str):
            assert not isinstance(row['taxonomy_string'],str)
            continue

        # This is a list of length-4 tuples that each look like:
        #
        # (41789, 'species', 'taxidea taxus', ['american badger'])
        taxonomic_match = eval(row['taxonomy_string'])

        # match_at_level = taxonomic_match[0]
        for match_at_level in taxonomic_match:
            assert len(match_at_level) == 4
            # E.g. "species"
            levels_used.add(match_at_level[1])

    levels_used = [s for s in levels_used if isinstance(s,str)]

    for s in levels_used:
        assert s in known_levels, 'Unrecognized level {}'.format(s)

    for s in levels_to_include:
        assert s in levels_used

    for s in levels_to_include:
        df[s] = ''

    # i_row = 0; row = df.iloc[i_row]; row
    for i_row,row in df.iterrows():

        if not isinstance(row['scientific_name'],str):
            assert not isinstance(row['taxonomy_string'],str)
            continue

        # E.g.: (43117, 'genus', 'lepus', ['hares and jackrabbits']
        taxonomic_match = eval(row['taxonomy_string'])

        for match_at_level in taxonomic_match:
            level = match_at_level[1]
            if level in levels_to_include:
                df.loc[i_row,level] = match_at_level[2]

    df = df.drop('source',axis=1)
    df.to_csv(release_taxonomy_file,header=True,index=False)

    print('Wrote final output to {}'.format(release_taxonomy_file))


