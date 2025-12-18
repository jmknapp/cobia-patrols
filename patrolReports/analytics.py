"""
Analytics module for parsing Apache access logs.
Supports reading rotated logs (including .gz compressed files).
"""

import re
import os
import gzip
import glob
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from pathlib import Path

# Apache combined log format regex
LOG_PATTERN = re.compile(
    r'(?P<ip>\d+\.\d+\.\d+\.\d+)\s+'
    r'(?P<identd>-|\S+)\s+'
    r'(?P<user>-|\S+)\s+'
    r'\[(?P<time>[^\]]+)\]\s+'
    r'"(?P<method>\w+)\s+(?P<path>[^\s]+)\s+[^"]*"\s+'
    r'(?P<status>\d+)\s+'
    r'(?P<size>-|\d+)\s+'
    r'"(?P<referer>[^"]*)"\s+'
    r'"(?P<user_agent>[^"]*)"'
)

# Default log path (can be overridden)
DEFAULT_LOG_PATH = '/var/log/apache2/cobiapatrols_access.log'

def parse_log_line(line):
    """Parse a single Apache log line."""
    match = LOG_PATTERN.match(line)
    if match:
        return match.groupdict()
    return None

def should_filter_ip(ip):
    """Check if IP should be filtered out (local network)."""
    if ip.startswith('192.168.'):
        return True
    if ip.startswith('10.'):
        return True
    if ip.startswith('172.') and 16 <= int(ip.split('.')[1]) <= 31:
        return True
    if ip == '127.0.0.1':
        return True
    return False

AI_BOT_PATTERNS = [
    'gptbot', 'chatgpt', 'openai',           # OpenAI
    'claudebot', 'claude-web', 'anthropic',   # Anthropic
    'google-extended',                        # Google AI training
    'cohere-ai',                              # Cohere
    'bytespider',                             # ByteDance/TikTok AI
    'ccbot',                                  # Common Crawl (AI training)
    'perplexitybot',                          # Perplexity AI
    'youbot',                                 # You.com AI
    'ia_archiver',                            # Internet Archive (used for AI)
    'amazonbot',                              # Amazon AI
    'meta-externalagent',                     # Meta AI
    'diffbot',                                # Diffbot AI
]

REGULAR_BOT_PATTERNS = [
    'bot', 'crawler', 'spider', 'slurp', 'googlebot', 'bingbot',
    'yandex', 'baidu', 'duckduckbot', 'facebookexternalhit',
    'twitterbot', 'linkedinbot', 'semrush', 'ahrefsbot', 'mj12bot',
    'dotbot', 'petalbot', 'applebot', 'seznambot',
]

def is_ai_bot(user_agent):
    """Check if user agent is an AI scraper/trainer."""
    ua_lower = user_agent.lower()
    return any(bot in ua_lower for bot in AI_BOT_PATTERNS)

def is_bot(user_agent):
    """Check if user agent is likely a bot (including AI bots)."""
    ua_lower = user_agent.lower()
    return any(bot in ua_lower for bot in REGULAR_BOT_PATTERNS + AI_BOT_PATTERNS)

def parse_apache_time(time_str):
    """Parse Apache log timestamp."""
    try:
        # Format: 16/Dec/2025:14:30:45 +0000
        return datetime.strptime(time_str.split()[0], '%d/%b/%Y:%H:%M:%S')
    except:
        return None

def get_analytics(log_path=None, days=30):
    """
    Parse Apache logs and return analytics data.
    
    Args:
        log_path: Path to Apache access log
        days: Number of days to analyze
    
    Returns:
        Dictionary with analytics data
    """
    if log_path is None:
        log_path = DEFAULT_LOG_PATH
    
    # Find all log files (current + rotated)
    log_files = []
    if os.path.exists(log_path):
        log_files.append(log_path)
    
    # Find rotated logs: access.log.1, access.log.2.gz, etc.
    log_dir = os.path.dirname(log_path)
    log_base = os.path.basename(log_path)
    for rotated in glob.glob(os.path.join(log_dir, f'{log_base}.*')):
        log_files.append(rotated)
    
    # Sort by modification time (newest first) for efficiency
    log_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    
    if not log_files:
        return {
            'error': f'Log file not found: {log_path}',
            'total_hits': 0,
            'unique_visitors': 0,
            'page_views': {},
            'daily_hits': {},
            'top_referers': [],
            'browsers': {},
            'bot_hits': 0,
            'status_codes': {},
        }
    
    cutoff_date = datetime.now() - timedelta(days=days)
    
    # Counters
    total_hits = 0
    filtered_hits = 0
    bot_hits = 0
    ai_bot_hits = Counter()  # Track AI bots specifically
    unique_ips = set()
    ip_hits = Counter()  # Track hits per IP
    page_views = Counter()
    daily_hits = defaultdict(int)
    daily_visitors = defaultdict(set)
    referers = Counter()
    browsers = Counter()
    status_codes = Counter()
    hourly_hits = defaultdict(int)
    last_24h_hits = defaultdict(int)  # Actual last 24 hours timeline
    user_agents = Counter()  # Track user agents
    error_paths = Counter()  # Track 404 paths
    paths_by_type = {
        'pages': Counter(),
        'api': Counter(),
        'static': Counter(),
        'pdfs': Counter(),
    }
    
    try:
        for log_file in log_files:
            # Open gzipped or plain text files
            if log_file.endswith('.gz'):
                f = gzip.open(log_file, 'rt', errors='ignore')
            else:
                f = open(log_file, 'r', errors='ignore')
            
            try:
                for line in f:
                    parsed = parse_log_line(line)
                    if not parsed:
                        continue
                    
                    ip = parsed['ip']
                    
                    # Filter local IPs
                    if should_filter_ip(ip):
                        filtered_hits += 1
                        continue
                    
                    # Parse timestamp
                    log_time = parse_apache_time(parsed['time'])
                    if not log_time or log_time < cutoff_date:
                        continue
                    
                    total_hits += 1
                    path = parsed['path']
                    user_agent = parsed['user_agent']
                    status = parsed['status']
                    referer = parsed['referer']
                    
                    # Check for bots
                    if is_bot(user_agent):
                        bot_hits += 1
                        # Track AI bots specifically
                        if is_ai_bot(user_agent):
                            for pattern in AI_BOT_PATTERNS:
                                if pattern in user_agent.lower():
                                    ai_bot_hits[pattern] += 1
                                    break
                        continue  # Skip bots from main stats
                    
                    # Track unique visitors
                    unique_ips.add(ip)
                    ip_hits[ip] += 1
                    user_agents[user_agent[:100]] += 1  # Truncate long UAs
                    
                    # Daily stats
                    date_key = log_time.strftime('%Y-%m-%d')
                    daily_hits[date_key] += 1
                    daily_visitors[date_key].add(ip)
                    
                    # Hourly distribution (aggregate by hour of day)
                    hourly_hits[log_time.hour] += 1
                    
                    # Last 24 hours timeline (actual hours)
                    hours_ago = (datetime.now() - log_time).total_seconds() / 3600
                    if hours_ago <= 24:
                        hour_key = log_time.strftime('%Y-%m-%d %H:00')
                        last_24h_hits[hour_key] += 1
                    
                    # Status codes
                    status_codes[status] += 1
                    
                    # Track 404 paths
                    if status == '404':
                        error_paths[path.split('?')[0]] += 1
                    
                    # Categorize paths
                    if path.startswith('/static/'):
                        paths_by_type['static'][path] += 1
                    elif path.startswith('/api/') or path.startswith('/search'):
                        paths_by_type['api'][path.split('?')[0]] += 1
                    elif path.startswith('/pdfs/') or path.endswith('.pdf'):
                        paths_by_type['pdfs'][path] += 1
                    elif path.startswith('/view'):
                        # Extract PDF name from query
                        if 'file=' in path:
                            pdf_name = path.split('file=')[1].split('&')[0]
                            paths_by_type['pages'][f'/view ({pdf_name})'] += 1
                        else:
                            paths_by_type['pages']['/view'] += 1
                    else:
                        paths_by_type['pages'][path.split('?')[0]] += 1
                    
                    # Page views (exclude static assets)
                    if not path.startswith('/static/') and not path.endswith(('.js', '.css', '.png', '.jpg', '.ico', '.svg')):
                        page_views[path.split('?')[0]] += 1
                    
                    # Referers (external only)
                    if referer and referer != '-' and 'cobiapatrols.com' not in referer:
                        # Clean up referer
                        try:
                            from urllib.parse import urlparse
                            parsed_ref = urlparse(referer)
                            ref_domain = parsed_ref.netloc
                            if ref_domain:
                                referers[ref_domain] += 1
                        except:
                            pass
                    
                    # Browsers
                    if 'Firefox' in user_agent:
                        browsers['Firefox'] += 1
                    elif 'Chrome' in user_agent and 'Edg' not in user_agent:
                        browsers['Chrome'] += 1
                    elif 'Safari' in user_agent and 'Chrome' not in user_agent:
                        browsers['Safari'] += 1
                    elif 'Edg' in user_agent:
                        browsers['Edge'] += 1
                    else:
                        browsers['Other'] += 1
            finally:
                f.close()
    
    except Exception as e:
        return {'error': str(e)}
    
    # Calculate daily visitor counts
    daily_visitor_counts = {date: len(ips) for date, ips in daily_visitors.items()}
    
    # Sort daily data
    sorted_dates = sorted(daily_hits.keys())
    
    return {
        'total_hits': total_hits,
        'filtered_hits': filtered_hits,
        'bot_hits': bot_hits,
        'ai_bot_hits': dict(ai_bot_hits.most_common(10)),
        'unique_visitors': len(unique_ips),
        'page_views': dict(page_views.most_common(20)),
        'daily_hits': {d: daily_hits[d] for d in sorted_dates},
        'daily_visitors': {d: daily_visitor_counts.get(d, 0) for d in sorted_dates},
        'top_referers': referers.most_common(10),
        'browsers': dict(browsers),
        'status_codes': dict(status_codes),
        'error_paths': dict(error_paths.most_common(10)),
        'hourly_distribution': dict(hourly_hits),
        'last_24h': {k: last_24h_hits[k] for k in sorted(last_24h_hits.keys())},
        'paths_by_type': {k: dict(v.most_common(10)) for k, v in paths_by_type.items()},
        'top_ips': ip_hits.most_common(15),
        'top_user_agents': user_agents.most_common(10),
        'days_analyzed': days,
        'log_path': log_path,
        'log_files_read': len(log_files),
    }


if __name__ == '__main__':
    # Test with sample data
    import json
    stats = get_analytics(days=7)
    print(json.dumps(stats, indent=2, default=str))

