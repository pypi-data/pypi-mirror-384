#!/usr/bin/env python3
"""
Test bilingual image generation for curriculum questions using English/Arabic test questions
"""

import asyncio
import csv
import os
import pytest
import logging
import json
import time
from src.image_generation.image_generation_agent import ImageGenerationAgent
from src.config import Config
from tests.test_questions_en_ar import TEST_QUESTIONS

logger = logging.getLogger(__name__)

# Configure logging for pytest
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

# Force enable image generation for testing
Config.ENABLE_IMAGE_GENERATION = True

curriculum_mcqs = TEST_QUESTIONS


@pytest.mark.asyncio
async def test_curriculum_questions_bilingual():
    """Test bilingual image generation for all curriculum questions"""
    
    # Initialize the image generation agent
    agent = ImageGenerationAgent()
    
    # JSON file path - use absolute path to ensure consistency
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    json_path = os.path.join(project_root, "data", "imagen.json")
    
    logger.info(f"JSON path: {json_path}")
    
    # Ensure data directory exists
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    
    # Load existing questions to skip
    existing_questions = set()
    existing_data = []
    
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r') as f:
                existing_data = json.load(f)
                logger.info(f"Loaded {len(existing_data)} total entries from JSON")
                
                for item in existing_data:
                    question_text = item.get('question', '')
                    logger.debug(f"Processing JSON entry: '{question_text[:50]}...'")
                    
                    # Check if this question already has agent_v1_ar generator
                    if 'agent_v1_ar' in item:
                        existing_questions.add((question_text, 'agent_v1_ar'))
                        logger.debug(f"  ✅ Added to existing_questions: '{question_text[:30]}...'")
                    else:
                        logger.debug(f"  ⏸️  No agent_v1_ar entry for: '{question_text[:30]}...'")
                        
            logger.info(f"Found {len(existing_questions)} existing questions with agent_v1_ar in JSON")
            logger.info("First 5 existing questions:")
            for i, (q, gen) in enumerate(list(existing_questions)[:5]):
                logger.info(f"  {i+1}. '{q[:50]}...' ({gen})")
                
        except json.JSONDecodeError:
            logger.warning("JSON file exists but is empty or invalid, starting fresh")
            existing_data = []
    else:
        logger.info("JSON file doesn't exist, will create it")
        # Create empty JSON file
        with open(json_path, 'w') as f:
            json.dump([], f)
    
    # Process each grade level
    for grade_level, topics in curriculum_mcqs.items():
        logger.info(f"\n{'='*50}")
        logger.info(f"Testing Grade: {grade_level}")
        logger.info(f"{'='*50}")
        
        # Process each topic in the grade
        for topic, question_data in topics.items():
            # Extract English and Arabic questions
            if isinstance(question_data, dict) and 'english' in question_data and 'arabic' in question_data:
                english_question = question_data['english']
                arabic_question = question_data['arabic']
            else:
                logger.warning(f"Skipping malformed question data for topic '{topic}': {question_data}")
                continue
                
            # Check if this English question already exists with the same generator
            if (english_question, 'agent_v1_ar') in existing_questions:
                logger.info(f"\n⏭️  Skipping (already exists): {english_question}")
                continue
                
            logger.info(f"\nTopic: {topic}")
            logger.info(f"English Question: {english_question}")
            logger.info(f"Arabic Question: {arabic_question}")
            
            try:
                # Determine grade number for agent
                if grade_level.startswith("Grade"):
                    grade = int(grade_level.split()[1])
                else:
                    # For non-numeric grades, default to 12
                    grade = 12
                
                # Generate image using Arabic question
                logger.info("Generating image...")
                start_time = time.time()
                image_url = await agent.generate_image_for_question(
                    question=arabic_question,
                    grade=grade,
                    subject="mathematics"
                )
                end_time = time.time()
                time_taken = end_time - start_time
                
                if image_url:
                    logger.info(f"✅ Success! Image URL: {image_url}")
                    # Check if it's a local file path or Supabase URL
                    if not image_url.startswith('http'):
                        logger.warning(f"⚠️  Got local file path instead of URL: {image_url}")
                    
                    # Append to JSON
                    try:
                        # Re-read latest file before updating
                        if os.path.exists(json_path):
                            with open(json_path, 'r') as f:
                                existing_data = json.load(f)
                        else:
                            existing_data = []
                        
                        # Find existing entry or create new one
                        existing_entry = None
                        for entry in existing_data:
                            if entry['question'] == english_question:
                                existing_entry = entry
                                break
                        
                        if existing_entry:
                            # Update agent_v1_ar and add Arabic question, preserve all other fields
                            existing_entry['agent_v1_ar'] = {
                                "image_url": image_url,
                                "time_taken": round(time_taken, 2),
                                "quality_feedback": "No quality check performed"
                            }
                            # Add Arabic question field
                            existing_entry['question_arabic'] = arabic_question
                        else:
                            # Create new entry with required fields including Arabic question
                            new_entry = {
                                'question': english_question,
                                'question_arabic': arabic_question,
                                'grade': grade_level,
                                'topic': topic,
                                'agent_v1_ar': {
                                    "image_url": image_url,
                                    "time_taken": round(time_taken, 2),
                                    "quality_feedback": "No quality check performed"
                                }
                            }
                            existing_data.append(new_entry)
                        
                        # Write entire JSON file
                        with open(json_path, 'w') as f:
                            json.dump(existing_data, f, indent=2, ensure_ascii=False)
                        
                        logger.info(f"✅ Saved to JSON: {json_path}")
                        logger.info(f"JSON now has {len(existing_data)} entries")
                    except Exception as e:
                        logger.error(f"Failed to write to JSON: {e}")
                else:
                    logger.error("❌ Failed to generate image")
                    
            except Exception as e:
                logger.error(f"❌ Error: {e}")
            
            # Delay between requests to avoid rate limiting
            await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(test_curriculum_questions_bilingual())