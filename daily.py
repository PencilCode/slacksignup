# A script to periodically poll the Google spreadsheets
# signup, and add people to the slack group

import os, time, urllib, urllib2, csv, json

slackinviteurl = (
    'https://pencilcode.slack.com/api/users.admin.invite?t=' +
    str(int(time.time())))
slackchannels = 'C07M2MC5S'
slacktoken = open(os.path.join(
    os.path.dirname(os.path.realpath(__file__)), 'slack.token')).read().strip()

googleformcsv = (
    'https://docs.google.com/spreadsheets/d/' +
    '1ds0B7KN26b8z5CSZejrdHbGwGzyDXNpsC9smw0L6RH8/pub?' +
    'gid=376741817&single=true&output=csv')
timeformat = "%m/%d/%Y %H:%M:%S"
statusfile = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), 'status.csv')
lasttime = (0, 0, 0, 0, 0, 0, 0)
try:
  with open(statusfile, 'r') as f:
    statusreader = csv.reader(f)
    for row in statusreader:
      [timestamp, email, name, comment, status, note] = row
      t = time.strptime(timestamp, timeformat)
      if t > lasttime:
        lasttime = t
except Exception:
  pass

# Open up the file for writing status
statuswriter = csv.writer(open(statusfile, 'ab+'))

# Fetch the Google spreadsheet
resp = urllib2.urlopen(googleformcsv)
reader = csv.reader(resp)
# skip the header row
reader.next()

# Read all the lines
linecount = 0
requested = 0
invited = 0
for row in reader:
  status = False
  note = ''
  linecount += 1
  [timestamp, email, name, comment] = row

  try:
    # Parse timestamp and discard old rows
    t = time.strptime(timestamp, timeformat)
    if t <= lasttime:
      continue

    # Parse email and discard non-email-addresses
    email = email.strip()
    if '@' not in email:
      continue

    # Parse firstname-lastname
    splitname = name.split(None, 1)
    first = last = ''
    if len(splitname) > 0:
      first = splitname[0]
    if len(splitname) > 1:
      last = splitname[1]

    # Post to slack
    payload = {
      'email': email,
      'channels': slackchannels,
      'first_name': first,
      'last_name': last,
      'token': slacktoken,
      'set_active': 'true'
    }
    requested += 1
    data = urllib.urlencode(payload)
    response = json.load(urllib2.urlopen(urllib2.Request(slackinviteurl, data)))
    status = response['ok']
    if 'error' in response:
      note = response['error']
    if status:
      invited += 1
  except Exception as e:
    note = str(e)

  statuswriter.writerow([timestamp, email, name, comment,
     status and 'true' or 'false',
     note])

print 'Read', linecount, 'lines.', requested, 'added', invited, 'invited'
