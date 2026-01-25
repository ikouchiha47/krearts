"""
Detailed Walkthrough: Friends Turning Enemies

This example shows step-by-step how two friends organically turn against
each other through the self-evolving story graph system.

The key: They start aligned but interpret events differently based on
their core values, leading to gradual worldview divergence.
"""

import asyncio
from narrative_graph import (
    StoryGraph,
    CharacterArc,
    Worldview,
    Value,
    ValueType,
    Belief,
    Event,
    EventType,
    RelationshipType,
)


async def detailed_friends_to_enemies_walkthrough():
    """
    Complete walkthrough of two police partners becoming enemies.
    
    Setup:
    - Alex: Justice-oriented (by-the-book cop)
    - Jordan: Compassion-oriented (considers context)
    - Both start as close friends and partners
    
    Arc:
    - Witness same events but interpret differently
    - Small conflicts accumulate
    - Forcing event requires choosing sides
    - Relationship breaks at justified moment
    """
    
    print("="*80)
    print("FRIENDS TO ENEMIES: Detailed Walkthrough")
    print("="*80)
    
    # ========================================================================
    # SETUP: Initialize story graph
    # ========================================================================
    
    print("\n" + "="*80)
    print("INITIAL SETUP")
    print("="*80)
    
    graph = StoryGraph()
    
    # Create Alex: Justice-oriented character
    alex_worldview = Worldview(
        core_beliefs={
            "law_and_order": Belief(
                statement="The law must be applied equally to everyone",
                confidence=0.95,
                formed_at=0
            ),
            "ends_justify_means": Belief(
                statement="The ends do not justify the means",
                confidence=0.85,
                formed_at=0
            )
        },
        values_hierarchy=[
            Value(
                type=ValueType.JUSTICE,
                importance=1.0,
                description="Rules must be followed for society to function"
            ),
            Value(
                type=ValueType.TRUTH,
                importance=0.9,
                description="Honesty is paramount"
            ),
            Value(
                type=ValueType.DUTY,
                importance=0.8,
                description="Following orders and protocol"
            ),
        ],
        biases=["confirmation_bias_toward_rules", "black_and_white_thinking"]
    )
    
    alex_arc = graph.add_character(
        char_id="alex",
        initial_worldview=alex_worldview,
        growth_trajectory="Will learn that absolute justice can be cruel"
    )
    
    # Create Jordan: Compassion-oriented character
    jordan_worldview = Worldview(
        core_beliefs={
            "context_matters": Belief(
                statement="Every situation has context that matters",
                confidence=0.90,
                formed_at=0
            ),
            "protect_vulnerable": Belief(
                statement="We must protect those who can't protect themselves",
                confidence=0.85,
                formed_at=0
            )
        },
        values_hierarchy=[
            Value(
                type=ValueType.COMPASSION,
                importance=1.0,
                description="Understanding and helping others"
            ),
            Value(
                type=ValueType.LOYALTY,
                importance=0.9,
                description="Standing by friends and colleagues"
            ),
            Value(
                type=ValueType.JUSTICE,
                importance=0.7,
                description="Fairness with understanding of circumstances"
            ),
        ],
        biases=["empathy_bias", "situational_ethics"]
    )
    
    jordan_arc = graph.add_character(
        char_id="jordan",
        initial_worldview=jordan_worldview,
        growth_trajectory="Will learn that compassion without accountability enables harm"
    )
    
    # Create initial relationship: Close friends
    relationship = graph.add_relationship(
        char1_id="alex",
        char2_id="jordan",
        initial_trust=0.9,  # Very high initial trust
        relationship_type=RelationshipType.FRIEND
    )
    
    print("\n📊 INITIAL STATE:")
    print(f"  Alex's top value: JUSTICE (importance: 1.0)")
    print(f"  Jordan's top value: COMPASSION (importance: 1.0)")
    print(f"  Relationship: {relationship.relationship_type.value}")
    print(f"  Trust level: {relationship.trust_level:.2f}")
    print(f"  Worldview divergence: {alex_arc.worldview.calculate_divergence(jordan_arc.worldview):.2f}")
    
    # Check for value conflicts
    alex_top = alex_arc.worldview.get_most_important_value()
    jordan_top = jordan_arc.worldview.get_most_important_value()
    initial_conflict = alex_top.conflicts_with(jordan_top, "police work")
    print(f"  Value conflict strength: {initial_conflict:.2f}")
    
    print("\n💭 INITIAL ALIGNMENTS:")
    print("  ✓ Both believe in protecting people")
    print("  ✓ Both believe in their duty as officers")
    print("  ✓ Both trust each other deeply")
    print("  ⚠️  But: Different ideas about HOW to achieve justice")
    
    # ========================================================================
    # EVENT 1: First small conflict
    # ========================================================================
    
    print("\n" + "="*80)
    print("EVENT 1: Minor Traffic Stop Escalates")
    print("="*80)
    
    event1 = Event(
        id="traffic_stop",
        beat_number=1,
        type=EventType.CONFLICT,
        description="Stop a driver with a broken tail light. Driver is nervous, admits to having unpaid tickets. Has kids in car, is trying to get to work.",
        participants=["alex", "jordan"],
        witnesses=["driver", "kids"],
        stakes=0.3,  # Low stakes
        requires_interpretation=True
    )
    
    consequences1 = graph.add_event(event1)
    
    print("\n📖 SITUATION:")
    print("  Driver: Single parent, working two jobs, can't afford tickets")
    print("  Options: Write ticket (enforcing law) or let go with warning (compassion)")
    
    print("\n🤔 CHARACTER INTERPRETATIONS:")
    print("  Alex sees: 'This is still breaking the law. Rules exist for everyone.'")
    print("  Jordan sees: 'This person is struggling. One more ticket could break them.'")
    
    print("\n⚖️  RESOLUTION:")
    print("  Alex wants to write ticket")
    print("  Jordan gives warning instead")
    print("  Small disagreement but they move on")
    
    # Update relationship (minor strain)
    relationship.update_trust(-0.05, "Minor disagreement on traffic stop")
    
    print(f"\n📊 AFTER EVENT 1:")
    print(f"  Trust: {relationship.trust_level:.2f} (slight decrease)")
    print(f"  Worldview divergence: {alex_arc.worldview.calculate_divergence(jordan_arc.worldview):.2f}")
    print("  Status: Still friends, but Alex feels Jordan is 'too soft'")
    
    # ========================================================================
    # EVENT 2: Medium conflict
    # ========================================================================
    
    print("\n" + "="*80)
    print("EVENT 2: Witness Police Brutality")
    print("="*80)
    
    event2 = Event(
        id="brutality_witness",
        beat_number=2,
        type=EventType.REVELATION,
        description="Witness their sergeant beating a suspect who resisted arrest. Suspect is now compliant but sergeant continues.",
        participants=["alex", "jordan", "sergeant", "suspect"],
        witnesses=["alex", "jordan"],
        stakes=0.7,  # High stakes
        requires_interpretation=True
    )
    
    consequences2 = graph.add_event(event2)
    
    print("\n📖 SITUATION:")
    print("  Sergeant Miller (their mentor) beats a suspect")
    print("  Suspect: Young, poor, was running from warrant for unpaid fines")
    print("  Context: Sergeant is under investigation stress, wife has cancer")
    
    print("\n🤔 CHARACTER INTERPRETATIONS:")
    print("\n  Alex's view:")
    print("    - 'This is assault. Badge doesn't give him that right.'")
    print("    - 'Must report to Internal Affairs.'")
    print("    - Core value triggered: JUSTICE (1.0) + TRUTH (0.9)")
    print("    - Belief: 'The law must be applied equally' (0.95 confidence)")
    
    print("\n  Jordan's view:")
    print("    - 'This is wrong, but Miller is under incredible stress.'")
    print("    - 'He's been a good cop for 20 years. Everyone breaks sometimes.'")
    print("    - 'If we report him, his career is over. His family needs his income.'")
    print("    - Core value triggered: COMPASSION (1.0) + LOYALTY (0.9)")
    print("    - Belief: 'Context matters' (0.90 confidence)")
    
    print("\n💬 THE ARGUMENT:")
    print("  Alex: 'We have to report this.'")
    print("  Jordan: 'He made a mistake. We can handle it internally.'")
    print("  Alex: 'A mistake? He beat an unarmed man!'")
    print("  Jordan: 'And his wife is dying! Have some compassion!'")
    print("  Alex: 'Compassion for him? What about the victim?'")
    print("  Jordan: 'What about Miller's kids when he loses everything?'")
    
    # Update worldviews - this is a pivotal moment
    from narrative_graph import WorldviewShift
    
    alex_shift = WorldviewShift(
        beat_number=2,
        trigger_event_id="brutality_witness",
        old_belief="Can work within the system to fix problems",
        new_belief="The system protects abusers. Must go outside chain of command.",
        confidence=0.7,
        emotional_impact=0.8,
        reasoning="Seeing brutality made abstract principles concrete"
    )
    alex_arc.worldview_shifts.append(alex_shift)
    
    jordan_shift = WorldviewShift(
        beat_number=2,
        trigger_event_id="brutality_witness",
        old_belief="Can handle problems with understanding and dialogue",
        new_belief="Some people prioritize rules over human suffering",
        confidence=0.6,
        emotional_impact=0.7,
        reasoning="Alex's rigidity surprised and disappointed Jordan"
    )
    jordan_arc.worldview_shifts.append(jordan_shift)
    
    print("\n📊 WORLDVIEW SHIFTS:")
    print(f"  Alex: {alex_shift.old_belief}")
    print(f"    → {alex_shift.new_belief}")
    print(f"  Jordan: {jordan_shift.old_belief}")
    print(f"    → {jordan_shift.new_belief}")
    
    # Update relationship (major strain)
    relationship.update_trust(-0.15, "Major disagreement on handling brutality")
    
    print(f"\n📊 AFTER EVENT 2:")
    print(f"  Trust: {relationship.trust_level:.2f} (significant decrease)")
    current_divergence = alex_arc.worldview.calculate_divergence(jordan_arc.worldview)
    print(f"  Worldview divergence: {current_divergence:.2f}")
    print(f"  Relationship: {relationship.relationship_type.value}")
    print("  Status: Strained but still partners")
    
    # ========================================================================
    # EVENT 3: The betrayal
    # ========================================================================
    
    print("\n" + "="*80)
    print("EVENT 3: Alex Reports to IA (Without Telling Jordan)")
    print("="*80)
    
    event3 = Event(
        id="internal_affairs_report",
        beat_number=3,
        type=EventType.BETRAYAL,
        description="Alex files report with Internal Affairs without telling Jordan. IA opens investigation into Sergeant Miller.",
        participants=["alex", "jordan", "internal_affairs"],
        witnesses=["internal_affairs_agents"],
        stakes=0.9,  # Very high stakes
        requires_interpretation=False  # Clear betrayal
    )
    
    consequences3 = graph.add_event(event3)
    
    print("\n📖 SITUATION:")
    print("  Alex couldn't let it go")
    print("  Filed report alone, believing it was the right thing")
    print("  Jordan finds out from other officers")
    print("  Sergeant Miller suspended, under investigation")
    print("  Jordan feels betrayed - Alex went behind their back")
    
    print("\n🤔 CHARACTER JUSTIFICATIONS:")
    print("\n  Alex's reasoning:")
    print("    - 'Jordan was never going to agree.'")
    print("    - 'Someone had to do the right thing.'")
    print("    - 'If Jordan cared about justice, they'd understand.'")
    print("    - Value: JUSTICE (1.0) override LOYALTY to partner")
    
    print("\n  Jordan's response:")
    print("    - 'Alex stabbed me in the back.'")
    print("    - 'Partners don't keep secrets like this.'")
    print("    - 'Alex destroyed a good man's career over one mistake.'")
    print("    - Value: LOYALTY (0.9) was violated")
    
    # Major worldview shifts
    alex_shift2 = WorldviewShift(
        beat_number=3,
        trigger_event_id="internal_affairs_report",
        old_belief="Can convince Jordan to do the right thing",
        new_belief="Jordan prioritizes comfort over justice",
        confidence=0.8,
        emotional_impact=0.6,
        reasoning="Had to act alone because Jordan wouldn't support justice"
    )
    alex_arc.worldview_shifts.append(alex_shift2)
    
    jordan_shift2 = WorldviewShift(
        beat_number=3,
        trigger_event_id="internal_affairs_report",
        old_belief="Alex is my trusted partner",
        new_belief="Alex is a self-righteous crusader who doesn't care who gets hurt",
        confidence=0.9,
        emotional_impact=0.9,
        reasoning="Alex betrayed trust and destroyed Miller's life"
    )
    jordan_arc.worldview_shifts.append(jordan_shift2)
    
    # Relationship severely damaged
    relationship.update_trust(-0.4, "Alex filed IA report without telling Jordan")
    relationship.conflicts.append("IA report betrayal")
    
    print(f"\n📊 AFTER EVENT 3:")
    print(f"  Trust: {relationship.trust_level:.2f} (major decrease)")
    current_divergence = alex_arc.worldview.calculate_divergence(jordan_arc.worldview)
    print(f"  Worldview divergence: {current_divergence:.2f}")
    print(f"  Relationship: {relationship.relationship_type.value}")
    print("  Status: Partnership effectively over")
    
    # ========================================================================
    # EVENT 4: The breaking point
    # ========================================================================
    
    print("\n" + "="*80)
    print("EVENT 4: Public Confrontation")
    print("="*80)
    
    event4 = Event(
        id="public_confrontation",
        beat_number=4,
        type=EventType.CONFRONTATION,
        description="Jordan confronts Alex in front of other officers. Accuses Alex of being a traitor. Alex accuses Jordan of being corrupt.",
        participants=["alex", "jordan"],
        witnesses=["other_officers"],
        stakes=1.0,  # Maximum stakes - point of no return
        requires_interpretation=False
    )
    
    consequences4 = graph.add_event(event4)
    
    print("\n📖 SITUATION:")
    print("  Jordan publicly confronts Alex in the precinct")
    print("  Years of partnership dissolving in anger")
    print("  Other officers forced to pick sides")
    
    print("\n💬 THE CONFRONTATION:")
    print("  Jordan: 'You destroyed a good man's life!'")
    print("  Alex: 'He destroyed his own life by beating a suspect!'")
    print("  Jordan: 'He was under stress! He made a mistake!'")
    print("  Alex: 'And I'm supposed to cover for him? That makes me corrupt!'")
    print("  Jordan: 'You're not a cop, you're a goddamn robot!'")
    print("  Alex: 'And you're not a cop, you're an enabler!'")
    print("  Jordan: 'We're done. Don't ever call me your partner again.'")
    print("  Alex: 'Fine by me. I don't work with corrupt cops.'")
    
    # Check for breaking point
    breaking_point = graph.relationship_engine.evaluate_breaking_point(
        alex_arc,
        jordan_arc,
        event4,
        relationship
    )
    
    print("\n" + "="*80)
    print("BREAKING POINT ANALYSIS")
    print("="*80)
    
    if breaking_point:
        print("\n✅ BREAKING POINT CONDITIONS MET:")
        print(f"  1. Worldview divergence: {breaking_point['worldview_divergence']:.2f} (threshold: 0.50)")
        print(f"  2. Value conflict: {breaking_point['value_conflict']:.2f} (threshold: 0.50)")
        print(f"  3. Forcing event: Stakes = {event4.stakes} (threshold: 0.70)")
        print(f"  4. Arc progression: {len(alex_arc.worldview_shifts)} + {len(jordan_arc.worldview_shifts)} shifts")
        
        print("\n🧠 CHARACTER REASONING:")
        print(f"  Alex: {breaking_point['char1_reasoning']}")
        print(f"  Jordan: {breaking_point['char2_reasoning']}")
        
        print("\n📊 FINAL STATE:")
        relationship.update_trust(breaking_point["trust_delta"], "Breaking point reached")
        print(f"  Trust: {relationship.trust_level:.2f}")
        print(f"  Relationship: {relationship.relationship_type.value}")
        print(f"  Reversible: {breaking_point['reversible']}")
        
        print("\n✅ NARRATIVE JUSTIFICATION:")
        print(f"  {breaking_point['arc_justification']}")
        
    else:
        print("\n❌ BREAKING POINT NOT REACHED")
        print("  Not enough development to justify relationship break")
    
    # ========================================================================
    # VALIDATION
    # ========================================================================
    
    print("\n" + "="*80)
    print("NARRATIVE VALIDATION")
    print("="*80)
    
    print("\n✅ THIS BREAKDOWN IS JUSTIFIED BECAUSE:")
    print("\n1. WORLDVIEW DIVERGENCE:")
    print("   - Started with shared goal (protect people)")
    print("   - Gradually revealed different interpretations")
    print("   - Multiple experiences reinforced divergence")
    print(f"   - Final divergence: {alex_arc.worldview.calculate_divergence(jordan_arc.worldview):.2f}/1.0")
    
    print("\n2. VALUE CONFLICTS:")
    print("   - Alex: JUSTICE (1.0) vs Jordan: COMPASSION (1.0)")
    print("   - Both legitimate values, genuinely incompatible in this context")
    print("   - Neither character is 'wrong' - they have different priorities")
    
    print("\n3. CHARACTER ARCS:")
    print(f"   - Alex had {len(alex_arc.worldview_shifts)} worldview shifts")
    print(f"   - Jordan had {len(jordan_arc.worldview_shifts)} worldview shifts")
    print(f"   - Both characters evolved their beliefs based on experiences")
    
    print("\n4. FORCING EVENTS:")
    print("   - Not sudden - built up over multiple incidents")
    print("   - Each event increased stakes")
    print("   - Final confrontation forced permanent choice")
    
    print("\n5. SHARED EXPERIENCES:")
    print(f"   - Experienced {len(relationship.shared_experiences)} events together")
    print(f"   - Accumulated {len(relationship.conflicts)} conflicts")
    print("   - Each one showing their different worldviews")
    
    # ========================================================================
    # CONTRAST WITH BAD WRITING
    # ========================================================================
    
    print("\n" + "="*80)
    print("CONTRAST: What Makes This GOOD vs BAD Writing")
    print("="*80)
    
    print("\n❌ BAD WRITING (Unmotivated):")
    print("   'Alex and Jordan were best friends. Then one day, Alex")
    print("   betrayed Jordan for no clear reason. Now they hate each other.'")
    print("\n   Problems:")
    print("   - No worldview tracking")
    print("   - No value conflicts")
    print("   - No arc progression")
    print("   - Sudden, arbitrary change")
    
    print("\n✅ GOOD WRITING (Motivated):")
    print("   'Alex and Jordan started aligned but with different core values.")
    print("   Through shared experiences, they interpreted events differently.")
    print("   Small conflicts accumulated. Finally, a high-stakes situation")
    print("   forced them to choose between their conflicting values.'")
    print("\n   Strengths:")
    print("   - Clear worldview tracking")
    print("   - Genuine value conflicts")
    print("   - Organic arc progression")
    print("   - Justified, earned change")
    
    # ========================================================================
    # SYSTEM VALIDATION
    # ========================================================================
    
    print("\n" + "="*80)
    print("SYSTEM VALIDATION CHECKS")
    print("="*80)
    
    # Validate plot coherence
    is_valid, violations = graph.validate_plot_coherence()
    
    print(f"\n✅ Plot coherence: {'VALID' if is_valid else 'INVALID'}")
    
    if violations:
        print("\n⚠️  Issues found:")
        for v in violations:
            print(f"  - {v}")
    else:
        print("\n✅ No coherence violations")
    
    # Validate consequences
    from narrative_graph import ConsequenceEngine
    engine = ConsequenceEngine()
    
    print("\n📋 Consequence Validation:")
    for consequence in list(graph.consequences.values())[:3]:
        is_valid, reasoning, confidence = engine.evaluate_consequence_validity(
            graph.events[consequence.triggering_event_id],
            consequence,
            alex_arc,
            jordan_arc,
            relationship
        )
        
        print(f"\n  Consequence: {consequence.description[:50]}...")
        print(f"  Valid: {is_valid} (confidence: {confidence:.2f})")
        if not is_valid:
            print(f"  Issues: {reasoning}")
    
    print("\n" + "="*80)
    print("CONCLUSION")
    print("="*80)
    
    print("\n✅ This relationship breakdown is:")
    print("  - Logically consistent")
    print("  - Emotionally believable")
    print("  - Narratively earned")
    print("  - Character-driven (not plot-driven)")
    print("  - Satisfying to audiences")
    
    print("\n💡 Key Insight:")
    print("  By tracking worldviews, values, and experiences, the system")
    print("  ensures that major relationship changes are organically motivated.")
    print("  No arbitrary betrayals. No sudden heel-turns. Just two people")
    print("  who care about different things finding themselves on opposite sides.")
    
    print("\n" + "="*80)
    print("END OF WALKTHROUGH")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(detailed_friends_to_enemies_walkthrough())