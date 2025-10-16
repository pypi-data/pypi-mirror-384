import time
from datetime import datetime
from datetime import timedelta
import traceback
from .client import request_post
from .client import request_get

JOBS = "jobs"
FIVE_MINUES = timedelta(minutes=5)


def create_search_job(query, start: datetime = None, end: datetime = None, limit=100, timeout_ms=1000,
                      return_type="json"):
    start_timestamp = end_timestamp = 0
    if start is None:
        start = datetime.now() - FIVE_MINUES
        start_timestamp = int(start.timestamp() * 1000)
    if end is None:
        end = datetime.now()
        end_timestamp = int(end.timestamp() * 1000)

    if isinstance(start, int):
        start_timestamp = start

    if isinstance(end, int):
        end_timestamp = end

    data = {
        "query": query,
        "startTime": start_timestamp,
        "endTime": end_timestamp,
        "collectSize": limit,
        "timeout": timeout_ms,

        "app": "search",
        "preview": False,
        "mode": "smart",
    }


    if return_type == "json":
        return request_post(JOBS, data=data, custom_headers={"Content-Type": "application/json"}).json()
    else:
        return request_post(JOBS, data=data, custom_headers={"Content-Type": "application/json"})


def get_search_job_status(jobid, return_type="json"):
    if return_type == "json":
        return request_get(f"{JOBS}/{jobid}", custom_headers={"Content-Type": "application/json"}).json()
    else:
        return request_get(f"{JOBS}/{jobid}", custom_headers={"Content-Type": "application/json"})


def get_search_job_result(jobid):
    return request_get(f"{JOBS}/{jobid}/results", custom_headers={"Content-Type": "application/json"}).json()

def get_search_job_summary(jobid):
    return request_get(f"{JOBS}/{jobid}/summary", custom_headers={"Content-Type": "application/json"}).json()

def search_spl(spl, start=None, end=None, limit=100, req_timeout=3000):
    resp = create_search_job(query=spl, start=start, end=end, limit=limit, timeout_ms=req_timeout)
    jobid = ""
    if ("meta" in resp) and resp["meta"]["process"] == 1:
        return resp["result"]
    else:
        jobid = resp["id"]

    while True:
        status = get_search_job_status(jobid)
        if ("process" in status) and status["process"] == 1:
            break
        time.sleep(0.2)
    return get_search_job_result(jobid)

def search_summary(spl, start=None, end=None, limit=100, req_timeout=3000):
    resp = create_search_job(query=spl, start=start, end=end, limit=limit, timeout_ms=req_timeout)
    jobid = resp["id"]

    while True:
        status = get_search_job_status(jobid)
        if ("process" in status) and status["process"] == 1:
            break
        time.sleep(0.2)
    return get_search_job_summary(jobid)

def search_spl_meta(spl, start=None, end=None, limit=100, req_timeout=30000):
    if start:
        start = int(start * 1000)
    if end:
        end = int(end * 1000)
    result = {
        'duration': 0, 'query': spl,
        'range': {
            'start': datetime.fromtimestamp(start / 1000).strftime('%Y-%m-%d %H:%M:%S'),
            'end': datetime.fromtimestamp(end / 1000).strftime('%Y-%m-%d %H:%M:%S')
        }
    }
    resp = create_search_job(query=spl, start=start, end=end, limit=limit, timeout_ms=req_timeout, return_type="raw")
    resp_data = resp.json()
    result['status_code'] = resp.status_code
    if resp.status_code == 200 and "meta" in resp_data and resp_data["meta"]["process"] == 1:
        result['duration'] = round(resp.elapsed.total_seconds() * 1000)
        result['resultSize'] = resp_data['meta']['resultSize']
        return result

    elif resp.status_code == 200:
        jobid = resp["id"]

    else:
        result['message'] = resp.text
        return result

    while True:
        status = get_search_job_status(jobid, return_type="raw")
        result['status_code'] = status.status_code
        result['duration'] += round(status.elapsed.total_seconds() * 1000)
        status_data = status.json()
        if ("process" in status_data) and status_data["process"] == 1:
            result['resultSize'] = status_data['meta']['resultSize']
            return status
        time.sleep(0.2)


def search_pql(base_url, pql, start=None, end=None, limit=100, req_timeout=30000):
    """
    promtheus query language
    Args:
        pql:
        start:
        end:
        limit:
        req_timeout:

    Returns:

    """
    url = "{}/api/v1/query_range".format(base_url)
    if not end:
        end = time.time()

    if not start:
        start = end - 600

    params = {
        "query": pql,
        "start": start,
        "end": end,
        "step": "60",
        "limit": limit,
        "timeout": req_timeout,
        'nocache': 1
    }
    resp = {"query": pql, 'range': {
        'start': datetime.fromtimestamp(start).strftime('%Y-%m-%d %H:%M:%S'),
        'end': datetime.fromtimestamp(end).strftime('%Y-%m-%d %H:%M:%S')
    }}

    try:
        result = request_get(url, query_params=params)
        resp['status_code'] = result.status_code
        if result.status_code != 200:
            resp['message'] = result.text
            resp['duration'] = result.elapsed.total_seconds() * 1000
            return resp

        resp['resultSize'] = len(result.json()['data']['result'])
        data = result.json()['data']['result']
        resp['metricSize'] = sum([len(x['values']) for x in data])
        resp['duration'] = result.elapsed.total_seconds() * 1000
    except Exception as e:
        traceback.print_exc()
        resp['message'] = e
        resp['duration'] = 0
        return resp
    return resp


if __name__ == "__main__":
    # print(search_spl('search2 repo="*"', limit=1, req_timeout=1000))
    print(search_pql('http://192.168.10.78:9090', 'avg by (instance,device) (node_disk_read_bytes_total)'))
