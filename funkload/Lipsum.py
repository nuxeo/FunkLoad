# -*- coding: ISO-8859-15 -*-
# (C) Copyright 2005 Nuxeo SAS <http://nuxeo.com>
# Author: bdelbosc@nuxeo.com
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
# 02111-1307, USA.
#
"""A simple Lorem ipsum generator.

$Id: Lipsum.py 24649 2005-08-29 14:20:19Z bdelbosc $
"""
import random

# vacabulary simple ascii
V_ASCII = ('ad', 'aquam', 'albus', 'archaeos', 'arctos', 'argentatus',
           'arvensis', 'australis', 'biscort' 'borealis', 'brachy', 'bradus',
           'brevis', 'campus', 'cauda', 'caulos', 'cephalus', 'chilensis',
           'chloreus', 'cola', 'cristatus', 'cyanos', 'dactylus', 'deca',
           'dermis', 'delorum', 'di', 'diplo', 'dodeca', 'dolicho',
           'domesticus', 'dorsum', 'dulcis', 'echinus', 'ennea', 'erythro',
           'familiaris', 'flora', 'folius', 'fuscus', 'fulvus', 'gaster',
           'glycis', 'hexa', 'hortensis', 'it', 'indicus', 'lateralis',
           'leucus', 'lineatus', 'lipsem', 'lutea', 'maculatus', 'major',
           'maximus', 'melanus', 'minimus', 'minor', 'mono', 'montanus',
           'morphos', 'mauro', 'niger', 'nona', 'nothos', 'notos',
           'novaehollandiae', 'novaeseelandiae', 'noveboracensis', 'obscurus',
           'occidentalis', 'octa', 'oeos', 'officinalis', 'oleum',
           'orientalis', 'ortho', 'pachys', 'palustris', 'parvus', 'pedis',
           'pelagius', 'penta', 'petra', 'phyllo', 'phyton', 'platy',
           'pratensis', 'protos', 'pteron', 'punctatus', 'rhiza', 'rhytis',
           'rubra', 'rostra', 'rufus', 'sativus', 'saurus', 'sinensis',
           'stoma', 'striatus', 'silvestris', 'sit', 'so', 'tetra',
           'tinctorius', 'tomentosus', 'tres', 'tris', 'trich', 'thrix',
           'unus', 'variabilis', 'variegatus', 'ventrus', 'verrucosus', 'via',
           'viridis', 'vitis', 'volans', 'vulgaris', 'xanthos', 'zygos',
           )

# vocabulary with some diacritics
V_DIAC = ('acanth', 'acro', 'actino', 'adelphe', 'adéno', 'aéro', 'agogue',
          'agro', 'algie', 'allo', 'amphi', 'andro', 'anti', 'anthropo',
          'aqui', 'archéo', 'archie', 'auto', 'bio', 'calli', 'cephal',
          'chiro', 'chromo', 'chrono', 'dactyle', 'démo', 'eco', 'eudaimonia',
          'êthos', 'géo', 'glyphe', 'gone', 'gramme', 'graphe', 'hiéro',
          'homo', 'iatrie', 'lipi', 'lipo', 'logie', 'lyco', 'lyse', 'machie',
          'mélan', 'méta', 'naute', 'nèse', 'pedo', 'phil', 'phobie', 'podo',
          'polis', 'poly', 'rhino', 'xeno', 'zoo',
          )

# latin 9 vocabulary
V_8859_15 = ('jàcánth', 'zâcrö', 'bãctinõ', 'zädelphe', 'kådénô', 'zæró',
             'agòguê', 'algië', 'allð', 'amphi', 'añdro', 'añti', 'aqúi',
             'aùtø', 'biø', 'caßi', 'çephal', 'lýco', 'rÿtøñ', 'oþiß',
             'es', 'du', 'de', 'le', 'as', 'us', 'i', 'ave', 'ov Œ',
             'zur œ', 'ab Ÿ',
             )

# common char to build identifier
CHARS = "abcdefghjkmnopqrstuvwxyz123456789"

# separator
SEP = ',' * 10 + ';?!'

class Lipsum:
    """Kind of Lorem ipsum generator."""

    def __init__(self, vocab=V_ASCII,
                 chars=CHARS, sep=SEP):
        self.vocab = vocab
        self.chars = chars
        self.sep = sep

    def getWord(self):
        """Return a random word."""
        return random.choice(self.vocab)

    def getUniqWord(self, length_min=None, length_max=None):
        """Generate a kind of uniq identifier."""
        length_min = length_min or 5
        length_max = length_max or 9
        length = random.randrange(length_min, length_max)
        chars = self.chars
        return ''.join([random.choice(chars) for i in range(length)])

    def getSubject(self, length=5, prefix=None, uniq=False,
                   length_min=None, length_max=None):
        """Return a subject of length words."""
        subject = []
        if prefix:
            subject.append(prefix)
        if uniq:
            subject.append(self.getUniqWord())
        if length_min and length_max:
            length = random.randrange(length_min, length_max+1)
        for i in range(length):
            subject.append(self.getWord())
        return ' '.join(subject).capitalize()

    def getSentence(self):
        """Return a random sentence."""
        sep = self.sep
        length = random.randrange(5, 20)
        sentence = [self.getWord() for i in range(length)]
        for i in range(random.randrange(0, 3)):
            sentence.insert(random.randrange(length-4)+2, random.choice(sep))
        sentence = ' '.join(sentence).capitalize() + '.'
        sentence = sentence.replace(' ,', ',')
        sentence = sentence.replace(',,', ',')
        return sentence

    def getParagraph(self, length=4):
        """Return a paragraph."""
        return ' '.join([self.getSentence() for i in range(length)])

    def getMessage(self, length=7):
        """Return a message paragraph length."""
        return '\n\n'.join([self.getParagraph() for i in range(
            random.randrange(3,length))])

    def getPhoneNumber(self, lang="fr", format="medium"):
        """Return a random Phone number."""
        if lang == "en_US":
            num = []
            num.append("%3.3i" % random.randrange(0, 999))
            num.append("%4.4i" % random.randrange(0, 9999))
            if format == "short":
                return "-".join(num)
            num.insert(0, "%3.3i" % random.randrange(0, 999))
            if format == "medium":
                return "(%s) %s-%s" % tuple(num)
            # default long
            return "+00 1 (%s) %s-%s" % tuple(num)

        # default lang == 'fr':
        num = ['07']
        for i in range(4):
            num.append('%2.2i' % random.randrange(0, 99))
        if format == "medium":
            return " ".join(num)
        elif format == "long":
            num[0] = '(0)7'
            return "+33 "+ " ".join(num)
        # default format == 'short':
        return "".join(num)

    def getAddress(self, lang="fr"):
        """Return a random address."""
        # default lang == fr
        return "%i %s %s\n%5.5i %s" % (
            random.randrange(1, 100),
            random.choice(['rue', 'avenue', 'place', 'boulevard']),
            self.getSubject(length_min=1, length_max=3),
            random.randrange(99000, 99999),
            self.getSubject(length_min=1, length_max=2))


def main():
    """Testing."""
    print 'Word: %s\n' % (Lipsum().getWord())
    print 'UniqWord: %s\n' % (Lipsum().getUniqWord())
    print 'Subject: %s\n' % (Lipsum().getSubject())
    print 'Subject uniq: %s\n' % (Lipsum().getSubject(uniq=True))
    print 'Sentence: %s\n' % (Lipsum().getSentence())
    print 'Paragraph: %s\n' % (Lipsum().getParagraph())
    print 'Message: %s\n' % (Lipsum().getMessage())
    print 'Phone number: %s\n' % Lipsum().getPhoneNumber()
    print 'Phone number fr short: %s\n' % Lipsum().getPhoneNumber(
        lang="fr", format="short")
    print 'Phone number fr medium: %s\n' % Lipsum().getPhoneNumber(
        lang="fr", format="medium")
    print 'Phone number fr long: %s\n' % Lipsum().getPhoneNumber(
        lang="fr", format="long")
    print 'Phone number en_US short: %s\n' % Lipsum().getPhoneNumber(
        lang="en_US", format="short")
    print 'Phone number en_US medium: %s\n' % Lipsum().getPhoneNumber(
        lang="en_US", format="medium")
    print 'Phone number en_US long: %s\n' % Lipsum().getPhoneNumber(
        lang="en_US", format="long")
    print 'Address default: %s' % Lipsum().getAddress()


if __name__ == '__main__':
    main()
