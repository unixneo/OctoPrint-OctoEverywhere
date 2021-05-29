# automatically generated by the FlatBuffers compiler, do not modify

# namespace: Proto

import octoflatbuffers
from octoflatbuffers.compat import import_numpy
np = import_numpy()

class HandshakeAck(object):
    __slots__ = ['_tab']

    @classmethod
    def GetRootAs(cls, buf, offset=0):
        n = octoflatbuffers.encode.Get(octoflatbuffers.packer.uoffset, buf, offset)
        x = HandshakeAck()
        x.Init(buf, n + offset)
        return x

    @classmethod
    def GetRootAsHandshakeAck(cls, buf, offset=0):
        """This method is deprecated. Please switch to GetRootAs."""
        return cls.GetRootAs(buf, offset)
    # HandshakeAck
    def Init(self, buf, pos):
        self._tab = octoflatbuffers.table.Table(buf, pos)

    # HandshakeAck
    def Accepted(self):
        o = octoflatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(4))
        if o != 0:
            return bool(self._tab.Get(octoflatbuffers.number_types.BoolFlags, o + self._tab.Pos))
        return False

    # HandshakeAck
    def ConnectedAccounts(self, j):
        o = octoflatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(6))
        if o != 0:
            a = self._tab.Vector(o)
            return self._tab.String(a + octoflatbuffers.number_types.UOffsetTFlags.py_type(j * 4))
        return ""

    # HandshakeAck
    def ConnectedAccountsLength(self):
        o = octoflatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(6))
        if o != 0:
            return self._tab.VectorLen(o)
        return 0

    # HandshakeAck
    def ConnectedAccountsIsNone(self):
        o = octoflatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(6))
        return o == 0

    # HandshakeAck
    def Error(self):
        o = octoflatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(8))
        if o != 0:
            return self._tab.String(o + self._tab.Pos)
        return None

    # HandshakeAck
    def BackoffSeconds(self):
        o = octoflatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(10))
        if o != 0:
            return self._tab.Get(octoflatbuffers.number_types.Uint64Flags, o + self._tab.Pos)
        return 0

    # HandshakeAck
    def RequiresPluginUpdate(self):
        o = octoflatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(12))
        if o != 0:
            return bool(self._tab.Get(octoflatbuffers.number_types.BoolFlags, o + self._tab.Pos))
        return False

def Start(builder): builder.StartObject(5)
def HandshakeAckStart(builder):
    """This method is deprecated. Please switch to Start."""
    return Start(builder)
def AddAccepted(builder, accepted): builder.PrependBoolSlot(0, accepted, 0)
def HandshakeAckAddAccepted(builder, accepted):
    """This method is deprecated. Please switch to AddAccepted."""
    return AddAccepted(builder, accepted)
def AddConnectedAccounts(builder, connectedAccounts): builder.PrependUOffsetTRelativeSlot(1, octoflatbuffers.number_types.UOffsetTFlags.py_type(connectedAccounts), 0)
def HandshakeAckAddConnectedAccounts(builder, connectedAccounts):
    """This method is deprecated. Please switch to AddConnectedAccounts."""
    return AddConnectedAccounts(builder, connectedAccounts)
def StartConnectedAccountsVector(builder, numElems): return builder.StartVector(4, numElems, 4)
def HandshakeAckStartConnectedAccountsVector(builder, numElems):
    """This method is deprecated. Please switch to Start."""
    return StartConnectedAccountsVector(builder, numElems)
def AddError(builder, error): builder.PrependUOffsetTRelativeSlot(2, octoflatbuffers.number_types.UOffsetTFlags.py_type(error), 0)
def HandshakeAckAddError(builder, error):
    """This method is deprecated. Please switch to AddError."""
    return AddError(builder, error)
def AddBackoffSeconds(builder, backoffSeconds): builder.PrependUint64Slot(3, backoffSeconds, 0)
def HandshakeAckAddBackoffSeconds(builder, backoffSeconds):
    """This method is deprecated. Please switch to AddBackoffSeconds."""
    return AddBackoffSeconds(builder, backoffSeconds)
def AddRequiresPluginUpdate(builder, requiresPluginUpdate): builder.PrependBoolSlot(4, requiresPluginUpdate, 0)
def HandshakeAckAddRequiresPluginUpdate(builder, requiresPluginUpdate):
    """This method is deprecated. Please switch to AddRequiresPluginUpdate."""
    return AddRequiresPluginUpdate(builder, requiresPluginUpdate)
def End(builder): return builder.EndObject()
def HandshakeAckEnd(builder):
    """This method is deprecated. Please switch to End."""
    return End(builder)