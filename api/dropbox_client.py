import os
import dropbox
import dropbox.files

class Dropbox(dropbox.Dropbox):
    def download_folder_to(self, dstpath: str, dbxpath: str, logs: bool = False):
        if not os.path.isdir(dstpath):
            os.mkdir(dstpath)
        for entry in self.files_list_folder(dbxpath).entries:
            if isinstance(entry, dropbox.files.FolderMetadata):
                self.download_folder_to(f'{dstpath}/{entry.name}', f'{dbxpath}/{entry.name}')
                if logs:
                    print(f'  Created folder: {dstpath}/{entry.name}')
            elif not os.path.isfile(f'{dstpath}/{entry.name}'):
                self.files_download_to_file(f'{dstpath}/{entry.name}', f'{dbxpath}/{entry.name}')
                if logs:
                    print(f'    Downloaded file: {entry.name}')
