# toolshell.py

import cmd
import shlex
import os.path
import sys
from typing import Optional

import ptsl
from ptsl import PTSL_pb2 as pt


class ToolShell(cmd.Cmd):
    intro = """
Toolshell is a demonstration command interpreter that
can remotely operate Pro Tools. Type `help` or `?` to
list commands.

To begin, type `connect`.
    """
    prompt = "(not connected) "

    client = None

    def run_command_on_session(self, command_id: pt.CommandId,
                               args: dict) -> Optional[dict]:
        if self.client is None:
            print("Command failed, not connected")
            return None

        try:
            r = self.client.run_command(command_id, args)
            return r
        except ptsl.errors.CommandError as e:
            if e.error_type == pt.PT_NoOpenedSession:
                print("command failed, no session is currently open")
                return None
        except Exception:
            print("Command failed, Pro Tools may not be running")
            return None

    def do_connect(self, _):
        'Connect to Pro Tools'
        self.client = ptsl.client.Client(company_name="py-ptsl",
                                         application_name=sys.argv[0])
        if self.client is not None:
            self.prompt = "(pt) "

    def do_sinfo(self, _):
        'Print info about the open session: SINFO'
        r = self.run_command_on_session(pt.CId_GetSessionName, {})

        assert r, "Failed to receive a response"
        session_name = r['session_name']
        r = self.run_command_on_session(pt.CId_GetSessionIDs, {})
        assert r
        print(f"Connected to Pro Tools session \"{session_name}\"")
        print(f"Session origin ID: {r['origin_id']}")
        print(f"Session instance ID: {r['instance_id']}")

    def do_newsession(self, args):
        'Create a new session: NEWSESSION name save-path sample-rate'
        name, path, sr = shlex.split(args)
        print(f"Creating new session {name} at {path} and SR {sr}")
        command_args = {'session_name': name,
                        'session_location': os.path.expanduser(path),
                        'file_type': 'FT_WAVE',
                        'sample_rate': 'SR_' + str(sr),
                        'bit_depth': 'Bit24',
                        'input_output_settings': "IO_Last",
                        "is_interleaved": True,
                        "is_cloud_project": False,
                        "create_from_template": False,
                        "template_group": "",
                        "template_name": ""
                        }
        assert self.client
        self.client.run_command(pt.CreateSession, command_args)

    def do_newtracks(self, args):
        'Create new audio track: NEWTRACKS count format'
        count, fmt = shlex.split(args)
        command_args = {'number_of_tracks': count,
                        'track_name': "New Track",
                        'track_format': 'TF_' + fmt,
                        'track_type': 'TT_Audio',
                        'track_timebase': 'TTB_Samples',
                        'insertion_point_position': 'TIPoint_Unknown',
                        }
        self.run_command_on_session(pt.CId_CreateNewTracks, command_args)

    def do_locate(self, args):
        'Locate to a given time: LOCATE time'
        time = args.strip()
        command_args = {'play_start_marker_time': time,
                        'in_time': time,
                        'out_time': time,
                        }
        self.run_command_on_session(pt.CId_SetTimelineSelection, command_args)

    def do_newmemloc(self, args):
        'Create a new marker memory location: NEWMEMLOC start-time'
        command_args = {'name': 'New Marker',
                        'start_time': args.strip(),
                        'end_time': args.strip(),
                        'time_properties': 'TP_Marker',
                        'reference': 'MLR_FollowTrackTimebase',
                        'general_properties': {
                            'zoom_settings': False,
                            'pre_post_roll_times': False,
                            'track_visibility': False,
                            'track_heights': False,
                            'group_enables': False,
                            'window_configuration': False,
                        },
                        'comments': "Created by toolshell",
                        'color_index': 1,
                        'location': 'MLC_MainRuler'
                        }

        self.run_command_on_session(pt.CId_CreateMemoryLocation, command_args)

    def do_play(self, _):
        'Toggle the play state of the transport: PLAY'
        assert self.client
        try:
            self.client.run_command(pt.CommandId.TogglePlayState, {})
        except ptsl.errors.CommandError as e:
            if e.error_type == pt.PT_NoOpenedSession:
                print("play failed, no session is currently open")
                return False

    def do_geteditmode(self, _):
        'Get the edit mode of the session:'
        r = self.run_command_on_session(pt.CId_GetEditMode, {})
        print(f"Edit mode: {r['current_setting']}")

    def do_seteditmode(self, args):
        'Set the edit mode of the session:'
        command_args = {'edit_mode': args.strip()}
        self.run_command_on_session(pt.CId_SetEditMode, command_args)

    def do_getedittool(self, _):
        'Get the edit tool of the session:'
        r = self.run_command_on_session(pt.CId_GetEditTool, {})
        print(f"Edit tool: {r['current_setting']}")

    def do_setedittool(self, args):
        'Set the edit tool of the session:'
        command_args = {'edit_tool': args.strip()}
        self.run_command_on_session(pt.CId_SetEditTool, command_args)

    def do_recallzoompreset(self, args):
        'Recall a zoom preset in Pro Tools:'
        command_args = {'zoom_preset': int(args.strip())}
        self.run_command_on_session(pt.CId_RecallZoomPreset, command_args)

    def do_getsessionids(self, _):
        'Get the originId, instanceId and parentId of the current opened session'
        r = self.run_command_on_session(pt.CId_GetSessionIDs, {})
        print(f"Origin ID: {r['origin_id']}")
        print(f"Instance ID: {r['instance_id']}")
        print(f"Parent ID: {r['parent_id']}")

    def do_selectmemorylocation(self, args):
        'Select a memory location in the timeline:'
        command_args = {'number': int(args.strip())}
        self.run_command_on_session(pt.CId_SelectMemoryLocation, command_args)

    def do_mutetracks(self, args):
        'Mute one or more tracks by their track names, enclosed in quotations'
        command_args = {'track_names': shlex.split(args.strip()),
                        'enabled' : True
                        }
        self.run_command_on_session(pt.CId_SetTrackMuteState, command_args)

    def do_unmutetracks(self, args):
        'Unmute one or more tracks by their track names, enclosed in quotations'
        command_args = {'track_names': shlex.split(args.strip()),
                        'enabled' : False
                        }
        self.run_command_on_session(pt.CId_SetTrackMuteState, command_args)

    def do_solotracks(self, args):
        'Solo one or more tracks by their track names, enclosed in quotations.'
        command_args = {'track_names': shlex.split(args.strip()),
                        'enabled' : True
                        }
        self.run_command_on_session(pt.CId_SetTrackSoloState, command_args)

    def do_unsolotracks(self, args):
        'Unsolo one or more tracks by their track names, enclosed in quotations.'
        command_args = {'track_names': shlex.split(args.strip()),
                        'enabled' : False
                        }
        self.run_command_on_session(pt.CId_SetTrackSoloState, command_args)

    def do_solosafetracks(self, args):
        'Solo safe one or more tracks by their track names, enclosed in quotations.'
        command_args = {'track_names': shlex.split(args.strip()),
                        'enabled' : True
                        }
        self.run_command_on_session(pt.CId_SetTrackSoloSafeState, command_args)

    def do_unsolosafetracks(self, args):
        'Unsolo safe one or more tracks by their track names, enclosed in quotations.'
        command_args = {'track_names': shlex.split(args.strip()),
                        'enabled' : False
                        }
        self.run_command_on_session(pt.CId_SetTrackSoloSafeState, command_args)

    def do_recordsafetracks(self, args):
        'Record safe one or more tracks by their track names, enclosed in quotations.'
        command_args = {'track_names': shlex.split(args.strip()),
                        'enabled' : True
                        }
        self.run_command_on_session(pt.CId_SetTrackRecordSafeEnableState, command_args)

    def do_unrecordsafetracks(self, args):
        'Unrecord safe one or more tracks by their track names, enclosed in quotations.'
        command_args = {'track_names': shlex.split(args.strip()),
                        'enabled': False
                        }
        self.run_command_on_session(pt.CId_SetTrackRecordSafeEnableState, command_args)

    def do_trackinputmonitorenable(self, args):
        'Enable input monitor on one or more tracks by their track names, enclosed in quotations.'
        command_args = {'track_names': shlex.split(args.strip()),
                        'enabled': True
                        }
        self.run_command_on_session(pt.CId_SetTrackInputMonitorState, command_args)

    def do_trackinputmonitordisable(self, args):
        'Enable input monitor on one or more tracks by their track names, enclosed in quotations.'
        command_args = {'track_names': shlex.split(args.strip()),
                        'enabled': False
                        }
        self.run_command_on_session(pt.CId_SetTrackInputMonitorState, command_args)

    def do_tracksmartdspenable(self, args):
        'Enable Smart DSP on one or more tracks by their track names, enclosed in quotations.'
        command_args = {'track_names': shlex.split(args.strip()),
                        'enabled': True
                        }
        self.run_command_on_session(pt.CId_SetTrackSmartDspState, command_args)

    def do_tracksmartdspdisable(self, args):
        'Enable Smart DSP on one or more tracks by their track names, enclosed in quotations.'
        command_args = {'track_names': shlex.split(args.strip()),
                        'enabled': False
                        }
        self.run_command_on_session(pt.CId_SetTrackSmartDspState, command_args)

    def do_hidetracks(self, args):
        'Hide one or more tracks by their track names, enclosed in quotations.'
        command_args = {'track_names': shlex.split(args.strip()),
                        'enabled': True
                        }
        self.run_command_on_session(pt.CId_SetTrackHiddenState, command_args)

    def do_showtracks(self, args):
        'Show one or more tracks by their track names, enclosed in quotations.'
        command_args = {'track_names': shlex.split(args.strip()),
                        'enabled': False
                        }
        self.run_command_on_session(pt.CId_SetTrackHiddenState, command_args)

    def do_maketrackinactive(self, args):
        'Make one or more tracks inactive by their track names, enclosed in quotations.'
        command_args = {'track_names': shlex.split(args.strip()),
                        'enabled': True
                        }
        self.run_command_on_session(pt.CId_SetTrackInactiveState, command_args)

    def do_maketrackactive(self, args):
        'Make one or more tracks active by their track names, enclosed in quotations.'
        command_args = {'track_names': shlex.split(args.strip()),
                        'enabled': False
                        }
        self.run_command_on_session(pt.CId_SetTrackInactiveState, command_args)

    def do_freezetracks(self, args):
        'Freeze one or more tracks by their track names, enclosed in quotations.'
        command_args = {'track_names': shlex.split(args.strip()),
                        'enabled': True
                        }
        self.run_command_on_session(pt.CId_SetTrackFrozenState, command_args)

    def do_unfreezetracks(self, args):
        'Unfreeze one or more tracks by their track names, enclosed in quotations.'
        command_args = {'track_names': shlex.split(args.strip()),
                        'enabled': False
                        }
        self.run_command_on_session(pt.CId_SetTrackFrozenState, command_args)

    def do_bye(self, _):
        'Quit Toolshell and return to your shell: BYE'
        print("Toolshell quitting...")
        if self.client:
            self.client.close()
        return True



if __name__ == '__main__':
    ToolShell().cmdloop()
