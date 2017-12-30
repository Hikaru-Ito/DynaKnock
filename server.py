# -*- coding:utf-8 -*-
import socket
import pyaudio
import Dynaknock

CHUNK = 512
RATE = 44100


def create_server_socket(port):
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind(('', port))
    server_sock.listen(256)
    print('Server Run Port:{}'.format(port))
    return server_sock


def accept_loop(server_sock):
    print('Ready For Accept')
    new_sock, (remote_host, remote_remport) = server_sock.accept()
    return new_sock


def create_audio_stream(chunk, rate):
    p = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=rate,
        input=True,
        output=False,
        frames_per_buffer=chunk
    )
    return stream


if __name__ == "__main__":

    # Launch Socket Server
    server_sock = create_server_socket(7777)

    # waiting connection from client
    sock = accept_loop(server_sock)

    # create audio stream
    stream = create_audio_stream(CHUNK, RATE)

    # start detection
    analyzer = Dynaknock.Analyzer(stream, sock)
    analyzer.start_detection()