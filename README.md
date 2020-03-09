# README - ECE140A Lab 5

## Introduction

In lab 5, we will use components and concepts from previous labs (with a few
more additional components) to make our JetBots participate in a relay race
autonomously. The lab will be divided into five (six) stages:

0. **Setup**. Getting the lab 5 code on your JetBots.
1. **Pre-processing**. The participants perform calibration.
2. **Discovery**. The participants discover each other.
3. **Consensus**. The participants will decide where each of them should start the
   race.
4. **Race**. Self-explantory.
5. **Post-processing**. The participants aggregate the information obtained during
   the race to generate a "map" of the tracks.

> Note: This lab will have checkpoints/deliverables corresponding to every stage
> that must be demonstrated on the specified lab session dates.

> Note: If the TAs find that the lab is easier or harder than expected then they
> may increase or decrease the complexity of some of the stages (yay modularity!), so keep your
> eyes peeled for their Piazza posts.

## Setup

Perform the following steps for the setup stage.

1. Get the `140A-lab-5` repo (if you're reading this then you already have it).
2. Make sure that you have the MQTT and ML stuff on you JetBot from the previous labs.
3. Copy your repo on to your JetBot.

### Deliverables

1. The lab 5 repo copied to your JetBot.
2. Brief demonstration of your ML behaviors. Even if you couldn't get them to
   work perfectly for lab 2, you have a chance to improve them now.

## Pre-processing

The main objective of the pre-processing step is to come up with a frame of reference that will be used for navigation.
In subsequent steps, as you delve deeper into the problem, you will be required to know the position of the bot in a defined coordinate system.
You will also be required to extrapolate the position of the bot given that it has travelled in a certain direction with a certain velocity. The measurement will be done in m/s and cm/s. The speed that will be used on the bot is 0.2 which is approximately 25cm/s.
However, you are expected to calculate this for your specific JetBots since there may be variability between them. Similar calibration can also be done for the angular movement as well, however, whether you will be required to calibrate for angular movement will be intimated later depending on the complexity and the progress everyone is making.

The pit-stops where the three bots are placed will be demarcated in the space. The students will be required to calculate the coordinates of the pit-stops and start points and configure their bots to go to the start points from the pit-stops.

### Deliverables
1. A python function/method to make the bot go to point B, given that the position of self is known.

### Checkpoints
1. Configure bot to go to start point from pitstop


## Discovery

This stage is *very* similar to problem 1 from lab 4. First, the TAs will
arbitrarily pick three teams to participate in a race. These teams must discover
each other using MQTT communication. 

1. Each team publishes information about themselves on the topic
   `lab5/discovery` with the [appropriate message
   format](messages/team_discovery.json).
2. Each team must maintain a dictionary of all the participating teams(including
   self). This dictionary should not contain any duplicates.
3. Each then team subscribes to the topic `lab5/<own_teamname>/in` and should
   publish to `lab5/<teamname>/in` to send messages to team `<teamname>`.

### Deliverables

1. A python method that publishes the team information.
2. Demonstration that you are indeed subscribed to `lab5/<own_teamname>/in`.

## Consensus

In an IoT or a distributed environment, it is essential that different parties
have some mechanism for achieving consensus concerning decisions that affect
them all. It turns out that, in general, this is a very difficult problem to solve.
However, by making some assumptions we can make it significantly more tractable. For
this stage, first we will operate under the assumption that no (malicious)
adversaries exist. Then we will relax that assumption a bit by saying that the
majority of the players are not adversaries.

The main task at hand here is to get from a "pit-stop" position to the nearest
(for each team) starting point.

### Assumption 1: No adversaries

Under this assumption, all that is needed for successful behavior is that a
majority of the players have "correct" behavior. This is how we proceed:

1. The TAs will assign a "pit-stop" position to each team. Each pit-stop has an
   associated number (1, 2 or 3) associated with it. They will also assign a
   team to be the "leader" randomly (more on this later).
2. The teams must subscribe to topics `lab5/consensus/pitstop_coordinates/<i>`, where
   `<i> = 1, 2, 3`. The message you receive is of the [given format](messages/coordinates.json).
   Then they place their JetBots in the appropriate locations.
3. For these pit-stops, each team needs to make its way to the nearest starting
   point. The coordinates of each starting point can be found by subscribing to
   `lab5/consensus/start_coordinates/<i>`, where `<i> = 1, 2, 3`. The message
   format is the [same as above](messages/coordinates.json).
4. Now that each team has access to all the pit-stop and starting coordinates,
   to demonstrate your understanding of the problem, you need to compute the
   distance between each of the pit-stops to each of the starting points.
   Convert this computed information in a serialzed JSON object (by using
   `json.dumps` or similar) and send it as a message to the topic
   `lab5/consensus/understanding`. [See here](messages/understanding.json) for
   the message format.
5. Each team verifies the correctness of every other team's calculation and
   publishes [a message](messages/ok.json) accordingly to
   `lab5/consensus/understanding/ok`. 
> Make sure to have a threshold for distance computation verification. That is,
> if the calulation of other teams is within 0.1 of your calculation, consider
> it to be valid.

6. They leader team must check the `lab5/consensus/understanding/ok` topic and
   see that every team has been verified.
   1. If everything is okay, then the leader sends [a
      message](messages/init.json) to all the teams (including itself) on
      `lab5/<teamname>/in` and each of them start moving to the start points.
   2. If not, the leader publishes a [failure message](messages/fail.json) to `lab5/consensus/fail`. The TAs will then step in.

### Assumption 2: With two adversaries

> Note: This is not a part of the lab currently, but could be included later.

Steps 1-4 are exactly the same as when operating under assumption 1. But now,
there will be two adversarial players (read: the TAs) that are impersonating
some teams. They will publish incorrect distance calculations. 

### Deliverables

1. A python function that calulates the euclidean distance between two points.
2. A python method that uses the above function to calculate the distance
   between the pit-stops and starting points, and publishes this.
3. Demonstration of correct message publishing and subscribing.
4. A python method that verifies the distance calulations against their own calculations.
5. A python method that does the verification (as done by the leader).
   
### Checkpoints

1. A successful run-through of the above scenario.

## Race

Finally! The JetBots are at the three starting points. This proceeds as follows:

1. The leader is subscribed to the topic `lab5/race/go`.
2. As soon as the leader receives [a message](messages/go.json) on that topic,
   it sends [a message](messages/go_1.json) to all its teammates to their 'in'
   topics.
> This [message](messages/go_1.json) will enable to you to know the identity of
> the leader.

3. When the team on start position 1 receives a message from the leader, it starts moving
   using the road following ML behavior.
4. It continues to move until its collision avoidance detects an obstacle (the
   next JetBot).
> Note: there will be no other obstacles on the track, so the first obstacle to
> be detected should be the next JetBot (or an obstacle signifying the goal).

5. During the race, each team logs the coordinates of the points they passed
   through.

6. The first JetBot then stops and sends [a message](messages/go_2.json) to all
   its teammates. It also publishes its logged path as [a message](messages/path.json) to
   `lab5/race/path`.

7. The second JetBot moves until it detects an obstacle (next JetBot). It then
   stops and sends [a message](messages/go_3.json) to all its teammates. Like
   the first bot, it also publishes its logged path as [a message](messages/path.json) to `lab5/race/path`.
   
8. Similary, when the third team completes the race, it also publishes its logged path as [a  message](messages/path.json). This marks the end of the race.

### Deliverables

1. Good road following behavior. Improved from before if it wasn't robust.
2. Good collision avoidance behavior (especially at detecting other JetBots).

### Checkpoints

1. A successful run-through of the race.


## Post-processing

The key objective of post-processing is to visualize the path that was transversed by the bots.
The aggregated data will be sent to a REST server and be stored on the rest server.
The three teams collaborating for the race will be when interacting with the rest server, getting the data
and visualizing it in the browser using a javascript library.

The code for visualization is given below.

```html
<!doctype html>
<html>
	<head>
		<meta charset="UTF-8">
		<title>Canvas Tile Map</title>
		<style>
			#canvas{
				border: 0px solid black;
			}
		</style>
	</head>
	<body>
		<canvas id="canvas" height="400px" width="800px"></canvas>
		<script>
			var canvas = document.getElementById("canvas");
			var context = canvas.getContext("2d");
			var mapArray=[
				[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
				[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
				[0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
				[0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
				[0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0],	
				[0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,0,0,0,0,0],
				[0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0],
				[0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0],
				[0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0],
				[0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,0,0,0,0,0,0,0,0,0],
				[0,0,0,0,0,0,0,1,1,1,1,1,1,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0],
				[0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0],
				[0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0],
				[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
				[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
				[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
			];

			var path = new Image();
			var background = new Image();
			
			// Add the appropriate png file
			path.src= '/home/muditj/Desktop/path.png';
			// Add the appropriate png file
			background.src = '/home/muditj/Desktop/background.png';

			var posX=0;
			var posY = 0;

			path.onload = function (){
			background.onload = function (){
			for(var i=0; i < mapArray.length; i++){
				for(var j=0; j < mapArray[i].length; j++){
					if(mapArray[i][j]==0){
						context.drawImage(path,posX, posY, 25, 25);
					}
					if(mapArray[i][j]==0){
						context.drawImage(background,posX,posY,25,25);
					}
					posX+=25;
				}
				posY+=25;
				posX=0;
			}
		}
	}


		</script>
	</body>
</html>
```

Note: Right now the code written translates an 8m * 4m track into 800 * 400 pixels on the browser. The track is plotted with a granularity of 25cms.
