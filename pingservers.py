# source: https://codereview.stackexchange.com/questions/133476/custom-python-server-status-checker
# modified slightly from source to be more flexible given different server environments
import socket
from os import system
from datetime import datetime, time
from email.mime.text import MIMEText
import smtplib
import atexit
import ssl
import sys
import urllib2

SERVER_LIST = [
	('MAINSERVER','localhost', 'plain', 80),
	('PLEX','localhost', 'url', '32400/web/index.html'),
	('nifi','localhost','url','3689/nifi/'),
	('Kibana','localhost','url','5601/app/kibana'),
	#('Elasticsearch','localhost','plain',9200), not working...
	]

SRV_DOWN = []
SRV_UP = []

ADMIN_NOTIFY_LIST = ["<phonenumber>@vtext.com"]
FROM_ADDRESS = "<EMAIL>@gmail.com"
PWD = '<PWD>'

LOW=1
NORMAL=2
HIGH=3

@atexit.register
def _exit():
	print "%s  Server Status Checker Now Exiting." % (current_timestamp())

def current_timestamp():
	return datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")

def send_server_status_report():
	priority = NORMAL

	send_mail = True

	if len(SRV_UP) ==0:
		up_str = "Servers online: None!"
		priority = HIGH
	else:
		up_str = "Servers online: " + ", ".join(SRV_UP)

	if len(SRV_DOWN) ==0:
		down_str = "Servers down: None!"
		send_mail = False
	else:
		down_str = "Servers down: " + ", ".join(SRV_DOWN) + "   ***CHECK IF SERVERS LISTED ARE REALLY DOWN!***"
		priority = HIGH

	if len(SRV_UP) == len(SERVER_LIST) and len(SRV_DOWN) == 0:
		priority = LOW

	if send_mail:
		body = """Server Status Report - %s
	%s

	%s""" % (current_timestamp(), down_str, up_str)

		msg = MIMEText(body)
		msg['Subject'] = "Server Status Report - %s" % (current_timestamp())
		msg['From'] = FROM_ADDRESS
		msg['Sender'] = FROM_ADDRESS

		PRIORITY_TO_XPRIORITY = {
			LOW: '5',
			NORMAL: 'Normal',
			HIGH: '1',
		}

		msg['X-Priority'] = PRIORITY_TO_XPRIORITY[priority]

		smtp = None

		try:
			smtp = smtplib.SMTP('smtp.gmail.com', 587)
			smtp.starttls()
			smtp.login(FROM_ADDRESS, PWD)
		except Exception as e:
			print "Could not correctly establish SMTP connection with Google, error was: %s" % (e.__str__())
			exit()

		for destaddr in ADMIN_NOTIFY_LIST:
			msg['To'] = destaddr

			try:
				smtp.sendmail(FROM_ADDRESS, destaddr, msg.as_string())
				print "%s  Status email sent to [%s]." % (current_timestamp(),destaddr)
			except Exception as e:
				print "Could not send message, error was: %s" % (e.__str__())
				continue

		smtp.close()
	else:
		print "%s  All's good, do nothing." % (current_timestamp())


def main():
	for (srv, url, mechanism, port) in sorted(SERVER_LIST):
		print srv, ", ", url, ", ",  mechanism, ", ", port

		try:
			if mechanism == 'plain':
				print "%s  Using Plain for [%s]..." % (current_timestamp(), srv)
				socket.create_connection(("%s.layerbnc.org" % url, port), timeout=10)
			elif mechanism == 'ssl':
				print "%s  Using SSL for [%s]..." % (current_timestamp(), srv)
				ssl.wrap_socket(socket.create_connection(("%s" % url, port), timeout=10))
			elif mechanism == 'url':
				print "%s  Using URL for [%s]..." % (current_timestamp(), srv)
				urllib2.urlopen('http://' + url + ':' + port, timeout=10)
			else:
				print "%s  Invalid mechanism defined for [%s], skipping..." % (current_timestamp(), srv)
				continue
			SRV_UP.append(srv)
			print "%s  %s: UP" % (current_timestamp(), srv)
		except socket.timeout:
			SRV_DOWN.append(srv)
			print "%s  %s: DOWN" % (current_timestamp(), srv)
		except urllib2.URLError as err:
			SRV_DOWN.append(srv)
			print "%s  %s: DOWN" % (current_timestamp(), srv)
		except Exception as err:
			print "An error occurred: %s" % (err.__str__())
			exit()

	send_server_status_report()

	exit()


if __name__ == "__main__":
	print "%s  Server Status Checker Running...." % (current_timestamp())
	main()
