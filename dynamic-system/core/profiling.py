import numpy as np
from facenet_models import FacenetModel
import cv2

facenet = FacenetModel()
import skimage.io as io


def img_to_array(image_path):
    """ Converts image from image path into numpy array
    Parameters:
    image_path: string

    Returns:
    numpy array
    """
    # shape-(Height, Width, Color)
    image = io.imread(str(image_path))
    if image.shape[-1] == 4:
        # Image is RGBA, where A is alpha -> transparency
        # Must make image RGB.
        image = image[..., :-1]  # png -> RGB

    return image


def userinput(camera=False, image_directory="", array=None):
    """
    If camera is true, take a picture from the camera. If not, it reads the picture from a directory.
    """
    if camera:
        cam = cv2.VideoCapture(0)
        ret, image = cam.read()
        cam.release()
    elif array is not None:
        image = array
    else:
        # read image directory in matplotlib
        assert image_directory != "", "Please enter a valid image directory"
        image = img_to_array(image_directory)
    boxes, probabilities, landmarks = facenet.detect(image)
    if boxes is None:
        return (None, None)
    assert len(boxes) != 0, "This photo has no faces detected"
    for i in range(boxes.shape[0]):
        if not probabilities[i] > 0.9:
            boxes = np.delete(boxes, i, 0)  # delete probs and boxes for detections under tolerance
            probabilities = np.delete(probabilities, i, 0)
    return (boxes, facenet.compute_descriptors(image,
                                               boxes))  # returns the coordinates in a tuple with the array of descriptors for each face in the image


class Profiling:
    """
    This class is meant as a per-person Profile to host the name and average descriptor for an individual
    """

    def __init__(self, name):
        self.name = name
        self.array_of_descriptors = np.array([])
        self.average_descriptor = None

    @property
    def parameters(self):
        """
        Returns name and average descriptor
        """
        return (self.name, self.array_of_descriptors, self.average_descriptor)

    def add_descriptor_vectors(self, descriptors):
        """
        Takes in descriptors, and adds it to self.array_of_descriptors
        Parameters:
            descriptors: numpy array of descriptor vectors for the picture to be added
        """
        # Checks to see if the array of descriptors is empty, if so descriptors becomes the list and is reshaped to (1, 512)
        if np.shape(self.array_of_descriptors)[0] == 0:
            self.array_of_descriptors = descriptors
            self.array_of_descriptors = np.reshape(descriptors, (1, 512))
        else:
            self.array_of_descriptors = np.vstack((self.array_of_descriptors, descriptors))
        # Updates the average descriptors with each new addition
        self.average_descriptor = np.average(self.array_of_descriptors, axis=0)
