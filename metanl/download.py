import urllib, os, sys
import tarfile

def _mkdir(newdir):
    """
    http://code.activestate.com/recipes/82465/
    
    works the way a good mkdir should :)
        - already exists, silently complete
        - regular file in the way, raise an exception
        - parent directory(ies) does not exist, make them as well
    """
    if os.path.isdir(newdir):
        pass
    elif os.path.isfile(newdir):
        raise OSError("A file with the same name as the desired " \
                      "directory, '%s', already exists." % newdir)
    else:
        head, tail = os.path.split(newdir)
        if head and not os.path.isdir(head):
            _mkdir(head)
        if tail:
            os.mkdir(newdir)

def download(rem_filename, dest_filename):
    dir = os.path.dirname(dest_filename)
    _mkdir(dir)
    def dlProgress(count, blockSize, totalSize):
        percent = int(count*blockSize*100/totalSize)
        sys.stdout.write("\r" + rem_filename + "... %2d%%" % percent)
        sys.stdout.flush()
    urllib.urlretrieve(rem_filename, dest_filename, reporthook=dlProgress)
    return True

def get_or_download_wordlist_file():
    remote_filename = "http://lumino.so/downloads/google-books-frequencies.txt"
    target_filename = os.path.expanduser('~/.local/share/dict/google-books-frequencies.txt')
    if not os.path.isfile(target_filename):
        download(remote_filename, target_filename)
    return open(target_filename)

def get_frequency_list():
    """
    Get a list of words by their frequency in the English Google Books corpus.
    """
    freqs = {}
    file = get_or_download_wordlist_file()
    for line in file:
        word, freq = line.split()
        freqs[word] = int(freq)
    return freqs
