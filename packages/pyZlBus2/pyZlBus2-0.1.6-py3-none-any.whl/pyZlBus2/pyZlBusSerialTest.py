#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from serial import Serial   # pip install -U PySerial
from serial.tools import list_ports as sysComList
from queue import Queue
import threading
import time

import pyZlBus2 as zlb

#---------------------------------------------------------------------------------------------
g_bufferQueue = Queue(200)
g_quit = False
g_ser = None
g_pkt = None
#---------------------------------------------------------------------------------------------

# 搜索到串口
def sys_serial_info() -> list:
    com_list = list(sysComList.comports())
    if len(com_list) == 0:
        print("未搜索到串口...")
    else:
        print("系统串口列表如下:")
    for uart in com_list:
        if uart.description.find('蓝牙链接上的标准串行') == -1:
            print(uart)
    print()

# 串口接收线程函数
def receiveThread():
    global g_bufferQueue
    global g_quit
    global g_ser
    while g_quit == False :
        try:
            if g_ser is not None:
                data = g_ser.read_all()
                if len(data) and g_bufferQueue.full() == False:
                    g_bufferQueue.put(data)
                else:
                    time.sleep(0.1)
            else:
                time.sleep(0.2)
        except Exception as e:
            pass

# 串口数据处理线程函数
def processThread():
    global g_bufferQueue
    global g_quit
    global g_ser
    while g_quit == False :
        try:
            data = g_bufferQueue.get(block=True, timeout=0.1)
            if len(data):
                notification_handler(data, g_pkt)
        except Exception as e:
            pass

def serialWrite(data: bytes):
    global g_ser
    if len(data) > 0 and (g_ser != None):
        g_ser.write(data)

#---------------------------------------------------------------------------------------------

def notification_handler(data: bytes, pkt:zlb.ZlBusUnPack = None):
    global g_pkt
    try:
        if pkt is None:
            pkt = g_pkt
        
        # 将流数据加入进，解包接口
        pkt.decodeDataStreamInput(data)
        # print("size =", pkt.count())

        # 查询解包后,FIFO Block个数
        while pkt.count() > 0:
            # 获取FIFO Block, 无效Block 或FIFO 中无数据时,返回None
            block =  pkt.getHeadBlockNote()
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
        # print(data.hex(' '))

#---------------------------------------------------------------------------------------------
def serialDemo():
    global g_quit
    global g_ser
    global g_pkt

    # 实例化解包单元,并设置内部解包FIFO大小
    """
        tracker_nums: 模块数量
        user_id: 用户ID, 多个串口时，用于识别串口
        fifoMaxSize: 解包FIFO大小 >= (tracker_nums * 5)
    """
    g_pkt = zlb.ZlBusUnPack(tracker_nums = 1, user_id = 0xFF, fifoMaxSize = 10)

    # 手动设置上传数据流水号编码, 默认FLOW_ID_FORMAT_8,可忽略该步骤
    # g_pkt.setFlowIdFormat(zlb.api.e_TK_FlowIdFormat.TK_FLOW_ID_FORMAT_8)

    #------------------------------------------------------------------------
    sys_serial_info()
    inputStr = input("输入串口号[例如COM1](无串口号时，直接回车键退出即可): ")

    #------------------------------------------------------------------------
    if inputStr != '' and (inputStr.find('com') or inputStr.find('COM')):
        uartStr = inputStr
    else:
        uartStr = None

    if uartStr:
        g_quit = False
        g_ser = Serial(uartStr, 115200)

        receive_thread = threading.Thread(target=receiveThread)
        receive_thread.start()

        process_thread = threading.Thread(target=processThread)
        process_thread.start()

        # 获取上传数据格式，用于上传数据解析
        serialWrite(zlb.api.ul_getDataFormat())

        time.sleep(1)

        # 将姿态数据调整为串口输出 (开发板确保，接口模式包含UART)
        # write(zlb.api.hl_configOutDataPort(zlb.api.e_DataOutPort.TK_RF_PORT | zlb.api.e_DataOutPort.TK_UART_PORT))
        serialWrite(zlb.api.hl_configOutDataPort(zlb.api.e_DataOutPort.TK_UART_PORT))

        while True:
            user_input = input("\r\n输入'q'退出: ")
            if user_input == 'q' or user_input == 'Q' or user_input == 'quit':
                g_ser.close() # 关闭串口
                g_ser = None
                print("退出程序。")
                break
        g_quit = True
        receive_thread.join()
        process_thread.join()


__all__ = [serialDemo]

if __name__ == '__main__':
    serialDemo()
