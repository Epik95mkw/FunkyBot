import fnmatch
import os
import shutil
from core import paths


def dropbox():
    path1 = paths.CTGP
    path2 = paths.MAIN + 'dropbox'
    if 'dropbox' in os.listdir(paths.MAIN):
        shutil.rmtree(path2, ignore_errors=True)
    os.mkdir(path2)
    path2 += '/CTGP Custom Tracks/'
    os.mkdir(path2)

    for track in os.listdir(path1):
        if track[0] == '_':
            continue
        print(track)
        os.mkdir(path2 + track)
        szs = fnmatch.filter(os.listdir(path1 + track), '*.szs')[0]
        img = fnmatch.filter(os.listdir(path1 + track), '*.png')[0]
        shutil.copy(path1 + track + '/' + szs, path2 + track)
        shutil.copy(path1 + track + '/course.kmp', path2 + track)
        shutil.copy(path1 + track + '/course.kcl', path2 + track)
        shutil.copy(path1 + track + '/' + img, path2 + track)


if __name__ == '__main__':
    dropbox()
