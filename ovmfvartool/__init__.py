import sys, argparse, struct, uuid, binascii, io, datetime
import yaml


__version__ = "0.0.0"


def nicehex(x, L):
    s = hex(x)[2:]
    return s.rjust(L, " ")


def repasc(x):
    if x >= 0x20 and x <= 0x7E:
        return chr(x)
    return "."


def hexdump(f, offset=0, limit=None, elide=False, lba=False, reverse=False):
    if limit is None:
        prev = f.tell()
        f.seek(0, 2)
        fl = f.tell()
        f.seek(prev)
    else:
        fl = limit

    offsetChars = len(hex(fl + offset)[2:])
    consumed = 0

    prevLine = None
    eliding = False
    while limit is None or consumed < limit:
        Lr = 16
        if limit is not None and consumed + Lr > limit:
            Lr = limit - consumed

        d = f.read(Lr)
        if d == b"":
            break

        if elide and d == prevLine:
            if not eliding:
                eliding = True
                print(
                    "*                               **                                             "
                )
        else:
            eliding = False
            dh = binascii.hexlify(d).decode("ascii")
            if len(d) < 16:
                dh = dh.ljust(32, " ")

            asc = ""
            for x in d:
                asc += repasc(x)

            offs = "%08x" % offset

            asc = "|" + asc + "|"
            pre = ""
            if lba:
                if lba is True:
                    lba = (4096, 4608)
                blkDataSize, blkSize = lba
                om = offset % blkSize
                oms = "D"
                if om >= blkDataSize:
                    oms = "H"
                    om -= blkDataSize
                pre = "%s %s%s> " % (
                    nicehex(offset // blkSize, offsetChars),
                    oms,
                    nicehex(om, 4),
                )
            print(
                "%s%s)  %s %s %s %s %s %s %s %s  %s %s %s %s %s %s %s %s  %s"
                % (
                    pre,
                    nicehex(offset, offsetChars),
                    dh[0:2],
                    dh[2:4],
                    dh[4:6],
                    dh[6:8],
                    dh[8:10],
                    dh[10:12],
                    dh[12:14],
                    dh[14:16],
                    dh[16:18],
                    dh[18:20],
                    dh[20:22],
                    dh[22:24],
                    dh[24:26],
                    dh[26:28],
                    dh[28:30],
                    dh[30:32],
                    asc.ljust(18, " "),
                )
            )

        offset += Lr
        consumed += Lr
        prevLine = d

    return consumed


knownUUIDs = []
knownUUIDsByName = {}


def registerUUID(s, name):
    u = uuid.UUID(s)
    knownUUIDs.append((u, name))
    knownUUIDsByName[name] = u
    return u


def resolveUUID(u):
    for (u2, u2Name) in knownUUIDs:
        if u2 == u:
            return u2Name
    return str(u)


def lookupUUID(u):
    if u in knownUUIDsByName:
        return knownUUIDsByName[u]
    else:
        return uuid.UUID(u)


gEfiSystemNvDataFvGuid = registerUUID(
    "8d2bf1ff-9676-8b4c-a985-2747075b4f50", "gEfiSystemNvDataFvGuid"
)
gEfiAuthenticatedVariableGuid = registerUUID(
    "782cf3aa-7b94-9a43-a180-2e144ec37792", "gEfiAuthenticatedVariableGuid"
)

gEdkiiVarErrorFlagGuid = registerUUID(
    "e87fb304-aef6-0b48-bdd5-37d98c5e89aa", "gEdkiiVarErrorFlagGuid"
)
gEfiMemoryTypeInformationGuid = registerUUID(
    "9f04194c-3741-d34d-9c10-8b97a83ffdfa", "gEfiMemoryTypeInformationGuid"
)
gMtcVendorGuid = registerUUID("114070eb-0214-d311-8e77-00a0c969723b", "gMtcVendorGuid")
gEfiGlobalVariableGuid = registerUUID(
    "61dfe48b-ca93-d211-aa0d-00e098032b8c", "gEfiGlobalVariableGuid"
)
gEfiIScsiInitiatorNameProtocolGuid = registerUUID(
    "45493259-44ec-0d4c-b1cd-9db139df070c", "gEfiIscsiInitiatorNameProtocolGuid"
)
gEfiIp4Config2ProtocolGuid = registerUUID(
    "d16e445b-0be3-aa4f-871a-3654eca36080", "gEfiIp4Config2ProtocolGuid"
)
gEfiImageSecurityDatabaseGuid = registerUUID(
    "cbb219d7-3a3d-9645-a3bc-dad00e67656f", "gEfiImageSecurityDatabaseGuid"
)
gEfiSecureBootEnableDisableGuid = registerUUID(
    "f0a30bc7-af08-4556-99c4-001009c93a44", "gEfiSecureBootEnableDisableGuid"
)
gEfiCustomModeEnableGuid = registerUUID(
    "0cec76c0-2870-9943-a072-71ee5c448b9f", "gEfiCustomModeEnableGuid"
)
gIScsiConfigGuid = registerUUID(
    "16d6474b-d6a8-5245-9d44-ccad2e0f4cf9", "gIScsiConfigGuid"
)
gEfiCertDbGuid = registerUUID("6ee5bed9-dc75-d949-b4d7-b534210f637a", "gEfiCertDbGuid")
gMicrosoftVendorGuid = registerUUID(
    "bd9afa77-5903-324d-bd60-28f4e78f784b", "gMicrosoftVendorGuid"
)
gEfiVendorKeysNvGuid = registerUUID(
    "e0e47390-ec60-6e4b-9903-4c223c260f3c", "gEfiVendorKeysNvGuid"
)
mBmHardDriveBootVariableGuid = registerUUID(
    "e1e9b7fa-dd39-2b4f-8408-e20e906cb6de", "mBmHardDriveBootVariableGuid"
)

FV_MAGIC = 0x4856465F


class UEFITime(object):
    def __init__(self, t=None):
        if t:
            (
                self.year,
                self.month,
                self.day,
                self.hour,
                self.minute,
                self.second,
                self.pad1,
                self.nanosecond,
                self.timezone,
                self.daylight,
                self.pad2,
            ) = (
                t.year,
                t.month,
                t.day,
                t.hour,
                t.minute,
                t.second,
                0,
                t.microsecond * 1000,
                0,
                0,
                0,
            )
            print(t)
        else:
            (
                self.year,
                self.month,
                self.day,
                self.hour,
                self.minute,
                self.second,
                self.pad1,
                self.nanosecond,
                self.timezone,
                self.daylight,
                self.pad2,
            ) = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

    @classmethod
    def deserialize(cls, b):
        o = cls()
        (
            o.year,
            o.month,
            o.day,
            o.hour,
            o.minute,
            o.second,
            o.pad1,
            o.nanosecond,
            o.timezone,
            o.daylight,
            o.pad2,
        ) = struct.unpack("<HBBBBBBIhBB", b)
        return o

    def serialize(self):
        return struct.pack(
            "<HBBBBBBIhBB",
            self.year,
            self.month,
            self.day,
            self.hour,
            self.minute,
            self.second,
            self.pad1,
            self.nanosecond,
            self.timezone,
            self.daylight,
            self.pad2,
        )

    @property
    def time(self):
        if self.year == 0:
            return None
        if self.timezone == 2047:
            tz = datetime.timezone.utc
        else:
            tz = datetime.timezone(datetime.timedelta(minutes=self.timezone))
        return datetime.datetime(
            self.year,
            self.month,
            self.day,
            self.hour,
            self.minute,
            self.second,
            self.nanosecond // 1000,
            tz,
        )


class FirmwareVolumeHeader(object):
    @classmethod
    def deserialize(cls, f):
        o = cls()
        (
            o.vector,
            o.fsUUID,
            o.fvLen,
            o.magic,
            o.flags,
            o.hdrLen,
            o.checksum,
            o.extHdrOff,
            o.reserved,
            o.rev,
        ) = struct.unpack("<16s16sQIIHHHBB", f.read(56))
        o.fsUUID = uuid.UUID(bytes=o.fsUUID)

        if o.magic != FV_MAGIC:
            raise Exception("expected magic, not a EFI_FIRMWARE_VOLUME_HEADER MAGIC")

        if o.fsUUID != gEfiSystemNvDataFvGuid:
            raise Exception(
                "unexpected UUID, not a EFI_FIRMWARE_VOLUME_HEADER: %s" % fsUUID
            )

        o.blkInfo = []
        while True:
            numBlk, blkLen = struct.unpack("<II", f.read(8))
            if numBlk == 0 and blkLen == 0:
                break
            o.blkInfo.append((numBlk, blkLen))

        return o

    def serialize(self):
        b = struct.pack(
            "<16s16sQIIHHHBB",
            self.vector,
            self.fsUUID.bytes,
            self.fvLen,
            self.magic,
            self.flags,
            self.hdrLen,
            self.checksum,
            self.extHdrOff,
            self.reserved,
            self.rev,
        )
        for numBlk, blkLen in self.blkInfo:
            b += struct.pack("<II", numBlk, blkLen)

        b += struct.pack("<II", 0, 0)
        return b

    @classmethod
    def create(cls):
        o = cls()
        o.vector = b"\x00" * 16
        o.fsUUID = gEfiSystemNvDataFvGuid
        o.fvLen = 528 * 1024
        o.magic = FV_MAGIC
        o.flags = 0x4FEFF
        o.hdrLen = 72
        o.checksum = 0xB8AF
        o.extHdrOff = 0
        o.reserved = 0
        o.rev = 2
        o.blkInfo = [(132, 4096)]
        return o

    def print(self):
        print("Firmware Volume Header")
        print("======================")
        print("UUID:                %s" % resolveUUID(self.fsUUID))
        print(
            "FV Length:           %s bytes (%s KiB)" % (self.fvLen, self.fvLen / 1024)
        )
        print("Flags:               0x%08x" % self.flags)
        print("Header Length:       %s bytes" % self.hdrLen)
        print("Checksum:            0x%02x" % self.checksum)
        print("Ext. Header Offset:  0x%x" % self.extHdrOff)
        print("Revision:            %s" % self.rev)
        print("")
        print("Blocks:")

        for numBlk, blkLen in self.blkInfo:
            print(
                "  %s * %s byte blocks (%s KiB total)"
                % (numBlk, blkLen, numBlk * blkLen / 1024)
            )

        print("")


class VariableStoreHeader(object):
    @classmethod
    def deserialize(cls, f):
        o = cls()

        o.hdrUUID, o.len, o.fmt, o.state, o.reserved1, o.reserved2 = struct.unpack(
            "<16sIBBHI", f.read(28)
        )
        o.hdrUUID = uuid.UUID(bytes=o.hdrUUID)

        if o.hdrUUID != gEfiAuthenticatedVariableGuid:
            raise Exception("unexpected UUID, not a VARIABLE_STORE_HEADER")

        if o.fmt != 0x5A:
            raise Exception(
                "VARIABLE_STORE_HEADER format is not set to FORMATTED (0x5A)"
            )
        if o.state != 0xFE:
            raise Exception("VARIABLE_STORE_HEADER state is not set to HEALTHY (0xFE)")

        return o

    def serialize(self):
        return struct.pack(
            "<16sIBBHI",
            self.hdrUUID.bytes,
            self.len,
            self.fmt,
            self.state,
            self.reserved1,
            self.reserved2,
        )

    @classmethod
    def create(cls):
        o = cls()
        o.hdrUUID = gEfiAuthenticatedVariableGuid
        o.len = 262072
        o.fmt = 0x5A
        o.state = 0xFE
        o.reserved1 = 0
        o.reserved2 = 0
        return o

    def print(self):
        print("Variable Store Header")
        print("=====================")
        print("Length:              %s bytes (%.1f KiB)" % (self.len, self.len / 1024))
        print("Format:              0x%02x" % self.fmt)
        print("State:               0x%02x" % self.state)

        print("")


class AuthenticatedVariable(object):
    @classmethod
    def deserialize(cls, f):
        o = cls()

        (
            o.magic,
            o.state,
            o.reserved1,
            o.flags,
            o.monotonicCount,
            o.timestamp,
            o.pubKeyIdx,
            o.nameLen,
            o.dataLen,
            o.vendorUUID,
        ) = struct.unpack("<HBBIQ16sIII16s", f.read(60))
        o.vendorUUID = uuid.UUID(bytes=o.vendorUUID)
        o.timestamp = UEFITime.deserialize(o.timestamp)

        if o.magic == 0xFFFF:
            return None
        if o.magic != 0x55AA:
            raise Exception(
                "unexpected magic (0x%x), not an AUTHENTICATED_VARIABLE_HEADER" % magic
            )

        o.name = f.read(o.nameLen).decode("utf-16le").rstrip("\0")
        o.data = f.read(o.dataLen)

        if f.tell() % 4:
            f.read(4 - (f.tell() % 4))

        assert (f.tell() % 4) == 0
        return o

    @classmethod
    def deserializeFromDocument(cls, vendorID, name, doc):
        o = cls()
        o.magic = 0x55AA
        o.reserved1 = 0
        o.flags = doc.get("Flags", 0)
        if not doc.get("Volatile"):
            o.flags = o.flags | 0x1
        if doc.get("Boot Access"):
            o.flags = o.flags | 0x2
        if doc.get("Runtime Access"):
            o.flags = o.flags | 0x4
        if doc.get("Hardware Error Record"):
            o.flags = o.flags | 0x8
        if doc.get("Authenticated Write Access"):
            o.flags = o.flags | 0x10
        if doc.get("Time Based Authenticated Write Access"):
            o.flags = o.flags | 0x20
        if doc.get("Append Write"):
            o.flags = o.flags | 0x40

        if doc.get("Timestamp"):
            o.timestamp = UEFITime(doc["Timestamp"])
        else:
            o.timestamp = UEFITime()

        o.monotonicCount = doc.get("Monotonic Count", 0)
        o.pubKeyIdx = doc.get("Public Key Index", 0)
        o.name = name
        o.data = doc["Data"]
        o.dataLen = len(o.data)
        o.nameLen = len(name) * 2 + 2
        o.state = (0x40 | 0x80) ^ 0xFF
        o.vendorUUID = lookupUUID(vendorID)
        return o

    def serialize(self):
        name = self.name.encode("utf-16le")
        assert self.nameLen == len(name) + 2
        assert self.dataLen == len(self.data)
        b = struct.pack(
            "<HBBIQ16sIII16s",
            self.magic,
            self.state,
            self.reserved1,
            self.flags,
            self.monotonicCount,
            self.timestamp.serialize(),
            self.pubKeyIdx,
            self.nameLen,
            self.dataLen,
            self.vendorUUID.bytes,
        )
        b += name + b"\0\0"
        b += self.data
        return b

    @property
    def isDeleted(self):
        state = self.state ^ 0xFF
        return bool(state & 2)

    def print(self):
        state = self.state ^ 0xFF
        origState = state
        VAR_IN_DELETED_TRANSITION = 0xFE ^ 0xFF
        VAR_DELETED = 0xFD ^ 0xFF
        VAR_HEADER_VALID_ONLY = 0x7F ^ 0xFF
        VAR_ADDED = 0x40

        stext = ""
        for n, v in (
            ("VAR_IN_DELETED_TRANSITION", VAR_IN_DELETED_TRANSITION),
            ("VAR_DELETED", VAR_DELETED),
            ("VAR_HEADER_VALID_ONLY", VAR_HEADER_VALID_ONLY),
            ("VAR_ADDED", VAR_ADDED),
        ):
            if (state & v) == v:
                if len(stext) > 0:
                    stext += " | "
                stext += n
                state = state ^ v

        if state:
            if len(stext) > 0:
                stext += " | "
            stext += "0x%x" % state

        ftext = []
        flags = self.flags
        for n, v in (
            ("NON_VOLATILE", 0x1),
            ("BOOTSERVICE_ACCESS", 0x2),
            ("RUNTIME_ACCESS", 0x4),
            ("HARDWARE_ERROR_RECORD", 0x8),
            ("AUTHENTICATED_WRITE_ACCESS", 0x10),
            ("TIME_BASED_AUTHENTICATED_WRITE_ACCESS", 0x20),
            ("APPEND_WRITE", 0x40),
        ):
            if flags & v:
                flags = flags ^ v
                ftext.append(n)

        ftext = " ".join(ftext)
        if flags:
            ftext += " 0x%08x" % flags

        print("Authenticated Variable")
        print("======================")
        print("Name:                %r" % self.name)
        print("Vendor UUID:         %s" % resolveUUID(self.vendorUUID))
        print("Monotonic Count:     %s" % self.monotonicCount)
        print("Public Key Index:    %s" % self.pubKeyIdx)
        print("State:               %s" % stext)
        print("Flags:               %s" % ftext)
        t = self.timestamp.time
        if t:
            print("Timestamp:           %s" % t)
        print("Data Length:         %s bytes" % self.dataLen)
        hexdump(io.BytesIO(self.data), elide=True)
        print("")
        return True


def cmdDump(args):
    with open(args["input-file"], "rb") as f:
        fvh = FirmwareVolumeHeader.deserialize(f)
        fvh.print()

        vsh = VariableStoreHeader.deserialize(f)
        vsh.print()

        while True:
            av = AuthenticatedVariable.deserialize(f)
            if not av:
                break
            if not av.isDeleted or args.get("deleted"):
                av.print()

    return 0


def cmdExport(args):
    doc = dict(Variables={})
    docVars = doc["Variables"]

    with open(args["input-file"], "rb") as f:
        fvh = FirmwareVolumeHeader.deserialize(f)
        vsh = VariableStoreHeader.deserialize(f)
        while True:
            av = AuthenticatedVariable.deserialize(f)
            if not av:
                break
            if av.isDeleted:
                continue
            k = resolveUUID(av.vendorUUID)
            docVars.setdefault(k, {})
            docVars[k][av.name] = x = {}
            x["Data"] = av.data
            if av.monotonicCount:
                x["Monotonic Count"] = av.monotonicCount
            if av.pubKeyIdx:
                x["Public Key Index"] = av.pubKeyIdx
            if not (av.flags & 0x1):
                x["Volatile"] = True
            if av.flags & 0x2:
                x["Boot Access"] = True
            if av.flags & 0x4:
                x["Runtime Access"] = True
            if av.flags & 0x8:
                x["Hardware Error Record"] = True
            if av.flags & 0x10:
                x["Authenticated Write Access"] = True
            if av.flags & 0x20:
                x["Time Based Authenticated Write Access"] = True
            if av.flags & 0x40:
                x["Append Write"] = True

            flags = av.flags & ~(0x1 | 0x2 | 0x4 | 0x8 | 0x10 | 0x20 | 0x40)
            if flags:
                x["Flags"] = flags

            t = av.timestamp.time
            if t:
                x["Timestamp"] = t

    print(yaml.dump(doc))
    return 0


def cmdCompile(args):
    with open(args["input-file"], "r") as f:
        doc = yaml.safe_load(f.read())

        vs = []
        docVars = doc.get("Variables", {})
        for vendorID in docVars.keys():
            for name in docVars[vendorID].keys():
                av = AuthenticatedVariable.deserializeFromDocument(
                    vendorID, name, docVars[vendorID][name]
                )
                vs.append(av)

    with open(args["output-file"], "wb") as fo:
        fm = io.BytesIO(b"\xFF" * (528 * 1024))
        fm.write(FirmwareVolumeHeader.create().serialize())
        fm.write(VariableStoreHeader.create().serialize())

        for v in vs:
            fm.write(v.serialize())
            if fm.tell() % 4:
                fm.write(b"\xFF" * (4 - (fm.tell() % 4)))
            assert (fm.tell() % 4) == 0

        if fm.tell() > 0x41000:
            raise Exception("too many variables to fit in file")

        fm.seek(0x41000)
        fm.write(
            binascii.unhexlify(
                b"2b29589e687c7d49a0ce6500fd9f1b952caf2c64feffffffe00f000000000000"
            )
        )
        fm.seek(0)
        fo.write(fm.read())

    return 0


def cmdGenerateBlank(args):
    with open(args["output-file"], "wb") as fo:
        fm = io.BytesIO(b"\xFF" * (528 * 1024))
        fm.write(FirmwareVolumeHeader.create().serialize())
        fm.write(VariableStoreHeader.create().serialize())

        fm.seek(0x41000)
        fm.write(
            binascii.unhexlify(
                b"2b29589e687c7d49a0ce6500fd9f1b952caf2c64feffffffe00f000000000000"
            )
        )
        fm.seek(0)
        fo.write(fm.read())

    return 0


def run():
    ap = argparse.ArgumentParser()
    subap = ap.add_subparsers(help="subcommands")
    apDump = subap.add_parser(
        "dump", help="Dump information in a OVMF_VARS.fd file in human-readable form"
    )
    apExport = subap.add_parser(
        "export", help="Export the contents of OVMF_VARS.fd as YAML"
    )
    apCompile = subap.add_parser("compile", help="Generate an OVMF_VARS.fd from YAML")
    apGenerateBlank = subap.add_parser(
        "generate-blank", help="Generate an empty OVMF_VARS.fd file"
    )

    apDump.add_argument("input-file", help="OVMF_VARS.fd file to dump")
    apDump.add_argument(
        "--deleted", "-d", action="store_true", help="show deleted variables"
    )
    apDump.set_defaults(func=cmdDump)

    apExport.add_argument("input-file", help="OVMF_VARS.fd file to dump")
    apExport.set_defaults(func=cmdExport)

    apCompile.add_argument("input-file", help="YAML file to compile")
    apCompile.add_argument("output-file", help="Filename to write OVMF_VARS.fd to")
    apCompile.set_defaults(func=cmdCompile)

    apGenerateBlank.add_argument(
        "output-file", help="Filename to write OVMF_VARS.fd to"
    )
    apGenerateBlank.set_defaults(func=cmdGenerateBlank)

    args = vars(ap.parse_args())
    if not args.get("func"):
        ap.print_usage()
        return 1

    return args["func"](args)

    doc = dict(Variables={})
    docVars = doc["Variables"]
    with open(args["input-file"], "rb") as f:
        fvh = FirmwareVolumeHeader.deserialize(f)
        fvh.print()

        vsh = VariableStoreHeader.deserialize(f)
        vsh.print()

        while True:
            av = AuthenticatedVariable.deserialize(f)
            if not av:
                break
            if not av.isDeleted:
                av.print()
                k = resolveUUID(av.vendorUUID)
                docVars.setdefault(k, {})
                docVars[k][av.name] = x = {}
                x["Data"] = av.data
                x["Monotonic Count"] = av.monotonicCount
                x["Public Key Index"] = av.pubKeyIdx
                x["Flags"] = av.flags

    print(yaml.dump(doc))
    return 0
