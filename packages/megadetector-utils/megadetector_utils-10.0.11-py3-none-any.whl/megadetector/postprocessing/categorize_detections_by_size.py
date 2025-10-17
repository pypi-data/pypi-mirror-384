"""

categorize_detections_by_size.py

Given a MegaDetector .json file, creates a separate category for bounding boxes
above one or more size thresholds.

"""

#%% Constants and imports

import json

from collections import defaultdict
from tqdm import tqdm

from megadetector.utils.ct_utils import write_json


#%% Support classes

class SizeCategorizationOptions:
    """
    Options used to parameterize categorize_detections_by_size().
    """

    def __init__(self):

        #: Thresholds to use for separation, as a fraction of the image size.
        #:
        #: Should be sorted from smallest to largest.
        self.size_thresholds = [0.95]

        #: List of category numbers to use in separation; uses all categories if None
        self.categories_to_separate = None

        #: Dimension to use for thresholding; can be "size", "width", or "height"
        self.measurement = 'size'

        #: Categories to assign to thresholded ranges; should have the same length as
        #: "size_thresholds".
        self.size_category_names = ['large_detection']


#%% Main functions

def categorize_detections_by_size(input_file,output_file=None,options=None):
    """
    Given a MegaDetector .json file, creates a separate category for bounding boxes
    above one or more size thresholds, optionally writing results to [output_file].

    Args:
        input_file (str): file to process
        output_file (str, optional): optional output file
        options (SizeCategorizationOptions, optional): categorization parameters

    Returns:
        dict: data loaded from [input_file], with the new size-based categories.
        Identical to what's written to [output_file], if [output_file] is not None.
    """
    if options is None:
        options = SizeCategorizationOptions()

    if options.categories_to_separate is not None:
        options.categories_to_separate = \
            [str(c) for c in options.categories_to_separate]

    assert len(options.size_thresholds) == len(options.size_category_names), \
        'Options struct should have the same number of category names and size thresholds'

    # Sort size thresholds and names from largest to smallest
    options.size_category_names = [x for _,x in sorted(zip(options.size_thresholds, # noqa
                                                             options.size_category_names),reverse=True)]
    options.size_thresholds = sorted(options.size_thresholds,reverse=True)

    with open(input_file) as f:
        data = json.load(f)

    detection_categories = data['detection_categories']
    category_keys = list(detection_categories.keys())
    category_keys = [int(k) for k in category_keys]
    max_key = max(category_keys)

    threshold_to_category_id = {}
    for i_threshold,threshold in enumerate(options.size_thresholds):

        category_id = str(max_key+1)
        max_key += 1
        detection_categories[category_id] = options.size_category_names[i_threshold]
        threshold_to_category_id[i_threshold] = category_id

        print('Creating category for {} with ID {}'.format(
            options.size_category_names[i_threshold],category_id))

    images = data['images']

    print('Loaded {} images'.format(len(images)))

    # For each image...
    #
    # im = images[0]

    category_id_to_count = defaultdict(int)

    for im in tqdm(images):

        if im['detections'] is None:
            assert im['failure'] is not None and len(im['failure']) > 0
            continue

        # d = im['detections'][0]
        for d in im['detections']:

            # Are there really any detections here?
            if (d is None) or ('bbox' not in d) or (d['bbox'] is None):
                continue

            # Is this a category we're supposed to process?
            if (options.categories_to_separate is not None) and \
               (d['category'] not in options.categories_to_separate):
                continue

            # https://github.com/agentmorris/MegaDetector/tree/main/megadetector/api/batch_processing#detector-outputs
            w = d['bbox'][2]
            h = d['bbox'][3]
            detection_size = w*h

            metric = None

            if options.measurement == 'size':
                metric = detection_size
            elif options.measurement == 'width':
                metric = w
            else:
                assert options.measurement == 'height', 'Unrecognized measurement metric'
                metric = h
            assert metric is not None

            for i_threshold,threshold in enumerate(options.size_thresholds):

                if metric >= threshold:

                    category_id = threshold_to_category_id[i_threshold]

                    category_id_to_count[category_id] += 1
                    d['category'] = category_id

                    break

            # ...for each threshold
        # ...for each detection

    # ...for each image

    for i_threshold in range(0,len(options.size_thresholds)):
        category_name = options.size_category_names[i_threshold]
        category_id = threshold_to_category_id[i_threshold]
        category_count = category_id_to_count[category_id]
        print('Found {} detections in category {}'.format(category_count,category_name))

    if output_file is not None:
        write_json(output_file,data)

    return data

# ...def categorize_detections_by_size()
