# -*- coding: utf-8 -*-
u"""
Provide Japanese NLP functions by wrapping the output of MeCab.

Requires mecab to be installed separately.

>>> print normalize(u'これはテストです')
テスト
>>> tag_and_stem(u'これはテストです。')
[(u'\\u3053\\u308c', 'STOP', u'\\u3053\\u308c'), (u'\\u306f', 'STOP', u'\\u306f'), (u'\\u30c6\\u30b9\\u30c8', 'TERM', u'\\u30c6\\u30b9\\u30c8'), (u'\\u3067\\u3059', 'STOP', u'\\u3067\\u3059'), (u'\\u3002', '.', u'\\u3002')]
"""

from metanl.general import preprocess_text
from metanl.wordlist import Wordlist, get_frequency
from metanl.extprocess import ProcessWrapper, ProcessError
import unicodedata

class MeCabError(ProcessError): pass

# MeCab outputs the part of speech of its terms. We can simply identify
# particular (coarse or fine) parts of speech as containing stopwords.

STOPWORD_CATEGORIES = set([
    u'助詞',          # coarse: particle
    u'連体詞',        # coarse: adnominal adjective ("rentaishi")
    u'助動詞',        # coarse: auxiliary verb
    u'接続詞',        # coarse: conjunction
    u'フィラー',      # coarse: filler
    u'記号',          # coarse: symbol
    u'助詞類接続',    # fine: particle connection
    u'代名詞',        # fine: pronoun
    u'接尾',          # fine: suffix
])


# Forms of particular words are also stopwords.
#
# A thought: Should the rare kanji version of suru not be a stopword?
# I'll need to ask someone who knows more Japanese, but it may be
# that if they're using the kanji it's for particular emphasis.
STOPWORD_ROOTS = set([
    u'する',          # suru: "to do"
    u'為る',          # suru in kanji (very rare)
    u'くる',          # kuru: "to come"
    u'来る',          # kuru in kanji
    u'いく',          # iku: "to go"
    u'行く',          # iku in kanji
    u'もの',          # mono: "thing"
    u'物',            # mono in kanji
    u'よう',          # yō: "way"
    u'様',            # yō in kanji
])

HEPBURN_TABLE = {
    'SI': 'shi',
    'Sy': 'sh',
    'TI': 'chi',
    'TU': 'tsu',
    'Ty': 'ch',
    'HU': 'fu',
    'Zy': 'j',
    'ZI': 'ji',
    'DI': 'ji',
    'Dy': 'j',
}

class MeCabWrapper(ProcessWrapper):
    """
    Handle Japanese text using the command-line version of MeCab.
    (mecab-python is convenient, but its installer is too flaky to rely on.)

    ja_cabocha gives more sophisticated results, but requires a large number of
    additional dependencies. Using this tool for Japanese requires only
    MeCab to be installed and accepting UTF-8 text.
    """
    def _get_command(self):
        return ['mecab']

    def _get_process(self):
        try:
            proc = ProcessWrapper._get_process(self)
        except (OSError, ProcessError):
            raise MeCabError("MeCab didn't start. See README.txt for details "
                             "about installing MeCab and other Japanese NLP tools.")
        self.mecab_encoding = self._detect_mecab_encoding(proc)
        return proc
    
    def _detect_mecab_encoding(self, proc):
        """
        Once we've found a MeCab binary, it may be installed in UTF-8 or it
        may be installed in EUC-JP. We need to determine which one by
        experimentation.
        """
        proc.stdin.write(u'a\n')
        out = proc.stdout.readline()
        
        # out is now a string in an unknown encoding, and might not even be
        # valid in *any* encoding before the tab character. But after the
        # tab, it should all be in the encoding of the installed dictionary.
        encoding = 'utf-8'
        try:
            out.decode('utf-8')
        except UnicodeDecodeError:
            try:
                out.decode('euc-jp')
                encoding = 'euc-jp'
            except UnicodeDecodeError:
                raise MeCabError("I can't understand MeCab in either UTF-8 or "
                                 "EUC-JP. Check the configuration of MeCab and "
                                 "its dictionary.")
        if proc.stdout.readline() != 'EOS\n':
            raise MeCabError("Sorry! I got unexpected lines back from MeCab "
                             "and don't know what to do next.")
        return encoding
    
    def get_record_root(self, record):
        """
        Given a MeCab record, return the root word.
        """
        if record[7] == '*':
            return record[0]
        else:
            return record[7]

    def get_record_token(self, record):
        return record[0]

    def analyze(self, text):
        """
        Runs a line of text through MeCab, and returns the results as a
        list of lists ("records") that contain the MeCab analysis of each
        word.
        """
        try:
            process = self.process  # make sure things are loaded
            text = preprocess_text(text).lower()
            n_chunks = (len(text)+1024)//1024
            results = []
            for chunk in xrange(n_chunks):
                chunk_text = text[chunk*1024:(chunk+1)*1024].encode(self.mecab_encoding)
                self.send_input(chunk_text+'\n')
                #self.input_log.write(text+'\n')
                out_line = ''
                while True:
                    out_line = self.receive_output_line()
                    #self.output_log.write(out_line)
                    out_line = out_line.decode(self.mecab_encoding)

                    if out_line == u'EOS\n':
                        break

                    word, info = out_line.strip(u'\n').split(u'\t')
                    record = [word] + info.split(u',')
                    
                    # special case for detecting nai -> n
                    if record[0] == u'ん' and record[5] == u'不変化型':
                        record[7] = record[1] = u'ない'

                    results.append(record)
            return results
        except ProcessError:
            self.restart_process()
            return self.analyze(text)

    def to_kana(self, text):
        records = self.analyze(text)
        kana = []
        for record in records:
            if len(record) > 8:
                kana.append(record[8])
            else:
                kana.append(record[0])
        return ' '.join(k for k in kana if k)
    
    def romanize(self, text):
        kana = self.to_kana(text)
        pieces = []
        currently_japanese = False
        for char in kana:
            name = unicodedata.name(char)
            if name.startswith('HIRAGANA') or name.startswith('KATAKANA'):
                names = name.split()
                charname = names[-1]
                if name.endswith('SMALL TU'):
                    pieces.append(u'っ')
                elif names[1] == 'PROLONGED':
                    if currently_japanese:
                        pieces.append(pieces[-1][-1])
                    else:
                        pieces.append(u'-')
                else:
                    if names[-2] == 'SMALL':
                        if not currently_japanese:
                            pieces.append('xx')
                        pieces[-1] = pieces[-1][:-1] + charname.lower()
                    else:
                        pieces.append(charname)
                currently_japanese = True

            else:
                pieces.append(char)
                currently_japanese = False
        for i in xrange(len(pieces)):
            if pieces[i] == u'っ':
                if i == len(pieces) - 1 or not ('A' <= pieces[i+1][0] <= 'Z'):
                    pieces[i] = 't'
                else:
                    pieces[i] = pieces[i+1][0]
            else:
                while pieces[i][:2] in HEPBURN_TABLE:
                    pieces[i] = HEPBURN_TABLE[pieces[i][:2]] + pieces[i][2:]
        return u''.join(pieces).lower()

    def is_stopword_record(self, record, common_words=False):
        """
        Determine whether a single MeCab record represents a stopword.

        By default this only strips out particles and auxiliary verbs,
        but if common_words is set to True it will also strip common verbs
        and nouns such as くる and よう.
        """
        # preserve negations
        if record[7] == u'ない':
            return False
        return (record[1] in STOPWORD_CATEGORIES or
                record[2] in STOPWORD_CATEGORIES or
                (common_words and record[7] in STOPWORD_ROOTS))

class NoStopwordMeCabWrapper(MeCabWrapper):
    """
    This version of the MeCabWrapper doesn't label anything as a stopword. It'
    used in building ConceptNet because discarding stopwords based on MeCab
    categories loses too much information.
    """
    def is_stopword_record(self, record, common_words=False):
        return False

def word_frequency(word, default_freq=0):
    """
    Looks up the word's frequency in the Leeds Internet Japanese corpus.
    """
    return get_frequency(word, 'ja', default_freq)

def get_wordlist():
    return Wordlist.load('leeds-internet-ja.txt')

MECAB = MeCabWrapper()
normalize = MECAB.normalize
normalize_list = MECAB.normalize_list
tokenize = MECAB.tokenize
tokenize_list = MECAB.tokenize_list
analyze = MECAB.analyze
romanize = MECAB.romanize
tag_and_stem = MECAB.tag_and_stem
is_stopword = MECAB.is_stopword
