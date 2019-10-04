]import cv2
import imutils
import numpy as np
import matplotlib.pyplot as plt
from scipy.cluster import hierarchy
from collections import Counter


def readImage(image_name):
    return cv2.imread(image_name)


def showImage(image):
    image = imutils.resize(image, width=600)
    cv2.imshow('image', image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def featureExtraction(image):
    gray_img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    sift = cv2.xfeatures2d.SIFT_create()
    kp, desc = sift.detectAndCompute(gray_img, None)
    return kp, desc


def featureMatching(keypoints, descriptors):
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
            if hierarchy.distance.pdist(np.array([keypoints[match[i].queryIdx].pt, keypoints[match[i].trainIdx].pt])) > 10:
                good_matches_1.append(keypoints[match[i].queryIdx])
                good_matches_2.append(keypoints[match[i].trainIdx])

    points_1 = []   # Shape (n, 2)
    points_2 = []  # Shape (n, 2)
    for i in range(np.shape(good_matches_1)[0]):
        points_1.append(good_matches_1[i].pt)
        points_2.append(good_matches_2[i].pt)

    if len(points_1) > 0:
        p = np.hstack((points_1, points_2))  # column bind
        unique_p = np.unique(p, axis=0)  # Remove any duplicated points
        return np.float32(unique_p[:, 0:2]), np.float32(unique_p[:, 2:4])  # Get back normal shape: (n, 4) -> (n, 2) and (n, 2)

    else:
        return None, None


def hierarchicalClustering(points_1, points_2, metric, th):
    points = np.vstack((points_1, points_2))     # vertically stack both sets of points
    distance = hierarchy.distance.pdist(points)
    Z = hierarchy.linkage(distance, metric)
    C = hierarchy.fcluster(Z, t=th, criterion='inconsistent', depth=4)
    return filterOutliers(C, points)


def filterOutliers(cluster, points):
    cluster_count = Counter(cluster)

    to_remove = []  # Find clusters that does not have more than 3 points (remove them)
    for key in cluster_count:
        if cluster_count[key] <= 3:
            to_remove.append(key)

    indices = []    # Find indices of points that corresponds to the cluster that needs to be removed
    for i in range(len(to_remove)):
        indices = np.concatenate([indices, np.where(cluster == to_remove[i])], axis=None)

    indices = indices.astype(int)
    indices = sorted(indices, reverse=True)

    for i in range(len(indices)):   # Remove points that belong to each unwanted cluster
        points = np.delete(points, indices[i], axis=0)

    for i in range(len(to_remove)): # Remove unwanted clusters
        cluster = cluster[cluster != to_remove[i]]

    n = int(np.shape(points)[0]/2)
    points1 = points[:n]
    points2 = points[n:]
    return cluster, points1, points2


def plotImage(img, p1, p2, C):
    plt.imshow(img)
    plt.axis('off')

    colors = C[:np.shape(p1)[0]]
    plt.scatter(p1[:, 0], p1[:, 1], c=colors, s=30)

    for item in zip(p1, p2):
        x1 = item[0][0]
        y1 = item[0][1]

        x2 = item[1][0]
        y2 = item[1][1]

        plt.plot([x1, x2],[y1, y2], 'c')

    plt.show()


def run(image):
    kp, desc = featureExtraction(image)
    p1, p2 = featureMatching(kp, desc)
    showImage(image)

    if p1 is None:
        print("No tampering was found")
        return False

    clusters, p1, p2 = hierarchicalClustering(p1, p2, 'ward', 2.2)

    image = cv2.cvtColor(image,cv2.COLOR_BGR2RGB)
    plotImage(image, p1, p2, clusters)
    return True


if __name__ == "__main__":
    img = readImage("monash_copy.jpg")
    run(img)