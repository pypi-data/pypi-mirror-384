import datetime
import logging
import sys

from cloudpss.job.TemplateManager import TemplateManager

from .jobReceiver import JobReceiver
import os
from urllib.parse import urlparse
import websocket
import pytz
import threading
import time
utc_tz = pytz.timezone("UTC")

from ..utils.IO import IO
from ..version import __version__
from email.utils import parsedate_to_datetime

class Message(object):
    def __init__(self, id, token):
        self.id = id
        self.token = token

    
    
class MessageStreamReceiver(JobReceiver):
    def __init__(self, output,**kwargs):
        super().__init__()
        self.id = output
        self.origin = kwargs.get("baseUrl",None)
        if self.origin is None:
            self.origin =os.environ.get("CLOUDPSS_API_URL", "https://cloudpss.net/")
        self.__hasOpen = False
        self.templates=TemplateManager()
        self.timeOffset=0
        self.lastMessageTime=0
    
    
    def updateTime(self,timestamp):
        self.lastMessageTime = timestamp
        
    ## 判断是否到达当前时间点的数据或者消息流结束
    def isEnd(self,current_time=None):
        
        if self.status == 1:
            return True
        logging.debug('lastMessageTime',self.lastMessageTime)
        current_time = current_time if current_time is not None else time.time()
        return (self.lastMessageTime/1000)>=current_time-self.timeOffset
        
    def __path(self, from_=None):
        if self.id is None:
            raise Exception("id is None")
        u = list(urlparse(self.origin))
        head = "wss" if u[0] == "https" else "ws"
        path = head + "://" + str(u[1]) + "/api/streams/id/" + self.id
        if from_ is not None:
            path = path + "?from=" + str(from_)
        return path
  
    ###下面是兼容Receiver部分功能实现
    def __on_message_legacy(self,  *args, **kwargs):
        if type(args[0]) != websocket.WebSocketApp:
            message = args[0]
        else:
            message = args[1]
        return self.__on_message(message)
    def __on_message(self, message):
        try:
            data = IO.deserialize(message, "ubjson")
            self.updateTime(data["timestamp"])
            self.ws.url = self.__path(data["id"])
            msg = IO.deserialize(data["data"], "ubjson")
            if type(msg) is list:
                if len(msg) == 3:
                    pass
                    
                    templateMessage = self.templates.invoke(msg)
                    for m in templateMessage:
                        self.messages.append(m)
                    return
                else:
                    self.templates.create(msg)
                    return
            
            self.messages.append(msg)
            return msg
        except Exception as e:
            self.ws.close()
            return None


    def __on_error(self,  *args, **kwargs):
        logging.debug("MessageStreamReceiver error")
        err = args[1] if len(args)>1 else None
        if isinstance(err, websocket.WebSocketConnectionClosedException):
            self.close(args[0])
            return
        msg = {
            "type": "log",
            "verb": "create",
            "version": 1,
            "data": {
                "level": "error",
                "content": "websocket error",
            },
        }
        self.messages.append(msg)

    def __on_close(self, *args, **kwargs):
        if len(args)>1:
            msg =args[2]
            
            if msg is not None and msg.startswith("CMS_NO_STREAM_ID:"):
                self._status = 1
                msg = {
                    "type": "log",
                    "version": 1,
                    "data": {
                        "level": "critical",
                        "content": "未找到任务的输出流，运行结果可能已被清理。",
                    },
                }
                self.messages.append(msg)
                return
        logging.debug("MessageStreamReceiver close")
        msg = {
            "type": "log",
            "verb": "create",
            "version": 1,
            "data": {
                "level": "info",
                "content": "websocket closed",
            },
        }
        self.messages.append(msg)
        self._status = 1
    
    def __on_open(self,ws, *args, **kwargs):
        self.ws = ws
        serverTime = parsedate_to_datetime(ws.sock.headers['date'])
        self.timeOffset = time.time()+time.timezone-serverTime.timestamp()
        
        logging.debug(f"MessageStreamReceiver on_open")
        self._status = 0
        self.__hasOpen = True
        pass

    def close(self, ws):
        self._status = 1
        ws.close()

    @property
    def status(self):
        return self._status

    def waitFor(self,timeOut=sys.maxsize):
        """
            阻塞方法，直到任务完成

            :params timeOut: 超时时间
        """
        start = time.time()
        while self.status == 0:
            time.sleep(0)
            if time.time()-start>timeOut:
                raise Exception("time out")
       

    def connect(self):
        self._status = 0
        path = self.__path()
        logging.info(f"receive data from websocket: {path}")
        self.ws = websocket.WebSocketApp(
            path,
            on_open=self.__on_open,
            on_message=self.__on_message_legacy,
            on_error=self.__on_error,
            on_close=self.__on_close,
            header={
                "User-Agent": "cloudpss-sdk-python/" + __version__
            }
        )
        thread = threading.Thread(target=self.ws.run_forever, kwargs={'ping_interval':60,'ping_timeout':5,'reconnect':True})
        thread.setDaemon(True)
        thread.start()
        while not self.__hasOpen:
            time.sleep(0)
        
