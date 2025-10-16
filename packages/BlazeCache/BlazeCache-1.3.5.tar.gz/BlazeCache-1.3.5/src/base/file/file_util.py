import base64
import json
import os
import shutil
import sys
import time
import urllib.request
from base.log import log_util


def Retry(func, times, *args, **kwargs):
    '''
    重试函数, 文件操作容易因资源竞争导致失败, 因此需要失败后重试
    '''
    for _ in range(times):
        value = func(*args, **kwargs)  
        if value:
            return value
        time.sleep(5)
    return False

class FileUtil:
    '''
    封装常用的文件操作工具, 方便快速完成文件操作
    '''
    logger = log_util.BccacheLogger(name="FileUtil")
    
    @classmethod
    def remove_folder(cls, folder: str, retry_times: int = 5) -> bool:
        def remove_folder_impl():
            if not os.path.exists(folder):
                cls.logger.info('[RemoveFolder]', folder, 'not existed')
                return True

            cls.logger.info('[RemoveFolder]', 'Delete', folder)
            try:
                shutil.rmtree(folder)
            except BaseException as e:
                cls.logger.error('[RemoveFolder]', e)

            ret = not os.path.exists(folder)
            cls.logger.info('[RemoveFolder]', 'Delete', folder,
                'success' if ret else 'failure')
            return ret

        Retry(remove_folder_impl, retry_times)
        
    @classmethod
    def remove_file(cls, file: str, retry_times: int = 5) -> bool:
        def remove_file_impl():
            try:
                if not os.path.exists(file):
                    cls.logger.info('[RemoveFile]', file, 'not existed')
                    return True

                cls.logger.info('[RemoveFile]', 'Delete', file)
                os.remove(file)
            except BaseException as e:
                cls.logger.error('[RemoveFile]', e)

            ret = not os.path.exists(file)
            cls.logger.info('[RemoveFile]', 'Delete', file, 'success' if ret else 'failure')
            return ret

        Retry(remove_file_impl, retry_times)
    
    @classmethod
    def get_folder_size(cls, folder: str, details: dict = {}) -> int:
        '''
        计算指定目录的 size 大小, 一般会用来统计 out 缓存目录的大小, 做调试确认信息使用
        
        Agrs:
            folder: 目录路径名
            details: 可选参数, 用于收集目录中每个文件和子目录的详细大小信息
            
        Returns:
            返回整个目录的总体积
        '''
        if folder is None:
            return 0

        if not os.path.exists(folder):
            return 0

        size = 0
        for r in os.listdir(folder):
            item = os.path.join(folder, r)

            if os.path.islink(item) or os.path.isfile(item):
                item_size = os.path.getsize(item)
                # 链接符号不计算大小, 主要是两层考虑
                # 1. 链接文件指向的实体若不在 folder 下, 则不应该计算大小
                # 2. 链接文件指向的实体若在 folder 下, 则会重复计算大小
                # 但需要将 folder 的所有文件记录添加至 details 中
                if os.path.islink(item):
                    item_size = 0
                if details is not None:
                    details[r] = item_size
                size += item_size

            elif os.path.isdir(item):
                temp_tails = {}
                size += cls.FolderSize(item, temp_tails)
                if details is not None:
                    details[r] = temp_tails

        return size
    
    @classmethod
    def make_directory_exists(cls, dirname: str) -> bool:
        if dirname is None or dirname == '':
            return False

        cls.logger.info(f"[make] Make {dirname} existed")
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        return True
    
    @classmethod
    def download_url(cls, url: str, local_path: str) -> bool:
        cls.logger.info(f"download {url} => {local_path}")
        def DownloadURL_Impl():
            try:
                if os.path.dirname(local_path) != '':
                    if not os.path.exists(os.path.dirname(local_path)):
                        cls.make_directory_exists(os.path.dirname(local_path))
                urllib.request.urlretrieve(url, local_path)
                return True
            except BaseException as e:
                cls.logger.error(f"[download] error: {e}")
                return False
        if not Retry(DownloadURL_Impl, 50):
            cls.logger.error(f"Fail to download {url}")
            return False
        
    @classmethod
    def send_http_post_request(cls, post_url, content, method='POST',
                authorization=None, get_header=False,
                allow_exceptions=False, custom_header=None, asw=None):
        '''
        Args:
            allow_exceptions: 为 True 代表不重试任务直接失败, 否则会重试 post 任务
            asw: 为 True 可以获取接口返回的报错信息 例如401 或者 404 等错误码 直接返回错误码 不重试任务直接失败
        '''
        def HttpPost_Impl():
            try:
                header = {
                    "Content-Type": "application/json; charset=utf-8",
                    "accept": "application/json, text/plain, */*",
                }
                if custom_header is not None:
                    header.update(custom_header)
                if authorization is not None:
                    if authorization.startswith('Bearer'):
                        header['Authorization'] = authorization
                    else:
                        if isinstance(authorization, str):
                            authorizations = authorization.encode('utf-8')
                            header['Authorization'] = 'Basic {}'.format(
                                base64.b64encode(authorizations).decode('ascii'))

                body = json.dumps(content).encode('utf-8')
                request = urllib.request.Request(post_url, data=body, headers=header)
                request.get_method = lambda: method
                try:
                    response = urllib.request.urlopen(request, timeout=30)
                except urllib.error.HTTPError as e:
                    response = e
                    cls.logger.error(response)
                if get_header:
                    res = json.dumps(dict(response.headers))
                else:
                    res = json.loads(response.read().decode('utf-8'))
                if len(res) == 0:
                    res = '{}'
                if not asw and "code" in res and not (res["code"] in [0, 1, 200, "0", "1", "200"]):
                    cls.logger.error(('[http] request fail method:', method))
                    cls.logger.error(('[http] request fail post_url:', post_url))
                    cls.logger.error(('[http] request fail data:', content))
                    cls.logger.error(("[http] request fail res:", res))
                return res
            except urllib.error.URLError as e:
                if allow_exceptions:
                    raise e

                cls.logger.error('[http]', e)
                if hasattr(e, 'code') and hasattr(e, 'read'):
                    cls.logger.error('[http]', e.code)
                    try:
                        res = e.read().decode('utf-8') if hasattr(e.read(), 'decode') else e.read()
                        cls.logger.info('[content]', res)
                    except Exception as ex:
                        cls.logger.error('[http] Failed to read error content:', ex)

                if asw is not None:
                    return e
                return False

        res = Retry(HttpPost_Impl, 5)
        if res is False:
            cls.logger.error('[http]', 'Fail to send http post request', post_url)
            sys.exit(1)
        return res
    
class ChangeDirectory:

    def __init__(self, new_directory):
        self.new_directory = new_directory
        self.current_directory = os.getcwd()

    def __enter__(self):
        os.chdir(self.new_directory)

    def __exit__(self, exc_type, exc_value, trace):
        os.chdir(self.current_directory)
