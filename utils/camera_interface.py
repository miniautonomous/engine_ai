# def rsIntelDaq(self):
#     """
#       Sub-acquisition method for the Intel Real Sense camera
#     """
#     # --------------------------------- Image capture -------------------------------------
#     # Capture an image from a Intel Real Sense Camera
#     #
#     if self.ui.rsIntelOn:
#         self.uiUtils.initTimer()
#         frames = self.ui.rsPipeline.wait_for_frames()
#         color_frame = frames.get_color_frame()
#         if not color_frame:
#             self.ui.rsIntelOn = False
#
#         self.ui.imgMain = np.asanyarray(color_frame.get_data())
#         # Process the image to display to the user
#         tmpShowImg = np.flipud(self.ui.imgMain)
#         tmpShowImg = tmpShowImg[:, :, [2, 1, 0]]
#         # No need to re-order the colors for this camera
#         # --------------Update the UI texture to display the image to the user---------------
#         self.ui.imgTexture.blit_buffer(tmpShowImg.reshape(self.ui.imgNumPixels * \
#                                                           self.ui.imgWidthFactor))
#         self.ui.canvas.ask_update()  # This is required to have the image refreshed and it
#         # refers to the canvas "stereocam.kv" file
#         # Compute the camera actual frame rate
#         dtFps = self.uiUtils.getTimer()
#         if dtFps == 0:
#             print('rsIntelDaq method: Imaged dropped')
#             dtFps = 1 / 30  # default the FPS to 30 in case a value does NOT get read
#         self.camBufferFPS, fpsAvg = movingAvg(self.camBufferFPS, 1 / dtFps)
#         self.camRealRate = round(fpsAvg, 1)