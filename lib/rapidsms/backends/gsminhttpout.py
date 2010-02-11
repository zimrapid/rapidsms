#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8


import time
import pygsm
import Queue
import gsm 

from rapidsms.message import Message
from rapidsms.connection import Connection
from rapidsms import log
from rapidsms import utils
from datetime import datetime
from rapidsms.backends.gsm import Backend
from rapidsms.backends.http import HttpServer
from rapidsms.backends.httphandlers import RapidBaseHttpHandler
import httphandlers as handlers

class Backend(Backend):
    _title = "HybridBackend"
    
    def _log(self, modem, msg, level):
       gsm.Backend._log(self,modem,msg,level)

    def configure(self, *args, **kwargs):
       if 'handler' in kwargs:
           handler = kwargs.pop('handler')
       else :
           handler = 'ClickatellHandler'
       if 'httpport' in kwargs:
           port = kwargs.pop('httpport')
       else:
           port = 8001
       if 'host' in kwargs:
           host = kwargs.pop('host')
       else:
           host = "127.0.0.1"

       component_class = getattr(handlers, handler)

       self.httphandler = component_class

       magickeys = self.httphandler.get_handler_param_keys()
       handlersettings = {}
       for key in magickeys:
           if key in kwargs:
               handlersettings[key] = kwargs.pop(key)
       
       gsm.Backend.configure(self,*args,**kwargs)

       self.httphandler.set_handler_params(handlersettings)
       self.httpserver = HttpServer((host, int(port)), component_class)
 
       #Let the handler know who to call back to
       self.httphandler.backend = self

    def run (self):
        gsm.Backend.run(self)
        self.httpserver.handle_request()
    
    def __send_sms(self, message):
        self.httphandler.outgoing(message)
        
    def start(self):
        gsm.Backend.start(self)

    def stop(self):
        # call superclass to stop--sets self._running
        # to False so that the 'run' loop will exit cleanly.
        gsm.Backend.stop(self)
