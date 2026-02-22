# ファイル形式変換アプリ

Streamlit で動作する、シンプルなファイル形式変換アプリです。  
アップロードしたファイルの拡張子を自動判定し、対応する変換先フォーマットを選んでダウンロードできます。

## 主な機能

- 表形式ファイルの相互変換（CSV / TSV / JSON / XLSX）
- テキストファイルの変換（TXT ⇄ MD）
- 画像ファイルの変換（PNG / JPG / WEBP / BMP）
- PDF を画像に変換
  - 1ページのみ変換
  - 全ページ変換（ZIPで一括ダウンロード）
  - DPI（解像度）指定

## 対応フォーマット

### 表形式

- 入力: `csv`, `tsv`, `json`, `xlsx`
- 出力: 上記4形式の相互変換

### テキスト

- 入力: `txt`, `md`
- 出力: `txt` または `md`

### 画像

- 入力: `png`, `jpg`, `jpeg`, `webp`, `bmp`
- 出力: `png`, `jpg`, `webp`, `bmp`

### PDF

- 入力: `pdf`
- 出力: `png`, `jpg`, `webp`, `bmp`

## セットアップ

### 1. リポジトリを取得

```bash
git clone https://github.com/ukimotodatascience/file-format-converter.git
cd file-format-converter
```

### 2. 依存ライブラリをインストール

```bash
pip install -r requirements.txt
```

## 実行方法

```bash
streamlit run app.py
```

ブラウザが自動で開かない場合は、ターミナルに表示されるURL（通常 `http://localhost:8501`）へアクセスしてください。

## 使い方

1. ファイルをアップロード
2. 変換先フォーマットを選択
3. （PDFの場合）ページ指定 or 全ページ変換、DPI設定
4. **変換する** をクリック
5. **変換済みファイルをダウンロード** から保存

## 注意事項

- 入力ファイルの内容によっては、変換時にエラーになることがあります。
- PDF は暗号化・破損・特殊構造のファイルで読み取りに失敗する場合があります。
- 文字コードは UTF-8 を前提としています。

## 使用ライブラリ

- [Streamlit](https://streamlit.io/)
- [pandas](https://pandas.pydata.org/)
- [openpyxl](https://openpyxl.readthedocs.io/)
- [Pillow](https://python-pillow.org/)
- [PyMuPDF](https://pymupdf.readthedocs.io/)
