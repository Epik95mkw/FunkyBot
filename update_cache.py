from core.paths import *
from api.dropbox_client import Dropbox


def main():
    print('WARNING: Delete all removed track folders manually before running this!')
    yesno: str = input('\nContinue? (Y/N) ')
    if yesno.upper() != 'Y':
        print('\nUpdate aborted.')
        return
    print('')

    print('Updating local file storage.')
    dbx = Dropbox(DROPBOX_TOKEN)
    if not os.path.isdir(MAIN):
        os.mkdir(MAIN)
    if not os.path.isdir(TEMP):
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
