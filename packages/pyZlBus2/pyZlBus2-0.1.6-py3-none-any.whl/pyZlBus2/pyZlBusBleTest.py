#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import platform
from time import time, sleep
from bleak import BleakClient, BleakScanner
from bleak.backends.characteristic import BleakGATTCharacteristic
from threading import Thread

import pyZlBus2 as zlb


# Serivce Characteristic UUID
CmdCtrl_WriteNotify_UUID = "AEC91001-6E7A-4BC2-9A4C-4CDA7A728F58"   # characteristic
UploadData_Notify_UUID   = "AEC91002-6E7A-4BC2-9A4C-4CDA7A728F58"   # characteristic
TxData_Notify_UUID       = "AEC91003-6E7A-4BC2-9A4C-4CDA7A728F58"   # characteristic

DEBUG = 0

class ZlBusSdk(Thread):
    def __init__(self, advNameStr: str = '', searchStr: str = 'zl', bleScannerPass: bool = False):
        Thread.__init__(self)  # 必须步骤
        if platform.system() == 'Windows':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        self.advNameStr  = advNameStr
        self.searchStr   = searchStr
        self.bFound      = False
        self.bQuit       = False
        self.blueAddr    = ""
        self.findAddr    = {}
        self.client      = None
        self.scannerPass = bleScannerPass
        # step 1, 实例化解包单元,并设置内部解包FIFO大小
        self.pkt = zlb.ZlBusUnPack(tracker_nums = 1, user_id = 0xFF, fifoMaxSize = 10)

        # step 2, 手动设置上传数据流水号编码, 默认FLOW_ID_FORMAT_8
        self.pkt.setFlowIdFormat(zlb.api.e_TK_FlowIdFormat.TK_FLOW_ID_FORMAT_8)

        # step 3, 手动设置上传数据的数据格式，用于解包格式识别，错误的数据格式，无法解包成功，包数据直接丢弃
        # self.pkt.setDataFormat(0, zlb.api.e_Upload_DataFormat.NEW_UPLOAD_DATA_TIME | zlb.api.e_Upload_DataFormat.NEW_UPLOAD_DATA_QUATERNION|
        #                    zlb.api.e_Upload_DataFormat.NEW_UPLOAD_DATA_GYRO | zlb.api.e_Upload_DataFormat.NEW_UPLOAD_DATA_LIN_ACC)
        # or
        # 通过蓝牙获取, 见listenData函数中的如下调用 await client.write_gatt_char(CmdCtrl_WriteNotify_UUID, zlb.api.ul_getDataFormat(), response=True)

    def detection_callback(self, device, advertisement_data):
        if self.advNameStr != '':
            if device.name == self.advNameStr:
                self.blueAddr = device.address
                self.bFound = True
        elif device is not None and device.name is not None:
            if device.name.startswith(self.searchStr) or device.name.startswith(self.searchStr.upper()):
                if device.address in self.findAddr:
                    pass
                else:
                    self.findAddr[device.address] = device.name
                    print(device.name, " | ", device.address)

    def notification_handler(self, characteristic: BleakGATTCharacteristic, data: bytearray):
        if (DEBUG):
            print("low level rev data:",data) 

        try:
            # step 4 将流数据加入进，解包接口
            self.pkt.decodeDataStreamInput(bytes(data))
            # print("size =", self.pkt.count())

            # step 5 查询解包后,FIFO Block个数
            while self.pkt.count() > 0:
                # step 6 获取FIFO Block, 无效Block 或FIFO 中无数据时,返回None
                block =  self.pkt.getHeadBlockNote()
                # print("type(block) =", type(block))
                
                if block != None:
                    if isinstance(block, zlb.ImuDataBlock):
                        print('IMU 数据 类型------------------------------------------------')
                        
                        pktId = block.getIdBlock()
                        print("rfId = ", hex(pktId.rfId), ", flowId =", pktId.flowId)
                        
                        state, timeMs = block.getTimeStamp()
                        if state:
                            print("时间戳[ms]:", timeMs)
                        state, quat = block.getAhrsQuaternion()
                        if state:
                            print("四元数[w x y z]:", quat.element.w, quat.element.x, quat.element.y, quat.element.z)
                        state, euler = block.getAhrsEuler()
                        if state:
                            print("欧拉角[roll pitch yaw]:", euler.angle.roll, euler.angle.pitch, euler.angle.yaw)
                        state, acc = block.getAcc()
                        if state:
                            print("加速度[x y z]:", acc.axis.x, acc.axis.y, acc.axis.z)
                        state, gyro = block.getGyro()
                        if state:
                            print("陀螺仪[x y z]:", gyro.axis.x, gyro.axis.y, gyro.axis.z)
                        state, mag = block.getMag()
                        if state:
                            print("磁力计[x y z]:", mag.axis.x, mag.axis.y, mag.axis.z)
                        state, linAcc = block.getLinAcc()
                        if state:
                            print("线性加速度[x y z]:", linAcc.axis.x, linAcc.axis.y, linAcc.axis.z)
                    elif isinstance(block, zlb.AntValueBlock):
                        print('手指弯曲 数据 类型------------------------------------------------')
                        pktId = block.getIdBlock()
                        print("rfId = ", hex(pktId.rfId), ", flowId =", pktId.flowId)
                        state, antValue = block.getAntValue()
                        if state:
                            print('手指弯曲值:', state, antValue)
                    elif isinstance(block, zlb.BatteryBlock):
                        print('电池 数据 类型------------------------------------------------')
                        pktId = block.getIdBlock()
                        state, mv = block.getAdcMv()
                        print("rfId = ", hex(pktId.rfId))
                        if state:
                            print("电池电压:", mv, "mv")
                        state, level = block.getLevel()
                        if state:
                            print("电池电量:", level, "%")
                    elif isinstance(block, zlb.api.ul_UploadDataFormatBlock):
                        format = block.uploadDataFormat
                        pkId = block.pkId
                        print(f'rfId[{hex(pkId.rfId)}],上报数据格式:{hex(format)}')
                    elif isinstance(block, zlb.api.hl_FlowIdFormatBlock):
                        print('上传数据流水号格式', block.flowIdFormat)
                    else:
                        if isinstance(block, zlb.CtrlBaseBlock):
                            pkId = block.getIdBlock()
                            print("数据类型", type(block))
                            print(f'rfId[{hex(pkId.rfId)}], cmdId[{hex(pkId.cmdId)}],subCmdId[{hex(pkId.subCmdId)}]')
                            print(f'error[{hex(block.isError())}], errCode[{hex(block.getErrCode())}]')
                        else:
                            print("其他数据类型", type(block))
        except Exception as e:
            print(f'数据解析异常 [Error] -> {e}')
            print(data.hex(' '))

    async def findBlue(self, timeout: float = 5.0):
        try:
            print(' 1、搜索Ble设备...')
            self.findAddr.clear()
            self.bFound = False
            self.client = None
            endTime = time() + timeout
            async with BleakScanner(detection_callback = self.detection_callback) as scanner:
                if platform.system() == 'Windows' and self.scannerPass == False:
                    await scanner.start()
                    # pass
                while not self.bFound and time() < endTime:
                    await asyncio.sleep(0.1)

            if  self.advNameStr != '':
                if not self.bFound:
                    print('搜索Ble设备超时 [Error]')
                    print('未搜索到指定设备 [Error]')
                else:
                    print(f'搜索到指定设备 MacAddress: {self.blueAddr}')
        except asyncio.CancelledError as e:
            print(f'搜索Ble设备, 协程工作异常 [Error] -> {e}')
        except Exception as e:
            print(f'搜索Ble设备异常 [Error] -> {e}')

    async def listenData(self):
        try:
            print(' 2、连接BLE设备 + IO Test...')

            async with BleakClient(self.blueAddr) as self.client:
                print('    连接BLE设备成功.')
                await asyncio.sleep(0.2)
                await self.client.start_notify(UploadData_Notify_UUID, self.notification_handler)
                await asyncio.sleep(0.1)
                await self.client.start_notify(CmdCtrl_WriteNotify_UUID, self.notification_handler)
                await asyncio.sleep(0.1)
                await self.client.start_notify(TxData_Notify_UUID, self.notification_handler)
                await asyncio.sleep(0.5)
                await self.client.write_gatt_char(CmdCtrl_WriteNotify_UUID, zlb.api.ul_getDataFormat(), response=True)
                await asyncio.sleep(0.1)
                # await self.client.write_gatt_char(CmdCtrl_WriteNotify_UUID, zlb.api.hl_configOutDataPort(zlb.api.e_DataOutPort.TK_RF_PORT | zlb.api.e_DataOutPort.TK_UART_PORT), response=True)
                await self.client.write_gatt_char(CmdCtrl_WriteNotify_UUID, zlb.api.hl_configOutDataPort(zlb.api.e_DataOutPort.TK_RF_PORT), response=True)
                await asyncio.sleep(0.1)
                while not self.bQuit:
                    await asyncio.sleep(0.1)

                if self.bQuit:
                    await self.client.disconnect()
                self.client = None
        except asyncio.CancelledError as e:
            print(f'连接BLE设备, 协程工作异常 [Error] -> {e}')
            self.client = None
        except Exception as e:
            print(f'连接BLE设备异常 [Error] -> {e}')
            self.client = None

    def getAddr(self):
        return self.blueAddr

    def setAddr(self, addr):
        self.blueAddr = addr

    def setAdvNameStr(self, name):
        self.advNameStr = name

    def find(self):
        try:
            asyncio.run(self.findBlue())
        except asyncio.CancelledError as e:
            print(f' #1、搜索Ble设备, 协程工作异常 [Error] -> {e}')
        except Exception as e:
            print(f' #1、搜索Ble设备异常 [Error] -> {e}')

    def run(self):
        try:
            asyncio.run(self.listenData())
        except asyncio.CancelledError as e:
            print(f' #2、连接BLE设备, 协程工作异常 [Error] -> {e}')
        except Exception as e:
            print(f' #2、连接BLE设备异常 [Error] -> {e}')

    def stop(self):
        self.bQuit = True

    def waitFound(self, timeout:float = 5.0):
        if self.blueAddr is None:
            return False
        endTime = time() + timeout
        while self.bFound == False:
            sleep(0.1)
            if time() > endTime:
                return False
        return True

    def waitConnect(self, timeout:float = 5.0):
        if self.blueAddr is None:
            return False
        endTime = time() + timeout
        while not(self.client is not None and self.client.is_connected):
            print("waitConnect...")
            sleep(0.1)
            if time() > endTime:
                return False
        return True


def bleDemo(advNameStr: str = '', bleScannerPass: bool = False):
    searchStr = (advNameStr[:2] if advNameStr else 'zl')
    icDev = ZlBusSdk(advNameStr, searchStr, bleScannerPass)
    
    if advNameStr == '':
        icDev.find()
        advNameStr = input("输入设备名 或 q 退出: ")
        if advNameStr == 'q' or advNameStr == 'Q' or advNameStr == 'quit':
            return
        else:
            icDev.setAdvNameStr(advNameStr)
    icDev.find()
    if icDev.bFound:
        icDev.start()
        state = icDev.waitConnect()
    else:
        print('未发现设备:', advNameStr)
        return

    if not state:
        print('设备未连接成功')
        return
    
    while True:
        user_input = input("输入'q'退出: ")
        if user_input == 'q' or user_input == 'Q' or user_input == 'quit':
            icDev.stop()
            print("退出程序。")
            break


__all__ = [bleDemo]


if __name__ == '__main__':
    bleDemo()

