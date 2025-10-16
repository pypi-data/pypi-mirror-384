import json
import os
import sys
from datetime import datetime
from typing import Dict, Any
from base.log import log_util
from base.track_report import track_report_util
from base.file import file_util
import requests
from importlib.metadata import version, PackageNotFoundError
def singleton(cls):
    instances = {}
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return get_instance



@singleton
class MetricsReporter:
    """
    一个单例类，用于收集、管理和格式化所有用于上报的数据。
    它会从多个来源收集信息（如 CI 环境变量、配置文件、运行时状态），
    并在最后将它们整合成一个符合数据库表结构的字典。
    """


    def __init__(self):
        try:
            blazecache_version = version("BlazeCache")
        except PackageNotFoundError:
            # 如果包没有被安装（例如直接以脚本方式运行），则提供一个默认值
            blazecache_version = "0.0.0-dev"
        self._report_data: Dict[str, Any] = {
            # 核心识别与分类字段
            "product_name": None,
            "task_type": None,
            "branch_type": None,
            "os": sys.platform.lower(), # 默认使用 sys.platform
            "job_id": None,
            "mr_id": None,
            "blazecache_version": blazecache_version,

            # JSON 字段 (初始化为空字典)
            "timings_sec": {},
            "build_context": {},
            "perforce_context": {},
            "run_config": {},
            "run_artifacts": {}
        }
        self.event_tracker = track_report_util.EventTracker()
        self.logger = log_util.BccacheLogger(name="MetricsReporter")
        
    def add_ci_context(self, mr_id: int = None, job_id: str = None):
        """
        添加或更新 CI 相关的上下文信息。
        """
        if mr_id is not None:
            self._report_data['mr_id'] = int(mr_id) # 确保 mr_id 是整数
            self.logger.info(f"Updated context with mr_id: {mr_id}")
        
        if job_id is not None:
            self._report_data['job_id'] = job_id
            self.logger.info(f"Updated context with job_id: {job_id}")


    def set_initial_context(self, 
                            product_name: str, 
                            task_type: str, 
                            branch_type: str, 
                            os_type: str):
        """
        设置最核心的运行上下文信息。
        这些信息通常在 BlazeCache 初始化时就能确定。
        """
        self._report_data["product_name"] = product_name
        self._report_data["task_type"] = task_type
        self._report_data["branch_type"] = branch_type
        self._report_data["os"] = os_type
        self.logger.info(f"Initialized reporter context for {product_name}/{task_type}")

    def add_perforce_context(self, p4_config: Dict[str, Any]):
        """
        添加本次运行实际使用的 Perforce 配置。
        """
        safe_p4_config = p4_config.copy()
        safe_p4_config.pop("P4PASSWD", None) # 上报前移除密码
        self._report_data["perforce_context"] = safe_p4_config

    def add_run_config(self, run_config: Dict[str, Any]):
        """
        添加本次运行的其他输入配置，例如来自 JSON 文件的配置。
        """
        self._report_data["run_config"].update(run_config)

    def add_build_context(self, build_context: Dict[str, Any]):
        """
        添加构建上下文，如实际使用的 commit、branch 等动态信息。
        """
        self._report_data["build_context"].update(build_context)

    def add_run_artifact(self, name: str, url: str):
        """
        添加一个运行产物的链接。
        """
        self._report_data["run_artifacts"][name] = url

    def _to_camel_case(self, snake_str: str) -> str:
        """将下划线命名的字符串转换为驼峰命名"""
        components = snake_str.split('_')
        # 第一个部分保持原样，后续部分首字母大写
        return components[0] + ''.join(x.title() for x in components[1:])
    
    def generate_report(self) -> Dict[str, Any]:
        """
        生成最终的上报数据字典，并确保键名为驼峰式。
        【重要】此版本移除了内部的 json.dumps()，以确保所有字段作为对象发送。
        """
        # 1. 从 EventTracker 获取数据
        all_timings = self.event_tracker.get_all_timings()
        product_name = self._report_data.get("product_name")
        if product_name and product_name in all_timings:
            self._report_data["timings_sec"] = all_timings[product_name]

        final_report_snake = self._report_data.copy()

        # ===================== 修改 =====================
        # json_fields = ["timings_sec", "build_context", "perforce_context", "run_config", "run_artifacts"]
        # for field in json_fields:
        #     if isinstance(final_report_snake[field], dict):
        #         final_report_snake[field] = json.dumps(final_report_snake[field])
        # ====================================================
        
        # 2. 键名转换
        final_report_camel = {self._to_camel_case(k): v for k, v in final_report_snake.items()}

        self.logger.info("Final report generated successfully (as pure dict).")
        return final_report_camel

    
    def upload(self, api_endpoint: str, timeout: int = 30):
        """
        将收集到的指标数据上报到指定的 API 端点。

        Args:
            api_endpoint (str): 服务端接收上报的完整 URL。
                                例如: "http://your-service.com/blazecache-metrics/"
            timeout (int): 请求超时时间，单位为秒。
        
        Returns:
            bool: True 表示上报成功，False 表示失败。
        """
        report_data = self.generate_report()
        
        headers = {
            "Content-Type": "application/json"
        }

        try:
            self.logger.info(f"Uploading metrics to {api_endpoint}...")
            self.logger.debug(f"Payload: {json.dumps(report_data, indent=2)}")

            response = requests.post(
                url=api_endpoint,
                headers=headers,
                json=report_data, 
                timeout=timeout
            )

            # 检查 HTTP 状态码，如果不是 2xx，则会抛出异常
            response.raise_for_status() 

            self.logger.info("Metrics uploaded successfully!")
            self.logger.info(f"Server response: {response.json()}")
            print("数据上报成功！")
            print(f"服务器响应: {response.json()}")
            return True

        except requests.exceptions.HTTPError as http_err:
            self.logger.error(f"HTTP error occurred: {http_err}")
            self.logger.error(f"Response body: {http_err.response.text}")
            print(f"HTTP 错误: {http_err}")
            print(f"服务器返回内容: {http_err.response.text}")
            return False
        except requests.exceptions.RequestException as req_err:
            self.logger.error(f"An error occurred during the request: {req_err}")
            return False
        except Exception as e:
            self.logger.error(f"An unexpected error occurred: {e}")
            return False
        
# [建议] 将这个新类添加到 blazecache_reporter.py 文件中

class DisabledMetricsReporter:
    """
    一个空的报告器实现，用于在禁用上报功能时替代 MetricsReporter。
    """
    def __init__(self, *args, **kwargs):
        # 可以在这里加一条日志，明确告知功能已禁用
        self.logger = log_util.BccacheLogger(name="DisabledMetricsReporter")
        self.logger.info("Metrics reporting is disabled. All reporting calls will be ignored.")

    def add_ci_context(self, *args, **kwargs):
        pass

    def set_initial_context(self, *args, **kwargs):
        pass

    def add_perforce_context(self, *args, **kwargs):
        pass

    def add_run_config(self, *args, **kwargs):
        pass

    def add_build_context(self, *args, **kwargs):
        pass

    def add_run_artifact(self, *args, **kwargs):
        pass

    def generate_report(self) -> Dict[str, Any]:
        return {} # 返回一个空字典

    def upload(self, *args, **kwargs) -> bool:
        print("数据上报功能已禁用，跳过上报。")
        return True #

# see: https://open.feishu.cn/document/ukTMukTMukTM/ukTNwUjL5UDM14SO1ATN
class BotContent:

    def __init__(self, title, title_template):
        self.content = {
            'header': {
                'title': {
                    'tag': 'plain_text',
                    'content': title,
                },
                'template': title_template,
            },
            'elements': [],
            'actions': [],
        }
        self.actions = []

    # see: https://open.feishu.cn/document/ukTMukTMukTM/uADOwUjLwgDM14CM4ATN
    def Markdown(self, markdown_string):
        self.content['elements'].append({
            'tag': 'markdown',
            'content': markdown_string,
        })

    def LinkButton(self, title, url, btntype='primary'):
        self.actions.append({
            'tag': 'button',
            'text': {
                'tag': 'lark_md',
                'content': title,
            },
            'type': btntype,
            'url': url,
        })

    def EmptyLine(self):
        self.Markdown('\n')

    def SplitLine(self):
        self.content['elements'].append({
            'tag': 'hr',
        })

    def Content(self):
        if len(self.actions) > 0:
            self.content['elements'].append({
                'tag': 'action',
                'actions': self.actions,
                'layout': 'flow',
            })
        return self.content


def Notify(content, userNames=None, chatIds=None, userIds=None, openIds=None, emails=None):
    if userNames is None and\
            chatIds is None and\
            userIds is None and\
            openIds is None and\
            emails is None:
        return False

    data = {
        'content': content,
        'userNames': userNames,
        'chatIds': chatIds,
        'userIds': userIds,
        'openIds': openIds,
        'emails': emails,
    }
    addr = 'https://cloudapi.bytedance.net/faas/services/tt4pezwhuea88poyz8/invoke/specify_for_native_send_message'
    print(data)
    file_util.FileUtil.send_http_post_request(addr, data)
