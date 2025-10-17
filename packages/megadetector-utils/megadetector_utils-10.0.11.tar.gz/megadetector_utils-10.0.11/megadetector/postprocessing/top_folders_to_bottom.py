"""

top_folders_to_bottom.py

Given a base folder with files like:

* A/1/2/a.jpg
* B/3/4/b.jpg

...moves the top-level folders to the bottom in a new output folder, i.e., creates:

* 1/2/A/a.jpg
* 3/4/B/b.jpg

In practice, this is used to make this:

animal/camera01/image01.jpg

...look like:

camera01/animal/image01.jpg

"""

#%% Constants and imports

import os
import sys
import shutil
import argparse

from pathlib import Path
from tqdm import tqdm

from functools import partial
from multiprocessing.pool import ThreadPool

from megadetector.utils.path_utils import path_is_abs


#%% Classes

class TopFoldersToBottomOptions:
    """
    Options used to parameterize top_folders_to_bottom()
    """

    def __init__(self,
                 input_folder,
                 output_folder,
                 copy=True,
                 n_threads=1,
                 overwrite=False):

        #: Whether to copy (True) vs. move (False) false when re-organizing
        self.copy = copy

        #: Number of worker threads to use, or <1 to disable parallelization
        self.n_threads = n_threads

        #: Input folder
        self.input_folder = input_folder

        #: Output folder
        self.output_folder = output_folder

        #: If this is False and an output file exists, throw an error
        self.overwrite = overwrite


#%% Main functions

def _process_file(relative_filename,options,execute=True):

    assert ('/' in relative_filename) and \
        ('\\' not in relative_filename) and \
        (not path_is_abs(relative_filename))

    # Find top-level folder
    tokens = relative_filename.split('/')
    topmost_folder = tokens.pop(0)
    tokens.insert(len(tokens)-1,topmost_folder)

    # Find file/folder names
    output_relative_path = '/'.join(tokens)
    output_relative_folder = '/'.join(tokens[0:-1])

    output_absolute_folder = os.path.join(options.output_folder,output_relative_folder)
    output_absolute_path = os.path.join(options.output_folder,output_relative_path)

    if execute:

        os.makedirs(output_absolute_folder,exist_ok=True)

        input_absolute_path = os.path.join(options.input_folder,relative_filename)

        if not options.overwrite:
            assert not os.path.isfile(output_absolute_path), \
                'Error: output file {} exists'.format(output_absolute_path)

        # Move or copy
        if options.copy:
            shutil.copy(input_absolute_path, output_absolute_path)
        else:
            shutil.move(input_absolute_path, output_absolute_path)

    return output_absolute_path

# ...def _process_file()


def top_folders_to_bottom(options):
    """
    top_folders_to_bottom.py

    Given a base folder with files like:

    * A/1/2/a.jpg
    * B/3/4/b.jpg

    ...moves the top-level folders to the bottom in a new output folder, i.e., creates:

    * 1/2/A/a.jpg
    * 3/4/B/b.jpg

    In practice, this is used to make this:

    animal/camera01/image01.jpg

    ...look like:

    camera01/animal/image01.jpg

    Args:
        options (TopFoldersToBottomOptions): See TopFoldersToBottomOptions for parameter details.

    """

    os.makedirs(options.output_folder,exist_ok=True)

    # Enumerate input folder
    print('Enumerating files...')
    files = list(Path(options.input_folder).rglob('*'))
    files = [p for p in files if not p.is_dir()]
    files = [str(s) for s in files]
    print('Enumerated {} files'.format(len(files)))

    # Convert absolute paths to relative paths
    relative_files = [os.path.relpath(s,options.input_folder) for s in files]

    # Standardize delimiters
    relative_files = [s.replace('\\','/') for s in relative_files]

    base_files = [s for s in relative_files if '/' not in s]
    if len(base_files) > 0:
        print('Warning: ignoring {} files in the base folder'.format(len(base_files)))
        relative_files = [s for s in relative_files if '/' in s]

    # Make sure each input file maps to a unique output file
    absolute_output_files = [_process_file(s, options, execute=False) for s in relative_files]
    assert len(absolute_output_files) == len(set(absolute_output_files)),\
        "Error: input filenames don't map to unique output filenames"

    # relative_filename = relative_files[0]

    # Loop
    if options.n_threads <= 1:

        for relative_filename in tqdm(relative_files):
            _process_file(relative_filename,options)

    else:

        print('Starting a pool with {} threads'.format(options.n_threads))
        pool = ThreadPool(options.n_threads)
        try:
            process_file_with_options = partial(_process_file, options=options)
            _ = list(tqdm(pool.imap(process_file_with_options, relative_files), total=len(relative_files)))
        finally:
            pool.close()
            pool.join()
            print('Pool closed and join for folder inversion')

# ...def top_folders_to_bottom(...)


#%% Interactive driver

if False:

    pass

    #%%

    input_folder = r"G:\temp\output"
    output_folder = r"G:\temp\output-inverted"
    options = TopFoldersToBottomOptions(input_folder,output_folder,copy=True,n_threads=10)

    #%%

    top_folders_to_bottom(options)


#%% Command-line driver

# python top_folders_to_bottom.py "g:\temp\separated_images" "g:\temp\separated_images_inverted" --n_threads 10

def main(): # noqa

    parser = argparse.ArgumentParser()
    parser.add_argument('input_folder', type=str, help='Input image folder')
    parser.add_argument('output_folder', type=str, help='Output image folder')

    parser.add_argument('--copy', action='store_true',
                        help='Copy images, instead of moving (moving is the default)')
    parser.add_argument('--overwrite', action='store_true',
                        help='Allow image overwrite (default=False)')
    parser.add_argument('--n_threads', type=int, default=1,
                        help='Number of threads to use for parallel operation (default=1)')

    if len(sys.argv[1:])==0:
        parser.print_help()
        parser.exit()

    args = parser.parse_args()

    # Convert to an options object
    options = TopFoldersToBottomOptions(
        args.input_folder,
        args.output_folder,
        copy=args.copy,
        n_threads=args.n_threads,
        overwrite=args.overwrite)

    top_folders_to_bottom(options)

if __name__ == '__main__':
    main()
