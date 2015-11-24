#!/usr/bin/env python

import sys
import os
import re

class Initiative:
    def __init__(self, data):
        self.name = data[0]

        if len(data) > 1:
            self.owner = data[1]
            if self.owner[-1] != ']':
                raise Exception("Closing bracket missing in initiative owner")

            self.owner = self.owner[:-1]

        self.toplinegoals = []
        self.kpis = []
        self.projects = []

class Project:
    def __init__(self, name):
        self.name = name
        self.when = None
        self.targets = []
        self.dependencies = ""

class Target:
    def __init__(self, name):
        self.name = name
        self.when = None
        self.dependencies = ""
        self.resources = None

    def addResources(self, r):
        if self.resources == None:
            self.resources = {}

        r = r.strip()

        if len(r) == 0:
            return

        if r == '0':
            r = "none 0"

        for m in r.split(','):
            team = ""
            res = "0"
            try:
                m = m.strip()
                (team, res) = m.split()

                team = team.strip()
                res = res.strip()

                if res == "?":
                    print("Resourcing in {} TBD for {}" \
                          .format(team, self.name))
                else:
                    self.resources[team] = self.resources.setdefault(team, 0) + float(res)
            except:
                print("Invalid resource declaration '{}' in target {}".format(m, self.name))

cur_initiative = None
cur_project = None
cur_target = None

in_topline_goal = False
in_kpi = False

initiatives = []
maintenance = None

verbose = len(sys.argv) > 1 and sys.argv[1] == "-v"

topline_goals = {
    "Build for Quality": "A. Build for Quality",
    "Invite Participation": "B. Invite Participation ",
    "Be Clear, Compelling & Focused": "C. Be Clear, Compelling & Focused ",
    "Grow Our Influence": "D. Grow Our Influence ",
    "Prototype the Future": "E. Prototype the Future "
}

INPUT_PATH = os.path.join(os.path.expanduser("~"),
                          "Downloads/2016Initiatives.txt")

if os.path.exists(INPUT_PATH):
    os.rename(INPUT_PATH, INPUT_PATH + ".tmp")

with open(os.path.join(INPUT_PATH + ".tmp"), "r") as f:
    for line in f:
        line = line[:-1]
        if line.encode('utf-8').startswith(b'\xef\xbb\xbf'):
            line = line[1:]

        origline = line
        line = line.strip()

        line = re.sub(r'\[..?\]', '', line)

        if len(line) == 0:
            continue

        #print(origline)

        if line.startswith("* Not going to happen"):
            break

        if line.startswith("* Initiative: Platform Maintenance"):
            cur_initiative = Initiative([line[14:]])
            maintenance = cur_initiative
            cur_project = None
            continue

        if line.startswith("* Initiative: "):
            cur_initiative = Initiative(line[14:].split('['))
            initiatives.append(cur_initiative)
            cur_project = None
            continue

        if line.startswith("* Supported topline goals:"):
            in_topline_goal = True
            continue

        if line.startswith("* Key Performance Indicators (KPI):"):
            in_topline_goal = False
            in_kpi = True
            continue

        if line.startswith("* Project/Deliverable: "):
            in_topline_goal = False
            in_kpi = False

            cur_project = Project(line[23:])
            cur_initiative.projects.append(cur_project)
            continue

        if line.startswith("* Team: ") and cur_initiative == maintenance:
            in_topline_goal = False
            in_kpi = False

            cur_project = Project(line[8:])
            cur_initiative.projects.append(cur_project)
            continue

        if line.startswith("* Target:"):
            cur_project.targets.append(Target(line[10:]))

            continue

        if line.startswith("* Drivers: ") or \
           line.startswith("* Notes: ") or \
           line.startswith("* Feedback Notes: "):
            continue

        if origline.startswith("      * When:"):
            cur_project.when = line[8:]
            continue

        if origline.startswith("         * When:"):
            cur_project.targets[-1].when = line[8:]
            continue

        if origline.startswith("      * Dependencies: "):
            cur_project.dependencies = line[16:]
            continue

        if origline.startswith("         * Dependencies: "):
            cur_project.targets[-1].dependencies = line[16:]
            continue

        if line.startswith("* Resources:"):
            cur_project.targets[-1].addResources(line[12:])
            continue

        if in_topline_goal is True:
            cur_initiative.toplinegoals.append(line[2:])
            continue

        if in_kpi is True:
            cur_initiative.kpis.append(line[2:])
            continue

        if verbose:
            print(origline)


if verbose:
    print("\n\n\ndump:\n\n")

def dump_all():
    for i in initiatives:
        print(i.name)
        print("goals: {}".format(i.toplinegoals))
        print("kpis: {}".format(i.kpis))
        for p in i.projects:
            print("  project: {}".format(p.name))

            if p.when != None:
                print("    when: {}".format(p.when))

            for t in p.targets:
                print("    target: {}".format(t.name))

                if t.when != None:
                    print("      when: {}".format(t.when))
def dump_CSV_all():
    for i in initiatives:
        for p in i.projects:
            targets = ""
            for t in p.targets:
                if targets != "":
                    targets += '\n'

                when = None
                if t.when != None:
                    when = t.when
                elif p.when != None:
                    when = p.when

                targets += t.name

                if when != None:
                    targets += " [{}]".format(when)

            if not i.toplinegoals[0] in topline_goals:
                raise Exception("Invalid topline goal: '{}'".format(i.toplinegoals[0]))

            print('"{}", "{}", "", "{}", "", "{}", "{}"' \
                  .format(topline_goals[i.toplinegoals[0]], i.name, p.name,
                          targets, p.when or ""))
def dump_resources():
    res = {}

    def dump_initiative_resources(initiatives):
        for i in initiatives:
            for p in i.projects:
                if i != maintenance:
                    who = re.search(r'\[.*\]$', p.name)

                    if who == None:
                        print("Missing owner for initiative {}".format(p.name))

                for t in p.targets:
                    if t.resources == None:
                        print("Resource declaration missing from {}, {}" \
                              .format(p.name, t.name))

                    if t.resources:
                        for r in t.resources:
                            if r == '':
                                print("Missing team name for target {}" \
                                      .format(t.name))

                            if r in res:
                                res[r] += t.resources[r]
                            elif r != "none" and t.resources[r] != 0.0:
                                res[r] = t.resources[r]

                        #print("{}, {}: {}".format(p.name, t.name, t.resources))

    dump_initiative_resources(initiatives + [maintenance])

    total = 0.0

    for team in sorted(res.keys()):
        print("{}: {}".format(team, res[team]))

        total += res[team]

    print("Total: {}".format(total))

def dump_CSV_projects():
    res = {}
    for i in initiatives:
        for p in i.projects:
            when = ""
            if p.when != None:
                when = p.when

            if not i.toplinegoals[0] in topline_goals:
                raise Exception("Invalid topline goal: '{}'" \
                                .format(i.toplinegoals[0]))

            print('"{}", "{}", "", "{}", "", "", "{}"' \
                  .format(topline_goals[i.toplinegoals[0]], i.name, p.name,
                          when))



dump_resources()
