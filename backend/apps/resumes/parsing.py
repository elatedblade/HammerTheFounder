from io import BytesIO
from zipfile import ZipFile, BadZipFile
from xml.etree import ElementTree


class DocumentParseError(Exception):
    def __init__(self, code):
        self.code = code


def extract_text(content, content_type):
    if content_type == "application/pdf":
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise DocumentParseError("pdf_parser_not_installed") from exc
        try:
            reader = PdfReader(BytesIO(content), strict=True)
            if reader.is_encrypted:
                raise DocumentParseError("encrypted_document")
            if len(reader.pages) > 100:
                raise DocumentParseError("too_many_pages")
            fragments = []
            size = 0
            for page in reader.pages:
                fragment = page.extract_text() or ""
                size += len(fragment) + 1
                if size > 200000:
                    raise DocumentParseError("extracted_text_too_large")
                fragments.append(fragment)
            text = "\n".join(fragments)
        except DocumentParseError:
            raise
        except Exception as exc:
            raise DocumentParseError("invalid_pdf") from exc
    elif content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        try:
            with ZipFile(BytesIO(content)) as archive:
                entries = archive.infolist()
                if len(entries) > 1000 or sum(entry.file_size for entry in entries) > 20_000_000:
                    raise DocumentParseError("document_too_large")
                entry = archive.getinfo("word/document.xml")
                if entry.file_size > 2_000_000:
                    raise DocumentParseError("document_too_large")
                xml = archive.read(entry)
            if b"<!DOCTYPE" in xml or b"<!ENTITY" in xml or b"\x00" in xml:
                raise DocumentParseError("unsafe_document")
            root = ElementTree.fromstring(xml)
            text = "\n".join("".join(node.itertext()) for node in root.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"))
        except DocumentParseError:
            raise
        except (BadZipFile, KeyError, ElementTree.ParseError, RuntimeError, OSError) as exc:
            raise DocumentParseError("invalid_docx") from exc
    else:
        raise DocumentParseError("unsupported_document_type")
    if not text.strip():
        raise DocumentParseError("no_extractable_text_ocr_required")
    if len(text) > 200000:
        raise DocumentParseError("extracted_text_too_large")
    return text.replace("\x00", "").strip()
