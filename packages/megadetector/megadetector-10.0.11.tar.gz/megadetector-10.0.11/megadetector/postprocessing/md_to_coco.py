"""

md_to_coco.py

"Converts" MegaDetector output files to COCO format.  "Converts" is in quotes because
this is an opinionated transformation that requires a confidence threshold for most
applications.

Does not currently handle classification information.

"""

#%% Constants and imports

import os
import json
import uuid
import sys
import argparse

from tqdm import tqdm

from megadetector.visualization import visualization_utils as vis_utils
from megadetector.utils.path_utils import insert_before_extension
from megadetector.utils.ct_utils import write_json

default_confidence_threshold = 0.15


#%% Functions

def md_to_coco(md_results_file,
               coco_output_file=None,
               image_folder=None,
               confidence_threshold=default_confidence_threshold,
               validate_image_sizes=False,
               info=None,
               preserve_nonstandard_metadata=True,
               include_failed_images=True,
               include_annotations_without_bounding_boxes=True,
               empty_category_id='0',
               overwrite_behavior='skip',
               verbose=True,
               image_filename_to_size=None,
               unrecognized_category_handling='error'):
    """
    "Converts" MegaDetector output files to COCO format.  "Converts" is in quotes because
    this is an opinionated transformation that typically requires a confidence threshold.

    The default confidence threshold is not 0; the assumption is that by default, you are
    going to treat the resulting COCO file as a set of labels.  If you are using the resulting COCO
    file to *evaluate* a detector, rather than as a set of labels, you likely want a
    confidence threshold of 0.  Confidence values will be written to the semi-standard "score"
    field for each image (regardless of the threshold) if preserve_nonstandard_metadata is True.

    A folder of images is required if width and height information are not available
    in the MD results file.

    Args:
        md_results_file (str): MD results .json file to convert to COCO
            format
        coco_output_file (str, optional): COCO .json file to write; if this is None, we'll return
            a COCO-formatted dict, but won't write it to disk.  If this is 'auto', we'll write to
            [md_results_file_without_extension].coco.json.
        image_folder (str, optional): folder of images, required if 'width' and 'height' are not
            present in the MD results file (they are not required by the format)
        confidence_threshold (float, optional): boxes below this confidence threshold will not be
            included in the output data
        validate_image_sizes (bool, optional): if this is True, we'll check the image sizes
            regardless of whether "width" and "height" are present in the MD results file.
        info (dict, optional): arbitrary metadata to include in an "info" field in the COCO-formatted
            output
        preserve_nonstandard_metadata (bool, optional): if this is True, confidence will be preserved in a
            non-standard "score" field in each annotation, and any random fields present in each image's
            data (e.g. EXIF metadata) will be propagated to COCO output
        include_failed_images (bool, optional): if this is True, failed images will be propagated to COCO output
            with a non-empty "failure" field and no other fields, otherwise failed images will be skipped.
        include_annotations_without_bounding_boxes (bool, optional): the only time we end up with
            annotations without bounding boxes is when a detection has the category [empty_category_id];
            this determines whether those annotations are included in the output.
        empty_category_id (str, optional): category ID reserved for the 'empty' class, should not be
            attached to any bounding boxes
        overwrite_behavior (str, optional): determines behavior if the output file exists ('skip' to skip conversion,
            'overwrite' to overwrite the existing file, 'error' to raise an error, 'skip_if_valid' to skip conversion
            if the .json file appears to be intact (does not verify COCO formatting, just intact-.json-ness))
        verbose (bool, optional): enable debug output, including the progress bar,
        image_filename_to_size (dict, optional): dictionary mapping relative image paths to (w,h) tuples.  Reading
            image sizes is the slowest step, so if you need to convert many results files at once for the same
            set of images, things will be gobs faster if you read the image sizes in advance and pass them in
            via this argument.  The format used here is the same format output by parallel_get_image_sizes().
        unrecognized_category_handling (str or float, optional): specifies what to do when encountering category
            IDs not in the category mapping.  Can be "error", "ignore", or "warning".  Can also be a float,
            in which case an error is thrown if an unrecognized category has a confidence value higher than
            this value.

    Returns:
        dict: the COCO data dict, identical to what's written to [coco_output_file] if [coco_output_file]
        is not None.
    """

    assert isinstance(md_results_file,str)
    assert os.path.isfile(md_results_file), \
        'MD results file {} does not exist'.format(md_results_file)
    assert (isinstance(unrecognized_category_handling,float)) or \
           (unrecognized_category_handling in ('error','warning','ignore')), \
        'Invalid category handling behavior {}'.format(unrecognized_category_handling)

    if coco_output_file == 'auto':
        coco_output_file = insert_before_extension(md_results_file,'coco')

    if coco_output_file is not None:
        if os.path.isfile(coco_output_file):
            if overwrite_behavior == 'skip':
                print('Skipping conversion of {}, output file {} exists'.format(
                    md_results_file,coco_output_file))
                return None
            elif overwrite_behavior == 'skip_if_valid':
                output_file_is_valid = True
                try:
                    with open(coco_output_file,'r') as f:
                        _ = json.load(f)
                except Exception:
                    print('COCO file {} is invalid, proceeding with conversion'.format(
                        coco_output_file))
                    output_file_is_valid = False
                if output_file_is_valid:
                    print('Skipping conversion of {}, output file {} exists and is valid'.format(
                        md_results_file,coco_output_file))
                    return None
            elif overwrite_behavior == 'overwrite':
                pass
            elif overwrite_behavior == 'error':
                raise ValueError('Output file {} exists'.format(coco_output_file))

    with open(md_results_file,'r') as f:
        md_results = json.load(f)

    coco_images = []
    coco_annotations = []

    if verbose:
        print('Converting MD results file {} to COCO file {}...'.format(
            md_results_file, coco_output_file))

    # im = md_results['images'][0]
    for im in tqdm(md_results['images'],disable=(not verbose)):

        coco_im = {}
        coco_im['id'] = im['file']
        coco_im['file_name'] = im['file']

        # There is no concept of this in the COCO standard
        if 'failure' in im and im['failure'] is not None:
            if include_failed_images:
                coco_im['failure'] = im['failure']
                coco_images.append(coco_im)
            continue

        # Read/validate image size
        w = None
        h = None

        if ('width' not in im) or ('height' not in im) or validate_image_sizes:
            if (image_folder is None) and (image_filename_to_size is None):
                raise ValueError('Must provide an image folder or a size mapping when ' + \
                                 'height/width need to be read from images')

            w = None; h = None

            if image_filename_to_size is not None:

                if im['file'] not in image_filename_to_size:
                    print('Warning: file {} not in image size mapping dict, reading from file'.format(
                        im['file']))
                else:
                    image_size = image_filename_to_size[im['file']]
                    if image_size is not None:
                        assert len(image_size) == 2
                        w = image_size[0]
                        h = image_size[1]

            if w is None:

                image_file_abs = os.path.join(image_folder,im['file'])
                pil_im = vis_utils.open_image(image_file_abs)
                w = pil_im.width
                h = pil_im.height

            if validate_image_sizes:
                if 'width' in im:
                    assert im['width'] == w, 'Width mismatch for image {}'.format(im['file'])
                if 'height' in im:
                    assert im['height'] == h, 'Height mismatch for image {}'.format(im['file'])
        else:

            w = im['width']
            h = im['height']

        coco_im['width'] = w
        coco_im['height'] = h

        # Add other, non-standard fields to the output dict
        if preserve_nonstandard_metadata:
            for k in im.keys():
                if k not in ('file','detections','width','height'):
                    coco_im[k] = im[k]

        coco_images.append(coco_im)

        # detection = im['detections'][0]
        for detection in im['detections']:

            # Skip below-threshold detections
            if confidence_threshold is not None and detection['conf'] < confidence_threshold:
                continue

            # Create an annotation
            ann = {}
            ann['id'] = str(uuid.uuid1())
            ann['image_id'] = coco_im['id']

            md_category_id = detection['category']

            if md_category_id not in md_results['detection_categories']:

                s = 'unrecognized category ID {} occurred with confidence {} in file {}'.format(
                        md_category_id,detection['conf'],im['file'])
                if isinstance(unrecognized_category_handling,float):
                    if detection['conf'] > unrecognized_category_handling:
                        raise ValueError(s)
                    else:
                        continue
                elif unrecognized_category_handling == 'warning':
                    print('Warning: {}'.format(s))
                    continue
                elif unrecognized_category_handling == 'ignore':
                    continue
                else:
                    raise ValueError(s)

            coco_category_id = int(md_category_id)
            ann['category_id'] = coco_category_id

            if md_category_id != empty_category_id:

                assert 'bbox' in detection,\
                    'Oops: non-empty category with no bbox in {}'.format(im['file'])

                ann['bbox'] = detection['bbox']

                # MegaDetector: [x,y,width,height] (normalized, origin upper-left)
                # COCO: [x,y,width,height] (absolute, origin upper-left)
                ann['bbox'][0] = ann['bbox'][0] * coco_im['width']
                ann['bbox'][1] = ann['bbox'][1] * coco_im['height']
                ann['bbox'][2] = ann['bbox'][2] * coco_im['width']
                ann['bbox'][3] = ann['bbox'][3] * coco_im['height']

            else:

                # In very esoteric cases, we use the empty category (0) in MD-formatted output files
                print('Warning: empty category ({}) used for annotation for image {}'.format(
                    empty_category_id,im['file']))
                pass

            if preserve_nonstandard_metadata:
                # "Score" is a semi-standard string here, recognized by at least pycocotools
                # ann['conf'] = detection['conf']
                ann['score'] = detection['conf']

            if 'bbox' in ann or include_annotations_without_bounding_boxes:
                coco_annotations.append(ann)

        # ...for each detection

    # ...for each image

    output_dict = {}

    if info is not None:
        output_dict['info'] = info
    else:
        output_dict['info'] = {'description':'Converted from MD results file {}'.format(md_results_file)}
    output_dict['info']['confidence_threshold'] = confidence_threshold

    output_dict['images'] = coco_images
    output_dict['annotations'] = coco_annotations

    output_dict['categories'] = []

    for md_category_id in md_results['detection_categories'].keys():

        coco_category_id = int(md_category_id)
        coco_category = {'id':coco_category_id,
                         'name':md_results['detection_categories'][md_category_id]}
        output_dict['categories'].append(coco_category)

    if verbose:
        print('Writing COCO output file...')

    write_json(coco_output_file,output_dict)

    return output_dict

# ...def md_to_coco(...)


#%% Interactive driver

if False:

    pass

    #%% Configure options

    md_results_file = os.path.expanduser('~/data/md-test.json')
    coco_output_file = os.path.expanduser('~/data/md-test-coco.json')
    image_folder = os.path.expanduser('~/data/md-test')
    validate_image_sizes = True
    confidence_threshold = 0.2
    validate_image_sizes=True
    info=None
    preserve_nonstandard_metadata=True
    include_failed_images=False


    #%% Programmatic execution

    output_dict = md_to_coco(md_results_file,
                   coco_output_file=coco_output_file,
                   image_folder=image_folder,
                   confidence_threshold=confidence_threshold,
                   validate_image_sizes=validate_image_sizes,
                   info=info,
                   preserve_nonstandard_metadata=preserve_nonstandard_metadata,
                   include_failed_images=include_failed_images)


    #%% Command-line example

    s = f'python md_to_coco.py {md_results_file} {coco_output_file} {confidence_threshold} '
    if image_folder is not None:
        s += f' --image_folder {image_folder}'
    if preserve_nonstandard_metadata:
        s += ' --preserve_nonstandard_metadata'
    if include_failed_images:
        s += ' --include_failed_images'

    print(s); import clipboard; clipboard.copy(s)


    #%% Preview the resulting file

    from megadetector.visualization import visualize_db
    options = visualize_db.DbVizOptions()
    options.parallelize_rendering = True
    options.viz_size = (900, -1)
    options.num_to_visualize = 5000

    html_file,_ = visualize_db.visualize_db(coco_output_file,
                                              os.path.expanduser('~/tmp/md_to_coco_preview'),
                                              image_folder,options)

    from megadetector.utils import path_utils # noqa
    path_utils.open_file(html_file)


#%% Command-line driver

def main(): # noqa

    parser = argparse.ArgumentParser(
        description='"Convert" MD output to COCO format, in quotes because this is an opinionated ' + \
                    'transformation that requires a confidence threshold')

    parser.add_argument(
        'md_results_file',
        type=str,
        help='Path to MD results file (.json)')

    parser.add_argument(
        'coco_output_file',
        type=str,
        help='Output filename (.json)')

    parser.add_argument(
        'confidence_threshold',
        type=float,
        default=default_confidence_threshold,
        help='Confidence threshold (default {})'.format(default_confidence_threshold)
        )

    parser.add_argument(
        '--image_folder',
        type=str,
        default=None,
        help='Image folder, only required if we will need to access image sizes'
        )

    parser.add_argument(
        '--preserve_nonstandard_metadata',
        action='store_true',
        help='Preserve metadata that isn\'t normally included in ' +
             'COCO-formatted data (e.g. EXIF metadata, confidence values)'
        )

    parser.add_argument(
        '--include_failed_images',
        action='store_true',
        help='Keep a record of corrupted images in the output; may not be completely COCO-compliant'
        )

    if len(sys.argv[1:]) == 0:
        parser.print_help()
        parser.exit()

    args = parser.parse_args()

    md_to_coco(args.md_results_file,
               args.coco_output_file,
               args.image_folder,
               args.confidence_threshold,
               validate_image_sizes=False,
               info=None,
               preserve_nonstandard_metadata=args.preserve_nonstandard_metadata,
               include_failed_images=args.include_failed_images)

if __name__ == '__main__':
    main()
