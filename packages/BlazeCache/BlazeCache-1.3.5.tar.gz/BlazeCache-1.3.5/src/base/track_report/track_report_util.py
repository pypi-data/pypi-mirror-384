from base.log import log_util
from datetime import datetime
import time


def singleton(cls):
    instances = {}

    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance

@singleton
class EventTracker:
    '''
    该类为单例模式, 全局只有一个实例对象
    负责计时统计功能, 会记录所有 event 事件的耗时情况
    
    使用示例:
    event_tracker.record_start("event_name")
    ...
    event_tracker.record_end("event_name")
    '''
    def __init__(self):
        self.events = {}
        self.postEvents = {}
        self.logger = log_util.BccacheLogger(name="EventTracker")
        self.product_name = None
    
    def initialize(self, product_name: str):
        """
        初始化 EventTracker，设置全局的产品名称。
        """
        if self.product_name is None:
            self.product_name = product_name
            self.logger.info(f"[EventTracker] Initialized with product: {self.product_name}")
        else:
            self.logger.warning(f"[EventTracker] Already initialized with product: {self.product_name}. Ignoring new initialization.")

    def record_start(self, event_name: str, product_name: str=None):
        
        effective_product_name = product_name or self.product_name
        if not effective_product_name:
            self.logger.error("[EventTracker] Error: product_name is not set. Please call initialize() first or provide it in the call.")
            return
        now = datetime.now()

        if effective_product_name not in self.events:
            self.events[effective_product_name] = {
                event_name: {
                    'start_time': now
                }
            }
            self.logger.info("[EventTracker] event: {} start. product: {}".format(event_name, effective_product_name))
        elif event_name not in self.events[effective_product_name]:
            self.events[effective_product_name] [event_name]= {

                    'start_time': now

            }
            self.logger.info("[EventTracker] event: {} start. product: {}".format(event_name, effective_product_name))
        else:
            self.logger.info('[EventTracker] event: {} already exists. product: {}'.format(event_name, effective_product_name))
    
    def record_end(self, event_name: str, status: str = "success", product_name: str = None):
        """
        记录事件的结束时间，并附带一个状态。

        Args:
            event_name (str): 事件名称。
            status (str, optional): 事件的最终状态，如 'success', 'failure'。默认为 "success"。
            product_name (str, optional): 产品名称，如果未提供，则使用初始化时的名称。
        """
        effective_product_name = product_name or self.product_name
        if not effective_product_name:
            self.logger.error("[EventTracker] Error: product_name is not set. Please call initialize() first or provide it in the call.")
            return
        
        now = datetime.now()
        if effective_product_name not in self.events:
            self.logger.warning(f"[EventTracker] product: {effective_product_name} not created. Cannot record end.")
            return
        elif event_name not in self.events[effective_product_name]:
            self.logger.warning(f"[EventTracker] event: {event_name} not started. Cannot record end.")
            return
        
        self.events[effective_product_name][event_name]['end_time'] = now
        self.events[effective_product_name][event_name]['status'] = status.lower() # 统一转为小写
        self.logger.info(f"[EventTracker] event: {event_name} end. status: {status}, product: {effective_product_name}")

    def get_time_elapsed(self, event_name: str, product_name: str, is_format_time: bool = False):
        '''
        获取单一事件的耗时时间
        
        Args:
            is_format_time: 是否返回格式化后的时间 
        '''
        if product_name in self.events and event_name in self.events[product_name] and len(self.events[product_name][event_name]) > 1:
            end_time = self.events[product_name][event_name]['end_time']
            start_time = self.events[product_name][event_name]['start_time']
            time_delta = end_time - start_time

            seconds = time_delta.total_seconds()
            
            if not is_format_time:
                return seconds
            
            hours, remainder = divmod(seconds, 3600)
            minutes, seconds = divmod(remainder, 60)

            if hours >= 1:
                return '{:02}:{:02}:{:02}'.format(int(hours), int(minutes), int(seconds))
            elif minutes >= 1:
                return '{} m {} s'.format(int(minutes), int(seconds))
            else:
                return '{} s'.format(int(seconds))

    def print_table(self):
        '''
        输出全量 events 耗时的接口
        该接口一般用于整个项目运行结束后, 打印所有 events 耗时情况
        
        Returns:
            postEvents: 返回一个 Dict 结构, 记录了所有 event 事件的耗时, 单位为秒
            一般用于数据上报
        '''
        self.logger.info("{:<20} {:<20} {:<20}".format('Event', 'Product', 'Time elapsed'))
        for product_name in self.events:
            if product_name not in self.postEvents:
             self.postEvents[product_name] = {}
            event_dict = self.events[product_name]
            for event_name in event_dict:
                time_elapsed = self.get_time_elapsed(event_name, product_name, True)
                get_event_time = self.get_time_elapsed(event_name, product_name)
                self.logger.info("{:<20} {:<20} {:<20}".format(event_name, product_name, time_elapsed))
                if get_event_time:
                   self.postEvents[product_name][event_name] = get_event_time
        
        
        self.logger.info(self.postEvents)

        return self.postEvents

    def get_all_timings(self) -> dict:
        """
        获取所有已完成事件的耗时和状态数据。
        
        Returns:
            dict: 一个包含所有产品及其事件数据的字典。
                  结构: { 
                      "product_A": {
                          "event_1": {"duration_sec": 10.5, "status": "success"}, 
                          "event_2": {"duration_sec": 20.1, "status": "failure"}
                      }, 
                      "product_B": ... 
                  }
        """
        all_timings = {}
        for product_name, event_dict in self.events.items():
            if product_name not in all_timings:
                all_timings[product_name] = {}
            
            for event_name, event_data in event_dict.items():
                # 确保事件已结束
                if 'end_time' in event_data:
                    time_sec = self.get_time_elapsed(event_name, product_name, is_format_time=False)
                    if time_sec is not None:
                        # 获取状态，如果不存在则默认为 'success'
                        status = event_data.get('status', 'success')
                        
                        all_timings[product_name][event_name] = {
                            "duration_sec": round(time_sec, 2),
                            "status": status
                        }
        
        self.logger.info(f"完成所有事件耗时与状态计算: {all_timings}")
        return all_timings
   
if __name__ == "__main__":
    tracker = EventTracker()
    tracker.record_start("Test", "Lark")
    time.sleep(10)
    tracker.record_end("Test", "Lark")
    tracker.print_table()