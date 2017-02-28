#!/usr/bin/env python

import sys
import json
import csv

from trello import TrelloSession

board = TrelloSession().boards['Platform Status Board']

projects_list = board.lists['Programs/Projects']

project_urls = {}

for p in projects_list.cards:
    proj = projects_list.cards[p]
    project_urls[proj.shortUrl] = proj
    
csvwriter = csv.writer(sys.stdout, delimiter=',', quotechar='"')

n = 0

data = []

for c in board.cards:
    n += 1
    card = board.cards[c]
    #print(card.name)

    #if not ('Need UX' in card.labels or 'Developer Tools' in card.labels):
    #    continue

    if card.listId not in board.listsById:
        continue
    
    card_list = board.listsById[card.listId]

    if card_list.name in ['Programs/Projects', '2017 Platform OKR\'s']:
        continue

    labels = []

    for l in card.labels:
        labels.append(card.labels[l].name)

    need_priority = ""

    if 'Need Priority' in labels:
        need_priority = 'x'
#        labels.remove('Need Priority')

    need_review = ""

    if 'Needs Review' in labels:
        need_review = 'x'
#        labels.remove('Needs Review')

    old_priority = ""

    for p in range(0, 12):
        ps = 'Old-P{}'.format(p)

        if ps in labels:
            old_priority = str(p)
            labels.remove(ps)

            break

    new_priority = ""

    for p in range(0, 4):
        ps = 'P{}'.format(p)

        if ps in labels:
            new_priority = str(p)
            labels.remove(ps)

            break

    if len(labels) == 0:
        labels = ""

    desc = card.desc

    proj = ""
    
    p = desc.split("Project: ")

    if len(p) < 2:
        p = desc.split("Projects: ")

    if len(p) > 1:
        proj_url = p[1].split('\n')[0]

        if proj_url in project_urls:
            proj = project_urls[proj_url].name

    r = desc.split('Resource needs (in 1/2 person years): ')

    res = ""
    
    if len(r) > 1:
        res = r[1].split('\n')[0].strip().replace("'", '"')

        if len(res) > 0:
            if not (res.startswith('(') and res.endswith(')')) :
                print("Invalid resource string '{}' in card {}" \
                      .format(res, card.name))

                continue

            parts = res[1:-1].split(' ')

            total = float(parts[0])

            try:
                res = json.loads(' '.join(parts[1:]))
            except Exception as e:
                print("Invalid resource declaration {} in card {}." \
                      .format(res, card.name))

                continue

            sum = 0.0
            
            for a in res:
                sum += res[a]

            if sum != total:
                print("Total ({:.02f}) does not match sum ({:.02f}) in card {}" \
                                .format(total, sum, card.name))
                
    responsible = ""
    team = ""

    for m in card.members:
        member = board.membersById[m]

        if member.fullName.endswith(" Team"):
            team = member.fullName
        else:
            responsible += member.fullName + ", "

    if responsible.endswith(", "):
        responsible = responsible[:-2]
            
    data.append([card.name, proj, card_list.name, str(labels), old_priority,
                 new_priority, need_priority, need_review, team, responsible,
                 card.id, res])

resources = set()

for entry in data:
    res = entry[-1]

    for a in res:
        resources.add(a)

csvwriter.writerow(["Title", "Project", "List Name", "Labels", "Old Priority",
                    "New Priority", "Needs Priority", "Needs Review", "Team",
                    "Responsible", "id"] +
                   ['res-' + r for r in sorted(resources)])

for entry in data:
    res = entry.pop()

    rl = []

    if res != "":
        for r in sorted(resources):
            if r in res and res[r] != 0:
                rl.append(res[r])
            else:
                rl.append("")

    csvwriter.writerow(entry + rl)
