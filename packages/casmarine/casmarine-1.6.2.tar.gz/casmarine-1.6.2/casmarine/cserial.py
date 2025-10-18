import time
import enum
from crccheck.crc import Crc32Mpeg2 as CRC32
from ctypes import *
import struct
import serial
import requests
import tempfile
from stm32loader.main import main as stm32loader_main

Index = enum.IntEnum('Index', [
    'HeaderL',
    'HeaderH',
    'PackageSize',
    'Command', 
    'Reset', 
    'JoystickButtonHome',
    'ResetDepth',
    'ResetAxis',
    'JoystickButtonPidOn',
    'JoystickButtonPidOff', 
    'FrontLightsOn',
    'FrontLightsOff', 
    'DownLightsOn',
    'DownLigthsOff',
    'Cakar',
    'DeadZoneOnOff', 
    'CorrectiveHead',
    'CorrectiveDepth',
    'GoToDestination',
    'CalibrationOk',
    'SysStatus',
    'GyroStatus',
    'AccStatus',
    'MagStatus',
    'MeasureDepth',
    'ControlDataX', 
    'ControlDataY', 
    'ControlDataZ', 
    'ControlDataH', 
    'ControlDataR', 
    'ControlDataP',
    'AccelX',
    'AccelY',
    'AccelZ',
    'MagX',
    'MagY',
    'MagZ',
    'GyroX',
    'GyroY',
    'GyroZ',
    'AccelRadius',
    'MagRadius',
    'RollPIDP', 
    'RollPIDI', 
    'RollPIDD', 
    'PitchPIDP', 
    'PitchPIDI', 
    'PitchPIDD', 
    'HeadPIDP', 
    'HeadPIDI', 
    'HeadPIDD', 
    'DepthPIDP', 
    'DepthPIDI', 
    'DepthPIDD',
    'RollError' ,
    'PitchError' ,
    'HeadError' ,
    'DepthError' ,
    'HeadAngle', 
    'PitchAngle',
    'RollAngle',
    'QuaAngleX',
    'QuaAngleY',
    'QuaAngleZ',
    'QuaAngleW',
    'ImuTemp',   
    'Pressure', 
    'Temperature',
    'DepthPosition',
    'PitchSetPoint',
    'RollSetPoint',
    'HeadSetPoint',
    'DepthSetPoint',
    'YSmooth',
    'Destination',
    'VelocityParam',
    'CRC',
], start = 0
)


class Commands(enum.IntEnum):
    PING = 0,
    BL_JUMP = 1 ,
    RESTART = 1 << 1,


class _Data():
    def __init__(self, index, type: str, value=0, rw=True) -> None:
        self.__index = int(index)
        self.__value = value
        self.__type = type
        self.__rw = rw
        self.__size = struct.calcsize(type)

    def value(self, value=None):
        if value is None:
            return self.__value
        elif self.__rw:
            self.__value = struct.unpack('<' + self.__type, struct.pack('<' + self.__type, value))[0]

    def index(self) -> enum.IntEnum:
        return self.__index

    def type(self) -> str:
        return self.__type

    def size(self) -> int:
        return self.__size


class Protocol():
    CONST_DATA_SIZE = 8
    __RELEASE_URL = "https://github.com/CASMarine/CASXII_MB_FW_FILE/raw/master/CASXII_MotherBoard_V1.0.0.bin"

    def __init__(self, baud=115200, port='/dev/ttyTHS1') -> None:
        self.__ser = serial.Serial(port=port, baudrate=baud, timeout=0.1)
        self.__ack_size = 0
        self.__post_time_sleep = 15 / baud
        self.connecting_control = False
        self.variables = [
            _Data(Index.HeaderL, 'B', 0x59, rw=False),
            _Data(Index.HeaderH, 'B', 0x73, rw=False),
            _Data(Index.PackageSize, 'B'),
            _Data(Index.Command, 'B'),
            _Data(Index.Reset, 'B'),
            _Data(Index.JoystickButtonHome, 'B'),
            _Data(Index.ResetDepth, 'B'),
            _Data(Index.ResetAxis, 'B'),
            _Data(Index.JoystickButtonPidOn, 'B'),
            _Data(Index.JoystickButtonPidOff, 'B'),
            _Data(Index.FrontLightsOn, 'B'),
            _Data(Index.FrontLightsOff, 'B'),
            _Data(Index.DownLightsOn, 'B'),
            _Data(Index.DownLigthsOff, 'B'),
            _Data(Index.Cakar, 'B'),
            _Data(Index.DeadZoneOnOff, 'B'),
            _Data(Index.CorrectiveHead, 'h'),
            _Data(Index.CorrectiveDepth, 'h'),
            _Data(Index.GoToDestination, 'f'),
            _Data(Index.CalibrationOk, 'B'),
            _Data(Index.SysStatus, 'B'),
            _Data(Index.GyroStatus, 'B'),
            _Data(Index.AccStatus, 'B'),
            _Data(Index.MagStatus, 'B'),
            _Data(Index.MeasureDepth, 'B'),
            _Data(Index.ControlDataX, 'b'),
            _Data(Index.ControlDataY, 'b'),
            _Data(Index.ControlDataZ, 'b'),
            _Data(Index.ControlDataH, 'b'),
            _Data(Index.ControlDataR, 'b'),
            _Data(Index.ControlDataP, 'b'),
            _Data(Index.AccelX, 'h'),
            _Data(Index.AccelY, 'h'),
            _Data(Index.AccelZ, 'h'),
            _Data(Index.MagX, 'h'),
            _Data(Index.MagY, 'h'),
            _Data(Index.MagZ, 'h'),
            _Data(Index.GyroX, 'h'),
            _Data(Index.GyroY, 'h'),
            _Data(Index.GyroZ, 'h'),
            _Data(Index.AccelRadius, 'h'),
            _Data(Index.MagRadius, 'h'),
            _Data(Index.RollPIDP, 'f'),
            _Data(Index.RollPIDI, 'f'),
            _Data(Index.RollPIDD, 'f'),
            _Data(Index.PitchPIDP, 'f'),
            _Data(Index.PitchPIDI, 'f'),
            _Data(Index.PitchPIDD, 'f'),
            _Data(Index.HeadPIDP, 'f'),
            _Data(Index.HeadPIDI, 'f'),
            _Data(Index.HeadPIDD, 'f'),
            _Data(Index.DepthPIDP, 'f'),
            _Data(Index.DepthPIDI, 'f'),
            _Data(Index.DepthPIDD, 'f'),
            _Data(Index.RollError, 'f'),
            _Data(Index.PitchError, 'f'),
            _Data(Index.HeadError, 'f'),
            _Data(Index.DepthError, 'f'),
            _Data(Index.HeadAngle, 'f'),
            _Data(Index.PitchAngle, 'f'),
            _Data(Index.RollAngle, 'f'),
            _Data(Index.QuaAngleX, 'f'),
            _Data(Index.QuaAngleY, 'f'),
            _Data(Index.QuaAngleZ, 'f'),
            _Data(Index.QuaAngleW, 'f'),
            _Data(Index.ImuTemp, 'f'),
            _Data(Index.Pressure, 'f'),
            _Data(Index.Temperature, "f"),
            _Data(Index.DepthPosition, 'f'),
            _Data(Index.PitchSetPoint, 'f'),
            _Data(Index.RollSetPoint, 'f'),
            _Data(Index.HeadSetPoint, 'f'),
            _Data(Index.DepthSetPoint, 'f'),
            _Data(Index.YSmooth, 'f'),
            _Data(Index.Destination, 'f'),
            _Data(Index.VelocityParam, 'f'),
            _Data(Index.CRC, 'I'),
        ]

    def __write_bus(self, data):
        self.__ser.write(data)

    def __read_bus(self, byte_count):
        data = self.__ser.read(byte_count)
        # print(list(data))
        if (len(data) == byte_count):
            # print(data)
            return data
        return None

    def get_ack_size(self) -> int:
        return self.__ack_size

    def set_variables_command(self, idx_list = []):
        fmt_str = ''
        for idx in idx_list:
            fmt_str += 'B'
        struct_out_command = (struct.pack(fmt_str, *[int((index << 1) + 1) for index in idx_list]))
        struct_out_command = list(struct_out_command)
        return struct_out_command


    def set_variables(self, idx_list=[], value_list=[]):

        fmt_str = ''.join([var.type() for var in self.variables[:3]])
        for idx, value in zip(idx_list, value_list):
            self.variables[int(idx)].value(value)
            fmt_str += 'B' + self.variables[int(idx)].type()

        struct_out = [var.value() for var in self.variables[:3]]

        for idx in idx_list:
                struct_out += [*[int((idx << 1) + 1), self.variables[int(idx)].value()]]

        struct_out_set = list(struct.pack('<' + fmt_str, *struct_out))

        return struct_out_set

    def get_variables(self, id_list: list):
        fmt_str = ''
        fmt_str_size = ''

        for idx in id_list:
            fmt_str += 'B'
            fmt_str_size += self.variables[int(idx)].type()

        
        struct_out_get = (struct.pack(fmt_str, *[int(index << 1) for index in id_list]))

        crc_size = self.variables[int(Index.CRC)].size()  

        self.__ack_size = self.calculate_struct_size(fmt_str_size) + crc_size + len(id_list) + 3
        
        struct_out_get = list(struct_out_get)

        return struct_out_get

    def calculate_struct_size(self, fmt: str) -> int:
        format_sizes = {
            'b': 1, 'B': 1,
            'h': 2, 'H': 2,
            'i': 4, 'I': 4,
            'f': 4,
        }

        total_size = 0
        i = 0
        while i < len(fmt):
            count_str = ''
            while i < len(fmt) and fmt[i].isdigit():
                count_str += fmt[i]
                i += 1
            count = int(count_str) if count_str else 1

            if i >= len(fmt):
                raise ValueError("Invalid format string")

            fmt_char = fmt[i]
            if fmt_char not in format_sizes:
                raise ValueError(f"Unknown format character: {fmt_char}")
            total_size += count * format_sizes[fmt_char]
            i += 1

        return total_size


        

    def create_mb_pack(self, idx_list_set=[], value_list_set=[], idx_list_get=[], idx_list_command=[]):
        struct_out_set = self.set_variables(idx_list_set, value_list_set)
        struct_out_get = self.get_variables(idx_list_get)
        struct_out_command = self.set_variables_command(idx_list_command)
        struct_out = struct_out_set + struct_out_get + struct_out_command
        struct_out[int(Index.PackageSize)] = len(struct_out) + self.variables[int(Index.CRC)].size()
        self.variables[int(Index.CRC)].value(CRC32.calc(struct_out))
        struct_out = bytes(struct_out) + struct.pack('<' + self.variables[int(Index.CRC)].type(),
                                                     self.variables[int(Index.CRC)].value())
        self.__write_bus(struct_out)


    def unpack_mb_packed(self, id_list: list):
        if self.read_ack():
            pass

    def read_ack(self) -> bool:
        ret = self.__read_bus(self.get_ack_size())
        # print(ret)
        if ret is None or len(ret) == 0:
            return False
        if len(ret) == self.get_ack_size():
            if (CRC32.calc(ret[:-4]) == struct.unpack('<I', ret[-4:])[0]):
                if ret[int(Index.PackageSize)] >= self.__class__.CONST_DATA_SIZE:
                    self.parse_received(ret)
                    self.connecting_control = True
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False

    def parse_received(self, data):
        data = data[3:-4]
        fmt_str = '<'

        i = 0
        while i < len(data):
            fmt_str += 'B' + self.variables[int(data[i])].type()
            i += self.variables[int(data[i])].size() + 1

        unpacked = list(struct.unpack(fmt_str, data))
        grouped = zip(*(iter(unpacked),) * 2)
        for group in grouped:
            self.variables[group[0]].value(group[1])

    def ping(self) -> bool:
        self.variables[int(Index.Command)].value(Commands.PING)
        fmt_str = ''.join([var.type() for var in self.variables[:4]])
        self.__ack_size = struct.calcsize(fmt_str) + self.variables[int(Index.CRC)].size()
        struct_out = [var.value() for var in self.variables[:4]]
        struct_out = list(struct.pack('<' + fmt_str, *struct_out))
        struct_out[int(Index.PackageSize)] = len(struct_out) + self.variables[int(Index.CRC)].size()
        self.variables[int(Index.CRC)].value(CRC32.calc(struct_out))
        data = bytes(struct_out) + struct.pack('<' + self.variables[int(Index.CRC)].type(), self.variables[int(Index.CRC)].value())
        self.__write_bus(data)
        pre_xfer_time = time.time()
        is_alive = self.read_ack()
        post_xfer_time = time.time()
        print("connection is {}, got {} bytes,  time={}".format(is_alive, self.__ack_size, post_xfer_time - pre_xfer_time))
        return is_alive
        
    def reboot(self):
        self.variables[int(Index.Command)].value(Commands.RESTART)
        fmt_str = ''.join([var.type() for var in self.variables[:4]])
        struct_out = [var.value() for var in self.variables[:4]]
        struct_out = list(struct.pack('<' + fmt_str, *struct_out))
        struct_out[int(Index.PackageSize)] = len(struct_out) + self.variables[int(Index.CRC)].size()
        self.variables[int(Index.CRC)].value(CRC32.calc(struct_out))
        data =bytes(struct_out) + struct.pack('<' + self.variables[int(Index.CRC)].type(),
                                               self.variables[int(Index.CRC)].value())
        self.__write_bus(data)

    def enter_bootloader(self):
        self.variables[int(Index.Command)].value(Commands.BL_JUMP)
        fmt_str = ''.join([var.type() for var in self.variables[:4]])
        struct_out = [var.value() for var in self.variables[:4]]
        struct_out = list(struct.pack('<' + fmt_str, *struct_out))
        struct_out[int(Index.PackageSize)] = len(struct_out) + self.variables[int(Index.CRC)].size()
        self.variables[int(Index.CRC)].value(CRC32.calc(struct_out))
        data = bytes(struct_out) + struct.pack('<' + self.variables[int(Index.CRC)].type(),
                                            self.variables[int(Index.CRC)].value())
        print(list(data))
        self.__write_bus(data)
    def update_fw_version(self):
        fw_file = tempfile.NamedTemporaryFile("wb+")
    
        response = requests.get(url=self.__class__.__RELEASE_URL)
        if response.status_code == 200 :
            
            response = requests.get(url=self.__class__.__RELEASE_URL)
            if (response.status_code == 200):
                fw_file.write(response.content)
            else:
                raise Exception("Could not fetch requested binary file! Check your connection to GitHub.")

            self.enter_bootloader()
            time.sleep(0.1)

            # Close serial port
            serial_settings = self.__ser.get_settings()
            self.__ser.close()

            # Upload binary
            args = ['-p', self.__ser.portstr, '-b', str(115200), '-e', '-w', '-v', fw_file.name]
            stm32loader_main(*args)

            # Delete uploaded binary
            if (not fw_file.closed):
                fw_file.close()

            # Re open port to the user with saved settings
            self.__ser.apply_settings(serial_settings)
            self.__ser.open()
            return True
        else:
            raise Exception("Could not found requested firmware files list! Check your connection to GitHub.")
    