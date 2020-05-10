# Sierra's SCI vocab format has "old" version (used by vocab.0) - with 7 bits ascii
# and 8th bit used for string end
# while "new" version (used by vocab.900) has 8 bits ascii
#
# reference: http://sci.sierrahelp.com/Documentation/SCISpecifications/27-TheParser.html#AEN5794
# for Hebrew translation, we need to the vocab to be in the newer version

# this exports vocab file to a csv
# TODO: I was too lazy to properly create one vocab import/export tool
# see also vocab_import.py

import pathlib
import csv

INPUT_FILE = r"C:\Zvika\ScummVM-dev\HebrewAdventure\sq3\patches\vocab.000.orig"
OUTPUT_FILE = r"C:\Zvika\ScummVM-dev\HebrewAdventure\sq3\patches\vocab.csv"

classes = {
    0x004: 'CONJUNCTION',
    0x008: 'ASSOCIATION',
    0x010: 'PREPOSITION',
    0x020: 'ARTICLE',
    0x040: 'ADJECTIVE',
    0x080: 'PRONOUN',
    0x100: 'NOUN',
    0x200: 'INDICATIVE_VERB',
    0x400: 'ADVERB',
    0x800: 'IMPERATIVE_VERB'
}


def get_classes(i):
    result = []
    for k in classes.keys():
        if i & k != 0:
            result.append(classes[k])
    return result


in_vocab = list(pathlib.Path(INPUT_FILE).read_bytes())

#TODO: automatic recognize file kind, and support exporting new kind
kind = "old"

if kind == "old":
    num_of_pointers_to_ignore = 26

vocab = []
bytes_until_word_text = 0
at_start_of_word = True
current_word = ""
for idx, val in enumerate(in_vocab[(num_of_pointers_to_ignore*2):]):
    if bytes_until_word_text == 0:
        if at_start_of_word:
            at_start_of_word = False
            current_word = current_word[:int(val)]
        elif val < 0x80:
            current_word += chr(val)
        else:
            current_word += chr(val - 0x80)
            bytes_until_word_text = 3
            at_start_of_word = True
            i = idx + num_of_pointers_to_ignore*2
            entry = {
                'word': current_word,
                'class': get_classes(in_vocab[i+1] * 256 + in_vocab[i+2] >> 4),
                'group': (in_vocab[i+2] & 0b1111) * 256 + in_vocab[i+3]
            }
            vocab.append(entry)
    else:
        bytes_until_word_text -= 1

vocab_by_group = {}
for entry in vocab:
    group = entry['group']
    if group in vocab_by_group:
        vocab_by_group[group]['words'].append(entry['word'])
        if sorted(vocab_by_group[group]['class']) != sorted(entry['class']):
            vocab_by_group[group]['class'].extend(entry['class'])
            vocab_by_group[group]['class'] = sorted(set(vocab_by_group[group]['class']))
            print ("Warning: class mismatch: ", vocab_by_group[group])
    else:
        vocab_by_group[group] = {
            'words': [entry['word']],
            'class': entry['class']
        }

sorted_vocab = []
for k in sorted(vocab_by_group.keys()):
    entry = vocab_by_group[k]
    entry['group'] = k
    entry['words'] = " | ".join(entry['words'])
    entry['class'] = " | ".join(entry['class'])
    sorted_vocab.append(entry)

keys = sorted_vocab[0].keys()
with open(OUTPUT_FILE, 'w', newline='') as output_file:
    dict_writer = csv.DictWriter(output_file, keys)
    dict_writer.writeheader()
    dict_writer.writerows(sorted_vocab)
