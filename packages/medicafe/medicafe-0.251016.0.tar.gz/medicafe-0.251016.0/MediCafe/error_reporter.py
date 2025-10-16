import os, sys, time, json, zipfile, hashlib, platform

try:
	import requests
except Exception:
	requests = None

from MediCafe.MediLink_ConfigLoader import load_configuration, log as mc_log


ASCII_SAFE_REPLACEMENTS = [
	('"', '"'),
	("'", "'"),
]


def _safe_ascii(text):
	try:
		if text is None:
			return ''
		if isinstance(text, bytes):
			try:
				text = text.decode('ascii', 'ignore')
			except Exception:
				text = text.decode('utf-8', 'ignore')
		else:
			text = str(text)
		return text.encode('ascii', 'ignore').decode('ascii', 'ignore')
	except Exception:
		return ''


def _tail_file(path, max_lines):
	lines = []
	try:
		with open(path, 'r') as f:
			for line in f:
				lines.append(line)
				if len(lines) > max_lines:
					lines.pop(0)
		return ''.join(lines)
	except Exception:
		return ''


def _get_latest_log_path(local_storage_path):
	try:
		files = []
		for name in os.listdir(local_storage_path or '.'):
			if name.startswith('Log_') and name.endswith('.log'):
				files.append(os.path.join(local_storage_path, name))
		if not files:
			return None
		files.sort(key=lambda p: os.path.getmtime(p))
		return files[-1]
	except Exception:
		return None


def _redact(text):
	# Best-effort ASCII redaction: mask obvious numeric IDs and bearer tokens
	try:
		text = _safe_ascii(text)
		import re
		patterns = [
			(r'\b(\d{3}-?\d{2}-?\d{4})\b', '***-**-****'),
			(r'\b(\d{9,11})\b', '*********'),
			(r'Bearer\s+[A-Za-z0-9\-._~+/]+=*', 'Bearer ***'),
			(r'Authorization:\s*[^\n\r]+', 'Authorization: ***'),
		]
		for pat, rep in patterns:
			text = re.sub(pat, rep, text)
		return text
	except Exception:
		return text


def _ensure_dir(path):
	try:
		if not os.path.exists(path):
			os.makedirs(path)
		return True
	except Exception:
		return False


def _compute_report_id(zip_path):
	try:
		h = hashlib.sha256()
		with open(zip_path, 'rb') as f:
			chunk = f.read(256 * 1024)
			h.update(chunk)
		return 'mc-{}-{}'.format(int(time.time()), h.hexdigest()[:12])
	except Exception:
		return 'mc-{}-{}'.format(int(time.time()), '000000000000')


def collect_support_bundle(include_traceback=True, max_log_lines=2000):
	config, _ = load_configuration()
	medi = config.get('MediLink_Config', {})
	local_storage_path = medi.get('local_storage_path', '.')
	queue_dir = os.path.join(local_storage_path, 'reports_queue')
	_ensure_dir(queue_dir)

	stamp = time.strftime('%Y%m%d_%H%M%S')
	bundle_name = 'support_report_{}.zip'.format(stamp)
	zip_path = os.path.join(queue_dir, bundle_name)

	latest_log = _get_latest_log_path(local_storage_path)
	log_tail = _tail_file(latest_log, max_log_lines) if latest_log else ''
	log_tail = _redact(log_tail)

	traceback_txt = ''
	if include_traceback:
		try:
			trace_path = os.path.join(local_storage_path, 'traceback.txt')
			if os.path.exists(trace_path):
				with open(trace_path, 'r') as tf:
					traceback_txt = _redact(tf.read())
		except Exception:
			traceback_txt = ''

	meta = {
		'app_version': _safe_ascii(_get_version()),
		'python_version': _safe_ascii(sys.version.split(' ')[0]),
		'platform': _safe_ascii(platform.platform()),
		'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
		'error_summary': _safe_ascii(_first_line(traceback_txt)),
		'traceback_present': bool(traceback_txt),
		'config_flags': {
			'console_logging': bool(medi.get('logging', {}).get('console_output', False)),
			'test_mode': bool(medi.get('TestMode', False))
		}
	}

	try:
		with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
			z.writestr('meta.json', json.dumps(meta, ensure_ascii=True, indent=2))
			if latest_log and log_tail:
				z.writestr('log_tail.txt', log_tail)
			if traceback_txt:
				z.writestr('traceback.txt', traceback_txt)
			z.writestr('README.txt', _readme_text())
		return zip_path
	except Exception as e:
		mc_log('Error creating support bundle: {}'.format(e), level='ERROR')
		return None


def _first_line(text):
	try:
		for line in (text or '').splitlines():
			line = line.strip()
			if line:
				return line[:200]
		return ''
	except Exception:
		return ''


def _readme_text():
	return (
		"MediCafe Support Bundle\n\n"
		"This archive contains a redacted log tail, optional traceback, and metadata.\n"
		"You may submit this bundle automatically from the app or send it manually to support.\n"
	)


def _get_version():
	try:
		from MediCafe import __version__
		return __version__
	except Exception:
		return 'unknown'


def submit_support_bundle(zip_path):
	config, _ = load_configuration()
	medi = config.get('MediLink_Config', {})
	rep = medi.get('error_reporting', {}) if isinstance(medi, dict) else {}
	endpoint_url = _safe_ascii(rep.get('endpoint_url', ''))
	auth_token = _safe_ascii(rep.get('auth_token', ''))
	insecure = bool(rep.get('insecure_http', False))
	max_bytes = int(rep.get('max_bundle_bytes', 2097152))

	if not requests:
		print("[ERROR] requests module not available; cannot submit report.")
		return False
	if not endpoint_url:
		print("[ERROR] error_reporting.endpoint_url not configured.")
		return False
	if not os.path.exists(zip_path):
		print("[ERROR] Bundle not found: {}".format(zip_path))
		return False
	try:
		size = os.path.getsize(zip_path)
		if size > max_bytes:
			print("[INFO] Bundle size {} exceeds cap {}; rebuilding smaller not implemented here.".format(size, max_bytes))
	except Exception:
		pass

	report_id = _compute_report_id(zip_path)
	headers = {
		'X-Auth-Token': auth_token or '',
		'X-Report-Id': report_id,
		'User-Agent': 'MediCafe-Reporter/1.0'
	}

	# Prepare meta.json stream derived from inside the zip for server convenience
	meta_json = '{}'
	try:
		with zipfile.ZipFile(zip_path, 'r') as z:
			if 'meta.json' in z.namelist():
				meta_json = z.read('meta.json')
	except Exception:
		meta_json = '{}'

	try:
		bundle_fh = open(zip_path, 'rb')
		files = {
			'meta': ('meta.json', meta_json, 'application/json'),
			'bundle': (os.path.basename(zip_path), bundle_fh, 'application/zip')
		}
		r = requests.post(endpoint_url, headers=headers, files=files, timeout=(10, 20), verify=(not insecure))
		code = getattr(r, 'status_code', None)
		if code == 200:
			print("[SUCCESS] Report submitted. ID: {}".format(report_id))
			return True
		elif code == 401:
			print("[ERROR] Unauthorized (401). Check error_reporting.auth_token.")
			return False
		elif code == 413:
			print("[ERROR] Too large (413). Consider reducing max log lines.")
			return False
		else:
			print("[ERROR] Submission failed with status {}".format(code))
			return False
	except Exception as e:
		print("[ERROR] Submission exception: {}".format(e))
		return False
	finally:
		try:
			bundle_fh.close()
		except Exception:
			pass


def flush_queued_reports():
	config, _ = load_configuration()
	medi = config.get('MediLink_Config', {})
	local_storage_path = medi.get('local_storage_path', '.')
	queue_dir = os.path.join(local_storage_path, 'reports_queue')
	if not os.path.isdir(queue_dir):
		return 0, 0
	count_ok = 0
	count_total = 0
	for name in sorted(os.listdir(queue_dir)):
		if not name.endswith('.zip'):
			continue
		zip_path = os.path.join(queue_dir, name)
		count_total += 1
		print("Attempting upload of queued report: {}".format(name))
		ok = submit_support_bundle(zip_path)
		if ok:
			try:
				os.remove(zip_path)
			except Exception:
				pass
			count_ok += 1
	return count_ok, count_total


def capture_unhandled_traceback(exc_type, exc_value, exc_traceback):
	try:
		config, _ = load_configuration()
		medi = config.get('MediLink_Config', {})
		local_storage_path = medi.get('local_storage_path', '.')
		trace_path = os.path.join(local_storage_path, 'traceback.txt')
		import traceback
		text = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
		text = _redact(text)
		with open(trace_path, 'w') as f:
			f.write(text)
		print("An error occurred. A traceback was saved to {}".format(trace_path))
	except Exception:
		pass

