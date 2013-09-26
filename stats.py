#!/usr/bin/python
# -*- coding: UTF-8 -*-
import re
import pygal
from datetime import datetime, timedelta
from pygal.style import DarkSolarizedStyle

log_file_name = "server.log"
output_dir = "./"

js = ["http://kozea.github.com/pygal.js/javascripts/svg.jquery.js",
	"http://kozea.github.com/pygal.js/javascripts/pygal-tooltips.js"]

chat_re = re.compile(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[INFO\] <(\w+)> (.+)")
slain_re = re.compile(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[INFO\] (\w+) was slain by (\w+)")
fell_re = re.compile(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[INFO\] (\w+) fell from a high place")
doomed_re = re.compile(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[INFO\] (\w+) was doomed to fall( by \w+)?")
lava_re = re.compile(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[INFO\] (\w+) tried to swim in lava( to escape \w+)?")
cactus_re = re.compile(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[INFO\] (\w+) was pricked to death$")

join_re = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[INFO\] (\w+) joined the game$")
left_re = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[INFO\] (\w+) left the game$")

slain_kill = dict()
nb_fell_kill = 0
doomed_kill = dict()
doomed_no_mod = "<himself>"
nb_lava_kill = 0
lava_escape = dict()
nb_cactus_kill = 0
users_kill = dict()

user_time = dict()
connection_count = []

def check_msg(line):
	m = chat_re.match(line)
	if m:   
		author = m.group(1)
		msg =  m.group(2)
		return True
	else:
		return False

def add_user_kill(user):
	if user in users_kill:
		users_kill[user] += 1
	else:
		users_kill[user] = 1

def check_slain(line):
	m = slain_re.match(line)
	if m:
		date = m.group(1)
		user = m.group(2)
		mob = m.group(3)	
		if mob in slain_kill:
			slain_kill[mob] += 1
		else:
			slain_kill[mob] = 1
		add_user_kill(user)
		return True
	else:
		return False

def check_fall(line):
	ret = False
	m = fell_re.match(line)
	if m:
		global nb_fell_kill
		date = m.group(1)
		user = m.group(2)
		nb_fell_kill += 1
		add_user_kill(user)
		ret = True
	else:
		m = doomed_re.match(line)
		if m:
			date = m.group(1) 
			user = m.group(2)
			if m.group(3):
				mob = m.group(3)[4:]
			else:
				mob = doomed_no_mod
			add_user_kill(user)
			if mob in doomed_kill:
				doomed_kill[mob] += 1
			else:
				doomed_kill[mob] = 1
			ret = True		
	return ret

def check_lava(line):
	ret = False
	m = lava_re.match(line)
	if m:
		date = m.group(1)
		user = m.group(2)
		add_user_kill(user)
		if m.group(3):
			mob = m.group(3)[11:]
			if mob in lava_escape:
				lava_escape[mob] += 1
			else:
				lava_escape[mob] = 1
		else:
			global nb_lava_kill
			nb_lava_kill += 1
		ret = True
	return ret

def check_cactus(line):
	m = cactus_re.match(line)
	if m:
		global nb_cactus_kill
		date = m.group(1)
		user = m.group(2)
		add_user_kill(user)
		nb_cactus_kill += 1
		return True
	else:
		return False
		
def check_kill(line):
	ret = True
	if not check_slain(line):
		if not check_fall(line):
			if not check_lava(line):
				if not check_cactus(line):
					ret = False
	return ret

def check_connection(line):
	ret = False
	m = join_re.match(line)
	if m:
		date = datetime.strptime(m.group(1),"%Y-%m-%d %H:%M:%S")
		user = m.group(2)
		if connection_count:
			last_con = connection_count[len(connection_count)-1][1]
			connection_count.append((date,last_con))
			connection_count.append((date,last_con+1))
		else:
			connection_count.append((date,1))
		
		if user in user_time:
			user_time[user][1] = date
		else:
			user_time[user] = [timedelta(0),date]
		ret = True
	else:
		m = left_re.match(line)
		if m:
			date = datetime.strptime(m.group(1),"%Y-%m-%d %H:%M:%S")
			user = m.group(2)
			last_con = connection_count[len(connection_count)-1][1]
			connection_count.append((date, last_con))
			connection_count.append((date,last_con-1))

			user_time[user][0] += date - user_time[user][1]
			user_time[user][1] = None

			ret = True
	return ret


log_file = open(log_file_name, "r")

for line in log_file:
	if not check_msg(line):
		if not check_kill(line):
			check_connection(line)

last_date = datetime.strptime(line[0:18],"%Y-%m-%d %H:%M:%S")

user_death_chart = pygal.Pie(style=DarkSolarizedStyle, js=js)
user_death_chart.title = "Mort par utilisateur (%s)" % last_date
for user in users_kill:
	user_death_chart.add(user, users_kill[user])
user_death_chart.render_to_file(output_dir+"death_by_user.svg")

slain_kill_count = 0
fell_kill_count = nb_fell_kill
lava_kill_count = nb_lava_kill

slain_death_chart = pygal.Pie(style=DarkSolarizedStyle, js=js)
slain_death_chart.title = "Tue par mob (%s)" % last_date
for mob in slain_kill:
	slain_death_chart.add(mob, slain_kill[mob])
	slain_kill_count += slain_kill[mob]
slain_death_chart.render_to_file(output_dir+"slain_by_mob.svg")

fell_death_chart = pygal.Pie(style=DarkSolarizedStyle, js=js)
fell_death_chart.title = "Mort par chute (%s)" % last_date
fell_death_chart.add("Seul", nb_fell_kill)
for mob in doomed_kill:
	fell_death_chart.add("Par %s" % (mob), doomed_kill[mob])
	fell_kill_count += 1
fell_death_chart.render_to_file(output_dir+"fell_by_mob.svg")

lava_death_chart = pygal.Pie(style=DarkSolarizedStyle, js=js)
lava_death_chart.title = "Mort dans la lave (%s)" % last_date
lava_death_chart.add("Seul", nb_lava_kill)
for mob in lava_escape:
	lava_death_chart.add("Par %s" % (mob), lava_escape[mob])
	lava_kill_count += 1
lava_death_chart.render_to_file(output_dir+"lava_by_mob.svg")

death_type_chart = pygal.Pie(style=DarkSolarizedStyle, js=js)
death_type_chart.title = "Type de mort (%s)" % last_date
death_type_chart.add("Tue", slain_kill_count)
death_type_chart.add("Chute", fell_kill_count)
death_type_chart.add("Lave", lava_kill_count)
death_type_chart.add("Cactus", nb_cactus_kill)
death_type_chart.render_to_file(output_dir+"total_death.svg")

death_prop_chart = pygal.Pie(style=DarkSolarizedStyle, js=js)
death_prop_chart.title = "Mort par type (%s)" % last_date
for mob in slain_kill:
	death_prop_chart.add("Slain by " +mob, slain_kill[mob])
death_prop_chart.add("Chutte tout seul", nb_fell_kill)
for mob in doomed_kill:
	death_prop_chart.add("Chutte par " + mob, doomed_kill[mob])
death_prop_chart.add("Lave tout seul", nb_lava_kill)
for mob in lava_escape:
	death_prop_chart.add("Lave par " + mob, lava_escape[mob])
death_type_chart.add("Cactus", nb_cactus_kill)
death_prop_chart.render_to_file(output_dir+"death_prop.svg")

connection_chart = pygal.DateY(style=DarkSolarizedStyle, show_dots=False,
	x_label_rotation=20, show_legend=False, js=js)
connection_chart.Title = "Connexion au cours du temps (%s)" % last_date
connection_chart.add("Connexion", connection_count)
connection_chart.render_to_file(output_dir+"connexion.svg")

play_time_chart = pygal.Bar(style=DarkSolarizedStyle, show_legend=False, js=js)
play_time_chart.title = "Temps de jeu par utilisateur en heure (%s)" % last_date
play_time_chart.x_labels = [ user for user in user_time ]
play_time_chart.add("Temps", [ user_time[user][0].total_seconds()/3600. for user in user_time])
play_time_chart.render_to_file(output_dir+"temps.svg")
