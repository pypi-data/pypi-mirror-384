#!/usr/bin/env python
"""
 pixel_check:   Test if an image shows the 2 pixel shift pattern
                (see below for details)

 Usage from the command line:
    python pixel_test.py  <filename> <fix>

    If filename is not specified one can enter this interactively
    If filename is a directory path all image files (sdR*.fit)
        in that directory will be scanned.
    If filename is a specific file only this image will be scanned

    <fix> can be True or False (False is the default if this argument is not given.
    If the argument is True, pixel_check will attempt to fix the image if the
        pixel_shift error is detected.
    The fixed image is written to sdR*.fit_fixed (see comment about overscan
        region below).
"""

import os
import sys

import numpy as np
from astropy.io import fits


pixel_jump_hi = 1000.0
pixel_jump_low = 300.0

debug_flag = False


def pixel_check(filename, fix=False):
    hdulist = fits.open(filename)

    pixdata = hdulist[0].data
    if pixdata.shape != (4224, 4352):
        print(
            "Are you sure this is a BOSS image - "
            "Pixel array size is not (4224,4352) but %s." % str(pixdata.shape)
        )
    y_size = pixdata.shape[0]
    x_size = pixdata.shape[1]
    start_row = 0
    end_row = 0
    count = 0
    if debug_flag:
        print("Checking column sums...")
    sums = pixdata.sum(axis=0)
    mean = sums[2:20].mean()
    sigma = sums[2:20].std()
    if (sums[0] - mean) / sigma > 5:
        count += 1
        if debug_flag:
            print("Column 0 deviates more than 5 sigma from mean. Pixel Shift Error.")
    if (sums[1] - mean) / sigma > 5:
        count += 1
        if debug_flag:
            print("Column 1 deviates more than 5 sigma from mean. Pixel Shift Error.")

    end = len(sums)
    mean = sums[end - 20 : end - 2].mean()
    sigma = sums[end - 20 : end - 2].std()
    if (sums[end - 1] - mean) / sigma > 5:
        count += 1
        if debug_flag:
            print(
                "Last column deviates more than 5 sigma from mean. Pixel Shift Error."
            )
    if (sums[end - 2] - mean) / sigma > 5:
        count += 1
        if debug_flag:
            print(
                "Next to last column 1 deviates more than 5 "
                "sigma from mean. Pixel Shift Error."
            )

    # For now just print an error message and run the other test.
    # This needs to be improved.
    if count == 4:
        print(
            "Test 1: First + last column sums of %s are more than "
            " 5 sigma from the mean." % filename
        )
        print("        Pixel Shift Error detected.")
    else:
        print("Test 1: False")

    #
    # Determine background level
    #
    bkg_1 = 0.0
    bkg_2 = 0.0
    bkg_3 = 0.0
    bkg_4 = 0.0
    for i in range(25):
        bkg_1 += pixdata[i, 0]
        bkg_2 += pixdata[i, x_size - 1]
        bkg_3 += pixdata[y_size - i - 1, 0]
        bkg_4 += pixdata[y_size - i - 1, x_size - 1]
    bkg_left = (bkg_1 + bkg_3) / 50.0
    bkg_right = (bkg_2 + bkg_4) / 50.0
    if debug_flag:
        print("Background levels (left, right) ", bkg_left, bkg_right)

    # Find the suspicous pattern:
    #      1) Look for non background data in columns 0,1 and 4350, 4351
    #      2) Calculate the jump in pixel values
    #      3) Check if at least in one of the columns the change is larger
    #           than a high threshold
    #      4) Check that all for "jumps" are above a low threshold
    #      5) Confirm that the error pattern is symmetric around the center of
    #           the pixel array (row 2112)

    for i in range(y_size - 1):
        jump_0 = abs(pixdata[i, 0] - bkg_left)
        jump_1 = abs(pixdata[i, 1] - bkg_left)
        jump_2 = abs(pixdata[i, 2] - bkg_left)
        jump_4349 = abs(pixdata[i, x_size - 3] - bkg_right)
        jump_4350 = abs(pixdata[i, x_size - 2] - bkg_right)
        jump_4351 = abs(pixdata[i, x_size - 1] - bkg_right)
        if start_row == 0:
            if (max(jump_0, jump_1, jump_4350, jump_4351) > pixel_jump_hi) and (
                min(jump_0, jump_1, jump_4350, jump_4351) > pixel_jump_low
            ):
                if debug_flag:
                    print(
                        (
                            "found step in pixel values at row %d: %f, %f, %f, %f"
                            % (i, jump_0, jump_1, jump_4350, jump_4351)
                        )
                    )
                    print(
                        (
                            "Step in control columns (2, 4349): %f, %f"
                            % (jump_2, jump_4349)
                        )
                    )
                start_row = i
        elif end_row == 0:
            if max(jump_0, jump_1, jump_4350, jump_4351) < pixel_jump_low:
                if debug_flag:
                    print(
                        (
                            "found step in pixel values at row %d: %f, %f, %f, %f"
                            % (i, jump_0, jump_1, jump_4350, jump_4351)
                        )
                    )
                    print(
                        (
                            "Step in control columns (2, 4349): %f, %f"
                            % (jump_2, jump_4349)
                        )
                    )
                end_row = i

    if start_row != 0 and end_row != 0:
        pixel_shift = True
        if start_row + end_row == y_size:
            if debug_flag:
                print("Found pattern.")
        else:
            if debug_flag:
                print(
                    "Found something but start_row + end_row is not equal to y size ."
                )
            pixel_shift = False
        # Confirm that we have a 2 pixel shift
        # there should be no jump in columns 2 and 4349
        for column in (2, x_size - 3):
            if (
                abs(pixdata[start_row, column] - pixdata[start_row - 1, column])
                > pixel_jump_low
            ):
                pixel_shift = False
                break
            if (
                abs(pixdata[end_row, column] - pixdata[end_row + 1, column])
                > pixel_jump_low
            ):
                pixel_shift = False
                break
    else:
        pixel_shift = False

    if not pixel_shift:
        return False

    if not fix:
        return pixel_shift

    # Now lets try to fix things
    # We can move pixel blocks around using numpy but doing this on the formatted images
    # is not quiet correct since the overscan lines will also be shifted.If this matters
    # for the bias(?) calculation and has to undo toe formatting done in
    # DAQInterface.py, shuffle the bad blocks around and format again. The current
    # version of this code does not do this.
    #
    # Strategy: allocate a new numpy array of the same size and fill it with zeros
    # Copy the good part of the image below the shifted region from the original
    #   pixel array to the output array
    # Copy the good part of the image above the shifted region
    # (Left side) Copy the shifted region 2 pixels to the left
    # (Left side) Copy columns 0 and 1 from the original pixel array to the center
    #   (array size in x)/2 - 2 (and 1)
    # (Right side) Copy the shifted region 2 pixels to the right
    # (Right side) Copy the last two columns of the original pixel array to the center
    #   (array size in x)/2 + 2 (and 1)
    outfile = filename + "_fixed"

    output_array = np.zeros((y_size, x_size), dtype=np.uint16)
    output_array[0:start_row, :] = pixdata[0:start_row, :]
    output_array[end_row:, :] = pixdata[end_row:, :]
    output_array[start_row:end_row, 0 : (x_size / 2 - 2)] = pixdata[
        start_row:end_row, 2 : (x_size / 2)
    ]
    output_array[start_row:end_row, (x_size / 2 - 2) : (x_size / 2)] = pixdata[
        start_row:end_row, 0:2
    ]
    output_array[start_row:end_row, (x_size / 2) : (x_size / 2 + 2)] = pixdata[
        start_row:end_row, x_size - 2 : x_size
    ]
    output_array[start_row:end_row, (x_size / 2 + 2) :] = pixdata[
        start_row:end_row, (x_size / 2) : x_size - 2
    ]

    hdulist[0].data = output_array
    hdulist.writeto(outfile)
    return "Fixed"


def check_dir(directory, fix=False):
    for file_name in os.listdir(directory):
        if file_name.find("sdR") != -1 and file_name.find(".fit") != -1:
            print(
                (
                    "Test 2: Does image %s include the pixel shift error: %s"
                    % (
                        file_name,
                        str(pixel_check(os.path.join(directory, file_name), fix)),
                    )
                )
            )


if __name__ == "__main__":
    try:
        file_name = sys.argv[1]
    except:
        file_name = input("Enter image file name: ")
    try:
        fix = sys.argv[2]
    except:
        fix = False
    if os.path.isfile(file_name):
        # debug_flag = True
        print(
            "Test 2: Does image %s include the pixel shift error: %s"
            % (file_name, str(pixel_check(file_name, fix)))
        )
    else:
        print("Checking image files in directory %s." % str(file_name))
        check_dir(file_name, fix)
