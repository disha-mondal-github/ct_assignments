import os
import PyPDF2
import docx2txt
from typing import List
from llama_index.core import Document


class DocumentProcessor:
    """Process various document formats for the legal chatbot"""
    
    def __init__(self, documents_folder: str = "documents"):
        self.documents_folder = documents_folder
        if not os.path.exists(documents_folder):
            os.makedirs(documents_folder)
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF file"""
        try:
            text = ""
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except Exception as e:
            print(f"Error reading PDF {pdf_path}: {str(e)}")
            return ""
    
    def extract_text_from_docx(self, docx_path: str) -> str:
        """Extract text from DOCX file"""
        try:
            return docx2txt.process(docx_path)
        except Exception as e:
            print(f"Error reading DOCX {docx_path}: {str(e)}")
            return ""
    
    def extract_text_from_txt(self, txt_path: str) -> str:
        """Extract text from TXT file"""
        try:
            with open(txt_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            print(f"Error reading TXT {txt_path}: {str(e)}")
            return ""
    
    def process_document(self, file_path: str) -> Document:
        """Process a single document and return LlamaIndex Document object"""
        file_extension = os.path.splitext(file_path)[1].lower()
        file_name = os.path.basename(file_path)
        
        if file_extension == '.pdf':
            text = self.extract_text_from_pdf(file_path)
        elif file_extension == '.docx':
            text = self.extract_text_from_docx(file_path)
        elif file_extension == '.txt':
            text = self.extract_text_from_txt(file_path)
        else:
            print(f"Unsupported file format: {file_extension}")
            return None
        
        if text.strip():
            return Document(
                text=text,
                metadata={
                    "filename": file_name,
                    "file_path": file_path,
                    "document_type": "legal_document"
                }
            )
        return None
    
    def process_all_documents(self) -> List[Document]:
        """Process all documents in the documents folder"""
        documents = []
        
        if not os.path.exists(self.documents_folder):
            print(f"Documents folder '{self.documents_folder}' not found!")
            return documents
        
        for filename in os.listdir(self.documents_folder):
            file_path = os.path.join(self.documents_folder, filename)
            if os.path.isfile(file_path):
                doc = self.process_document(file_path)
                if doc:
                    documents.append(doc)
                    print(f"Processed: {filename}")
        
        print(f"Total documents processed: {len(documents)}")
        return documents