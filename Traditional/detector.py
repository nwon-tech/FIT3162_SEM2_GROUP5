import cv2
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial.distance import pdist


def readImage(image_name):
    """
    Function to read a given image name
    :param image_name: A string representing the name of the image
    :return: The image represented in a numpy.ndarray type
    """
    img = cv2.imread(image_name)
    return img


def showImage(image):
    """
    Function to display the image to the user. Closes the image window when user presses key "0"
    :param image: An image of type numpy.ndarray
    :return: None
    """
    cv2.namedWindow('image', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('image', 600, 600)  # Resize image window for better visuals
    cv2.imshow('image',image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def computeKeypoints(image):    #Extract keypoints of the given image
    """
    Function to compute keypoints of the given image
    :param image: An image of type numpy.ndarray
    :return: A list of keypoints
    """
    sift = cv2.xfeatures2d.SIFT_create()
    kp = sift.detect(image)
    return kp


def computeDescriptors(image, keypoints):
    """
    Function to compute the descriptors for each keypoint provided
    :param image: An image of type numpy.ndarray
    :param keypoints: A list of keypoints in the image
    :return: A tuple (keypoints, descriptors) whereby keypoints is a list of keypoints in an image and descriptors is a
             2d array consisiting of the shape (n, 128), whereby n is the number of keypoints. The number of columns is
             128 due to the use of the SIFT algorithm
    """
    sift = cv2.xfeatures2d.SIFT_create()
    kp, descriptors = sift.compute(image, keypoints)
    return kp, descriptors


def featureExtraction(image):
    """
    Function to extract the key features (keypoints and descriptors) of an image. Makes use of the computeKeypoints()
    and computeDescriptors() function.
    :param image: An image of type numpy.ndarray
    :return: A tuple (keypoints, descriptors)
    """

    # Image is converted to grayscale since color information would not help much.
    # Reference: https://www.quora.com/In-image-processing-applications-why-do-we-convert-from-RGB-to-Grayscale
    gray_img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    kp = computeKeypoints(gray_img)
    kp, desc = computeDescriptors(gray_img, kp)
    return kp, desc

def featureMatching(keypoints, descriptors):
    """
    Function to perform feature matching. Makes use of brute force matcher.
    Reference: https://docs.opencv.org/trunk/dc/dc3/tutorial_py_matcher.html
    :param keypoints: A list of keypoints
    :param descriptors: A 2-dimensional array of shape (n, 128), whereby n is the number of keypoints
    :return:
    """

    norm = cv2.NORM_L2  # cv2.NORM_L2 is used since we are using the SIFT algorithm
    k = 10  # number of closest match we want to find for each keypoint

    matcher = cv2.BFMatcher(norm)
    matches = matcher.knnMatch(descriptors, descriptors, k)

    # Apply ratio test to get good matches
    ratio = 0.5
    good_matches_1 = []
    good_matches_2 = []

    for match in matches:
        k = 1   # Ignore the first element in the matches array (distance to itself is always 0)

        while match[k].distance < ratio * match[k + 1].distance:  # d_i/d_(i+1) < T (threshold)
            k += 1

        for i in range(1, k):
            # Compute pairwise distance between the two points to ensure they are spatially separated
            if pdist(np.array([keypoints[match[i].queryIdx].pt, keypoints[match[i].trainIdx].pt])) > 10:
                good_matches_1.append(keypoints[match[i].queryIdx])
                good_matches_2.append(keypoints[match[i].trainIdx])

    points_1 = []   # Shape (n, 2)
    for i in range(np.shape(good_matches_1)[0]):
        points_1.append(good_matches_1[i].pt)

    points_2 = []  # Shape (n, 2)
    for i in range(np.shape(good_matches_2)[0]):
        points_2.append(good_matches_2[i].pt)

    if len(points_1) > 0 or len(points_2) > 0:
        # Combine 2d array points_1 (n, 2) and points_2 (n, 2) by their column -> (n, 4)
        p = np.hstack((points_1, points_2))

        # Remove any duplicated points
        # References: https://stackoverflow.com/questions/16970982/find-unique-rows-in-numpy-array
        unique_p = np.unique(p, axis=0)

        # Get back normal shape: (n, 4) -> (n, 2) and (n, 2)
        return np.float32(unique_p[:, 0:2]), np.float32(unique_p[:, 2:4])

    else:
        return None, None