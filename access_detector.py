import asyncio

from systemd import journal
from datetime import datetime, timedelta, timezone

# Contains all authorized PID's
authorized_pids  = []
notified_entries = []
closed_pids      = []

def add_closed_pid(real_ts, pid):
	p = {'pid': pid, 'ts': real_ts}

	if p not in closed_pids:
		print(f'Added {pid} to closed pids.')
		closed_pids.append(p)

def remove_old_closed_pids():
	for closed in closed_pids:
		t = datetime.now(timezone.utc) - closed['ts']

		# Over 1 hour since it was marked as closed_pid
		if t.seconds > 3600:
			print(f'Removing OLD closed pid: {closed["pid"]}')
			closed_pids.remove(closed)

def is_authorized_entry(entry, ip_whitelist):
	msg = entry['MESSAGE']
	pid = entry['_PID']

	for closed in closed_pids:
		if closed['pid'] == pid:
			return True

	if pid in authorized_pids:
		if 'session closed' in msg or 'Received disconnect' in msg or 'Disconnected' in msg:
			print(f'Removed pid: {pid} from authorized pids.')
			authorized_pids.remove(pid)
			add_closed_pid(entry['__REALTIME_TIMESTAMP'], pid)
		return True

	for ip in ip_whitelist:
		if ip in msg:
			print(f'Added pid: {pid} to authorized pids. IP-Address: {ip} found in message.')
			authorized_pids.append(pid)
			return True

	return False

def load_entries(ip_whitelist):
	j = journal.Reader()
	j.seek_realtime(datetime.now() - timedelta(hours=1))
	j.add_match('_COMM=sshd')

	entries = []

	for entry in j:
		if not is_authorized_entry(entry, ip_whitelist):
			entries.append(entry)

	return entries

async def watch_entries(client, settings):
	while True:
		entries = load_entries(settings['ip_whitelist'])

		for entry in entries:
			if entry not in notified_entries:
				notified_entries.append(entry)

				channel = client.get_channel(settings['channel_id'])
				await channel.send(f'<@{settings["owner_id"]}>, [{entry["SYSLOG_TIMESTAMP"]}] {entry["MESSAGE"]}')

		remove_old_closed_pids()

		# Check entries every 10 seconds.
		await asyncio.sleep(10)
