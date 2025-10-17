import re
import subprocess
from pathlib import Path
import tempfile
from pypl2 import PL2FileReader


_PROBE_MAP = {
    "PROBE_MODEL_R1_256_1S": "1S256",
    "PROBE_MODEL_R1_512_1S": "1S512",
    "PROBE_MODEL_R1_512_1S_NHP": "1S512-N",
    "PROBE_MODEL_R1_1024_4S": "4S1024",
    "PROBE_MODEL_R1_1024_8S": "8S1024",
}


def get_pixel_map_dump(pl2_file_path):
    with tempfile.NamedTemporaryFile(mode="w+") as tmp_out:
        with tempfile.NamedTemporaryFile(mode="w+") as tmp_err:
            parent_folder = Path(__file__).parent
            executable_path = str(parent_folder / "pixelmapdump.exe")
            p = subprocess.Popen([executable_path, pl2_file_path], stdout=tmp_out, stderr=tmp_err, text=True)
            p.wait()

            tmp_out.seek(0)
            tmp_err.seek(0)
            stdout = tmp_out.read()
            stderr = tmp_err.read()
    
    probe_pattern = re.compile(r"Port \d+ probe = \w+")
    timestamp_pattern = re.compile(r"t = (.+)\nbad\: (.+)")

    probe_info = probe_pattern.findall(stdout)
    timestamp_info = [(float(timestamp), [] if bad_channels=="no bad channels" \
                       else [int(bad_channel) for bad_channel in bad_channels.split(",")]) \
                        for timestamp, bad_channels in timestamp_pattern.findall(stdout)]

    return probe_info, timestamp_info



def get_probe_names(pl2_file_path:str|Path):
    """
    Returns list of probes used to record .pl2 file.

    Args:
        pl2_file_path - path to .pl2 file from which to extract data
    
    Outputs:
        probe_list - list of probe names
    """

    manufacturer = 'plexon'

    probes, _ = get_pixel_map_dump(pl2_file_path)
    probes = [_PROBE_MAP[x] for x in [x.split(" = ")[1] for x in probes] if x !='none']

    return probes



def _get_channel_out_of_tune_durations(pl2_file_path:str|Path):
    """
    Returns list of channel out of tune durations for specified .pl2 file.

    Args:
        pl2_file_path - path to .pl2 file from which to extract data
    
    Outputs:
        List of channel out of tune durations
    """
    
    if type(pl2_file_path)==Path:
        pl2_file_path = str(pl2_file_path)

    pl2 = PL2FileReader(pl2_file_path)
    file_info = pl2.get_file_info()
    recording_duration = file_info.duration_of_recording / file_info.timestamp_frequency
    
    for source_name in pl2.get_source_names():
        if source_name not in ("WB", "SPKC"):
            continue

        source_channel_names = pl2.get_source_channel_names(source_name, include_disabled=False)
        if source_channel_names:
            break
    
    channel_indexes = [int(source_channel_name.replace(source_name,""))-1 for source_channel_name in source_channel_names]
    channel_out_of_tune_durations = {channel_index: 0.0 for channel_index in channel_indexes}
    
    # get pixel map dump
    _, timestamp_info = get_pixel_map_dump(pl2_file_path)
    n_timestamps = len(timestamp_info)

    for index, (timestamp, channels) in enumerate(timestamp_info):
        # determine the "next" timestamp and hence the duration of the current block
        if index==n_timestamps - 1:
            next_timestamp = recording_duration
        else:
            next_timestamp = timestamp_info[index+1][0]
        
        block_duration = next_timestamp - timestamp

        # increment the out-of-tune time for the channels included in the current block
        for channel in channels:
            channel_out_of_tune_durations[channel] += block_duration

    pl2.close()

    return channel_out_of_tune_durations

def get_bad_channels(pl2_file_path:str|Path, limit:float, mode:str="absolute"):
    """
    Returns list of bad channels in .pl2 file.

    Args:
        pl2_file_path - path to .pl2 file from which to extract data
        limit - threshold value for determining bad channels
        mode - "absolute" or "relative" (defaults to "absolute")
             - for "absolute", limit specifies the number of seconds a channel 
               can be out of tune before it is deemed "bad."
             - for "relative", limit specifies the fraction (NOT PERCENTAGE) 
               of time a channel can be out of tune before it is deemed "bad" 
               (must be between 0.0 and 1.0).

    Outputs:
        bad_channels - list of bad channels
    """

    if mode not in ("absolute", "relative"):
        raise("Invalid mode specified.")

    pl2 = PL2FileReader(pl2_file_path)
    file_info = pl2.get_file_info()
    recording_duration = file_info.duration_of_recording / file_info.timestamp_frequency
    oot_durations_dict = _get_channel_out_of_tune_durations(pl2_file_path)
    
    bad_channels = []
    for channel, oot_dur in oot_durations_dict.items():
        if mode=="absolute":
            if oot_dur >= limit:
                bad_channels.append(channel)

        elif mode=="relative":
            oot_fractional = oot_dur / recording_duration
            if (oot_fractional) >= limit:
                bad_channels.append(channel)

    pl2.close()

    return bad_channels