import json


class MultiplexRecordingArgs:

    def __init__(
        self,
        height: int = 1920,
        width: int = 1080,
        fps: float = 30,
        bitrate: int = 5000000,
        vflip: int = 0,
        hflip: int = 0,
        encoding: str = '',
        segment_length_seconds: float = 0,
        audio: int = 0,
        rotation_degrees: int = 0,
        video_gop_size: int = 60,
        video_bitrate_mode: int = 0,
        sequence_header_mode: int = 1,
        repeat_sequence_header: int = 0,
        h264_i_frame_period: int = 60,
        h264_level: int = 11,
        h264_profile: int = 4,
        h264_i_qp: int = 20,
        h264_p_qp: int = 23,
        h264_b_qp: int = 25,
        h264_minimum_qp_value: int = 20,
        h264_maximum_qp_value: int = 51,
        device_id: int = 0,
        **kwargs
    ):
        self.height = height
        self.width = width
        self.fps = fps
        self.bitrate = bitrate
        self.vflip = vflip
        self.hflip = hflip
        self.encoding = encoding
        self.segment_length_seconds = segment_length_seconds
        self.audio = audio
        self.rotation_degrees = rotation_degrees
        self.device_id = device_id
        self.video_gop_size = video_gop_size
        self.video_bitrate_mode = video_bitrate_mode
        self.sequence_header_mode = sequence_header_mode
        self.repeat_sequence_header = repeat_sequence_header
        self.h264_i_frame_period = h264_i_frame_period
        self.h264_level = h264_level
        self.h264_profile = h264_profile
        self.h264_i_qp = h264_i_qp
        self.h264_p_qp = h264_p_qp
        self.h264_b_qp = h264_b_qp
        self.h264_minimum_qp_value = h264_minimum_qp_value
        self.h264_maximum_qp_value = h264_maximum_qp_value

        camel_to_snake = {
            "segmentLengthSeconds": "segment_length_seconds",
            "rotationDegrees": "rotation_degrees",
            "deviceID": "device_id",
        }

        for camel_key, snake_key in camel_to_snake.items():
            if camel_key in kwargs:
                setattr(self, snake_key, kwargs.pop(camel_key))

        self.extra_fields = kwargs

        if kwargs:
            print(f"Extra fields: {kwargs}")

    def to_dict(self):
        return {
            "height": self.height,
            "width": self.width,
            "fps": self.fps,
            "bitrate": self.bitrate,
            "vflip": self.vflip,
            "hflip": self.hflip,
            "encoding": self.encoding,
            "segmentLengthSeconds": self.segment_length_seconds,
            "audio": self.audio,
            "rotationDegrees": self.rotation_degrees,
            "deviceID": self.device_id,
            "video_gop_size": self.video_gop_size,
            "video_bitrate_mode": self.video_bitrate_mode,
            "sequence_header_mode": self.sequence_header_mode,
            "repeat_sequence_header": self.repeat_sequence_header,
            "h264_i_frame_period": self.h264_i_frame_period,
            "h264_level": self.h264_level,
            "h264_profile": self.h264_profile,
            "h264_i_qp": self.h264_i_qp,
            "h264_p_qp": self.h264_p_qp,
            "h264_b_qp": self.h264_b_qp,
            "h264_minimum_qp_value": self.h264_minimum_qp_value,
            "h264_maximum_qp_value": self.h264_maximum_qp_value,
        }

    def to_json(self):
        return json.dumps(self.to_dict())
