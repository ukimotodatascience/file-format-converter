import io
import json
from pathlib import Path
from typing import Any, cast

import pandas as pd
import streamlit as st
import pymupdf
from PIL import Image


TABULAR_TARGETS = {
    "csv": ["json", "xlsx", "tsv"],
    "tsv": ["csv", "json", "xlsx"],
    "json": ["csv", "tsv", "xlsx"],
    "xlsx": ["csv", "tsv", "json"],
}

TEXT_TARGETS = {
    "txt": ["md"],
    "md": ["txt"],
}

IMAGE_TARGETS = {
    "png": ["jpg", "webp", "bmp"],
    "jpg": ["png", "webp", "bmp"],
    "jpeg": ["png", "webp", "bmp"],
    "webp": ["png", "jpg", "bmp"],
    "bmp": ["png", "jpg", "webp"],
}

PDF_TARGETS = {
    "pdf": ["png", "jpg", "webp", "bmp"],
}


def detect_extension(filename: str) -> str:
    return Path(filename).suffix.lower().lstrip(".")


def get_candidates(ext: str) -> list[str]:
    if ext in TABULAR_TARGETS:
        return TABULAR_TARGETS[ext]
    if ext in TEXT_TARGETS:
        return TEXT_TARGETS[ext]
    if ext in IMAGE_TARGETS:
        return IMAGE_TARGETS[ext]
    if ext in PDF_TARGETS:
        return PDF_TARGETS[ext]
    return []


def load_tabular(source_ext: str, raw: bytes) -> pd.DataFrame:
    bio = io.BytesIO(raw)
    if source_ext == "csv":
        return pd.read_csv(bio)
    if source_ext == "tsv":
        return pd.read_csv(bio, sep="\t")
    if source_ext == "json":
        data = json.loads(raw.decode("utf-8"))
        if isinstance(data, dict):
            data = [data]
        return pd.json_normalize(data)
    if source_ext == "xlsx":
        return pd.read_excel(bio)
    raise ValueError("未対応の表形式ファイルです")


def convert_tabular(source_ext: str, target_ext: str, raw: bytes) -> tuple[bytes, str]:
    df = load_tabular(source_ext, raw)

    if target_ext == "csv":
        text = df.to_csv(index=False)
        return text.encode("utf-8"), "text/csv"
    if target_ext == "tsv":
        text = df.to_csv(index=False, sep="\t")
        return text.encode("utf-8"), "text/tab-separated-values"
    if target_ext == "json":
        text = df.to_json(orient="records", force_ascii=False, indent=2)
        if text is None:
            raise ValueError("JSONへの変換結果が空でした")
        return text.encode("utf-8"), "application/json"
    if target_ext == "xlsx":
        out = io.BytesIO()
        with pd.ExcelWriter(cast(Any, out), engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Sheet1")
        return (
            out.getvalue(),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    raise ValueError("未対応の変換先です")


def convert_text(source_ext: str, target_ext: str, raw: bytes) -> tuple[bytes, str]:
    text = raw.decode("utf-8")

    if source_ext == "txt" and target_ext == "md":
        return text.encode("utf-8"), "text/markdown"
    if source_ext == "md" and target_ext == "txt":
        return text.encode("utf-8"), "text/plain"

    raise ValueError("未対応のテキスト変換です")


def convert_image(source_ext: str, target_ext: str, raw: bytes) -> tuple[bytes, str]:
    img = Image.open(io.BytesIO(raw))
    out = io.BytesIO()

    pil_fmt = "JPEG" if target_ext == "jpg" else target_ext.upper()
    if pil_fmt == "JPEG" and img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    img.save(out, format=pil_fmt)

    mime_map = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "webp": "image/webp",
        "bmp": "image/bmp",
    }
    return out.getvalue(), mime_map[target_ext]


def get_pdf_page_count(raw: bytes) -> int:
    with pymupdf.open(stream=raw, filetype="pdf") as doc:
        return doc.page_count


def convert_pdf(
    target_ext: str,
    raw: bytes,
    page_number: int = 1,
    dpi: int = 200,
) -> tuple[bytes, str]:
    with pymupdf.open(stream=raw, filetype="pdf") as doc:
        if doc.page_count == 0:
            raise ValueError("PDFにページがありません")

        page_index = page_number - 1
        if page_index < 0 or page_index >= doc.page_count:
            raise ValueError("指定されたページ番号が範囲外です")

        page = doc.load_page(page_index)
        scale = dpi / 72.0
        matrix = pymupdf.Matrix(scale, scale)
        pix = page.get_pixmap(matrix=matrix, alpha=False)

    image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    out = io.BytesIO()

    pil_fmt = "JPEG" if target_ext == "jpg" else target_ext.upper()
    image.save(out, format=pil_fmt)

    mime_map = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "webp": "image/webp",
        "bmp": "image/bmp",
    }
    return out.getvalue(), mime_map[target_ext]


def convert_file(
    source_ext: str,
    target_ext: str,
    raw: bytes,
    page_number: int = 1,
    dpi: int = 200,
) -> tuple[bytes, str]:
    if source_ext in TABULAR_TARGETS:
        return convert_tabular(source_ext, target_ext, raw)
    if source_ext in TEXT_TARGETS:
        return convert_text(source_ext, target_ext, raw)
    if source_ext in IMAGE_TARGETS:
        return convert_image(source_ext, target_ext, raw)
    if source_ext in PDF_TARGETS:
        return convert_pdf(
            target_ext=target_ext, raw=raw, page_number=page_number, dpi=dpi
        )
    raise ValueError("この形式の変換は現在未対応です")


st.set_page_config(page_title="ファイル形式変換アプリ", page_icon="🔄")
st.title("🔄 ファイル形式変換アプリ")
st.write(
    "アップロードしたファイルの形式を自動判定し、変換先フォーマットを選んでダウンロードできます。"
)

uploaded_file = st.file_uploader("ファイルをアップロード", type=None)

if uploaded_file:
    source_ext = detect_extension(uploaded_file.name)
    candidates = get_candidates(source_ext)

    st.info(f"検出された形式: **.{source_ext or '不明'}**")

    if not source_ext:
        st.error(
            "拡張子が取得できませんでした。拡張子付きのファイル名で再アップロードしてください。"
        )
    elif not candidates:
        st.warning("このファイル形式はまだ対応していません。")
    else:
        target_ext = st.selectbox("変換先フォーマットを選択", candidates)
        page_number = 1
        dpi = 200

        if source_ext == "pdf":
            raw_for_pdf = uploaded_file.getvalue()
            page_count = get_pdf_page_count(raw_for_pdf)
            st.caption(f"PDFページ数: {page_count}")
            page_number = st.number_input(
                "変換するページ番号",
                min_value=1,
                max_value=page_count,
                value=1,
                step=1,
            )
            dpi = st.slider("画像解像度 (DPI)", min_value=72, max_value=300, value=200)

        if st.button("変換する", type="primary"):
            try:
                raw = uploaded_file.getvalue()
                converted, mime = convert_file(
                    source_ext,
                    target_ext,
                    raw,
                    page_number=int(page_number),
                    dpi=int(dpi),
                )
                output_name = f"{Path(uploaded_file.name).stem}.{target_ext}"

                st.success("変換が完了しました。")
                st.download_button(
                    label="変換済みファイルをダウンロード",
                    data=converted,
                    file_name=output_name,
                    mime=mime,
                )
            except Exception as e:
                st.error(f"変換中にエラーが発生しました: {e}")
