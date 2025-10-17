"""

create_lila_test_set.py

Create a test set of camera trap images, containing N empty and N non-empty
images from each LILA data set.

"""

#%% Constants and imports

import json
import os
import random

from megadetector.data_management.lila.lila_common import \
    read_lila_metadata, read_metadata_file_for_dataset
from megadetector.utils.url_utils import parallel_download_urls
from megadetector.utils.path_utils import open_file

n_empty_images_per_dataset = 1
n_non_empty_images_per_dataset = 1

# We'll write images, metadata downloads, and temporary files here
lila_local_base = os.path.expanduser('~/lila')

output_dir = os.path.join(lila_local_base,'lila_test_set')
os.makedirs(output_dir,exist_ok=True)

metadata_dir = os.path.join(lila_local_base,'metadata')
os.makedirs(metadata_dir,exist_ok=True)

random.seed(0)


#%% Download and parse the metadata file

metadata_table = read_lila_metadata(metadata_dir)


#%% Download and extract metadata for every dataset

for ds_name in metadata_table.keys():
    metadata_table[ds_name]['metadata_filename'] = \
        read_metadata_file_for_dataset(ds_name=ds_name,
                                       metadata_dir=metadata_dir,
                                       metadata_table=metadata_table)


#%% Choose images from each dataset

# Takes ~60 seconds

empty_category_names = ['empty','blank']

# ds_name = (list(metadata_table.keys()))[0]
for ds_name in metadata_table.keys():

    print('Choosing images for {}'.format(ds_name))

    json_filename = metadata_table[ds_name]['metadata_filename']

    with open(json_filename,'r') as f:
        d = json.load(f)

    category_id_to_name = {c['id']:c['name'] for c in d['categories']}
    category_name_to_id = {c['name']:c['id'] for c in d['categories']}

    ## Find empty images

    empty_category_present = False
    for category_name in category_name_to_id:
        if category_name in empty_category_names:
            empty_category_present = True
            break
    if not empty_category_present:
        empty_annotations_to_download = []
    else:
        empty_category_id = None
        for category_name in empty_category_names:
            if category_name in category_name_to_id:
                if empty_category_id is not None:
                    print('Warning: multiple empty categories in dataset {}'.format(ds_name))
                else:
                    empty_category_id = category_name_to_id[category_name]
        assert empty_category_id is not None
        empty_annotations = [ann for ann in d['annotations'] if ann['category_id'] == empty_category_id]
        try:
            empty_annotations_to_download = random.sample(empty_annotations,n_empty_images_per_dataset)
        except ValueError:
            print('No empty images available for dataset {}'.format(ds_name))
            empty_annotations_to_download = []

    ## Find non-empty images

    non_empty_annotations = [ann for ann in d['annotations'] if ann['category_id'] != empty_category_id]
    try:
        non_empty_annotations_to_download = random.sample(non_empty_annotations,n_non_empty_images_per_dataset)
    except ValueError:
        print('No non-empty images available for dataset {}'.format(ds_name))
        non_empty_annotations_to_download = []


    annotations_to_download = empty_annotations_to_download + non_empty_annotations_to_download

    image_ids_to_download = set([ann['image_id'] for ann in annotations_to_download])
    assert len(image_ids_to_download) == len(set(image_ids_to_download))

    images_to_download = []
    for im in d['images']:
        if im['id'] in image_ids_to_download:
            images_to_download.append(im)
    assert len(images_to_download) == len(image_ids_to_download)

    metadata_table[ds_name]['images_to_download'] = images_to_download

# ...for each dataset


#%% Convert to URLs

preferred_cloud = 'gcp'

# ds_name = (list(metadata_table.keys()))[0]
for ds_name in metadata_table.keys():

    base_url = metadata_table[ds_name]['image_base_url_' + preferred_cloud]
    assert not base_url.endswith('/')

    # Retrieve image file names
    filenames = [im['file_name'] for im in metadata_table[ds_name]['images_to_download']]

    urls_to_download = []

    # Convert to URLs
    for fn in filenames:
        url = base_url + '/' + fn
        urls_to_download.append(url)

    metadata_table[ds_name]['urls_to_download'] = urls_to_download

# ...for each dataset


#%% Download image files (prep)

url_to_target_file = {}

# ds_name = (list(metadata_table.keys()))[0]
for ds_name in metadata_table.keys():

    base_url = metadata_table[ds_name]['image_base_url_' + preferred_cloud]
    assert not base_url.endswith('/')
    base_url += '/'

    urls_to_download = metadata_table[ds_name]['urls_to_download']

    # url = urls_to_download[0]
    for url in urls_to_download:

        assert base_url in url
        output_file_relative = ds_name.lower().replace(' ','_') + \
            '_' + url.replace(base_url,'').replace('/','_').replace('\\','_')
        output_file_absolute = os.path.join(output_dir,output_file_relative)
        url_to_target_file[url] = output_file_absolute

    # ...for each url

# ...for each dataset


#%% Download image files (execution)

download_results = parallel_download_urls(url_to_target_file,
                                          verbose=False,
                                          overwrite=False,
                                          n_workers=20,
                                          pool_type='thread')

# r = download_results[0]
for r in download_results:
   assert r['status'] in ('skipped','success')


#%% Open the test test

open_file(output_dir)
