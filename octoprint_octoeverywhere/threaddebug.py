
import threading
import time
import sys
import traceback

class ThreadDebug:
    
    def Start(self, logger, delaySec):
        try:
            th = threading.Thread(target=self.threadWorker, args=(logger, delaySec))
            th.setDaemon(True)
            th.start()
        except Exception as e:
            logger.error("Failed to start Thread Debug Thread: "+str(e))

    def threadWorker(self, logger, delaySec):
        while True:
            try:
                logger.info("ThreadDump - Starting Thread Dump")
                for threadId, stack in sys._current_frames().items():
                    trace = ""
                    for filename, lineno, name, line in traceback.extract_stack(stack):
                        parts = filename.split("\\")
                        if len(parts) == 0:
                            parts  = filename.split("/")
                        if len(parts) > 0:
                            trace += ", "+parts[len(parts)-1]+":"+name
                        else:
                            trace += ", "+filename+":"+name
                    logger.info("ThreadDump- Id: "+str(threadId) + " -> "+str(trace))

            except Exception as e:
                logger.error("Exception in ThreadDebug : "+str(e))
                pass

            time.sleep(delaySec)

