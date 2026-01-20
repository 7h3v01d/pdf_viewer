import json
import os
import fitz
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import QRectF, Qt, QPoint

def load_annotations(pdf_document, pdf_file_path):
    annotations = {}
    if pdf_document:
        try:
            for page_num in range(pdf_document.page_count):
                page = pdf_document.load_page(page_num)
                for annot in page.annots():
                    if annot.type[0] == 8:
                        pos = annot.rect.top_left
                        text = annot.info["content"]
                        if page_num not in annotations:
                            annotations[page_num] = []
                        annotations[page_num].append((pos.x, pos.y, text))
        except Exception as e:
            if hasattr(pdf_document, 'status_bar'):
                pdf_document.status_bar.showMessage(f"Error loading PDF annotations: {str(e)}")
    annotation_file = pdf_file_path + ".annotations.json"
    if os.path.exists(annotation_file):
        try:
            with open(annotation_file, "r") as f:
                json_annotations = json.load(f)
                json_annotations = {int(k): v for k, v in json_annotations.items()}
                for page_num in json_annotations:
                    if page_num not in annotations:
                        annotations[page_num] = []
                    for x, y, text in json_annotations[page_num]:
                        duplicate = False
                        for existing_x, existing_y, existing_text in annotations[page_num]:
                            if abs(existing_x - x) < 1 and abs(existing_y - y) < 1 and existing_text == text:
                                duplicate = True
                                break
                        if not duplicate:
                            annotations[page_num].append((x, y, text))
        except Exception as e:
            if hasattr(pdf_document, 'status_bar'):
                pdf_document.status_bar.showMessage(f"Error loading JSON annotations: {str(e)}")
    return annotations

def save_annotations(pdf_reader):
    if pdf_reader.pdf_file_path:
        annotation_file = pdf_reader.pdf_file_path + ".annotations.json"
        try:
            with open(annotation_file, "w") as f:
                json.dump(pdf_reader.annotations, f)
            pdf_reader.status_bar.showMessage("Annotations saved to JSON")
        except Exception as e:
            pdf_reader.status_bar.showMessage(f"Error saving JSON annotations: {str(e)}")

def search_text(pdf_reader):
    search_term = pdf_reader.search_input.text().strip()
    if not search_term:
        pdf_reader.status_bar.showMessage("Enter a search term")
        return
    pdf_reader.search_results = []
    pdf_reader.current_search_index = -1
    try:
        for page_num in range(pdf_reader.total_pages):
            page = pdf_reader.pdf_document.load_page(page_num)
            rects = page.search_for(search_term)
            if rects:
                pdf_reader.search_results.append({"page": page_num, "rects": rects})
        if pdf_reader.search_results:
            pdf_reader.current_search_index = 0
            pdf_reader.current_page = pdf_reader.search_results[0]["page"]
            pdf_reader.annotation_mode = False
            pdf_reader.toggle_annotation_mode(force_off=True) # Ensure cursor reset
            pdf_reader.update_view() # CHANGED FROM update_page()
            
            # Use view_mode to conditionally enable/disable prev/next buttons
            is_single = (pdf_reader.view_mode == 0)
            pdf_reader.prev_button.setEnabled(pdf_reader.current_page > 0 and is_single)
            pdf_reader.next_button.setEnabled(pdf_reader.current_page < pdf_reader.total_pages - 1 and is_single)
            pdf_reader.move_up_button.setEnabled(pdf_reader.current_page > 0)
            pdf_reader.move_down_button.setEnabled(pdf_reader.current_page < pdf_reader.total_pages - 1)
            pdf_reader.thumbnail_list.setCurrentRow(pdf_reader.current_page)
            if pdf_reader.view_mode == 1:
                pdf_reader.scroll_to_page(pdf_reader.current_page)
                
            pdf_reader.next_search_button.setEnabled(len(pdf_reader.search_results) > 1)
            pdf_reader.prev_search_button.setEnabled(False)
            pdf_reader.status_bar.showMessage(f"Found {len(pdf_reader.search_results)} matches")
        else:
            pdf_reader.next_search_button.setEnabled(False)
            pdf_reader.prev_search_button.setEnabled(False)
            pdf_reader.status_bar.showMessage("No matches found")
    except Exception as e:
        pdf_reader.status_bar.showMessage(f"Search error: {str(e)}")

def next_search_result(pdf_reader):
    if pdf_reader.search_results and pdf_reader.current_search_index < len(pdf_reader.search_results) - 1:
        pdf_reader.current_search_index += 1
        pdf_reader.current_page = pdf_reader.search_results[pdf_reader.current_search_index]["page"]
        pdf_reader.annotation_mode = False
        pdf_reader.toggle_annotation_mode(force_off=True) # Ensure cursor reset
        pdf_reader.update_view() # CHANGED FROM update_page()
        
        is_single = (pdf_reader.view_mode == 0)
        pdf_reader.prev_button.setEnabled(pdf_reader.current_page > 0 and is_single)
        pdf_reader.next_button.setEnabled(pdf_reader.current_page < pdf_reader.total_pages - 1 and is_single)
        pdf_reader.move_up_button.setEnabled(pdf_reader.current_page > 0)
        pdf_reader.move_down_button.setEnabled(pdf_reader.current_page < pdf_reader.total_pages - 1)
        pdf_reader.thumbnail_list.setCurrentRow(pdf_reader.current_page)
        if pdf_reader.view_mode == 1:
            pdf_reader.scroll_to_page(pdf_reader.current_page)
            
        pdf_reader.next_search_button.setEnabled(pdf_reader.current_search_index < len(pdf_reader.search_results) - 1)
        pdf_reader.prev_search_button.setEnabled(pdf_reader.current_search_index > 0)

def prev_search_result(pdf_reader):
    if pdf_reader.search_results and pdf_reader.current_search_index > 0:
        pdf_reader.current_search_index -= 1
        pdf_reader.current_page = pdf_reader.search_results[pdf_reader.current_search_index]["page"]
        pdf_reader.annotation_mode = False
        pdf_reader.toggle_annotation_mode(force_off=True) # Ensure cursor reset
        pdf_reader.update_view() # CHANGED FROM update_page()
        
        is_single = (pdf_reader.view_mode == 0)
        pdf_reader.prev_button.setEnabled(pdf_reader.current_page > 0 and is_single)
        pdf_reader.next_button.setEnabled(pdf_reader.current_page < pdf_reader.total_pages - 1 and is_single)
        pdf_reader.move_up_button.setEnabled(pdf_reader.current_page > 0)
        pdf_reader.move_down_button.setEnabled(pdf_reader.current_page < pdf_reader.total_pages - 1)
        pdf_reader.thumbnail_list.setCurrentRow(pdf_reader.current_page)
        if pdf_reader.view_mode == 1:
            pdf_reader.scroll_to_page(pdf_reader.current_page)
            
        pdf_reader.next_search_button.setEnabled(pdf_reader.current_search_index < len(pdf_reader.search_results) - 1)
        pdf_reader.prev_search_button.setEnabled(pdf_reader.current_search_index > 0)

def add_page(pdf_reader):
    if not pdf_reader.pdf_document:
        pdf_reader.status_bar.showMessage("No PDF loaded")
        return
    try:
        pdf_reader.pdf_document.insert_page(pdf_reader.current_page + 1)
        pdf_reader.total_pages += 1
        new_annotations = {}
        for page_num in pdf_reader.annotations:
            if page_num <= pdf_reader.current_page:
                new_annotations[page_num] = pdf_reader.annotations[page_num]
            else:
                new_annotations[page_num + 1] = pdf_reader.annotations[page_num]
        pdf_reader.annotations = new_annotations
        new_search_results = []
        for result in pdf_reader.search_results:
            if result["page"] <= pdf_reader.current_page:
                new_search_results.append(result)
            else:
                new_search_results.append({"page": result["page"] + 1, "rects": result["rects"]})
        pdf_reader.search_results = new_search_results
        
        pdf_reader.load_pages() # NEW: Need to reload/recreate page widgets
        pdf_reader.update_view() # CHANGED FROM update_page()

        # Rebuild pages and form fields
        pdf_reader.pages = [pdf_reader.pdf_document.load_page(i) for i in range(pdf_reader.total_pages)]
        pdf_reader.form_fields = {i: list(p.widgets()) for i, p in enumerate(pdf_reader.pages)}
        
        pdf_reader.load_thumbnails()
        pdf_reader.load_toc()
        pdf_reader.page_label.setText(f" / {pdf_reader.total_pages}")
        
        is_single = (pdf_reader.view_mode == 0)
        pdf_reader.next_button.setEnabled(pdf_reader.current_page < pdf_reader.total_pages - 1 and is_single)
        pdf_reader.move_down_button.setEnabled(pdf_reader.current_page < pdf_reader.total_pages - 1)
        pdf_reader.move_up_button.setEnabled(pdf_reader.current_page > 0)
        pdf_reader.status_bar.showMessage("Blank page added")
    except Exception as e:
        pdf_reader.status_bar.showMessage(f"Error adding page: {str(e)}")

def remove_page(pdf_reader):
    if not pdf_reader.pdf_document or pdf_reader.total_pages <= 1:
        pdf_reader.status_bar.showMessage("Cannot remove page: No PDF loaded or only one page")
        return
    try:
        pdf_reader.pdf_document.delete_page(pdf_reader.current_page)
        pdf_reader.total_pages -= 1
        if pdf_reader.current_page >= pdf_reader.total_pages:
            pdf_reader.current_page = pdf_reader.total_pages - 1
        new_annotations = {}
        for page_num in pdf_reader.annotations:
            if page_num < pdf_reader.current_page:
                new_annotations[page_num] = pdf_reader.annotations[page_num]
            elif page_num > pdf_reader.current_page:
                new_annotations[page_num - 1] = pdf_reader.annotations[page_num]
        pdf_reader.annotations = new_annotations
        new_search_results = []
        for result in pdf_reader.search_results:
            if result["page"] < pdf_reader.current_page:
                new_search_results.append(result)
            elif result["page"] > pdf_reader.current_page:
                new_search_results.append({"page": result["page"] - 1, "rects": result["rects"]})
        pdf_reader.search_results = new_search_results
        
        pdf_reader.load_pages() # NEW: Need to reload/recreate page widgets
        pdf_reader.update_view() # CHANGED FROM update_page()

        # Rebuild pages and form fields
        pdf_reader.pages = [pdf_reader.pdf_document.load_page(i) for i in range(pdf_reader.total_pages)]
        pdf_reader.form_fields = {i: list(p.widgets()) for i, p in enumerate(pdf_reader.pages)}
        
        pdf_reader.load_thumbnails()
        pdf_reader.load_toc()
        pdf_reader.page_label.setText(f" / {pdf_reader.total_pages}")
        
        is_single = (pdf_reader.view_mode == 0)
        pdf_reader.prev_button.setEnabled(pdf_reader.current_page > 0 and is_single)
        pdf_reader.next_button.setEnabled(pdf_reader.current_page < pdf_reader.total_pages - 1 and is_single)
        pdf_reader.move_up_button.setEnabled(pdf_reader.current_page > 0)
        pdf_reader.move_down_button.setEnabled(pdf_reader.current_page < pdf_reader.total_pages - 1)
        pdf_reader.status_bar.showMessage("Page removed")
    except Exception as e:
        pdf_reader.status_bar.showMessage(f"Error removing page: {str(e)}")

def move_page_up(pdf_reader):
    if not pdf_reader.pdf_document or pdf_reader.current_page <= 0:
        pdf_reader.status_bar.showMessage("Cannot move page up")
        return
    try:
        pdf_reader.pdf_document.move_page(pdf_reader.current_page, pdf_reader.current_page - 1)
        pdf_reader.current_page -= 1
        new_annotations = {}
        for page_num in pdf_reader.annotations:
            if page_num == pdf_reader.current_page:
                new_annotations[page_num + 1] = pdf_reader.annotations[page_num]
            elif page_num == pdf_reader.current_page + 1:
                new_annotations[page_num - 1] = pdf_reader.annotations[page_num]
            else:
                new_annotations[page_num] = pdf_reader.annotations[page_num]
        pdf_reader.annotations = new_annotations
        new_search_results = []
        for result in pdf_reader.search_results:
            if result["page"] == pdf_reader.current_page:
                new_search_results.append({"page": result["page"] + 1, "rects": result["rects"]})
            elif result["page"] == pdf_reader.current_page + 1:
                new_search_results.append({"page": result["page"] - 1, "rects": result["rects"]})
            else:
                new_search_results.append(result)
        pdf_reader.search_results = new_search_results
        
        pdf_reader.load_pages() # NEW: Need to reload/recreate page widgets
        pdf_reader.update_view() # CHANGED FROM update_page()

        # Rebuild pages and form fields
        pdf_reader.pages = [pdf_reader.pdf_document.load_page(i) for i in range(pdf_reader.total_pages)]
        pdf_reader.form_fields = {i: list(p.widgets()) for i, p in enumerate(pdf_reader.pages)}
        
        pdf_reader.load_thumbnails()
        pdf_reader.load_toc()
        
        is_single = (pdf_reader.view_mode == 0)
        pdf_reader.prev_button.setEnabled(pdf_reader.current_page > 0 and is_single)
        pdf_reader.next_button.setEnabled(pdf_reader.current_page < pdf_reader.total_pages - 1 and is_single)
        pdf_reader.move_up_button.setEnabled(pdf_reader.current_page > 0)
        pdf_reader.move_down_button.setEnabled(pdf_reader.current_page < pdf_reader.total_pages - 1)
        pdf_reader.thumbnail_list.setCurrentRow(pdf_reader.current_page)
        pdf_reader.status_bar.showMessage("Page moved up")
    except Exception as e:
        pdf_reader.status_bar.showMessage(f"Error moving page: {str(e)}")

def move_page_down(pdf_reader):
    if not pdf_reader.pdf_document or pdf_reader.current_page >= pdf_reader.total_pages - 1:
        pdf_reader.status_bar.showMessage("Cannot move page down")
        return
    try:
        pdf_reader.pdf_document.move_page(pdf_reader.current_page, pdf_reader.current_page + 1)
        pdf_reader.current_page += 1
        new_annotations = {}
        for page_num in pdf_reader.annotations:
            if page_num == pdf_reader.current_page - 1:
                new_annotations[page_num + 1] = pdf_reader.annotations[page_num]
            elif page_num == pdf_reader.current_page:
                new_annotations[page_num - 1] = pdf_reader.annotations[page_num]
            else:
                new_annotations[page_num] = pdf_reader.annotations[page_num]
        pdf_reader.annotations = new_annotations
        new_search_results = []
        for result in pdf_reader.search_results:
            if result["page"] == pdf_reader.current_page - 1:
                new_search_results.append({"page": result["page"] + 1, "rects": result["rects"]})
            elif result["page"] == pdf_reader.current_page:
                new_search_results.append({"page": result["page"] - 1, "rects": result["rects"]})
            else:
                new_search_results.append(result)
        pdf_reader.search_results = new_search_results
        
        pdf_reader.load_pages() # NEW: Need to reload/recreate page widgets
        pdf_reader.update_view() # CHANGED FROM update_page()

        # Rebuild pages and form fields
        pdf_reader.pages = [pdf_reader.pdf_document.load_page(i) for i in range(pdf_reader.total_pages)]
        pdf_reader.form_fields = {i: list(p.widgets()) for i, p in enumerate(pdf_reader.pages)}
        
        pdf_reader.load_thumbnails()
        pdf_reader.load_toc()
        
        is_single = (pdf_reader.view_mode == 0)
        pdf_reader.prev_button.setEnabled(pdf_reader.current_page > 0 and is_single)
        pdf_reader.next_button.setEnabled(pdf_reader.current_page < pdf_reader.total_pages - 1 and is_single)
        pdf_reader.move_up_button.setEnabled(pdf_reader.current_page > 0)
        pdf_reader.move_down_button.setEnabled(pdf_reader.current_page < pdf_reader.total_pages - 1)
        pdf_reader.thumbnail_list.setCurrentRow(pdf_reader.current_page)
        pdf_reader.status_bar.showMessage(f"Page moved down to position {pdf_reader.current_page + 1}")
    except Exception as e:
        pdf_reader.status_bar.showMessage(f"Error moving page: {str(e)}")

def handle_thumbnail_reorder(pdf_reader, parent, start, end, destination, row):
    if not pdf_reader.pdf_document:
        pdf_reader.status_bar.showMessage("No PDF loaded")
        return
    try:
        pdf_reader.pdf_document.move_page(start, row)
        if pdf_reader.current_page == start:
            pdf_reader.current_page = row
        elif start < pdf_reader.current_page <= row:
            pdf_reader.current_page -= 1
        elif row <= pdf_reader.current_page < start:
            pdf_reader.current_page += 1
        new_annotations = {}
        for page_num in range(pdf_reader.total_pages):
            if page_num == start:
                new_annotations[row] = pdf_reader.annotations.get(page_num, [])
            elif start < page_num <= row:
                new_annotations[page_num - 1] = pdf_reader.annotations.get(page_num, [])
            elif row < page_num <= start:
                new_annotations[page_num + 1] = pdf_reader.annotations.get(page_num, [])
            else:
                new_annotations[page_num] = pdf_reader.annotations.get(page_num, [])
        pdf_reader.annotations = new_annotations
        new_search_results = []
        for result in pdf_reader.search_results:
            page_num = result["page"]
            if page_num == start:
                new_search_results.append({"page": row, "rects": result["rects"]})
            elif start < page_num <= row:
                new_search_results.append({"page": page_num - 1, "rects": result["rects"]})
            elif row < page_num <= start:
                new_search_results.append({"page": page_num + 1, "rects": result["rects"]})
            else:
                new_search_results.append(result)
        pdf_reader.search_results = new_search_results
        
        pdf_reader.load_pages() # NEW: Need to reload/recreate page widgets
        pdf_reader.update_view() # CHANGED FROM update_page()

        # Rebuild pages and form fields
        pdf_reader.pages = [pdf_reader.pdf_document.load_page(i) for i in range(pdf_reader.total_pages)]
        pdf_reader.form_fields = {i: list(p.widgets()) for i, p in enumerate(pdf_reader.pages)}
        
        pdf_reader.load_thumbnails()
        pdf_reader.load_toc()
        
        is_single = (pdf_reader.view_mode == 0)
        pdf_reader.prev_button.setEnabled(pdf_reader.current_page > 0 and is_single)
        pdf_reader.next_button.setEnabled(pdf_reader.current_page < pdf_reader.total_pages - 1 and is_single)
        pdf_reader.move_up_button.setEnabled(pdf_reader.current_page > 0)
        pdf_reader.move_down_button.setEnabled(pdf_reader.current_page < pdf_reader.total_pages - 1)
        pdf_reader.thumbnail_list.setCurrentRow(pdf_reader.current_page)
        pdf_reader.status_bar.showMessage(f"Page moved from position {start + 1} to {row + 1}")
    except Exception as e:
        pdf_reader.status_bar.showMessage(f"Error reordering page: {str(e)}")