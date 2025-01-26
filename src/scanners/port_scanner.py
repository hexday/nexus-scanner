import asyncio
import socket
from typing import List, Dict, Optional, Set
import time
from dataclasses import dataclass
import aiohttp
import struct
import logging
from concurrent.futures import ThreadPoolExecutor


@dataclass
class PortScanResult:
    port: int
    state: str  # 'open', 'closed', 'filtered'
    service: Optional[str]
    banner: Optional[str]
    response_time: float


class PortScanner:
    def __init__(self,
                 concurrency: int = 100,
                 timeout: float = 2.0,
                 common_ports: bool = True):
        self.concurrency = concurrency
        self.timeout = timeout
        self.common_ports = common_ports
        self.executor = ThreadPoolExecutor(max_workers=concurrency)
        self.logger = logging.getLogger("nexus.portscanner")

        # Common service ports
        self.service_ports = {
            20: 'FTP-DATA', 21: 'FTP', 22: 'SSH', 23: 'TELNET',
            25: 'SMTP', 53: 'DNS', 80: 'HTTP', 110: 'POP3',
            111: 'RPCBIND', 135: 'MSRPC', 139: 'NETBIOS',
            143: 'IMAP', 443: 'HTTPS', 445: 'SMB',
            993: 'IMAPS', 995: 'POP3S', 1723: 'PPTP',
            3306: 'MYSQL', 3389: 'RDP', 5900: 'VNC',
            8080: 'HTTP-PROXY'
        }

    async def scan_target(self, target: str, port_range: Optional[List[int]] = None) -> List[PortScanResult]:
        """Scan target for open ports"""
        ports = port_range or self._get_ports_to_scan()
        results = []

        # Create scan tasks
        tasks = []
        sem = asyncio.Semaphore(self.concurrency)

        for port in ports:
            task = asyncio.create_task(
                self._scan_port_with_semaphore(sem, target, port)
            )
            tasks.append(task)

        # Execute scans
        scan_results = await asyncio.gather(*tasks)
        results.extend([r for r in scan_results if r is not None])

        # Get service banners for open ports
        banner_tasks = []
        for result in results:
            if result.state == 'open':
                task = asyncio.create_task(
                    self._get_service_banner(target, result)
                )
                banner_tasks.append(task)

        if banner_tasks:
            await asyncio.gather(*banner_tasks)

        return sorted(results, key=lambda x: x.port)

    async def _scan_port_with_semaphore(self,
                                        sem: asyncio.Semaphore,
                                        target: str,
                                        port: int) -> Optional[PortScanResult]:
        """Scan single port with semaphore for concurrency control"""
        async with sem:
            return await self._scan_port(target, port)

    async def _scan_port(self, target: str, port: int) -> Optional[PortScanResult]:
        """Scan a single port using TCP connect scan"""
        start_time = time.time()

        try:
            # Use ThreadPoolExecutor for blocking socket operations
            future = self.executor.submit(self._tcp_connect_scan, target, port)
            is_open = await asyncio.wrap_future(future)

            if is_open:
                state = 'open'
            else:
                state = 'closed'

        except (socket.timeout, ConnectionRefusedError):
            state = 'closed'
        except Exception as e:
            self.logger.debug(f"Error scanning port {port}: {str(e)}")
            state = 'filtered'

        scan_time = time.time() - start_time

        return PortScanResult(
            port=port,
            state=state,
            service=self.service_ports.get(port),
            banner=None,
            response_time=scan_time
        )

    def _tcp_connect_scan(self, target: str, port: int) -> bool:
        """Perform TCP connect scan"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)

        try:
            result = sock.connect_ex((target, port))
            return result == 0
        finally:
            sock.close()

    async def _get_service_banner(self, target: str, result: PortScanResult):
        """Attempt to get service banner"""
        try:
            banner = await self._fetch_banner(target, result.port)
            if banner:
                result.banner = banner.strip()
        except Exception as e:
            self.logger.debug(f"Error getting banner for port {result.port}: {str(e)}")

    async def _fetch_banner(self, target: str, port: int) -> Optional[str]:
        """Fetch service banner using common protocols"""
        protocols = {
            80: self._http_banner,
            443: self._https_banner,
            22: self._ssh_banner,
            21: self._ftp_banner,
            25: self._smtp_banner
        }

        if port in protocols:
            return await protocols[port](target, port)

        return await self._generic_banner(target, port)

    async def _http_banner(self, target: str, port: int) -> Optional[str]:
        """Get HTTP server banner"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                        f"http://{target}:{port}",
                        timeout=self.timeout
                ) as response:
                    return response.headers.get('Server')
            except:
                return None

    async def _https_banner(self, target: str, port: int) -> Optional[str]:
        """Get HTTPS server banner"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                        f"https://{target}:{port}",
                        timeout=self.timeout,
                        verify_ssl=False
                ) as response:
                    return response.headers.get('Server')
            except:
                return None

    async def _ssh_banner(self, target: str, port: int) -> Optional[str]:
        """Get SSH banner"""
        try:
            reader, writer = await asyncio.open_connection(target, port)
            banner = await reader.read(1024)
            writer.close()
            await writer.wait_closed()
            return banner.decode().strip()
        except:
            return None

    async def _ftp_banner(self, target: str, port: int) -> Optional[str]:
        """Get FTP banner"""
        try:
            reader, writer = await asyncio.open_connection(target, port)
            banner = await reader.read(1024)
            writer.close()
            await writer.wait_closed()
            return banner.decode().strip()
        except:
            return None

    async def _smtp_banner(self, target: str, port: int) -> Optional[str]:
        """Get SMTP banner"""
        try:
            reader, writer = await asyncio.open_connection(target, port)
            banner = await reader.read(1024)
            writer.close()
            await writer.wait_closed()
            return banner.decode().strip()
        except:
            return None

    async def _generic_banner(self, target: str, port: int) -> Optional[str]:
        """Attempt to get banner from unknown service"""
        try:
            reader, writer = await asyncio.open_connection(target, port)
            writer.write(b'\r\n')
            await writer.drain()
            banner = await reader.read(1024)
            writer.close()
            await writer.wait_closed()
            return banner.decode().strip()
        except:
            return None

    def _get_ports_to_scan(self) -> List[int]:
        """Get list of ports to scan based on configuration"""
        if self.common_ports:
            return sorted(self.service_ports.keys())
        return list(range(1, 1025))  # Well-known ports
