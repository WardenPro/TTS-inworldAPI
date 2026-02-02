import pyaudio
import time
from dataclasses import dataclass

@dataclass
class AudioDevice:
    index: int
    name: str
    channels: int
    sample_rate: int
    is_input: bool

class AudioDeviceManager:
    def __init__(self):
        self.pa = pyaudio.PyAudio()

    def list_devices(self):
        devices = []
        info = self.pa.get_host_api_info_by_index(0)
        num_devices = info.get('deviceCount')

        for i in range(0, num_devices):
            if (self.pa.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
                dev = self.pa.get_device_info_by_host_api_device_index(0, i)
                devices.append(AudioDevice(
                    index=i,
                    name=dev.get('name'),
                    channels=dev.get('maxInputChannels'),
                    sample_rate=int(dev.get('defaultSampleRate')),
                    is_input=True
                ))
            
            if (self.pa.get_device_info_by_host_api_device_index(0, i).get('maxOutputChannels')) > 0:
                dev = self.pa.get_device_info_by_host_api_device_index(0, i)
                devices.append(AudioDevice(
                    index=i,
                    name=dev.get('name'),
                    channels=dev.get('maxOutputChannels'),
                    sample_rate=int(dev.get('defaultSampleRate')),
                    is_input=False
                ))
        return devices

    def terminate(self):
        self.pa.terminate()

class MicCapture:
    def __init__(self, device_index=None, sample_rate=48000, chunk_ms=20):
        self.pa = pyaudio.PyAudio()
        self.device_index = device_index
        self.sample_rate = sample_rate
        self.chunk_size = int(sample_rate * (chunk_ms / 1000))
        self.stream = None
        self.callback = None
    
    def start(self, callback):
        self.callback = callback
        self.stream = self.pa.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.sample_rate,
            input=True,
            input_device_index=self.device_index,
            frames_per_buffer=self.chunk_size,
            stream_callback=self._stream_callback
        )
        self.stream.start_stream()

    def _stream_callback(self, in_data, frame_count, time_info, status):
        if self.callback:
            self.callback(in_data)
        return (None, pyaudio.paContinue)

    def stop(self):
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.pa.terminate()

class AudioOutput:
    def __init__(self, device_index=None, sample_rate=48000):
        self.pa = pyaudio.PyAudio()
        self.device_index = device_index
        self.sample_rate = sample_rate
        self.stream = None

    def start(self):
        self.stream = self.pa.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.sample_rate,
            output=True,
            output_device_index=self.device_index
        )
    
    def write(self, data):
        if self.stream:
            self.stream.write(data)

    def stop(self):
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.pa.terminate()
