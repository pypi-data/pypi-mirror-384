"""
AI-Human Collaboration MCP Tools

Tools enabling real-time communication and interactive element selection
between AI models and human users during browser automation.
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

from ..collaboration import CollaborationMessaging, ElementInspector, UserPrompts
from ..collaboration.voice_communication import VoiceCommunication, VoiceSettings
from ..context import Context

class SendMessageParams(BaseModel):
    """Parameters for sending messages to users"""
    text: str = Field(description="Message text to display to user")
    message_type: str = Field(default="info", description="Message type: info, success, warning, error")
    duration: int = Field(default=5000, description="Duration in milliseconds (0 = persistent)")
    title: Optional[str] = Field(default=None, description="Optional title for the message")

class UserPromptParams(BaseModel):
    """Parameters for user confirmation prompts"""
    message: str = Field(description="Question or confirmation message")
    title: Optional[str] = Field(default=None, description="Dialog title")
    confirm_text: str = Field(default="CONFIRM", description="Text for confirm button")
    cancel_text: str = Field(default="CANCEL", description="Text for cancel button")
    danger_level: str = Field(default="normal", description="Danger level: safe, normal, destructive")

class ElementSelectionParams(BaseModel):
    """Parameters for interactive element selection"""
    instructions: str = Field(description="Instructions to show user for element selection")
    timeout: int = Field(default=60000, description="Timeout in milliseconds")

class FormFieldSelectionParams(BaseModel):
    """Parameters for collaborative form field selection"""
    field_names: List[str] = Field(description="List of form field names to select")

class VoiceSpeakParams(BaseModel):
    """Parameters for AI text-to-speech"""
    text: str = Field(description="Text for AI to speak aloud")
    rate: float = Field(default=1.0, description="Speech rate (0.1 to 2.0)")
    pitch: float = Field(default=1.0, description="Speech pitch (0.0 to 2.0)")
    volume: float = Field(default=0.8, description="Speech volume (0.0 to 1.0)")
    voice_name: Optional[str] = Field(default=None, description="Specific voice to use")
    language: str = Field(default="en-US", description="Speech language")

class VoiceListenParams(BaseModel):
    """Parameters for listening to user voice"""
    timeout: int = Field(default=30000, description="Timeout in milliseconds")
    continuous: bool = Field(default=False, description="Continuous listening mode")

class VoiceQuestionParams(BaseModel):
    """Parameters for voice Q&A"""
    question: str = Field(description="Question to ask the user aloud")
    timeout: int = Field(default=30000, description="Timeout for user response")
    rate: float = Field(default=1.0, description="Speech rate for question")
    voice_name: Optional[str] = Field(default=None, description="Voice to use for question")

async def browser_collaboration_send_message(
    context: Context,
    params: SendMessageParams
) -> Dict[str, Any]:
    """
    Send a real-time message to the user during browser automation.
    
    Features cyberpunk-themed notifications with auto-dismiss functionality.
    Useful for providing status updates, warnings, or information to users.
    """
    
    page = await context.get_current_page()
    messaging = CollaborationMessaging()
    
    # Initialize messaging system if not already done
    await messaging.initialize(page)
    
    # Send message with specified parameters
    await messaging.send_message(
        page,
        params.text,
        params.message_type,  # type: ignore
        params.duration,
        params.title
    )
    
    return {
        "status": "message_sent",
        "text": params.text,
        "type": params.message_type,
        "duration": params.duration
    }

async def browser_collaboration_request_confirmation(
    context: Context,
    params: UserPromptParams
) -> Dict[str, Any]:
    """
    Request user confirmation before proceeding with an action.
    
    Shows interactive modal dialog with cyberpunk styling. User can confirm
    or cancel using buttons or ESC key. Essential for sensitive operations.
    """
    
    page = await context.get_current_page()
    prompts = UserPrompts()
    
    # Initialize prompt system if not already done
    await prompts.initialize(page)
    
    if params.danger_level in ["safe", "normal", "destructive"]:
        # Use permission helper for standardized danger level handling
        confirmed = await prompts.ask_permission(
            page,
            params.message,
            params.danger_level
        )
    else:
        # Use custom prompt with user-specified button text
        confirmed = await prompts.confirm(
            page,
            params.message,
            params.title,
            params.confirm_text,
            params.cancel_text
        )
    
    return {
        "status": "user_responded",
        "confirmed": confirmed,
        "message": params.message,
        "danger_level": params.danger_level
    }

async def browser_collaboration_select_element(
    context: Context,
    params: ElementSelectionParams
) -> Dict[str, Any]:
    """
    Request user to interactively select an element on the page.
    
    Activates visual element inspector with highlighting. User clicks on
    desired element to get detailed information including XPath, attributes,
    and positioning data. Revolutionary feature for precise automation.
    """
    
    page = await context.get_current_page()
    inspector = ElementInspector()
    
    # Initialize inspector system if not already done
    await inspector.initialize(page)
    
    # Start element selection and wait for user input
    element_details = await inspector.start_inspection(
        page,
        params.instructions,
        params.timeout
    )
    
    if element_details is None:
        return {
            "status": "cancelled",
            "message": "User cancelled element selection"
        }
    
    return {
        "status": "element_selected",
        "element": {
            "tag_name": element_details.tag_name,
            "id": element_details.id,
            "class_name": element_details.class_name,
            "text_content": element_details.text_content,
            "xpath": element_details.xpath,
            "attributes": element_details.attributes,
            "bounding_rect": element_details.bounding_rect,
            "visible": element_details.visible
        }
    }

async def browser_collaboration_form_field_selection(
    context: Context,
    params: FormFieldSelectionParams
) -> Dict[str, Any]:
    """
    Guide user through selecting multiple form fields in sequence.
    
    Streamlines form automation by having user identify each field
    (email, password, submit button, etc.) in order. Returns detailed
    element information for each field for precise automation.
    """
    
    page = await context.get_current_page()
    inspector = ElementInspector()
    messaging = CollaborationMessaging()
    
    # Initialize systems
    await inspector.initialize(page)
    await messaging.initialize(page)
    
    # Notify user about the form field selection process
    await messaging.notify_info(
        page, 
        f"I'll guide you through selecting {len(params.field_names)} form fields",
        "🤖 FORM FIELD SELECTION"
    )
    
    # Collect form field elements
    field_elements = await inspector.collaborative_form_filling(
        page,
        params.field_names
    )
    
    # Convert results for JSON response
    results = {}
    selected_count = 0
    
    for field_name, element_details in field_elements.items():
        if element_details is not None:
            results[field_name] = {
                "tag_name": element_details.tag_name,
                "id": element_details.id,
                "class_name": element_details.class_name,
                "text_content": element_details.text_content,
                "xpath": element_details.xpath,
                "attributes": element_details.attributes,
                "bounding_rect": element_details.bounding_rect,
                "visible": element_details.visible
            }
            selected_count += 1
        else:
            results[field_name] = None
    
    # Notify completion
    if selected_count == len(params.field_names):
        await messaging.notify_success(
            page,
            f"Successfully identified all {selected_count} form fields!",
            "✅ FORM MAPPING COMPLETE"
        )
    else:
        await messaging.notify_warning(
            page,
            f"Selected {selected_count} of {len(params.field_names)} fields",
            "⚠️ INCOMPLETE SELECTION"
        )
    
    return {
        "status": "form_fields_mapped",
        "total_fields": len(params.field_names),
        "selected_fields": selected_count,
        "field_elements": results
    }

async def browser_collaboration_notify_info(
    context: Context,
    text: str,
    title: Optional[str] = None
) -> Dict[str, Any]:
    """Send an info notification to the user (5s auto-dismiss)"""
    
    page = await context.get_current_page()
    messaging = CollaborationMessaging()
    await messaging.initialize(page)
    await messaging.notify_info(page, text, title)
    
    return {"status": "info_sent", "text": text}

async def browser_collaboration_notify_success(
    context: Context,
    text: str,
    title: Optional[str] = None
) -> Dict[str, Any]:
    """Send a success notification to the user (3s auto-dismiss)"""
    
    page = await context.get_current_page()
    messaging = CollaborationMessaging()
    await messaging.initialize(page)
    await messaging.notify_success(page, text, title)
    
    return {"status": "success_sent", "text": text}

async def browser_collaboration_notify_warning(
    context: Context,
    text: str,
    title: Optional[str] = None
) -> Dict[str, Any]:
    """Send a warning notification to the user (4s auto-dismiss)"""
    
    page = await context.get_current_page()
    messaging = CollaborationMessaging()
    await messaging.initialize(page)
    await messaging.notify_warning(page, text, title)
    
    return {"status": "warning_sent", "text": text}

async def browser_collaboration_notify_error(
    context: Context,
    text: str,
    title: Optional[str] = None
) -> Dict[str, Any]:
    """Send an error notification to the user (6s auto-dismiss)"""
    
    page = await context.get_current_page()
    messaging = CollaborationMessaging()
    await messaging.initialize(page)
    await messaging.notify_error(page, text, title)
    
    return {"status": "error_sent", "text": text}

# Voice Communication Tools

async def browser_voice_speak(
    context: Context,
    params: VoiceSpeakParams
) -> Dict[str, Any]:
    """
    Have the AI speak text aloud to the user using text-to-speech.
    
    Revolutionary voice communication feature enabling AI to speak directly
    to users during browser automation. Uses Web Speech API for natural
    voice synthesis with configurable speech parameters.
    
    Features:
    - Natural text-to-speech with multiple voice options
    - Configurable speech rate, pitch, and volume
    - Language support for international users
    - Specific voice selection (male/female, accents)
    - Real-time speech status indicators
    """
    
    page = await context.get_current_page()
    voice_comm = VoiceCommunication()
    
    # Initialize voice system
    await voice_comm.initialize(page)
    
    # Configure voice settings
    settings = VoiceSettings(
        speech_rate=params.rate,
        speech_pitch=params.pitch,
        speech_volume=params.volume,
        voice_name=params.voice_name,
        language=params.language
    )
    
    # Speak the text
    await voice_comm.speak_to_user(page, params.text, settings)
    
    return {
        "status": "speech_started",
        "text": params.text,
        "voice_settings": {
            "rate": params.rate,
            "pitch": params.pitch,
            "volume": params.volume,
            "voice_name": params.voice_name,
            "language": params.language
        }
    }

async def browser_voice_listen(
    context: Context,
    params: VoiceListenParams
) -> Dict[str, Any]:
    """
    Listen for user voice input using speech recognition.
    
    Breakthrough capability enabling AI to hear and understand user voice
    commands during browser automation. Uses Web Speech API for accurate
    speech-to-text conversion with real-time transcript display.
    
    Features:
    - Real-time speech recognition
    - Live transcript display with confidence scores
    - Configurable timeout and continuous listening
    - Noise handling and error recovery
    - Visual feedback for listening status
    """
    
    page = await context.get_current_page()
    voice_comm = VoiceCommunication()
    
    # Initialize voice system
    await voice_comm.initialize(page)
    
    # Listen for voice input
    voice_result = await voice_comm.listen_for_response(page, params.timeout)
    
    if voice_result is None:
        return {
            "status": "no_voice_input",
            "message": "No voice input received within timeout period"
        }
    
    return {
        "status": "voice_received",
        "transcript": voice_result.get("transcript", ""),
        "confidence": voice_result.get("confidence", 0.0),
        "timestamp": voice_result.get("timestamp"),
        "is_final": voice_result.get("isFinal", False)
    }

async def browser_voice_ask_question(
    context: Context,
    params: VoiceQuestionParams
) -> Dict[str, Any]:
    """
    Ask a question aloud and wait for user's voice response.
    
    Revolutionary two-way voice communication combining text-to-speech
    questions with speech recognition responses. Enables natural conversation
    between AI and user during browser automation workflows.
    
    Features:
    - Natural question delivery with TTS
    - Automatic listening activation after question
    - Real-time response transcription
    - Configurable voice and timing parameters
    - Fallback handling for no response
    
    Use cases:
    - Confirming actions through voice ("Should I click submit?")
    - Gathering user preferences ("Which option do you prefer?")
    - Troubleshooting assistance ("What error do you see?")
    - Interactive form completion ("What's your email address?")
    """
    
    page = await context.get_current_page()
    voice_comm = VoiceCommunication()
    
    # Initialize voice system
    await voice_comm.initialize(page)
    
    # Configure voice settings for question
    settings = VoiceSettings(
        speech_rate=params.rate,
        voice_name=params.voice_name,
        language="en-US"
    )
    
    # Ask question and get response
    response = await voice_comm.ask_voice_question(
        page, 
        params.question, 
        settings
    )
    
    if response is None:
        return {
            "status": "no_response",
            "question": params.question,
            "message": "User did not provide a voice response"
        }
    
    return {
        "status": "question_answered",
        "question": params.question,
        "user_response": response,
        "voice_settings": {
            "rate": params.rate,
            "voice_name": params.voice_name
        }
    }

async def browser_voice_show_controls(
    context: Context
) -> Dict[str, Any]:
    """Show voice control panel to enable user voice interaction"""
    
    page = await context.get_current_page()
    voice_comm = VoiceCommunication()
    await voice_comm.initialize(page)
    await voice_comm.show_voice_controls(page)
    
    return {"status": "voice_controls_shown"}

async def browser_voice_get_available_voices(
    context: Context
) -> Dict[str, Any]:
    """Get list of available text-to-speech voices on the user's system"""
    
    page = await context.get_current_page()
    voice_comm = VoiceCommunication()
    await voice_comm.initialize(page)
    
    voices = await voice_comm.get_available_voices(page)
    
    return {
        "status": "voices_retrieved",
        "available_voices": voices,
        "voice_count": len(voices)
    }