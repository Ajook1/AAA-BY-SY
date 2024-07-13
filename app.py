import os
from flask import Flask, request, render_template, send_file
from werkzeug.utils import secure_filename
from pdfminer.high_level import extract_text
from fpdf import FPDF
from transformers import pipeline

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize summarization pipeline
summarizer = pipeline('summarization', model='facebook/bart-large-cnn')

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/summarize', methods=['POST'])
def summarize():
    pdf_files = [request.files[f'pdf{i}'] for i in range(1, 5)]

    pdf_paths = []
    for pdf in pdf_files:
        if pdf.filename == '':
            return "Please upload all PDF files.", 400

        filename = secure_filename(pdf.filename)
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        pdf.save(pdf_path)

        try:
            extracted_text = extract_text(pdf_path)
            if extracted_text:
                summary_text = summarize_text(extracted_text)
                pdf_paths.append((filename, summary_text))
            else:
                return f"Failed to extract text from {filename}.", 500
        except Exception as e:
            return f"Error processing {filename}: {str(e)}", 500

    if pdf_paths:
        combined_pdf_path = create_combined_summary_pdf(pdf_paths)
        return send_file(combined_pdf_path, as_attachment=True, download_name='combined_summaries.pdf')
    else:
        return "No summaries generated.", 500

def summarize_text(text):
    max_chunk_size = 1000
    text_chunks = [text[i:i + max_chunk_size] for i in range(0, len(text), max_chunk_size)]
    summarized_text = ""

    for chunk in text_chunks:
        summarized = summarizer(chunk, max_length=150, min_length=30, do_sample=False)
        summarized_text += summarized[0]['summary_text'] + " "

    return summarized_text.strip()

def create_combined_summary_pdf(pdf_summaries):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Load the logo
    logo_path = 'static\mgmLogo.png'  
    logo_width = 30
    logo_height = 30 

   
    college_name = "MGM's College Of Engineering"
    
    # Width for the college name
    pdf.set_font("Times", size=18, style='B')
    title_width = pdf.get_string_width(college_name)
    
    
    total_width = logo_width + 10 + title_width
    
    
    start_x = (210 - total_width) / 2  

    
    pdf.image(logo_path, x=start_x, y=10, w=logo_width, h=logo_height)
    
    # Adjust position for college name to be in line with logo
    pdf.set_xy(start_x + logo_width + 10, 10 + (logo_height / 4))
    pdf.cell(0, 10, txt=college_name, ln=False, align='L')
    
    # Move to the next line after the logo and title, with some additional space
    pdf.ln(logo_height + 10)

    for index, (filename, summary_text) in enumerate(pdf_summaries):
        pdf.set_font("Arial", size=16, style='B')
        
        pdf.cell(200, 10, txt=f"Summary of {filename}", ln=True, align='C')
        pdf.set_line_width(0.5)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(10)

        pdf.set_font("Arial", size=12)
        summary_text = summary_text.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 10, summary_text)
        pdf.ln(10)

    combined_pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], 'combined_summaries.pdf')
    pdf.output(combined_pdf_path)

    return combined_pdf_path


if __name__ == '__main__':
    app.run(debug=True, port=5000)
