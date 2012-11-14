from metanl.wordlist import get_wordlist, merge_lists

def merge_english():
    books = get_wordlist('en-books')
    twitter = get_wordlist('en-twitter')
    combined = merge_lists([(books, '', 1e9), (twitter, '', 1e9)])
    combined.save('multi-en.txt')
    combined.save_logarithmic('multi-en-logarithmic.txt')
    total = sum(combined.worddict.values())
    print "Average frequency:", total / len(combined.worddict)

if __name__ == '__main__':
    merge_english()
