#!/usr/bin/env python

import sys
import os
import csv

from trello import TrelloSession

board = TrelloSession().boards['Platform Status Board']

projects_list = board.lists['Projects']

project_urls = {}

for p in projects_list.cards:
    proj = projects_list.cards[p]
    project_urls[proj.shortUrl] = proj

csvreader = csv.reader(sys.stdin)

# skip the header row
next(csvreader)

for row in csvreader:
    priority = "P" + row[5]
    name = row[0]

    card_id = row[9]

    if card_id not in board.cardsById:
        print("Card {} ({}) missing from trello, skipping." \
              .format(name, card_id))

        continue

    if priority not in ['P0', 'P1', 'P2', 'P3']:
        continue

    card = board.cardsById[card_id]

    if priority not in card.labels:
        for p in ['P0', 'P1', 'P2', 'P3']:
            if p not in card.labels:
                continue

            print("Removing label {} from card {}".format(p, name))

            card.deleteLabel(board.labels[p].id)

        print("Adding label {} ({}) to card {}" \
              .format(board.labels[priority].id,
                      board.labels[priority].name, name))

        card.addLabel(board.labels[priority].id)

    if 'Need Priority' in card.labels:
        if any(i in card.labels for i in ['P0', 'P1', 'P2', 'P3']):
            print("Removing Need Priority from card {}.".format(name))

            card.deleteLabel(board.labels['Need Priority'].id)
        else:
            print("Not removing Need Priority from card {}".format(name))
