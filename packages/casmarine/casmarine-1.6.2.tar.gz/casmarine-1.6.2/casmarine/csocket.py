import struct
import socket


class Udp():
    _fmt = ['B', 'c', 'b', 'h', 'H', 'i', 'I', 'l', 'L', 'q', 'Q', 'f', 'd', 's', 'p']

    def __init__(self, port: int, addr: str, msg_size=4096, set_time=0.1, client=False):  # client true if receiving
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._max_msg_size = 65507
        self._msg_size = msg_size
        self._set_time = set_time
        self._addr = addr
        self._port = port
        self._af_inet_addr_pair = (self._addr, self._port)

        if client:
            try:
                self._sock.bind(self._af_inet_addr_pair)
            except Exception as e:
                raise e

        self._sock.setblocking(False)
        self._sock.settimeout(self._set_time)

    def __del__(self):
        self._sock.shutdown(socket.SHUT_RDWR)
        self._sock.close()

    def get_sock_addr(self):
        return self._af_inet_addr_pair

    def send(self, data: list):
        if data is None or len(data) > self._max_msg_size:
            raise IndexError()
        struct_out = bytearray(data)
        self._sock.sendto(struct_out, self._af_inet_addr_pair)

    def receive(self):
        struct_out, _ = self._sock.recvfrom(self._msg_size)
        if struct_out is None:
            return None
        return list(struct_out)

    def send_f(self, data: list, fmt: str):
        fmt_list = [i for i in fmt]
        for x in fmt_list:
            if x not in self.__class__._fmt:
                raise TypeError()
        struct_out = struct.pack('!' + fmt, *data)
        self._sock.sendto(struct_out, self._af_inet_addr_pair)

    def receive_f(self, fmt: str):
        fmt_list = [i for i in fmt]
        for x in fmt_list:
            if x not in self.__class__._fmt:
                raise TypeError()
        struct_out, _ = self._sock.recvfrom(self._msg_size)
        if struct_out is None:
            return None
        return list(struct.unpack('!' + fmt, struct_out))

    def receive_f_sim(self):       
        struct_out, _ = self._sock.recvfrom(self._max_msg_size)
        if not struct_out:
            return None
        decoded_data = struct_out.decode("utf-8").strip()
        parts = decoded_data.split(",")  
        try:
            liste1 = [float(x) for x in parts] 
            return liste1
        except Exception as e:
            raise e
    def send_f_sim(self, data: list, fmt: str):
        fmt_list = [i for i in fmt]
        for x in fmt_list:
            if x not in self.__class__._fmt:
                raise TypeError()
        struct_out = struct.pack('<' + fmt, *data)
        self._sock.sendto(struct_out, self._af_inet_addr_pair)