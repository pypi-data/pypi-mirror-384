#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#====================================================================
# 固件版本支持 V00.92.19.000 以上
#====================================================================
# from typing import Tuple
import ZlBusApi as zlapi
import ctypes
import math

#------------------------------------------------------------------------------------
class CtrlBaseBlock:
    '''
    指令 -> 回复结构
    '''
    def __init__(self, _block:zlapi.ul_CtrlDataBaseBlock = None):
        super().__init__()
        self.block = zlapi.ul_CtrlDataBaseBlock()
        ctypes.memset(ctypes.addressof(self.block), 0, ctypes.sizeof(self.block))

        if _block != None:
            self.block = _block

    def printClassName(self):
        print("CtrlBaseBlock")

    def getIdBlock(self) -> zlapi.xxxIdBlock:
        return self.block.pkId

    def isError(self) -> bool:
        return self.block.error

    def getErrCode(self) -> int:
        return self.block.errCode


class ImuDataBlock:
    def __init__(self, _block:zlapi.ul_ImuDataBlock = None) -> None:
        super().__init__()
        self.block = zlapi.ul_ImuDataBlock()
        ctypes.memset(ctypes.addressof(self.block), 0, ctypes.sizeof(self.block))

        if _block != None:
            self.block = _block

    def printClassName(self):
        print("ImuDataBlock")

    def getIdBlock(self) -> zlapi.xxxIdBlock:
        return self.block.pkId

    def getEffectiveDataFormat(self) -> int:
        '''
        当前时间有效数据映射位(bit位 1:有效 0:无效)
        '''
        return self.block.effectiveDataFormat

    def getTimeStamp(self) -> tuple[bool, float]:
        state = False
        if self.block.effectiveDataFormat & (zlapi.e_Upload_DataFormat.NEW_UPLOAD_DATA_TIME | zlapi.e_Upload_DataFormat.NEW_UPLOAD_DATA_HL_TIME):
            state = True
        return (state, 0.0 if math.isnan(self.block.timeStamp) else self.block.timeStamp)

    def getTemperature(self) -> tuple[bool, float]:
        state = False
        if self.block.effectiveDataFormat & zlapi.e_Upload_DataFormat.NEW_UPLOAD_DATA_TEMP:
            state = True
        return (state, self.block.temperature)
    
    def getAhrsQuaternion(self) -> tuple[bool, zlapi.AhrsQuaternion]:
        state = False
        if self.block.effectiveDataFormat & zlapi.e_Upload_DataFormat.NEW_UPLOAD_DATA_QUATERNION:
            state = True
        return (state, self.block.quat)

    def getAhrsEuler(self) -> tuple[bool, zlapi.AhrsEuler]:
        state = False
        if self.block.effectiveDataFormat & zlapi.e_Upload_DataFormat.NEW_UPLOAD_DATA_RPY:
            state = True
        return (state, self.block.euler)

    def getAcc(self) -> tuple[bool, zlapi.Axis3_Float]:
        state = False
        if self.block.effectiveDataFormat & zlapi.e_Upload_DataFormat.NEW_UPLOAD_DATA_ACC:
            state = True
        return (state, self.block.acc)

    def getGyro(self) -> tuple[bool, zlapi.Axis3_Float]:
        state = False
        if self.block.effectiveDataFormat & zlapi.e_Upload_DataFormat.NEW_UPLOAD_DATA_GYRO:
            state = True
        return (state, self.block.gyro)

    def getMag(self) -> tuple[bool, zlapi.Axis3_Float]:
        state = False
        if self.block.effectiveDataFormat & zlapi.e_Upload_DataFormat.NEW_UPLOAD_DATA_MAG:
            state = True
        return (state, self.block.mag)

    def getLinAcc(self) -> tuple[bool, zlapi.Axis3_Float]:
        state = False
        if self.block.effectiveDataFormat & zlapi.e_Upload_DataFormat.NEW_UPLOAD_DATA_LIN_ACC:
            state = True
        return (state, self.block.lineAcc)


class UpLoadDeviceStateBlock:
    """
    模块(IC)主动上报
    """
    def __init__(self, _block:zlapi.ul_DeviceStateBlock = None) -> None:
        super().__init__()
        self.block = zlapi.ul_DeviceStateBlock()
        ctypes.memset(ctypes.addressof(self.block), 0, ctypes.sizeof(self.block))

        if _block != None:
            self.block = _block
    
    def printClassName(self):
        print("UpLoadDeviceStateBlock")

    def getIdBlock(self) -> zlapi.xxxIdBlock:
        return self.block.pkId
    
    def getDeviceState(self) -> int:
        return self.block.deviceState


class BatteryBlock:
    def __init__(self, _block:zlapi.ul_BatteryBlock = None) -> None:
        super().__init__()
        self.block = zlapi.ul_BatteryBlock()
        ctypes.memset(ctypes.addressof(self.block), 0, ctypes.sizeof(self.block))

        if _block != None:
            self.block = _block

    def printClassName(self):
        print("BatteryBlock")

    def getIdBlock(self) -> zlapi.xxxIdBlock:
        return self.block.pkId

    def getAdcMv(self) -> tuple[bool, int]:
        return (self.block.mvOk, self.block.mv)

    def getLevel(self) -> tuple[bool, int]:
        return  (self.block.levelOk, self.block.level)


class AntValueBlock:
    def __init__(self, _block:zlapi.ul_AntValueBlock = None) -> None:
        super().__init__()
        self.block = zlapi.ul_AntValueBlock()
        ctypes.memset(ctypes.addressof(self.block), 0, ctypes.sizeof(self.block))

        if _block != None:
            self.block = _block

    def printClassName(self):
        print("AntValueBlock")

    def getIdBlock(self) -> zlapi.xxxIdBlock:
        return self.block.pkId

    def getAntNum(self) -> int:
        return self.block.antNums

    def getEffectiveDataFormat(self) -> int:
        '''
        当前时间有效数据映射位(bit位 1:有效 0:无效)
        '''
        return self.block.effectiveDataFormat

    def getTimeStamp(self) -> tuple[bool, float]:
        state = False
        if self.block.effectiveDataFormat & (zlapi.e_Upload_DataFormat.NEW_UPLOAD_DATA_TIME | zlapi.e_Upload_DataFormat.NEW_UPLOAD_DATA_HL_TIME):
            state = True
        return (state, 0.0 if math.isnan(self.block.timeStamp) else self.block.timeStamp)
    
    def isNormalization(self):
        return self.block.normalization
    
    def getAntValue(self) -> tuple[bool, tuple]:
        state = False
        if self.block.effectiveDataFormat & zlapi.e_Upload_DataFormat.NEW_UPLOAD_DATA_ADCx:
            state = True
        return (state, tuple(self.block.antValue[:self.block.antNums]))


class DongleScanBlock:
    def __init__(self, _block:zlapi.DL_ScanBlock = None) -> None:
        super().__init__()
        self.block = zlapi.DL_ScanBlock()
        ctypes.memset(ctypes.addressof(self.block), 0, ctypes.sizeof(self.block))

        if _block != None:
            self.block = _block

    def printClassName(self):
        print("DongleScanBlock")

    def getIdBlock(self) -> zlapi.xxxIdBlock:
        return self.block.pkId
    
    def getMac(self) -> bytes:
        return bytes(self.block.mac)

    def getName(self) -> str:
        return bytes(self.block.name).split(b'\0', 1)[0].decode('utf-8', errors='ignore')


class DongleTimeStampSyncBlock:
    def __init__(self, _block:zlapi.DL_TimeStampSyncBlock = None) -> None:
        super().__init__()
        self.block = zlapi.DL_TimeStampSyncBlock()
        ctypes.memset(ctypes.addressof(self.block), 0, ctypes.sizeof(self.block))

        if _block != None:
            self.block = _block

    def printClassName(self):
        print("DongleTimeStampSyncBlock")

    def getIdBlock(self) -> zlapi.xxxIdBlock:
        return self.block.pkId
    
    def getTimeStamp(self) -> float:
        return 0.0 if math.isnan(self.block.timeStamp) else self.block.timeStamp


#================================================================================================

class ZlBusUnPack:
    def __init__(self, tracker_nums:int = 1, user_id:int = 0xFF, fifoMaxSize:int = 10):
        # 创建解码器句柄： self.ddb
        self.ddb = zlapi.ul_dataDecodeBlockCreate(tracker_nums = tracker_nums, user_id = user_id, max_nums = fifoMaxSize)
        
        self.blockId_map = {
            # e_BlockID
            zlapi.e_BlockID.BlockID_OK : (zlapi.ul_CtrlDataBaseBlock, ctypes.sizeof(zlapi.ul_CtrlDataBaseBlock), self.__getCtrlBaseBlockNote),
            zlapi.e_BlockID.BlockID_ERROR : (zlapi.ul_CtrlDataBaseBlock, ctypes.sizeof(zlapi.ul_CtrlDataBaseBlock), self.__getCtrlBaseBlockNote),

            # e_BlockID_DataExport
            zlapi.e_BlockID_DataExport.BlockID_00001000 : (zlapi.ul_ImuDataBlock, ctypes.sizeof(zlapi.ul_ImuDataBlock), self.__getImuDataBlockNote),
            zlapi.e_BlockID_DataExport.BlockID_00001100 : (zlapi.ul_DeviceStateBlock, ctypes.sizeof(zlapi.ul_DeviceStateBlock), self.__getUpLoadDeviceStateBlockNote),
            zlapi.e_BlockID_DataExport.BlockID_00001400 : (zlapi.ul_BatteryBlock, ctypes.sizeof(zlapi.ul_BatteryBlock), self.__getBatteryBlockNote),
            zlapi.e_BlockID_DataExport.BlockID_00001500 : (zlapi.ul_AntValueBlock, ctypes.sizeof(zlapi.ul_AntValueBlock), self.__getAntValueBlockNote),

            # e_BlockID_UL
            zlapi.e_BlockID_UL.BlockID_0000D501 : (zlapi.ul_UploadDataFormatBlock, ctypes.sizeof(zlapi.ul_UploadDataFormatBlock), None),
            zlapi.e_BlockID_UL.BlockID_0000D503 : (zlapi.ul_SamplingHzBlock, ctypes.sizeof(zlapi.ul_SamplingHzBlock), None),
            zlapi.e_BlockID_UL.BlockID_0000D505 : (zlapi.ul_UploadHzBlock, ctypes.sizeof(zlapi.ul_UploadHzBlock), None),
            zlapi.e_BlockID_UL.BlockID_0000D50B : (zlapi.ul_FilterMapBlock, ctypes.sizeof(zlapi.ul_FilterMapBlock), None),
            zlapi.e_BlockID_UL.BlockID_0000D50D : (zlapi.ul_IcDirBlock, ctypes.sizeof(zlapi.ul_IcDirBlock), None),
            zlapi.e_BlockID_UL.BlockID_0000D50F : (zlapi.ul_DevieRfNameBlock, ctypes.sizeof(zlapi.ul_DevieRfNameBlock), None),
            zlapi.e_BlockID_UL.BlockID_0000D511 : (zlapi.ul_RfPowerBlock, ctypes.sizeof(zlapi.ul_RfPowerBlock), None),
            zlapi.e_BlockID_UL.BlockID_0000D563 : (zlapi.ul_RgbDataBlock, ctypes.sizeof(zlapi.ul_RgbDataBlock), None),
            zlapi.e_BlockID_UL.BlockID_0000D565 : (zlapi.ul_UartBaudRateBlock, ctypes.sizeof(zlapi.ul_UartBaudRateBlock), None),
            zlapi.e_BlockID_UL.BlockID_0000D567 : (zlapi.ul_BlockSizeBlock, ctypes.sizeof(zlapi.ul_BlockSizeBlock), None),
            zlapi.e_BlockID_UL.BlockID_0000D577 : (zlapi.ul_DeviceMacBlock, ctypes.sizeof(zlapi.ul_DeviceMacBlock), None),
            zlapi.e_BlockID_UL.BlockID_0000D579 : (zlapi.ul_DeviceSnFullStrBlock, ctypes.sizeof(zlapi.ul_DeviceSnFullStrBlock), None),
            zlapi.e_BlockID_UL.BlockID_0000D57B : (zlapi.ul_DeviceBoardVersionBlock, ctypes.sizeof(zlapi.ul_DeviceBoardVersionBlock), None),
            zlapi.e_BlockID_UL.BlockID_0000D57D : (zlapi.ul_DeviceFirmwareVersionBlock, ctypes.sizeof(zlapi.ul_DeviceFirmwareVersionBlock), None),

            # e_BlockID_UHL
            zlapi.e_BlockID_UHL.BlockID_0000D603 : (zlapi.hl_DotIdBlock, ctypes.sizeof(zlapi.hl_DotIdBlock), None),
            zlapi.e_BlockID_UHL.BlockID_0000D607 : (zlapi.hl_BleConnIntervalBlock, ctypes.sizeof(zlapi.hl_BleConnIntervalBlock), None),
            zlapi.e_BlockID_UHL.BlockID_0000D611 : (zlapi.hl_AccRangeBlock, ctypes.sizeof(zlapi.hl_AccRangeBlock), None),
            zlapi.e_BlockID_UHL.BlockID_0000D613 : (zlapi.hl_GyroRangeBlock, ctypes.sizeof(zlapi.hl_GyroRangeBlock), None),
            zlapi.e_BlockID_UHL.BlockID_0000D61B : (zlapi.hl_MagEllipsoidCalParamBlock, ctypes.sizeof(zlapi.hl_MagEllipsoidCalParamBlock), None),
            zlapi.e_BlockID_UHL.BlockID_0000D621 : (zlapi.hl_FlowIdFormatBlock, ctypes.sizeof(zlapi.hl_FlowIdFormatBlock), None),
            zlapi.e_BlockID_UHL.BlockID_0000D62B : (zlapi.hl_AhrsOffsetBlock, ctypes.sizeof(zlapi.hl_AhrsOffsetBlock), None),
            zlapi.e_BlockID_UHL.BlockID_0000D631 : (zlapi.hl_DataPortBlock, ctypes.sizeof(zlapi.hl_DataPortBlock), None),
            zlapi.e_BlockID_UHL.BlockID_0000D633 : (zlapi.hl_DataPortMapBlock, ctypes.sizeof(zlapi.hl_DataPortMapBlock), None),
            zlapi.e_BlockID_UHL.BlockID_0000D635 : (zlapi.hl_DeviceStateBlock, ctypes.sizeof(zlapi.hl_DeviceStateBlock), None),
            zlapi.e_BlockID_UHL.BlockID_0000D641 : (zlapi.hl_AntFilterParamBlock, ctypes.sizeof(zlapi.hl_AntFilterParamBlock), None),
            zlapi.e_BlockID_UHL.BlockID_0000D643 : (zlapi.hl_FingerMapBlock, ctypes.sizeof(zlapi.hl_FingerMapBlock), None),

            # e_BlockID_UDG
            zlapi.e_BlockID_UDG.BlockID_0000C001 : (zlapi.DL_DongleSnFullStrBlock, ctypes.sizeof(zlapi.DL_DongleSnFullStrBlock), None),
            zlapi.e_BlockID_UDG.BlockID_0000C007 : (zlapi.DL_DeviceBoardVersionBlock, ctypes.sizeof(zlapi.DL_DeviceBoardVersionBlock), None),
            zlapi.e_BlockID_UDG.BlockID_0000C008 : (zlapi.DL_DeviceFirmwareVersionBlock, ctypes.sizeof(zlapi.DL_DeviceFirmwareVersionBlock), None),
            zlapi.e_BlockID_UDG.BlockID_0000C011 : (zlapi.DL_DeviceListBlock, ctypes.sizeof(zlapi.DL_DeviceListBlock), None),
            zlapi.e_BlockID_UDG.BlockID_0000C013 : (zlapi.DL_DeviceConnNumsBlock, ctypes.sizeof(zlapi.DL_DeviceConnNumsBlock), None),
            zlapi.e_BlockID_UDG.BlockID_0000C021 : (zlapi.DL_IdentifyWayBlock, ctypes.sizeof(zlapi.DL_IdentifyWayBlock), None),
            
            # e_BlockID_FDG
            zlapi.e_BlockID_FDG.BlockID_0000C000 : (zlapi.DL_ScanBlock, ctypes.sizeof(zlapi.DL_ScanBlock), self.__getDongleScanBlockNote),
            zlapi.e_BlockID_FDG.BlockID_0000C000 : (zlapi.DL_TimeStampSyncBlock, ctypes.sizeof(zlapi.DL_TimeStampSyncBlock), self.__getDongleTimeStampSyncBlockNote),
        }

    def __del__(self):
        """
        销毁解码器句柄。
        """
        zlapi.ul_dataDecodeBlockDelete(self.ddb)

    #==============================================================================================
    # 解码数据输入口
    def decodeDataStreamInput(self, data:bytes) -> int:
        '''
        将收到的原始字节流送入解码器，解码后的数据节点追加到链表中。
        '''
        return zlapi.ul_dataBlockDecode(self.ddb, data)

    # 清空数据链表
    def clear(self) -> int:
        return zlapi.ul_dataBlockNoteClear(self.ddb)

    def size(self) -> int:
        '''
        数据链表中,节点个数
        '''
        return zlapi.ul_dataBlockNoteSize(self.ddb)
    
    def count(self) -> int:
        '''
        数据链表中,节点个数
        '''
        return zlapi.ul_dataBlockNoteSize(self.ddb)

    def length(self) -> int:
        '''
        数据链表中,节点个数
        '''
        return zlapi.ul_dataBlockNoteSize(self.ddb)

    def getHeadBlockId(self) -> int:
        '''
        从数据链表中，读取头节点 blockId,从而确定ul_getDataNote_Del中 block参数 和 blockSize参数
        '''
        return (zlapi.ul_dataBlockGetBlockID(self.ddb) & 0xFFFFFFFF)

    def removeHeadDataNote(self) -> None:
        '''
        从数据列表中，删除错误的头节点
        '''
        zlapi.ul_dataBlockSkipNote(self.ddb)
        return None

    def getHeadBlockNote(self, blockId: int = None):
        if self.size() > 0:
            if blockId == None:
                blockId = self.getHeadBlockId()

            if blockId in self.blockId_map:
                decode_data = zlapi.ul_dataBlockReadNote(self.ddb, self.blockId_map[blockId][1])
                if self.blockId_map[blockId][2] is None:
                    return self.blockId_map[blockId][0].from_buffer_copy(decode_data)
                else:
                    return self.blockId_map[blockId][2](decode_data)
            else:
                return self.removeHeadDataNote()
        else:
            return None
    
    #==============================================================================================

    # 手动设置上报数据，数据格式 (self.ddb 结构中的上报数据格式)
    def setDataFormat(self, tkIndex:int =  0, dataFormat:int = 0) -> int:
        return zlapi.ul_manualModifyDataFormat(self.ddb, tkIndex, dataFormat)

    # 手动设置上报数据，流水号格式 (self.ddb 结构中的流水号格式)
    def setFlowIdFormat(self, flowIdFormat:int) -> int:
        return zlapi.ul_manualModifyDataFlowIdFormat(self.ddb, flowIdFormat)

    # 获取流水号格式(self.ddb 结构中的流水号格式)
    def getFlowIdFormat(self) -> int:
        return zlapi.ul_getDataFlowIdFormat(self.ddb)
    
    #==============================================================================================

    def __getCtrlBaseBlockNote(self, decode_data: bytes) -> CtrlBaseBlock:
        return CtrlBaseBlock(zlapi.ul_CtrlDataBaseBlock.from_buffer_copy(decode_data))

    def __getImuDataBlockNote(self, decode_data: bytes) -> ImuDataBlock:
        return ImuDataBlock(zlapi.ul_ImuDataBlock.from_buffer_copy(decode_data))

    def __getUpLoadDeviceStateBlockNote(self, decode_data: bytes) -> UpLoadDeviceStateBlock:
        return UpLoadDeviceStateBlock(zlapi.ul_DeviceStateBlock.from_buffer_copy(decode_data))

    def __getBatteryBlockNote(self, decode_data: bytes) -> BatteryBlock:
        return BatteryBlock(zlapi.ul_BatteryBlock.from_buffer_copy(decode_data))

    def __getAntValueBlockNote(self, decode_data: bytes) -> AntValueBlock:
        return AntValueBlock(zlapi.ul_AntValueBlock.from_buffer_copy(decode_data))

    def __getDongleScanBlockNote(self, decode_data: bytes) -> DongleScanBlock:
        return DongleScanBlock(zlapi.DL_ScanBlock.from_buffer_copy(decode_data))

    def __getDongleTimeStampSyncBlockNote(self, decode_data: bytes) -> DongleTimeStampSyncBlock:
        return DongleTimeStampSyncBlock(zlapi.DL_TimeStampSyncBlock.from_buffer_copy(decode_data))

__all__ = [
    "CtrlBaseBlock",
    "ImuDataBlock",
    "UpLoadDeviceStateBlock",
    "BatteryBlock",
    "AntValueBlock",
    "DongleScanBlock",
    "DongleTimeStampSyncBlock",
    "ZlBusUnPack",
]

#================================================================================================
# 指令回复结构
#================================================================================================
# block = zlapi.ul_CtrlDataBaseBlock()
# print("block.error =", block.error)
# print("block.errCode =", block.errCode)

# block = zlapi.ul_UploadDataFormatBlock()
# print("block.uploadDataFormat =", block.uploadDataFormat)

# block = zlapi.ul_SamplingHzBlock()
# print("block.samplingHz =", block.samplingHz)

# block = zlapi.ul_UploadHzBlock()
# print("block.UploadHz =", block.UploadHz)

# block = zlapi.ul_IcDirBlock()
# print("block.icDir =", block.icDir)

# block = zlapi.ul_DevieRfNameBlock()
# print("block.name =", bytes(block.name).split(b'\0', 1)[0].decode('utf-8', errors='ignore'))

# block = zlapi.ul_RfPowerBlock()
# print("block.rssi =", block.rssi)

# block = zlapi.ul_RgbDataBlock()
# print("block.color =", block.color)
# print("block.mode =", block.mode)

# block = zlapi.ul_UartBaudRateBlock()
# print("block.baudRate =", block.baudRate)

# block = zlapi.ul_BlockSizeBlock()
# print("block.type =", block.type)
# print("block.blockSize =", block.blockSize)

# block = zlapi.ul_DeviceMacBlock()
# print("block.mac =", block.mac.hex(' '))

# block = zlapi.ul_DeviceSnFullStrBlock()
# print("block.snFullStr =", bytes(block.snFullStr).split(b'\0', 1)[0].decode('utf-8', errors='ignore'))

# block = zlapi.ul_DeviceBoardVersionBlock()
# print("block.boardVersion =", bytes(block.boardVersion).split(b'\0', 1)[0].decode('utf-8', errors='ignore'))

# block = zlapi.ul_DeviceFirmwareVersionBlock()
# print("block.firmwareVersion =", bytes(block.firmwareVersion).split(b'\0', 1)[0].decode('utf-8', errors='ignore'))
