# Authors: Reykjavik University (Judy Fong <judyfong@ru.is>) and (Arnar Freyr Kristinsson <arnark17@ru.is> )
# Description: Convert gecko rttm files to also have recordingids in the first <NA>,
# adds audio filenames to rttm files as the second field,
# remove [] stuff (foreign, noise, music) from rttm files where there is a [something]+number,
#renames the rttm/json/srt files to just the audio filename 
# and calls the create_segments_and_text.py
#All fields are optional: --rrtm, --srt or --subtitle-file
#If none is provided, only statistics are shown

from decimal import * 
import create_segments_and_text

#removes [something]+number (speaker number) - rttm files
def rm_brckts_spker_rttm(line):
    spkridOrBracketStuff = line.split(" ")[7]
    if "]+" in spkridOrBracketStuff:
        spkrnum = spkridOrBracketStuff.split("+")[1]
        endbrackpos = line.find("]")
        bgnbrackpos = line.find("[")
        removed = line.replace ( line[ bgnbrackpos : endbrackpos+2 ], "")
        return removed
    else:
        return line

#Convert timestamps to seconds and partial seconds ss.ff
def cnvrt_hh_mm_sec(hh_mm_ss):
    hh, m, s = hh_mm_ss.split(':')
    return ( int(hh) * 3600 ) + ( int(m) * 60) + Decimal(s.replace(",","."))

#Checks if a string is a timestamp
def is_srt_tmstmp(tmstamp):
    mintmstamplen = 8 # 00:00:00 (hh:mm:ss) - minimum timestamp length
    if (len (tmstamp) >= mintmstamplen):
        if(tmstamp[0:2].isnumeric() and tmstamp[2] == ':' and tmstamp[3:5].isnumeric() \
                    and tmstamp[5] == ':' and tmstamp[6:8].isnumeric() \
                    and tmstamp[9:].isnumeric() ):
            return True
    return False
    
#checks if there is some speech in the rttm file at specific segment 
def is_speech_rttm(srt_line, rttm_lines):
    if(tmstmp_scnds(srt_line) != []):
        srt_range = tmstmp_scnds(srt_line)
        for rttm_line in rttm_lines:
            rttm_bgn_tm = rttm_line.split()[3]
            rttm_spkr = rttm_line.split()[7]
            if( Decimal(rttm_bgn_tm) >= srt_range[0] and Decimal(rttm_bgn_tm) < Decimal(str(srt_range[1])) ):
                if(rttm_spkr.isnumeric()):
                    return False
    return True
#Returns the timestamps in seconds to compare the srt file to the rttm file to remove the correct segments with no speech in it.
def tmstmp_scnds(line):
      fstcol = line.split("\n")[0].split(' ')[0]
      lstcol = line.split("\n")[0].split(' ')[-1]
      arrow = "-->"
      #Find the correct line (a line that has a timestamp)
      if( is_srt_tmstmp(fstcol) and is_srt_tmstmp(lstcol)):
        expln = fstcol + " " + arrow + " " + lstcol
        if(expln == line[:-1]):
            return [ cnvrt_hh_mm_sec(fstcol), cnvrt_hh_mm_sec(lstcol) ]
      return []

#Gets the audio filename
def get_audio_filename(filename, os):
    (filename, ext) = os.path.splitext(filename)
    if ("_" in filename and "-" in filename):
        audiofilename = filename.split("_")[0].split("-")[1]
        return audiofilename+ext
    elif ("-" in filename):
        audiofilename = filename.split("-")[1]
        return audiofilename+ext
    else:
        return filename+ext

#renames files given a list contents of a directory and a file type
def rename(dircontents, dirname, os):
    for filename in dircontents:
        audiofilename = get_audio_filename(filename, os)
        os.rename(dirname+"/"+filename, dirname+"/"+audiofilename)
        (fl, ext) = os.path.splitext(filename)
        print("The file {} has been renamed to {}".format(filename, audiofilename))

#Renames Json, Rttm and srt files
def rnm_json_rttm_srt(os):
    json = 'json'
    rttm = 'rttm'
    segments = 'segments'

    if os.path.exists(json):
        json_files = os.listdir(json)
        rename(json_files, json, os)

    if os.path.exists(rttm):
        rttm_files = os.listdir(rttm)
        rename(rttm_files, rttm, os)

    if os.path.exists(segments):
        srt_files = os.listdir(segments)
        rename(srt_files, segments, os)

#Checks the given arguments and calls the corresponding function
def checkArguments(args):
    if args.rttm and args.srt and not args.subtitle_file:
        main(args.rttm, args.srt)

    elif args.rttm and not args.srt and not args.subtitle_file:
       main(args.rttm, None)
    
    elif args.srt and not args.rttm and not args.subtitle_file:
       main(None, args.srt) 

    elif args.rttm and args.srt and args.subtitle_file:
        main(args.rttm, args.srt)
        create_segments_and_text.main(args.subtitle_file)
    
    elif args.subtitle_file and not args.srt and not args.rttm:
        create_segments_and_text.main(args.subtitle_file)
    
    elif args.rttm and args.subtitle_file and not args.srt:
        main(args.rttm, None)
        create_segments_and_text.main(args.subtitle_file)

    elif args.srt and args.subtitle_file and not args.rttm:
        main(None, args.srt)
        create_segments_and_text.main(args.subtitle_file)

    else:
        print('A file needs to be given.')
        exit(0)

#Trims the srt file - removes segments that don't have any speech
def trim_srt(gecko_srt, srt_folder, gecko_rttm, rttm_lines, os):
    base = os.path.basename(gecko_srt)
    segment_id = 0
    if not os.path.exists(srt_folder):
        os.mkdir(srt_folder)
    with open(gecko_srt , 'r') as gecko_srt_file, open(srt_folder+ base, 'w') \
        as srt_file:
        for line in gecko_srt_file:
                print(line)
                #For the segment id
                if(line.rstrip().isalnum()):
                    segment_id = segment_id + 1
                if(gecko_rttm != None):
                    if not is_speech_rttm(line, rttm_lines):
                        print(segment_id, end='\n', file=srt_file)
                        print(line, end='\n', file=srt_file)
    print("The file {} has been trimmed".format(base))

#Removes []+number stuff 
def trim_rttm(gecko_rttm, rttm_folder, os):
    rttm_lines = []
    base = os.path.basename(gecko_rttm)
    (audiofilename, ext) = os.path.splitext( get_audio_filename(gecko_rttm, os) )
    (filename, ext) = os.path.splitext(base.replace("_",""))
    if not os.path.exists(rttm_folder):
        os.mkdir(rttm_folder)
    with open(gecko_rttm , 'r') as gecko_file, open(rttm_folder+ base, 'w') \
    as rttm_file:
        for line in gecko_file:
            line = rm_brckts_spker_rttm(line)
            rttm_lines.append(line)
            print(line.rstrip().replace('<NA>', filename, 1).replace('<NA>', audiofilename, 1), end='\n',
            file=rttm_file)
    print("The file {} has been trimmed".format(base))
    return rttm_lines

#Creates the csv file
def create_csv(csv_filename):
    import csv2spkids #The csv script used to create the csv file
    csv2spkids.main(csv_filename, "True")
    print("CSV file have been created")

def total_speech_time():
    import os
    total = 0
    segment_time = 0
    segment_folder = "./segments"
    segments_files = os.listdir(segment_folder)
    segment_time = [] #For sorting segment time for correct subtraction
    segment_cnt = 0
    fstcol = None
    lstcol = None

    for segment_file in segments_files:
        with open(segment_folder+"/"+segment_file) as srt_file:
            for line in srt_file:
                fstcol = line.split("\n")[0].split(' ')[0]
                lstcol = line.split("\n")[0].split(' ')[-1]
                if(is_srt_tmstmp(fstcol) and is_srt_tmstmp(lstcol)):
                    segment_time = cnvrt_hh_mm_sec(lstcol) - cnvrt_hh_mm_sec(fstcol)
                    # Some .srt files may contain invalid srt line(s) that affect the calculations, 
                    # so some minimal .srt verfication is done here. 
                    # Gecko should fix this when .srt file is saved again, including the segment id's. 
                    # To avoid this in the future a little bit of verification must take place.
                    segment_cnt = segment_cnt + 1
                    if(segment_time < 0):
                        print("Segment failure")
                        print(line)
                        print("The segment above, segment id: {} in the file {} needs to be fixed".format(segment_cnt, segment_file))
                        exit(0) #Obviously something wrong so won't continue until the file is fixed manually
                    total = total + segment_time
            segment_cnt = 0
    return total

#Creates a string to print in the Readme for statistics
def statistics_string(total_speakers, total_time, ided_speakers, unknown_speakers):
    statistics = "\n----------\n"
    statistics_lines = None
    total_mins = round( (Decimal(total_time / 60 )), 3)
    hours = round(total_mins / 60)
    minutes = round(total_mins - (60*hours))
    statistics = statistics + "{} minutes ({} hrs {} mins) of speech\n{} ided speakers\n".format(total_mins, hours, minutes, ided_speakers)
    statistics = statistics + "{} unknown speakers\n".format(unknown_speakers) 
    statistics = statistics + "{} total speakers\n".format(total_speakers)
    return statistics

#Creates the statistics from the Info CSV file and from the segments files in the segments folder
def create_statistics(csv_info_file):
    ided_speakers = 0
    unknown_speakers = 0
    total_speakers = 0
    total_time = total_speech_time()
    stats = None
    speaker_names = set()
    with open(csv_info_file, 'r') as spk_info:
        for line in spk_info:
            spk_name = line.split(',')[2]
            if(spk_name.split()[0] != "Unknown"):
                speaker_names.add(spk_name)
            else:
                unknown_speakers = unknown_speakers + 1

    ided_speakers = len(speaker_names)
    total_speakers = ided_speakers + unknown_speakers
    
    stats = statistics_string(total_speakers, total_time, ided_speakers, unknown_speakers)
    return stats

#Auto replaces statistics given there is a line that has some string that indicates the correct place in the file
#Only one occourence of any name should be taken into the account so for people who share exactly the same name, 
#one of them will only be considered.
def update_ruv_di_readme(ruv_di_readme, statistics_indicator, csv_info_file):
    statistics = create_statistics(csv_info_file)
    statistics_line_count = 0
    readme_contents = ""
    with open(ruv_di_readme, 'r') as readme_file_contents:
        for line in readme_file_contents:
            if(line.rstrip() == statistics_indicator):
                readme_contents = readme_contents + statistics_indicator + statistics
                #How many lines to skip in the original file - create statistics is the string for writing
                #in the readme file
                # -2 because of new line in the end - don't want to skip new line
                statistics_line_count = len(create_statistics(csv_info_file).split('\n'))-2 
            elif(statistics_line_count == 0):
                readme_contents = readme_contents + line
            else:
                statistics_line_count = statistics_line_count - 1
                
    with open(ruv_di_readme, 'w') as readme_file:
        print(readme_contents, file=readme_file)

    print("Statistics have been updated")
    return None

def main(gecko_rttm, gecko_srt):
    import os
    rttm_lines = []
    srt_folder = 'segments/'
    rttm_folder = 'rttm/'
    print("------------------------------------------------------------")
    if(gecko_rttm != None):
        rttm_lines = trim_rttm(gecko_rttm, rttm_folder, os)

    if(gecko_srt != None):
        trim_srt(gecko_srt, srt_folder, gecko_rttm, rttm_lines, os)
    print("------------------------------------------------------------")
    rnm_json_rttm_srt(os)
    print("------------------------------------------------------------")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Optional arguments that are possible to provide, depending on what is needed to be done. \
        If none arguments are provided the script will only rename the corresponding files if they exist')
    parser.add_argument('--rttm', required=False, help='the path to the rttm-file')
    parser.add_argument('--srt', required=False, help='the path to the srt-file')
    parser.add_argument('--subtitle-file', required=False, help='the path to the srt-file or subtitle-file')
    parser.add_argument('--create_csv_off', required=False, default='false', help='create the csv file on/off')
    parser.add_argument('--statistics', required=False, default='../reco2spk_num2spk_info.csv', help='the path to the CSV file')
    parser.add_argument('--statistics_off', required=False, default='false', help='log the statistics on/off')
    parser.add_argument('--create_csv', required=False, default='../reco2spk_num2spk_name.csv', help='the path to the CSV file')
    parser.add_argument('--ruv_di_readme', required=False, default='./ruv-di_README', help='Ruv-di readme file path')
    parser.add_argument('--update_ruv_di_readme_off', required=False, default='false', help='Update Ruv-di readme on/off')
    args = parser.parse_args()
    checkArguments(args)
    if args.create_csv_off == 'false':
       create_csv(args.create_csv)
    if args.statistics_off == 'false':
        create_statistics(args.statistics)
    if args.update_ruv_di_readme_off == 'false':
        update_ruv_di_readme(args.ruv_di_readme, "Statistics", args.statistics)