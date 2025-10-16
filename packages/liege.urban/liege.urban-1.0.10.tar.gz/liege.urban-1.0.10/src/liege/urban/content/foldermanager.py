# -*- coding: utf-8 -*-

from Products.urban.FolderManager import FolderManager


def Title(self):
    """
    """

    title = "{} ({})".format(
        self.getInitials(),
        self.displayValue(self.Vocabulary('grade')[0], self.getGrade()).encode('utf8')
    )
    return title


FolderManager.Title = Title
