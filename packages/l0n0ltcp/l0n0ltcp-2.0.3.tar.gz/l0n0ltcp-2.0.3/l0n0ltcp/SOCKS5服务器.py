#!/usr/bin/env python3
# 本文件使用 microsoft copilit  gpt5 生成
# generate by microsoft copilit gpt5
import asyncio
import struct
import socket
import argparse
from typing import Tuple, Optional
from .通用 import 使用uvloop

SOCKS_VERSION = 5

# SOCKS5 reply codes (RFC 1928)
REP_SUCCEEDED = 0x00
REP_GENERAL_FAILURE = 0x01
REP_CONNECTION_NOT_ALLOWED = 0x02
REP_NETWORK_UNREACHABLE = 0x03
REP_HOST_UNREACHABLE = 0x04
REP_CONNECTION_REFUSED = 0x05
REP_TTL_EXPIRED = 0x06
REP_COMMAND_NOT_SUPPORTED = 0x07
REP_ADDRESS_TYPE_NOT_SUPPORTED = 0x08

# ATYP
ATYP_IPV4 = 0x01
ATYP_DOMAIN = 0x03
ATYP_IPV6 = 0x04

# CMD
CMD_CONNECT = 0x01
CMD_BIND = 0x02       # Not implemented
CMD_UDP_ASSOCIATE = 0x03  # Not implemented

READ_TIMEOUT = 15.0
PIPE_BUFFER_LIMIT = 64 * 1024


async def read_exact(reader: asyncio.StreamReader, n: int) -> bytes:
    """Read exactly n bytes with timeout."""
    try:
        return await asyncio.wait_for(reader.readexactly(n), READ_TIMEOUT)
    except asyncio.IncompleteReadError as e:
        raise ConnectionError("incomplete read") from e
    except asyncio.TimeoutError as e:
        raise TimeoutError("read timeout") from e


async def socks5_handshake(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    """
    Client greeting:
      +----+----------+----------+
      |VER | NMETHODS | METHODS  |
      +----+----------+----------+
      | 1  |    1     | 1 to 255 |
    Server selects:
      +----+--------+
      |VER | METHOD |
      +----+--------+
      | 1  |   1    |
    """
    # Read VER, NMETHODS
    data = await read_exact(reader, 2)
    ver, nmethods = data[0], data[1]
    if ver != SOCKS_VERSION:
        raise ConnectionError(f"unsupported version: {ver}")

    methods = await read_exact(reader, nmethods)
    # We only support NO AUTHENTICATION REQUIRED (0x00)
    if 0x00 not in methods:
        # Reply: no acceptable methods (0xFF)
        writer.write(struct.pack("!BB", SOCKS_VERSION, 0xFF))
        await writer.drain()
        raise ConnectionError("no acceptable auth method")

    # Select NO AUTH
    writer.write(struct.pack("!BB", SOCKS_VERSION, 0x00))
    await writer.drain()


async def parse_request(reader: asyncio.StreamReader) -> Tuple[int, str, int]:
    """
    Request:
      +----+-----+-------+------+----------+----------+
      |VER | CMD |  RSV  | ATYP | DST.ADDR | DST.PORT |
      +----+-----+-------+------+----------+----------+
      | 1  |  1  |  0x00 |  1   | Variable |    2     |
    Returns (cmd, host, port)
    """
    header = await read_exact(reader, 4)
    ver, cmd, rsv, atyp = header
    if ver != SOCKS_VERSION or rsv != 0x00:
        raise ConnectionError("bad request header")

    if atyp == ATYP_IPV4:
        addr = await read_exact(reader, 4)
        host = socket.inet_ntop(socket.AF_INET, addr)
    elif atyp == ATYP_DOMAIN:
        dlen = (await read_exact(reader, 1))[0]
        domain = await read_exact(reader, dlen)
        host = domain.decode("idna")  # domain label; IDNA safe
    elif atyp == ATYP_IPV6:
        addr = await read_exact(reader, 16)
        host = socket.inet_ntop(socket.AF_INET6, addr)
    else:
        raise ConnectionError("address type not supported")

    port_bytes = await read_exact(reader, 2)
    port = struct.unpack("!H", port_bytes)[0]

    return cmd, host, port


def build_reply(rep: int, bind_host: str, bind_port: int, atyp_hint: Optional[int] = None) -> bytes:
    """
    Server reply:
      +----+-----+-------+------+----------+----------+
      |VER | REP |  RSV  | ATYP | BND.ADDR | BND.PORT |
      +----+-----+-------+------+----------+----------+
      | 1  |  1  |  0x00 |  1   | Variable |    2     |
    """
    ver = SOCKS_VERSION
    rsv = 0x00
    # Choose ATYP consistent with bind_host format
    # If hint provided, use it; otherwise detect by literal format.
    if atyp_hint is not None:
        atyp = atyp_hint
    else:
        try:
            socket.inet_pton(socket.AF_INET, bind_host)
            atyp = ATYP_IPV4
        except OSError:
            try:
                socket.inet_pton(socket.AF_INET6, bind_host)
                atyp = ATYP_IPV6
            except OSError:
                atyp = ATYP_DOMAIN

    if atyp == ATYP_IPV4:
        addr = socket.inet_pton(socket.AF_INET, bind_host)
        body = struct.pack("!BBBB4sH", ver, rep, rsv, atyp, addr, bind_port)
    elif atyp == ATYP_IPV6:
        addr = socket.inet_pton(socket.AF_INET6, bind_host)
        body = struct.pack("!BBBB16sH", ver, rep, rsv, atyp, addr, bind_port)
    else:  # domain
        domain_bytes = bind_host.encode("idna")
        body = struct.pack("!BBBBB", ver, rep, rsv, ATYP_DOMAIN, len(
            domain_bytes)) + domain_bytes + struct.pack("!H", bind_port)
    return body


async def pipe_stream(reader: asyncio.StreamReader, writer: asyncio.StreamWriter, label: str) -> None:
    try:
        while True:
            data = await reader.read(PIPE_BUFFER_LIMIT)
            if not data:
                break
            writer.write(data)
            await writer.drain()
    except asyncio.CancelledError:
        pass
    except Exception as e:
        # Optional: log if needed
        # print(f"pipe {label} error: {e}")
        pass
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass


async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    peer = writer.get_extra_info("peername")
    local = writer.get_extra_info("sockname")
    # print(f"new client {peer} -> {local}")
    try:
        await socks5_handshake(reader, writer)
        cmd, host, port = await parse_request(reader)

        if cmd != CMD_CONNECT:
            # Reply command not supported
            rep = REP_COMMAND_NOT_SUPPORTED
            reply = build_reply(rep, "0.0.0.0", 0, atyp_hint=ATYP_IPV4)
            writer.write(reply)
            await writer.drain()
            return

        # Resolve and connect
        try:
            target_reader, target_writer = await asyncio.wait_for(
                asyncio.open_connection(host=host, port=port),
                timeout=READ_TIMEOUT
            )
        except asyncio.TimeoutError:
            rep = REP_TTL_EXPIRED
            reply = build_reply(rep, "0.0.0.0", 0, atyp_hint=ATYP_IPV4)
            writer.write(reply)
            await writer.drain()
            return
        except (OSError, ConnectionError):
            # Host unreachable or refused; choose a generic failure for simplicity
            rep = REP_GENERAL_FAILURE
            reply = build_reply(rep, "0.0.0.0", 0, atyp_hint=ATYP_IPV4)
            writer.write(reply)
            await writer.drain()
            return

        # Success reply: report proxy's local bind address for this outbound connection
        bound = target_writer.get_extra_info("sockname")
        bind_host, bind_port = bound[0], bound[1]
        success = build_reply(REP_SUCCEEDED, bind_host, bind_port)
        writer.write(success)
        await writer.drain()

        # Bi-directional piping
        client_to_target = asyncio.create_task(
            pipe_stream(reader, target_writer, "c->t")
        )
        target_to_client = asyncio.create_task(
            pipe_stream(target_reader, writer, "t->c")
        )

        done, pending = await asyncio.wait(
            {client_to_target, target_to_client},
            return_when=asyncio.FIRST_COMPLETED
        )
        for task in pending:
            task.cancel()

    except Exception as e:
        # Optional: quick debug
        # print(f"client {peer} error: {e}")
        pass
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass


async def run() -> None:
    parser = argparse.ArgumentParser(description="socks5服务器")
    parser.add_argument("本地监听地址",  help="本地监听地址")
    parser.add_argument("本地监听端口", type=int,  help="本地监听端口")
    args = parser.parse_args()
    server = await asyncio.start_server(handle_client, args.本地监听地址, args.本地监听端口)
    addr_list = ", ".join(
        f"{s.getsockname()[0]}:{s.getsockname()[1]}" for s in server.sockets or [])
    print(f"[SOCKS5] listening on {addr_list} (NO-AUTH, CONNECT only)")
    async with server:
        await server.serve_forever()

def main():
    try:
        使用uvloop()
        asyncio.run(run())
    except KeyboardInterrupt:
        print("\n[SOCKS5] shutting down")
