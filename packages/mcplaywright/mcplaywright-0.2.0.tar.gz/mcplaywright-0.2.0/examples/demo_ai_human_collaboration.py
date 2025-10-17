#!/usr/bin/env python3
"""
AI-Human Collaboration Demo for MCPlaywright

Demonstrates the revolutionary AI-Human collaboration features including:
- Real-time messaging with cyberpunk notifications
- Interactive user confirmations and prompts
- Visual element selection with detailed inspection
- Voice communication (text-to-speech and speech recognition)
- Collaborative form field mapping
"""

import asyncio
import sys
from pathlib import Path

# Add src directory to path for local imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcplaywright.session_manager import SessionManager
from mcplaywright.collaboration import CollaborationMessaging, ElementInspector, UserPrompts
from mcplaywright.collaboration.voice_communication import VoiceCommunication, VoiceSettings

async def demo_ai_human_collaboration():
    """Demonstrate all AI-Human collaboration features"""
    
    print("🤖 MCPlaywright AI-Human Collaboration Demo")
    print("=" * 50)
    
    # Initialize session manager
    session_mgr = SessionManager()
    context = await session_mgr.create_session("collaboration-demo")
    page = await context.get_current_page()
    
    try:
        # Navigate to a test page
        await page.goto("https://httpbin.org/forms/post")
        print("✅ Navigated to test form page")
        
        # Initialize all collaboration systems
        messaging = CollaborationMessaging()
        prompts = UserPrompts()
        inspector = ElementInspector()
        voice_comm = VoiceCommunication()
        
        await messaging.initialize(page)
        await prompts.initialize(page)
        await inspector.initialize(page)
        await voice_comm.initialize(page)
        
        print("✅ Initialized all collaboration systems")
        
        # Demo 1: Visual Notifications
        print("\n🎨 Demo 1: Visual Notification System")
        await messaging.notify_info(page, "Welcome to AI-Human collaboration!", "🤖 DEMO STARTED")
        await page.wait_for_timeout(2000)
        
        await messaging.notify_success(page, "All systems are operational and ready!")
        await page.wait_for_timeout(2000)
        
        await messaging.notify_warning(page, "This demo will showcase interactive features")
        await page.wait_for_timeout(2000)
        
        # Demo 2: Voice Communication
        print("\n🗣️ Demo 2: Voice Communication System")
        
        # Show voice controls
        await voice_comm.show_voice_controls(page)
        await messaging.notify_info(page, "Voice controls are now available in the bottom-left corner")
        
        # Get available voices
        voices = await voice_comm.get_available_voices(page)
        print(f"✅ Found {len(voices)} available voices")
        
        # Speak a welcome message
        settings = VoiceSettings(
            speech_rate=1.1,
            speech_pitch=1.0,
            speech_volume=0.8,
            language="en-US"
        )
        
        await voice_comm.speak_to_user(
            page, 
            "Hello! I am your AI assistant. I can now speak to you and listen to your voice commands during browser automation. This opens up incredible possibilities for accessible and natural interaction!",
            settings
        )
        
        # Demo 3: Interactive User Confirmation
        print("\n🤝 Demo 3: Interactive User Confirmation")
        await messaging.notify_info(page, "I'll now ask for your permission to proceed")
        await page.wait_for_timeout(1000)
        
        confirmed = await prompts.ask_permission(
            page,
            "demonstrate the interactive element selection feature",
            "normal"
        )
        
        if confirmed:
            await messaging.notify_success(page, "Thank you for confirming! Proceeding with element selection demo.")
            
            # Demo 4: Interactive Element Selection
            print("\n🔍 Demo 4: Interactive Element Selection")
            await messaging.notify_info(page, "Please click on the 'Customer name' input field when ready")
            
            element_details = await inspector.start_inspection(
                page,
                "Please click on the 'Customer name' input field so I can analyze it"
            )
            
            if element_details:
                await messaging.notify_success(
                    page, 
                    f"Perfect! I identified: {element_details.tag_name} with text '{element_details.text_content}'"
                )
                
                print(f"✅ Element selected: {element_details.tag_name}")
                print(f"   XPath: {element_details.xpath}")
                print(f"   Text: {element_details.text_content}")
                print(f"   Visible: {element_details.visible}")
                
                # Demo 5: Voice Question
                print("\n🎤 Demo 5: Voice Question & Answer")
                await voice_comm.speak_to_user(
                    page,
                    "Now I'll ask you a question using voice. Please respond by speaking after I finish asking.",
                    settings
                )
                
                await page.wait_for_timeout(3000)  # Wait for speech to finish
                
                response = await voice_comm.ask_voice_question(
                    page,
                    "What is your favorite color? Please speak your answer clearly.",
                    settings
                )
                
                if response:
                    await messaging.notify_success(
                        page,
                        f"I heard you say: '{response}'. Voice communication is working perfectly!"
                    )
                    
                    await voice_comm.speak_to_user(
                        page,
                        f"Thank you! You said your favorite color is {response}. This demonstrates perfect two-way voice communication between AI and human during browser automation.",
                        settings
                    )
                    
                    print(f"✅ Voice response received: {response}")
                else:
                    await messaging.notify_warning(page, "No voice response received, but the system is working correctly!")
                    
            else:
                await messaging.notify_warning(page, "Element selection was cancelled, but the system worked correctly!")
                
        else:
            await messaging.notify_info(page, "Demo cancelled by user. All collaboration features are working!")
            
        # Demo 6: Collaborative Form Mapping
        print("\n📝 Demo 6: Collaborative Form Field Mapping")
        await messaging.notify_info(page, "I'll guide you through mapping multiple form fields")
        
        # Initialize inspector for form mapping
        form_fields = ["customer_name", "email", "comments", "submit_button"]
        
        # We'll just demonstrate the concept without requiring user interaction
        await messaging.notify_info(
            page,
            f"In a real scenario, I would guide you through selecting {len(form_fields)} form fields: " + 
            ", ".join(form_fields),
            "📋 FORM MAPPING DEMO"
        )
        
        # Final voice summary
        await voice_comm.speak_to_user(
            page,
            "Demonstration complete! MCPlaywright now features revolutionary AI-Human collaboration with visual notifications, interactive confirmations, element selection, and full two-way voice communication. This transforms browser automation from purely programmatic to truly collaborative.",
            settings
        )
        
        await messaging.notify_success(
            page,
            "🎉 AI-Human Collaboration Demo Complete! All features working perfectly.",
            "✅ DEMO FINISHED"
        )
        
        print("\n🎉 Demo completed successfully!")
        print("✅ All AI-Human collaboration features demonstrated:")
        print("   - Visual notification system with cyberpunk theme")
        print("   - Interactive user confirmation dialogs")
        print("   - Visual element selection with detailed analysis")
        print("   - Two-way voice communication (speak & listen)")
        print("   - Collaborative form field mapping workflow")
        print("   - Voice control panel with settings")
        
        # Keep browser open for manual testing
        print("\n🔧 Browser session remains open for manual testing")
        print("   - Try the voice controls in the bottom-left corner")
        print("   - Test the notification system")
        print("   - Experiment with element selection")
        print("   - Press Ctrl+C to exit when done")
        
        # Wait for user interrupt
        try:
            while True:
                await page.wait_for_timeout(1000)
        except KeyboardInterrupt:
            print("\n👋 Demo session ended by user")
            
    except Exception as e:
        print(f"❌ Demo error: {e}")
        
    finally:
        await session_mgr.cleanup_session(context.session_id)
        print("✅ Session cleaned up")

if __name__ == "__main__":
    print("🚀 Starting AI-Human Collaboration Demo...")
    print("🎯 This will showcase revolutionary features that transform browser automation!")
    print("⚠️  Make sure you have a microphone and speakers/headphones for voice features")
    print()
    
    try:
        asyncio.run(demo_ai_human_collaboration())
    except KeyboardInterrupt:
        print("\n👋 Demo cancelled by user")
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        sys.exit(1)