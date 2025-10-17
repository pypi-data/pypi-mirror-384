import asyncio
import html
import io
import os
import re
import tempfile
import uuid
from email.header import decode_header, make_header
from email.message import Message
from email.parser import BytesParser
from email.policy import default
from typing import Any, Callable, Dict, List, Optional

from ..common.logger import logger
from .base_handler import BaseHandler

_MAX_ATTACHMENT_BYTES = 50 * 1024 * 1024  # 50MB safety cap
_READ_CHUNK = 1024 * 1024  # 1MB
_PARSE_TIMEOUT_SEC = 30
_CONVERT_TIMEOUT_SEC = 60


def _safe_decode_header(value: Optional[str]) -> str:
    try:
        if not value:
            return ""
        return str(make_header(decode_header(value)))
    except Exception:
        return value or ""


def _coerce_charset(s: bytes, charset: Optional[str]) -> str:
    for cs in [charset, "utf-8", "latin-1"]:
        if not cs:
            continue
        try:
            return s.decode(cs, errors="replace")
        except Exception:
            continue
    return s.decode("utf-8", errors="replace")


def _basic_html_to_md(html_text: str) -> str:
    # Minimal, dependency-free HTML → Markdown-ish conversion that preserves readability
    txt = html_text
    txt = re.sub(r"(?is)<(script|style).*?>.*?</\1>", "", txt)
    txt = re.sub(r"(?i)<br\s*/?>", "\n", txt)
    txt = re.sub(r"(?i)</p\s*>", "\n\n", txt)
    txt = re.sub(r"(?i)<li\s*>", "- ", txt)
    txt = re.sub(r"(?i)</h1\s*>", "\n\n", re.sub(r"(?i)<h1\s*>(.*?)</h1\s*>", r"# \1\n\n", txt))
    txt = re.sub(r"(?i)</h2\s*>", "\n\n", re.sub(r"(?i)<h2\s*>(.*?)</h2\s*>", r"## \1\n\n", txt))
    txt = re.sub(r"(?i)</h3\s*>", "\n\n", re.sub(r"(?i)<h3\s*>(.*?)</h3\s*>", r"### \1\n\n", txt))
    txt = re.sub(r"(?i)<a\s+[^>]*href=['\"]([^'\"]+)['\"][^>]*>(.*?)</a>", r"[\2](\1)", txt)
    txt = re.sub(
        r"(?i)<img\s+[^>]*alt=['\"]([^'\"]*)['\"][^>]*src=['\"]([^'\"]+)['\"][^>]*>",
        r"![\1](\2)",
        txt,
    )
    txt = re.sub(r"(?is)<[^>]+>", "", txt)
    txt = html.unescape(txt)
    # Normalize whitespace
    txt = re.sub(r"[ \t]+\n", "\n", txt)
    txt = re.sub(r"\n{3,}", "\n\n", txt).strip()
    return txt


class EmailHandler(BaseHandler):
    SUPPORTED_EXTENSIONS = frozenset({".eml", ".p7s", ".msg"})

    async def handle(self, file_path: str, *args, **kwargs) -> Optional[str]:
        logger.info(f"EmailHandler: Processing email file: {file_path}")
        attachment_converter: Optional[Callable[[str, str], "asyncio.Future[str]"]] = kwargs.get(
            "attachment_converter"
        )
        try:
            email_data = await asyncio.wait_for(
                asyncio.to_thread(self._parse_email, file_path), timeout=_PARSE_TIMEOUT_SEC
            )
            if not email_data:
                return None
            markdown_content = await self._build_markdown(email_data, attachment_converter)
            return markdown_content
        except asyncio.TimeoutError:
            logger.error(f"EmailHandler: Timeout while processing email file: {file_path}")
            return None
        except Exception as e:
            logger.exception(f"EmailHandler: Error processing email file: {file_path}: {e}")
            return None

    def _parse_email(self, file_path: str) -> Dict[str, Any]:
        """
        Parses the EML/P7S file and extracts relevant information.
        Returns:
            {
                "subject": str,
                "from": str,
                "to": str,
                "cc": str,
                "bcc": str,
                "date": str,
                "body_text": str,   # text/plain best-effort
                "body_html": str,   # raw HTML if present
                "attachments": List[Dict[str, str]]  # [{"filename":..., "path":..., "content_type":..., "cid":...}]
            }
        """
        try:
            with open(file_path, "rb") as f:
                msg: Message = BytesParser(policy=default).parse(f)
            subject = _safe_decode_header(msg.get("Subject", "(No Subject)")) or "(No Subject)"
            from_ = _safe_decode_header(msg.get("From", "(Unknown Sender)")) or "(Unknown Sender)"
            to_ = _safe_decode_header(msg.get("To", "")) or ""
            cc_ = _safe_decode_header(msg.get("Cc", "")) or ""
            bcc_ = _safe_decode_header(msg.get("Bcc", "")) or ""
            date_ = msg.get("Date", "(Unknown Date)") or "(Unknown Date)"
            body_text = ""
            body_html = ""
            attachments: List[Dict[str, str]] = []

            def _should_skip(part: Message) -> bool:
                ctype = (part.get_content_type() or "").lower()
                # Skip S/MIME signatures and pkcs7 blobs as attachments
                if ctype in ("application/pkcs7-signature", "application/pkcs7-mime"):
                    return True
                return False

            if msg.is_multipart():
                for part in msg.walk():
                    if part.is_multipart():
                        continue
                    if _should_skip(part):
                        continue
                    disp = part.get_content_disposition() or ""
                    ctype = (part.get_content_type() or "").lower()
                    cid = (part.get("Content-ID") or "").strip().strip("<>")
                    payload = part.get_payload(decode=True) or b""
                    if disp == "attachment" or (
                        disp == "inline" and cid
                    ):  # treat inline with CID as attachment (e.g., images)
                        filename = part.get_filename()
                        filename = (
                            _safe_decode_header(filename)
                            if filename
                            else f"attachment-{uuid.uuid4().hex}"
                        )
                        # Write safely with size cap
                        suffix = os.path.splitext(filename)[1][:10] if filename else ""
                        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                            written = 0
                            stream = io.BytesIO(payload)
                            while True:
                                chunk = stream.read(_READ_CHUNK)
                                if not chunk:
                                    break
                                written += len(chunk)
                                if written > _MAX_ATTACHMENT_BYTES:
                                    raise ValueError(
                                        f"Attachment '{filename}' exceeds {_MAX_ATTACHMENT_BYTES} bytes"
                                    )
                                tmp_file.write(chunk)
                            attachments.append(
                                {
                                    "filename": filename,
                                    "path": tmp_file.name,
                                    "content_type": ctype,
                                    "cid": cid,
                                }
                            )
                        continue
                    if ctype == "text/plain" and not body_text:
                        body_text = _coerce_charset(payload, part.get_content_charset() or "utf-8")
                    elif ctype == "text/html" and not body_html:
                        body_html = _coerce_charset(payload, part.get_content_charset() or "utf-8")
            else:
                ctype = (msg.get_content_type() or "").lower()
                if ctype == "text/plain":
                    body_text = _coerce_charset(
                        msg.get_payload(decode=True) or b"", msg.get_content_charset() or "utf-8"
                    )
                elif ctype == "text/html":
                    body_html = _coerce_charset(
                        msg.get_payload(decode=True) or b"", msg.get_content_charset() or "utf-8"
                    )
            return {
                "subject": subject,
                "from": from_,
                "to": to_,
                "cc": cc_,
                "bcc": bcc_,
                "date": date_,
                "body_text": body_text.strip(),
                "body_html": body_html.strip(),
                "attachments": attachments,
            }
        except Exception as e:
            logger.exception(f"EmailHandler: Error parsing email {file_path}: {e}")
            return {}

    async def _build_markdown(
        self,
        email_data: Dict[str, Any],
        attachment_converter: Optional[Callable[[str, str], "asyncio.Future[str]"]] = None,
    ) -> str:
        # Resolve inline CID references in HTML to temp file paths (if any)
        cid_map = {a["cid"]: a for a in email_data.get("attachments", []) if a.get("cid")}
        body_md = ""
        if email_data.get("body_text"):
            body_md = email_data["body_text"]
        elif email_data.get("body_html"):
            html_body = email_data["body_html"]
            if cid_map:
                for cid, meta in cid_map.items():
                    html_body = re.sub(
                        rf"(?i)src=['\"]cid:{re.escape(cid)}['\"]",
                        f"src=\"{meta['path']}\"",
                        html_body,
                    )
            body_md = _basic_html_to_md(html_body)
        header_lines = [
            f"# Email: {email_data.get('subject', '(No Subject)')}",
            f"**From:** {email_data.get('from', '')}",
            f"**To:** {email_data.get('to', '')}",
        ]
        if email_data.get("cc"):
            header_lines.append(f"**Cc:** {email_data['cc']}")
        if email_data.get("bcc"):
            header_lines.append(f"**Bcc:** {email_data['bcc']}")
        header_lines.append(f"**Date:** {email_data.get('date', '')}")
        markdown_parts: List[str] = ["\n".join(header_lines), ""]
        if body_md:
            markdown_parts.append("```")
            markdown_parts.append(body_md)
            markdown_parts.append("```")
        # Convert attachments (non-CID inline images will also appear here)
        attachments = email_data.get("attachments", [])
        for att in attachments:
            filename = att.get("filename", "attachment")
            path = att.get("path")
            ctype = att.get("content_type", "")
            if att.get("cid"):  # Already linked in body if referenced; still list it
                markdown_parts.append(f"\n## Inline asset: {filename} ({ctype})\n")
                markdown_parts.append(
                    f"![{filename}]({path})"
                    if ctype.startswith("image/")
                    else f"[{filename}]({path})"
                )
                continue
            markdown_parts.append(f"\n## Attachment: {filename} ({ctype})\n")
            try:
                if attachment_converter:
                    converted = await asyncio.wait_for(
                        attachment_converter(path, ctype), timeout=_CONVERT_TIMEOUT_SEC
                    )
                    markdown_parts.append(converted if converted else f"[Saved attachment]({path})")
                else:
                    # Built-in light handling when no converter provided
                    if ctype.startswith("image/"):
                        markdown_parts.append(f"![{filename}]({path})")
                    elif ctype.startswith("text/"):
                        try:
                            with open(path, "rb") as f:
                                content = f.read(_MAX_ATTACHMENT_BYTES + 1)
                            if len(content) > _MAX_ATTACHMENT_BYTES:
                                raise ValueError(
                                    f"Attachment too large to inline (> {_MAX_ATTACHMENT_BYTES} bytes)"
                                )
                            text = _coerce_charset(content, "utf-8")
                            markdown_parts.append("\n```")
                            markdown_parts.append(text.strip())
                            markdown_parts.append("```")
                        except Exception as e:
                            logger.warning(
                                f"EmailHandler: Inline text fallback failed for {filename}: {e}"
                            )
                            markdown_parts.append(f"[Saved attachment]({path})")
                    elif ctype == "text/html":
                        try:
                            with open(path, "rb") as f:
                                content = f.read(min(_MAX_ATTACHMENT_BYTES, 5 * 1024 * 1024))
                            text = _coerce_charset(content, "utf-8")
                            markdown_parts.append(_basic_html_to_md(text))
                        except Exception as e:
                            logger.warning(
                                f"EmailHandler: HTML to MD fallback failed for {filename}: {e}"
                            )
                            markdown_parts.append(f"[Saved attachment]({path})")
                    else:
                        markdown_parts.append(f"[Saved attachment]({path})")
            except asyncio.TimeoutError:
                logger.error(f"EmailHandler: Timeout converting attachment '{filename}'")
                markdown_parts.append(f"[Attachment conversion timed out: {filename}]")
            except Exception as e:
                logger.error(f"EmailHandler: Error converting attachment '{filename}': {e}")
                markdown_parts.append(f"[Error converting attachment: {e}]")
            finally:
                try:
                    os.remove(path)
                except OSError as e:
                    logger.warning(
                        f"EmailHandler: Could not remove temporary attachment file '{path}': {e}"
                    )
        return "\n".join(markdown_parts)
