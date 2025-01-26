import ssl
import socket
import OpenSSL
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging


@dataclass
class SSLCertificate:
    subject: str
    issuer: str
    version: int
    serial_number: str
    not_before: datetime.datetime
    not_after: datetime.datetime
    signature_algorithm: str
    public_key_bits: int
    public_key_type: str
    extensions: List[str]
    san: List[str]


@dataclass
class SSLScanResult:
    hostname: str
    port: int
    certificate: SSLCertificate
    protocols: List[str]
    cipher_suites: List[str]
    vulnerabilities: List[str]
    grade: str
    warnings: List[str]


class SSLChecker:
    def __init__(self, timeout: int = 10, concurrent_checks: int = 10):
        self.timeout = timeout
        self.executor = ThreadPoolExecutor(max_workers=concurrent_checks)
        self.logger = logging.getLogger("nexus.sslchecker")

        # Define security standards
        self.minimum_protocol = ssl.TLSVersion.TLSv1_2
        self.insecure_ciphers = {
            'RC4', 'DES', '3DES', 'MD5', 'NULL',
            'EXPORT', 'LOW', 'MEDIUM'
        }

    async def check_ssl(self, hostname: str, port: int = 443) -> SSLScanResult:
        """Perform comprehensive SSL/TLS security check"""
        try:
            # Run SSL checks in thread pool to avoid blocking
            future = self.executor.submit(
                self._perform_ssl_checks,
                hostname,
                port
            )
            return await asyncio.wrap_future(future)

        except Exception as e:
            self.logger.error(f"SSL check failed for {hostname}:{port} - {str(e)}")
            raise

    def _perform_ssl_checks(self, hostname: str, port: int) -> SSLScanResult:
        """Execute all SSL security checks"""
        context = self._create_ssl_context()
        cert = self._get_certificate(hostname, port)
        protocols = self._check_protocols(hostname, port)
        ciphers = self._check_cipher_suites(hostname, port)

        vulnerabilities = []
        warnings = []

        # Check certificate validity
        self._check_certificate_validity(cert, hostname, vulnerabilities, warnings)

        # Check protocols and ciphers
        self._check_security_settings(protocols, ciphers, vulnerabilities, warnings)

        # Calculate security grade
        grade = self._calculate_security_grade(
            vulnerabilities,
            warnings,
            cert,
            protocols,
            ciphers
        )

        return SSLScanResult(
            hostname=hostname,
            port=port,
            certificate=self._parse_certificate(cert),
            protocols=protocols,
            cipher_suites=ciphers,
            vulnerabilities=vulnerabilities,
            grade=grade,
            warnings=warnings
        )

    def _create_ssl_context(self) -> ssl.SSLContext:
        """Create SSL context for testing"""
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        context.set_ciphers('ALL:@SECLEVEL=0')
        return context

    def _get_certificate(self, hostname: str, port: int) -> OpenSSL.crypto.X509:
        """Retrieve SSL certificate from server"""
        context = self._create_ssl_context()
        with socket.create_connection((hostname, port), timeout=self.timeout) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssl_sock:
                der_cert = ssl_sock.getpeercert(binary_form=True)
                return OpenSSL.crypto.load_certificate(
                    OpenSSL.crypto.FILETYPE_ASN1,
                    der_cert
                )

    def _check_protocols(self, hostname: str, port: int) -> List[str]:
        """Check supported SSL/TLS protocols"""
        protocols = []
        versions = [
            ssl.TLSVersion.SSLv3,
            ssl.TLSVersion.TLSv1,
            ssl.TLSVersion.TLSv1_1,
            ssl.TLSVersion.TLSv1_2,
            ssl.TLSVersion.TLSv1_3
        ]

        for version in versions:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS)
            context.minimum_version = version
            context.maximum_version = version
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            try:
                with socket.create_connection((hostname, port), timeout=self.timeout) as sock:
                    with context.wrap_socket(sock, server_hostname=hostname) as ssl_sock:
                        protocols.append(ssl_sock.version())
            except:
                continue

        return protocols

    def _check_cipher_suites(self, hostname: str, port: int) -> List[str]:
        """Check supported cipher suites"""
        context = self._create_ssl_context()
        ciphers = []

        with socket.create_connection((hostname, port), timeout=self.timeout) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssl_sock:
                ciphers = ssl_sock.shared_ciphers()

        return [cipher[0] for cipher in ciphers] if ciphers else []

    def _parse_certificate(self, cert: OpenSSL.crypto.X509) -> SSLCertificate:
        """Parse certificate information"""
        subject = dict(cert.get_subject().get_components())
        issuer = dict(cert.get_issuer().get_components())

        # Get Subject Alternative Names
        san = []
        for i in range(cert.get_extension_count()):
            ext = cert.get_extension(i)
            if ext.get_short_name() == b'subjectAltName':
                san = str(ext).split(', ')

        return SSLCertificate(
            subject=subject.get(b'CN', b'').decode(),
            issuer=issuer.get(b'CN', b'').decode(),
            version=cert.get_version(),
            serial_number=hex(cert.get_serial_number()),
            not_before=datetime.datetime.strptime(
                cert.get_notBefore().decode(),
                '%Y%m%d%H%M%SZ'
            ),
            not_after=datetime.datetime.strptime(
                cert.get_notAfter().decode(),
                '%Y%m%d%H%M%SZ'
            ),
            signature_algorithm=cert.get_signature_algorithm().decode(),
            public_key_bits=cert.get_pubkey().bits(),
            public_key_type=cert.get_pubkey().type_name(),
            extensions=[ext.get_short_name().decode() for ext in cert.get_extensions()],
            san=san
        )

    def _check_certificate_validity(
            self,
            cert: OpenSSL.crypto.X509,
            hostname: str,
            vulnerabilities: List[str],
            warnings: List[str]
    ):
        """Check certificate validity and security"""
        now = datetime.datetime.utcnow()
        not_after = datetime.datetime.strptime(
            cert.get_notAfter().decode(),
            '%Y%m%d%H%M%SZ'
        )

        # Check expiration
        if now > not_after:
            vulnerabilities.append("Certificate has expired")
        elif (not_after - now).days < 30:
            warnings.append("Certificate expires in less than 30 days")

        # Check key strength
        key = cert.get_pubkey()
        if key.type_name() == 'RSA' and key.bits() < 2048:
            vulnerabilities.append("Weak RSA key (< 2048 bits)")
        elif key.type_name() == 'EC' and key.bits() < 256:
            vulnerabilities.append("Weak ECC key (< 256 bits)")

    def _check_security_settings(
            self,
            protocols: List[str],
            ciphers: List[str],
            vulnerabilities: List[str],
            warnings: List[str]
    ):
        """Check protocol and cipher security"""
        # Check protocols
        if 'SSLv3' in protocols:
            vulnerabilities.append("SSLv3 supported (POODLE vulnerability)")
        if 'TLSv1.0' in protocols:
            warnings.append("TLSv1.0 supported (outdated)")
        if 'TLSv1.1' in protocols:
            warnings.append("TLSv1.1 supported (outdated)")

        # Check ciphers
        for cipher in ciphers:
            if any(weak in cipher.upper() for weak in self.insecure_ciphers):
                vulnerabilities.append(f"Weak cipher supported: {cipher}")

    def _calculate_security_grade(
            self,
            vulnerabilities: List[str],
            warnings: List[str],
            cert: OpenSSL.crypto.X509,
            protocols: List[str],
            ciphers: List[str]
    ) -> str:
        """Calculate overall security grade"""
        score = 100

        # Deduct for vulnerabilities
        score -= len(vulnerabilities) * 20

        # Deduct for warnings
        score -= len(warnings) * 5

        # Check protocols
        if 'TLSv1.3' not in protocols:
            score -= 10
        if 'SSLv3' in protocols:
            score -= 20

        # Check certificate strength
        key = cert.get_pubkey()
        if key.type_name() == 'RSA' and key.bits() < 2048:
            score -= 20

        # Calculate grade
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'
