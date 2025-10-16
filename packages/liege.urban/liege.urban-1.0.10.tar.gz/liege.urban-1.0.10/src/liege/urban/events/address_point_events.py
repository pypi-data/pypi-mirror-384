# -*- coding: utf-8 -*-


def on_delete(parcel, event):
    """
      Reindex licence of this parcel after deletion.
    """
    parcel.aq_inner.aq_parent.reindexObject(idxs=['shore'])
