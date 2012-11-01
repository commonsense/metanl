from metanl.wordlist import get_wordlist, merge_lists

def merge_english():
    books = get_wordlist('en-books')
    twitter = get_wordlist('en-twitter')
    combined = merge_lists([(books, '', 1e9), (twitter, '', 1e9)])
    combined.save('multi-en.txt')
    combined.save_zipf('multi-en.zipf.txt')

if __name__ == '__main__':
    merge_english()
