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

PRIORITY_NOT_SET = -2
PRIORITY_UNKNOWN = -1
PRIORITY_THRESHOLD = 8

class Project:
    def __init__(self, name, initiative):
        [self.name, self.owner] = name_and_owner(name)
        self.initiative = initiative
        self.when = None
        self.targets = []
        self.dependencies = ""
        self.res = {}
        self.res_total = 0.0
        self.priority = PRIORITY_NOT_SET
        self.strategic_investment = None

class Target:
    def __init__(self, name, project):
        [self.name, self.owner] = name_and_owner(name)
        self.project = project
        self.when = None
        self.dependencies = ""
        self.resources = None
        self.priority = PRIORITY_NOT_SET

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

    def getpriority(self):
        if self.priority != PRIORITY_NOT_SET:
            return self.priority

        return self.project.priority

    def gettotalresources(self):
        res = 0.0

        if self.resources == None:
            return 0.0

        for r in self.resources:
            if r == '':
                continue

            if r.endswith(" ($)"):
                continue

            res += self.resources[r]

        return res

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
                          "Downloads/2016H1Initiatives.txt")

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
            maintenance.projects.append(cur_project)
            cur_project.priority = 11
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

        def readpriority(s):
            p = s.strip()

            if p == '?':
                return PRIORITY_UNKNOWN

            p = int(p)

            if not p in range(0, 12):
                raise Exception("Priority {} out of range.".format(p))

            return p

        if origline.startswith("         * Priority:"):
            cur_project.targets[-1].priority = readpriority(line[11:])
            continue

        if origline.startswith("      * Priority:"):
            cur_project.priority = readpriority(line[11:])
            continue

        if line.startswith("* Strategic Investment:"):
            cur_project.strategic_investment = line[23:].strip()
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

# Run throgh all targets and verify stuff as well as compute Project
# resource totals as well as dollar totals.
dollar_targets = []
for i in (initiatives + [maintenance]):
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

                    if t.getpriority() > 0 or p.strategic_investment:
                        p.res[r] = p.res.setdefault(r, 0) + t.resources[r]
                        p.res_total += t.resources[r]

                #print("{}, {}: {}".format(p.name, t.name, t.resources))
            else:
                if verbose:
                    print("No resource request for target {}." \
                          .format(t.name))

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
                if t.getpriority() < PRIORITY_THRESHOLD:
                    continue

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

            if targets == "":
                continue

            if not i.toplinegoals[0] in topline_goals:
                raise Exception("Invalid topline goal: '{}'" \
                                .format(i.toplinegoals[0]))

            print('"{}", "{}", "", "{}", "", "{}", "{}"' \
                  .format(topline_goals[i.toplinegoals[0]], i.name, p.name,
                          targets, p.when or ""))

def dump_resources(priority = -3):
    def get_resources(initiatives):
        res = {}
        for i in initiatives:
            for p in i.projects:
                if p.strategic_investment != None:
                    continue

                for t in p.targets:
                    if t.getpriority() <= 0:
                        continue

                    if t.getpriority() < priority:
                        continue

                    if t.resources:
                        for r in t.resources:
                            if r == '':
                                continue

                            if r.endswith(" ($)"):
                                continue

                            res[r] = res.setdefault(r, 0) + t.resources[r]

        return res

    res = get_resources(initiatives + [maintenance])

    def dump_res(res, title, dump_delta = False, current_hc = False):
        print("\n\n" + title)
        total = 0.0
        total_hc = 0

        for team in sorted(res.keys(), key=str.lower):
            if team == "none" and res[team] == 0:
                continue

            delta = ""

            if dump_delta:
                s = " (unknown team"

                if team in teams:
                    t = teams[team]
                    if t.headcount == 0:
                        s = " (no current data"
                    else:
                        new = res[team] - t.headcount
                        reqs = t.reqs

                        total_hc += t.ftes

                        s = " (current {}".format(t.ftes + t.contr)

                        if t.reqs:
                            s += ", reqs {}".format(t.reqs)

                        s += ", new {}{:.2f}" \
                             .format('+' if new >= 0 else '', new)

                delta = s + ")"

            print("  {: <15s}: {: >6.2f}{}" \
                  .format(team, res[team], delta))

            total += res[team]

        chc = ""

        if current_hc:
            chc =  " (current {})".format(total_hc)

        print("  -----------------------\n  Total          : {: >6.2f}{}" \
              .format(total, chc))

    if priority >= 0 or priority == -3:
        dump_res(res, "All resource requests", True, True)

    if priority != -3:
        return

    projects = []

    if verbose:
        for i in initiatives:
            projects += i.projects

        for p in sorted(projects, key=lambda p: -p.res_total):
            dump_res(p.res, "Project: {} [{}]".format(p.name, p.owner))

    print("\nMaintenance:")

    total = 0.0

    for p in sorted(maintenance.projects, key=lambda p: -p.res_total):
        print("  {: <15s}: {: >6.2f}".format(p.name, p.res[p.name]))

        total += p.res[p.name]

    print("  -----------------------")
    print("  Total          : {: >6.2f}".format(total))

    print("\nMoney requested:")

    for t in dollar_targets:
        for r in t.resources:
            if not r.endswith(" ($)"):
                continue

            print("  ${}k allocated for {} for {}, {}" \
                  .format(int(t.resources[r] / 1000), r, t.project.name,
                          t.name))

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

def dump_prioritized():
    prioritized = {}
    res = {}

    for i in initiatives:
        for p in i.projects:
            if p.strategic_investment != None:
                continue

            for t in p.targets:
                if not t.getpriority() in prioritized:
                    prioritized[t.getpriority()] = []

                prioritized[t.getpriority()].append(t)

                if not t.getpriority() in res:
                    res[t.getpriority()] = 0

                res[t.getpriority()] += t.gettotalresources()

    maintenance_total = 0.0

    for p in maintenance.projects:
        maintenance_total += p.res[p.name]

    print ("Priority Maintenance, resource needs {:.2f}\n" \
           .format(maintenance_total))

    prev = maintenance_total

    for p in sorted(prioritized.keys(), reverse = True):
        ps = str(p)
        if p == PRIORITY_NOT_SET:
            ps = "not set"
        elif p == PRIORITY_UNKNOWN:
            ps = "unknown"
        print("Priority {}, resource needs {:.2f}, total {}:" \
              .format(ps, res[p], prev + res[p]))

        if p > 0:
            dump_resources(p)

        print("\nIncluded targets {}:".format(len(prioritized[p])))

        prev = prev + res[p]

        for t in prioritized[p]:
            if t.resources:
                print("  {}, {}".format(t.project.name, t.name))

        print()

    total_si = 0.0

    for i in initiatives:
        for p in i.projects:
            if p.strategic_investment == None:
                continue

            t = 0
            for r in p.res:
                t += p.res[r]

            print("Strategic investment {}, resource needs {} {}:" \
                  .format(p.strategic_investment, t, str(p.res)))

            total_si += p.res_total

    print("Total strategic investment: {:.2f}".format(total_si))

def dump_initiative_asks():
    print("\nHeadcount asks per initiative:")
    total = 0.0
    for i in initiatives + [maintenance]:
        ptotal = 0.0
        for p in i.projects:
            for t in p.targets:
                if t.getpriority() >= PRIORITY_THRESHOLD:
                    ptotal += t.gettotalresources()

        print("  {}: {:.2f}" \
              .format(i.name, ptotal))

        total += ptotal

    print("Initiatives total: {:.2f}".format(total))

dump_resources()
dump_prioritized()
dump_initiative_asks()
