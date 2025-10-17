import math as m
from PIL import Image, ImageOps
import numpy as np
def normalize(ch_input):
    """
    normalizes an input array according to the rgb linearlization algorithm
    Args:
        ch_input: a 2d array containing pixel values of one rgb channel

    Returns: 
        void

    Dependencies: 
        requires 'pow' module from library 'math' to linearlize bright pixels
    """
    for i in range(0, len(ch_input)):
        for j in range(0, len(ch_input[0])):
            if(ch_input[i][j] <= 0.0405):
                ch_input[i][j] = ch_input[i][j] / 12.92
            else:
                ch_input[i][j] = m.pow( ((ch_input[i][j] + 0.055)/1.055), 2.4 )  

CHANNEL_WEIGHTS = [0.2126, 0.7152, 0.0722]
def rgb_to_grayscale (img_array):  
    """
    converts an array of rgb pixel values into grayscale using the grayscale conversion algorithm
    Args:
        img_array: a 3 dimensional array containing data on the image
                   more specifically, it is a numpy array obtained from calling
                   numpy.asarray on PIL.Image.open, and NOT an appended list of
                   rgb pixel values
    Returns: 
        gray_values: a 2 dimensional array containing grayscale converted pixel values for the image

    Dependencies: 
        reqires module 'Image' from library 'PIL' for valid input data
        requires library 'numpy' for valid input type
    """
    ch_data = [0] * 3
    for i in range(0, len(ch_data)):
        ch_data[i] = img_array[:,:,i] / 255
        normalize(ch_data[i])
        ch_data[i] = ch_data[i] * CHANNEL_WEIGHTS[i]

    gray_values = np.zeros((len(ch_data[0]), len(ch_data[0][0])))

    for i in range(0, len(gray_values)):
        for j in range(0, len(gray_values[0])):
            for k in range(0, len(ch_data)):
                gray_values[i][j] += ch_data[k][i][j] * 255 

    return gray_values

class image:
    in_path: str
    img_data: list
    ch_data: list

    zero_width: int
    zero_height: int

    TGT_WIDTH = 100
    TGT_HEIGHT = 100
    size: tuple
    set_target_size_called = False

    def set_in_path(self, path:str):
        """
        sets the path for a new image
        Args:
            path <string>:  the path to the image
        Returns: 
            void
        Dependencies: 
            None
        """
        self.in_path = path

    def set_tar_size(self, width, height):
        """
        sets the output target size to map the image to
        Args:
            width <int>: the desired output width
            height <int>: the desired output height
        Returns: 
            void
        Dependencies: 
            None
        """
        self.TGT_WIDTH = width
        self.TGT_HEIGHT = height
        self.set_target_size_called = True

    def new_image(self):
        """
        initializes a new image class. a path must be set but target size will default to 100 with no call
        Args:
            none
        Returns: 
            void
        Dependencies: 
            None
        """

        t = Image.open(self.in_path)
        (self.zero_width,self.zero_height) = (t.width // 2, t.height // 2)
        if(self.set_target_size_called == False):
            self.TGT_WIDTH = self.zero_width
            self.TGT_HEIGHT = self.zero_height

        self.size = (self.TGT_WIDTH, self.TGT_HEIGHT)
        t2 = ImageOps.pad(t, self.size, color = '#000')
        self.img_data = np.asarray(t2, dtype= np.uint8)
        self.img_data = self.img_data.copy() 

        
    
    def get_rgb_data(self):
        for i in range(0, 3):
            self.ch_data = np.zeros( (3, len(self.img_data), len(self.img_data[0]) ) )
            self.ch_data[i] = self.img_data[:,:,i] / 255
            normalize(self.ch_data[i])
            self.img_data[:,:,i] = self.ch_data[i] * 255

    
    def get_grayscale_data(self):
        self.ch_data = self.img_data / 255
        normalize(self.ch_data)
        self.img_data = self.ch_data * 255
    
    def show_image(self):
        img_out = Image.fromarray(self.img_data)
        img_out.show()
    