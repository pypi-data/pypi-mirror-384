#coding=utf-8
import os
import time
import datetime
import threading
import sys
import numpy as np
import cv2


sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
sys.path.append('../BerxelSdkDriver/')

from BerxelSdkDriver.BerxelHawkContext import *
from BerxelSdkDriver.BerxelHawkDevice import *
from BerxelSdkDriver.BerxelHawkFrame import *
from BerxelSdkDriver.BerxelHawkDefines import *



class HawkIr(object):

    def __init__(self):
        self.__context = None
        self.__device = None
        self.__deviceList = []

    # Step 1 open device
    def openDevice(self):
        self.__context = BerxelHawkContext()

        if self.__context is None:
            print("init failed")
            return  False

        self.__context.initCamera()

        self.__deviceList = self.__context.getDeviceList()

        if len(self.__deviceList) <  1:
            print("can not find device")
            return False

        print("device addres : ", self.__deviceList[0].deviceAddress)
        self.__device = self.__context.openDevice(self.__deviceList[0])

        if self.__device is None:
            return False

        return True

    # Step 2 ： open Stream

    def startStream(self):

        if self.__device is None:
            return  False

        frameMode = self.__device.getCurrentFrameMode(BerxelHawkStreamType.forward_dict['BERXEL_HAWK_IR_STREAM'])
        self.__device.setFrameMode(BerxelHawkStreamType.forward_dict['BERXEL_HAWK_IR_STREAM'] ,frameMode)

        ret = self.__device.startStreams(BerxelHawkStreamType.forward_dict['BERXEL_HAWK_IR_STREAM'])

        if ret == 0:
            print("start stream succeed")
            return True
        else:
            print("start stream failed")
            return False
    # 3: read Frame

    def displayImage(self):

        hawkFrame = self.__device.readIrFrame(30)
        if hawkFrame is None:
            return 1

        width  = hawkFrame.getWidth()
        height = hawkFrame.getHeight()
        streamType = hawkFrame.getStreamType()
        dataSize = hawkFrame.getDataSize()
        pxielType = hawkFrame.getPixelType()
        index = hawkFrame.getFrameIndex()
        frameBuffer = hawkFrame.getDataAsUint16()


        # print("pixel = ", pxielType)
        # print("type = ", streamType)
        # print("frameIndex = ", index)
        # print("fps =" , hawkFrame.getFps())
        # print("w= ", width)
        # print("h =", height)
        # print("datasize = ",dataSize)
        # print(frameBuffer)

        ir_array = np.ndarray(shape=(height, width), dtype=np.uint16, buffer=frameBuffer)
        ir_array_disp = ((ir_array / 10000.) * 255).astype(np.uint8)

        cv2.namedWindow("IR", cv2.WINDOW_AUTOSIZE)
        cv2.imshow('IR', np.uint8(ir_array_disp))

        ch = 0xFF & cv2.waitKey(1)

        if ch == 27 or ch == 81 or ch == 113:
            return -1

        self.__device.releaseFrame(hawkFrame)

        return 1

    def ShowFrame(self):

        print ("Sart Show Frame...")

        time.sleep(1)
        while 1:
            ret = self.displayImage()
            if ret != 1:
                break

        self.closeStream()
        self.clsoeDevice()
        return




    #4 : closeStream
    def closeStream(self):
        if self.__device is None:
            return  False

        ret = self.__device.stopStream(BerxelHawkStreamType.forward_dict['BERXEL_HAWK_IR_STREAM'])

        if ret == 0:
            print("close stream succeed")
            return True
        else:
            print("clsoe stream failed")
            return False

    def clsoeDevice(self):
        if self.__context is None:
            return False

        if self.__device is None:
            return  False

        ret = self.__context.clsoeDevice(self.__device)
        if ret == 0:
            print("clsoe device succeed")
        else:
            print("close device Failed")

        self.__context.destroyCamera()

    def StartTest(self):

        if self.openDevice() == False:
            return
        #
        if self.startStream() == False:
            return

        tShowFrame = threading.Thread(target=self.ShowFrame)
        tShowFrame.start()




if __name__ == '__main__':
    print('PyCharm')
    irView = HawkIr()
    irView.StartTest()
