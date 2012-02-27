# -*- coding: utf-8 -*-
from metanl.general import preprocess_text
import subprocess

"""
Japanese MeCab wrapper, being ported from simplenlp.
"""

class MeCabError(Exception): pass

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
    u'よう',          # you: "way"
    u'様',            # you in kanji
])

class MeCabWrapper(object):
    """
    Handle Japanese text using the command-line version of MeCab.
    (mecab-python is convenient, but its installer is too flaky to rely on.)

    ja_cabocha gives more sophisticated results, but requires a large number of
    additional dependencies. Using this tool for Japanese requires only
    MeCab to be installed and accepting UTF-8 text.
    """
    def __init__(self):
        """
        Create a MeCabNL object by opening a pipe to the mecab command.
        """
        try:
            self.mecab = subprocess.Popen(['mecab'], bufsize=1, close_fds=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
        except OSError:
            raise MeCabError("`mecab` didn't start. See README.txt for details "
                             "about installing MeCab and other Japanese NLP tools.")
        self.mecab_encoding = 'utf-8'
        self._detect_mecab_encoding()
        #self.input_log = open('mecab-in.txt', 'w')
        #self.output_log = open('mecab-out.txt', 'w')
    
    def __del__(self):
        """
        Clean up by closing the pipe.
        """
        #self.input_log.close()
        #self.output_log.close()
        if hasattr(self, 'mecab'):
            self.mecab.stdin.close()
    
    def _detect_mecab_encoding(self):
        """
        Once we've found a MeCab binary, it may be installed in UTF-8 or it
        may be installed in EUC-JP. We need to determine which one by
        experimentation.
        """
        self.mecab.stdin.write(u'a\n')
        out = self.mecab.stdout.readline()
        
        # out is now a string in an unknown encoding, and might not even be
        # valid in *any* encoding before the tab character. But after the
        # tab, it should all be in the encoding of the installed dictionary.

        try:
            out.decode('utf-8')
        except UnicodeDecodeError:
            try:
                self.mecab_encoding = 'euc-jp'
                out.decode('euc-jp')
            except UnicodeDecodeError:
                raise MeCabError("I can't understand MeCab in either UTF-8 or "
                                 "EUC-JP. Check the configuration of MeCab and "
                                 "its dictionary.")
        if self.mecab.stdout.readline() != 'EOS\n':
            raise MeCabError("Sorry! I got unexpected lines back from MeCab "
                             "and don't know what to do next.")
    
    def get_record_root(self, record):
        """
        Given a MeCab record, return the root word.
        """
        if record[7] == '*':
            return record[0]
        else:
            return record[7]

    def analyze(self, text):
        """
        Runs a line of text through MeCab, and returns the results as a
        list of lists ("records") that contain the MeCab analysis of each
        word.
        """
        text = preprocess_text(text).lower()
        n_chunks = (len(text)+1024)//1024
        results = []
        for chunk in xrange(n_chunks):
            chunk_text = text[chunk*1024:(chunk+1)*1024].encode(self.mecab_encoding)
            self.mecab.stdin.write(chunk_text+'\n')
            #self.input_log.write(text+'\n')
            out_line = ''
            while True:
                out_line = self.mecab.stdout.readline()
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

    def tokenize_list(self, text):
        """
        Split a text into separate words.
        
        This does not de-agglutinate as much as ja_cabocha does, but the words
        where they differ are likely to be stopwords anyway.
        """
        return [record[0] for record in self.analyze(text)]
    tokenize = tokenize_list
    
    def is_stopword_record(self, record, common_words=False):
        """
        Determine whether a single MeCab record represents a stopword.

        By default this only strips out particles and auxiliary verbs,
        but if common_words is set to True it will also strip common verbs
        and nouns such as くる and よう.
        """
        return (record[1] in STOPWORD_CATEGORIES or
                record[2] in STOPWORD_CATEGORIES or
                (common_words and record[7] in STOPWORD_ROOTS))

    def is_stopword(self, text):
        """
        Determine whether a single word is a stopword, or whether a short
        phrase is made entirely of stopwords, disregarding context.

        Use of this function should be avoided; it's better to give the text
        in context and let MeCab determine which words are the stopwords.
        """
        found_content_word = False
        for record in self.analyze(text):
            if not self.is_stopword_record(record):
                found_content_word = True
                break
        return not found_content_word

    def normalize_list(self, text, cache=None):
        """
        Get a canonical list representation of Japanese text, with words
        separated and reduced to their base forms.

        TODO: use the cache.
        """
        words = []
        analysis = self.analyze(text)
        for record in analysis:
            if not self.is_stopword_record(record):
                words.append(self.get_record_root(record))
        if not words:
            # Don't discard stopwords if that's all you've got
            words = [record[0] for record in analysis]
        return words

    def normalize(self, text, cache=None):
        """
        Get a canonical string representation of Japanese text, like
        :meth:`normalize_list` but joined with spaces.

        TODO: use the cache.
        """
        return ' '.join(self.normalize_list(text))

    def extract_phrases(self, text):
        """
        Given some text, extract phrases of up to 2 content words,
        and map their normalized form to the complete phrase.
        """
        analysis = self.analyze(text)
        for pos1 in xrange(len(analysis)):
            rec1 = analysis[pos1]
            if not self.is_stopword_record(rec1):
                yield self.get_record_root(rec1), rec1[0]
                for pos2 in xrange(pos1+1, len(analysis)):
                    rec2 = analysis[pos2]
                    if not self.is_stopword_record(rec2):
                        roots = [self.get_record_root(rec1),
                                 self.get_record_root(rec2)]
                        pieces = [analysis[i][0] for i in xrange(pos1, pos2+1)]
                        term = ' '.join(roots)
                        phrase = ''.join(pieces)
                        yield term, phrase
                        break

MECAB = MeCabWrapper()
