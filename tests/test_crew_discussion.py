#!/usr/bin/env python3
"""Test CrewAI-based character discussion with manager agent"""

from cinema.agents.character.discussion import CharacterDiscussionCrew, CharacterDiscussionSchema
from cinema.context import DirectorsContext
from cinema.models.storyline import Storyline
from cinema.registry import OpenAiHerd

async def test_discussion():
    from dotenv import load_dotenv

    print("🎭 Testing CrewAI Character Discussion\n")
    print("=" * 80)
    
    load_dotenv()

    # Setup
    ctx = DirectorsContext(llmstore=OpenAiHerd, debug=True)
    storyline = Storyline.from_flow_state("43e21caa")
    
    # Get characters
    print("\nAvailable characters:")
    for char in storyline.characters:
        print(f"  - {char.name!r}")
    
    jack = storyline.get_character_by_name("Jack Malone")
    print(f"\nLooking for Jack Malone: {jack is not None}")
    
    # Use exact name from character list with curly quotes
    tommy = storyline.get_character_by_name('Tommy "The Knife" Russo')
    print(f"Looking for Tommy: {tommy is not None}")
    
    if not jack or not tommy:
        print("\n❌ Characters not found!")
        print(f"Jack: {jack}")
        print(f"Tommy: {tommy}")
        return
    
    print(f"Character 1: {jack.name} ({jack.role})")
    print(f"  Motivation: {jack.motivations[:100]}...")
    print(f"\nCharacter 2: {tommy.name} ({tommy.role})")
    print(f"  Motivation: {tommy.motivations[:100]}...")
    print("\n" + "=" * 80)
    
    # Create discussion crew
    print("\nCreating discussion crew...")
    chardi = CharacterDiscussionCrew(
        ctx=ctx,
        characters=[jack, tommy],
        workflow_id="43e21caa",
    )
    
    print("Bootstrapping crew...")
    chardi.bootstrap()
    print("✅ Crew ready!")

    print("\n" + "=" * 80)
    print("\n🚀 Starting discussion with manager agent coordination...\n")
    
    # Run discussion
    inputs = CharacterDiscussionSchema(
        storyline=storyline.storyline_text,
        characters=[jack, tommy],
        discussion_goal=(
            "Jack confronts Tommy about Eddie Chen's death. "
            "Jack wants the truth. Tommy wants to protect himself and the organization. "
            "The discussion should reveal: What really happened to Eddie? "
            "Is Tommy guilty? Can they trust each other?"
        ),
    )

    result = await chardi.crew().kickoff_async(inputs=inputs.to_crew())
    transcript = result.raw if hasattr(result, 'raw') else str(result)
    
    print("\n" + "=" * 80)
    print("✅ Discussion completed!")
    print("=" * 80)
    
    # Save transcript
    output_file = chardi.save_transcript(transcript, "jack_tommy_eddie_discussion.txt")
    print(f"\n📄 Transcript saved: {output_file}")
    
    # Show excerpt
    print("\n" + "=" * 80)
    print("TRANSCRIPT EXCERPT:")
    print("=" * 80)
    print(transcript[:1000] + "...")
    print("\n" + "=" * 80)

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_discussion())
