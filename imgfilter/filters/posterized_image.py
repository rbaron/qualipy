import cv2
import numpy

from .. import get_data
from ..machine_learning.svm import SVM
from ..utils.image_utils import read_image
from ..utils.utils import scaled_prediction

from filter import Filter


def get_input_vector(img):
    hist = cv2.calcHist([img], [0], None, [256], [0, 255])

    diffs = numpy.diff(hist.T[0])  # calculate derivatives
    sum_of_derivatives = numpy.sum(numpy.abs(diffs))
    derivative_average = sum_of_derivatives / 255.
    number_of_peaks = numpy.sum((diffs[:-1] > 0) & (diffs[1:] < 0))

    return numpy.array([derivative_average, number_of_peaks],
                       dtype=numpy.float32)


class Posterized(Filter):

    """Filter for detecting posterized images"""

    name = 'posterized'
    speed = 1

    def __init__(self, threshold=0.5, invert_threshold=False, svm_file=None):
        """Initializes a posterized image filter

        :param threshold: threshold at which the given prediction is changed
                          from negative to positive
        :type threshold: float
        :param invert_threshold: whether the result should be greater than
                                 the given threshold (default) or lower
                                 for an image to be considered positive
        :type invert_threshold: bool
        """
        super(Posterized, self).__init__(threshold, invert_threshold)

        self.svm = SVM()
        if svm_file is None:
            self.svm.load(get_data('svm/posterized.yml'))
        else:
            self.svm.load(svm_file)

    def predict(self, image_path, return_boolean=True, ROI=None):
        """Predict if a given image is posterized

        :param image_path: path to the image
        :type image_path: str
        :param return_boolean: whether to return the result as a
                               float between 0 and 1 or as a boolean
                               (threshold is given to the class)
        :type return_boolean: bool
        :param ROI: possible region of interest as a 4-tuple
                    (x0, y0, width, height), None if not needed
        :returns: the prediction as a bool or float depending on the
                  return_boolean parameter
        """
        image = read_image(image_path, ROI)
        prediction = self.svm.predict(get_input_vector(image))
        prediction = scaled_prediction(prediction)

        if return_boolean:
            return self.boolean_result(prediction)
        return prediction

    def train(self, images, labels, save_path=None):
        """Retrain the filter with new training images. The new
        model needs to be saved with the save function for later
        use.

        :param images: list of image paths to training images
        :type images: list
        :param labels: list of labels associated with the images,
                       0 for negative and 1 for positive
        :type labels: list
        :param save_path: possible filepath to save the resulting
                          model to, None if not needed
        :type save_path: str
        """
        super(Posterized, self).train(
            images, labels, self.svm,
            lambda img: cv2.imread(img, cv2.CV_LOAD_IMAGE_GRAYSCALE),
            get_input_vector)

        if save_path is not None:
            self.save(save_path)

    def load(self, path):
        """Load an SVM model from a file. Note that a model can
        also be given on initialization of the class.

        :param path: path to the SVM data file
        :type path: str
        """
        self.svm.load(path)

    def save(self, path):
        """Save the current SVM model to a file.

        :param path: path to the destination file
        :type path: str
        """
        self.svm.save(path)
