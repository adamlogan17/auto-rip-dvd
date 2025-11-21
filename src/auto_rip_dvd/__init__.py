def main() -> None:
    import os
    import auto_rip_dvd.auto_rip as auto_rip_dvd

    iso_out_dir = os.getenv('ISO_OUT_DIR', 'C:\\iso_movies\\')
    mp4_out_dir = os.getenv('MP4_OUT_DIR', 'C:\\mp4_movies\\')
    mkv_out_dir = os.getenv('MKV_OUT_DIR', 'C:\\mkv_movies\\')
    disc_drive = os.getenv('DISC_DRIVE', 'E:\\')

    output_folders = {
        'mp4': mp4_out_dir,
        'mkv': mkv_out_dir,
        'iso': iso_out_dir
    }


    while True:
        if auto_rip_dvd.dvd_detected(disc_drive):
            user_input = auto_rip_dvd.console_user_input()
            auto_rip_dvd.dvd_rip_workflow(output_folders, user_input)