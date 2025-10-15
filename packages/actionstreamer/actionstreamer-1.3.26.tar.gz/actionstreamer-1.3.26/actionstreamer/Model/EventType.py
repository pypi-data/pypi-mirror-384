from enum import Enum


class EventType:

    class Video(Enum):
        
        Follow = 8
        Join_conference = 24
        Leave_conference = 25
        Multiplex_capture_frames = 36
        Multiplex_join_conference = 31
        Multiplex_leave_conference = 39
        Multiplex_start_recording = 29
        Multiplex_start_RTMP = 32
        Multiplex_start_send_ActionSync = 30
        Multiplex_stop_capturing_frames = 40
        Multiplex_stop_recording = 37
        Multiplex_stop_RTMP = 38
        Multiplex_stop_send_ActionSync = 41
        Start_audio_multiplex_send_UDP = 51
        Stop_audio_multiplex_send_UDP = 52
        Start_bars = 9        
        Start_camera_multiplex = 28
        Start_microphone_multiplex = 55
        Start_receive_ActionSync = 5
        Start_receive_ActionSync_multiplex = 34
        Start_receive_UDP_audio = 53
        Start_receive_UDP_audio_multiplex = 49
        Start_receive_UDP_video_multiplex = 45
        Start_recording = 1
        Start_RTMP = 14
        Start_send_ActionSync = 3
        Start_send_UDP_audio = 47
        Start_send_UDP_video = 43
        Stop_bars = 10
        Stop_receive_ActionSync = 6
        Stop_receive_UDP_audio = 54
        Stop_receive_UDP_audio_multiplex = 50
        Stop_receive_UDP_video_multiplex = 46
        Stop_recording = 2
        Stop_RTMP = 15
        Stop_send_ActionSync = 4
        Stop_send_UDP_audio = 48
        Stop_send_UDP_video = 44
        Test_event = 7
        Test_stop = 11
        

    class Transcoding(Enum):
        Transcode_file = 12
        Concatenate_files = 16
        Extract_video = 23
        Concatenate_files_ext = 26


    class Transfer(Enum):
        Transfer_file = 13


    class Device(Enum):  
        Add_network = 17
        Remove_network = 18
        Update_networks = 19
        Send_network_list = 20
        Update_software = 21
        Update_setting = 22
        Clear_flag_queue = 27
        End_process = 35
        Reboot_device = 42
        Restart_agents = 58
        Set_input_volume = 56
        Set_output_volume = 57


    class Workflow:
        Event_preset_workflow = 33