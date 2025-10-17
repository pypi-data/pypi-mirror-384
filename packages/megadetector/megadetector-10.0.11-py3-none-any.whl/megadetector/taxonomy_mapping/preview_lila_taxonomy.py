"""

preview_lila_taxonomy.py

Does some consistency-checking on the LILA taxonomy file, and generates
an HTML preview page that we can use to determine whether the mappings
make sense.

"""

#%% Imports and constants

from tqdm import tqdm

import os
import pandas as pd

# lila_taxonomy_file = r"c:\git\agentmorrisprivate\lila-taxonomy\lila-taxonomy-mapping.csv"
lila_taxonomy_file = os.path.expanduser('~/lila/lila_additions_2025.10.07.csv')

preview_base = os.path.expanduser('~/lila/lila_taxonomy_preview')
os.makedirs(preview_base,exist_ok=True)
html_output_file = os.path.join(preview_base,'index.html')


#%% Support functions

def parse_taxonomy_string(taxonomy_string):

    taxonomic_match = eval(taxonomy_string)
    matched_entity = taxonomic_match[0]
    assert len(matched_entity) == 4

    level = matched_entity[1]

    scientific_name = matched_entity[2]

    common_names = matched_entity[3]
    if len(common_names) == 1:
        common_name = common_names[0]
    else:
        common_name = str(common_names)

    return scientific_name,common_name,level,taxonomic_match

def taxonomy_string_to_common_name(taxonomy_string):
    _,cn,_,_ = parse_taxonomy_string(taxonomy_string)
    return cn

def taxonomy_string_to_scientific(taxonomy_string):
    sn,_,_,_ = parse_taxonomy_string(taxonomy_string)
    return sn

def taxonomy_string_to_level(taxonomy_string):
    _,_,level,_ = parse_taxonomy_string(taxonomy_string)
    return level


#%% Prepare taxonomy lookup

from megadetector.taxonomy_mapping.species_lookup import \
    initialize_taxonomy_lookup, get_preferred_taxonomic_match

initialize_taxonomy_lookup()


#%% Check for mappings that disagree with the taxonomy string

# For example, cases where the "level" column says "species", but the taxonomy string says it's a genus.

df = pd.read_csv(lila_taxonomy_file)

n_taxonomy_changes = 0

# Look for internal inconsistency
for i_row,row in df.iterrows():

    sn = row['scientific_name']
    if not isinstance(sn,str):
        continue

    ts = row['taxonomy_string']
    assert sn == taxonomy_string_to_scientific(ts)

    assert row['taxonomy_level'] == taxonomy_string_to_level(ts)

# Look for outdated mappings
taxonomy_preference = 'inat'

# i_row = 0; row = df.iloc[i_row]
for i_row,row in tqdm(df.iterrows(),total=len(df)):

    try:

        sn = row['scientific_name']
        if not isinstance(sn,str):
            continue

        m = get_preferred_taxonomic_match(sn,taxonomy_preference)
        assert m.scientific_name == sn

        ts = row['taxonomy_string']
        assert m.taxonomy_string[0:50] == ts[0:50], 'Mismatch for {}:\n\n{}\n\n{}\n'.format(
            row['dataset_name'],ts,m.taxonomy_string)

        if ts != m.taxonomy_string:
            n_taxonomy_changes += 1
            df.loc[i_row,'taxonomy_string'] = m.taxonomy_string

    except Exception as e:

        print('Error at row {}: {}'.format(i_row,str(e)))
        raise

# ...for each row

print('\nMade {} taxonomy changes'.format(n_taxonomy_changes))

# Optionally re-write
if False:
    df.to_csv(lila_taxonomy_file,header=True,index=False)


#%% List null mappings

# These should all be things like "empty", "unidentified", "fire", "car", etc.

# i_row = 0; row = df.iloc[i_row]
for i_row,row in df.iterrows():
    if (not isinstance(row['taxonomy_string'],str)) or (len(row['taxonomy_string']) == 0):
        print('No mapping for {}:{}'.format(row['dataset_name'],row['query']))


#%% List mappings with scientific names but no common names

for i_row,row in df.iterrows():
    cn = row['common_name']
    sn = row['scientific_name']
    ts = row['taxonomy_string']
    if (isinstance(ts,str)) and (len(ts) >= 0):
        if (not isinstance(cn,str)) or (len(cn) == 0):
            print('No mapping for {}:{}:{}'.format(row['dataset_name'],row['query'],row['scientific_name']))


#%% List mappings that map to different things in different data sets

import numpy as np
def isnan(x):
    if not isinstance(x,float):
        return False
    return np.isnan(x)

from collections import defaultdict
query_to_rows = defaultdict(list)

queries_with_multiple_mappings = set()

n_suppressed = 0

suppress_multiple_matches = [
    ['porcupine','Snapshot Camdeboo','Idaho Camera Traps'],
    ['porcupine','Snapshot Enonkishu','Idaho Camera Traps'],
    ['porcupine','Snapshot Karoo','Idaho Camera Traps'],
    ['porcupine','Snapshot Kgalagadi','Idaho Camera Traps'],
    ['porcupine','Snapshot Kruger','Idaho Camera Traps'],
    ['porcupine','Snapshot Mountain Zebra','Idaho Camera Traps'],
    ['porcupine','Snapshot Serengeti','Idaho Camera Traps'],

    ['porcupine','Snapshot Serengeti','Snapshot Mountain Zebra'],
    ['porcupine','Snapshot Serengeti','Snapshot Kruger'],
    ['porcupine','Snapshot Serengeti','Snapshot Kgalagadi'],
    ['porcupine','Snapshot Serengeti','Snapshot Karoo'],
    ['porcupine','Snapshot Serengeti','Snapshot Camdeboo'],

    ['porcupine','Snapshot Enonkishu','Snapshot Camdeboo'],
    ['porcupine','Snapshot Enonkishu','Snapshot Mountain Zebra'],
    ['porcupine','Snapshot Enonkishu','Snapshot Kruger'],
    ['porcupine','Snapshot Enonkishu','Snapshot Kgalagadi'],
    ['porcupine','Snapshot Enonkishu','Snapshot Karoo'],

    ['kudu','Snapshot Serengeti','Snapshot Mountain Zebra'],
    ['kudu','Snapshot Serengeti','Snapshot Kruger'],
    ['kudu','Snapshot Serengeti','Snapshot Kgalagadi'],
    ['kudu','Snapshot Serengeti','Snapshot Karoo'],
    ['kudu','Snapshot Serengeti','Snapshot Camdeboo'],

    ['fox','Caltech Camera Traps','Channel Islands Camera Traps'],
    ['fox','Idaho Camera Traps','Channel Islands Camera Traps'],
    ['fox','Idaho Camera Traps','Caltech Camera Traps'],

    ['pangolin','Snapshot Serengeti','SWG Camera Traps'],

    ['deer', 'Wellington Camera Traps', 'Idaho Camera Traps'],
    ['deer', 'Wellington Camera Traps', 'Caltech Camera Traps'],

    ['unknown cervid', 'WCS Camera Traps', 'Idaho Camera Traps']

]

for i_row,row in df.iterrows():

    query = row['query']
    taxonomy_string = row['taxonomy_string']

    for previous_i_row in query_to_rows[query]:

        previous_row = df.iloc[previous_i_row]
        assert previous_row['query'] == query
        query_match = False
        if isnan(row['taxonomy_string']):
            query_match = isnan(previous_row['taxonomy_string'])
        elif isnan(previous_row['taxonomy_string']):
            query_match = isnan(row['taxonomy_string'])
        else:
            query_match = previous_row['taxonomy_string'][0:10] == taxonomy_string[0:10]

        if not query_match:

            suppress = False

            # x = suppress_multiple_matches[-1]
            for x in suppress_multiple_matches:
                if x[0] == query and \
                    ( \
                    (x[1] == row['dataset_name'] and x[2] == previous_row['dataset_name']) \
                    or \
                    (x[2] == row['dataset_name'] and x[1] == previous_row['dataset_name']) \
                    ):
                    suppress = True
                    n_suppressed += 1
                    break

            if not suppress:
                print('Query {} in {} and {}:\n\n{}\n\n{}\n'.format(
                    query, row['dataset_name'], previous_row['dataset_name'],
                    taxonomy_string, previous_row['taxonomy_string']))

            queries_with_multiple_mappings.add(query)

    # ...for each row where we saw this query

    query_to_rows[query].append(i_row)

# ...for each row

print('Found {} queries with multiple mappings ({} occurrences suppressed)'.format(
    len(queries_with_multiple_mappings),n_suppressed))


#%% Verify that nothing "unidentified" maps to a species or subspecies

# E.g., "unidentified skunk" should never map to a specific species of skunk

allowable_unknown_species = [
    'unknown_tayra' # AFAIK this is a unique species, I'm not sure what's implied here
]

unk_queries = ['skunk']
for i_row,row in df.iterrows():

    query = row['query']
    level = row['taxonomy_level']

    if not isinstance(level,str):
        assert not isinstance(row['taxonomy_string'],str)
        continue

    if ( \
        'unidentified' in query or \
        ('unk' in query and ('skunk' not in query and 'chipmunk' not in query))\
        ) \
        and \
        ('species' in level):

        if query not in allowable_unknown_species:

            print('Warning: query {}:{} maps to {} {}'.format(
                row['dataset_name'],
                row['query'],
                row['taxonomy_level'],
                row['scientific_name']
                ))


#%% Make sure there are valid source and level values for everything with a mapping

for i_row,row in df.iterrows():
    if isinstance(row['scientific_name'],str):
        if 'source' in row:
            assert isinstance(row['source'],str)
        assert isinstance(row['taxonomy_level'],str)


#%% Find WCS mappings that aren't species or aren't the same as the input

# WCS used scientific names, so these remappings are slightly more controversial
# then the standard remappings.

# row = df.iloc[-500]
for i_row,row in df.iterrows():

    if not isinstance(row['scientific_name'],str):
        continue
    if 'WCS' not in row['dataset_name']:
        continue

    query = row['query']
    scientific_name = row['scientific_name']
    common_name = row['common_name']
    level = row['taxonomy_level']
    taxonomy_string = row['taxonomy_string']

    common_name_from_taxonomy = taxonomy_string_to_common_name(taxonomy_string)
    query_string = query.replace(' sp','')
    query_string = query_string.replace('unknown ','')

    # Anything marked "species" or "unknown" by definition doesn't map to a species,
    # so ignore these.
    if (' sp' not in query) and ('unknown' not in query) and \
        (level != 'species') and (level != 'subspecies'):
        print('WCS query {} ({}) remapped to {} {} ({})'.format(
            query,common_name,level,scientific_name,common_name_from_taxonomy))

    if query_string != scientific_name:
        pass
        # print('WCS query {} ({}) remapped to {} ({})'.format(
        #     query,common_name,scientific_name,common_names_from_taxonomy))


#%% Download sample images for all scientific names

# You might have to do this:
#
# pip install python-magic
# pip install python-magic-bin

# Takes ~1 minute per 10 rows

remapped_queries = {'papio':'papio+baboon',
                    'damaliscus lunatus jimela':'damaliscus lunatus',
                    'mazama':'genus+mazama',
                    'mirafra':'genus+mirafra'}

import os
from megadetector.taxonomy_mapping import retrieve_sample_image

scientific_name_to_paths = {}
image_base = os.path.join(preview_base,'images')
images_per_query = 15
min_valid_images_per_query = 3
min_valid_image_size = 3000

# TODO: parallelize this loop
#
# i_row = 0; row = df.iloc[i_row]
for i_row,row in df.iterrows():

    s = row['scientific_name']

    if (not isinstance(s,str)) or (len(s)==0):
        continue

    query = s.replace(' ','+')

    if query in remapped_queries:
        query = remapped_queries[query]

    query_folder = os.path.join(image_base,query)
    os.makedirs(query_folder,exist_ok=True)

    # Check whether we already have enough images for this query
    image_files = os.listdir(query_folder)
    image_fullpaths = [os.path.join(query_folder,fn) for fn in image_files]
    sizes = [os.path.getsize(p) for p in image_fullpaths]
    sizes_above_threshold = [x for x in sizes if x > min_valid_image_size]
    if len(sizes_above_threshold) > min_valid_images_per_query:
        print('Skipping query {}, already have {} images'.format(s,len(sizes_above_threshold)))
        continue

    # Check whether we've already run this query for a previous row
    if query in scientific_name_to_paths:
        continue

    print('Processing query {} of {} ({})'.format(i_row,len(df),query))
    paths = retrieve_sample_image.download_images(query=query,
                                             output_directory=image_base,
                                             limit=images_per_query,
                                             verbose=True)
    print('Downloaded {} images for {}'.format(len(paths),query))
    scientific_name_to_paths[query] = paths

# ...for each row in the mapping table


#%% Rename .jpeg to .jpg

from megadetector.utils import path_utils
all_images = path_utils.recursive_file_list(image_base,False)

for fn in tqdm(all_images):
    if fn.lower().endswith('.jpeg'):
        new_fn = fn[0:-5] + '.jpg'
        os.rename(fn, new_fn)


#%% Choose representative images for each scientific name

# Specifically, sort by size, and take the largest unique sizes. Very small files tend
# to be bogus thumbnails, etc.

max_images_per_query = 4
scientific_name_to_preferred_images = {}

# s = list(scientific_name_to_paths.keys())[0]
for s in list(df.scientific_name):

    if not isinstance(s,str):
        continue

    query = s.replace(' ','+')

    if query in remapped_queries:
        query = remapped_queries[query]

    query_folder = os.path.join(image_base,query)
    assert os.path.isdir(query_folder)
    image_files = os.listdir(query_folder)
    image_fullpaths = [os.path.join(query_folder,fn) for fn in image_files]
    sizes = [os.path.getsize(p) for p in image_fullpaths]
    path_to_size = {}
    for i_fp,fp in enumerate(image_fullpaths):
        path_to_size[fp] = sizes[i_fp]
    paths_by_size = [x for _, x in sorted(zip(sizes, image_fullpaths),reverse=True)]

    # Be suspicious of duplicate sizes
    b_duplicate_sizes = [False] * len(paths_by_size)

    for i_path,p in enumerate(paths_by_size):
        if i_path == len(paths_by_size) - 1:
            continue
        if path_to_size[p] == path_to_size[paths_by_size[i_path+1]]:
            b_duplicate_sizes[i_path] = True

    paths_by_size_non_dup = [i for (i, v) in zip(paths_by_size, b_duplicate_sizes) if not v]

    preferred_paths = paths_by_size_non_dup[:max_images_per_query]
    scientific_name_to_preferred_images[s] = preferred_paths

# ...for each scientific name


#%% Delete unused images

used_images = []
for images in scientific_name_to_preferred_images.values():
    used_images.extend(images)

print('Using a total of {} images'.format(len(used_images)))
used_images_set = set(used_images)

from megadetector.utils import path_utils
all_images = path_utils.recursive_file_list(image_base,False)

unused_images = []
for fn in all_images:
    if fn not in used_images_set:
        unused_images.append(fn)

print('{} of {} files unused (diff {})'.format(len(unused_images),len(all_images),
                                               len(all_images) - len(unused_images)))

for fn in tqdm(unused_images):
    os.remove(fn)


#%% Produce HTML preview

with open(html_output_file, 'w', encoding='utf-8') as f:

    f.write('<html><head></head><body>\n')

    names = scientific_name_to_preferred_images.keys()
    names = sorted(names)

    f.write('<p class="speciesinfo_p" style="font-weight:bold;font-size:130%">'
            'dataset_name: <b><u>category</u></b> mapped to taxonomy_level scientific_name (taxonomic_common_name) (manual_common_name)</p>\n'
            '</p>')

    # i_row = 2; row = df.iloc[i_row]
    for i_row, row in tqdm(df.iterrows(), total=len(df)):

        s = row['scientific_name']

        taxonomy_string = row['taxonomy_string']
        if isinstance(taxonomy_string,str):
            taxonomic_match = eval(taxonomy_string)
            matched_entity = taxonomic_match[0]
            assert len(matched_entity) == 4
            common_names = matched_entity[3]
            if len(common_names) == 1:
                common_name_string = common_names[0]
            else:
                common_name_string = str(common_names)
        else:
            common_name_string = ''

        f.write('<p class="speciesinfo_p" style="font-weight:bold;font-size:130%">')

        if isinstance(row.scientific_name,str):
            output_string = '{}: <b><u>{}</u></b> mapped to {} {} ({}) ({})</p>\n'.format(
                row.dataset_name, row.query,
                row.taxonomy_level, row.scientific_name, common_name_string,
                row.common_name)
            f.write(output_string)
        else:
            f.write('{}: <b><u>{}</u></b> unmapped'.format(row.dataset_name,row.query))

        if s is None or s not in names:
            f.write('<p class="content_p">no images available</p>')
        else:
            image_paths = scientific_name_to_preferred_images[s]
            basedir = os.path.dirname(html_output_file)
            relative_paths = [os.path.relpath(p,basedir) for p in image_paths]
            image_paths = [s.replace('\\','/') for s in relative_paths]
            n_images = len(image_paths)
            # image_paths = [os.path.relpath(p, output_base) for p in image_paths]
            image_width_percent = round(100 / n_images)
            f.write('<table class="image_table"><tr>\n')
            for image_path in image_paths:
                f.write('<td style="vertical-align:top;" width="{}%">'
                        '<img src="{}" style="display:block; width:100%; vertical-align:top; height:auto;">'
                        '</td>\n'.format(image_width_percent, image_path))
            f.write('</tr></table>\n')

    # ...for each row

    f.write('</body></html>\n')


#%% Open HTML preview

from megadetector.utils.path_utils import open_file
open_file(html_output_file)
