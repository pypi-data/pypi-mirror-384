import os
import yarl
import numpy as np
import json
from deeplabel.label.gallery.images import Image

def url_to_name(url:str):
    return yarl.URL(url).name

def url_to_extension(url:str):
    """Return file's extension from url
    eg.
        .txt, .png, .jpg
    Note: Returns with presiding '.'
    """
    return os.path.splitext(url_to_name(url))[1]


def image_to_name(image:Image):
    """Image object to <image_id>.<image_extension>
    takes care of appropriate extension, i.e., jpg/png/etc
    """
    return image.image_id+url_to_extension(image.image_url)

def pascal_voc_color_map(N:int=256, normalized:bool=False):
    """ Copied from: https://gist.github.com/wllhf/a4533e0adebe57e3ed06d4b50c8419ae
    And tested by doing Image.open('<some img from pascal dataset>').getpalette()
    """
    def bitget(byteval:int, idx:int):
        return ((byteval & (1 << idx)) != 0)

    dtype = 'float32' if normalized else 'uint8'
    cmap = np.zeros((N, 3), dtype=dtype)
    for i in range(N):
        r = g = b = 0
        c = i
        for j in range(8):
            r = r | (bitget(c, 0) << 7-j)
            g = g | (bitget(c, 1) << 7-j)
            b = b | (bitget(c, 2) << 7-j)
            c = c >> 3

        cmap[i] = np.array([r, g, b])

    cmap = cmap/255 if normalized else cmap
    return cmap

def vertices_to_bbox(vertices:list):
    """ fetches bounding box from list of vertices 
        i.e. [x1, y1, x2, y2, x3, y3...]
    """
    
    x = [vertices[i] for i in range(0, len(vertices),2)]
    y = [vertices[i] for i in range(1, len(vertices),2)]
    top_left_x = min(x)
    top_left_y = min(y)
    width = max(x) - min(x)
    height = max(y) - min(y)

    bbox = [top_left_x, top_left_y, width, height] 
    return bbox

def encode_ids(object_list:list):
    '''
        Creates {string_id : int_id} mapping
        example - {'63a3d58833d3e1001f57aa50':1, '63a3d5a933d3e1001f57aa52':2}
    '''
    encoded_dict = {}
    for k, entry in enumerate(object_list):
        encoded_dict[entry['id']] = k
    return encoded_dict


def replace_ids(json_path:str):
    '''
        This function replaces string ids in coco json with int ones.
    '''
    json_file = json.load(open(json_path,'r'))

    category_ids_dict = encode_ids(json_file['categories'])
    image_ids_dict = encode_ids(json_file['images'])
    annotation_ids_dict = encode_ids(json_file['annotations'])

    #replacing string ids with int ids in categories
    for idx in range(len(json_file['categories'])):
        this_id = json_file['categories'][idx]['id']

        json_file['categories'][idx]['id_orig'] = this_id
        json_file['categories'][idx]['id'] = category_ids_dict[this_id]

    #replacing string ids with int ids in images
    for idx in range(len(json_file['images'])):
        this_id = json_file['images'][idx]['id']

        json_file['images'][idx]['id_orig'] = this_id
        json_file['images'][idx]['id'] = image_ids_dict[this_id]


    #replacing string ids with int ids in annotations and removing entries with unknown category ids
    new_annotations = []
    for idx in range(len(json_file['annotations'])):
        annotation_entry = json_file['annotations'][idx]
        
        this_id = annotation_entry['id']
        this_category_id = annotation_entry['category_id']
        this_image_id = annotation_entry['image_id']

        if this_category_id in category_ids_dict:
            annotation_entry['id_orig'] = this_id
            annotation_entry['id'] = annotation_ids_dict[this_id]
            annotation_entry['category_id'] = category_ids_dict[this_category_id]
            annotation_entry['image_id'] = image_ids_dict[this_image_id]
            new_annotations.append(annotation_entry)

    json_file['annotations'] = new_annotations
    json.dump(json_file, open(json_path,'w'), indent=4)