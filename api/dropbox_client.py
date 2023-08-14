import os
import dropbox
import dropbox.files


class Dropbox(dropbox.Dropbox):

    def download_folder_to(self, dstpath: str, dbxpath: str):
        os.mkdir(dstpath)
        for entry in self.files_list_folder(dbxpath).entries:
            if isinstance(entry, dropbox.files.FolderMetadata):
                self.download_folder_to(f'{dstpath}/{entry.name}', f'{dbxpath}/{entry.name}')
            else:
                self.files_download_to_file(f'{dstpath}/{entry.name}', f'{dbxpath}/{entry.name}')


def test():
    dbx = Dropbox(DROPBOX_TOKEN)
    print(dbx.users_get_current_account().name)
    dbx.download_folder_to('C:/Users/epik9/Desktop/dropbox', '/CTGP Custom Tracks')


if __name__ == '__main__':
    test()
