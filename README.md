# Resume Analyzer - Smart Filtering System

A modern web application for analyzing and filtering resumes based on skills, experience, and qualifications. Built with Flask and featuring a beautiful, responsive UI.

## Features

- **Smart Resume Parsing**: Extracts text from PDF and DOCX files
- **Flexible Filtering**: Filter by skills, experience, qualifications, or all criteria
- **Beautiful UI**: Modern, responsive design with drag-and-drop file upload
- **Detailed Analysis**: Comprehensive resume analysis with scoring
- **Export Results**: Download analysis results in Excel format
- **Real-time Processing**: Instant analysis with progress indicators

## Supported File Formats

- PDF files (.pdf)
- Microsoft Word documents (.docx)

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Setup Instructions

1. **Clone or download the project files**

2. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Access the application**
   Open your web browser and go to: `http://localhost:5000`

## Usage

### Step 1: Upload Resumes
- Click "Choose Files" or drag and drop resume files
- Supported formats: PDF and DOCX
- You can upload multiple files at once

### Step 2: Configure Analysis
Choose your filtering criteria:

1. **Skills Only**: Filter resumes based on required skills
2. **Experience Only**: Filter resumes based on minimum experience
3. **Qualification Only**: Filter resumes based on education level
4. **All Criteria**: All requirements must be met (AND logic)
5. **No Filtering**: Accept all resumes without filtering

### Step 3: Set Parameters
- **Required Skills**: Enter skills separated by commas (e.g., "python, java, machine learning")
- **Minimum Experience**: Enter years of experience (e.g., 2.5)
- **Required Qualifications**: Enter qualifications separated by commas (e.g., "btech, mtech")

### Step 4: View Results
- See detailed analysis statistics
- Review individual resume results
- Download results in Excel format

## Filtering Options

### Skills Filtering
- Searches for specific skills in resume text
- Case-insensitive matching
- Multiple skills can be specified

### Experience Filtering
- Extracts experience from resume text
- Supports various formats (e.g., "5 years", "3+ years")
- Handles fresher/intern keywords

### Qualification Filtering
- Recognizes various degree types:
  - BTech/BE (Bachelor of Technology/Engineering)
  - MTech/ME (Master of Technology/Engineering)
  - BSc (Bachelor of Science)
  - MSc (Master of Science)
  - BCom (Bachelor of Commerce)
  - MCom (Master of Commerce)
  - PhD (Doctor of Philosophy)
  - Diploma

## Output Files

The application generates three types of Excel files:

1. **All Results**: Complete analysis of all resumes
2. **Accepted Resumes**: Only resumes that match criteria
3. **Rejected Resumes**: Resumes that don't match criteria

Each file contains:
- Candidate information (name, email, phone)
- Experience details
- Education qualifications
- Matched skills
- Analysis score
- Acceptance/rejection reasons

## Technical Details

### Architecture
- **Backend**: Flask (Python web framework)
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **File Processing**: pdfplumber (PDF), docx2txt (DOCX)
- **Data Analysis**: pandas, numpy
- **File Export**: openpyxl

### Key Components
- `app.py`: Main Flask application
- `templates/`: HTML templates
- `uploads/`: Temporary file storage
- `parser_1.py`: Original command-line parser (for reference)

### Security Features
- Secure file upload handling
- File type validation
- Session-based file management
- Automatic cleanup of temporary files

## Troubleshooting

### Common Issues

1. **Port already in use**
   - Change the port in `app.py`: `app.run(port=5001)`

2. **File upload errors**
   - Ensure files are PDF or DOCX format
   - Check file size (recommended < 10MB per file)

3. **Import errors**
   - Verify all dependencies are installed: `pip install -r requirements.txt`
   - Check Python version (3.8+ required)

4. **Permission errors**
   - Ensure write permissions for the uploads directory
   - Run with appropriate user permissions

### Performance Tips

- For large numbers of resumes (>50), consider processing in batches
- Ensure sufficient disk space for temporary files
- Close other applications to free up memory

## Development

### Project Structure
```
avres/
├── app.py                 # Main Flask application
├── parser_1.py           # Original command-line parser
├── requirements.txt      # Python dependencies
├── README.md            # This file
├── templates/           # HTML templates
│   ├── index.html      # Main upload page
│   ├── analyze.html    # Analysis configuration
│   └── results.html    # Results display
└── uploads/            # Temporary file storage
```

### Adding New Features

1. **New File Formats**: Extend the `allowed_file()` function
2. **Additional Filters**: Modify the `process_resumes()` function
3. **UI Enhancements**: Update HTML templates and CSS
4. **Export Formats**: Add new export functions

## License

This project is open source and available under the MIT License.

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review the code comments
3. Create an issue with detailed error information

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

**Note**: This application is designed for educational and professional use. Ensure compliance with data protection regulations when processing personal information. 