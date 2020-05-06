import random

from anki.collection import _Collection
from anki.sched import Scheduler
from anki.consts import NEW_CARDS_DUE
from anki.utils import ids2str, intTime


# TODO
# fix Collection.genCards - modify "due" similar to dueForDid below


def _dueForDid(self, did, due):
    conf = self.decks.confForDid(did)
    # in order due?
    if conf['new']['order'] == NEW_CARDS_DUE:
        return due
    else:
        # random mode
        return random.randrange(1, max(due, 1000))

_Collection._dueForDid = _dueForDid


def sortCards(self, cids, start=1, step=1, shuffle=False, shift=False):
    if not cids:
        return

    scids = ids2str(cids)
    now = intTime()
    # determine cid ordering
    due = {}
    if shuffle:
        cids = list(cids)
        random.shuffle(cids)
    for c, cid in enumerate(cids):
        due[cid] = start+c*step
    high = start+c*step
    # shift?
    if shift:
        low = self.col.db.scalar(
            "select min(due) from cards where due >= ? and type = 0 "
            "and id not in %s" % scids,
            start)
        if low is not None:
            shiftby = high - low + 1
            self.col.db.execute("""
update cards set mod=?, usn=?, due=due+? where id not in %s
and due >= ? and queue = 0""" % scids, now, self.col.usn(), shiftby, low)
    # reorder cards
    d = []
    for cid, in self.col.db.execute(
        "select id from cards where type = 0 and id in "+scids):
        d.append((due[cid], now, self.col.usn(), cid))
    self.col.db.executemany(
        "update cards set due=?,mod=?,usn=? where id = ?", d)

Scheduler.sortCards = sortCards
