# engine_ai

Welcome to the code base for **engine_ai**!

This is the on-vehicle software that controls the car. In this
README, we will review how to install it on your compute platform, its overall code layout and finally how to use it
to control your vehicle. Please be aware that additional supporting content is available in our main portal page: 

https://miniautonomous.github.io/portal/

This is where you will find more resources regarding scaled vehicle assembly, **trainer_ai**, (used for training 
networks), and a variety of other information that might be helpful on your journey.

# Major Update

We have just completed a major update to our stack that includes:

* Vehicle stack ported to Jetpack 4.6
* Replaced the Intel RealSense D435i with the Raspberry Pi CM 2 camera as the primary vision sensor
* Created a port of **trainer_ai** for Pytorch!

Please note that we split the [trainer_ai](https://github.com/miniautonomous/trainer_ai) code base into a Keras 
repository and a PyTorch repository, (the latter of which will be published shortly), but that it is our intent to keep 
both versions fully compatible with vehicle stack. 

As we publish this update, please note that we will be updating this README, the **trainer_ai** README's, (since soon 
there will be two), and of course our main portal site. 

## Table of Contents

1. [Introduction](#introduction)
2. [Installation](#installation)
   
   i. [Option 1: Install from the MiniAutonmous SD Image](#option1-installing-from-the-miniautonomous-sd-card-image)
   
   ii. [Option 2: Build Required Libraries off of Jetpack 4.5](#option-2-use-the-nvidia-jetson-pack-45-image-and-build-the-required-libraries)
      
      1. [Installing Kivy](#installing-kivy)
   
      2. [Installing **pyrealsense**](#installing-the-pyrealsense-library)
   
3. [Code Structure & **trainer_ai** Interdependence](#code-structure)   
4. [Usage & Functionality](#usage-and-functionality)

   i. [*jetson_clocks*: Boosting inference performance](#jeston_clocks-a-hidden-gem)

# Introduction

**engine_ai** is the Python-based control framework for the scaled vehicle. It allows the user to manually drive the car,
record data with it and, once said data is uploaded to **trainer_ai** and a network trained, operate the vehicle in an
autonomous state. If you are not familiar with the miniAutonomous framework, we suggest visiting our primary portal page
before diving into this repo, but a summary slide is provided here to give you an overall view of the ecosystem.

<p align="center">
<img src=./img/intro_slide.png width="75%"><p></p>
<p align="center"> Figure 1: miniAutonomous in a slide</p>

This code repo provides the on-vehicle component of the functional loop given in the slide, and a primary components of
its functionality revolves around a Kivy user interface (UI) which is displayed on the car's embedded LCD.
A screen grab of the UI is shown in Figure 2 below:

<p align="center">
<img src=./img/ui_in_action.png width="70%"><p></p>
<p align="center"> Figure 2: The <i>engine_ai</i> UI in action!</p>

The code base is somewhat hardware agnostic and has been ported to both the NVIDIA Jetson Nano Developer Kit and to an 
Intel NUC. We will focus on the installation on the Jetson Nano since this is our compute platform of choice. We then
review the overall code structure followed by usage and functionality once deployed to a vehicle.

# Installation

Installation on a Jetson Nano is relatively straightforward if one uses the SD card image provided. This might be the 
best option for many users since that would bypass having to compile OpenCV from source library or having to deal with 
certain issues regarding some backend components. If the user would like to compile things from scratch off a fresh 
NVIDIA image, then we have notes of the things we needed to do to create an initial working compute platform.

## Option 1: Installing from the MiniAutonomous SD Card Image

If you want to skip the harshness of compiling OpenCV from source, then we highly recommend using the SD card image we 
have made available. The image has all the required  libraries installed and/or compiled, and both *engine_ai* and 
*trainer_ai* can be found in the **Code_Base** directory. Our image was created for a 64 GB MicroSD card. (At the time
of this writing, 64 GB MicroSD cards are a few dollars more than its 32 GB MicroSD cards, so we decided to step up the
memory available.)

The one critical issue that has come up on occasion is that before using the image we provide, it may be necessary to go 
through the initial startup process specified by NVIDIA for the Jetson Development Kit. (If our image boots the Nano up,
then there is no need to use the NVIDIA image.) This initial spin-up process includes flashing the most recent SD 
image NVIDIA provides, (which at the time of this writing is **JetPack 4.6**), for the Jetson **BEFORE** re-flashing it 
with the SD card we provide. 

The initial startup process consists of following the basic steps specified in the following URL:

https://developer.nvidia.com/embedded/learn/get-started-jetson-nano-devkit#write

Once you flash your device with the given JetPack image, download the image we provide and flash the Nano 
as you did originally with the JetPack image. Out SD card image is provided here:

[MiniAutonomous SD Card Image](https://drive.google.com/file/d/1tetrCtiTsfmPOa2i_ScAkhKoDOaWam9c/view?usp=sharing)

Disclaimer: We have flashed a number of different Jetson Nanos, (Developer Kit & 2 GB versions), with this image and 
never had an issue, but the Jetson platform has its quirks. If the above doesn't work, go to option 2.

## Option 2: Use the NVIDIA Jetson *JetPack 4.6* Image and Build the Required Libraries on Your Own

If your preference is to build the supporting software stack on your own, which is completely understandable, please know
that it's not simply a matter of doing a pip install off of the **requirements.txt** we provide. In fact, we can
guarantee that will not work on the Jetson platform.

For the Jetson, there is at the moment one primary challenging component to install: OpenCV. In past iterations of our 
stack, we had to deal with Kivy and the **pyrealsense** library, but the former is now easily address by doing a pip 
install of the kivy-jetson package, i.e.

``` python
pip install kivy-jetson
```

As for the latter, well that's a bit of sad story. It appears that Intel has decided to discontinue the RealSense line 
of products, so although the cameras are still available via third parties, they are priced very aggressively and more 
importantly will not be actively supported by Intel. Fortunately for us, however, the Raspberry Pi CM 2 has proven to be
an excellent replacement and is quite affordable. The key issue now is to build OpenCV from source on the Jetson to 
ensure full GPU support. Although the compile time for OpenCV is quite long on the Jetson platform, it has proven to be
relatively straightforward process, thanks in large parts to the efforts of **Automatic Addison** and his wonderful 
blog. 

Please note: if you already have an Intel Realsense camera or are have found one at a reasonable price, we have 
preserved our older version of *engine_ai* to the *realsense_support* branch.

Let's now begin with the OpenCV build instructions.

### Building OpenCV

Building OpenCV from source can avoid a number of issues that occur behind the scenes. Usually compile things on the 
Jetson nano platform is an exercise in patience and attrition, but thanks to **Automatic Addison**, the process has 
been broken down quite clearly. Once you have flashed your Jetson, head over to this URL and follow his instructions to
the letter:

[How to build OpenCV on the Jetson Nano](https://automaticaddison.com/how-to-install-opencv-4-5-on-nvidia-jetson-nano/)

If for any reason the URL is removed, let us know and we will create a summary to walk you through the process. Once you
complete the process above, please restart your Nano.

### Running the Raspberry Pi CM 2 Module

One of the nice things of using the Pi CM 2 module is that works virtually out of the box. By following Jim from Jetson 
Hack's script, (details provided @[Jetson Hacks: Using the Raspberry Pi CM 2](https://www.jetsonhacks.com/2019/04/02/jetson-nano-raspberry-pi-camera/), we got the camera up and running immediately. The one issue we did
find is that post switching the *engine_ai* to read from the new camera, there was a slight but steady lag in image 
rendering in our UI. We then made some hardwired changes to the arguments that get passed to **nvarguscamerasrc**, and
then we got our stability back.

Great. We are ready to start using *engine_ai*!

# Code Structure

Our intent in open sourcing this code set is to create a clear and transparent source code that would allow the user
to quickly understand the overall structure of the code and be able to focus on the deep learning components required
to allow  the vehicle to operate autonomously. 

Here is a brief summary of the primary files and directories content to orient you as you study the code.

```angular2html
    engine_ai.py: primary script that contains the control loop
    engine.kv: the Kivy table that controls the various properties of the User Interface (UI)
   
    >[arduino]: directory that contains the sketches and Python layers to interact with the vehicle's Arduino Mega
               microcontroller.
    >[kvSubPanels]: directory that contains the Kivy components that are members of the primary UI
    >[utils]: directory that contains the utilities that allow you to record data, store your prior selections when
              using the UI, and various utility functions that help do basic numeric and data processing
```

As with most control frameworks, at the heart of the software is a continuously running loop that determines both the 
current requirements on the system from the user and the current status of the vehicle. This loop is titled
**drive_loop**, and can be found on line 166 of *engine_ai.py*. This method should be your starting point
for reviewing the code and most elements will fall out from its various calls.

Two things we wanted to focus on here is the loading mechanism of trained networks and data recording function.

## Loading Trained Models

*trainer_ai* is the training component of *engine_ai* and a separate README is dedicated to its description.
(Please see its repo here: https://github.com/miniautonomous/trainer_ai.) *trainer_ai* allows for training networks
with sequences, (networks that my have a LSTM, GRU, bi-directional RNN, etc), allowing a model to have state memory, or
without sequences so that the network just takes an image in and produces a steering/throttle output. When the model is
loaded, in the method **load_dnn** on line 510, *engine_ai* reviews the shape of the input tensor and determines if 
the model uses sequences or not. 

In addition, *trainer_ai* can save a model as a standard **Keras** model or as a parsed **TensorRT** model. We highly,
highly recommend you use the parsed **TensorRT** option. This allows the network to run at least 4 to 5 
frames-per-second faster. We have a global variable, **USE_TRT** set to True, but if you are using and Intel NUC as your
compute platform you are going to have to set this to false since at the time of this writing, TensorRT is not available
on that platform.

## Data Recording

Before you actually run in autonomous mode, you are going to have to record data for the task you want the vehicle to
replicate. To do this, we have developed a threaded implementation of a data logger that uses the **HDF5** file format
to log image data and driver input in terms of throttle and steering. Here is a sample frame of a log file:

<p align="center">
<img src=./img/hdf5_sample.png width="75%"><p></p>
<p align="center"> Figure 3: A sample frame form an HDF5 file</p>

If you want to use the data logger for another application, all the pertinent code is found in the **write_hdf5.py** 
file in the **utils** directory. 

# Usage and Functionality

Great, so how do we use it? Good question! First thing, kick off the UI:

```python
python3 engine_ai.py
```

Once that's done, there are two parts to interacting with the code base: the UI and the radio transmitter. Let start
with the UI and then discuss how to use the transmitter.

Here is a labeled rendition of the UI:

<p align="center">
<img src=./img/ui_usage_labels.png width="75%"><p></p>
<p align="center"> Figure 4: UI layout and functions</p>

There are three buttons that require input from the user via a keyboard: the Power on/off button,
the Network Model button, and the Log Folder button. The very first step to start the system is to 
power it on via the Power button. The default state of the vehicle is in manual drive mode, so you should
now be able to drive the car around as if it was a standard RC car. 

PLEASE NOTE: When you start the car, have it on a stand with the wheels not making contact with any surface. Always test
responsiveness of the vehicle while the car is on the stand first to ensure you have full control.

If you have a trained **Keras** model file or **TensorRT** parsed model stored in a directory, use the Network Model 
button to select it. If you do not have a network model selected, switching the vehicle to autonomous mode will not 
change the state of the vehicle: a message in the Information Bar will inform the user to load a network first.

If you want to drive the vehicle and record data, use the Log Folder button to pick the directory where you want to 
store data first before doing the actual recording. Please note that the UI will remember your previous selections for 
the Network Model and Log Folder buttons, so once you restart the UI and click on those buttons, the UI will default to 
your last selections.

So now that you have the button options under your belt, it is now time to review what the transmitter controls. Here is
an image of the transmitter we have chosen for *MiniAutonomous*:

<p align="center">
<img src=./img/transmitter.png width="75%"><p></p>
<p align="center"> Figure 5: Transmitter description</p>

When you first start **engine_ai**, the default state of the vehicle will be manual driving. As with standard RC cars,
the throttle trigger and steering wheel will allow you to navigate it manually. Once a log folder has been selected to
store your data, the red rocker switch embedded in the handle of the transmitter will allow you to start and stop
recording: flip it down to start logging and up to stop. A green light will light up the recording status indicator of 
the UI to show that the vehicle is logging data. Each time you stop/start the logging state, a new **HDF5** will be 
created, logging the RGB coming from the camera along with your steering and throttle inputs. 
(Please see Figure 2 above.)

Finally, let's focus on autonomy. Say you have taken your data off of the vehicle, uploaded it to a server and used
*trainer_ai* to train a network. You can upload the resulting network to your vehicle and select it using the Network
Model button on the UI. Usually this takes 20 to 30 seconds for the network to be loaded on the Jetson. Once it is, you
can switch the drive mode of the vehicle from manual to an autonomous state using the three-way switch at the top of the
transmitter. When the swtich is back towards you, you are in manual drive model. There are two autonomous state: 
steering autonomous and Full AI, which is steering+throttle. Flip the switch to the middle, so that its pointing 
straight up, and you are in the steering autonomous state. Flip it all the way forward, and you have put the car into 
the Full AI mode. We suggest you never throw the switch to Full AI until you have tested your network performance out 
with manual throttle control. That will allow you to see how well your model is doing before you actually kick things 
off. 

PLEASE NOTE: When you switch the car to an autonomous state, once again make sure you have it on a stand with the wheels
not making contact with any surface. On occasion, when the vehicle is switched from the manual state to an autonomous 
state for the first time after being brought up, there is a slight pause where the Arduino Mega is expecting an input 
and is not receiving anything. The Arduino sometimes then decides to swap all the interrupts and the car is not 
responsive and the wheels might start to turn at max speed. Simply power off the UI, (**not** the car), and power it 
back up again and the Arduino will go back to desired interrupt schedule. It should not happen again for the rest of 
your drive test.

In terms of Full AI, we provide two options: either your network controls the throttle, or you set a constant velocity 
by setting a PWM value for throttle. The default state of the code is the latter: constant throttle value, but it's a 
key ingredient to train models to both control velocity and steering, so all you have to do is un-comment lines 359 to 
362 of **engine_ai.py** and you will have your throttle control handed over to your trained network.

## *jetson_clocks*: A hidden gem!

So a little hidden gem that is buried deep, (well, not really all that deep), in the Jetson stack is the command
*jetson_clocks*. What does it do, you ask? Well it makes everything run faster. Fundamentally,  it sets the frequencies
of all compute nodes on the device to the maximum possible setting. We have found that by typing the following in the 
terminal before launching *engine_ai*,

```angular2html
   sudo jetson_clocks
```
you get a boost of 4 to 5 additional frames-per-second when running inference on the Nano. The *sudo* password is 
*mini123*. (Please don't tell anybody.)

You may be tempted to just put something in your *bashrc* script, but we do note that your power consumption goes way up
when all the clocks are full tilt, so just keep that in mind since it might not be too helpful when manually driving the
car and/or logging data.