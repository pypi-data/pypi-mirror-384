# -*- coding: utf-8 -*-
import os
import base64
import re
import json
from typing import List, Union, Dict, Tuple, Optional
import io
import warnings

# Ignorer les avertissements non pertinents
warnings.filterwarnings("ignore", category=DeprecationWarning) 

# --- Core Libraries ---
import fitz  # PyMuPDF
import cv2   # OpenCV for image processing
import numpy as np
from PIL import Image

# --- Advanced Feature Libraries ---
try:
    from unstructured.partition.image import partition_image
    from unstructured.documents.elements import Table, Title, ListItem, Text
    UNSTRUCTURED_AVAILABLE = True
except ImportError:
    UNSTRUCTURED_AVAILABLE = False

try:
    from markdownify import markdownify as md
    MARKDOWNIFY_AVAILABLE = True
except ImportError:
    MARKDOWNIFY_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False


class RostaingOCR:
    """
    Classe d'extraction de contenu sémantique. Elle identifie la structure
    (titres, paragraphes, listes, tableaux) et la formate en Markdown enrichi
    (avec JSON pour les tableaux), offrant une sortie optimale pour les LLMs et RAG.
    """
    SUPPORTED_IMAGE_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff']
    
    def __init__(self,
                 input_path_or_paths: Union[str, List[str]],
                 output_basename: str = "output",
                 print_to_console: bool = False,
                 save_images_externally: bool = True,
                 image_dpi: int = 300,
                 languages: List[str] = ['fra', 'eng']):
        if not all([UNSTRUCTURED_AVAILABLE, MARKDOWNIFY_AVAILABLE, BS4_AVAILABLE]):
            raise ImportError("Missing required libraries : unstructured, markdownify, beautifulsoup4.")
        if isinstance(input_path_or_paths, str):
            self.input_paths = [input_path_or_paths]
        else:
            self.input_paths = input_path_or_paths
        self.output_basename = output_basename
        self.output_md_path = f"{self.output_basename}.md"
        self.output_txt_path = f"{self.output_basename}.txt"
        self.save_images_externally = save_images_externally
        self.image_output_dir = f"{self.output_basename}_assets"
        self.image_dpi = image_dpi
        self.languages = languages
        self.print_to_console = print_to_console
        self.results: Dict[str, str] = {}
        self._run_extraction()

    def _run_extraction(self):
        print(f"\nStarting RostaingOCR Semantic Extraction...")
        if self.save_images_externally and not os.path.exists(self.image_output_dir):
            os.makedirs(self.image_output_dir)
        for i, file_path in enumerate(self.input_paths):
            try:
                if not os.path.exists(file_path): raise FileNotFoundError(f"File not found: {file_path}")
                print(f"\n--- Processing {os.path.basename(file_path)} ({i+1}/{len(self.input_paths)}) ---")
                extracted_content = self._extract_content_from_single_file(file_path)
                if extracted_content:
                    self.results[file_path] = f"# Document: {os.path.basename(file_path)}\n\n{extracted_content}"
                    print(f"--- SUCCESS for '{os.path.basename(file_path)}' ---")
                    if self.print_to_console: self._print_result_to_console(os.path.basename(file_path), extracted_content)
                else:
                    self.results[file_path] = ""
                    print(f"--- FAILURE (no content found) for '{os.path.basename(file_path)}' ---")
            except Exception as e:
                import traceback
                error_msg = f"[FATAL ERROR during processing of '{file_path}': {e}]"
                print(error_msg)
                traceback.print_exc()
                self.results[file_path] = error_msg
        
        final_output = [content for content in self.results.values() if content]
        if final_output: self._save_outputs("\n\n===\n\n".join(final_output))
        print("\nProcessing complete.")
    
    def _get_image_markdown(self, image_bytes: bytes, alt_text: str, image_format: str, image_filename: str) -> str:
        if self.save_images_externally:
            image_path = os.path.join(self.image_output_dir, image_filename)
            with open(image_path, "wb") as f: f.write(image_bytes)
            relative_path = os.path.join(os.path.basename(self.image_output_dir), image_filename).replace("\\", "/")
            return f"![{alt_text}]({relative_path})"
        else:
            return f"![{alt_text}](data:image/{image_format};base64,{base64.b64encode(image_bytes).decode('utf-8')})"

    def _extract_urls(self, text: str) -> List[str]:
        return re.findall(r'https?://\S+|www\.\S+', text)

    def _detect_signatures(self, image: Image.Image, pnum: int, doc_name: str) -> str:
        img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        img_gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(img_gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        md_output = []
        sig_count = 0
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            area = w * h
            if 5000 < area < 200000 and 1.5 < w/h < 5.0:
                roi = thresh[y:y+h, x:x+w]
                if float(area) > 0 and 0.1 < cv2.countNonZero(roi) / float(area) < 0.5:
                    if not md_output: md_output.append("\n### Detected Signatures (Experimental)\n")
                    sig_count += 1
                    sig_crop = img_cv[y:y+h, x:x+w]
                    _, buffer = cv2.imencode('.png', sig_crop)
                    filename = f"{doc_name}_p{pnum}_sig_{sig_count}.png"
                    md_output.append(self._get_image_markdown(buffer.tobytes(), f"Signature {sig_count}", "png", filename))
        if sig_count > 0: print(f"      - Found {sig_count} potential signature(s) on page {pnum}.")
        return "\n".join(md_output)
        
    def _is_numeric_like(self, s: str) -> bool:
        s = s.strip()
        if not s: return False
        return bool(re.search(r'[\d€$%,]', s))

    def _parse_html_table(self, html_content: str) -> Dict:
        soup = BeautifulSoup(html_content, 'html.parser')
        headers = []
        body_rows = []
        
        all_rows = []
        for row_tag in soup.find_all('tr'):
            cols = [td.get_text(strip=True) for td in row_tag.find_all(['td', 'th'])]
            if any(c.strip() for c in cols):
                all_rows.append(cols)
        
        if not all_rows: return {'headers': [], 'rows': [], 'rows_as_dicts': []}

        if soup.find('th'):
            first_row_tags = soup.find('tr').find_all(['td', 'th'])
            if all(tag.name == 'th' for tag in first_row_tags):
                headers = all_rows.pop(0)
                body_rows = all_rows
                print(f"      - Headers found via <th> tags: {headers}")

        if not headers and len(all_rows) > 1:
            first_row = all_rows[0]
            second_row = all_rows[1]
            first_row_is_text = [not self._is_numeric_like(cell) for cell in first_row]
            second_row_is_numeric = [self._is_numeric_like(cell) for cell in second_row]
            
            if sum(first_row_is_text) > len(first_row) / 2 and sum(second_row_is_numeric) > 0:
                headers = all_rows.pop(0)
                body_rows = all_rows
                print(f"      - Headers inferred by data-type analysis: {headers}")
        
        if not body_rows: body_rows = all_rows

        json_data = []
        if headers:
            headers = [h if h else f"col_{i+1}" for i, h in enumerate(headers)]
            for row in body_rows:
                padded_row = row + [''] * (len(headers) - len(row))
                json_data.append(dict(zip(headers, padded_row[:len(headers)])))
        else: 
            json_data = body_rows

        return {'headers': headers, 'rows': body_rows, 'rows_as_dicts': json_data}

    def _process_image_elements(self, elements: List) -> Tuple[str, str]:
        md_parts = []
        text_parts = []
        for el in elements:
            if isinstance(el, Title):
                md_parts.append(f"### {el.text}\n")
            elif isinstance(el, ListItem):
                md_parts.append(f"- {el.text}") 
            elif isinstance(el, Table):
                # --- CORRECTION ICI ---
                html_content = el.metadata.text_as_html
                if html_content:  # On vérifie si le contenu HTML existe avant de l'analyser
                    table_data = self._parse_html_table(html_content)
                    if table_data['rows_as_dicts']:
                        json_repr = json.dumps(table_data['rows_as_dicts'], indent=2, ensure_ascii=False)
                        md_parts.append(f"\n#### Extracted Table (JSON Format)\n```json\n{json_repr}\n```\n")
                        text_parts.append(json_repr)

                    md_parts.append("#### Extracted Table (Markdown Format)\n")
                    if table_data['headers']:
                        md_parts.append("| " + " | ".join(table_data['headers']) + " |")
                        md_parts.append("| " + " | ".join(['---'] * len(table_data['headers'])) + " |")
                        for row in table_data['rows']:
                            md_parts.append("| " + " | ".join(row) + " |")
                    else: 
                        md_parts.append(md(html_content, heading_style="ATX"))
                    md_parts.append("\n")
                else:
                    # Solution de repli : utiliser le texte brut si le HTML n'est pas disponible
                    print("      - Warning: Table element found without HTML content. Using plain text fallback.")
                    if el.text:
                        md_parts.append(f"\n**[Unstructured Table Content]**\n{el.text}\n")
                        text_parts.append(el.text)

            else: # NarrativeText, etc.
                md_parts.append(f"{el.text}\n")
            
            text_parts.append(el.text)
        
        return "\n".join(md_parts), "\n".join(text_parts)

    def _extract_content_from_single_file(self, input_path: str) -> str:
        file_basename, file_extension = os.path.splitext(os.path.basename(input_path))
        file_extension = file_extension.lower()
        
        page_processor = lambda pil_image, p_num: self._process_page_image(pil_image, p_num, file_basename)

        if file_extension == '.pdf':
            all_pages_content = []
            doc = fitz.open(input_path)
            for i, page in enumerate(doc):
                print(f"    - Processing page {i + 1}/{len(doc)}...")
                pix = page.get_pixmap(dpi=self.image_dpi)
                pil_image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                all_pages_content.append(page_processor(pil_image, i + 1))
            return "\n\n---\n\n".join(all_pages_content)
            
        elif file_extension in self.SUPPORTED_IMAGE_EXTENSIONS:
            pil_image = Image.open(input_path)
            return page_processor(pil_image, 1)
        else:
            return f"[ERROR: Unsupported file type: {file_extension}]"

    def _process_page_image(self, pil_image: Image.Image, p_num: int, doc_name: str) -> str:
        page_md = [f"## Page {p_num}\n"]
        
        with io.BytesIO() as img_buffer:
            pil_image.save(img_buffer, format="PNG")
            img_buffer.seek(0)
            print(f"      - Analyzing page layout with 'unstructured' (Languages: {self.languages})...")
            elements = partition_image(file=img_buffer, strategy="hi_res", languages=self.languages)
        
        md_content, text_content = self._process_image_elements(elements)
        if md_content:
            page_md.append("### Extracted Content\n" + md_content)
        
        urls = self._extract_urls(text_content)
        if urls:
            page_md.extend(["\n### Detected URLs\n"] + [f"- <{url}>" for url in urls])
        
        page_md.append(self._detect_signatures(pil_image, p_num, doc_name))
        return "\n".join(page_md)

    def _save_outputs(self, final_content: str):
        print(f"\n[Saving the results]...")
        txt_content = re.sub(r"!\[.*?\]\(.*?\)|```json.*?```", "[Data Block]", final_content, flags=re.DOTALL)
        txt_content = re.sub(r'#+\s?', '', txt_content)
        for path, content in [(self.output_md_path, final_content), (self.output_txt_path, txt_content)]:
            try:
                with open(path, 'w', encoding='utf-8') as f: f.write(content)
                print(f"  - Success: output saved to '{path}'.")
            except IOError as e: print(f"  - ERROR: Unable to write to '{path}'. Error: {e}")

    def _print_result_to_console(self, filename: str, content: str):
        print("\n" + "="*20 + f" CONTENT OF {filename} " + "="*20)
        print(content)
        print("=" * (44 + len(filename)) + "\n")

    def __str__(self) -> str:
        summary_lines = [f"--- Summary of RostaingOCR ---"]
        if not self.results: return "\n".join(summary_lines + ["No files were processed."])
        summary_lines.append(f"Output files: '{self.output_txt_path}', '{self.output_md_path}'")
        if self.save_images_externally: summary_lines.append(f"Image assets saved in: '{self.image_output_dir}/'")
        for file_path, content in self.results.items():
            status = "✅ Success" if content and not content.startswith("[FATAL ERROR") else "❌ Failure"
            summary_lines.append(f"\n  - File processed: {os.path.basename(file_path)}")
            summary_lines.append(f"    Status: {status}")
        return "\n".join(summary_lines)