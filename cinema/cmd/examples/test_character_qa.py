#!/usr/bin/env python3
"""
Test character Q&A to verify character consistency and behavior mapping.

Usage:
    # List characters in a workflow
    python cinema/cmd/examples/test_character_qa.py list [flow_id]
    
    # Interactive mode (with history)
    python cinema/cmd/examples/test_character_qa.py interactive [flow_id] [character_name]
    
    # Interactive mode (without history)
    python cinema/cmd/examples/test_character_qa.py interactive --no-history [character_name]
    
    # Test mode (with history)
    python cinema/cmd/examples/test_character_qa.py test [flow_id] [character_name]
    
    # Test mode (without history)
    python cinema/cmd/examples/test_character_qa.py test --no-history [character_name]
    
    # Enable memory store (tracks decisions across interactions)
    python cinema/cmd/examples/test_character_qa.py test --memory [character_name]
    
Examples:
    # List all characters
    python cinema/cmd/examples/test_character_qa.py list 43e21caa
    
    # Test Jack (default)
    python cinema/cmd/examples/test_character_qa.py test --no-history
    
    # Test Tommy using prefix match
    python cinema/cmd/examples/test_character_qa.py test --no-history Tommy
    
    # Test Captain Morrison with memory
    python cinema/cmd/examples/test_character_qa.py test --memory Captain
    
    # Interactive with Veronica and memory
    python cinema/cmd/examples/test_character_qa.py interactive --memory Veronica
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List

from crewai.utilities.types import LLMMessage

from cinema.agents.character.crew import CharacterQA
from cinema.context import DirectorsContext
from cinema.models.storyline import Storyline
from cinema.registry import OpenAiHerd


# Test questions organized by character role
# Character: Jack Malone (Detective) - Quick Test (10 questions, one from each category)
DETECTIVE_QUICK_TEST = [
    # === PERSONALITY & QUIRKS ===
    "Do you have any habits or quirks when you're working a case?",
    
    # === IN-STORYLINE SITUATIONS ===
    "You're standing in a rain-soaked warehouse, looking at a body. What's going through your mind?",
    
    # === SIMILAR HYPOTHETICAL SITUATIONS ===
    "A corrupt cop threatens you to drop a case. What's your reaction?",
    
    # === BACKSTORY & MOTIVATIONS ===
    "Tell me about your time on the police force. What happened?",
    
    # === SKILLS & APPROACH ===
    "Walk me through how you investigate a murder scene.",
    
    # === STRESS & FAILURE RESPONSES ===
    "How do you deal with the guilt when you can't save someone?",
    
    # === ADDITIONAL CONTEXT ===
    "You find evidence that contradicts what a client told you. How do you handle it?",
    "Someone offers you money to look the other way on evidence. How do you respond?",
    "What drives you to keep going despite everything this city throws at you?",
    "The system is corrupt and justice seems impossible. Why keep fighting?",
]

# Character: Jack Malone (Detective) - Full Test
DETECTIVE_TEST_QUESTIONS = [
    # === PERSONALITY & QUIRKS ===
    "Do you have any habits or quirks when you're working a case?",
    "What do you do when you're nervous or under pressure?",
    
    # === IN-STORYLINE SITUATIONS (from chapters) ===
    "You're standing in a rain-soaked warehouse, looking at a body. What's going through your mind?",
    "A woman walks into your office asking you to find her missing brother. How do you respond?",
    "You're at O'Reilly's Bar and you see someone you're tailing arguing with another person. What do you do?",
    "You find evidence that contradicts what a client told you. How do you handle it?",
    
    # === SIMILAR HYPOTHETICAL SITUATIONS (not in chapters) ===
    "A corrupt cop threatens you to drop a case. What's your reaction?",
    "You discover your client has been lying to you about their involvement. What do you do?",
    "Someone offers you money to look the other way on evidence. How do you respond?",
    "You're following a lead in a dangerous part of town at night. What precautions do you take?",
    
    # === BACKSTORY & MOTIVATIONS ===
    "Tell me about your time on the police force. What happened?",
    "Why did you become a private investigator instead of staying a cop?",
    "What drives you to keep going despite everything this city throws at you?",
    
    # === SKILLS & APPROACH ===
    "Walk me through how you investigate a murder scene.",
    "How do you get information from someone who doesn't want to talk?",
    "What's your approach when the evidence doesn't add up?",
    
    # === STRESS & FAILURE RESPONSES ===
    "What happens when a case goes wrong and someone gets hurt?",
    "How do you deal with the guilt when you can't save someone?",
    "The system is corrupt and justice seems impossible. Why keep fighting?",
]

# Character: Tommy "The Knife" Russo (Killer)
KILLER_TEST_QUESTIONS = [
    # === PERSONALITY & QUIRKS ===
    "Do you have any habits or things you do regularly?",
    "What do you do when you're stressed or angry?",
    
    # === IN-STORYLINE SITUATIONS ===
    "You're at the docks collecting debts. Someone can't pay. What happens?",
    "The boss orders you to handle someone who's become a problem. How do you approach it?",
    "You run into an old friend from the neighborhood. What goes through your mind?",
    "Someone threatens to expose your activities to the police. What do you do?",
    
    # === SIMILAR HYPOTHETICAL SITUATIONS ===
    "A childhood friend asks you for help getting out of trouble with the mob. What's your response?",
    "You're ordered to do something that conflicts with your personal code. How do you handle it?",
    "Someone finds evidence linking you to a crime. What's your move?",
    "You have to choose between loyalty to the mob and protecting someone you care about. What do you choose?",
    
    # === BACKSTORY & MOTIVATIONS ===
    "How did you end up working for the mob?",
    "Tell me about growing up in the neighborhood.",
    "What keeps you loyal to the organization?",
    
    # === SKILLS & APPROACH ===
    "How do you handle intimidation work?",
    "What's your approach when things need to be done quietly?",
    "How do you make sure there are no loose ends?",
    
    # === GUILT & INTERNAL CONFLICT ===
    "Do you ever regret the choices you've made?",
    "What do you think about when you're alone?",
    "Is there anything from your past you wish you could change?",
]

# Character: Captain Morrison (Accomplice/Corrupt Cop)
ACCOMPLICE_TEST_QUESTIONS = [
    # === PERSONALITY & QUIRKS ===
    "What's your daily routine at the precinct?",
    "How do you maintain order in your department?",
    
    # === IN-STORYLINE SITUATIONS ===
    "A detective brings you evidence that could expose powerful people. What do you do?",
    "Someone from your past threatens to reveal your dealings. How do you respond?",
    "You need to make a case disappear. Walk me through your process.",
    "An honest cop in your department is getting too close to the truth. What's your move?",
    
    # === SIMILAR HYPOTHETICAL SITUATIONS ===
    "The press starts asking questions about a case you buried. How do you handle it?",
    "Someone offers you more money but it means betraying your current arrangement. What do you do?",
    "A federal investigation starts looking into your precinct. What's your strategy?",
    "You have to choose between protecting yourself or protecting your partners. What do you choose?",
    
    # === BACKSTORY & MOTIVATIONS ===
    "How did you rise through the ranks?",
    "What's your philosophy on law enforcement in this city?",
    "Why do you do what you do?",
    
    # === POWER & CONTROL ===
    "How do you maintain control over your officers?",
    "What's your relationship with the city's power brokers?",
    "How do you handle threats to your authority?",
    
    # === JUSTIFICATION & RATIONALIZATION ===
    "Do you see yourself as corrupt or pragmatic?",
    "How do you justify your actions?",
    "What would you say to someone who calls you a dirty cop?",
]

# Map character names to their test questions
CHARACTER_TEST_QUESTIONS = {
    "Jack Malone": DETECTIVE_TEST_QUESTIONS,
    "Tommy \"The Knife\" Russo": KILLER_TEST_QUESTIONS,
    "Tommy 'The Knife' Russo": KILLER_TEST_QUESTIONS,  # Handle both quote styles
    "Captain Morrison": ACCOMPLICE_TEST_QUESTIONS,
}

CHARACTER_QUICK_TEST = {
    "Jack Malone": DETECTIVE_QUICK_TEST,
}


async def qa(driver: CharacterQA, text: str, messages: List[LLMMessage]) -> str:
    """Ask a question to the character and get response"""
    output = await driver.kickoff_async(
        messages=[
            *messages,
            {"role": "user", "content": text},
        ]
    )
    return output.raw


async def interactive_mode(driver: CharacterQA, messages: List[LLMMessage], with_history: bool = True):
    """Interactive Q&A loop with user input"""
    print(f"\n{'='*80}")
    print(f"Interactive Character Q&A: {driver.character.name}")
    print(f"History: {'Enabled' if with_history else 'Disabled'}")
    print(f"{'='*80}\n")
    print("Type your questions (or 'quit' to exit):\n")
    
    conversation_history = messages.copy() if with_history else []
    
    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\nGoodbye!")
                break
            
            # Get response
            print(f"\n{driver.character.name}: ", end="", flush=True)
            
            if with_history:
                response = await qa(driver, user_input, conversation_history)
                # Add to history
                conversation_history.append({"role": "user", "content": user_input})
                conversation_history.append({"role": "assistant", "content": response})
            else:
                # No history - fresh context each time
                response = await qa(driver, user_input, messages)
            
            print(response)
            print()
            
        except KeyboardInterrupt:
            print("\n\nInterrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")
            continue


async def test_mode(driver: CharacterQA, messages: List[LLMMessage], questions: List[str], with_history: bool = True):
    """Run predefined test questions"""
    print(f"\n{'='*80}")
    print(f"Test Mode: {driver.character.name}")
    print(f"History: {'Enabled' if with_history else 'Disabled'}")
    print(f"Questions: {len(questions)}")
    print(f"{'='*80}\n")
    
    conversation_history = messages.copy() if with_history else []
    results = []
    
    for i, question in enumerate(questions, 1):
        print(f"\n{'─'*80}")
        print(f"Q{i}: {question}")
        print(f"{'─'*80}")
        
        if with_history:
            response = await qa(driver, question, conversation_history)
            # Add to history
            conversation_history.append({"role": "user", "content": question})
            conversation_history.append({"role": "assistant", "content": response})
        else:
            # No history - fresh context each time
            response = await qa(driver, question, messages)
        
        print(f"\n{driver.character.name}:")
        print(response)
        
        results.append({
            "question": question,
            "response": response,
        })
    
    print(f"\n{'='*80}\n")
    return results


async def main():
    """Main entry point with mode selection"""
    
    # Parse arguments
    mode = sys.argv[1] if len(sys.argv) > 1 else "interactive"
    with_history = "--no-history" not in sys.argv
    with_memory = "--memory" in sys.argv
    flow_id = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] != "--no-history" and sys.argv[2] != "--memory" else "43e21caa"
    
    # Handle list mode early
    if mode == "list":
        storyline = Storyline.from_flow_state(flow_id)
        print(f"\n{'='*80}")
        print(f"Characters in {flow_id}")
        print(f"{'='*80}\n")
        for char in storyline.characters:
            print(f"  {char.name:30} ({char.role})")
        print(f"\n{'='*80}\n")
        return
    
    # Setup logging - redirect crew logs to file
    log_dir = Path("output/character_qa_logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"crew_{timestamp}.log"
    
    # Configure logging to file only
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
        ]
    )
    
    # Suppress crew logs from console
    logging.getLogger('crewai').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('openai').setLevel(logging.WARNING)
    
    print(f"📝 Crew logs: {log_file}\n")
    
    # Setup
    ctx = DirectorsContext(
        llmstore=OpenAiHerd,
        debug=False,  # Disable debug to reduce console noise
    )
    
    storyline = Storyline.from_flow_state(flow_id)
    
    # Get character name from args or default to Jack Malone
    character_name = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith("--") else "Jack Malone"
    
    # Try exact match first
    character = storyline.get_character_by_name(character_name)
    
    # If not found, try prefix match (case-insensitive)
    if character is None:
        search_lower = character_name.lower()
        matches = [char for char in storyline.characters if char.name.lower().startswith(search_lower)]
        
        if len(matches) == 1:
            character = matches[0]
            print(f"✓ Matched character: {character.name}")
        elif len(matches) > 1:
            print(f"❌ Multiple characters match '{character_name}':")
            for char in matches:
                print(f"  - {char.name} ({char.role})")
            print(f"\nPlease be more specific.")
            return
        else:
            print(f"❌ Character '{character_name}' not found!")
            print(f"\nAvailable characters:")
            for char in storyline.characters:
                print(f"  - {char.name} ({char.role})")
            print(f"\nTip: Use 'list' mode to see all characters:")
            print(f"  python cinema/cmd/examples/test_character_qa.py list {flow_id}")
            return
    
    driver = CharacterQA(
        ctx=ctx, 
        character=character,
        workflow_id=flow_id,
        enable_memory=with_memory,
    )
    driver.bootstrap()
    
    if with_memory:
        print(f"💾 Memory enabled: output/book_{flow_id}/characters/{character.name.lower().replace(' ', '_')}/memory.json")
    
    messages: List[LLMMessage] = [
        {"role": "system", "content": storyline.storyline_text}
    ]
    
    # Get character-specific test questions
    # Check if quick test mode
    use_quick = "--quick" in sys.argv
    
    if use_quick:
        test_questions = CHARACTER_QUICK_TEST.get(
            character.name,
            DETECTIVE_QUICK_TEST  # Default fallback
        )
    else:
        test_questions = CHARACTER_TEST_QUESTIONS.get(
            character.name,
            DETECTIVE_TEST_QUESTIONS  # Default fallback
        )
    
    # Run based on mode
    if mode == "test":
        results = await test_mode(driver, messages, test_questions, with_history)
        
        # Save results
        output_file = f"test_results_{driver.character.name.replace(' ', '_')}_{timestamp}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n✅ Results saved to: {output_file}")
        
    else:  # interactive mode
        await interactive_mode(driver, messages, with_history)


if __name__ == "__main__":
    asyncio.run(main())
