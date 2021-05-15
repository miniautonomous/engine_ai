# engine_ai

Welcome to the code base for **engine_ai**!

This is the on-vehicle software that controls the drone. In this
README, we will present the over-all code structure, how to install it on your compute platform, and how to use it to
control your vehicle. Please be aware that additional supporting content is available in our main portal page: 

https://miniautonomous.github.io/portal/

This is where you will find more resources regarding scaled vehicle assembly, **trainer_ai**, (used for training 
networks), and a variety of other information that might be helpful on your journey.

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

**engine_ai** is the Python-based control framework for the drone. It allows the user to manually drive the drone,
record data with it and, once said data is uploaded to **trainer_ai** and a network trained, operate the drone in an
autonomous state.

Its functionality revolves around a Kivy UI, shown in Figure 1 below:

<p align="center">
<img src=./img/ui_in_action.png width="75%"><p></p>
<p align="center"> Figure 1: The **engine_ai** UI in action!</p>

The code base is somewhat hardware agnostic, and has been ported to both the NVIDIA Jetson Nano Developer Kit and to an 
Intel NUC. We will focus on the installation on the Jetson Nano since this is our compute platform of choice. We then
review the overall code structure followed by usage and functionality once deployed to a vehicle.

# Installation

Installation on a Jetson Nano is relatively straightforward if one uses the SD card image provided. This might be the 
best option for many users since that would bypass having to compile for the Nano the RealSense Python Library and 
eliminate having to deal with certain issues regarding Kivy and its backend. If the user would like to compile things
from scratch off a fresh NVIDIA image, then we have notes of the things we needed to do to create an initial working 
compute platform.

## Option 1: Installing from the MiniAutonomous SD Card Image

If you want to skip the harshness of compiling Kivy and the **pyrealsense2** API to interact with the RealSense camera,
then we highly recommend using the SD card image we have made available. The image has all the required 
libraries installed and/or compiled, and both *engine_ai* and *trainer_ai* can be found in the **Code_Base** 
directory.

The one critical issue that has come up on occasion is that before using the image we provide, it is necessary to go 
through the initial startup process specified by NVIDIA for the Jetson Development Kit. This includes flashing the
base SD image NVIDIA provides, (which at the time of this writing is **JetPack 4.5**), for the Jetson **BEFORE**
re-flashing it with the SD card we provide. 

The initial startup process consists of following the basic steps specified in the following URL:

https://developer.nvidia.com/embedded/learn/get-started-jetson-nano-devkit#write

Once you flash your device with the given JetPack image, download the image we provide and flash the Nano 
as you did originally with the JetPack image. Out SD card image is provided here:

PUT LINK HERE ONCE READY

Disclaimer: We have flashed a number of different Jetson Nanos, (Developer Kit & 2 GB versions), with this image and 
never had an issue, but the Jetson platform has it quirks. If the above doesn't work, go to option 2.

## Option 2: Use the NVIDIA Jetson *JetPack 4.5* Image and Build the Required Libraries on Your Own

If your preference is to build the supporting software stack on your own which is completely understandable, please know
that it's not simply a matter of doing a pip install off of the **requirements.txt** we provide. In fact, we can
guarantee that will not work on the Jetson platform.

For the Jetson, there are two challenging components to install. The first is installing Kivy, and the second
is installing the **pyrealsense** library, which is the more difficult of the two. Let's begin with Kivy.

### Installing Kivy

Our first pass at installing Kivy on the Nano was a series of false starts. The final winning recipe was found in the
Jetson Nano forums by user **devemin**. The original link is below, but here are the required steps:

```
    sudo add-apt-repository ppa:kivy-team/kivy
    sudo apt-get update
    sudo apt-get install python3-kivy
    sudo apt-get install kivy-examples
    
    sudo gedit ~/.bashrc
    
    export KIVY_GL_BACKEND=gl
    export DBUS_FATAL_WARNINGS=0
```
The Forum post where this was extracted from can be found here:

https://forums.developer.nvidia.com/t/kivy-app-fails-on-jetson-nano/77873/2

Please note that there is some debate about using **pygame** or **sdl2** as the backend window provider for Kivy. 
**pygame** is being discontinued, so my vote is for **sdl2**, but the app should load regardless of which of the two
you select. If you decide to go with **sdl2**, thankfully **apt** can help you out.

    sudo apt-get install libsdl2-dev libsdl2-image-dev

You may get some other dependencies that need to be installed, but we had no issues with this component.

   Note: 
      In python/Kivy, the order of your import statements, especially **Tensorflow** libraries and **OpenCV**, matters!
If you start making changes to the source code and for some reason add import statements and move around the current
ones, the result maybe that the Kivy UI will not launch. If that happens, make sure you go back to the original order of 
import statements in the base code. 

### Installing the **pyrealsense** Library

This was the most challenging task we had to get the stack up and running, and word of warning, it took hours for the 
little Jetson ARM processor to compile the install. **engine_ai** has the option of working with a webcam instead, which
should work out of the box once **OpenCV** is installed. The motivation to use the Intel RealSense camera is that it is
a very robust piece of hardware and it has other sensors that you might want to incorporate once you start expanding the
code base. If you would rather avoid the expenditure of purchasing one, skip this step and just install **OpenCV** which
is pretty boilerplate. 

Note: We decided to set the webcam option as the default option when one clones the **engine_ai** repo. If you are 
indeed using the RealSense camera, go to line *82* of the *engine_ai.py* file and set the option to **False**.

Right, let's install the library. After a few false starts, this is the recipe that worked for us. There are two 
fundamental steps: download and compile the RealSense API, and the fix a linking issue that will occur afterwards. 
Based on **FrankCreen's** post in **RealSense** github forum, (https://github.com/IntelRealSense/librealsense/issues/6964),
the critical steps we followed were

1. Update CMake by following the **GOBish** comment in the embedded link:
   ```
       wget http://www.cmake.org/files/v3.13/cmake-3.13.0.tar.gz
       tar xpvf cmake-3.13.0.tar.gz cmake-3.13.0/
       cd cmake-3.13.0/
       ./bootstrap --system-curl
       make -j6 
       echo 'export PATH=/home/nvidia/cmake-3.13.0/bin/:$PATH' >> ~/.bashrc
       source ~/.bashrc
   ```

2. Download the latest release from **RealSense** github portal:
   
   https://github.com/IntelRealSense/librealsense/releases/

   Extract the file in the directory of your choice, decend into it and create a *build* directory.

3. Run CMake in the *build* directory:
```
   make -j4
```
Note: This step will take a long time. We didn't time it, but hours. If you start this late in the day, you may 
wake up a little too early the next morning to find the compile ongoing. 

4. Do the install:
```angular2html
   sudo make install
```
The sudo password for our image is mini123. (Don't tell anybody.)

5. Add the following to the end of your .bashrc file and source it:
```angular2html
export PATH=$PATH:~/.local/bin
export PYTHONPATH=$PYTHONPATH:/usr/local/lib
export PYTHONPATH=$PYTHONPATH:/usr/local/lib/python3.6/pyrealsense2
```

After completing the above, and many big thanks to **FrankCreen** for summarizing this up, we had the following error
come up:

```angular2html
    ERROR [139670256056064] (handle-libusb.h:51) failed to open usb interface: 0, error: RS2_USB_STATUS_ACCESS
```

If this happens to you, we suggest following what **RealSenseSupport** posted in their issues forum,
( https://github.com/IntelRealSense/realsense-ros/issues/1408), which is to copy the rules file found here:
```
   https://github.com/IntelRealSense/librealsense/blob/master/config/99-realsense-libusb.rules
```
to the following directory on the Nano:
```angular2html
   /etc/udev/rules.d/
```
After restarting the Nano post copy, I was able to see the camera feed via 'realsense-viewer'. The first time you start
the viewer, it may ask you to upgrade the camera's firmware. We highly recommend you do that. Once it completes, you 
are ready to use *engine_ai**!

# Code Structure

Our intent in open sourcing this code set is to create a clear and transparent source code that would allow the user
to quickly understand the overall structure of the code and be able to focus on the deep learning components required
to allow  the vehicle to operate autonomously. 

Here is a brief summary of the directories and their contents to orient you as you study the code.

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
**drive_loop**, and can be found on line 173 of **engine_ai.py**.This method should be your starting point
for reviewing the code, and most elements will fall out from its various calls.

Two things we wanted to focus on here is the loading mechanism of trained networks and data recording function.

## Loading Trained Models

**trainer_ai** is the training component of **engine_ai** and a separate README is dedicated to its description.
(Please see its repo here: https://github.com/miniautonomous/trainer_ai.) **trainer_ai** allows for training networks
with sequences, (networks that my have a LSTM, GRU, bi-directional RNN, etc), allowing a model to have state memory, or
without sequences so that the network just takes an image in and produces a steering/throttle output. When the model is
loaded, in the method **load_dnn** on line 510, **engine_ai** reviews the shape of the input tensor and determines if 
the model uses sequences or not. 

In addition, **trainer_ai** can save a model as a standard *Keras* model or as a parsed **TensorRT** model. We highly,
highly recommend you use the parsed **TensorRT** option. This allows the network to run at least 4 to 5 
frames-per-second faster. We have a global variable, **USE_TRT** set to True, but if you are using and Intel NUC as your
compute platform you are going to have to set this to false since at the time of this writing, TensorRT is not available
on that platform.

## Data Recording

Before you actually run in autonomous mode, you are going to have to record data of the task you want the drone to
replicate. To do this, we have developed a threaded implementation of a data logger that uses the **HDF5** file format
to log image data and driver input in terms of throttle and steering. Here is a sample of frame log:

<p align="center">
<img src=./img/hdf5_sample.png width="75%"><p></p>
<p align="center"> Figure 2: A sample frame form an HDF5 file</p>

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
<p align="center"> Figure 3: UI layout and functions</p>

There are three buttons that require input from the user via a keyboard: the Power On/Off button,
the Network Model button, and the Log Folder button. The very step to start the system is to 
power it on via the Power Button. The default state of the vehicle is in manual drive mode, so you should
now be able to drive the drone around as if it was a standard RC car. 

PLEASE NOTE: We highly recommend that when you start the car, have it on a stand with the wheels not making
contact with any surface. Always test responsiveness of the vehicle while the car is on the stand first to ensure you
have full control.

If you have a trained Keras model file or TensorRT parsed model stored in a directory, use the Network Model button
to select it. If you do not have a network model selected, switching the vehicle to autonomous mode will not change
the state of the vehicle: a message in the Information Bar will inform the user to load a network first.

If you want to drive the vehicle and record data, use the Log Folder button to pick the directory where you want to 
store data first before doing the actual recording. 

Please note that the UI will remember your previous selections for the Network Model and Log Folder buttons, so once
you restart the UI and click on those buttons, the UI will default to your last selections.

So now that you have the button options under your belt, it is now time to review what the transmitter controls. Here is
an image of the transmitter we have chosen for *MiniAutonomous*:

<p align="center">
<img src=./img/transmitter.png width="75%"><p></p>
<p align="center"> Figure 4: Transmitter description</p>

When you first start **engine_ai**, the default state of the vehicle will be manual driving. As with standard RC cars,
the throttle trigger and steering wheel will allow you to navigate the drone. Once a log folder has been selected to
store your data, the red rocker switch embedded in the handle of the transmitter will allow you to start and stop
recording: flip it down to start logging and up to stop. A green light will light up in the recording status of the UI
to indicate the vehicle is logging data. Each time you stop/start the logging state, a new **HDF5** will be created, 
recording the RGB coming from the camera along with your steering and throttle inputs.(Please see Figure 2 above.)

Finally, let's focus on autonomy. Say you have taken your data off of the vehicle, uploaded it to a server and used
**trainer_ai** to train a network. You can upload the resulting network to your drone and select it using the Network
Select button on the UI. Usually this takes 20 to 30 seconds for the network to be loaded on the Jetson. Once it is, you
can switch the drive mode of the vehicle from manual to an autonomous state using the three-way switch at the top of the
transmitter. There are two autonomous state: steering autonomous and Full AI, which is steering+throttle. We suggest 
you never throw the switch to Full AI until you have test your network performance out with manual throttle control. 
That will allow you to see how well your model is doing before you actually kick things off. 

In terms of Full AI, we provide two options: either your network controls the throttle or you set a constant velocity 
by setting a PWM value for throttle. The default state of the code is the latter: constant throttle value, but it's a 
key ingredient to train models to both control velocity and steering, so all you have to do is un-comment lines 365 to 
370 of **engine_ai.py** and you will have your throttle control handed over to your trained network.

## *jeston_clocks*: A hidden gem!

So a little hidden gem that is buried deep, (well, not really all that deep), in the Jetson stack is the command
*jetson_clocks*. What does it do, you ask? Well it makes everything run faster. Fundamentally,  it sets the frecquencies
of all compute nodes on the device to the maximum possble setting. We have found that by typing the following in the 
terminal before launching **engine_**,

```angular2html
   sudo jetson_clocks
```
you get a boost of 4 to 5 additional frames-per-second when running inference on the Nano. 

You may be tempted to just put something in your *bashrc* script, but we do note that your power consumption goes way up
when all the clocks are full tilt, so just keep that in mind since it might not be too helpful when manually driving the
car and/or logging data.