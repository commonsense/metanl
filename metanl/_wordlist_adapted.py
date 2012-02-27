"""
The `solvertools.wordlist` module contains a class for working with
lazily-loaded wordlists, along with various string wrangling functions that
ensure you don't have to worry about things like capitalization and encoding.
"""

from __future__ import with_statement
from solvertools.util import get_dictfile, get_picklefile, save_pickle, \
                             load_pickle, file_exists, asciify
from collections import defaultdict
import re, codecs, unicodedata, logging
logger = logging.getLogger(__name__)

def identity(text):
    "Returns what you give it."
    return text

def _reverse_freq(val):
    "If this value is a number, negate it. Otherwise, leave it alone."
    if isinstance(val, (int, float)):
        return -val
    else:
        return val

def split_accents(text):
    """
    Separate accents from their base characters in Unicode text.
    """
    return unicodedata.normalize('NFKD', text)

def ensure_unicode(text):
    "Given a string of some kind, return the appropriate Unicode string."
    if isinstance(text, str):
        return text.decode('utf-8')
    else: return text

def case_insensitive(text):
    "Collapse case by converting everything to uppercase."
    return ensure_unicode(text).upper()

def case_insensitive_clean(text):
    "Collapse case by converting everything to uppercase."
    return split_accents(ensure_unicode(text.strip()).upper())

def case_insensitive_ascii(text):
    "Convert everything to uppercase and discard non-ASCII stuff."
    return asciify(ensure_unicode(text).upper())

def alphanumeric_only(text):
    """
    Convert everything to uppercase and discard everything but letters and
    digits.
    """
    return re.sub("[^A-Z0-9]", "", case_insensitive_ascii(text))

def alphanumeric_with_spaces(text):
    """
    Convert everything to uppercase and discard everything but letters, digits,
    and spaces.
    """
    return re.sub("[^A-Z0-9 ]", "", case_insensitive_ascii(text))
alphanumeric_and_spaces = alphanumeric_with_spaces

def letters_only(text):
    """
    Convert everything to uppercase ASCII, and discard everything but the
    letters A-Z.
    """
    return re.sub("[^A-Z]", "", case_insensitive_ascii(text))

def letters_and_spaces(text):
    """
    Convert everything to uppercase ASCII, and discard everything but the
    letters A-Z and spaces.
    """
    return re.sub("[^A-Z ]", "", case_insensitive_ascii(text))

def letters_only_unicode(text):
    """
    Convert everything to uppercase, and discard everything that doesn't act
    like a letter (that is, which doesn't have a separate lowercase version).
    Preserve accents and stuff.
    """
    return ''.join(ch for ch in case_insensitive(text)
                   if ch != ch.lower())

def alphagram(text):
    """
    Get the alphagram of a text -- that is, its characters in alphabetical
    order. Two texts with the same alphagram are anagrams of each other.

    This will always strip spaces and smash case; if you want other
    equivalences in your text, do them first.

        >>> alphagram('manic sages')
        'AACEGIMNSS'
        >>> alphagram('scan images')
        'AACEGIMNSS'

    You can search for words by their alphagrams using
    :mod:`solvertools.puzzlebase.wordplay`.
    """
    sortedlist = sorted(text.upper().replace(' ', ''))
    return ''.join(sortedlist)

def letter_bank(text):
    """
    Get the letter bank of a text, which is its alphagram with identical
    characters removed.

        >>> letter_bank('metallica')
        'ACEILMT'
        >>> letter_bank('climate')
        'ACEILMT'
    
    You can search for words by their letter banks using
    :mod:`solvertools.puzzlebase.wordplay`.
    """
    sortedlist = sorted(set(text.upper().replace(' ', '')))
    return ''.join(sortedlist)

def alphabet_filter(alphabet):
    def alphabet_filter_inner(text):
        return ''.join(c for c in case_insensitive(text) if c in alphabet)
    return alphabet_filter_inner

def classical_latin_letters(text):
    "Enforce I=J and U=V as some Latin-themed puzzles do."
    return letters_only(text).replace('U', 'V').replace('J', 'I')

def with_frequency(text):
    """
    Use this as a reader when the wordlist has comma-separated entries of the
    form `WORD,freq`.
    """
    word, freq = text.rsplit(',', 1)
    return (word, int(freq))

def csv(text):
    """
    Use this when each word is associated with a value, possibly with
    duplication -- for example, a phonetic dictionary or a translation
    dictionary -- and the word and value are separated by a comma.
    """
    word, valstr = text.split(',', 1)
    return (word, valstr)
comma_separated = csv

def tsv(text):
    """
    Use this when each word is associated with a value, possibly with
    duplication -- for example, a phonetic dictionary or a translation
    dictionary -- and the word and value are separated by a comma.
    """
    word, valstr = text.split('\t', 1)
    return (word, valstr)
tab_separated = tsv

def tsv_keys(text):
    """
    Get only the left column of a tab-separated file.
    """
    word, freq = text.rsplit('\t', 1)
    return word

def tsv_values(text):
    """
    Get all columns of a tab-separated file or entry.
    """
    return text.split('\t')

def tsv_weighted(text):
    """
    Get (text, weight) pairs, separated by a tab.
    """
    text, weight = text.split('\t')[:2]
    weight = int(weight)
    return (text, weight)

def csv_rev(text):
    """
    Use this to get the reverse mapping from a comma-separated list of words
    and values.
    """
    word, valstr = text.split(',', 1)
    return (valstr, word)
comma_separated_rev = csv_rev

def with_values(text):
    """
    Use this when each word is associated with one or more values.
    
    This is being deprecated in favor of a WordMapping with `comma_separated`
    as the reader.
    """
    word, valstr = text.split(',', 1)
    values = valstr.split('|')
    return (word, values)

WIKI_PARENTHESES = re.compile(r" \([^)]+\)")
SPACES = re.compile(" +")
def wiki_title_cleanup(text):
    """
    Given a Wikipedia article title, strip out the parenthesized parts of it,
    which are usually disambiguators that we won't try to handle.
    """
    result = SPACES.sub(" ", WIKI_PARENTHESES.sub("", text.replace('_', ' ')))
    assert result.find('  ') == -1
    return result

class Wordlist(object):
    """
    A lazily-loaded wordlist.

    Words are represented as a read-only dictionary, mapping each word in the
    list to a number that is intended to represent the word's frequency. For
    wordlists that do not include frequency information, the frequency will be
    1.

    You can use the syntax `word in wordlist` to test whether the wordlist
    contains a given word; `wordlist[word]` will be its frequency. Standard
    methods including `keys()`, `get()`, and `iteritems()` work as well.

    To load a wordlist, call this constructor with the name of
    the wordlist to load, as in `Wordlist("enable")`. Don't give an extension
    or a path, because those depend on whether it's loading from a `.txt` or
    `.pickle` file anyway.
    
    You should also provide a `convert` function,
    representing how to convert an arbitrary string to the format the wordlist
    uses. It will be applied to all words in the wordlist, in addition to
    strings you query it with later.  The default convert function ensures that
    all strings are Unicode and collapses case.

    If you want case to matter, use `ensure_unicode` or `asciify`
    as the convert function. Using `identity` is just asking for trouble
    the moment you encounter a stray umlaut.

    Use the `reader` function to specify how to read a word from each line.
    In most cases, this will be `identity` or `with_frequency`.

    Finally, you can set `pickle=False` if you don't want the wordlist to be
    loaded from or saved to a pickle file.
    """
    version = 3
    def __init__(self, filename, convert=case_insensitive, reader=identity,
                 pickle=True):
        self.filename = filename
        self.words = None
        self.sorted_words = None
        self.convert = convert
        self.reader = reader
        self.pickle = pickle

    def variant(self, convert=None, reader=None):
        """
        If you want to get the same dictionary, but with a different conversion
        function or (for some reason) a different line reader, use its .variant
        method.

        For example, if you want a version of the NPL wordlist that omits
        punctuation and spaces, you can ask for
        NPL.variant(alphanumerics_only).

        """
        if convert is None:
            convert = self.convert
        if reader is None:
            reader = self.reader
        return Wordlist(self.filename, convert, reader, pickle=self.pickle)

    # load the data when necessary
    def load(self):
        "Force this wordlist to be loaded."
        if self.pickle and file_exists(get_picklefile(self.pickle_name())):
            return self._load_pickle()
        elif file_exists(get_dictfile(self.filename+'.txt')):
            return self._load_txt()
        else:
            raise IOError("Cannot find a dictionary named '%s'." %
            self.filename)

    def _load_pickle(self):
        "Load this wordlist from a pickle."
        picklename = self.pickle_name()
        logger.info("Loading %s" % picklename)
        self.words, self.sorted_words = load_pickle(picklename)

    def _load_txt(self):
        "Load this wordlist from a plain text file."
        self.words = {}
        filename = get_dictfile(self.filename+'.txt')
        logger.info("Loading %s" % filename)
        with codecs.open(filename, encoding='utf-8') as wordlist:
            entries = [self.reader(line.strip()) for line in wordlist
                       if line.strip()]
            for entry in entries:
                if isinstance(entry, tuple) or isinstance(entry, list):
                    # this word has a value attached
                    word, val = entry
                    self.words[self.convert(word)] = max(
                        self.words.get(self.convert(word), 0),
                        val
                    )
                else:
                    self.words[self.convert(entry)] = 1

            # Sort the words by reverse frequency if possible,
            # then alphabetically

            self.sorted_words = sorted(self.words.keys(),
              key=lambda word: (_reverse_freq(self.words[word]), word))
        picklename = self.pickle_name()
        if self.pickle:
            logger.info("Saving %s" % picklename)
            save_pickle((self.words, self.sorted_words), picklename)
    
    def sorted(self):
        """
        Returns the words in the list in sorted order. The order is descending
        order by frequency, and lexicographic order after that.
        """
        return self.sorted_words

    # Implement the read-only dictionary methods
    def __iter__(self):
        "Yield the wordlist entries in sorted order."
        if self.words is None:
            self.load()
        return iter(self.sorted_words)

    def iteritems(self):
        "Yield the wordlist entries and their frequencies in sorted order."
        if self.words is None:
            self.load()
        for word in self.sorted_words:
            yield (word, self.words[word])

    def __contains__(self, word):
        """
        Check if a word is in the list. This applies the same `convert`
        function that was used to build the list to the word.
        """
        if self.words is None:
            self.load()
        return self.convert(word) in self.words
    
    def __getitem__(self, word):
        """
        Get a word's frequency in the list. This applies the same `convert`
        function that was used to build the list to the word.
        """
        if self.words is None:
            self.load()
        return self.words[self.convert(word)]
    
    def get(self, word, default=None):
        """
        Get the data (frequency) for a word.
        """
        if self.words is None:
            self.load()
        return self.words.get(self.convert(word), default)

    def keys(self):
        """
        Get all the words in the list, in sorted order.
        """
        if self.words is None:
            self.load()
        return self.sorted_words

    def __repr__(self):
        return "Wordlist(%r, %s, %s)" % (self.filename, self.convert.__name__,
                                         self.reader.__name__)
    def __str__(self):
        return repr(self)

    def pickle_name(self):
        """
        The filename that this wordlist will have when pickled. This is
        determined from its base filename and the names of the functions that
        transformed it.
        """
        return "%s.%s.%s.%s.pickle" % (self.filename, self.convert.__name__,
        self.reader.__name__, self.version)

    def __hash__(self):
        return hash((self.convert, self.filename))

    def __cmp__(self, other):
        if self.__class__ != other.__class__:
            return -1
        return cmp((self.filename, self.convert),
                   (other.filename, other.convert))

    def __getstate__(self):
        """
        Used for pickling this wordlist's metadata, but not the
        list of words itself.  Currently used by language_model.
        Maybe there is a better way of doing this.
        """
        d = dict(self.__dict__)
        d['words']=None
        d['sorted_words']=None
        return d

class WordMapping(Wordlist):
    """
    A wordlist-like object that describes a many-to-many mapping from one set
    to another. An example would be a phonetic wordlist.
    """
    def __init__(self, filename, convert=case_insensitive,
                 convert_out=case_insensitive,
                 reader=csv,
                 pickle=True):
        Wordlist.__init__(self, filename, convert, reader, pickle)
        self.convert_out = convert_out

    def reverse(self):
        # same thing but with comma_separated_rev
        return WordMapping(self.filename,
                           self.convert_out, self.convert,
                           reader=csv_rev,
                           pickle=self.pickle)

    def _load_txt(self):
        "Load this wordlist from a plain text file."
        # rewriting to be many-to-many
        self.words = defaultdict(list)
        filename = get_dictfile(self.filename+'.txt')
        logger.info("Loading %s" % filename)
        wordlist = codecs.open(filename, encoding='utf-8')
        entries = [self.reader(line.strip()) for line in wordlist
                   if line.strip()]
        for entry in entries:
            word, val = entry
            self.words[self.convert(word)].append(self.convert_out(val))
        
        # Sort the words by reverse frequency if possible,
        # then alphabetically

        self.sorted_words = sorted(self.words.keys())
        picklename = self.pickle_name()
        if self.pickle:
            logger.info("Saving %s" % picklename)
            save_pickle((self.words, self.sorted_words), picklename)
        wordlist.close()
    
    def pickle_name(self):
        """
        The filename that this wordlist will have when pickled. This is
        determined from its base filename and the names of the functions that
        transformed it.
        """
        return "%s.%s-%s.%s.%s.pickle" % (self.filename, self.convert.__name__,
        self.convert_out.__name__, self.reader.__name__, self.version)
    
# Define useful wordlists
ENABLE = Wordlist('enable', case_insensitive)
NPL = Wordlist('npl_allwords2', case_insensitive)
Google1M = Wordlist('google1M', letters_only, with_frequency)
Google200K = Wordlist('google200K', letters_only, with_frequency)
COMBINED = Wordlist('sages_combined', letters_only, with_frequency)
COMBINED_WORDY = Wordlist('sages_combined', alphanumeric_with_spaces, with_frequency)
PHRASES = Wordlist('google_phrases', alphanumeric_with_spaces, with_frequency)
LATIN = Wordlist('wikipedia_la', classical_latin_letters, with_frequency)
CHAOTIC = Wordlist('chaotic', letters_only, with_frequency)
WORDNET = Wordlist('wordnet', case_insensitive)
WIKTIONARY = Wordlist('wiktionary_english', alphanumeric_with_spaces, tsv_keys)
WIKIPEDIA = Wordlist('wikipedia_en_titles', alphanumeric_with_spaces, wiki_title_cleanup)
PHONETIC = WordMapping('phonetic', case_insensitive, ensure_unicode, csv)
CROSSWORD = WordMapping('crossword_clues', letters_only, ensure_unicode, tsv)
WORDNET_DEFS = WordMapping('wordnet_definitions', alphanumeric_only, ensure_unicode, tsv)
WIKTIONARY_DEFS = WordMapping('wiktionary_english', alphanumeric_only, ensure_unicode, tsv)
SCRABBLE_RACK = Wordlist('scrabble_rack', case_insensitive)
MUSICBRAINZ_ARTISTS = Wordlist('musicbrainz_artists', alphanumeric_with_spaces, with_frequency)
MUSICBRAINZ_ALBUMS = Wordlist('musicbrainz_albums', alphanumeric_with_spaces, with_frequency)
MUSICBRAINZ_TRACKS = Wordlist('musicbrainz_tracks', alphanumeric_with_spaces, with_frequency)
IMDB_MOVIES = Wordlist('imdb_movies', alphanumeric_with_spaces, with_frequency)
IMDB_ACTORS = Wordlist('imdb_actors', alphanumeric_with_spaces, with_frequency)
ANAGRAMS_HASH = WordMapping('anagrams_hash', case_insensitive, tsv_values, tsv)
ANAGRAMS_ALPHA = WordMapping('anagrams_alpha', case_insensitive, tsv_values, tsv)
MUSICBRAINZ_ARTIST_ALBUMS = WordMapping('musicbrainz_artist_album_rel',
  alphanumeric_with_spaces, tsv_weighted, tsv)
MUSICBRAINZ_ARTIST_TRACKS = WordMapping('musicbrainz_artist_track_rel',
  alphanumeric_with_spaces, tsv_weighted, tsv)
