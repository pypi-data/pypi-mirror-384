"""
脚本执行功能的Function Call包装器

支持执行Python、Shell等Linux原生支持的脚本语言
"""

import os
import subprocess
import tempfile
import shlex
from typing import Optional, Dict, Any
from ketacli.sdk.ai.function_call import function_registry
from rich.console import Console

console = Console(markup=False)


@function_registry.register(
    name="execute_script",
    description="执行脚本代码，支持Python、Shell、Bash等Linux原生支持的脚本语言",
    parameters={
        "type": "object",
        "properties": {
            "script_content": {
                "type": "string",
                "description": "要执行的脚本内容"
            },
            "script_type": {
                "type": "string",
                "description": "脚本类型，支持: python, shell, bash, sh, zsh",
                "default": "python"
            },
            "working_directory": {
                "type": "string",
                "description": "脚本执行的工作目录，默认为当前目录"
            },
            "timeout": {
                "type": "integer",
                "description": "脚本执行超时时间（秒），默认30秒",
                "default": 30
            },
            "environment_vars": {
                "type": "string",
                "description": "环境变量，格式：VAR1=value1,VAR2=value2"
            },
            "capture_output": {
                "type": "boolean",
                "description": "是否捕获输出，默认为true",
                "default": True
            }
        },
        "required": ["script_content"]
    }
)
def execute_script(script_content: str, script_type: str = "python", 
                  working_directory: Optional[str] = None, timeout: int = 30,
                  environment_vars: Optional[str] = None, 
                  capture_output: bool = True) -> str:
    """执行脚本代码"""
    try:
        # 验证脚本类型
        supported_types = {
            "python": {"interpreter": "python3", "extension": ".py"},
            "shell": {"interpreter": "sh", "extension": ".sh"},
            "bash": {"interpreter": "bash", "extension": ".sh"},
            "sh": {"interpreter": "sh", "extension": ".sh"},
            "zsh": {"interpreter": "zsh", "extension": ".sh"}
        }
        
        if script_type not in supported_types:
            return f"不支持的脚本类型: {script_type}。支持的类型: {', '.join(supported_types.keys())}"
        
        script_config = supported_types[script_type]
        interpreter = script_config["interpreter"]
        extension = script_config["extension"]
        
        # 检查解释器是否可用
        try:
            subprocess.run([interpreter, "--version"], 
                         capture_output=True, timeout=5, check=False)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return f"解释器 {interpreter} 不可用或未安装"
        
        # 设置工作目录
        if working_directory:
            if not os.path.exists(working_directory):
                return f"工作目录不存在: {working_directory}"
            if not os.path.isdir(working_directory):
                return f"指定的路径不是目录: {working_directory}"
        else:
            working_directory = os.getcwd()
        
        # 解析环境变量
        env = os.environ.copy()
        if environment_vars:
            try:
                for var_pair in environment_vars.split(','):
                    if '=' in var_pair:
                        key, value = var_pair.split('=', 1)
                        env[key.strip()] = value.strip()
            except Exception as e:
                return f"环境变量解析失败: {str(e)}"
        
        # 创建临时脚本文件
        with tempfile.NamedTemporaryFile(mode='w', suffix=extension, 
                                       delete=False, encoding='utf-8') as temp_file:
            temp_file.write(script_content)
            temp_file_path = temp_file.name
        
        try:
            # 为shell脚本添加执行权限
            if script_type in ["shell", "bash", "sh", "zsh"]:
                os.chmod(temp_file_path, 0o755)
            
            # 构建执行命令
            if script_type == "python":
                cmd = [interpreter, temp_file_path]
            else:
                cmd = [interpreter, temp_file_path]
            
            # 执行脚本
            result = subprocess.run(
                cmd,
                cwd=working_directory,
                env=env,
                capture_output=capture_output,
                text=True,
                timeout=timeout
            )
            
            # 构建返回结果
            output_parts = []
            
            if capture_output:
                if result.stdout:
                    output_parts.append(f"标准输出:\n{result.stdout}")
                if result.stderr:
                    output_parts.append(f"标准错误:\n{result.stderr}")
            
            output_parts.append(f"退出码: {result.returncode}")
            
            if result.returncode == 0:
                status = "执行成功"
            else:
                status = "执行失败"
            
            output_parts.insert(0, f"脚本执行状态: {status}")
            
            return "\n\n".join(output_parts)
            
        finally:
            # 清理临时文件
            try:
                os.unlink(temp_file_path)
            except OSError:
                pass
                
    except subprocess.TimeoutExpired:
        return f"脚本执行超时（{timeout}秒）"
    except Exception as e:
        return f"脚本执行失败: {str(e)}"


@function_registry.register(
    name="execute_command",
    description="执行系统命令",
    parameters={
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "要执行的系统命令"
            },
            "working_directory": {
                "type": "string",
                "description": "命令执行的工作目录，默认为当前目录"
            },
            "timeout": {
                "type": "integer",
                "description": "命令执行超时时间（秒），默认30秒",
                "default": 30
            },
            "environment_vars": {
                "type": "string",
                "description": "环境变量，格式：VAR1=value1,VAR2=value2"
            },
            "shell": {
                "type": "boolean",
                "description": "是否使用shell执行命令，默认为false",
                "default": False
            }
        },
        "required": ["command"]
    }
)
def execute_command(command: str, working_directory: Optional[str] = None,
                   timeout: int = 30, environment_vars: Optional[str] = None,
                   shell: bool = False) -> str:
    """执行系统命令"""
    try:
        # 设置工作目录
        if working_directory:
            if not os.path.exists(working_directory):
                return f"工作目录不存在: {working_directory}"
            if not os.path.isdir(working_directory):
                return f"指定的路径不是目录: {working_directory}"
        else:
            working_directory = os.getcwd()
        
        # 解析环境变量
        env = os.environ.copy()
        if environment_vars:
            try:
                for var_pair in environment_vars.split(','):
                    if '=' in var_pair:
                        key, value = var_pair.split('=', 1)
                        env[key.strip()] = value.strip()
            except Exception as e:
                return f"环境变量解析失败: {str(e)}"
        
        # 安全检查：禁止危险命令
        dangerous_commands = [
            'rm -rf /', 'rm -rf *', 'mkfs', 'dd if=', 'format',
            'fdisk', 'parted', 'shutdown', 'reboot', 'halt',
            'passwd', 'su -', 'sudo su', 'chmod 777 /'
        ]
        
        command_lower = command.lower().strip()
        for dangerous in dangerous_commands:
            if dangerous in command_lower:
                return f"拒绝执行危险命令: {command}"
        
        # 解析命令
        if shell:
            cmd = command
        else:
            try:
                cmd = shlex.split(command)
            except ValueError as e:
                return f"命令解析失败: {str(e)}"
        
        # 执行命令
        result = subprocess.run(
            cmd,
            cwd=working_directory,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=shell
        )
        
        # 构建返回结果
        output_parts = []
        
        if result.stdout:
            output_parts.append(f"标准输出:\n{result.stdout}")
        if result.stderr:
            output_parts.append(f"标准错误:\n{result.stderr}")
        
        output_parts.append(f"退出码: {result.returncode}")
        
        if result.returncode == 0:
            status = "执行成功"
        else:
            status = "执行失败"
        
        output_parts.insert(0, f"命令执行状态: {status}")
        
        return "\n\n".join(output_parts)
        
    except subprocess.TimeoutExpired:
        return f"命令执行超时（{timeout}秒）"
    except Exception as e:
        return f"命令执行失败: {str(e)}"


@function_registry.register(
    name="create_and_execute_script",
    description="创建脚本文件并执行，适用于需要保存脚本文件的场景",
    parameters={
        "type": "object",
        "properties": {
            "script_content": {
                "type": "string",
                "description": "要创建的脚本内容"
            },
            "script_path": {
                "type": "string",
                "description": "脚本文件保存路径"
            },
            "script_type": {
                "type": "string",
                "description": "脚本类型，支持: python, shell, bash, sh, zsh",
                "default": "python"
            },
            "make_executable": {
                "type": "boolean",
                "description": "是否设置脚本为可执行，默认为true",
                "default": True
            },
            "execute_immediately": {
                "type": "boolean",
                "description": "是否立即执行脚本，默认为true",
                "default": True
            },
            "timeout": {
                "type": "integer",
                "description": "脚本执行超时时间（秒），默认30秒",
                "default": 30
            }
        },
        "required": ["script_content", "script_path"]
    }
)
def create_and_execute_script(script_content: str, script_path: str,
                            script_type: str = "python", make_executable: bool = True,
                            execute_immediately: bool = True, timeout: int = 30) -> str:
    """创建脚本文件并执行"""
    try:
        # 验证脚本类型
        supported_types = {
            "python": {"interpreter": "python3", "shebang": "#!/usr/bin/env python3"},
            "shell": {"interpreter": "sh", "shebang": "#!/bin/sh"},
            "bash": {"interpreter": "bash", "shebang": "#!/bin/bash"},
            "sh": {"interpreter": "sh", "shebang": "#!/bin/sh"},
            "zsh": {"interpreter": "zsh", "shebang": "#!/bin/zsh"}
        }
        
        if script_type not in supported_types:
            return f"不支持的脚本类型: {script_type}。支持的类型: {', '.join(supported_types.keys())}"
        
        script_config = supported_types[script_type]
        interpreter = script_config["interpreter"]
        shebang = script_config["shebang"]
        
        # 检查目标目录是否存在
        script_dir = os.path.dirname(script_path)
        if script_dir and not os.path.exists(script_dir):
            try:
                os.makedirs(script_dir, exist_ok=True)
            except Exception as e:
                return f"创建目录失败: {str(e)}"
        
        # 为脚本添加shebang（如果需要且不存在）
        if script_type != "python" and not script_content.startswith("#!"):
            script_content = f"{shebang}\n{script_content}"
        
        # 创建脚本文件
        try:
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script_content)
        except Exception as e:
            return f"创建脚本文件失败: {str(e)}"
        
        # 设置执行权限
        if make_executable:
            try:
                os.chmod(script_path, 0o755)
            except Exception as e:
                return f"设置执行权限失败: {str(e)}"
        
        result_parts = [f"脚本文件已创建: {script_path}"]
        
        # 立即执行脚本
        if execute_immediately:
            try:
                if script_type == "python":
                    cmd = [interpreter, script_path]
                else:
                    cmd = [script_path] if make_executable else [interpreter, script_path]
                
                exec_result = subprocess.run(
                    cmd,
                    cwd=os.path.dirname(script_path) or os.getcwd(),
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                
                result_parts.append(f"脚本执行状态: {'成功' if exec_result.returncode == 0 else '失败'}")
                result_parts.append(f"退出码: {exec_result.returncode}")
                
                if exec_result.stdout:
                    result_parts.append(f"标准输出:\n{exec_result.stdout}")
                if exec_result.stderr:
                    result_parts.append(f"标准错误:\n{exec_result.stderr}")
                    
            except subprocess.TimeoutExpired:
                result_parts.append(f"脚本执行超时（{timeout}秒）")
            except Exception as e:
                result_parts.append(f"脚本执行失败: {str(e)}")
        
        return "\n\n".join(result_parts)
        
    except Exception as e:
        return f"创建和执行脚本失败: {str(e)}"