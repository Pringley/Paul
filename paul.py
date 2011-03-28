#!/usr/bin/env python
# Paul 0.0.1 - Paul Bunyan the IRC logger
# Copyright (C) 2011 Ben Pringle
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; widhout even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Contact: ben@pringley.com

"""Paul Bunyan is an IRC logger.

Usage:
    python paul.py [options] [channels]

Options:
    -s         server
    -p         port
    -n         nick

Example:
    python paul.py -n irc.psigenix.net sports gaming

"""

import os, socket, time, optparse, ConfigParser

version = '%prog 0.0.1'
usage = 'usage: %prog [options] channel1 channel2 ...'

endl = '\r\n' # IRC end-of-line
defaults = {
    'server': 'irc.freenode.net',
    'port': 6667,
    'nick': 'paul'
}

# Handle command-line arguments.
parser = optparse.OptionParser(usage = usage, version = version)
parser.add_option('--server', '-s',
                  default = '',
                  help = 'connect to this server [default: {0}]'.format(
                                                         defaults['server']))
parser.add_option('--port', '-p',
                  type = int,
                  default = 0,
                  help = 'connect on this port [default: {0}]'.format(
                                                         defaults['port']))
parser.add_option('--folder', '-f',
                  default = os.path.join(os.path.expanduser('~'),'.paul'),
                  help = 'read configuration and store logs in this folder'
                         ' [default: %default]')
parser.add_option('--nick', '-n',
                  default = '',
                  help = 'use this nick [default: {0}]'.format(
                                                         defaults['nick']))
(options, channels) = parser.parse_args()

# Load information from the configuration file.
config_file = os.path.join(options.folder, 'paul.cfg')
config = ConfigParser.ConfigParser()

# If there is no config file, make one with defaults.
if not os.access(config_file, os.R_OK):
    # Also make the folder if that doesn't exist.
    if not os.path.isdir(options.folder):
        os.makedirs(options.folder)
    # Insert default configuration.
    config.set('DEFAULT', 'server', defaults['server'])
    config.set('DEFAULT', 'port', str(defaults['port']))
    config.set('DEFAULT', 'nick', defaults['nick'])
    config.set('DEFAULT', 'channels', '')
    with open(config_file, 'wb') as f:
        config.write(f)
# Otherwise, read settings from the file.
else:
    config.read(config_file)
    if not options.server:
        options.server = config.get('DEFAULT', 'server')
    if not options.port:
        options.port = config.getint('DEFAULT', 'port')
    if not options.nick:
        options.nick = config.get('DEFAULT', 'nick')
    if not channels:
        channels = config.get('DEFAULT', 'channels').split()

# Use defaults if needed.
server = options.server or defaults['port']
port = options.port or defaults['server']
nick = options.nick or defaults['nick']

def timestamp():
    """Produce the current 24-hour local time in the form [H:M:S]"""
    return '[%s:%s:%s]' % tuple(
                 [str(z).rjust(2,'0') for z in time.localtime()[3:6]])

def write_log(logname, clean_data):
    """Log data to file.
    
    Keyword arguments:
    logname -- the folder to find the log
    clean_data -- the line to append
    
    The data will be stored in a file based on the date (Y-M-D.log).
    
    """
    
    logdir = os.path.join(options.folder, logname)
    # If the folder doesn't exist, make it.
    if not os.path.isdir(logdir):
        os.makedirs(logdir)
    # Now add the data to today's log.
    dayfile = '-'.join([
                    str(z).rjust(2,'0') for z in time.localtime()[0:3]])+'.log'
    logpath = os.path.join(logdir, dayfile)
    with open(logpath, 'a') as log:
        log.write(clean_data + '\n')

# Connect to the server.
irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
irc.connect((server, port))
print "Connecting ..."
time.sleep(3)

# Set nick and user strings.
irc.send('NICK paul' + endl)
irc.send('USER Paul host server :Paul Bunyan the IRC logger' + endl)

# Join channels.
for channel in channels:
    irc.send('JOIN #' + channel + endl)

while True:
    # Read incoming data.
    datalines = irc.recv(4096)
    
    # Process line by line.
    for data in datalines.split('\n'):

        # Return pings.
        if 'PING' in data:
            irc.send('PONG ' + data.split()[1] + endl)

        # Handle messages.
        elif 'PRIVMSG' in data:
            # Since IRC isn't changing anytime soon, we'll
            # use some magic-looking string manipulation to
            # extract the data.
            message = ':'.join(data.split(':')[2:]).replace(endl, '')
            sender = data.split('!')[0].replace(':', '').lower()
            destination = ''.join(data.split(':')[:2]).split(' ')[-2]

            # if the destination is us, it's a Private Message
            isPM = (destination == nick)

            # Reassemble the data cleanly for printing/logging.
            clean_data = '{0} <{1}> {2}'.format(timestamp(), sender, message)
            print clean_data

            # PMs mean user requests! Handle them.
            if isPM:
                # TODO
                pass

            # Log all non-PM messages.
            else:
                write_log(destination, clean_data)

        # Handle join events.
        elif 'JOIN' in data:
            # Data extraction magic:
            channel = ':'.join(data.split(':')[2:]).replace(endl, '').lower()
            sender = data.split('!')[0].replace(':', '').lower()
            # Log it!
            write_log(channel, '{0} {1} joined {2}.'.format(timestamp(), sender,
                                                            channel))

        # Handle part events.
        elif 'PART' in data:
            # Data extraction magic:
            channel = ':'.join(data.split(':')[2:]).replace(endl, '').lower()
            sender = data.split('!')[0].replace(':', '').lower()
            # Log it!
            write_log(channel, '{0} {1} joined {2}.'.format(timestamp(), sender,
                                                            channel))


# Disconnect.
irc.send('QUIT' + endl)
irc.close()
