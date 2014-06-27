Multilingual natural language tools, wrapping NLTK and other systems.

## Deprecated as of June 2014

`metanl` is no longer actively developed or supported.

This package was created to support the language-processing needs that
[ConceptNet 5](http://conceptnet5.media.mit.edu) shared with code developed at
Luminoso. Those needs have diverged, to the point where it made the most sense
to split the functionality again.

A simplified version of metanl has been moved into the `conceptnet5`
package, as `conceptnet5.language`.


## metanl.token_utils

Utilities for working with tokens:

- `tokenize` splits strings into tokens, using NLTK.
- `untokenize` rejoins tokens into a correctly-spaced string, using ad-hoc
  rules that aim to invert what NLTK does.
- `un_camel_case` splits a CamelCased string into tokens.

These functions make assumptions that work best in English, and work reasonably
in other Western languages, and fail utterly in languages that don't use
spaces.


## metanl.nltk_morphy

`nltk_morphy` is a lemmatizer (a stemmer with principles). It enables you to
reduce words to their root form in English, using the Morphy algorithm that's
built into WordNet, together with NLTK's part of speech tagger.

Morphy works best with a known part of speech. In fact, the way it works in
NLTK is pretty bad if you don't specify the part of speech. The `nltk_morphy`
wrapper provides:

- An alignment between the POS tags that `nltk.pos_tag` outputs, and the input
  that Morphy expects
- A strategy for tagging words whose part of speech is unknown
- A small list of exceptions, for cases where Morphy returns an unintuitive
  or wrong result

## metanl.extprocess

Sometimes, the best available NLP tools are written in some other language
besides Python. They may not provide a reasonable foreign function interface.
What they do often provide is a command-line utility.

`metanl.extprocess` provides abstractions over utilities that take in natural
language, and output a token-by-token analysis. This is used by two other
modules in `metanl`.

### metanl.freeling

FreeLing is an NLP tool that can analyze many European languages, including
English, Spanish, Italian, Portuguese, Welsh, and Russian. This module
allows you to run FreeLing in a separate process, and use its analysis
results in Python.

### metanl.mecab

In Japanese, NLP analyzers are particularly important, because without one
you don't even know where to split words.

MeCab is the most commonly used analyzer for Japanese text. This module runs
MeCab in an external process, allowing you to get its complete analysis
results, or just use it to tokenize or lemmatize text.

As part of MeCab's operation, it outputs the phonetic spellings of the words
it finds, in kana. We use this to provide a wrapper function that can
romanize any Japanese text.

