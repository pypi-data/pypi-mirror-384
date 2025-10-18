"""Mock数据生成插件

此插件包含所有mock数据生成相关的命令：
- mock_data: 生成通用数据
- mock_log: 生成日志数据
- mock_metrics: 生成指标数据
"""

import time
import json
import os
import math
import multiprocessing
import tempfile
import random
import shutil
import socket
import struct
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Manager
from rich.progress import Progress
from rich.console import Console
from mando import command, arg

from ketacli.sdk.util import Template, format_bytes
from ketacli.sdk.base.client import request_post

# 尝试导入ujson，如果不可用则使用标准json
try:
    import ujson as json_serializer
    USE_UJSON = True
except ImportError:
    import json as json_serializer
    USE_UJSON = False

# 创建控制台对象
console = Console()


class LogGenerator:
    """日志生成器类，用于生成不同类型的日志模板
    
    这个类抽象了不同日志类型的生成逻辑，支持多种日志类型，包括：
    - nginx: Nginx访问日志
    - java: Java应用日志
    - linux: Linux系统日志
    - apache: Apache访问日志
    - mysql: MySQL数据库日志
    - windows: Windows事件日志
    - mongodb: MongoDB数据库日志
    - docker: Docker容器日志
    
    每种日志类型都支持两种渲染模式：
    - render=True: 使用Jinja2模板引擎渲染，支持动态内容
    - render=False: 使用f-strings直接生成，性能更好
    
    使用示例：
    ```python
    generator = LogGenerator()
    nginx_log = generator.generate_log("nginx", render=True)
    java_log = generator.generate_log("java", render=False)
    ```
    """
    
    def __init__(self):
        """初始化日志生成器"""
        
        # 初始化日志类型映射
        self._log_generators = {
            "nginx": self._generate_nginx_log,
            "java": self._generate_java_log,
            "linux": self._generate_linux_log,
            "apache": self._generate_apache_log,
            "mysql": self._generate_mysql_log,
            "windows": self._generate_windows_log,
            "mongodb": self._generate_mongodb_log,
            "docker": self._generate_docker_log,
        }
    
    def get_supported_log_types(self):
        """获取支持的日志类型列表
        
        Returns:
            list: 支持的日志类型列表
        """
        return list(self._log_generators.keys())
    
    def generate_log(self, log_type="nginx", render=False):
        """生成指定类型的日志
        
        Args:
            log_type (str): 日志类型，支持 "nginx", "java", "linux", "apache", "mysql", "windows"
            render (bool): 是否使用Jinja2渲染，True使用模板渲染，False使用f-strings
            
        Returns:
            str: 生成的日志JSON字符串
        
        Raises:
            ValueError: 如果指定的日志类型不支持
        """
        if log_type not in self._log_generators:
            raise ValueError(f"不支持的日志类型: {log_type}，支持的类型: {', '.join(self.get_supported_log_types())}")
        
        # 调用对应的日志生成函数
        return self._log_generators[log_type](render)
    
    def _generate_nginx_log(self, render):
        """生成Nginx访问日志"""
        if render:
            data = (
                '{"raw":"{{ random.choice([\"192.168.1.1\", \"192.168.1.2\", \"192.168.1.3\", \"192.168.1.4\", \"192.168.1.5\"]) }} - - '
                '[{{ time.strftime(\"%d/%b/%Y:%H:%M:%S +0000\", time.localtime()) }}] '
                '\\\"{{ random.choice([\"GET\", \"POST\", \"PUT\"]) }} {{ random.choice([\"/\", \"/index.html\", \"/api/v1/users\", \"/login\", \"/static/css/main.css\"]) }} HTTP/1.1\\\" '
                '{{ random.choice([\"200\", \"201\", \"301\", \"302\", \"304\", \"400\", \"404\", \"500\"]) }} '
                '{{ random.randint(100, 10000) }} '
                '\\\"{{ random.choice([\"http://example.com\", \"http://referer.com\", \"-\"]) }}\\\" '
                '\\\"Mozilla/5.0 ({{ random.choice([\"Windows NT 10.0\", \"Macintosh\", \"Linux x86_64\", \"iPhone; CPU iPhone OS 14_0\"]) }}) '
                '{{ random.choice([\"Chrome/90.0.4430.212\", \"Safari/537.36\", \"Firefox/88.0\", \"Edge/91.0.864.48\"]) }}\\\"",' 
                '"host":"{{ random.choice([\"web-server-01\", \"web-server-02\", \"web-server-03\", \"web-server-04\", \"web-server-05\"]) }}",'
                '"origin": "nginx"'
                '}'
            )
        else:
            data = (
                f'{{"raw": "{random.choice(["192.168.1.1", "192.168.1.2", "192.168.1.3", "192.168.1.4", "192.168.1.5"])} - - '
                f'[{time.strftime("%d/%b/%Y:%H:%M:%S +0000", time.localtime())}] \\"{random.choice(["GET", "POST", "PUT", "DELETE"])} {random.choice(["/", "/index.html", "/api/v1/users", "/login", "/static/css/main.css"])} '
                f'HTTP/1.1\\" {random.choice(["200", "201", "301", "302", "304", "400", "404", "500"])} {random.randint(100, 10000)} '
                f'\\"-\\" \\"Mozilla/5.0 ({random.choice(["Windows NT 10.0", "Macintosh", "Linux x86_64", "iPhone; CPU iPhone OS 14_0"])}) '
                f'{random.choice(["Chrome/90.0.4430.212", "Safari/537.36", "Firefox/88.0", "Edge/91.0.864.48"])}\\"", '
                f'"host": "{random.choice(["web-server-01", "web-server-02", "web-server-03", "web-server-04", "web-server-05"])}", '
                f'"origin": "nginx"}}'
            )
        return data
    
    def _generate_java_log(self, render):
        """生成Java应用日志"""
        if render:
            data = (
                '{"raw":"{{ time.strftime(\"%Y-%m-%d %H:%M:%S,%f\"[:-3], time.localtime()) }} '
                '[{{ random.choice([\"main\", \"http-nio-8080-exec-1\", \"pool-1-thread-1\", \"AsyncTask-1\", \"RMI TCP Connection\"]) }}] '
                '{{ random.choice([\"INFO\", \"DEBUG\", \"WARN\", \"ERROR\", \"TRACE\"]) }} '
                '{{ random.choice([\"com.example.Controller\", \"org.springframework.web.servlet.DispatcherServlet\", \"com.example.service.UserService\", \"com.example.repository.UserRepository\", \"org.hibernate.SQL\"]) }} - '
                '{{ faker.sentence() }}",' 
                '"host":"{{ random.choice([\"app-server-01\", \"app-server-02\", \"app-server-03\", \"app-server-04\", \"app-server-05\"]) }}",'
                '"level":"{{ random.choice([\"INFO\", \"DEBUG\", \"WARN\", \"ERROR\", \"TRACE\"]) }}",'
                '"thread":"{{ random.choice([\"main\", \"http-nio-8080-exec-1\", \"pool-1-thread-1\", \"AsyncTask-1\", \"RMI TCP Connection\"]) }}",'
                '"class":"{{ random.choice([\"com.example.Controller\", \"org.springframework.web.servlet.DispatcherServlet\", \"com.example.service.UserService\", \"com.example.repository.UserRepository\", \"org.hibernate.SQL\"]) }}",'
                '"origin": "java"'
                '}'
            )
        else:
            log_levels = ["INFO", "DEBUG", "WARN", "ERROR", "TRACE"]
            threads = ["main", "http-nio-8080-exec-1", "pool-1-thread-1", "AsyncTask-1", "RMI TCP Connection"]
            classes = ["com.example.Controller", "org.springframework.web.servlet.DispatcherServlet", 
                      "com.example.service.UserService", "com.example.repository.UserRepository", "org.hibernate.SQL"]
            hosts = ["app-server-01", "app-server-02", "app-server-03", "app-server-04", "app-server-05"]
            
            level = random.choice(log_levels)
            thread = random.choice(threads)
            class_name = random.choice(classes)
            host = random.choice(hosts)
            message = f"Processing request ID {random.randint(10000, 99999)} for user {random.choice(['user1', 'admin', 'guest', 'customer'])}"
            
            data = (
                f'{{"raw": "{time.strftime("%Y-%m-%d %H:%M:%S,%f"[:-3], time.localtime())} '
                f'[{thread}] {level} {class_name} - {message}", '
                f'"host": "{host}", '
                f'"level": "{level}", '
                f'"thread": "{thread}", '
                f'"class": "{class_name}", '
                f'"origin": "java"}}'
            )
        return data
    
    def _generate_linux_log(self, render):
        """生成Linux系统日志"""
        if render:
            data = (
                '{"raw":"{{ time.strftime(\"%b %d %H:%M:%S\", time.localtime()) }} '
                '{{ random.choice([\"localhost\", \"server-01\", \"server-02\", \"server-03\"]) }} '
                '{{ random.choice([\"kernel\", \"systemd\", \"sshd\", \"cron\", \"NetworkManager\"]) }}: '
                '{{ faker.sentence() }}",'
                '"host":"{{ random.choice([\"linux-server-01\", \"linux-server-02\", \"linux-server-03\"]) }}",'
                '"service":"{{ random.choice([\"kernel\", \"systemd\", \"sshd\", \"cron\", \"NetworkManager\"]) }}",'
                '"origin": "linux"'
                '}'
            )
        else:
            services = ["kernel", "systemd", "sshd", "cron", "NetworkManager"]
            hosts = ["linux-server-01", "linux-server-02", "linux-server-03"]
            servers = ["localhost", "server-01", "server-02", "server-03"]
            
            service = random.choice(services)
            host = random.choice(hosts)
            server = random.choice(servers)
            message = f"Service {service} status update: {random.choice(['started', 'stopped', 'restarted', 'failed'])}"
            
            data = (
                f'{{"raw": "{time.strftime("%b %d %H:%M:%S", time.localtime())} '
                f'{server} {service}: {message}", '
                f'"host": "{host}", '
                f'"service": "{service}", '
                f'"origin": "linux"}}'
            )
        return data
    
    def _generate_apache_log(self, render):
        """生成Apache访问日志"""
        if render:
            data = (
                '{"raw":"{{ random.choice([\"10.0.0.1\", \"10.0.0.2\", \"10.0.0.3\"]) }} - - '
                '[{{ time.strftime(\"%d/%b/%Y:%H:%M:%S +0000\", time.localtime()) }}] '
                '\\\"{{ random.choice([\"GET\", \"POST\", \"HEAD\"]) }} {{ random.choice([\"/\", \"/about\", \"/contact\", \"/products\"]) }} HTTP/1.1\\\" '
                '{{ random.choice([\"200\", \"404\", \"500\"]) }} {{ random.randint(200, 5000) }}",'
                '"host":"{{ random.choice([\"apache-server-01\", \"apache-server-02\"]) }}",'
                '"origin": "apache"'
                '}'
            )
        else:
            ips = ["10.0.0.1", "10.0.0.2", "10.0.0.3"]
            methods = ["GET", "POST", "HEAD"]
            paths = ["/", "/about", "/contact", "/products"]
            statuses = ["200", "404", "500"]
            hosts = ["apache-server-01", "apache-server-02"]
            
            data = (
                f'{{"raw": "{random.choice(ips)} - - '
                f'[{time.strftime("%d/%b/%Y:%H:%M:%S +0000", time.localtime())}] '
                f'\\"{random.choice(methods)} {random.choice(paths)} HTTP/1.1\\" '
                f'{random.choice(statuses)} {random.randint(200, 5000)}", '
                f'"host": "{random.choice(hosts)}", '
                f'"origin": "apache"}}'
            )
        return data
    
    def _generate_mysql_log(self, render):
        """生成MySQL数据库日志"""
        if render:
            data = (
                '{"raw":"{{ time.strftime(\"%Y-%m-%d %H:%M:%S\", time.localtime()) }} '
                '{{ random.choice([\"[Note]\", \"[Warning]\", \"[ERROR]\"]) }} '
                '{{ faker.sentence() }}",'
                '"host":"{{ random.choice([\"mysql-server-01\", \"mysql-server-02\"]) }}",'
                '"level":"{{ random.choice([\"Note\", \"Warning\", \"ERROR\"]) }}",'
                '"origin": "mysql"'
                '}'
            )
        else:
            levels = ["Note", "Warning", "ERROR"]
            hosts = ["mysql-server-01", "mysql-server-02"]
            
            level = random.choice(levels)
            host = random.choice(hosts)
            message = f"Query executed: SELECT * FROM users WHERE id = {random.randint(1, 1000)}"
            
            data = (
                f'{{"raw": "{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())} '
                f'[{level}] {message}", '
                f'"host": "{host}", '
                f'"level": "{level}", '
                f'"origin": "mysql"}}'
            )
        return data
    
    def _generate_windows_log(self, render):
        """生成Windows事件日志"""
        if render:
            data = (
                '{"raw":"{{ time.strftime(\"%Y-%m-%d %H:%M:%S\", time.localtime()) }} '
                'EventID: {{ random.randint(1000, 9999) }} '
                'Source: {{ random.choice([\"System\", \"Application\", \"Security\"]) }} '
                'Level: {{ random.choice([\"Information\", \"Warning\", \"Error\"]) }} '
                'Description: {{ faker.sentence() }}",'
                '"host":"{{ random.choice([\"WIN-SERVER-01\", \"WIN-SERVER-02\"]) }}",'
                '"event_id":"{{ random.randint(1000, 9999) }}",'
                '"source":"{{ random.choice([\"System\", \"Application\", \"Security\"]) }}",'
                '"level":"{{ random.choice([\"Information\", \"Warning\", \"Error\"]) }}",'
                '"origin": "windows"'
                '}'
            )
        else:
            sources = ["System", "Application", "Security"]
            levels = ["Information", "Warning", "Error"]
            hosts = ["WIN-SERVER-01", "WIN-SERVER-02"]
            
            event_id = random.randint(1000, 9999)
            source = random.choice(sources)
            level = random.choice(levels)
            host = random.choice(hosts)
            description = f"Windows service {random.choice(['started', 'stopped', 'failed'])}"
            
            data = (
                f'{{"raw": "{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())} '
                f'EventID: {event_id} Source: {source} Level: {level} Description: {description}", '
                f'"host": "{host}", '
                f'"event_id": "{event_id}", '
                f'"source": "{source}", '
                f'"level": "{level}", '
                f'"origin": "windows"}}'
            )
        return data
    
    def _generate_mongodb_log(self, render):
        """生成MongoDB数据库日志"""
        if render:
            data = (
                '{"raw":"{{ time.strftime(\"%Y-%m-%dT%H:%M:%S.000+0000\", time.localtime()) }} '
                '{{ random.choice([\"I\", \"W\", \"E\"]) }} '
                '{{ random.choice([\"COMMAND\", \"QUERY\", \"WRITE\", \"NETWORK\"]) }} '
                '{{ faker.sentence() }}",'
                '"host":"{{ random.choice([\"mongo-server-01\", \"mongo-server-02\"]) }}",'
                '"severity":"{{ random.choice([\"I\", \"W\", \"E\"]) }}",'
                '"component":"{{ random.choice([\"COMMAND\", \"QUERY\", \"WRITE\", \"NETWORK\"]) }}",'
                '"origin": "mongodb"'
                '}'
            )
        else:
            severities = ["I", "W", "E"]
            components = ["COMMAND", "QUERY", "WRITE", "NETWORK"]
            hosts = ["mongo-server-01", "mongo-server-02"]
            
            severity = random.choice(severities)
            component = random.choice(components)
            host = random.choice(hosts)
            message = f"MongoDB operation completed: {random.choice(['insert', 'update', 'delete', 'find'])}"
            
            data = (
                f'{{"raw": "{time.strftime("%Y-%m-%dT%H:%M:%S.000+0000", time.localtime())} '
                f'{severity} {component} {message}", '
                f'"host": "{host}", '
                f'"severity": "{severity}", '
                f'"component": "{component}", '
                f'"origin": "mongodb"}}'
            )
        return data
    
    def _generate_docker_log(self, render):
        """生成Docker容器日志"""
        if render:
            data = (
                '{"raw":"{{ time.strftime(\"%Y-%m-%dT%H:%M:%S.000000000Z\", time.localtime()) }} '
                'container={{ random.choice([\"web-app\", \"database\", \"redis\", \"nginx\"]) }} '
                'level={{ random.choice([\"info\", \"warn\", \"error\", \"debug\"]) }} '
                'msg=\\"{{ faker.sentence() }}\\"",'
                '"host":"{{ random.choice([\"docker-host-01\", \"docker-host-02\"]) }}",'
                '"container":"{{ random.choice([\"web-app\", \"database\", \"redis\", \"nginx\"]) }}",'
                '"level":"{{ random.choice([\"info\", \"warn\", \"error\", \"debug\"]) }}",'
                '"origin": "docker"'
                '}'
            )
        else:
            containers = ["web-app", "database", "redis", "nginx"]
            levels = ["info", "warn", "error", "debug"]
            hosts = ["docker-host-01", "docker-host-02"]
            
            container = random.choice(containers)
            level = random.choice(levels)
            host = random.choice(hosts)
            message = f"Container {container} status: {random.choice(['running', 'stopped', 'restarting'])}"
            
            data = (
                f'{{"raw": "{time.strftime("%Y-%m-%dT%H:%M:%S.000000000Z", time.localtime())} '
                f'container={container} level={level} msg=\\"{message}\\"", '
                f'"host": "{host}", '
                f'"container": "{container}", '
                f'"level": "{level}", '
                f'"origin": "docker"}}'
            )
        return data


# 创建日志生成器实例
log_generator = LogGenerator()


def process_batch_data(batch_data, query_params, gzip, progress, task_id):
    """
    Process a batch of pre-loaded data and upload them to the server.
    """
    if not batch_data:
        return 0, {"success": False, "total": 0}
    
    try:
        # 构建请求数据
        data_str = '\n'.join(batch_data)
        data_length = len(data_str.encode('utf-8'))
        
        # 发送请求
        response = request_post(query_params, data_str, gzip=gzip)
        
        # 更新进度
        if progress:
            progress.update(task_id, advance=len(batch_data))
        
        return data_length, {"success": True, "total": len(batch_data), "response": response}
    
    except Exception as e:
        console.print(f"Error processing batch: {str(e)}")
        return 0, {"success": False, "total": len(batch_data), "error": str(e)}


def generate_and_upload(data, count, query_params, gzip, progress, task_id, output_type='server', output_file=None, worker_id=None, render=True):
    """
    Generate mock data and upload in a batch.
    :param data: The JSON string template.
    :param count: Number of data items to generate.
    :param query_params: Query parameters for the upload.
    :param gzip: Whether to use gzip for the request.
    :param progress: Shared progress object.
    :param task_id: Task ID for tracking progress.
    :param output_type: Where to write the data, 'server' or 'file'.
    :param output_file: File path to write data when output_type is 'file'.
    :param worker_id: Worker ID for creating worker-specific temp files.
    :return: Tuple of data length and response.
    """
    # 创建一次Template对象，避免重复创建
    temp = Template(data)
    
    # 使用批量渲染功能一次性生成所有数据
    rendered_texts = temp.batch_render(count, render=render)
    
    # 直接计算数据长度，避免额外的迭代
    data_length = sum(len(text) for text in rendered_texts)
    
    # 预分配列表大小以避免动态扩展
    local_datas = [None] * count
    
    # 批量解析JSON - 使用分块处理以提高性能
    CHUNK_SIZE = 5000  # 每次处理的数据量
    for i in range(0, count, CHUNK_SIZE):
        chunk = rendered_texts[i:i+CHUNK_SIZE]
        # 使用列表推导式批量解析JSON并直接赋值
        parsed_chunk = [json.loads(text) for text in chunk]
        # 将解析结果放入预分配的列表中
        for j, item in enumerate(parsed_chunk):
            local_datas[i+j] = item

    response = None
    if local_datas:
        if output_type == 'server':
            # 发送到服务端
            response = request_post("data", local_datas, query_params, gzip=gzip).json()
        elif output_type == 'file':
            # 写入文件
            if worker_id is not None:
                # 多进程模式，写入临时文件
                temp_file = f"{output_file}.tmp.{worker_id}"
                with open(temp_file, 'w', encoding='utf-8', buffering=32768) as f:
                    for item in local_datas:
                        f.write(json.dumps(item, ensure_ascii=False) + '\n')
                
                if progress:
                    progress[task_id] = progress.get(task_id, 0) + count
                
                return data_length, response, temp_file
            else:
                # 单进程模式，直接写入目标文件
                with open(output_file, 'w', encoding='utf-8', buffering=32768) as f:
                    for item in local_datas:
                        f.write(json.dumps(item, ensure_ascii=False) + '\n')
                
                if progress:
                    progress[task_id] = progress.get(task_id, 0) + count
                
                return data_length, response, None
        else:
            # 输出到stdout
            for item in local_datas:
                console.print(json.dumps(item, ensure_ascii=False), markup=False)
            
            if progress:
                progress[task_id] = progress.get(task_id, 0) + count
            
            return data_length, response, None

    # 更新进度条 - 只在多进程模式下使用字典形式的progress
    if progress and task_id and hasattr(progress, 'get'):
        progress[task_id] = progress.get(task_id, 0) + count
    
    return data_length, response, None


def handle_generate_to_server(repo, data, number, batch, gzip, workers, render):
    """处理生成数据并发送到服务端的场景"""
    query_params = {"repo": repo}
    
    if workers == 1:
        # 单进程处理
        with Progress() as progress:
            task = progress.add_task("Generating and uploading...", total=number)
            
            total_data_length = 0
            responses = []
            
            for i in range(0, number, batch):
                current_batch = min(batch, number - i)
                data_length, response, _ = generate_and_upload(
                    data, current_batch, query_params, gzip, None, None, 'server', render=render
                )
                total_data_length += data_length
                responses.append(response)
                # 手动更新进度条
                progress.update(task, advance=current_batch)
    else:
        # 多进程处理
        with Manager() as manager:
            # 使用manager.dict()作为进度字典，可以在多进程间共享
            progress_dict = manager.dict()
            
            with Progress() as progress:
                task = progress.add_task("Generating and uploading...", total=number)
                
                # 计算每个进程的工作量
                tasks_per_worker = math.ceil(number / workers)
                
                with ProcessPoolExecutor(max_workers=workers) as executor:
                    futures = []
                    
                    for worker_id in range(workers):
                        start_idx = worker_id * tasks_per_worker
                        if start_idx >= number:
                            break
                        
                        worker_count = min(tasks_per_worker, number - start_idx)
                        task_id = f"worker_{worker_id}"
                        progress_dict[task_id] = 0
                        
                        future = executor.submit(
                            generate_and_upload,
                            data, worker_count, query_params, gzip, progress_dict, task_id, 'server', render=render
                        )
                        futures.append(future)
                    
                    total_data_length, responses, _ = _collect_results(futures, progress_dict, number, progress, task)
    
    return total_data_length, responses, None


def handle_generate_to_file(data, number, batch, workers, output_file, render):
    """处理生成数据并写入文件的场景"""
    if workers == 1:
        # 单进程处理
        with Progress() as progress:
            task = progress.add_task("Generating to file...", total=number)
            
            total_data_length, response, _ = generate_and_upload(
                data, number, None, False, progress, task, 'file', output_file, render=render
            )
            
            return total_data_length, [response], []
    else:
        # 多进程处理
        with Manager() as manager:
            progress_dict = manager.dict()
            
            with Progress() as progress:
                task = progress.add_task("Generating to file...", total=number)
                
                # 计算每个进程的工作量
                tasks_per_worker = math.ceil(number / workers)
                
                with ProcessPoolExecutor(max_workers=workers) as executor:
                    futures = []
                    
                    for worker_id in range(workers):
                        start_idx = worker_id * tasks_per_worker
                        if start_idx >= number:
                            break
                        
                        worker_count = min(tasks_per_worker, number - start_idx)
                        task_id = f"worker_{worker_id}"
                        progress_dict[task_id] = 0
                        
                        future = executor.submit(
                            generate_and_upload,
                            data, worker_count, None, False, progress_dict, task_id, 'file', output_file, worker_id, render
                        )
                        futures.append(future)
                    
                    total_data_length, responses, temp_files = _collect_results(futures, progress_dict, number, progress, task)
                
                return total_data_length, responses, temp_files


def handle_file_to_server(repo, file_path, number, batch, gzip, workers):
    """处理从文件读取数据并发送到服务端的场景"""
    from ketacli.sdk.util import parse_url_params
    
    query_params = parse_url_params(repo=repo)
    
    # 读取文件内容
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            file_lines = f.readlines()
    except Exception as e:
        console.print(f"Error reading file {file_path}: {str(e)}")
        return 0, [], None
    
    # 限制行数
    if number > 0:
        file_lines = file_lines[:number]
    
    total_lines = len(file_lines)
    
    if workers == 1:
        # 单进程处理
        with Progress() as progress:
            task = progress.add_task("Uploading from file...", total=total_lines)
            
            total_data_length = 0
            responses = []
            
            for i in range(0, total_lines, batch):
                batch_lines = file_lines[i:i+batch]
                # 移除换行符
                batch_data = [line.rstrip('\n\r') for line in batch_lines]
                
                data_length, response = process_batch_data(batch_data, query_params, gzip, progress, task)
                total_data_length += data_length
                responses.append(response)
    else:
        # 多进程处理
        with Manager() as manager:
            progress_dict = manager.dict()
            
            with Progress() as progress:
                task = progress.add_task("Uploading from file...", total=total_lines)
                
                # 将文件行分配给不同的进程
                lines_per_worker = math.ceil(total_lines / workers)
                
                with ProcessPoolExecutor(max_workers=workers) as executor:
                    futures = []
                    
                    for worker_id in range(workers):
                        start_idx = worker_id * lines_per_worker
                        if start_idx >= total_lines:
                            break
                        
                        end_idx = min(start_idx + lines_per_worker, total_lines)
                        worker_lines = file_lines[start_idx:end_idx]
                        
                        # 移除换行符
                        worker_data = [line.rstrip('\n\r') for line in worker_lines]
                        
                        task_id = f"worker_{worker_id}"
                        progress_dict[task_id] = 0
                        
                        # 在多进程模式下，不传递progress对象给process_batch_data
                        future = executor.submit(
                            process_batch_data,
                            worker_data, query_params, gzip, None, None
                        )
                        futures.append(future)
                    
                    total_data_length, responses, _ = _collect_results(futures, progress_dict, total_lines, progress, task)
    
    return total_data_length, responses, None


def _collect_results(futures, progress_dict, number, prog, task):
    """收集多进程执行结果"""
    total_data_length = 0
    responses = []
    temp_files = []
    
    # 如果有进度条，监控进度更新
    if prog and task:
        completed = 0
        
        # 检查是否有有效的进度字典
        has_progress_dict = progress_dict and len(progress_dict) > 0
        
        while completed < number:
            if has_progress_dict:
                # 使用进度字典计算已完成的项目数
                current_completed = sum(progress_dict.values())
            else:
                # 基于完成的futures数量估算进度
                completed_futures = sum(1 for f in futures if f.done())
                current_completed = int((completed_futures / len(futures)) * number)
            
            if current_completed > completed:
                # 更新进度条
                prog.update(task, advance=current_completed - completed)
                completed = current_completed
            
            # 检查是否所有任务都已完成
            if all(future.done() for future in futures):
                # 确保进度条显示100%
                if has_progress_dict:
                    final_completed = sum(progress_dict.values())
                else:
                    final_completed = number
                    
                if final_completed > completed:
                    prog.update(task, advance=final_completed - completed)
                break
            
            # 短暂休眠以减少CPU使用
            time.sleep(0.1)
    
    # 收集结果
    for future in futures:
        try:
            result = future.result()
            if len(result) == 3:
                # generate_and_upload 返回 3 个值
                data_length, response, temp_file = result
                if temp_file:
                    temp_files.append(temp_file)
            else:
                # process_batch_data 返回 2 个值
                data_length, response = result
            
            total_data_length += data_length
            responses.append(response)
            
        except Exception as e:
            console.print(f"Error collecting result: {str(e)}")
            responses.append({"success": False, "total": 0, "error": str(e)})
    
    return total_data_length, responses, temp_files


@command
def mock_data(repo="default", data=None, file=None, number:int=1, batch:int=2000, gzip=False, workers:int=1, output_type="server", output_file=None, render=False):
    """
    Mock data to specified repo

    :param --repo: The target repo, default: "default"
    :param --data: The json string data default: {"raw":"{{ faker.sentence() }}", "host": "{{ faker.ipv4_private() }}"}
    :param --file: Upload json text from file path.
    :param --number,-n: Number of data, default 1. Use -1 for continuous generation
    :param --worker: for worker process configs like quantity.
    :param --gzip: a boolean for enabling gzip compression.
    :param --batch: to set batch processing size or related configs.
    :param --output_type: Where to write the data, 'server', 'file' or 'stdout', default: 'server'
    :param --output_file: File path to write data when output_type is 'file'
    :param --render: Whether to render the template, default: False. When set to False, it will skip template rendering and use raw text directly, which can improve performance for simple text data.
    """
    start = time.time()
    if workers:
        workers = int(workers)
    if batch:
        batch = int(batch)

    # 输入验证
    if repo is None:
        console.print(f"Please specify target repo with --repo")
        return

    if data is None and file is None:
        console.print(f"Please use --data or --file to specify data to upload")
        return

    if file and not os.path.exists(file):
        console.print(f"Error: file {file} does not exist")
        return

    if output_type == 'file' and not output_file:
        console.print("Error: output_file is required when output_type is 'file'")
        return

    if file is not None and output_type != 'server':
        console.print("When using file parameter, output_type can only be 'server'")
        return

    # 根据参数组合确定处理场景并调用对应的处理函数
    try:
        if file:
            # 场景3: 读文件并发送到服务端
            total_data_length, responses, _ = handle_file_to_server(
                repo, file, number, batch, gzip, workers
            )
        elif output_type == "server":
            # 场景1: 生成日志并发送到服务端
            total_data_length, responses, _ = handle_generate_to_server(
                repo, data, number, batch, gzip, workers, render
            )
        elif output_type == "file":
            # 场景2: 生成日志并写文件
            total_data_length, responses, temp_files = handle_generate_to_file(
                data, number, batch, workers, output_file, render
            )
            if workers > 1 and temp_files:
                try:
                    merge_start = time.time()
                    console.print(f"Starting to merge {len(temp_files)} temporary files...")
                    
                    # 合并所有临时文件到最终输出文件
                    with open(output_file, 'w', encoding='utf-8', buffering=32768) as outfile:
                        for temp_file in sorted(temp_files):
                            if os.path.exists(temp_file):
                                with open(temp_file, 'r', encoding='utf-8', buffering=32768) as infile:
                                    shutil.copyfileobj(infile, outfile, 1024*1024)  # 1MB块大小
                            # 删除临时文件
                            os.remove(temp_file)
                
                    merge_duration = time.time() - merge_start
                    console.print(f"Successfully merged {len(temp_files)} temporary files into {output_file} in {merge_duration:.2f} seconds")
                except Exception as e:
                    console.print(f"Error merging files: {str(e)}")
        elif output_type == "stdout":
            # 场景4: 生成日志并输出到标准输出
            total_data_length = 0
            responses = []
            temp_files = []
            
            # 生成并直接输出数据
            if number == -1:
                # 持续生成数据，不设上限
                i = 0
                while True:
                    try:
                        if render:
                            temp = Template(data)
                            rendered_data = temp.render()
                        else:
                            rendered_data = data
                        total_data_length += len(rendered_data)
                        print(rendered_data)
                        i += 1
                    except KeyboardInterrupt:
                        console.print(f"\nStopped by user. Generated {i} records.")
                        break
                    except Exception as e:
                        console.print(f"Error generating data: {str(e)}")
                        break
            else:
                # 生成指定数量的数据
                for i in range(number):
                    try:
                        if render:
                            temp = Template(data)
                            rendered_data = temp.render()
                        else:
                            rendered_data = data
                        total_data_length += len(rendered_data)
                        print(rendered_data)
                    except Exception as e:
                        console.print(f"Error generating data: {str(e)}")
                        break
        else:
            console.print(f"Error: unsupported output_type '{output_type}'")
            return

        # 显示结果摘要
        if output_type == "server" or file:
            if responses:
                success_count = sum(r['success'] for r in responses)
                total_count = sum(r['total'] for r in responses)
                console.print(f"Successfully uploaded: {success_count}/{total_count} batches")
            
            console.print(f"Total: {format_bytes(total_data_length)}")
        elif output_type == "file":
            console.print(f"Data written to {output_file}")
            console.print(f"Total: {format_bytes(total_data_length)} bytes")
        # stdout输出时不显示文件信息
            
        console.print(f'Total Duration: {time.time() - start:.2f} seconds')
        # 当number为-1时不显示速度统计
        if number != -1:
            console.print(f'速度: {number/(time.time() - start):.2f} 条/s')

    except Exception as e:
        console.print(f"Error during processing: {str(e)}")
        raise


@command
@arg("log_type", type=str,
     completer=lambda prefix, **kwd: [x for x in log_generator.get_supported_log_types() if
                                      x.startswith(prefix)])
def mock_log(repo="default", data=None, file=None, number=1, batch=2000, gzip=False, workers=1, output_type="server", output_file=None, render=False, log_type="nginx"):
    """Mock log data to specified repo, with multiple log types support
    :param --repo: The target repo, default: "default"
    :param --data: The json string data default:
        {
            "raw": "{{ faker.sentence(nb_words=10) }}",
            "host": "{{ faker.ipv4_private() }}"
        }
    :param --file: Upload json text from file path.
    :param --number,-n: Number of data, default 1. Use -1 for continuous generation
    :param --output_type: Where to write the data, 'server', 'file' or 'stdout', default: 'server'
    :param --output_file: File path to write data when output_type is 'file'
    :param --render: Whether to render the template, default: False. When set to False, it will skip template rendering and use raw text directly, which can improve performance for simple text data.
    :param --log_type: Type of log to generate, options: 'nginx', 'java', 'linux', default: 'nginx'
    """
    if not data:
        try:
            # 生成指定类型的日志
            data = log_generator.generate_log(log_type, render)
        except ValueError as e:
            console.print(f"[red]{str(e)}[/red]")
            return
        
    # 直接调用优化后的mock_data函数
    mock_data(repo, data, file, number, batch, gzip, workers, output_type, output_file, render)


@command
def mock_metrics(repo="metrics_keta", data=None, file=None, number=1, batch=2000, gzip=False, workers=1, output_type="server", output_file=None, render=False):
    """Mock metrics data to specified repo
    :param --repo: The target repo, default: "metrics_keta"
    :param --data: The json string data default:
        {
            "host": "{{ faker.ipv4_private() }}",
            "region": "{{ random.choice(['us-west-2', 'ap-shanghai', 'ap-nanjing', 'ap-guangzhou']) }}",
            "os": "{{ random.choice(['Ubuntu', 'Centos', 'Debian', 'TencentOS']) }}",
            "timestamp": {{ int(time.time() * 1000) }},
            "fields": {
                "redis_uptime_in_seconds": {{ random.randint(1,1000000) }},
                "redis_total_connections_received": {{ random.randint(1,1000000) }},
                "redis_expired_keys": {{ random.randint(1,1000000) }}
            }
        }
    :param --file: Upload json text from file path.
    :param --number,-n: Number of data, default 1. Use -1 for continuous generation
    :param --output_type: Where to write the data, 'server', 'file' or 'stdout', default: 'server'
    :param --output_file: File path to write data when output_type is 'file'
    :param --render: Whether to render the template, default: False. When set to False, it will skip template rendering and use raw text directly, which can improve performance for simple text data.
    """
    if not data:
        # 使用更紧凑的JSON格式，减少解析开销
        if render:
            data = (
                '{"host":"{{ faker.ipv4_private() }}",'
                '"region":"{{ random.choice([\"us-west-2\",\"ap-shanghai\",\"ap-nanjing\",\"ap-guangzhou\"]) }}",'
                '"os":"{{ random.choice([\"Ubuntu\",\"Centos\",\"Debian\",\"TencentOS\"]) }}",'
                '"timestamp":{{ int(time.time() * 1000) }},'
                '"fields":{'
                '"redis_uptime_in_seconds":{{ random.randint(1,1000000) }},'
                '"redis_total_connections_received":{{ random.randint(1,1000000) }},'
                '"redis_expired_keys":{{ random.randint(1,1000000) }}'
                '}}'
            )
        else:
            # 当render为false时，使用f-string直接生成数据，避免模板渲染开销
            regions = ["us-west-2", "ap-shanghai", "ap-nanjing", "ap-guangzhou"]
            os_types = ["Ubuntu", "Centos", "Debian", "TencentOS"]
            data = (
                f'{{"host":"{socket.inet_ntoa(struct.pack("!I", random.randint(0xc0a80001, 0xc0a8ffff)))}",'
                f'"region":"{random.choice(regions)}",'
                f'"os":"{random.choice(os_types)}",'
                f'"timestamp":{int(time.time() * 1000)},'
                f'"fields":{{'
                f'"redis_uptime_in_seconds":{random.randint(1,1000000)},'
                f'"redis_total_connections_received":{random.randint(1,1000000)},'
                f'"redis_expired_keys":{random.randint(1,1000000)}'
                f'}}}}'
            )
    # 直接调用优化后的mock_data函数
    mock_data(repo, data, file, number, batch, gzip, workers, output_type, output_file, render)