from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
import os
import docx2txt
import pdfplumber
import pandas as pd
import re
from werkzeug.utils import secure_filename
import tempfile
import shutil
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'docx'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except:
        pass
    return text

def extract_text_from_docx(docx_path):
    try:
        return docx2txt.process(docx_path)
    except:
        return ""

def extract_email_phone(text):
    email = ""
    phone = ""
    
    # Improved email pattern - more flexible and case-insensitive
    email_patterns = [
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b',
        r'\b[\w\.-]+@[\w\.-]+\.\w+\b',
        r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'
    ]
    
    # Improved phone pattern - more flexible
    phone_patterns = [
        r'(\+?\d{1,3})?[\s\-]?\(?\d{3,5}\)?[\s\-]?\d{3,5}[\s\-]?\d{3,5}',
        r'\+?\d{1,3}[\s\-]?\d{3,5}[\s\-]?\d{3,5}[\s\-]?\d{3,5}',
        r'\(?\d{3,5}\)?[\s\-]?\d{3,5}[\s\-]?\d{3,5}',
        r'\d{10,15}'  # Simple 10-15 digit number
    ]
    
    # Try different email patterns
    for pattern in email_patterns:
        email_match = re.search(pattern, text)
        if email_match:
            email = email_match.group(0)
            break
    
    # Try different phone patterns
    for pattern in phone_patterns:
        phone_match = re.search(pattern, text)
        if phone_match:
            phone = phone_match.group(0)
            break
    
    return email, phone

def extract_degrees(text):
    # Use casefold for better case-insensitive matching
    text_casefold = text.casefold()
    
    # Define qualification mappings with more variations
    qualification_mappings = {
        'btech': [
            'btech', 'b.tech', 'b.e', 'bachelor of technology', 'bachelor of engineering',
            'bachelor of tech', 'bachelor of eng', 'bachelor of engg',
            'b.tech', 'b.e.', 'bachelor', 'bachelor degree', 'bachelor of technology',
            'bachelor of engineering', 'bachelor of tech', 'bachelor of eng'
        ],
        'mtech': [
            'mtech', 'm.tech', 'master of technology', 'master of engineering', 'm.e',
            'master of tech', 'master of eng', 'master degree', 'master of technology',
            'master of engineering', 'master of tech', 'master of eng', 'm.tech', 'm.e.'
        ],
        'bsc': [
            'bsc', 'b.sc', 'bachelor of science', 'bachelor of science',
            'bachelor of sci', 'bachelor of science', 'b.sc', 'bsc.'
        ],
        'msc': [
            'msc', 'm.sc', 'master of science', 'master of science',
            'master of sci', 'master of science', 'm.sc', 'msc.'
        ],
        'bcom': [
            'bcom', 'b.com', 'bachelor of commerce', 'bachelor of commerce',
            'bachelor of comm', 'bachelor of commerce', 'b.com', 'bcom.'
        ],
        'mcom': [
            'mcom', 'm.com', 'master of commerce', 'master of commerce',
            'master of comm', 'master of commerce', 'm.com', 'mcom.'
        ],
        'phd': [
            'phd', 'doctorate', 'doctor of philosophy', 'doctor of philosophy',
            'doctorate degree', 'ph.d', 'ph.d.', 'doctor of philosophy'
        ],
        'diploma': [
            'diploma', 'polytechnic', 'diploma degree', 'polytechnic diploma',
            'diploma in', 'polytechnic in'
        ],
        'bmech': [
            'bachelor in mechanical engineering', 'bachelor in mechanical engg', 'bmech', 'bme'],   
        'bchem': [
            'bachelor in chemical engineering', 'bachelor in chemical engg', 'bche', 'bchem' 
        ]
    }
    
    found_degrees = set()
    
    # Check for each qualification type
    for degree_type, patterns in qualification_mappings.items():
        for pattern in patterns:
            if pattern in text_casefold:
                found_degrees.add(degree_type)
                break
    
    return found_degrees

def estimate_experience(text):
    exp_years = 0
    patterns = [
        r'(\d+)\+?\s+years? of experience',
        r'(\d+)\s+years? experience',
        r'experience\s*[:\-]?\s*(\d+)\s+years',
        r'(\d+)\s+yrs?\s+experience',
        r'(\d+)\s+years?\s+in\s+\w+',
        r'(\d+)\s+years?\s+of\s+work',
        r'(\d+)\s+years?\s+in\s+the\s+field',
        r'(\d+)\s+years?\s+professional',
        r'(\d+)\s+years?\s+industry',
        r'(\d+)\s+years?\s+development',
        r'(\d+)\s+years?\s+programming',
        r'(\d+)\s+years?\s+software',
        r'(\d+)\s+years?\s+it',
        r'(\d+)\s+years?\s+technology',
        r'\b(fresher|intern|trainee|entry level|no experience|0\s+years)\b'
    ]
    text_casefold = text.casefold()
    
    # First check for fresher/intern keywords
    fresher_keywords = ['fresher', 'intern', 'trainee', 'entry level', 'no experience', '0 years']
    if any(keyword in text_casefold for keyword in fresher_keywords):
        return 0
    
    # Then check for experience patterns
    for pattern in patterns[:-1]:  # Exclude the fresher pattern
        matches = re.findall(pattern, text_casefold)
        for match in matches:
            if match.isdigit():
                exp_years = max(exp_years, int(match))
    
    return exp_years

def extract_section(text, keywords, max_lines=5):
    sentences = re.split(r'\.\s|\n', text)
    lines = [s.strip() for s in sentences if any(k.casefold() in s.casefold() for k in keywords)]
    return " | ".join(lines[:max_lines])

def extract_name(text):
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    for line in lines[:5]:
        if len(line.split()) <= 5 and not any(w in line.casefold() for w in ['email', 'phone', 'curriculum', 'resume', '@']):
            return line
    return ""

def normalize_text(text):
    """Normalize text for case-insensitive processing"""
    return text.casefold()

def process_resumes(folder_path, required_skills, min_exp, min_qualifications, choice="1"):
    resume_scores = []
    total_resumes = 0
    matched_resumes = 0
    rejected_resumes = 0

    for file in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file)

        if file.casefold().endswith('.pdf'):
            text = extract_text_from_pdf(file_path)
        elif file.casefold().endswith('.docx'):
            text = extract_text_from_docx(file_path)
        else:
            continue

        total_resumes += 1
        text_normalized = normalize_text(text)

        name = extract_name(text)
        email, phone = extract_email_phone(text)
        experience_summary = extract_section(text, ['experience', 'worked', 'company', 'job', 'project'])
        education_summary = extract_section(text, ['secondary', 'phd', 'btech', 'bachelor', 'diploma', 'mtech'])
        internship_summary = extract_section(text, ['internship', 'fresher', 'trainee'])
        exp_years = estimate_experience(text)

        # Use case-insensitive skill matching
        matched_skills = [skill for skill in required_skills if skill.casefold() in text_normalized]
        degrees_in_resume = extract_degrees(text)
        
        # Use casefold for case-insensitive qualification matching with hierarchy
        has_min_qual = False
        
        # Define qualification hierarchy (lower to higher - reverse logic)
        qualification_hierarchy = {
            'diploma': ['diploma', 'btech', 'bsc', 'bcom', 'mtech', 'msc', 'mcom', 'phd'],
            'btech': ['btech', 'mtech', 'msc', 'phd'],
            'bmech': ['bmech', 'mmech', 'phd'],
            'bchem': ['bchem', 'mchem', 'phd'],
            'bsc': ['bsc', 'msc', 'phd'],
            'bcom': ['bcom', 'mcom', 'phd'],
            'mtech': ['mtech', 'phd'],
            'msc': ['msc', 'phd'],
            'mcom': ['mcom', 'phd'],
            'phd': ['phd']
        }
        
        for required_qual in min_qualifications:
            # Get acceptable qualifications for this requirement
            acceptable_quals = qualification_hierarchy.get(required_qual.casefold(), [required_qual.casefold()])
            
            for degree in degrees_in_resume:
                if degree.casefold() in acceptable_quals:
                    has_min_qual = True
                    break
            if has_min_qual:
                break

        # NEW LOGIC: Check only the selected requirement
        is_accepted = False
        acceptance_reasons = []
        rejection_reasons = []
        
        if choice == "1":  # Skills only
            if required_skills:
                if matched_skills:
                    is_accepted = True
                    acceptance_reasons.append(f"Skills MATCH: {matched_skills}")
                else:
                    rejection_reasons.append("Skills NO MATCH")
            else:
                is_accepted = True
                acceptance_reasons.append("No skills requirement specified")
                
        elif choice == "2":  # Experience only
            if min_exp > 0:
                if exp_years >= min_exp:
                    is_accepted = True
                    acceptance_reasons.append(f"Experience MATCH: {exp_years} years >= {min_exp} years")
                else:
                    rejection_reasons.append(f"Experience NO MATCH: {exp_years} years < {min_exp} years")
            else:
                is_accepted = True
                acceptance_reasons.append("No experience requirement specified")
                
        elif choice == "3":  # Qualification only
            if min_qualifications:
                if has_min_qual:
                    is_accepted = True
                    acceptance_reasons.append(f"Qualification MATCH: {list(degrees_in_resume)}")
                else:
                    rejection_reasons.append(f"Qualification NO MATCH: {degrees_in_resume} vs required {min_qualifications}")
            else:
                is_accepted = True
                acceptance_reasons.append("No qualification requirement specified")
                
        elif choice == "4":  # ALL criteria (AND logic)
            skills_met = False
            experience_met = False
            qualification_met = False
            
            # Check skills requirement
            if required_skills:
                if matched_skills:
                    skills_met = True
                    acceptance_reasons.append(f"Skills MATCH: {matched_skills}")
                else:
                    rejection_reasons.append("Skills NO MATCH")
            else:
                skills_met = True
            
            # Check experience requirement
            if min_exp > 0:
                if exp_years >= min_exp:
                    experience_met = True
                    acceptance_reasons.append(f"Experience MATCH: {exp_years} years >= {min_exp} years")
                else:
                    rejection_reasons.append(f"Experience NO MATCH: {exp_years} years < {min_exp} years")
            else:
                experience_met = True
            
            # Check qualification requirement
            if min_qualifications:
                if has_min_qual:
                    qualification_met = True
                    acceptance_reasons.append(f"Qualification MATCH: {list(degrees_in_resume)}")
                else:
                    rejection_reasons.append(f"Qualification NO MATCH: {degrees_in_resume} vs required {min_qualifications}")
            else:
                qualification_met = True
            
            # ALL must be met for option 4
            is_accepted = skills_met and experience_met and qualification_met
            
        elif choice == "5":  # Accept all
            is_accepted = True
            acceptance_reasons.append("No filtering - accepting all resumes")

        if is_accepted:
            matched_resumes += 1
            # Calculate score based on available information
            score = 0
            if matched_skills:
                score += len(matched_skills) * 5
            if exp_years > 0:
                score += exp_years * 2
            if degrees_in_resume:
                score += len(degrees_in_resume) * 3
            score += 5  # Base score
            
            resume_scores.append({
                "Candidate Name": name,
                "Filename": file,
                "Match Status": "ACCEPTED",
                "Score": score,
                "Matched Skills": ", ".join(matched_skills) if matched_skills else "None",
                "Experience Summary": experience_summary,
                "Qualification": education_summary,
                "Internship": internship_summary,
                "Email": email,
                "Phone": phone,
                "Years of Experience": exp_years,
                "Acceptance Reasons": ", ".join(acceptance_reasons),
                "Skills Match": "TRUE" if choice == "1" and matched_skills else "N/A",
                "Experience Match": "TRUE" if choice == "2" and exp_years >= min_exp else "N/A",
                "Qualification Match": "TRUE" if choice == "3" and has_min_qual else "N/A"
            })
        else:
            rejected_resumes += 1
            
            # Also add rejected resumes to track
            resume_scores.append({
                "Candidate Name": name,
                "Filename": file,
                "Match Status": "REJECTED",
                "Score": 0,
                "Matched Skills": ", ".join(matched_skills) if matched_skills else "None",
                "Experience Summary": experience_summary,
                "Qualification": education_summary,
                "Internship": internship_summary,
                "Email": email,
                "Phone": phone,
                "Years of Experience": exp_years,
                "Rejection Reasons": ", ".join(rejection_reasons),
                "Skills Match": "FALSE" if choice == "1" and not matched_skills else "N/A",
                "Experience Match": "FALSE" if choice == "2" and exp_years < min_exp else "N/A",
                "Qualification Match": "FALSE" if choice == "3" and not has_min_qual else "N/A"
            })

    # Summary statistics
    summary = {
        "total_resumes": total_resumes,
        "matched_resumes": matched_resumes,
        "rejected_resumes": rejected_resumes,
        "acceptance_rate": (matched_resumes/total_resumes)*100 if total_resumes > 0 else 0,
        "rejection_rate": (rejected_resumes/total_resumes)*100 if total_resumes > 0 else 0
    }
    
    if resume_scores:
        # Save all results (both accepted and rejected)
        df = pd.DataFrame(resume_scores)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(folder_path, f"resume_analysis_results_{timestamp}.xlsx")
        df.to_excel(output_file, index=False)
        
        # Save only accepted resumes
        accepted_df = df[df['Match Status'] == 'ACCEPTED'].copy()
        accepted_file = None
        if not accepted_df.empty:
            accepted_file = os.path.join(folder_path, f"accepted_resumes_{timestamp}.xlsx")
            accepted_df.to_excel(accepted_file, index=False)
        
        # Save only rejected resumes
        rejected_df = df[df['Match Status'] == 'REJECTED'].copy()
        rejected_file = None
        if not rejected_df.empty:
            rejected_file = os.path.join(folder_path, f"rejected_resumes_{timestamp}.xlsx")
            rejected_df.to_excel(rejected_file, index=False)
        
        return {
            "summary": summary,
            "results": resume_scores,
            "output_file": output_file,
            "accepted_file": accepted_file,
            "rejected_file": rejected_file
        }
    else:
        return {
            "summary": summary,
            "results": [],
            "output_file": None,
            "accepted_file": None,
            "rejected_file": None
        }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    if 'files' not in request.files:
        flash('No files selected')
        return redirect(request.url)
    
    files = request.files.getlist('files')
    
    if not files or files[0].filename == '':
        flash('No files selected')
        return redirect(request.url)
    
    session_folder = os.path.join(app.config['UPLOAD_FOLDER'], f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    os.makedirs(session_folder, exist_ok=True)
    
    uploaded_files = []
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(session_folder, filename)
            file.save(file_path)
            uploaded_files.append(filename)
        else:
            flash(f'Invalid file type: {file.filename}')
    
    if uploaded_files:
        flash(f'Successfully uploaded {len(uploaded_files)} files')
        return render_template('analyze.html', files=uploaded_files, session_folder=session_folder)
    else:
        flash('No valid files uploaded')
        return redirect(url_for('index'))

@app.route('/analyze', methods=['POST'])
def analyze():
    session_folder = request.form.get('session_folder')
    choice = request.form.get('choice')
    
    if not session_folder or not os.path.exists(session_folder):
        flash('Session folder not found')
        return redirect(url_for('index'))
    
    skills_input = request.form.get('skills', '').strip()
    experience_input = request.form.get('experience', '').strip()
    qualification_input = request.form.get('qualifications', '').strip()
    
    skills = [s.strip().casefold() for s in skills_input.split(",") if s.strip()] if skills_input else []
    
    try:
        min_exp = int(experience_input) if experience_input else 0
        if min_exp < 0:
            min_exp = 0
    except ValueError:
        min_exp = 0
    
    qualification_mapping = {
        'b.tech': 'btech', 'btech': 'btech', 'b.e': 'btech', 'bachelor of technology': 'btech',
        'bachelor of engineering': 'btech', 'bachelor of tech': 'btech', 'bachelor of eng': 'btech',
        'bmech': 'bachelor in mechanical engineering',
        'bachelor in mechanical engg': 'bmech',
        'bme': 'bmech',
        'bchem': 'bachelor in chemical engineering',
        'bachelor in chemical engg': 'bchem',
        'bche': 'bchem',
        'm.tech': 'mtech', 'mtech': 'mtech', 'm.e': 'mtech', 'master of technology': 'mtech',
        'master of engineering': 'mtech', 'master of tech': 'mtech', 'master of eng': 'mtech',
        'b.sc': 'bsc', 'bsc': 'bsc', 'bachelor of science': 'bsc',
        'm.sc': 'msc', 'msc': 'msc', 'master of science': 'msc',
        'b.com': 'bcom', 'bcom': 'bcom', 'bachelor of commerce': 'bcom',
        'm.com': 'mcom', 'mcom': 'mcom', 'master of commerce': 'mcom',
        'phd': 'phd', 'doctorate': 'phd', 'doctor of philosophy': 'phd',
        'diploma': 'diploma', 'polytechnic': 'diploma'
    }
    
    qualifications = []
    if qualification_input:
        for q in qualification_input.split(","):
            q = q.strip().casefold()
            if q:
                normalized_qual = qualification_mapping.get(q, q)
                qualifications.append(normalized_qual)
    
    result = process_resumes(session_folder, skills, min_exp, qualifications, choice)
    
    return render_template('results.html', result=result, choice=choice)

@app.route('/download/<filename>')
def download_file(filename):
    try:
        return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename), as_attachment=True)
    except FileNotFoundError:
        flash('File not found')
        return redirect(url_for('index'))

@app.route('/clear_session/<session_folder>')
def clear_session(session_folder):
    try:
        session_path = os.path.join(app.config['UPLOAD_FOLDER'], session_folder)
        if os.path.exists(session_path):
            shutil.rmtree(session_path)
        flash('Session cleared successfully')
    except Exception as e:
        flash(f'Error clearing session: {str(e)}')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
    