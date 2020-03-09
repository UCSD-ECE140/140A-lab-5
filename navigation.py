import torchvision
import torch
import torchvision.transforms as transforms
import torch.nn.functional as F
import cv2
import PIL.Image
import numpy as np
import traitlets
from jetbot import Camera, bgr8_to_jpeg
from jetbot import Robot
import time
import math

# Hint : Look at Road Following and Collision Avoidance Lab
class Navigation:
    def __init__(self):
        self.camera = Camera.instance(width=224, height=224)
        self.robot = Robot()
        #Collision Avoidance
        self.ca_model = torchvision.models.alexnet(pretrained=False)
        self.ca_model.classifier[6] = torch.nn.Linear(self.ca_model.classifier[6].in_features, 2)
        self.ca_model.load_state_dict(torch.load('best_model.pth'))
        self.device = torch.device('cuda')
        self.ca_model = self.ca_model.to(self.device)
        self.mean = torch.Tensor([0.485, 0.456, 0.406]).cuda().half()
        self.std = torch.Tensor([0.229, 0.224, 0.225]).cuda().half()
        self.normalize = torchvision.transforms.Normalize(self.mean, self.std)
        #Road following support variables
        self.angle = 0.0
        self.angle_last = 0.0
        # Instantiating the road following network.
        self.rf_model = torchvision.models.resnet18(pretrained=False)
        self.rf_model.fc = torch.nn.Linear(512, 2)
        self.rf_model.load_state_dict(torch.load('best_steering_model_xy.pth'))
        self.rf_model = self.rf_model.to(self.device)
        self.rf_model = self.rf_model.eval().half()
        self.speed_gain = 0.12
        self.steering_gain = 0
        self.steering_dgain = 0.1
        self.steering_bias = 0.0
        self.t_unit_dist = 0.04
        self.starttime = 0
        self.cumulative_angle = -1
        self.pitstop = []
        self.startposition = []
        self.pathpoints = [[]]
        self.proportionality_const = -1 # TODO : Add the proper value 

    def collision_avoidance_preprocessing(self, camera_value):
        """Preprocessing for collision avoidance."""
        ...
    
    def collision_avoidance(self, change):
        """This will determine the next start point which will be 
        which will be demarcated by the presence of another bot."""
        # Collision avoidance has to be trained to detect a bot as
        # and obstacle. This will then be called in the road following function.
        ...

    def road_following_preprocessing(self, image):
        "Preprocesses the image for road following."
        ...
        
    def road_following(self, change):
        "The main function to navigate in the race."
        ...
        # 1. This will ideally have the road following code
        # 2. This method will also call the collision avoidance 
        #       function which will detect the presence of a bot.
        # 3. Once the collision is detected it will verify it's position
        #       is within the range of the next start point
        # 4. If it is so, it will call the bot detected function
        #       which will publish a message on the appropriate topic.
        # 5. In addition to that it will also be storing its coordinate location
        # 6. The initial start angle (bot's orientation at the startpoint ) will 
        #       be provided to the students in the start-coordinates
      
    def collision_detected(self):
        """This will publish the message on the topic for the 
        next bot to run."""
        ...
    
    def move_to_start(self, pitstop, startpoint):
        """Calibrate the bot to reach the start positions."""
        # pitstop structure : list : [ x_coordinate, y_coordinate ]
        # startpoint structure : list : [ x_coordinate, y_coordinate, start_angle ]
        # start_angle : angle it makes with the x axis at the start location
    
    def sprint(self, baton_callback, pathpoints_callback):
        """Navigate through the track."""
        self.baton_callback = baton_callback
        self.path_callback = pathpoints_callback
        # Fill in more code




