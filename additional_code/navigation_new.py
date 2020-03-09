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
import traitlets
from IPython.display import display
import ipywidgets

class Navigation:
    def __init__(self):
        print('Setting up camera')
        self.camera = Camera.instance(width=224, height=224)
        print('Set up camera')
        self.robot = Robot()
        self.completed = False
        # Collision Avoidance.
        print('Loading CA model')
        self.ca_model = torchvision.models.alexnet(pretrained=False)
        self.ca_model.classifier[6] = torch.nn.Linear(self.ca_model.classifier[6].in_features, 2)
        #self.ca_model.load_state_dict(torch.load('best_model_nvidia.pth'))
        self.device = torch.device('cuda')
        self.ca_model = self.ca_model.to(self.device)
        print('Loaded CA model')
        self.mean = 255.0 * torch.Tensor(np.array([0.485, 0.456, 0.406])).cuda().half()
        self.std = 255.0 * torch.Tensor(np.array([0.485, 0.456, 0.406])).cuda().half()
        self.normalize = torchvision.transforms.Normalize(self.mean, self.std)
        # Road following support variables.
        self.angle = 0.0
        self.angle_last = 0.0
        # Instantiating the road following network.
        print('Loading RF model')
        self.rf_model = torchvision.models.resnet18(pretrained=False)
        self.rf_model.fc = torch.nn.Linear(512, 2)
        self.rf_model.load_state_dict(torch.load('best_steering_model_xy.pth'))
        self.rf_model = self.rf_model.to(self.device)
        self.rf_model = self.rf_model.eval().half()
        print('Loaded RF Model')
        # Initializing additional variables.
        self.speed_gain = 0.12
        self.steering_gain = 0
        self.steering_dgain = 0.1
        self.steering_bias = 0.0
        self.starttime = 0
        self.cumulative_angle = -1
        self.pitstop = []
        self.startposition = []
        self.start_num = -1
        self.baton_callback = None
        self.pathpoints_callback = None
        self.pathpoints = [[]]
        # Add proper value below.
        self.proportionality_const = -1 
        self.image_widget = ipywidgets.Image()
        self.previous_position = -1
        traitlets.dlink((self.camera, 'value'), (self.image_widget, 'value'), transform=bgr8_to_jpeg)

    def preprocess_detect_collision(self, camera_value):
        """Preprocessing for collision avoidance."""
        x = camera_value
        x = cv2.cvtColor(x, cv2.COLOR_BGR2RGB)
        x = x.transpose((2, 0, 1))
        x = torch.from_numpy(x).float()
        x = self.normalize(x)
        x = x.to(self.device)
        x = x[None, ...]
        print("Collision Detection Preprocessing done.")
        return x 
    
    def detect_collision(self, change):
        """This will determine the next start point which will be 
        which will be demarcated by the presence of another bot."""
        # Collision avoidance has to be trained to detect a bot as
        # an obstacle. This will then be called in the road following function.
        x = change['new']
        x = self.preprocess_detect_collision(x)
        y = self.ca_model(x)
        y = F.softmax(y, dim=1)
        prob_blocked = float(y.flatten()[0])
        # Debugging : print('Prob: ', prob_blocked)
        if prob_blocked < 0.5:
            print('Free')
            return False
        else:
            print('Blocked')
        return True

    def update_cumulative_angle(self, angle):
        """Update the cumulative angle."""
        self.cumulative_angle = angle * self.proportionality_const + self.cumulative_angle # self.angle is proportional to actual angle

    def log_data(self, angle):
        """Save the path coordinates."""
        self.update_cumulative_angle(angle)
        if (time.time() - self.starttime > 0.2): # every 0.2 seconds log the data
            print('Logging Data')
            # with the assumption that every 0.2s it moves 2 cm
            displacement_vec = [2 * math.cos(self.cumulative_angle), 2 * math.sin(self.cumulative_angle)]
            new_position = [self.previous_position[0] + displacement_vec[0], self.previous_position[1] + displacement_vec[1]]
            self.pathpoints.append(new_position)
            self.previous_position = new_position
            self.starttime = time.time()
        
    def update_motor_values(self, pid):
        """Update the left and right motor values."""
        steering_value = pid + self.steering_bias
        self.robot.left_motor.value = max(min(self.speed_gain + steering_value, 1.0), 0.0)
        self.robot.right_motor.value = max(min(self.speed_gain - steering_value, 1.0), 0.0)
    
    def preprocess_follow_road(self, image):
        """Preprocesses the image for road following."""
        image  = PIL.Image.fromarray(image)
        image = transforms.functional.to_tensor(image).to(self.device).half()
        image.sub_(self.mean[:, None, None]).div_(self.std[:, None, None])
        return image[None, ...]    
    
    def follow_road(self, change):
        """Function for road following"""
        self.starttime = time.time()
        if self.cumulative_angle == -1:
            self.cumulative_angle = self.startpoint[2]
            self.previous_position = self.startpoint[0:2]
        collision_detected = self.detect_collision(change)
        if self.completed:
            self.robot.stop()
        elif collision_detected:
            self.completed = True
            self.next_bot_detected()
        image = change['new']
        print('Processing camera frame for road processing')
        xy = self.rf_model(self.preprocess_follow_road(image)).detach().float().cpu().numpy().flatten()
        x = xy[0]
        y = (0.5 - xy[1]) / 2.0
        self.angle = np.arctan2(x,y)
        # Debugging : print('Angle = ', self.angle)
        pid = self.angle * self.steering_gain + (self.angle - self.angle_last) * self.steering_dgain
        print('Update Motor Values')
        self.update_motor_values(pid)
        print('Logging Data')
        self. log_data(self.angle)


    def next_bot_detected(self):
        """Call the baton and the pathpoints callback upon detecting a bot."""
        self.camera.unobserve(self.follow_road, names='value')
        time.sleep(0.1)
        self.robot.stop()
        self.baton_callback(self.start_num)
        self.pathpoints_callback(self.pathpoints)

    def move_forward(self, distance, turbo=0):
        """Move forward for a certain distance."""
        if(turbo == 1):
            self.linear_velocity_value = 0.3
            self.robot.forward(self.linear_velocity_value)
            time.sleep(0.7)
            self.robot.stop()
            return
        self.linear_velocity_value = 0.2
        self.t_unit_distance = 3.7
        self.robot.forward(self.linear_velocity_value)
        time.sleep(distance*self.t_unit_distance)
        self.robot.stop()

    def turn(self, direction, degrees):
        """Turn the bot either 90 or 180 degrees"""
        self.anticlockwise_turn_time = 0.35
        self.clockwise_turn_time = 0.35
        self.turn_velocity_value = 0.2
        if (degrees == 180):
            self.turn_time = 2 * self.turn_time
        if (direction == "clockwise"):
            self.robot.right(self.turn_velocity_value)
            time.sleep(self.clockwise_turn_time)
        elif (direction == "anticlockwise"):
            self.robot.left(self.turn_velocity_value)
            time.sleep(self.anticlockwise_turn_time)
        self.robot.stop()

    def move_to_start(self, pitstop, startpoint, startnum):
        """Move the bot from pitstop to startpoint."""
        self.pitstop = pitstop
        self.startpoint = startpoint
        delta_x = abs(startpoint[0] - pitstop[0])
        delta_y = abs(startpoint[1] - pitstop[1])
        if(startnum == 1):
            self.turn("anticlockwise", 90)
            self.move_forward(delta_y)
            self.turn("clockwise", 90)
            self.move_forward(delta_x)
            self.turn("clockwise", 90)
            #self.move_forward(self, 0, 1)
            self.startpoint.append(4.71) #radians
        elif(startnum == 2):
            self.move_forward(delta_x)
            self.turn("anticlockwise", 90)
            self.move_forward(delta_y)
            self.turn("clockwise", 90)
            #self.move_forward(self, 0, 1)
            self.startpoint.append(0) #radians
        elif(startnum == 3):
            self.move_forward(delta_x)
            self.turn("clockwise", 90)
            self.move_forward(delta_y)
            self.turn("clockwise", 90)
            #self.move_forward(self, 0, 1)
            self.startpoint.append(3.14) #radians
        self.robot.stop()

    def sprint(self, baton_callback, pathpoints_callback, start_num):
        """Navigate through the track."""
        # Debugging : print(f'Hello from sprint with start_num {start_num}')
        self.baton_callback = baton_callback
        self.pathpoints_callback = pathpoints_callback
        self.start_num = start_num
        self.follow_road({'new': self.camera.value})
        self.camera.observe(self.follow_road, names='value')
