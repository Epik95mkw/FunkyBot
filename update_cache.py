from core.paths import *
from api.dropbox_client import Dropbox


def main():
    print('Updating local file storage.')
    dbx = Dropbox(DROPBOX_TOKEN)
    os.mkdir(MAIN)
    os.mkdir(TEMP)

    print('Downloading CTGP tracks from Dropbox...')
    dbx.download_folder_to(CTGP, '/CTGP Custom Tracks')
    print('CTGP directory complete.')

    print('Downloading original tracks from Dropbox...')
    dbx.download_folder_to(REGS, '/MKWii Tracks')
    print('Original tracks directory complete.')

    print('All tracks cached successfully.')


if __name__ == '__main__':
    main()
