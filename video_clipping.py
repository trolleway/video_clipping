import os
from gooey import Gooey, GooeyParser
import tempfile
import datetime

@Gooey(optional_cols=2, program_name="crop minidv with subtitles",default_size=(610, 800))
def main():
    epilog = '''
    Loseless crop of dump MiniDV cassete to upload for Youtube.
    Try to crop srt file also (srt file can produce dvgrab)

    '''
    p = GooeyParser(description='Crop MiniDV file', epilog = epilog)
    p.add_argument('--start', help='start timecode', type=str, required=False)
    p.add_argument('--to', help='end timecode', type=str, required=False)
    p.add_argument('--src', help='Source video file', type=str, required=True, widget="FileChooser")
    p.add_argument('--preset', help='encoding preset', type=str, choices=['copy_dv', 'mp4','srt_test','indexprint','twitter','interpolate_60fps' ], required=False,widget="Dropdown")

    args = p.parse_args()

    #print args

    src = args.src
    #to = args.to

    if args.start is not None:
        start = args.start
    else:
        start = '0:0:0'

    if args.to is not None:
        to = ' -to ' + str(args.to)
    else:
        to = ''

    codename = str(datetime.datetime.now())
    result = generate_result_filename(src,codename)

    preset = args.preset
    if preset == 'copy_dv':
        cmd = 'ffmpeg -i "{src}" -ss {start} {to} -vcodec copy -acodec copy "{result}"'
        cmd = cmd.format(src=src, start=start, to=to, result = result)
        print cmd
        os.system(cmd)
    if preset == 'indexprint':
        ffopts=""

        ffopts+=' -filter:v "setpts=PTS/50"'   # de-interlacing

        # FILTERS
        ffopts+=" -vf yadif"   # de-interlacing

        # VIDEO ENCODING OPTIONS
        ffopts+=" -vcodec libx264"
        #ffopts+=" -preset slower"  # balance encoding speed vs compression ratio
        ffopts+=" -profile:v main -level 3.0 "  # compatibility, see https://trac.ffmpeg.org/wiki/Encode/H.264
        ffopts+=" -pix_fmt yuv420p"  # pixel format of MiniDV is yuv411, x264 supports yuv420
        ffopts+=" -crf 23"  # The constant quality setting. Higher value = less quality, smaller file. Lower = better quality, bigger file. Sane values are [18 - 24]
        ffopts+=" -x264-params ref=4"
        ffopts+=" -tune film"

        # AUDIO ENCODING OPTIONS
        ffopts+=" -an"

        # GENERIC OPTIONS
        ffopts+=" -movflags faststart"  # Run a second pass moving the index (moov atom) to the beginning of the file.

        result = change_filename_extension(result,'.mp4')

        part_to = ''
        if to is not None: part_to = ' -to ' + to + ' '
        cmd = 'ffmpeg -i "{src}" -ss {start} {part_to} {ffopts} "{result}"'
        cmd = cmd.format(src=src, start=start, to=to, result = result, part_to=part_to,ffopts=ffopts)
        print cmd
        os.system(cmd)
    elif preset == 'srt_test':
        ffopts=""

        result = change_filename_extension(result,'.mp4')
        subtitle_file = os.path.splitext(src)[0]+'.srt0'

        cmd = 'ffmpeg -i "{src}" -i "{subtitle_file}" -ss {start} {to} {ffopts} -vcodec copy -acodec copy "{result}"'
        cmd = cmd.format(src=src, start=start, to=to, result = result,ffopts=ffopts, subtitle_file = subtitle_file)
        print cmd
        os.system(cmd)

    elif preset == 'mp4':
        ffopts=""

        # FILTERS
        ffopts+="-vf yadif"   # de-interlacing

        # VIDEO ENCODING OPTIONS
        ffopts+=" -vcodec libx264"
        ffopts+=" -preset slower"  # balance encoding speed vs compression ratio
        ffopts+=" -profile:v main -level 3.0 "  # compatibility, see https://trac.ffmpeg.org/wiki/Encode/H.264
        ffopts+=" -pix_fmt yuv420p"  # pixel format of MiniDV is yuv411, x264 supports yuv420
        ffopts+=" -crf 23"  # The constant quality setting. Higher value = less quality, smaller file. Lower = better quality, bigger file. Sane values are [18 - 24]
        ffopts+=" -x264-params ref=4"
        ffopts+=" -tune film"

        # AUDIO ENCODING OPTIONS
        ffopts+=" -acodec aac"
        ffopts+=" -ac 2 -ar 24000 -ab 80k"  # 2 channels, 24k sample rate, 80k bitrate

        # GENERIC OPTIONS
        ffopts+=" -movflags faststart"  # Run a second pass moving the index (moov atom) to the beginning of the file.

        result = change_filename_extension(result,'.mp4')

        cmd = 'ffmpeg -i "{src}" -ss {start} {to} {ffopts} "{result}"'
        cmd = cmd.format(src=src, start=start, to=to, result = result,ffopts=ffopts)
        print cmd
        os.system(cmd)
        
    elif preset == 'twitter':
        ffopts=""

        # FILTERS
        ffopts+="-vf yadif"   # de-interlacing
       

        # VIDEO ENCODING OPTIONS
        ffopts+=" -vcodec libx264"
        ffopts+=" -preset faster"  # balance encoding speed vs compression ratio
        ffopts+=" -profile:v main -level 3.0 "  # compatibility, see https://trac.ffmpeg.org/wiki/Encode/H.264
        ffopts+=" -pix_fmt yuv420p"  # pixel format of MiniDV is yuv411, x264 supports yuv420
        ffopts+=" -crf 23"  # The constant quality setting. Higher value = less quality, smaller file. Lower = better quality, bigger file. Sane values are [18 - 24]
        ffopts+=" -x264-params ref=4"
        ffopts+=" -tune film"

        # AUDIO ENCODING OPTIONS
        ffopts+=" -acodec aac"
        ffopts+=" -ac 2 -ar 24000 -ab 80k"  # 2 channels, 24k sample rate, 80k bitrate

        # GENERIC OPTIONS
        ffopts+=" -movflags faststart "  # Run a second pass moving the index (moov atom) to the beginning of the file.
        ffopts+=" -threads 4"
        result = change_filename_extension(result,'.mp4')

        cmd = 'ffmpeg -i "{src}" -ss {start}  {to} {ffopts} "{result}"'
        cmd = cmd.format(src=src, start=start, to=to, result = result,ffopts=ffopts)
        print cmd
        os.system(cmd)
    elif preset == 'twitter_interpolate60fps':
        #two-pass process with fastest mode
        ffopts=""

        # FILTERS
        ffopts+="-vf yadif"   # de-interlacing

        # VIDEO ENCODING OPTIONS
        ffopts+=" -vcodec libx264"
        ffopts+=" -preset fastest"  # balance encoding speed vs compression ratio
        ffopts+=" -profile:v main -level 3.0 "  # compatibility, see https://trac.ffmpeg.org/wiki/Encode/H.264
        ffopts+=" -pix_fmt yuv420p"  # pixel format of MiniDV is yuv411, x264 supports yuv420
        ffopts+=" -crf 20"  # The constant quality setting. Higher value = less quality, smaller file. Lower = better quality, bigger file. Sane values are [18 - 24]
        ffopts+=" -x264-params ref=4"
        ffopts+=" -tune film"

        # AUDIO ENCODING OPTIONS
        ffopts+=" -acodec aac"
        ffopts+=" -ac 2 -ar 24000 -ab 80k"  # 2 channels, 24k sample rate, 80k bitrate

        # GENERIC OPTIONS
        ffopts+=" -movflags faststart"  # Run a second pass moving the index (moov atom) to the beginning of the file.

        result = change_filename_extension(result,'.mp4')
        pass1_filename = result+'.pass1.mp4'
        result = pass1_filename

        cmd = 'ffmpeg -i "{src}" -ss {start} {to} {ffopts} "{result}"'
        cmd = cmd.format(src=src, start=start, to=to, result = result,ffopts=ffopts)
        print cmd
        os.system(cmd)
        
        ffopts=""
        
        # FILTERS
        ffopts+=''' -filter:v "minterpolate='mi_mode=mci:mc_mode=aobmc:vsbmc=1:fps=60'" '''

        # VIDEO ENCODING OPTIONS
        ffopts+=" -vcodec libx264"

        ffopts+=" -profile:v main -level 3.0 "  # compatibility, see https://trac.ffmpeg.org/wiki/Encode/H.264
        ffopts+=" -pix_fmt yuv420p"  # pixel format of MiniDV is yuv411, x264 supports yuv420
        ffopts+=" -preset fastest"  # balance encoding speed vs compression ratio
        ffopts+=" -crf 18"  # The constant quality setting. Higher value = less quality, smaller file. Lower = better quality, bigger file. Sane values are [18 - 24]
        ffopts+=" -x264-params ref=4"
        ffopts+=" -tune film"

        # AUDIO ENCODING OPTIONS
        ffopts+=" -acodec copy"


        # GENERIC OPTIONS
        ffopts+=" -movflags faststart "  # Run a second pass moving the index (moov atom) to the beginning of the file.
        ffopts+=" -threads 4"
        result = change_filename_extension(result,'.mp4')

        cmd = 'ffmpeg -i "{src}" -ss {start} {to} {ffopts} "{result}"'
        cmd = cmd.format(src=src, start=start, to=to, result = result,ffopts=ffopts)
        print cmd
        os.system(cmd)
        
        os.unlink(pass1_filename)
        
        
    elif preset == 'interpolate_60fps':
        ffopts=""
        
        # FILTERS
        ffopts+=''' -filter:v "minterpolate='mi_mode=mci:mc_mode=aobmc:vsbmc=1:fps=60'" '''

        # VIDEO ENCODING OPTIONS
        ffopts+=" -vcodec libx264"

        ffopts+=" -profile:v main -level 3.0 "  # compatibility, see https://trac.ffmpeg.org/wiki/Encode/H.264
        ffopts+=" -pix_fmt yuv420p"  # pixel format of MiniDV is yuv411, x264 supports yuv420
        ffopts+=" -crf 18"  # The constant quality setting. Higher value = less quality, smaller file. Lower = better quality, bigger file. Sane values are [18 - 24]
        ffopts+=" -x264-params ref=4"
        ffopts+=" -tune film"

        # AUDIO ENCODING OPTIONS
        ffopts+=" -acodec aac"
        ffopts+=" -ac 2 -ar 24000 -ab 80k"  # 2 channels, 24k sample rate, 80k bitrate

        # GENERIC OPTIONS
        ffopts+=" -movflags faststart "  # Run a second pass moving the index (moov atom) to the beginning of the file.
        ffopts+=" -threads 4"
        result = change_filename_extension(result,'.mp4')

        cmd = 'ffmpeg -i "{src}" -ss {start} {to} {ffopts} "{result}"'
        cmd = cmd.format(src=src, start=start, to=to, result = result,ffopts=ffopts)
        print cmd
        os.system(cmd)
        
    quit()
    if dvgrab_srt_found(src):
        print("convert source to temporary compressed file with embded subtitle stream")
        srtfile = os.path.splitext(src)[0]+'.srt0'
        basefolder = os.path.dirname(os.path.abspath(src))
        tempvideo = create_temp_videofile(basefolder)
        cmd = 'ffmpeg -i "{src}" -i "{subtitle_file}" -c:v libx264 -crf 40 -preset ultrafast -an  -c:s mov_text {tempvideo_1}'
        cmd = cmd.format(src=src,subtitle_file = srtfile, tempvideo_1=tempvideo)
        print(cmd)
        os.system(cmd)
'''
8:46 10:44
ffmpeg -i "/media/trolleway/WDBlue_2GB/DV/20120922_1209/dvgrab-2012.09.22_09-44-28.avi" -i "/media/trolleway/WDBlue_2GB/DV/20120922_1209/dvgrab-2012.09.22_09-44-28.srt0" -c:v libx264  -crf 40 -preset ultrafast -an  -c:s mov_text /media/trolleway/WDBlue_2GB/DV/20120922_1209/gPQdZQ.mp4
ffmpeg -i /media/trolleway/WDBlue_2GB/DV/20120922_1209/gPQdZQ.mp4 -ss "0:16:28" -to "0:20:02" -vcodec copy -acodec copy /media/trolleway/WDBlue_2GB/DV/20120922_1209/5s.mp4
ffmpeg -txt_format text -i /media/trolleway/WDBlue_2GB/DV/20120922_1209/5s.mp4 /media/trolleway/WDBlue_2GB/DV/20120922_1209/5s.srt
#

'''
def generate_result_filename(src,codename):
    return os.path.join(os.path.dirname(os.path.abspath(src)), codename) + os.path.splitext(src)[1]

def dvgrab_srt_found(src):
    #return true if for videofile dvgrab-2012.09.22_09-44-28.avi found file dvgrab-2012.09.22_09-44-28.srt0
    base = os.path.splitext(src)[0]
    if os.path.isfile(base + '.srt0'):
        return True
    else:
        return False

def create_temp_videofile(basefolder):
    temp_name = next(tempfile._get_candidate_names())
    return os.path.join(basefolder,temp_name)+'.mp4'

def change_filename_extension(source,new_extension):
    pre, ext = os.path.splitext(source)
    new_filename = pre + new_extension
    return new_filename


if __name__ == '__main__':
    main()
