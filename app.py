from flask import Flask, render_template, request, jsonify
import base64 
import os 
from openai import AzureOpenAI 
from dotenv import load_dotenv
import io
from pdf2image import convert_from_bytes
import PyPDF2
import logging
import asyncio
from tools import get_summary_card_tool, process_summary_card
from history import HistoryManager
from datetime import datetime
from config import AZURE_CONFIG, AZURE_MODELS, MAX_FILE_SIZE, ALLOWED_EXTENSIONS

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Load environment variables
load_dotenv('keys.env')

# Initialize Azure OpenAI client
client = AzureOpenAI(
    api_version=AZURE_CONFIG['api_version'],
    api_key=AZURE_CONFIG['api_key'],
    azure_endpoint=AZURE_CONFIG['azure_endpoint']
)

# Initialize history manager
history_manager = HistoryManager()

# Voice style mappings
VOICE_STYLE_PROMPTS = {
    'contemplating_british': """You are an expert voice actor specializing in silly voices. Respond and vocalize to the user the EXACT same input text, but in your voice response you MUST express EACH of the vocal cadence, inflection, and tone of David Attenborough.""",
    
    'curious_american': """You are an expert voice actor specializing in silly voices. Respond and vocalize to the user the EXACT same input text, but in your voice response you MUST express EACH of the vocal cadence, inflection, and tone of Bill Nye the Science Guy.""",
    
    'energetic_host': """You are an expert voice actor specializing in silly voices. Respond and vocalize to the user the EXACT same input text, but in your voice response you MUST express EACH of the vocal cadence, inflection, and tone of Jimmy Fallon.""",
    
    'thoughtful_journalist': """You are an expert voice actor specializing in silly voices. Respond and vocalize to the user the EXACT same input text, but in your voice response you MUST express EACH of the vocal cadence, inflection, and tone of Morgan Freeman.""",
    
    'friendly_interviewer': """You are an expert voice actor specializing in silly voices. Respond and vocalize to the user the EXACT same input text, but in your voice response you MUST express EACH of the vocal cadence, inflection, and tone of Oprah Winfrey.""",
    
    'authoritative_professor': """You are an expert voice actor specializing in silly voices. Respond and vocalize to the user the EXACT same input text, but in your voice response you MUST express EACH of the vocal cadence, inflection, and tone of Neil deGrasse Tyson.""",
    
    'passionate_expert': """You are an expert voice actor specializing in silly voices. Respond and vocalize to the user the EXACT same input text, but in your voice response you MUST express EACH of the vocal cadence, inflection, and tone of Tony Robbins.""",
    
    'analytical_researcher': """You are an expert voice actor specializing in silly voices. Respond and vocalize to the user the EXACT same input text, but in your voice response you MUST express EACH of the vocal cadence, inflection, and tone of Carl Sagan.""",
    
    'experienced_practitioner': """You are an expert voice actor specializing in silly voices. Respond and vocalize to the user the EXACT same input text, but in your voice response you MUST express EACH of the vocal cadence, inflection, and tone of Gordon Ramsay.""",
    
    'industry_veteran': """You are an expert voice actor specializing in silly voices. Respond and vocalize to the user the EXACT same input text, but in your voice response you MUST express EACH of the vocal cadence, inflection, and tone of Steve Jobs.""",
    
    'pirate_interviewer': """You are an expert voice actor specializing in silly voices. Respond and vocalize to the user the EXACT same input text, but in your voice response you MUST express EACH of the vocal cadence, inflection, and tone of Johnny Depp as Jack Sparrow.""",
    
    'vampire_expert': """You are an expert voice actor specializing in silly voices. Respond and vocalize to the user the EXACT same input text, but in your voice response you MUST express EACH of the vocal cadence, inflection, and tone of Christopher Lee as Count Dracula."""
}

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx'}

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()  # This will print to console as well
    ]
)
logger = logging.getLogger(__name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf_hybrid(pdf_bytes):
    try:
        # First try to extract text directly using PyPDF2
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        num_pages = len(pdf_reader.pages)
        logger.info(f'PDF has {num_pages} pages')
        
        text = ""
        for page_num, page in enumerate(pdf_reader.pages, 1):
            logger.info(f'Processing page {page_num}/{num_pages}')
            page_text = page.extract_text()
            if page_text.strip():
                text += page_text + "\n"
        
        # If we got meaningful text, return it
        if len(text.strip()) > 500:  # Arbitrary threshold
            logger.info(f'Successfully extracted {len(text)} characters directly from PDF. Using text extraction.')
            return text
        else:
            logger.info(f'Only extracted {len(text.strip())} characters, which is below threshold of 500. Falling back to vision.')

        # If direct extraction didn't get enough text, fall back to vision approach
        logger.info('Direct text extraction insufficient, falling back to vision approach')
        return extract_text_from_pdf_vision(pdf_bytes)

    except Exception as e:
        logger.error(f'Error in hybrid PDF processing: {str(e)}', exc_info=True)
        raise Exception(f"Could not process PDF: {str(e)}")

async def process_page_vision(client, image, page_num, total_pages):
    try:
        logger.info(f'Processing page {page_num}/{total_pages}')
        
        # Convert image to PNG and base64
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        img_base64 = base64.b64encode(img_byte_arr).decode('utf-8')
        logger.info(f'Page {page_num} converted to PNG and base64 encoded')
    
        # Send to text / vision model
        logger.info(f'Sending page {page_num} to {AZURE_MODELS["text"]}')
        
        # Create a semaphore to limit concurrent API calls
        sem = asyncio.Semaphore(10)
        
        async with sem:
            completion = await asyncio.to_thread(
                client.chat.completions.create,
                model=AZURE_MODELS['text'],
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Please read this document and extract all the text you see in a clear format. Also describe graphs, images, and tables in a clear format."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{img_base64}"
                                }
                            }
                        ]
                    }
                ]
            )
        
        page_text = completion.choices[0].message.content
        logger.info(f'Successfully received text for page {page_num}')
        return page_num, page_text
    except Exception as e:
        logger.error(f'Error processing page {page_num}: {str(e)}', exc_info=True)
        raise

def extract_text_from_pdf_vision(pdf_bytes):
    try:
        # Convert PDF pages to images
        logger.info('Converting PDF to images')
        images = convert_from_bytes(pdf_bytes)
        
        if not images:
            raise Exception("Could not convert PDF to images")
            
        logger.info(f'Successfully converted PDF to {len(images)} images')
        
        # Create an event loop for async operations
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Process all pages concurrently with a semaphore limit of 10
        total_pages = len(images)
        tasks = []
        for idx, image in enumerate(images, start=1):
            task = process_page_vision(client, image, idx, total_pages)
            tasks.append(task)
        
        # Run all tasks concurrently
        logger.info(f'Processing all pages concurrently (max 10 at a time)')
        all_results = loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
        
        # Handle any exceptions and collect successful results
        processed_results = []
        for result in all_results:
            if isinstance(result, Exception):
                logger.error(f'Page processing error: {str(result)}')
                continue
            processed_results.append(result)
        
        # Sort results by page number and extract text
        processed_results.sort(key=lambda x: x[0])  # Sort by page number
        all_text = [text for _, text in processed_results]
        
        # Combine text from all pages
        final_text = "\n\n=== Page Break ===\n\n".join(all_text)
        logger.info(f'Successfully processed all {len(processed_results)} pages')
        logger.info(f'Final text:\n{final_text}')
        
        # Close the event loop
        loop.close()
        
        return final_text

    except Exception as e:
        logger.error(f'Error in vision PDF processing: {str(e)}', exc_info=True)
        raise Exception(f"Could not process PDF: {str(e)}")

def summarize_text(text, target_minutes, tone, language, goal, goal_instruction=None, voice1_style=None, voice2_style=None):
    try:
        # Add logging at the start of summarize_text
        logger.info(f"summarize_text called with:")
        logger.info(f"  target_minutes: {target_minutes}")
        logger.info(f"  tone: {tone}")
        logger.info(f"  language: {language}")
        logger.info(f"  goal: {goal}")
        if goal == "custom":
            logger.info(f"  goal_instruction: {goal_instruction}")
        if goal == "podcast":
            logger.info(f"  voice1_style: {voice1_style}")
            logger.info(f"  voice2_style: {voice2_style}")
        
        # Create a mapping for proper language names
        language_mapping = {
            'english': 'English',
            'spanish': 'Spanish',
            'french': 'French',
            'german': 'German',
            'italian': 'Italian',
            'portuguese': 'Portuguese',
            'dutch': 'Dutch',
            'polish': 'Polish',
            'japanese': 'Japanese',
            'chinese': 'Chinese',
            'korean': 'Korean',
            'swedish': 'Swedish'
        }
        
        # Get proper language name or default to English
        target_language = language_mapping.get(language.lower(), 'English')
        logger.info(f"  Mapped language '{language}' to '{target_language}'")
        
        logger.info(f'Starting text summarization for {target_minutes} minute(s) in {tone} tone, language: {target_language}')
        logger.info(f'Input text length: {len(text)} characters')
        
        # Assuming average speaking rate of 150 words per minute
        target_words = target_minutes * 110
        
        # Add tone-specific instructions
        tone_instructions = {
            'professional': "Use clear, precise language with business-appropriate terminology.",
            'conversational': "Use natural, friendly language as if speaking to a friend.",
            'enthusiastic': "Use energetic and engaging language with dynamic expressions.",
            'formal': "Use sophisticated vocabulary and academic language.",
            'casual': "Use relaxed, everyday language and a laid-back style.",
            'empathetic': "Use warm, understanding language that shows emotional awareness."
        }
        
        # Add goal-specific instructions
        goal_instructions = {
            'general_summary': "Create a comprehensive overview of the main points and key takeaways from the document.",
            'key_insights': "Focus on extracting and highlighting the most important insights, findings, and key points from the document.",
            'action_items': "Identify and list the main action items, tasks, and next steps mentioned in the document.",
            'topic_analysis': "Analyze the document with a focus on the specific topic or aspect requested.",
            'recommendations': "Extract and elaborate on the recommendations, suggestions, and proposed solutions from the document.",
            'podcast': f"""Create an engaging conversation about the document between two people:
Speaker 1 ({VOICE_STYLE_PROMPTS[voice1_style] if voice1_style else 'contemplating_british'}): Ask insightful questions about the content.
Speaker 2 ({VOICE_STYLE_PROMPTS[voice2_style] if voice2_style else 'authoritative_professor'}): Provide detailed, informative answers.
Make it feel like a natural podcast discussion while covering the key points from the document. When creating the summary put emphasis on the speak tone like  voice)"""
        }
        
        tone_instruction = tone_instructions.get(tone, tone_instructions['conversational']) if goal != 'podcast' else ""
        goal_instruction = goal_instructions.get(goal, goal_instruction if goal == "custom" else "Analyze the document according to this specific goal: " + goal)
        
        # Add language-specific instruction
        language_instruction = f"The summary must be written entirely in {target_language}. Do not use any other language."
        
        completion = client.chat.completions.create(
            model=AZURE_MODELS['text'],
            messages=[
                {
                    "role": "system",
                    "content": f"""You are a specialized document analyzer. {language_instruction}

Your task: {goal_instruction}

Format your response as a clear, engaging summary that takes approximately {target_minutes} minute(s) to read aloud (about {target_words} words). {tone_instruction}

Focus on delivering content that precisely matches the specified goal while maintaining a natural speaking flow. The summary should be like a script for audiobook narrator.
For every 100 words, make a page break, write out === Page Break === """
                },
                {
                    "role": "user",
                    "content": f"Please analyze this text in {target_language}, focusing on the specified goal and aiming for approximately {target_words} words:\n\n{text}"
                }
            ]
        )
        
        summary = completion.choices[0].message.content
        logger.info(f'Successfully generated {tone} summary in {target_language} (length: {len(summary)} characters)')
        logger.info(f'Summary:\n{summary}')
        return summary
        
    except Exception as e:
        logger.error(f'Error summarizing text: {str(e)}', exc_info=True)
        return None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload-document', methods=['POST'])
def upload_document():
    try:
        # Add detailed logging of all form data
        logger.info("Received form data:")
        for key, value in request.form.items():
            logger.info(f"  {key}: {value}")

        # Check if this is a rerun
        rerun_text = request.form.get('rerun_text')
        if rerun_text:
            logger.info("Processing rerun request with existing text")
            text = rerun_text
            # For reruns, we'll keep the original filename from the request
            original_filename = request.form.get('original_filename', 'Unknown Document')
        else:
            # Normal file processing
            if 'file' not in request.files:
                logger.warning('No file part in request')
                return jsonify({'status': 'error', 'message': 'No file uploaded'}), 400
            
            file = request.files['file']
            processing_method = request.form.get('processing_method', 'vision')
            
            if file.filename == '':
                logger.warning('No selected file')
                return jsonify({'status': 'error', 'message': 'No file selected'}), 400
            
            if not allowed_file(file.filename):
                logger.warning(f'Invalid file type: {file.filename}')
                return jsonify({'status': 'error', 'message': 'File type not allowed'}), 400

            logger.info(f'Processing file: {file.filename} using {processing_method} method')
            original_filename = file.filename
            
            # Read the file
            file_bytes = file.read()
            file_size = len(file_bytes) / 1024  # Size in KB
            logger.info(f'File size: {file_size:.2f} KB')
            
            # Extract text based on file type and processing method
            if file.filename.endswith('.pdf'):
                logger.info('Processing PDF file')
                if processing_method == 'vision':
                    text = extract_text_from_pdf_vision(file_bytes)
                else:
                    text = extract_text_from_pdf_hybrid(file_bytes)
            else:  # For txt files
                logger.info('Processing TXT file')
                text = file_bytes.decode('utf-8')

        if not text:
            logger.error('Text extraction failed')
            return jsonify({'status': 'error', 'message': 'Could not extract text from file'}), 400

        logger.info(f'Successfully extracted/received text (length: {len(text)} characters)')

        # Get processing parameters
        summary_length = int(request.form.get('summary_length', '2'))
        tone = request.form.get('tone', 'conversational')
        language = request.form.get('language', 'english')
        goal = request.form.get('goal', 'general_summary')
        goal_instruction = request.form.get('goal_instruction') if goal == 'custom' else None
        voice1_style = request.form.get('voice1_style', 'contemplating_british') if goal == 'podcast' else None
        voice2_style = request.form.get('voice2_style', 'authoritative_professor') if goal == 'podcast' else None

        # Summarize the text with target length
        logger.info(f'Starting text summarization for {summary_length} minute(s)')
        summary = summarize_text(text, summary_length, tone, language, goal, goal_instruction, voice1_style, voice2_style)
        if not summary:
            logger.error('Summarization failed')
            return jsonify({'status': 'error', 'message': 'Could not summarize text'}), 500

        logger.info(f'Successfully generated {summary_length}-minute summary (length: {len(summary)} characters)')

        # Generate audio from summary
        logger.info('Starting audio generation')
        voice = request.form.get('voice', 'alloy')
        logger.info(f'Using voice: {voice}')

        # First, get the formatted summary
        logger.info('Creating formatted summary card')
        format_completion = client.chat.completions.create(
            model=AZURE_MODELS['text'],
            messages=[
                {
                    "role": "system",
                    "content": f"You are a content formatter. Create a beautifully formatted summary card using the create_summary_card tool. Format the content according to the goal: {goal if goal != 'custom' else goal_instruction}"
                },
                {
                    "role": "user",
                    "content": summary
                }
            ],
            tools=[get_summary_card_tool(goal, goal_instruction)],
            tool_choice="required"
        )

        # Process the tool calls to create formatted summary
        formatted_summary = summary
        if hasattr(format_completion.choices[0].message, 'tool_calls') and format_completion.choices[0].message.tool_calls:
            tool_call = format_completion.choices[0].message.tool_calls[0]
            if tool_call.function.name == "create_summary_card":
                formatted_summary = process_summary_card(tool_call, goal, goal_instruction)

        # Generate audio chunks
        summary_chunks = summary.split("=== Page Break ===")
        summary_chunks = [chunk.strip() for chunk in summary_chunks if chunk.strip()]
        logger.info(f'Split summary into {len(summary_chunks)} chunks')
        
        audio_chunks = []
        for i, chunk in enumerate(summary_chunks):
            logger.info(f'Processing chunk {i+1}/{len(summary_chunks)}')
            chunk_completion = client.chat.completions.create(
                model=AZURE_MODELS['audio'],
                messages=[
                    {
                        "role": "system",
                        "content": [
                            {
                                "type": "text",
                                "text": f"""You are a professional audiobook reader. Your task is to read the provided text in {language}, ensuring it remains engaging throughout.

- **Language**: {language}
- **Voice**: {voice}
{f'- **Voice Style**: For Speaker 1 use: {VOICE_STYLE_PROMPTS[voice1_style]}, For Speaker 2 use: {VOICE_STYLE_PROMPTS[voice2_style]} this is VERY IMPORTANT' if goal == 'podcast' else f'- **Tone**: {tone}'}

# Output Format
Produce an engaging {'podcast' if goal == 'podcast' else 'audiobook narration'} in {language}, maintaining the specified {'voice style but do not read (SPEAKER etc out load), it is VERY IMPORTANT you adhere to the voice styles for each speaker' if goal == 'podcast' else 'tone'} and read the text WORD for WORD."""
                            }
                        ]
                    },
                    {
                        "role": "user",
                        "content": chunk
                    }
                ],
                modalities=["text", "audio"],
                audio={"voice": voice, "format": "wav"},
                temperature=1.2,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )
            
            audio_data = base64.b64decode(chunk_completion.choices[0].message.audio.data)
            audio_chunks.append(audio_data)
            logger.info(f'Successfully generated audio for chunk {i+1}')

        # Combine audio chunks
        logger.info('Combining audio chunks')
        from pydub import AudioSegment
        import io

        combined_audio = AudioSegment.empty()
        for audio_data in audio_chunks:
            audio_segment = AudioSegment.from_wav(io.BytesIO(audio_data))
            combined_audio += audio_segment

        combined_audio_bytes = io.BytesIO()
        combined_audio.export(combined_audio_bytes, format='wav')
        combined_audio_base64 = base64.b64encode(combined_audio_bytes.getvalue()).decode('utf-8')
        logger.info('Successfully combined all audio chunks')

        # Save to history (always save, whether it's a rerun or not)
        history_metadata = {
            'summary_length': summary_length,
            'tone': tone,
            'language': language,
            'goal': goal,
            'goal_instruction': goal_instruction if goal == 'custom' else None,
            'voice': voice,
            'processing_method': request.form.get('processing_method', 'vision') if not rerun_text else 'rerun'
        }
        
        history_manager.save_entry(
            audio_data=combined_audio_base64,
            summary_html=formatted_summary,
            original_filename=original_filename,
            metadata=history_metadata,
            extracted_text=text
        )

        logger.info('Successfully generated audio and formatted summary')
        return jsonify({
            'status': 'success',
            'audio_data': combined_audio_base64,
            'text_response': formatted_summary
        })

    except Exception as e:
        logger.error(f'Error in upload_document: {str(e)}', exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/history', methods=['GET'])
def get_history():
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        offset = (page - 1) * limit
        include_text = request.args.get('include_text', 'false').lower() == 'true'
        
        entries = history_manager.get_entries(limit=limit, offset=offset, include_text=include_text)
        return jsonify({
            'status': 'success',
            'entries': entries
        })
    except Exception as e:
        logger.error(f'Error getting history: {str(e)}', exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/history/text/<entry_id>', methods=['GET'])
def get_entry_text(entry_id):
    try:
        text = history_manager.get_entry_text(entry_id)
        if text:
            return jsonify({
                'status': 'success',
                'text': text
            })
        return jsonify({'status': 'error', 'message': 'Entry not found'}), 404
    except Exception as e:
        logger.error(f'Error getting entry text: {str(e)}', exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/history/<entry_id>', methods=['DELETE'])
def delete_history_entry(entry_id):
    """Delete a specific history entry"""
    try:
        history_manager = HistoryManager()
        success = history_manager.delete_entry(entry_id)
        if success:
            return jsonify({"status": "success", "message": "Entry deleted successfully"})
        else:
            return jsonify({"status": "error", "message": "Entry not found"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001) 