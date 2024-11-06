import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
import io
from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
import logging
import traceback
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pathlib import Path
import asyncio
from streamlit import cache_data, cache_resource
from google.cloud import speech
import tempfile
import numpy as np
import base64
import json
import datetime
import time
import re
import streamlit.components.v1 as components
from streamlit_audio_recorder import st_audio_recorder
from pydub import AudioSegment
import subprocess
import psutil

# Set page config as the first Streamlit command
st.set_page_config(layout="wide")

# Add at the start of your app
try:
    client = speech.SpeechClient()
    st.write("Successfully created Speech-to-Text client")
except Exception as e:
    st.error(f"Error creating Speech-to-Text client: {e}")

# Add near the top of your file, where other st.markdown calls are
st.markdown("""
    <style>
    #recordButton_audio_client::before {
        content: "Speak" !important;
    }
    #recordButton_audio_client[data-recording="true"]::before {
        content: "Stop" !important;
    }
    /* Hide clear recording buttons */
    button[kind="secondary"]:has(div:contains("Clear Recording")) {
        display: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

def load_environment():
    load_dotenv()
    if not os.getenv("GOOGLE_API_KEY"):
        st.error("Google API key not found. Please check your .env file.")
        st.stop()
    if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        st.error("Google Application Credentials not found. Please set the GOOGLE_APPLICATION_CREDENTIALS environment variable.")
        st.stop()

def initialize_session_state():
    if 'generated_content' not in st.session_state:
        st.session_state.generated_content = None
    if 'additional_statements' not in st.session_state:
        st.session_state.additional_statements = ""
    if 'input_method' not in st.session_state:
        st.session_state.input_method = {}
    if 'questions' not in st.session_state:
        st.session_state.questions = {
            'client': {"id": 0, "question": "Who is the client?", "type": "text", "answer": ""},
            
            'general_info': [
                {"id": 1, "question": "Why were we called?", "type": "text", "answer": ""},
                {"id": 2, "question": "Where is the project location?", "type": "text", "answer": ""},
                {"id": 3, "question": "What is the strategic purpose of this project?", "type": "text", "answer": ""},
                {"id": 4, "question": "What is the tactical goal of this project?", "type": "text", "answer": ""},
                {"id": 5, "question": "What is the scope of work proposed?", "type": "text", "answer": ""},
                {"id": 6, "question": "What is the technical approach to this project?", "type": "text", "answer": ""},
                {"id": 7, "question": "What are the obstacles to the tactical goal?", "type": "text", "answer": ""},
                {"id": 8, "question": "What is the proposed timeline for project completion?", "type": "text", "answer": ""},
                {"id": 9, "question": "What equipment is required?", "type": "text", "answer": ""},
                {"id": 10, "question": "Why is that equipment important and unique?", "type": "text", "answer": ""},
                {"id": 11, "question": "What is the desired end state?", "type": "text", "answer": ""}
            ],
            
            'project_details': {
                'main_questions': [
                    {"id": 1, "question": "Does this project involve multiple phases?", "type": "radio", "answer": ""},
                    {"id": 2, "question": "Are there specific technical requirements or limits to meet?", "type": "radio", "answer": ""}
                ],
                'phase_details': [
                    {"id": 1, "question": "How many phases does the project have and briefly describe each:", "type": "text", "answer": ""},
                    {"id": 2, "question": "What deliverables are required for each phase?", "type": "text", "answer": ""},
                    {"id": 3, "question": "What is the proposed timeline for each phase?", "type": "text", "answer": ""}
                ],
                'technical_details': [
                    {"id": 1, "question": "What are the specific technical requirements?", "type": "text", "answer": ""},
                    {"id": 2, "question": "What are the technical limits?", "type": "text", "answer": ""},
                    {"id": 3, "question": "Are there any regulatory standards to comply with?", "type": "text", "answer": ""}
                ]
            },
            
            'additional_details': [
                {"id": 1, "question": "What training is necessary for this project?", "type": "text", "answer": ""},
                {"id": 2, "question": "What reporting is necessary for this project?", "type": "text", "answer": ""},
                {"id": 3, "question": "What are the potential risks and mitigation strategies?", "type": "text", "answer": ""},
                {"id": 4, "question": "Are there intangible results expected? (expectations of client)", "type": "text", "answer": ""},
                {"id": 5, "question": "Are there any specific coordination requirements with other parties?", "type": "radio", "answer": ""}
            ],
            'coordination_details': [
                {"id": 1, "question": "Please provide details about the coordination requirements:", "type": "text", "answer": ""}
            ]
        }
    
    if 'effective_date' not in st.session_state:
        st.session_state.effective_date = datetime.date.today().isoformat()
    if 'client_address' not in st.session_state:
        st.session_state.client_address = ""
    if 'labor_costs' not in st.session_state:
        st.session_state.labor_costs = {
            'roles': [
                {'role': 'Project Management', 'rate': 325.00, 'hours': 0},
                {'role': 'Senior Wastewater Consultant', 'rate': 275.00, 'hours': 0},
                {'role': 'Wastewater Consultant', 'rate': 225.00, 'hours': 0},
                {'role': 'Senior Winemaker', 'rate': 250.00, 'hours': 0},
                {'role': 'Winemaker', 'rate': 200.00, 'hours': 0},
                {'role': 'Process Engineer', 'rate': 225.00, 'hours': 0},
                {'role': 'Mechanical Engineer', 'rate': 225.00, 'hours': 0},
                {'role': 'Fabrication Specialist', 'rate': 175.00, 'hours': 0},
                {'role': 'Discipline Specialist', 'rate': 175.00, 'hours': 0},
                {'role': 'Operation/Training Technician - ST', 'rate': 150.00, 'hours': 0},
                {'role': 'Operation/Training Technician - OT', 'rate': 225.00, 'hours': 0},
                {'role': 'Administration/Purchasing', 'rate': 135.00, 'hours': 0},
                {'role': 'Schedule Administration', 'rate': 135.00, 'hours': 0},
                {'role': 'Cost Administration', 'rate': 135.00, 'hours': 0}
            ],
            'expenses': {
                'mileage_rate': 0.625,
                'mileage': 0,
                'truck_days': 0,
                'truck_rate': 200.00,
                'materials_cost': 0,
                'materials_markup': 0.25
            },
            'total': 0
        }
                
    if 'effective_date' not in st.session_state:
        st.session_state.effective_date = datetime.date.today().isoformat()
    if 'client_address' not in st.session_state:
        st.session_state.client_address = ""

def create_document(content, file_format):
    buffer = io.BytesIO()

    if file_format == "DOCX":
        doc = Document()
        styles = doc.styles
        
        def get_or_add_style(name, style_type):
            try:
                return styles[name]
            except KeyError:
                return styles.add_style(name, style_type)
        
        # Title style (for "Statement of Work")
        title_style = get_or_add_style('CustomTitle', WD_STYLE_TYPE.PARAGRAPH)
        title_style.font.name = 'Calibri'
        title_style.font.size = Pt(16)
        title_style.font.bold = True
        title_style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Section heading style (for all numbered sections)
        heading_style = get_or_add_style('CustomHeading', WD_STYLE_TYPE.PARAGRAPH)
        heading_style.font.name = 'Calibri'
        heading_style.font.size = Pt(11)
        heading_style.font.bold = True
        
        # Body text style
        body_style = get_or_add_style('CustomBodyText', WD_STYLE_TYPE.PARAGRAPH)
        body_style.font.name = 'Calibri'
        body_style.font.size = Pt(11)
        
        # Add main SOW content
        for paragraph in content.split('\n\n'):
            if paragraph.strip():
                doc.add_paragraph(paragraph)

        # Add schedules
        if hasattr(st.session_state, 'attached_schedules') and st.session_state.attached_schedules:
            for file in st.session_state.attached_schedules:
                if file.name.lower().endswith('.docx'):
                    doc.add_page_break()
                    # Merge DOCX schedule
                    schedule_doc = Document(file)
                    for element in schedule_doc.element.body:
                        doc.element.body.append(element)
                else:
                    # For non-DOCX files, just add a reference
                    doc.add_paragraph(f"Note: {file.name} is provided as a separate file")

        doc.save(buffer)
    elif file_format == "TXT":
        lines = content.split('\n\n')
        formatted_content = []
        for line in lines:
            if line.strip() == "Statement of Work":
                formatted_content.append(line.center(80))
                formatted_content.append('')  # Add an empty line after the title
            else:
                formatted_content.append(line)
        buffer.write('\n\n'.join(formatted_content).encode())
    else:
        raise ValueError(f"Unsupported file format: {file_format}")
        
    buffer.seek(0)
    return buffer

def convert_pdf_to_text(pdf_file):
    text = ""
    with open(pdf_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n\n"
    return text

@cache_data
def query_vectorstore(query, k=5):
    vectorstore = load_vectorstore()
    results = vectorstore.similarity_search(query, k=k)
    return results

@cache_resource
def load_vectorstore():
    try:
        # Use the same path construction as in initialize_vectorstore
        vectorstore_path = os.path.join(os.path.dirname(__file__), 'config', 'vectorstore.faiss')
        print(f"\nAttempting to load vectorstore from: {vectorstore_path}")
        print(f"Path exists: {os.path.exists(vectorstore_path)}")
        print(f"Directory contents: {os.listdir(os.path.dirname(vectorstore_path))}")
        
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        print("Created embeddings object")
        
        vectorstore = FAISS.load_local(vectorstore_path, embeddings, allow_dangerous_deserialization=True)
        print("Successfully loaded vectorstore")
        return vectorstore
        
    except Exception as e:
        print(f"Error loading vectorstore: {str(e)}")
        print(f"Full error: {traceback.format_exc()}")
        return None

def display_labor_costs():
    st.subheader("Labor Cost Estimation")
    
    # Labor Costs
    total_labor_cost = 0
    st.markdown("##### Labor Rates")
    
    def format_hours(hours):
        """Convert decimal hours to HH:MM format"""
        whole_hours = int(hours)
        minutes = int((hours - whole_hours) * 60)
        return f"{whole_hours}:{minutes:02d}"

    def parse_hours(time_str):
        """Convert HH:MM format to decimal hours"""
        try:
            if ':' in time_str:
                hours, minutes = map(int, time_str.split(':'))
                return hours + minutes/60
            return float(time_str)
        except:
            return 0.0
    
    for i, role in enumerate(st.session_state.labor_costs['roles']):
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        
        with col1:
            st.text(role['role'])
        with col2:
            st.text(f"${role['rate']:.2f}/hr")
        with col3:
            hours = st.number_input(
                f"Hours", 
                value=float(role['hours']), 
                key=f"hours_{i}",
                min_value=0.0,
                step=0.25,  # Changed to 0.25 for quarter-hour increments
                format="%.2f",
                help="Enter time in quarter-hour increments (0.25 = 15 min, 0.5 = 30 min, 0.75 = 45 min)",
                label_visibility="collapsed"
            )
            displayed_time = format_hours(hours)
            st.text(f"({displayed_time})")  # Show HH:MM format below the input
            st.session_state.labor_costs['roles'][i]['hours'] = hours
        with col4:
            subtotal = role['rate'] * hours
            st.text(f"${subtotal:,.2f}")
            total_labor_cost += subtotal

    # Expenses
    st.markdown("##### Expenses")
    expenses = st.session_state.labor_costs['expenses']
    
    col1, col2 = st.columns(2)
    with col1:
        mileage = st.number_input(
            f"Mileage (${expenses['mileage_rate']:.3f}/mile)", 
            value=float(expenses['mileage']),
            min_value=0.0
        )
        truck_days = st.number_input(
            f"Truck Days (${expenses['truck_rate']:.2f}/day)", 
            value=int(expenses['truck_days']),
            min_value=0
        )
        materials_cost = st.number_input(
            f"Materials Cost (+ {expenses['materials_markup']*100}% markup)", 
            value=float(expenses['materials_cost']),
            min_value=0.0
        )
    
    with col2:
        mileage_total = mileage * expenses['mileage_rate']
        truck_total = truck_days * expenses['truck_rate']
        materials_total = materials_cost * (1 + expenses['materials_markup'])
        
        st.text(f"Mileage Total: ${mileage_total:,.2f}")
        st.text(f"Truck Total: ${truck_total:,.2f}")
        st.text(f"Materials Total: ${materials_total:,.2f}")

    # Update session state
    st.session_state.labor_costs['expenses']['mileage'] = mileage
    st.session_state.labor_costs['expenses']['truck_days'] = truck_days
    st.session_state.labor_costs['expenses']['materials_cost'] = materials_cost
    
    # Calculate grand total
    grand_total = total_labor_cost + mileage_total + truck_total + materials_total
    st.session_state.labor_costs['total'] = grand_total
    
    st.markdown("---")
    st.markdown(f"### Total Project Cost: ${grand_total:,.2f}")

def initialize_vectorstore():
    """Initialize the vectorstore with example documents"""
    try:
        print("Starting vectorstore initialization...")
        
        # Use relative path from the project root
        doc_path = os.path.join(os.path.dirname(__file__), 'config', 'documents')
        vectorstore_path = os.path.join(os.path.dirname(__file__), 'config', 'vectorstore.faiss')
        
        print(f"Loading documents from: {doc_path}")
        
        # Load PDF files only
        pdf_loader = DirectoryLoader(
            doc_path,
            glob="**/*.pdf",
            loader_cls=PyPDFLoader,
            recursive=True
        )
        documents = pdf_loader.load()
        print(f"Loaded {len(documents)} PDF documents")
        
        # Split documents
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        splits = text_splitter.split_documents(documents)
        print(f"Created {len(splits)} text chunks")
        
        # Use HuggingFace embeddings
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        
        # Create and save vectorstore
        vectorstore = FAISS.from_documents(splits, embeddings)
        vectorstore.save_local(vectorstore_path)
        
        print("Initialization complete!")
        return vectorstore
    except Exception as e:
        print(f"Error initializing vectorstore: {e}")
        return None

def get_answer(category, question_text):
    """Helper function to get answer for a specific question"""
    if category == 'client':
        return st.session_state.questions['client']["answer"]
    
    questions = st.session_state.questions.get(category, [])
    if isinstance(questions, list):
        for q in questions:
            if q["question"] == question_text:
                return q["answer"]
    elif isinstance(questions, dict):
        for section in questions.values():
            if isinstance(section, list):
                for q in section:
                    if q["question"] == question_text:
                        return q["answer"]
    return ""

def format_phase_details():
    """Format phase details if project has multiple phases"""
    phase_questions = st.session_state.questions['project_details']['phase_details']
    phases = ""
    for q in phase_questions:
        if q["answer"]:
            phases += f"- {q['question']}\n  {q['answer']}\n"
    return phases.strip()

def format_technical_requirements():
    """Format technical requirements if project has specific requirements"""
    tech_questions = st.session_state.questions['project_details']['technical_details']
    requirements = ""
    for q in tech_questions:
        if q["answer"]:
            requirements += f"- {q['question']}\n  {q['answer']}\n"
    return requirements.strip()

def format_labor_costs():
    total_cost = st.session_state.labor_costs['total']
    labor_lines = []
    
    for role in st.session_state.labor_costs['roles']:
        if role['hours'] > 0:
            cost = role['rate'] * role['hours']
            labor_lines.append(f"{role['role']}: {role['hours']:.1f} hours at ${role['rate']:.2f}/hr (${cost:,.2f})")
    
    return f"""Customer shall compensate RWS as follows:

{chr(10).join(labor_lines)}

Total Project Cost: ${total_cost:,.2f}"""

# Add after your helper functions
async def check_vectorstore():
    try:
        # Search for chunks that start with EXECUTIVE SUMMARY
        results = await asyncio.to_thread(
            query_vectorstore, 
            "EXECUTIVE SUMMARY Grapevine Land Management seeks to develop"  # Using exact start of your example
        )
        
        for i, doc in enumerate(results, 1):
            # Clean up the display text
            content = doc.page_content
            # Fix word spacing issues
            content = content.replace("EXECUTIVESUMMARY", "EXECUTIVE SUMMARY")
            content = content.replace("  ", " ")
            # Split and rejoin to fix running-together words
            content = ' '.join([word for word in content.split() if word])
            
            st.write(f"\nDocument {i}:")
            st.write(content[:1000])
            st.write("-" * 80)
    except Exception as e:
        st.error(f"Error accessing vectorstore: {str(e)}")

async def generate_sow():
    with st.spinner("Generating SOW..."):
        try:
            # First get all the user inputs
            client_name = st.session_state.questions['client']["answer"].strip()
            client_address = st.session_state.client_address
            effective_date = st.session_state.effective_date

            # Now add debug prints after we have the data
            print("\nUser Inputs:")
            print(f"Client Name: {client_name}")
            print(f"Strategic Purpose: {get_answer('general_info', 'Strategic Purpose')}")
            print(f"Technical Approach: {get_answer('general_info', 'Technical Approach')}")
            print(f"Additional Statements: {st.session_state.additional_statements}")
            
            legal_preamble = generate_legal_preamble(client_name, client_address, effective_date)

            # Check if project has phases and technical requirements
            has_phases = st.session_state.questions['project_details']['main_questions'][0]["answer"] == "Yes"
            has_requirements = st.session_state.questions['project_details']['main_questions'][1]["answer"] == "Yes"
            
            # Get formatted details if applicable
            phase_details = format_phase_details() if has_phases else "Single Phase Project"
            technical_requirements = format_technical_requirements() if has_requirements else ""

            # Generate labor costs text
            labor_cost_text = format_labor_costs()

            # Get context for each section using two-tier search
            print("\nGetting Executive Summary Context...")
            additional_context = st.session_state.additional_statements.strip()
            
            # Extract key terms from additional statements
            key_terms = " ".join([
                "nano-particles",
                "filtration",
                "wastewater treatment",
                "membrane",
                "regulatory compliance"
            ]) if additional_context else ""
            
            exec_summary_context = await query_vectorstore_two_tier(
                f"{client_name} wastewater treatment compliance",
                "executive_summary"
            )
            
            services_context = await query_vectorstore_two_tier(
                f"filtration system membrane treatment {key_terms}",
                "services"
            )
            
            deliverables_context = await query_vectorstore_two_tier(
                f"wastewater treatment system outputs compliance {key_terms}",
                "deliverables"
            )

            prompt = f"""
            As a specialist for Recovered Water Solutions, 
            please provide a Statement of Work (SOW) based on the following information:

            {legal_preamble}

            Strategic Context:
            - Why Called: {get_answer('general_info', 'Why were we called?')}
            - Strategic Purpose: {get_answer('general_info', 'What is the strategic purpose of this project?')}
            - Tactical Goal: {get_answer('general_info', 'What is the tactical goal of this project?')}
            - Desired End State: {get_answer('general_info', 'What is the desired end state?')}

            Technical Approach:
            - Scope of Work: {get_answer('general_info', 'What is the scope of work proposed?')}
            - Technical Approach: {get_answer('general_info', 'What is the technical approach to this project?')}
            - Equipment Required: {get_answer('general_info', 'What equipment is required?')}
            - Equipment Importance: {get_answer('general_info', 'Why is that equipment important and unique?')}

            Project Structure:
            {phase_details if has_phases else "Single Phase Project"}
            {technical_requirements if has_requirements else ""}

            Implementation Requirements:
            - Training Needs: {get_answer('additional_details', 'What training is necessary for this project?')}
            - Reporting Requirements: {get_answer('additional_details', 'What reporting is necessary for this project?')}
            - Risk Management: {get_answer('additional_details', 'What are the potential risks and mitigation strategies?')}

            {labor_cost_text}

            Additional context:
            {st.session_state.additional_statements}

            Relevant Executive Summary examples:
            """
            
            for doc in exec_summary_context:
                prompt += f"- {doc.page_content[:300]}...\n"
            
            prompt += "\n\nRelevant Services examples:\n"
            for doc in services_context:
                prompt += f"- {doc.page_content[:300]}...\n"
            
            prompt += "\n\nRelevant Deliverables examples:\n"
            for doc in deliverables_context:
                prompt += f"- {doc.page_content[:300]}...\n"

            prompt += """
            Your response should follow this exact format:
            # Executive Summary
            [Using the Strategic Context and examples, craft a compelling narrative that explains the project's purpose, goals, and desired outcomes. Focus on the business value and strategic importance.]

            # 1. Description of Services
            [Detail the technical approach, methodologies, and specific services using the Technical Approach section and examples]

            # 2. Description of Deliverables
            [List all tangible and intangible deliverables, including equipment, documentation, training, and reports]

            # 3. Work Schedule
            [Use the Project Structure information to detail timeline and phases]

            # 4. Term of this SOW
            [Standard term details]

            # 5. Basis for Compensation
            [Include the detailed labor costs and expenses provided]

            # 6. Title and Risk of Loss
            [Standard title and risk details]

            # 7. Additional Representations and Warranties
            [SKIP THIS SECTION - it will be added automatically]

            # 8. Additional Terms
            [Will be "None." unless specifically provided in app responses]

            # 9. List of attached SOW Schedules
            [List any relevant schedules or attachments]

            IMPORTANT: 
            1. Do not include any title or heading at the beginning of your response. Start directly with the Executive Summary.
            2. Maintain RWS's professional yet approachable tone throughout.
            3. Use the provided examples to match style and depth while customizing content to this specific project.
            """

            # Configure the model
            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            print("API Key loaded:", "Yes" if os.getenv("GOOGLE_API_KEY") else "No")

            # Create model and generate content
            model = genai.GenerativeModel('gemini-pro')  # New syntax
            response = await asyncio.to_thread(
                lambda: model.generate_content(prompt).text
            )

            if response:
                # First, remove all sections we handle separately (6-9)
                cleaned_response = re.sub(
                    r'(?:^|\n)(?:6\.|Section\s*6\.?)\s*Title\s*and\s*Risk\s*of\s*Loss.*?(?=(?:\n\s*(?:[7-9]\.|Section\s*[7-9]\.?))|$)|' +
                    r'(?:^|\n)(?:7\.|Section\s*7\.?)\s*Additional\s*Representations.*?(?=(?:\n\s*(?:[8-9]\.|Section\s*[8-9]\.?))|$)|' +
                    r'(?:^|\n)(?:8\.|Section\s*8\.?)\s*Additional\s*Terms.*?(?=(?:\n\s*(?:9\.|Section\s*9\.?))|$)|' +
                    r'(?:^|\n)(?:9\.|Section\s*9\.?)\s*List\s*of\s*attached.*?(?=$)',
                    '',
                    response,
                    flags=re.IGNORECASE|re.DOTALL
                )
                
                # Remove any SOW header
                cleaned_response = re.sub(r'^(Statement of Work|SOW)(\n+|\s+)', '', cleaned_response, flags=re.IGNORECASE)
                
                # Split at the last section (should be section 5)
                parts = re.split(r'(?=\d{1,2}\.\s+(?:Title|Additional|List))', cleaned_response)
                
                # Combine content with our generated sections
                st.session_state.generated_content = (
                    f"Statement of Work\n\n"
                    f"{legal_preamble}\n\n"
                    f"{parts[0].strip()}\n\n"  # Content through Section 5
                    f"{generate_section_6(client_name)}\n\n"  # Section 6
                    f"{generate_section_7(client_name)}\n\n"  # Section 7
                    f"{generate_section_8()}\n\n"  # Section 8
                    f"{generate_section_9()}"  # Section 9
                )
            else:
                raise ValueError("No content generated by the model.")
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.error("Full error details:")
            st.exception(e)

def transcribe_audio(audio_content, sample_rate_hertz=16000):
    try:
        if isinstance(audio_content, dict):
            audio_data = audio_content.get('data', audio_content.get('bytes', []))
        else:
            audio_data = audio_content
            
        audio_bytes = bytearray(audio_data)
        
        with open('input.webm', 'wb') as f:
            f.write(audio_bytes)
            
        result = subprocess.run(
            ['ffmpeg', '-y',
             '-i', 'input.webm',
             '-acodec', 'pcm_s16le', 
             '-ar', str(sample_rate_hertz),
             '-ac', '1', 'output.wav'],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        with open('output.wav', 'rb') as f:
            wav_content = f.read()
            
        audio = speech.RecognitionAudio(content=wav_content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=sample_rate_hertz,
            language_code="en-US"
        )
        
        response = client.recognize(config=config, audio=audio)
        transcript = response.results[0].alternatives[0].transcript
        
        return transcript
        
    except Exception as e:
        print(f"Error: {e}")
        return None

def get_audio_input(question, key):
    if key not in st.session_state:
        st.session_state[key] = ""
    
    # Add a transcription_complete flag
    transcription_key = f"transcription_complete_{key}"
    if transcription_key not in st.session_state:
        st.session_state[transcription_key] = False
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        text_value = st.text_area(question, 
                                key=f"text_{key}", 
                                value=st.session_state[key],
                                height=100)
        if text_value != st.session_state[key]:
            st.session_state[key] = text_value
    
    if st.session_state.input_method == 'Audio':
        with col2:
            st.write("Recording Status:")
            status_placeholder = st.empty()
            
            prev_audio_key = f"prev_audio_{key}"
            if prev_audio_key not in st.session_state:
                st.session_state[prev_audio_key] = None
            
            audio_bytes = st_audio_recorder(key=f"audio_{key}")
            
            # Only process when audio_bytes changes from None to not None
            if (audio_bytes is not None and 
                st.session_state[prev_audio_key] is None and 
                not st.session_state[transcription_key]):
                
                print(f"Triggering transcription for {key}")
                status_placeholder.info("Processing audio...")
                transcription = transcribe_audio(audio_bytes)
                
                if transcription:
                    st.session_state[key] = transcription
                    st.session_state[transcription_key] = True
                    status_placeholder.success("Transcription complete!")
                    st.rerun()
                else:
                    status_placeholder.error("Transcription failed")
            
            # Reset transcription flag after rerun
            if st.session_state[transcription_key]:
                st.session_state[transcription_key] = False
            
            # Update previous audio state
            st.session_state[prev_audio_key] = audio_bytes
    
    return st.session_state[key]

def generate_legal_preamble(client_name, client_address, sow_date):
    if not client_name:
        client_name = "[CLIENT NAME REQUIRED]"
    if not client_address:
        client_address = "[CLIENT ADDRESS REQUIRED]"
    if isinstance(sow_date, str):
        sow_date = datetime.date.fromisoformat(sow_date)
    sow_date_str = sow_date.strftime("%B %d, %Y")
    sow_year = sow_date.year

    preamble = f"""This statement of work ("SOW"), dated as of {sow_date_str} (the "SOW Effective Date") is by and between {client_name} ("Customer") with its principal place of business located at {client_address} and American Winesecrets, LLC, doing business as Recovered Water Solutions with its principal address at 1446 Industrial Avenue, Sebastopol, CA    95472, a California LLC ("Contractor" or "RWS"). This SOW and any accompanying exhibits, is incorporated into, forms a part of, and is in all respects subject to the terms of a Master Terms & Conditions Agreement (the "Agreement") dated {sow_date_str}."""
    return preamble

def handle_all_questions():
    st.subheader("Client Information")
    st.session_state.questions['client']["answer"] = get_audio_input("Who is the client?", "client")
    st.session_state.client_address = st.text_input("What is the client's address?", value=st.session_state.get("client_address", ""))

    st.subheader("Project Details")
    st.session_state.questions['primary_goal']["answer"] = get_audio_input("What is the primary goal of this project?", "primary_goal")
    st.session_state.questions['primary_challenge']["answer"] = get_audio_input("What is the primary challenge of this job?", "primary_challenge")
    st.session_state.questions['existing_systems']["answer"] = get_audio_input("Are there any existing systems or equipment relevant to this project?", "existing_systems")

    st.subheader("Additional Project Details")
    st.session_state.questions['timeline']["answer"] = get_audio_input("What is the proposed timeline for project completion?", "timeline")
    st.session_state.questions['kpis']["answer"] = get_audio_input("What are the key performance indicators (KPIs) for this project?", "kpis")
    st.session_state.questions['risks_mitigation']["answer"] = get_audio_input("What are the potential risks and mitigation strategies?", "risks_mitigation")
    st.session_state.questions['communication_protocols']["answer"] = get_audio_input("What are the communication protocols and reporting requirements?", "communication_protocols")
    st.session_state.questions['tangible_deliverables']["answer"] = get_audio_input("What tangible deliverables are expected (e.g., equipment, systems)?", "tangible_deliverables")
    st.session_state.questions['intangible_deliverables']["answer"] = get_audio_input("What intangible deliverables are expected (e.g., reports, training)?", "intangible_deliverables")

    st.subheader("Additional Statements")
    st.session_state.additional_statements = get_audio_input("Additional Statements", "additional_statements")

def generate_section_6(client_name):
    if hasattr(st.session_state, 'title_terms') and st.session_state.title_terms:
        terms = st.session_state.title_terms.replace('[Client Name]', client_name)
        return f"\n6. Title and Risk of Loss\n\n{terms}"
    return f"\n6. Title and Risk of Loss\n\nN/A"

def generate_section_7(client_name):
    return f"\n7. Additional Representations and Warranties\n\nAdditional Representations and Warranties. In addition to the representations and warranties set forth in the Agreement, Contractor represents and warrants to {client_name} that (i) its performance under the Agreement or this SOW nor any Deliverable (nor {client_name}'s use thereof) will not infringe the intellectual property rights of any third party, (ii) it is not aware of, and has not received any notice of, any encroachment or infringement of the rights of any third party, (iii) no Deliverable will contain a virus or other program or technology designed to permit unauthorized access to {client_name}'s system, and (iv) it will not lose or corrupt {client_name}'s data (including, without limitation, third party data)."

def generate_section_8():
    if hasattr(st.session_state, 'additional_terms') and st.session_state.additional_terms:
        return f"\n8. Additional Terms\n\n{st.session_state.additional_terms}"
    return f"\n8. Additional Terms\n\nNone."

def generate_section_9():
    if hasattr(st.session_state, 'attached_schedules') and st.session_state.attached_schedules:
        print(f"Debug - Generating section 9 with {len(st.session_state.attached_schedules)} files")
        schedule_list = "\n• ".join(file.name for file in st.session_state.attached_schedules)
        return f"\n9. List of attached SOW Schedules\n\n• {schedule_list}"
    return f"\n9. List of attached SOW Schedules\n\nNone"

async def search_for_executive_summary(user_input):
    # First search: Format and style from Executive Summaries
    format_results = await asyncio.to_thread(
        query_vectorstore, 
        "Executive Summary format and structure"
    )
    
    # Second search: Content from all relevant documents
    content_results = await asyncio.to_thread(
        query_vectorstore,
        f"Find relevant content for: {user_input}"
    )
    
    return format_results, content_results

async def search_for_executive_summary(user_input):
    """Two-tier search for executive summary generation"""
    try:
        # First search: Format and style from Executive Summaries
        format_results = await asyncio.to_thread(
            query_vectorstore, 
            "Find executive summary format and structure examples"
        )
        
        # Second search: Content from all relevant documents
        content_results = await asyncio.to_thread(
            query_vectorstore,
            f"Find relevant content for project about: {user_input}"
        )
        
        return format_results, content_results
    except Exception as e:
        print(f"Error in search: {e}")
        return None, None

async def generate_executive_summary(user_input, additional_statements):
    prompt = f"""
    Generate a compelling Executive Summary that tells the project's story. The summary should:
    
    Style and Tone:
    - Create narrative flow with a clear beginning, middle, and resolution
    - Build subtle tension by highlighting challenges/risks
    - Show how your expertise provides the solution
    - Maintain professional tone while engaging the reader
    - Use active voice and confident language
    
    Key Elements to Weave Together:
    - Current situation and critical challenges
    - Stakes and implications for the client
    - Your unique approach and expertise
    - Implementation strategy
    - Value proposition and expected outcomes
    
    Structure:
    - Opening: Hook reader with context and challenge
    - Middle: Present solution and expertise
    - Close: Highlight benefits and confidence in success
    
    Using this input:
    Project Details: {user_input}
    Additional Context: {additional_statements}
    
    Create a flowing 2-3 paragraph narrative that builds trust while showcasing your understanding and capability.
    Focus on telling a compelling story that demonstrates value and expertise.
    """

    # Generate using GenAI
    response = await generate_content(prompt)
    return response

async def query_vectorstore_two_tier(query, section_type="executive_summary"):
    """Two-tier search approach for different SOW sections"""
    try:
        print(f"\nStarting two-tier search for {section_type}")
        
        # Load vectorstore and add debug prints
        vectorstore = load_vectorstore()
        print(f"Vectorstore loaded: {vectorstore is not None}")
        
        if not vectorstore:
            print("Failed to load vectorstore - returning empty list")
            return []
        
        # First tier: broad context search based on section
        if section_type == "executive_summary":
            broad_query = f"EXECUTIVE SUMMARY Statement of Work water recycling"
            specific_query = f"project goals objectives {query}"
        elif section_type == "services":
            broad_query = f"DESCRIPTION OF SERVICES Statement of Work"
            specific_query = f"technical methodology implementation {query}"
        elif section_type == "deliverables":
            broad_query = f"DESCRIPTION OF DELIVERABLES Statement of Work"
            specific_query = f"project outputs milestones {query}"
        
        print(f"Broad query: {broad_query}")
        print(f"Specific query: {specific_query}")
        
        try:
            # Get more results for both searches
            broad_results = vectorstore.similarity_search(broad_query, k=4)      # Increased from 2 to 4
            print(f"Found {len(broad_results)} broad results")
            
            specific_results = vectorstore.similarity_search(specific_query, k=4) # Increased from 2 to 4
            print(f"Found {len(specific_results)} specific results")
            
            # Combine and allow more total results
            all_results = broad_results + specific_results
            return all_results[:6]  # Increased from 3 to 6
            
        except Exception as e:
            print(f"Error during search: {e}")
            return []
            
    except Exception as e:
        print(f"Error in two-tier search: {e}")
        return []

# Test function to see results
async def test_two_tier_search():
    st.write("Testing Two-Tier Search...")
    
    # Test Executive Summary search
    st.write("\n--- Executive Summary Search ---")
    exec_results = await query_vectorstore_two_tier(
        "water recycling project implementation",
        "executive_summary"
    )
    
    for i, doc in enumerate(exec_results, 1):
        st.write(f"\nDocument {i}:")
        st.write(doc.page_content[:500])
        st.write("-" * 80)
    
    # Test Services search
    st.write("\n--- Services Search ---")
    services_results = await query_vectorstore_two_tier(
        "technical implementation methodology",
        "services"
    )
    
    for i, doc in enumerate(services_results, 1):
        st.write(f"\nDocument {i}:")
        st.write(doc.page_content[:500])
        st.write("-" * 80)
    
    # Test Deliverables search
    st.write("\n--- Deliverables Search ---")
    deliverables_results = await query_vectorstore_two_tier(
        "project outputs and success criteria",
        "deliverables"
    )
    
    for i, doc in enumerate(deliverables_results, 1):
        st.write(f"\nDocument {i}:")
        st.write(doc.page_content[:500])
        st.write("-" * 80)

def test_transcription_robustness():
    print("\n=== Transcription Test Results ===")
    print("Input WebM size:", os.path.getsize('input.webm') if os.path.exists('input.webm') else "File not found")
    print("Output WAV size:", os.path.getsize('output.wav') if os.path.exists('output.wav') else "File not found")
    
    # Add to transcribe_audio function:
    try:
        print("Speech confidence score:", response.results[0].alternatives[0].confidence)
        print("Word-level timing:", response.results[0].alternatives[0].words)
    except:
        pass

def main():
    st.markdown("""
        <style>
            /* Your existing CSS code here */
        </style>
    """, unsafe_allow_html=True)

    initialize_session_state()
    load_environment()

    # Header and Logo
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(current_dir, "static", "RecWater-Solutions-Logo-1.png")
        if os.path.exists(image_path):
            st.image(image_path, width=200)
        else:
            st.error(f"Logo not found. Please ensure 'RecWater-Solutions-Logo-1.png' is in the 'static' folder.")

    with col2:
        st.markdown("<h1 style='text-align: center;'>Statement of Work Generator</h1>", unsafe_allow_html=True)

    st.markdown("---")
    
    st.session_state.input_method = st.radio("Choose input method:", ['Text', 'Audio'])

    # Client Information
    st.subheader("Client Information")
    st.session_state.questions['client']["answer"] = get_audio_input(st.session_state.questions['client']["question"], "client")
    st.session_state.client_address = st.text_input("What is the client's address?", value=st.session_state.get("client_address", ""))
    
    # Date Selection
    default_date = datetime.date.today()
    try:
        if isinstance(st.session_state.effective_date, str):
            default_date = datetime.date.fromisoformat(st.session_state.effective_date)
        elif isinstance(st.session_state.effective_date, datetime.date):
            default_date = st.session_state.effective_date
    except ValueError:
        pass
    st.session_state.effective_date = st.date_input("What is the effective date of this Statement of Work?", value=default_date)

    # General Project Information
    st.subheader("General Project Information")
    for question in st.session_state.questions['general_info']:
        question["answer"] = get_audio_input(question["question"], f"general_{question['id']}")
    
    # Project Details section
    st.subheader("Project Details")
    
    # Multiple phases question
    phases = st.radio(
        "Does this project involve multiple phases?",
        options=["Yes", "No"],
        index=1,
        key="phases"
    )
    
    if phases == "Yes":
        for question in st.session_state.questions['project_details']['phase_details']:
            st.session_state.questions['project_details']['phase_details'][st.session_state.questions['project_details']['phase_details'].index(question)]["answer"] = get_audio_input(question["question"], f"phase_{question['id']}")

    # Technical requirements question
    tech_req = st.radio(
        "Are there specific technical requirements or limits to meet?",
        options=["Yes", "No"],
        index=1,
        key="tech_req"
    )
    
    if tech_req == "Yes":
        for question in st.session_state.questions['project_details']['technical_details']:
            st.session_state.questions['project_details']['technical_details'][st.session_state.questions['project_details']['technical_details'].index(question)]["answer"] = get_audio_input(question["question"], f"tech_{question['id']}")

    # Additional Project Details
    st.subheader("Additional Project Details")
    for question in st.session_state.questions['additional_details']:
        if question["type"] == "radio":
            question["answer"] = st.radio(
                question["question"],
                ["Yes", "No"],
                key=f"additional_{question['id']}",
                index=0 if st.session_state.get(f"additional_{question['id']}") == "Yes" else 1
            )
            if question["answer"] == "Yes":
                for coord_q in st.session_state.questions['coordination_details']:
                    coord_q["answer"] = get_audio_input(coord_q["question"], f"coord_{coord_q['id']}")
        else:
            question["answer"] = get_audio_input(question["question"], f"additional_{question['id']}")

    # Project Costs
    st.markdown("---")
    st.subheader("Project Costs")
    display_labor_costs()

    # Additional Statements
    st.markdown("---")
    st.subheader("Additional Statements")
    additional_statements = get_audio_input("Please provide any additional statements:", "additional_statements")
    if "additional_statements" not in st.session_state or st.session_state.additional_statements != additional_statements:
        st.session_state.additional_statements = additional_statements

    # Additional Terms Conditional
    st.markdown("---")
    st.subheader("Additional Terms")
    has_additional_terms = st.radio("Are there additional terms?", ["No", "Yes"], key="has_additional_terms")
    if has_additional_terms == "Yes":
        additional_terms = st.text_area("Please enter the additional terms:", key="additional_terms_text")
        if additional_terms:
            st.session_state.additional_terms = additional_terms

    # Title and Risk of Loss Conditional
    st.markdown("---")
    st.subheader("Title and Risk of Loss")
    has_title_terms = st.radio("Any change to Title and Risk of Loss?", ["No", "Yes"], key="has_title_terms")
    if has_title_terms == "Yes":
        title_terms = st.text_area("Please enter Title and Risk of Loss terms:", key="title_terms_text")
        if title_terms:
            st.session_state.title_terms = title_terms

    # Schedule Attachments
    st.markdown("---")
    st.subheader("Schedule Attachments")
    st.markdown("Please attach any schedule files, Word docs only (DOCX format):")

    uploaded_files = st.file_uploader("Upload Schedules", 
                                    accept_multiple_files=True,
                                    type=['docx'])

    if uploaded_files:
        st.session_state.attached_schedules = uploaded_files
        st.write("Debug - Uploaded files stored in session state:")
        st.write(f"Number of files: {len(st.session_state.attached_schedules)}")
        for file in st.session_state.attached_schedules:
            st.write(f"- {file.name}")

    # Generate SOW Button
    st.markdown("---")
    if st.button("Generate SOW", key="generate_sow_button"):
        asyncio.run(generate_sow())

    # Display Generated Content
    if st.session_state.generated_content:
        st.subheader("Generated Statement of Work:")
        st.info(st.session_state.generated_content)
        st.markdown("---")

        # Download Options
        col1, col2 = st.columns([1, 3])
        with col1:
            file_format = st.selectbox("Select file format:", ["TXT", "DOCX"])

        try:
            document = create_document(st.session_state.generated_content, file_format)
            st.download_button(
                label=f"Download {file_format}",
                data=document,
                file_name=f"statement_of_work.{file_format.lower()}",
                mime="application/vnd.openxmlformats-office document.wordprocessingml.document" if file_format == "DOCX" else "text/plain"
            )
        except Exception as e:
            st.error(f"An error occurred while creating the {file_format} document: {str(e)}")

    if "audio_data" not in st.session_state:
        st.session_state.audio_data = None

    # Create a placeholder for the transcription
    transcription_placeholder = st.empty()

    # Handle the audio data when received
    if st.session_state.audio_data:
        transcription = handle_audio_data(st.session_state.audio_data)
        if transcription:
            transcription_placeholder.write(f"Transcription: {transcription}")
        st.session_state.audio_data = None  # Clear the audio data

if __name__ == "__main__":
    import sys
    # Check if running directly with Python
    if not sys.argv[0].endswith('streamlit'):
        if len(sys.argv) > 1 and sys.argv[1] == "--init-vectorstore":
            print("Initializing vectorstore...")
            initialize_vectorstore()
            sys.exit(0)
    
    # Normal Streamlit operation
    port = int(os.environ.get("PORT", 8080))
    main()