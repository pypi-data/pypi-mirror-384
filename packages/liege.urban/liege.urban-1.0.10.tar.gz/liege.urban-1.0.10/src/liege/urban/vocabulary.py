# -*- coding: utf-8 -*-

from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


class ShoreVocabularyFactory(object):

    def __call__(self, context):
        vocabulary = SimpleVocabulary(
            [
                SimpleTerm('D', 'D', 'Droite'),
                SimpleTerm('G', 'G', 'Gauche'),
                SimpleTerm('C', 'C', 'Centre'),
            ]
        )
        return vocabulary
