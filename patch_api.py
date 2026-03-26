import sys

with open('awaaz/api_server.py', 'r') as f:
    orig = f.read()

s1 = """    text: str = Query(..., description="Text to synthesize"),
    language: str = Query(..., description="Language code (e.g., 'hi', 'pa', 'en')"),
    speaker: str = Query(
        "ritu", description="Speaker voice (e.g., 'ritu' for female)"
    ),
    background_tasks: BackgroundTasks = BackgroundTasks(),
) -> TTSJob:"""
r1 = """    text: str = Query(..., description="Text to synthesize"),
    language: str = Query(..., description="Language code (e.g., 'hi', 'pa', 'en')"),
    speaker: str = Query(
        "ritu", description="Speaker voice (e.g., 'ritu' for female)"
    ),
    intent: Optional[str] = Query(None, description="Intent for emotional context (e.g., 'COMPLAINT')"),
    anger_score: Optional[float] = Query(None, description="Anger score (0.0 to 1.0)"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
) -> TTSJob:"""

orig = orig.replace(s1, r1)

s2 = """    job_manager.update_job_status(
        tts_job_id,
        ProcessingStatus.PROCESSING,
        input_text=text,
        language=language,
        speaker=speaker,
    )

    # Schedule background processing
    background_tasks.add_task(
        _synthesize_tts_background, tts_job_id, text, language, speaker
    )"""

r2 = """    job_manager.update_job_status(
        tts_job_id,
        ProcessingStatus.PROCESSING,
        input_text=text,
        language=language,
        speaker=speaker,
        intent=intent,
        anger_score=anger_score
    )

    # Schedule background processing
    background_tasks.add_task(
        _synthesize_tts_background, tts_job_id, text, language, speaker, intent, anger_score
    )"""
orig = orig.replace(s2, r2)

s3 = """async def _synthesize_tts_background(
    job_id: str, text: str, language: str, speaker: str
):
    \"\"\"Background task for TTS synthesis.\"\"\""""
r3 = """async def _synthesize_tts_background(
    job_id: str, text: str, language: str, speaker: str, intent: Optional[str] = None, anger_score: Optional[float] = None
):
    \"\"\"Background task for TTS synthesis.\"\"\""""
orig = orig.replace(s3, r3)

s4 = """        # Generate speech
        output_path = str(OUTPUT_DIR / f"{job_id}.wav")
        await tts_processor.synthesize(
            text=text,
            language=language,
            output_path=output_path,
        )"""

r4 = """        # Generate speech
        output_path = str(OUTPUT_DIR / f"{job_id}.wav")
        
        class MockSession:
            pass
        session = MockSession()
        session.intent = intent
        session.anger_score = anger_score or 0.0
        session.lang = language
        
        await tts_processor.synthesize(
            text=text,
            language=language,
            output_path=output_path,
            session=session
        )"""

orig = orig.replace(s4, r4)

with open('awaaz/api_server.py', 'w') as f:
    f.write(orig)

print("Patch applied.")