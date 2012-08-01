# -*- coding: utf-8 -*-
from metanl.general import unicode_is_punctuation
import subprocess

class ProcessError(Exception): pass

class ProcessWrapper(object):
    def __init__(self):
        """
        Create the external process that we will communicate with.
        """
        self.process = self._get_process()

    def __del__(self):
        """
        Clean up by closing the pipe.
        """
        if hasattr(self, 'process'):
            self.process.stdin.close()
    
    def _get_command(self):
        raise NotImplementedError

    def _get_process(self):
        command = self._get_command()
        try:
            return subprocess.Popen(command, bufsize=1, close_fds=True,
                                    stdout=subprocess.PIPE,
                                    stdin=subprocess.PIPE)
        except OSError:
            raise ProcessError("Couldn't start the external process: %r" %
                    command)

    def get_record_root(self, record):
        raise NotImplementedError

    def get_record_token(self, record):
        raise NotImplementedError

    def analyze(self, text):
        raise NotImplementedError

    def tokenize_list(self, text):
        """
        Split a text into separate words.
        """
        return [self.get_record_token(record) for record in self.analyze(text)]

    def tokenize(self, text):
        raise NotImplementedError("tokenize is deprecated. Use tokenize_list.")
    
    def is_stopword_record(self, record, common_words=False):
        raise NotImplementedError

    def is_stopword(self, text):
        """
        Determine whether a single word is a stopword, or whether a short
        phrase is made entirely of stopwords, disregarding context.

        Use of this function should be avoided; it's better to give the text
        in context and let the process determine which words are the stopwords.
        """
        found_content_word = False
        for record in self.analyze(text):
            if not self.is_stopword_record(record):
                found_content_word = True
                break
        return not found_content_word

    def get_record_pos(self, record):
        if self.is_stopword_record(record):
            return 'STOP'
        else:
            return 'TERM'

    def normalize_list(self, text, cache=None):
        """
        Get a canonical list representation of text, with words
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
            words = [self.get_record_token(record) for record in analysis]
        return words

    def normalize(self, text, cache=None):
        """
        Get a canonical string representation of this text, like
        :meth:`normalize_list` but joined with spaces.

        TODO: use the cache.
        """
        return ' '.join(self.normalize_list(text, cache))

    def tag_and_stem(self, text, cache=None):
        """
        Given some text, return a sequence of (stem, pos, text) triples as
        appropriate for the reader. `pos` can be as general or specific as
        necessary (for example, it might label all parts of speech, or it might
        only distinguish function words from others).
        """
        analysis = self.analyze(text)
        triples = []

        tag_is_next = False
        for record in analysis:
            root = self.get_record_root(record)
            token = self.get_record_token(record)

            if token:
                if tag_is_next:
                    triples.append((u'#'+token, 'TAG', u'#'+token))
                    tag_is_next = False
                elif token == u'#':
                    tag_is_next = True
                elif unicode_is_punctuation(token):
                    triples.append((token, '.', token))
                else:
                    pos = self.get_record_pos(record)
                    triples.append((root, pos, token))
        return triples

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

