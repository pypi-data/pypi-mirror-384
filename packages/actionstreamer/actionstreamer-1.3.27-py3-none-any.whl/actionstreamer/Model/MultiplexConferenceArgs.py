import json


class MultiplexConferenceArgs:

    def __init__(
        self,
        url: str = '',
        room_name: str = '',
        display_name: str = '',
        video_width: int = 1280,
        video_height: int = 720,
        framerate: float = 30,
        video_bitrate: int = 1000000,
        send_video: bool = True,
        send_audio: bool = True,
        receive_video: bool = True,
        receive_audio: bool = True,
        rotation_degrees: int = 0,
        return_audio_ip_address: str = '',
        return_audio_port: int = 0,
        device_id: int = 0,
        audio_loopback_index: int = 0,
        **kwargs
    ):
        self.url = url
        self.room_name = room_name
        self.display_name = display_name
        self.video_width = video_width
        self.video_height = video_height
        self.video_bitrate = video_bitrate
        self.framerate = framerate
        self.send_video = send_video
        self.send_audio = send_audio
        self.receive_video = receive_video
        self.receive_audio = receive_audio
        self.rotation_degrees = rotation_degrees
        self.return_audio_ip_address = return_audio_ip_address
        self.return_audio_port = return_audio_port
        self.device_id = device_id
        self.audio_loopback_index = audio_loopback_index
        camel_to_snake = {
            "roomName": "room_name",
            "displayName": "display_name",
            "videoWidth": "video_width",
            "videoHeight": "video_height",
            "videoBitrate": "video_bitrate",
            "sendVideo": "send_video",
            "sendAudio": "send_audio",
            "receiveVideo": "receive_video",
            "receiveAudio": "receive_audio",
            "rotationDegrees": "rotation_degrees",
            "returnAudioIPAddress": "return_audio_ip_address",
            "returnAudioPort": "return_audio_port",
            "deviceID": "device_id",
            "audioLoopbackIndex": "audio_loopback_index"
        }

        for camel_key, snake_key in camel_to_snake.items():
            if camel_key in kwargs:
                setattr(self, snake_key, kwargs.pop(camel_key))

        self.extra_fields = kwargs

        if kwargs:
            print(f"Extra fields: {kwargs}")

    def to_dict(self):
        return {
            "url": self.url,
            "roomName": self.room_name,
            "displayName": self.display_name,
            "videoWidth": self.video_width,
            "videoHeight": self.video_height,
            "videoBitrate": self.video_bitrate,
            "framerate": self.framerate,
            "sendVideo": self.send_video,
            "sendAudio": self.send_audio,
            "receiveVideo": self.receive_video,
            "receiveAudio": self.receive_audio,
            "rotationDegrees": self.rotation_degrees,
            "returnAudioIPAddress": self.return_audio_ip_address,
            "returnAudioPort": self.return_audio_port,
            "deviceID": self.device_id,
            "audioLoopbackIndex": self.audio_loopback_index
        }

    def to_json(self):
        return json.dumps(self.to_dict())
