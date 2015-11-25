#!/usr/bin/env python

import sys
import os
import re

def name_and_owner(s):
    data = s.split('[')
    name = data[0].strip()
    owner = None

    if len(data) > 1:
        owner = data[1]
        if owner[-1] != ']':
            raise Exception("Closing bracket missing in owner")

        owner = owner[:-1].strip()

    return [name, owner]

class Team:
    def __init__(self, name):
        data = name.split('(')
        self.name = data[0].strip()
        self.shortname = self.name

        if len(data) > 1:
            self.shortname = data[1]
            if self.shortname[-1] != ')':
                raise Exception("Closing parenthesis missing in team short name '{}'".format(name))

            self.shortname = self.shortname[:-1].strip()

        self.ftes = 0
        self.contr = 0
        self.reqs = 0

    @property
    def headcount(self):
        return self.ftes + self.contr + self.reqs

class Initiative:
    def __init__(self, name):
        [self.name, self.owner] = name_and_owner(name)
        self.toplinegoals = []
        self.kpis = []
        self.projects = []

class Project:
    def __init__(self, name, initiative):
        [self.name, self.owner] = name_and_owner(name)
        self.initiative = initiative
        self.when = None
        self.targets = []
        self.dependencies = ""
        self.res = {}
        self.res_total = 0.0

class Target:
    def __init__(self, name, project):
        [self.name, self.owner] = name_and_owner(name)
        self.project = project
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
                    if verbose:
                        print("Resourcing in {} TBD for {}" \
                              .format(team, self.name))
                elif res.startswith('$'):
                    team += " ($)"
                    res = res[1:]
                    self.resources[team] = self.resources.setdefault(team, 0) + float(res)
                else:
                    self.resources[team] = self.resources.setdefault(team, 0) + float(res)
            except:
                if verbose:
                    print("Invalid resource declaration '{}' in target {}" \
                          .format(m, self.name))

cur_team = None
cur_initiative = None
cur_project = None
cur_target = None

in_teams = None
in_topline_goal = False
in_kpi = False

initiatives = []
maintenance = None
teams = {}

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

        if origline == "Teams:":
            in_teams = True
            continue

        if in_teams:
            if line.startswith("* Notes: "):
                continue

            if line.startswith("* Team: "):
                cur_team = Team(line[8:])

                teams[cur_team.shortname] = cur_team

                continue

            if line.startswith("* Current FTEs:"):
                ftes = line[15:].strip()

                if len(ftes) > 0:
                    cur_team.ftes = int(ftes)

                continue

            if line.startswith("* Open reqs:"):
                reqs = line[12:].strip()

                if len(reqs) > 0:
                    cur_team.reqs = int(reqs)

                continue

            if line.startswith("* Current Contractors:"):
                contr = line[22:].strip()

                if len(contr) > 0:
                    cur_team.contr = int(contr)

                continue

            if line.startswith("* Initiative: "):
                in_teams = False
            else:
                if verbose:
                    print(line)

                continue

        if line.startswith("* Initiative: Platform Maintenance"):
            cur_initiative = Initiative(line[14:])
            maintenance = cur_initiative
            cur_project = None
            continue

        if line.startswith("* Initiative: "):
            cur_initiative = Initiative(line[14:])
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

            cur_project = Project(line[23:], cur_initiative)
            cur_initiative.projects.append(cur_project)
            continue

        if line.startswith("* Team: ") and cur_initiative == maintenance:
            in_topline_goal = False
            in_kpi = False

            cur_project = Project(line[8:], cur_initiative)
            cur_initiative.projects.append(cur_project)
            continue

        if line.startswith("* Target:"):
            cur_project.targets.append(Target(line[10:], cur_project))

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
    dollar_targets = []
    def dump_initiative_resources(initiatives):
        res = {}
        for i in initiatives:
            for p in i.projects:
                if i != maintenance:
                    if not p.owner:
                        print("Missing owner for project {}".format(p.name))

                for t in p.targets:
                    if t.resources == None:
                        print("Resource declaration missing from {}, {}" \
                              .format(p.name, t.name))
                    elif t.resources:
                        for r in t.resources:
                            if r == '':
                                print("Missing team name for target {}" \
                                      .format(t.name))

                                continue

                            if r.endswith(" ($)"):
                                dollar_targets.append(t)

                                continue

                            res[r] = res.setdefault(r, 0) + t.resources[r]
                            p.res[r] = p.res.setdefault(r, 0) + t.resources[r]
                            p.res_total += t.resources[r]

                        #print("{}, {}: {}".format(p.name, t.name, t.resources))
                    else:
                        if verbose:
                            print("No resource request for target {}." \
                                  .format(t.name))

        return res

    res = dump_initiative_resources(initiatives + [maintenance])

    def dump_res(res, title, dump_delta = False):
        print("\n\n" + title)
        total = 0.0

        for team in sorted(res.keys(), key=str.lower):
            if team == "none" and res[team] == 0:
                continue

            delta = ""

            if dump_delta:
                delta = "unknown team"

                if team in teams:
                    if teams[team].headcount == 0:
                        delta = "no current data"
                    else:
                        delta = res[team] - teams[team].headcount
                        delta = "{}{:.2f}".format('+' if delta >= 0 else '',
                                                  delta)

                delta = " ({})".format(delta)

            print("  {: <15s}: {:.2f}{}" \
                  .format(team, res[team], delta))

            total += res[team]

        print("  ----------------------\n  Total          : {:.2f}".format(total))

    dump_res(res, "All resources", True)

    projects = []

    for i in initiatives:
        projects += i.projects

    for p in sorted(projects, key=lambda p: -p.res_total):
        dump_res(p.res, "Project: {} [{}]".format(p.name, p.owner))

    for p in sorted(maintenance.projects, key=lambda p: -p.res_total):
        dump_res(p.res, "Maintenance: {}".format(p.name))

    print("\nMoney requested:")

    for t in dollar_targets:
        for r in t.resources:
            if not r.endswith(" ($)"):
                continue

            print(" ${}k allocated for {} for {}, {}".format(int(t.resources[r] / 1000), r, t.project.name, t.name))

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
