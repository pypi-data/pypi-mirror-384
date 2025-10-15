import skimage
import numpy as np
import time
from .core import segm_model_segment, post_process_segm
from .features import custom_post_process_segm
from . import io, plot
import inspect



import os # for dbug
import json # for dbug

def find_overlap(lab_1, lab_2):
    """
    Function to find the overlap between two labeled images.
    Args:
        lab_1: first labeled image
        lab_2: second labeled image
    Returns:
        ID_overlap: list of tuples with the ID of the object in lab_1 and the percentage of overlap with lab_2
    """
    overlap_mask = np.logical_and(lab_1 > 0, lab_2 > 0)

    rp_1 = skimage.measure.regionprops(lab_1)
    ID_overlap = []

    for obj in rp_1:
        label = obj.label
        region_lab_1 = lab_1 == label
        overlap_area = np.sum(np.logical_and(region_lab_1, overlap_mask))
        if overlap_area == 0:
            continue

        total_area = obj.area
        overlap_perc = overlap_area / total_area
        ID_overlap.append((label, overlap_perc))

    return ID_overlap

def get_obj_from_rps(rps, ID):
    for obj in rps:
        if obj.label == ID:
            return obj
    return None

def get_box_coords(rps, prev_lab_shape, ID, padding):
    """
    Calculate the coordinates of a bounding box around a given ID in a labeled image,
    with optional padding.
    Parameters:
    rps (list): A list of regionprops objects for the labeled image.
    prev_lab_shape (tuple): The shape of the labeled image.
    ID (int): The ID of the object for which to calculate the bounding box.
    padding (float): The fraction of the object's size to use as padding around the bounding box.
    Returns:
    tuple: A tuple containing the coordinates of the bounding box (box_x_min, box_x_max, box_y_min, box_y_max).
    """

    obj = get_obj_from_rps(rps, ID)
    box_x_min, box_y_min, box_x_max, box_y_max = obj.bbox

    size_x = box_x_max - box_x_min
    size_y = box_y_max - box_y_min

    padding_x = int(size_x * padding)
    padding_y = int(size_y * padding)

    box_x_min = max(0, box_x_min - padding_x)
    box_x_max = min(prev_lab_shape[0], box_x_max + padding_x)
    box_y_min = max(0, box_y_min - padding_y)
    box_y_max = min(prev_lab_shape[1], box_y_max + padding_y)

    return box_x_min, box_x_max, box_y_min, box_y_max

def find_overlapping_bboxs(IDs, bboxs, order=1):
    """
    Finds and merges overlapping bounding boxes by considering chained overlaps.
    
    Parameters:
    - IDs: List of IDs corresponding to the bounding boxes.
    - bboxs: List of bounding boxes (x_min, x_max, y_min, y_max).
    - order: Number of times to perform the merging process.
    
    Returns:
    - new_bboxs: List of merged bounding boxes.
    """

    def boxes_overlap(bbox1, bbox2):
        """Helper function to check if two bounding boxes overlap."""
        x_min1, x_max1, y_min1, y_max1 = bbox1
        x_min2, x_max2, y_min2, y_max2 = bbox2

        # Check if there's no overlap
        if (x_max1 <= x_min2 or 
            x_max2 <= x_min1 or 
            y_max1 <= y_min2 or 
            y_max2 <= y_min1
            ):
            return False
        else:
            return True
        
    IDs =  [[ID] for ID in IDs]

    for _ in range(order):
        merged = [False] * len(bboxs)  # Keep track of whether a box has been merged
        new_bboxs = []
        new_IDs = []

        for i, bbox in enumerate(bboxs):
            if merged[i]:  # Skip already merged boxes
                continue

            # Start with the current bbox as the base for merging
            current_merged_bbox = bbox
            merged[i] = True  # Mark this box as merged
            IDs_merged = IDs[i] # Keep track of the IDs that have been merged

            # Try to merge it with all other boxes
            for j, other_bbox in enumerate(bboxs):
                if i == j or merged[j]:
                    continue

                if boxes_overlap(current_merged_bbox, other_bbox):
                    # Merge the two boxes into one
                    x_min1, x_max1, y_min1, y_max1 = current_merged_bbox
                    x_min2, x_max2, y_min2, y_max2 = other_bbox

                    current_merged_bbox = (
                        min(x_min1, x_min2),
                        max(x_max1, x_max2),
                        min(y_min1, y_min2),
                        max(y_max1, y_max2)
                    )

                    merged[j] = True  # Mark the other box as merged
                    IDs_merged.extend(IDs[j])  # Add the IDs of the other box to the merged IDs

            # Add the merged bbox to the new list
            new_bboxs.append(current_merged_bbox)
            new_IDs.append(IDs_merged)


        # If no changes occur, break the loop early
        if len(new_bboxs) == len(bboxs):
            break

        # Update the list of bounding boxes
        bboxs = new_bboxs
        IDs = new_IDs

    return IDs, bboxs

# def fast_border_touching_labels(label_img):
#     # Get unique labels from the four borders
#     border_labels = np.r_[
#         label_img[0, :],        # Top row
#         label_img[-1, :],       # Bottom row
#         label_img[:, 0],        # Left column
#         label_img[:, -1]        # Right column
#     ]
#     # Use np.unique once on the combined array
#     return np.unique(border_labels[border_labels != 0])

def single_cell_seg(model, prev_lab, curr_lab, curr_img, IDs, new_unique_ID,
                    win, posData, distance_filler_growth=1,
                    overlap_threshold=0.5, padding=0.4,
                    export_bbox_for_training=False,
                    ):
    """
    Function to segment single cells in the current frame using the previous frame segmentation as a reference. 
    IDs is from the previous frame segmentation, and the current frame should have already been tracked so the IDs match!
    Args:
        model: eval function used to segment the cells
        prev_lab: previous frame segmentation
        curr_lab: current frame segmentation
        curr_img: current frame image
        IDs: list of IDs of the cells to segment
        new_unique_ID: ID to start labeling new cells
        win: from the gui window which sets model params
        posData: position data (see rest of acdc)
        distance_filler_growth: distance to grow the other IDs to fill the background
        overlap_threshold: minimum overlap percentage to consider a cell already segmented
        padding: padding around the cell to segment
        export_bbox_for_training: if True, export bounding boxes for training model

    Returns:
        curr_lab: current frame segmentation with the segmented cells
        assigned_IDs: list of IDs assigned to the newly segmented cells


    """
    if export_bbox_for_training:
        bboxs_for_debug = []

    model_kwargs = win.model_kwargs
    preproc_recipe = win.preproc_recipe
    applyPostProcessing = win.applyPostProcessing
    standardPostProcessKwargs = win.standardPostProcessKwargs
    customPostProcessFeatures = win.customPostProcessFeatures
    customPostProcessGroupedFeatures = win.customPostProcessGroupedFeatures

    prev_rp = skimage.measure.regionprops(prev_lab)
    prev_lab_shape = prev_lab.shape

    bboxs = [get_box_coords(prev_rp, prev_lab_shape, ID, padding) for ID in IDs]
    IDs_bboxs, bboxs = find_overlapping_bboxs(IDs, bboxs)
    
    assigned_IDs = []

    uses_diameter = inspect.signature(model.segment).parameters.get('diameter', None) is not None
    for IDs, bbox in zip(IDs_bboxs, bboxs):
        box_x_min, box_x_max, box_y_min, box_y_max = bbox

        box_curr_img = curr_img[box_x_min:box_x_max, box_y_min:box_y_max].copy()
        box_curr_lab = curr_lab[box_x_min:box_x_max, box_y_min:box_y_max]

        box_curr_lab_other_IDs = box_curr_lab.copy()
        IDs = np.array(IDs)
        box_curr_lab_other_IDs[np.isin(box_curr_lab_other_IDs, IDs)] = 0

        box_curr_lab_other_IDs_grown = skimage.segmentation.expand_labels(box_curr_lab_other_IDs, distance=distance_filler_growth)

        # Fill other IDs with random samples from the background
        indices_to_fill = np.where(box_curr_lab_other_IDs_grown != 0)
        box_background = box_curr_img[box_curr_lab_other_IDs_grown==0]
        random_samples = np.random.choice(box_background, size=indices_to_fill[0].shape, replace=True)
        box_curr_img[indices_to_fill] = random_samples

        # Run model, give it the diameter of cell if possible
        if uses_diameter:
            diameters = []
            for ID in IDs:
                obj = get_obj_from_rps(prev_rp, ID)
                diameters.append(obj.axis_major_length)
            
            if len(diameters) == 0:
                diameter = None
            else:
                diameter = np.mean(diameters)

            model_kwargs['diameter'] = diameter
            
        box_model_lab = segm_model_segment(
            model, box_curr_img, model_kwargs,
            preproc_recipe=preproc_recipe,
            posData=posData,
        )

        if export_bbox_for_training:
            bboxs_for_debug.append([IDs, bbox, box_model_lab.copy(), box_curr_lab.copy()])

        # Post-processing        
        if applyPostProcessing:
            box_model_lab = post_process_segm(
                box_model_lab, **standardPostProcessKwargs
            )
            if customPostProcessFeatures:
                box_model_lab = custom_post_process_segm(
                    posData, 
                    customPostProcessGroupedFeatures, 
                    box_model_lab, box_curr_img, posData.frame_i, 
                    posData.filename, 
                    posData.user_ch_name, 
                    customPostProcessFeatures
                )

            ### maybe add roi extension if cells are deleted...

        # Find the overlap between the model segmentation and the other IDs
        overlap = find_overlap(box_model_lab, box_curr_lab_other_IDs)

        # Set overlapping regions to 0, so already segmented cells are not overwritten
        for ID, overlap_perc in overlap:
            if overlap_perc > overlap_threshold:
                box_model_lab[box_model_lab == ID] = 0
                
        rp_model_lab = skimage.measure.regionprops(box_model_lab)
        for obj in rp_model_lab:
            box_curr_lab_other_IDs[box_model_lab == obj.label] = new_unique_ID
            assigned_IDs.append(new_unique_ID)
            new_unique_ID += 1

        positive_mask = box_curr_lab_other_IDs > 0
        curr_lab[box_x_min:box_x_max, box_y_min:box_y_max][positive_mask] = box_curr_lab_other_IDs[positive_mask]

        if export_bbox_for_training:
            bboxs_for_debug[-1].append(box_curr_lab_other_IDs.copy())

    if export_bbox_for_training:
        frame_i = posData.frame_i

        os.makedirs(os.path.join(posData.images_path, ".train_box_data", posData.filename), exist_ok=True)

        npz_filepath = os.path.join(posData.images_path, ".train_box_data", posData.filename)
        json_filepath = os.path.join(posData.images_path, ".train_box_data", posData.filename, 'info.json')

        try:
            with open(json_filepath, 'r') as f:
                loaded_dict = json.load(f)
        except FileNotFoundError:
            loaded_dict = {}

        try:
            bboxs_info = loaded_dict[frame_i]
        except KeyError:
            bboxs_info = []

        start_i = len(bboxs_info)
        end_i = start_i + len(bboxs_for_debug)

        for i in range(start_i, end_i):
            IDs, bbox, box_model_lab, box_prev_lab, box_final_lab = bboxs_for_debug[i - start_i]
            npz_path = os.path.join(npz_filepath, f"{frame_i}_{i}.npz")
            io.savez_compressed(npz_path, box_model_lab=box_model_lab, box_prev_lab=box_prev_lab, box_final_lab=box_final_lab)
            bboxs_info.append([IDs, bbox, npz_path])
            
        loaded_dict[frame_i] = bboxs_info

        with open(json_filepath, 'w') as f:
            json.dump(loaded_dict, f, indent=4)

    return curr_lab, assigned_IDs, IDs_bboxs, bboxs