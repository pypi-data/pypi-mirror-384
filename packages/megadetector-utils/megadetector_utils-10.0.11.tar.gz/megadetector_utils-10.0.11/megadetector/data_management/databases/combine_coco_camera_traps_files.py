"""

combine_coco_camera_traps_files.py

Merges two or more .json files in COCO Camera Traps format, optionally
writing the results to another .json file.

- Concatenates image lists, erroring if images are not unique.
- Errors on unrecognized fields.
- Checks compatibility in info structs, within reason.

*Example command-line invocation*

combine_coco_camera_traps_files input1.json input2.json ... inputN.json output.json

"""

#%% Constants and imports

import argparse
import json
import sys
from megadetector.utils import ct_utils


#%% Merge functions

def combine_cct_files(input_files,
                      output_file=None,
                      require_uniqueness=True,
                      filename_prefixes=None):
    """
    Merges the list of COCO Camera Traps files [input_files] into a single
    dictionary, optionally writing the result to [output_file].

    Args:
        input_files (list): paths to CCT .json files
        output_file (str, optional): path to write merged .json file
        require_uniqueness (bool, optional): whether to require that the images in
            each input_dict be unique
        filename_prefixes (dict, optional): dict mapping input filenames to strings
            that should be prepended to image filenames from that source

    Returns:
        dict: the merged COCO-formatted .json dict
    """

    input_dicts = []
    print('Loading input files')
    for fn in input_files:
        with open(fn, 'r', encoding='utf-8') as f:
            d = json.load(f)
            if filename_prefixes is not None:
                assert fn in filename_prefixes
                d['filename_prefix'] = filename_prefixes[fn]
            input_dicts.append(d)

    print('Merging results')
    merged_dict = combine_cct_dictionaries(
        input_dicts, require_uniqueness=require_uniqueness)

    print('Writing output')
    if output_file is not None:
        ct_utils.write_json(output_file, merged_dict)

    return merged_dict


def combine_cct_dictionaries(input_dicts, require_uniqueness=True):
    """
    Merges the list of COCO Camera Traps dictionaries [input_dicts].  See module header
    comment for details on merge rules.

    Args:
        input_dicts (list of dict): list of CCT dicts
        require_uniqueness (bool, optional): whether to require that the images in
            each input_dict be unique

    Returns:
        dict: the merged COCO-formatted .json dict
    """

    filename_to_image = {}
    all_annotations = []
    info = None

    category_name_to_id = {}
    category_name_to_id['empty'] = 0
    next_category_id = 1

    known_fields = ['info', 'categories', 'annotations','images','filename_prefix']

    # i_input_dict = 0; input_dict = input_dicts[i_input_dict]
    for i_input_dict,input_dict in enumerate(input_dicts):

        filename_prefix = ''
        if ('filename_prefix' in input_dict.keys()):
            filename_prefix = input_dict['filename_prefix']

        for k in input_dict.keys():
            if k not in known_fields:
                raise ValueError(f'Unrecognized CCT field: {k}')

        # We will prepend an index to every ID to guarantee uniqueness
        index_string = 'ds' + str(i_input_dict).zfill(3) + '_'

        old_cat_id_to_new_cat_id = {}

        # Map detection categories from the original data set into the merged data set
        for original_category in input_dict['categories']:

            original_cat_id = original_category['id']
            cat_name = original_category['name']
            if cat_name in category_name_to_id:
                new_cat_id = category_name_to_id[cat_name]
            else:
                new_cat_id = next_category_id
                next_category_id += 1
                category_name_to_id[cat_name] = new_cat_id

            if original_cat_id in old_cat_id_to_new_cat_id:
                assert old_cat_id_to_new_cat_id[original_cat_id] == new_cat_id
            else:
                old_cat_id_to_new_cat_id[original_cat_id] = new_cat_id

        # ...for each category


        # Merge original image list into the merged data set
        for im in input_dict['images']:

            if 'seq_id' in im:
                im['seq_id'] = index_string + str(im['seq_id'])
            if 'location' in im:
                im['location'] = index_string + im['location']

            im_file = filename_prefix + im['file_name']
            im['file_name'] = im_file
            if require_uniqueness:
                assert im_file not in filename_to_image, f'Duplicate image: {im_file}'
            else:
                if im_file in filename_to_image:
                    print('Redundant image {}'.format(im_file))

            # Create a unique ID
            im['id'] = index_string + str(im['id'])
            filename_to_image[im_file] = im

        # ...for each image


        # Same for annotations
        for ann in input_dict['annotations']:

            ann['image_id'] = index_string + str(ann['image_id'])
            ann['id'] = index_string + str(ann['id'])
            assert ann['category_id'] in old_cat_id_to_new_cat_id
            ann['category_id'] = old_cat_id_to_new_cat_id[ann['category_id']]

        # ...for each annotation

        all_annotations.extend(input_dict['annotations'])

        # Merge info dicts, don't check completion time fields
        if info is None:
            import copy
            info = copy.deepcopy(input_dict['info'])
            info['original_info'] = [input_dict['info']]
        else:
            info['original_info'].append(input_dict['info'])

    # ...for each dictionary

    # Convert merged image dictionaries to a sorted list
    sorted_images = sorted(filename_to_image.values(), key=lambda im: im['file_name'])

    all_categories = [{'id':category_name_to_id[cat_name],'name':cat_name} for\
                      cat_name in category_name_to_id.keys()]

    merged_dict = {'info': info,
                   'categories': all_categories,
                   'images': sorted_images,
                   'annotations': all_annotations}

    return merged_dict

# ...combine_cct_dictionaries(...)


#%% Command-line driver

def main(): # noqa

    parser = argparse.ArgumentParser()
    parser.add_argument(
        'input_paths', nargs='+',
        help='List of input .json files')
    parser.add_argument(
        'output_path',
        help='Output .json file')

    if len(sys.argv[1:]) == 0:
        parser.print_help()
        parser.exit()

    args = parser.parse_args()
    combine_cct_files(args.input_paths, args.output_path)

if __name__ == '__main__':
    main()
