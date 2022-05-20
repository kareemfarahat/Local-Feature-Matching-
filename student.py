import numpy as np
from skimage.filters import scharr_h, scharr_v, sobel_h, sobel_v, gaussian
import cv2
import matplotlib
import matplotlib.pyplot as plt


def get_interest_points(image, feature_width):
    """
    Returns interest points for the input image

    (Please note that we recommend implementing this function last and using cheat_interest_points()
    to test your implementation of get_features() and match_features())

    Implement the Harris corner detector (See Szeliski 4.1.1) to start with.
    You do not need to worry about scale invariance or keypoint orientation estimation
    for your Harris corner detector.
    You can create additional interest point detector functions (e.g. MSER)
    for extra credit.

    If you're finding spurious (false/fake) interest point detections near the boundaries,
    it is safe to simply suppress the gradients / corners near the edges of
    the image.

    Useful functions: A working solution does not require the use of all of these
    functions, but depending on your implementation, you may find some useful. Please
    reference the documentation for each function/library and feel free to come to hours
    or post on Piazza with any questions

        - skimage.feature.peak_local_max (experiment with different min_distance values to get good results)
        - skimage.measure.regionprops


    :params:
    :image: a grayscale or color image (your choice depending on your implementation)
    :feature_width:

    :returns:
    :xs: an np array of the x coordinates of the interest points in the image
    :ys: an np array of the y coordinates of the interest points in the image

    :optional returns (may be useful for extra credit portions):
    :confidences: an np array indicating the confidence (strength) of each interest point
    :scale: an np array indicating the scale of each interest point
    :orientation: an np array indicating the orientation of each interest point

    """
    Alpha = 0.03
    threshold = 0.005
    stride = 2
    sigma = 0.3
    rows = image.shape[0]
    columns = image.shape[1]
    xs = []
    ys = []
    dx = cv2.Sobel(image, cv2.CV_8U, 1, 0, ksize=5)
    dy = cv2.Sobel(image, cv2.CV_8U, 0, 1, ksize=5)
    dx = gaussian(dx, sigma)
    dy = gaussian(dy, sigma)

    dx2 = dx ** 2
    dy2 = dy ** 2
    dxy = dx * dy
    # find ssd
    for y in range(0, rows - feature_width, stride):
        for x in range(0, columns - feature_width, stride):
            Sxx = np.sum(dx2[y:y + feature_width + 1, x:x + feature_width + 1])
            Syy = np.sum(dy2[y:y + feature_width + 1, x:x + feature_width + 1])
            Sxy = np.sum(dxy[y:y + feature_width + 1, x:x + feature_width + 1])
            detH = (Sxx * Syy) - (Sxy ** 2)
            traceH = Sxx + Syy
            R = detH - Alpha * (traceH ** 2)
            # check the threshold
            if R > threshold:
                xs.append(x + int(feature_width / 2 - 1))
                ys.append(y + int(feature_width / 2 - 1))
    return np.asarray(xs), np.asarray(ys)


def get_features(image, x, y, feature_width):
    """
    Returns feature descriptors for a given set of interest points.

    To start with, you might want to simply use normalized patches as your
    local feature. This is very simple to code and works OK. However, to get
    full credit you will need to implement the more effective SIFT-like descriptor
    (See Szeliski 4.1.2 or the original publications at
    http://www.cs.ubc.ca/~lowe/keypoints/)

    Your implementation does not need to exactly match the SIFT reference.
    Here are the key properties your (baseline) descriptor should have:
    (1) a 4x4 grid of cells, each feature_width / 4 pixels square.
    (2) each cell should have a histogram of the local distribution of
        gradients in 8 orientations. Appending these histograms together will
        give you 4x4 x 8 = 128 dimensions.
    (3) Each feature should be normalized to unit length

    You do not need to perform the interpolation in which each gradient
    measurement contributes to multiple orientation bins in multiple cells
    As described in Szeliski, a single gradient measurement creates a
    weighted contribution to the 4 nearest cells and the 2 nearest
    orientation bins within each cell, for 8 total contributions. This type
    of interpolation probably will help, though.

    You do not have to explicitly compute the gradient orientation at each
    pixel (although you are free to do so). You can instead filter with
    oriented filters (e.g. a filter that responds to edges with a specific
    orientation). All of your SIFT-like feature can be constructed entirely
    from filtering fairly quickly in this way.

    You do not need to do the normalize -> threshold -> normalize again
    operation as detailed in Szeliski and the SIFT paper. It can help, though.

    Another simple trick which can help is to raise each element of the final
    feature vector to some power that is less than one.

    Useful functions: A working solution does not require the use of all of these
    functions, but depending on your implementation, you may find some useful. Please
    reference the documentation for each function/library and feel free to come to hours
    or post on Piazza with any questions

        - skimage.filters (library)


    :params:
    :image: a grayscale or color image (your choice depending on your implementation)
    :x: np array of x coordinates of interest points
    :y: np array of y coordinates of interest points
    :feature_width: in pixels, is the local feature width. You can assume
                    that feature_width will be a multiple of 4 (i.e. every cell of your
                    local SIFT-like feature will have an integer width and height).
    If you want to detect and describe features at multiple scales or
    particular orientations you can add input arguments.

    :returns:
    :features: np array of computed features. It should be of size
            [len(x) * feature dimensionality] (for standard SIFT feature
            dimensionality is 128)

    """
    # convert inputs to integers
    x = np.round(x).astype(int)
    y = np.round(y).astype(int)
    features = np.zeros((len(x), 4, 4, 8))
    sigma = 0.8
    filtered_image = gaussian(image, sigma)
    dx = scharr_v(filtered_image)
    dy = scharr_h(filtered_image)
    grad = np.sqrt(np.square(dx) + np.square(dy))
    thetas = np.arctan2(dy, dx)
    thetas[thetas < 0] += 2 * np.pi
    for m, (cor_x, cor_y) in enumerate(zip(x, y)):
        # getting the window to wirk on
        rows = (cor_x - (feature_width / 2 - 1), x + feature_width / 2)
        if rows[0] < 0:
            rows = (0, rows[1] - rows[0])
        if (rows[1] >= image.shape[0]).all():
            rows = (rows[0] + (image.shape[0] - 1 - rows[1]), image.shape[0] - 1)
        cols = (cor_y - (feature_width / 2 - 1), y + feature_width / 2)
        if cols[0] < 0:
            cols = (0, cols[1] - cols[0])
        if (cols[1] >= image.shape[1]).all():
            cols = (cols[0] - (cols[1] + 1 - image.shape[1]), image.shape[1] - 1)
        # square of features
        i1 = int(rows[0])
        i2 = rows[1].astype(int) + 1
        j1 = int(cols[0])
        j2 = cols[1].astype(int) + 1
        grad_w = grad[i1:i2[-1], j1:j2[-1]]
        theta_w = thetas[i1:i2[-1], j1:j2[-1]]
        for i in range(int(feature_width / 4)):
            for j in range(int(feature_width / 4)):
                current_grad = grad_w[int(i * feature_width / 4): int((i + 1) * feature_width / 4),
                               int(j * feature_width / 4): int((j + 1) * feature_width / 4)]
                current_grad = current_grad.flatten()
                current_theta = theta_w[int(i * feature_width / 4): int((i + 1) * feature_width / 4),
                                int(j * feature_width / 4): int((j + 1) * feature_width / 4)]
                current_theta = current_theta.flatten()
                features[m, i, j] = np.histogram(current_theta, bins=8,
                                                 range=(0, 2 * np.pi), weights=current_grad)[0]
    features = features.reshape((len(x), -1,))
    dev = np.linalg.norm(features, axis=1).reshape(-1, 1)
    dev[dev == 0] = 1  # to avoid deviding by zero
    features = features / dev
    threshold = 0.3
    features[features >= threshold] = threshold
    features = features ** 0.8

    return features


def match_features(im1_features, im2_features):
    """
    Implements the Nearest Neighbor Distance Ratio Test to assign matches between interest points
    in two images.

    Please implement the "Nearest Neighbor Distance Ratio (NNDR) Test" ,
    Equation 4.18 in Section 4.1.3 of Szeliski.

    For extra credit you can implement spatial verification of matches.

    Please assign a confidence, else the evaluation function will not work. Remember that
    the NNDR test will return a number close to 1 for feature points with similar distances.
    Think about how confidence relates to NNDR.

    This function does not need to be symmetric (e.g., it can produce
    different numbers of matches depending on the order of the arguments).

    A match is between a feature in im1_features and a feature in im2_features. We can
    represent this match as a the index of the feature in im1_features and the index
    of the feature in im2_features

    :params:
    :im1_features: an np array of features returned from get_features() for interest points in image1
    :im2_features: an np array of features returned from get_features() for interest points in image2

    :returns:
    :matches: an np array of dimension k x 2 where k is the number of matches. The first
            column is an index into im1_features and the second column is an index into im2_features
    :confidences: an np array with a real valued confidence for each match
    """

    # TODO: Your implementation here! See block comments and the project webpage for instructions

    # These are placeholders - replace with your matches and confidences!

    matches = []
    confidences = []

    # Loop over the number of features in the first image
    for i in range(im1_features.shape[0]):
        # Calculate the euclidean distance
        distance = np.sqrt(((im1_features[i, :] - im2_features) ** 2).sum(axis=1))

        # sort the distances in ascending order, while retaining the index of that distance
        sorted_distances = np.argsort(distance)
        # If the ratio between the 2 smallest distances is less than 0.8
        # add the smallest distance to the best matches
        if distance[sorted_distances[0]] < 0.8 * distance[sorted_distances[1]]:
            matches.append([i, sorted_distances[0]])
            confidences.append(1.0 - distance[sorted_distances[0]] / distance[sorted_distances[1]])

    confidences = np.asarray(confidences)
    confidences[np.isnan(confidences)] = np.min(confidences[~np.isnan(confidences)])

    return np.array(matches), confidences
