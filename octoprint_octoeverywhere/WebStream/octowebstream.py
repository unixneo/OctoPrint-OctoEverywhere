# namespace: WebStream

from octoprint_octoeverywhere.Proto.HttpHeader import HttpHeader
import threading
import traceback
import time
import queue

from .octowebstreamhttphelper import OctoWebStreamHttpHelper
from .octowebstreamwshelper import OctoWebStreamWsHelper
from ..octostreammsgbuilder import OctoStreamMsgBuilder
from ..Proto import WebStreamMsg
from ..Proto import MessageContext
from ..Proto import MessagePriority

#
# Respresents a web stream, which is how we send http request and web socket messages.
#
class OctoWebStream(threading.Thread):

    # Created when an open message is sent for a new web stream from the server.
    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, verbose=None):
        threading.Thread.__init__(self, group=group, target=target, name=name)
        self.Logger = args[0]    
        self.Id = args[1] 
        self.OctoSession = args[2]
        self.OpenWebStreamMsg = None
        self.IsClosed = False
        self.HasSentCloseMessage = False
        self.StateLock = threading.Lock()
        self.MsgQueue = queue.Queue()        
        self.HttpHelper = None
        self.WsHelper = None
        self.IsHelperClosed = False
        self.OpenedTime = time.time()

        # Vars for high pri streams
        self.IsHighPriStream = False
        self.HighPriLock = threading.Lock()
        self.ActiveHighPriStreamCount = 0
        self.ActiveHighPriStreamStart = time.time()


    # Called for all messages for this stream id. 
    #
    # This function is called on the main OctoSocket receive thread, so it should pass the
    # message off to the thread as quickly as possible.
    def OnIncomingServerMessage(self, webStreamMsg):
        # Don't accept messages after we are closed.
        if self.IsClosed:
            self.Logger.info("Web stream class "+str(self.Id)+" got a incoming message after it has been closed.")
            return

        # If this is a close measage, we need to call close now
        # since the main thread might be blocked waiting on a http call or something.
        if webStreamMsg.IsCloseMsg():
            # Note right now we don't support getting close mesages with data.
            if webStreamMsg.IsControlFlagsOnly == False:
                self.Logger.warn("Web stream "+str(self.Id)+" got a close message with data. The data will be ignored.")                
            # Set this flag, because we don't need to send a close message if the server already did.
            self.HasSentCloseMessage = True
            # Call close.
            self.Close()
        else:
            # Otherwise, put the message into the queue, so the thread will pick it up.
            self.MsgQueue.put(webStreamMsg)


    # Closes the web stream and all related elements.
    # This is called from the main socket receive thread, so it should
    # execute as quickly as possible.
    def Close(self):
        # Check the state and set the flag. Only allow this code to run
        # once.
        localHttpHelper = None
        localWsHelper = None
        self.StateLock.acquire()
        try:
            # If we are already closed, there's nothing to do.
            if self.IsClosed == True:
                return
            # We will close now, so set the flag.
            self.IsClosed = True

            # While under lock, exists, and if so, has it been closed.
            # Note it's possible that this helper is being crated on a different
            # thread and will be set just after we exit the lock. In that case
            # the creator logic will notice that the stream is closed and call close on it.
            # So if the http helper doesn't exist yet, we can't set the isClosed flag to false.
            if self.HttpHelper != None or self.WsHelper != None:
                if self.IsHelperClosed == False:          
                    self.IsHelperClosed = True
                    localHttpHelper = self.HttpHelper
                    localWsHelper = self.WsHelper
        except Exception as _:
            raise  
        finally:
            self.StateLock.release()

        # Remove ourselves from the session map
        self.OctoSession.WebStreamClosed(self.Id)

        # Put an empty message on the queue to wake it up to exit.
        self.MsgQueue.put(None)

        # Ensure we have sent the close message
        self.ensureCloseMessageSent()

        # If this was high pri, clear the state
        if self.IsHighPriStream:
            self.highPriStreamEnded()

        # If we got a ref to the helper, we need to call close on it.
        try:
            if localHttpHelper != None:
                localHttpHelper.Close()
            if localWsHelper != None:
                localWsHelper.Close()
        except Exception as e:
            self.Logger("Web stream "+str(self.Id)+" helper threw an exception during close "+str(e))

    # This is our main thread, where we will process all incoming messages.
    def run(self):
        try:
            self.mainThread()
        except Exception as e:
            self.Logger.error("Exception in web stream ["+str(self.Id)+"] connect loop: "+str(e))
            traceback.print_exc()
            self.OctoSession.OnSessionError(0)


    def mainThread(self):
        # Loop until we are closed.
        while self.IsClosed == False:

            # Wait on incoming messages
            # Timeout after 60 seconds just to check that we aren't closed.
            # It's important to set this value to None, otherwise on loops it will hold it's old value
            # which can accidentally re-process old messages.
            webStreamMsg = None
            try:
                webStreamMsg = self.MsgQueue.get(timeout=60)
            except Exception as e:
                # We get this exception on the timeout.
                pass

            # Check that we aren't closed
            if self.IsClosed == True:
                return

            # Check that we got a message and this wasn't just a timeout
            if webStreamMsg == None:
                continue

            # Handle the message.
            if webStreamMsg.IsOpenMsg():
                self.initFromOpenMessage(webStreamMsg)

            # Ensure we have an open message.
            if self.OpenWebStreamMsg == None:
                # Throw so we reset the connection.
                raise Exception("Web stream ["+str(self.Id)+"] got a non open message before it's open message.")

            # Don't pass it to the helper if there's nothing more.
            if webStreamMsg.IsControlFlagsOnly():
                continue

            # Allow the helper to process the message
            # We should only ever have one, but just for safety, check both.
            returnValue = True
            if self.HttpHelper != None:
                returnValue = self.HttpHelper.IncomingServerMessage(webStreamMsg)
            if self.WsHelper != None:
                returnValue = self.WsHelper.IncomingServerMessage(webStreamMsg)

            # If process server message returns true, we should close the stream.
            if returnValue == True:
                self.Close()
                return

            # When the http helper sends messages, it can indicate that the close flag has been set.
            # In such a case, self.HasSentCloseMessage will be true. We don't want to rely on the client
            # returning the correct returnValue, so if we see that we will call close to make sure things
            # are going down. Since Close() is guarded against multiple entries, this is totall fine.
            if self.HasSentCloseMessage == True and self.IsClosed == False:
                self.Logger.warn("Web stream "+str(self.id)+" processed a message and has sent a close message, but didn't call close on the web stream. Closing now.")
                self.Close()
                return


    def initFromOpenMessage(self, webStreamMsg):
        # Sanity check.
        if self.OpenWebStreamMsg != None:
            # Throw so we reset the connection.
            raise Exception("Web stream ["+str(self.Id)+"] already have an open message and we got another.")

        # Set the message.
        self.OpenWebStreamMsg = webStreamMsg

        # Check if this is high pri, if so, tell them system a high pri is active
        if(self.OpenWebStreamMsg.MsgPriority() < MessagePriority.MessagePriority.Normal):
            self.IsHighPriStream = True
            self.highPriStreamStarted()

        # At this point we know what kind of stream we are, http or ws.
        # Create the helper out of lock and then set it.
        # WE MUST ALWAYS SET THE HTTP HELPER OBJECT since down stream logic depends on it existing.
        # But, if the stream has closed since we created this object, we must call close on it.
        httpHelper = None
        wsHelper = None
        if webStreamMsg.IsWebsocketStream():
            wsHelper = OctoWebStreamWsHelper(self.Id, self.Logger, self, self.OpenWebStreamMsg, self.OpenedTime)
        else:
            httpHelper = OctoWebStreamHttpHelper(self.Id, self.Logger, self, self.OpenWebStreamMsg, self.OpenedTime)

        needsToCallCloseOnHelper = False
        self.StateLock.acquire()
        try:
            # Set the helper, which ever we made.
            self.HttpHelper = httpHelper
            self.WsHelper = wsHelper

            # If the stream is now closed...
            if self.IsClosed == True:
                # and the http helper didn't get closed called yet...
                if self.IsHelperClosed == False:
                    # We need to call it now.
                    self.IsHelperClosed = True
                    needsToCallCloseOnHelper = True
        except Exception as _:
            raise  
        finally:
            self.StateLock.release()

        # Outside of lock, if we need to close this helper, do it.
        if needsToCallCloseOnHelper == True:
            if httpHelper != None:
                httpHelper.Close()
            if wsHelper != None:
                wsHelper.Close()


    # Called by the helpers to send messages to the server.
    def SendToOctoStream(self, buffer, isCloseFlagSet = False, silentlyFail = False):
        # Make sure we aren't closed. If we are, don't allow the message to be sent.
        self.StateLock.acquire()
        try:
            if self.IsClosed == True:
                # The only reason we are allowed to send after a close is if we are sending the
                # close flag message.
                if isCloseFlagSet == False:
                    self.Logger.info("Web Stream "+str(self.Id) + " tried to send a message after close.")
                    return
                else:
                    # We can only send one close flag, so only allow this to send if we haven't sent yet.
                    if self.HasSentCloseMessage:
                        if silentlyFail == False:
                            self.Logger.warn("Web Stream "+str(self.Id)+" tried to send a close message after a close message was already sent")
                        return

            # No matter what, if the close flag is set, set the has sent now.
            if isCloseFlagSet:
                self.HasSentCloseMessage = True                   
        except Exception as _:
            raise  
        finally:
            self.StateLock.release()

        # Send now
        try:
            self.OctoSession.Send(buffer)
        except Exception as e:
            self.Logger.error("Web stream "+str(self.Id)+ " failed to send a message to the OctoStream. Error:"+str(e))

            # If this was the close message, set the has set flag back to false so we send again.
            # (this mostly won't matter, since the entire connection will go down anyways)
            self.HasSentCloseMessage = False

            # If we fail, close the entire connection.
            self.OctoSession.OnSessionError(0)

            # Return since things are going down.
            return

    # Ensures the close message is always sent, but only once.
    # The only way the close message doesn't need to be sent is if
    # the otherside started the close with a close message.
    def ensureCloseMessageSent(self):
        # Since the send function does the checking to ensure only one close message
        # gets sent, we will always try to create and send a message.
        try:
            builder = OctoStreamMsgBuilder.CreateBuffer(200)            
            WebStreamMsg.Start(builder)
            WebStreamMsg.AddStreamId(builder, self.Id)
            WebStreamMsg.AddIsControlFlagsOnly(builder, True)
            WebStreamMsg.AddIsCloseMsg(builder, True)
            webStreamMsgOffset = WebStreamMsg.End(builder)
            outputBuf = OctoStreamMsgBuilder.CreateOctoStreamMsgAndFinalize(builder, MessageContext.MessageContext.WebStreamMsg, webStreamMsgOffset)
            # Set the flag to silently fail, since the message might have already been sent by the helper.
            self.SendToOctoStream(outputBuf, True, True)
        except Exception as _:
            # This is bad, log it and kill the stream.
            self.Logger.error("Exception thrown while trying to send close message for web stream "+str(self.Id))
            self.OctoSession.OnSessionError(0)

    # Called by the OctoStreamHttpHelper if the request is normal pri.
    # If a high pri request is active, this should block until it's complete or for a little while.
    def BlockIfHighPriStreamActive(self):
        # Check the counter, don't worry about taking the lock, worst case
        # this logic would allow one request through or not block one.

        # If there are no high pri requests, don't block.
        if self.ActiveHighPriStreamCount == 0:
            return
        # As a sanity check, if the high pri request started more than 5 seconds ago
        # don't block.
        timeSinceStartSec = time.time() - self.ActiveHighPriStreamStart
        if timeSinceStartSec > 5.0:
            return

        # We should block this request
        # TODO - this would be better if we blocked on a event or something, but for now this is fine.
        # Note that the http will call this function before the request and on each response read loop, so the delays add up.
        time.sleep(0.1)

    # Called when a high pri stream is started
    def highPriStreamStarted(self):
        self.HighPriLock.acquire()
        try:
            self.ActiveHighPriStreamCount += 1
            self.ActiveHighPriStreamStart = time.time()
        except Exception as _:
            raise  
        finally:
            self.HighPriLock.release()

    # Called when a high pri stream is ended.
    def highPriStreamEnded(self):
        self.HighPriLock.acquire()
        try:
            self.ActiveHighPriStreamCount -= 1
        except Exception as _:
            raise  
        finally:
            self.HighPriLock.release()