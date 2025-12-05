# Character Agent Crew Specification

## Overview
Transform story characters into autonomous CrewAI agents that interact to generate narrative scenes through multi-agent collaboration.

## Objective
Create a system where characters from a detective storyline become independent agents with their own goals, personalities, and behaviors. These agents interact within scenarios to generate realistic dialogue and narrative progression.

## Architecture

### 1. Character Data Extraction

**Source**: Flow state storyline (`output/flow_states/storybuilder_{id}.json`)

**Character Schema** (extracted from storyline markdown):
```python
@dataclass
class CharacterData:
    name: str
    physical_traits: str
    ethnicity: str
    age: int
    quirks: List[str]
    backstory: str
    role: str  # detective, killer, victim, accomplice, witness, betrayal
    actions_locations: List[dict]  # Timeline of actions
    motivations: str
    identity_anchors: str  # Core beliefs, values
    long_term_goals: str
    relationships: str  # Key allies, rivals
    triggers_stress: str  # What escalates them
    skills_toolkit: str
    memory_hooks: List[str]  # Canonical facts
```

**Parser Implementation**:
- Read storyline from flow state JSON
- Parse markdown character sections using regex
- Extract structured data for each character
- Save to `output/book_{id}/characters/{character_name}.json`

### 2. Dynamic Agent Builder

**Agent Configuration** (derived from character data):

```python
class CharacterAgent:
    """Converts character data into CrewAI Agent"""
    
    def __init__(self, character_data: CharacterData, llm: LLM):
        self.data = character_data
        self.llm = llm
    
    def build_agent(self) -> Agent:
        return Agent(
            role=self._build_role(),
            goal=self._build_goal(),
            backstory=self._build_backstory(),
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
            max_iter=50  # Configurable
        )
    
    def _build_role(self) -> str:
        """
        Role format: "{character_role} - {name}"
        Example: "Detective - Jack Malone"
        """
        return f"{self.data.role.title()} - {self.data.name}"
    
    def _build_goal(self) -> str:
        """
        Combine long-term goals with immediate motivations
        Example: "Expose corruption and find Eddie's killer while 
                  maintaining your moral code despite the city's rot"
        """
        return f"{self.data.long_term_goals}. {self.data.motivations}"
    
    def _build_backstory(self) -> str:
        """
        Rich backstory including:
        - Character history
        - Personality traits (from quirks, identity_anchors)
        - Stress responses
        - Key relationships
        """
        return f"""
{self.data.backstory}

Personality:
{self._format_quirks()}

Core Beliefs: {self.data.identity_anchors}

Under Pressure: {self.data.triggers_stress}

Key Relationships: {self.data.relationships}
"""
```

### 3. Scenario Task Builder

**Scenario Types**:
1. **Interrogation**: Detective vs Suspect
2. **Confrontation**: Two characters with conflicting goals
3. **Negotiation**: Characters trying to reach agreement
4. **Investigation**: Detective examining evidence/witness

**Task Configuration**:
```python
class ScenarioTask:
    """Creates collaborative task for character agents"""
    
    def __init__(
        self,
        scenario_type: str,
        characters: List[CharacterData],
        context: dict,  # Storyline, evidence, location
        goal: str
    ):
        self.scenario_type = scenario_type
        self.characters = characters
        self.context = context
        self.goal = goal
    
    def build_task(self) -> Task:
        return Task(
            description=self._build_description(),
            expected_output=self._build_expected_output(),
            agent=None,  # Collaborative task
        )
    
    def _build_description(self) -> str:
        """
        Scenario description including:
        - Setting (location, time, atmosphere)
        - Characters present
        - Available evidence/information
        - Immediate situation
        - Character objectives
        """
        return f"""
## Scenario: {self.scenario_type}

### Setting
Location: {self.context['location']}
Time: {self.context['time']}
Atmosphere: {self.context['atmosphere']}

### Characters Present
{self._format_characters()}

### Situation
{self.context['situation']}

### Available Information
{self._format_evidence()}

### Objective
{self.goal}

### Instructions
- Stay in character based on your role, backstory, and motivations
- React authentically to other characters' actions and dialogue
- Use your skills and knowledge appropriately
- Consider your relationships and past interactions
- Respond to stress according to your personality
- Work toward your character's goals while interacting naturally
"""
    
    def _build_expected_output(self) -> str:
        return """
A narrative scene with:
- Realistic dialogue between characters
- Character actions and reactions
- Internal thoughts/motivations (when relevant)
- Scene progression toward resolution
- Authentic character voices and behaviors

Format as screenplay-style scene with:
- Character names in caps before dialogue
- Action lines describing behavior
- Stage directions in parentheses
"""
```

### 4. Character Crew

**Crew Configuration**:
```python
class CharacterCrew:
    """Manages multi-character agent interactions"""
    
    def __init__(
        self,
        characters: List[CharacterData],
        scenario: ScenarioTask,
        llm_store: LLMStore,
        max_iter: int = 20
    ):
        self.characters = characters
        self.scenario = scenario
        self.llm_store = llm_store
        self.max_iter = max_iter
    
    def build_crew(self) -> Crew:
        # Create agents for each character
        agents = [
            CharacterAgent(char, self.llm_store.load(LLMThinkerIntent))
            .build_agent()
            for char in self.characters
        ]
        
        # Create scenario task
        task = self.scenario.build_task()
        
        return Crew(
            agents=agents,
            tasks=[task],
            verbose=True,
            process=Process.sequential,  # Or hierarchical
            max_iter=self.max_iter
        )
    
    async def run_scenario(self) -> str:
        """Execute the scenario and return narrative output"""
        crew = self.build_crew()
        result = await crew.kickoff_async()
        return result.raw
```

## Test Implementation

### Phase 1: Character Data Extraction
**File**: `cinema/agents/character_crew/parser.py`

```python
def extract_characters_from_storyline(flow_id: str) -> List[CharacterData]:
    """Parse characters from flow state storyline"""
    # Load flow state
    # Parse markdown character sections
    # Create CharacterData objects
    # Save to JSON files
    pass
```

### Phase 2: Test Scenario
**File**: `cinema/cmd/examples/test_character_crew.py`

**Test Case 1: Interrogation**
- Characters: Jack Malone (detective) + Tommy Russo (killer)
- Scenario: Police interrogation room
- Goal: Jack tries to get Tommy to confess or reveal information
- Context: Evidence available (glove fibers, baseball card, ledger)
- Max iterations: 10, 20, 50

**Expected Behaviors**:
- Jack: Methodical questioning, uses evidence, reads body language
- Tommy: Defensive, loyal to mob, guilt over Eddie, opera whistling quirk

**Test Case 2: Confrontation**
- Characters: Jack Malone + Veronica Steele
- Scenario: Black Lotus Club backroom
- Goal: Jack confronts Veronica about her lies
- Context: Jack knows she hid evidence
- Max iterations: 15

**Expected Behaviors**:
- Jack: Torn between attraction and duty, direct questioning
- Veronica: Protective of secrets, manipulative, fear for safety

### Phase 3: Evaluation Metrics

**Quality Measures**:
1. **Character Consistency**: Do agents stay in character?
2. **Goal Pursuit**: Do agents work toward their objectives?
3. **Dialogue Quality**: Is dialogue realistic and character-appropriate?
4. **Scene Progression**: Does the scene move forward naturally?
5. **Relationship Dynamics**: Are character relationships reflected?

**Iteration Analysis**:
- Compare outputs at 10, 20, 50 iterations
- Measure: scene depth, revelation progression, dialogue quality
- Identify optimal iteration count

## File Structure

```
cinema/agents/character_crew/
├── __init__.py
├── parser.py              # Character data extraction
├── character_agent.py     # CharacterAgent class
├── scenario.py            # ScenarioTask class
├── crew.py                # CharacterCrew class
└── scenarios/
    ├── interrogation.yaml
    ├── confrontation.yaml
    └── investigation.yaml

cinema/cmd/examples/
└── test_character_crew.py  # Test script

output/book_{id}/characters/
├── Jack_Malone.json
├── Tommy_Russo.json
├── Veronica_Steele.json
├── Eddie_Chen.json
└── Captain_Morrison.json
```

## CLI Integration

```bash
# Extract characters from storyline
krearts characters extract 43e21caa

# Run character scenario
krearts characters scenario 43e21caa \
  --characters "Jack Malone,Tommy Russo" \
  --type interrogation \
  --max-iter 20

# List available scenarios
krearts characters scenarios
```

## Success Criteria

1. ✅ Characters successfully extracted and saved as JSON
2. ✅ Agents created with character-appropriate roles/goals/backstories
3. ✅ Scenario generates realistic dialogue and progression
4. ✅ Characters maintain consistency across iterations
5. ✅ Output quality improves with iteration count (up to threshold)
6. ✅ Different scenarios produce different interaction patterns

## Future Enhancements

1. **Multi-character scenes** (3+ characters)
2. **Memory persistence** across scenarios
3. **Dynamic scenario generation** from storyline events
4. **Character evolution** based on interactions
5. **Automated scene-to-chapter** conversion
6. **Character relationship graph** updates based on interactions

## Implementation Tasks

### Task 1: Character Data Model & Parser
**Priority**: P0 (Blocking)
**Estimate**: 2-3 hours

**Requirements**:
- [ ] Create `cinema/models/storyline.py` with `Character` and `Storyline` dataclasses
- [ ] Implement `Storyline.from_flow_state(flow_id)` to load from flow state JSON
- [ ] Parse markdown character sections using regex
- [ ] Extract all character fields (name, backstory, role, motivations, etc.)
- [ ] Return `List[Character]` from storyline
- [ ] Add unit tests with existing flow state data

**Acceptance Criteria**:
- Can load storyline from `output/flow_states/storybuilder_{id}.json`
- Extracts all 5 characters from test storyline
- All character fields populated correctly
- Characters accessible via `storyline.characters`

### Task 2: Character JSON Export
**Priority**: P0 (Blocking)
**Estimate**: 1 hour

**Requirements**:
- [ ] Implement `Character.to_json()` method
- [ ] Create `save_characters_to_dir(characters, output_dir)` function
- [ ] Save each character as `{character_name}.json`
- [ ] Create character manifest file listing all characters

**Acceptance Criteria**:
- Characters saved to `output/book_{id}/characters/`
- JSON files are valid and readable
- Manifest file lists all characters with roles

### Task 3: Character Agent Builder
**Priority**: P1
**Estimate**: 2-3 hours

**Requirements**:
- [ ] Create `cinema/agents/character_crew/character_agent.py`
- [ ] Implement `CharacterAgent` class
- [ ] Build CrewAI Agent from Character data
- [ ] Format role, goal, backstory appropriately
- [ ] Add personality traits and quirks to backstory

**Acceptance Criteria**:
- Can create Agent from Character object
- Agent has character-appropriate role/goal/backstory
- Backstory includes personality and relationships

### Task 4: Scenario Task Builder
**Priority**: P1
**Estimate**: 2-3 hours

**Requirements**:
- [ ] Create `cinema/agents/character_crew/scenario.py`
- [ ] Implement `ScenarioTask` class
- [ ] Create scenario templates (interrogation, confrontation)
- [ ] Build task description with context
- [ ] Define expected output format

**Acceptance Criteria**:
- Can create Task for different scenario types
- Task description includes setting, characters, objectives
- Expected output format is clear

### Task 5: Character Crew
**Priority**: P1
**Estimate**: 2-3 hours

**Requirements**:
- [ ] Create `cinema/agents/character_crew/crew.py`
- [ ] Implement `CharacterCrew` class
- [ ] Build Crew with multiple character agents
- [ ] Configure max_iter and process type
- [ ] Implement async execution

**Acceptance Criteria**:
- Can create Crew with 2+ character agents
- Crew executes scenario task
- Returns narrative output
- Configurable iteration count

### Task 6: Test Script
**Priority**: P1
**Estimate**: 1-2 hours

**Requirements**:
- [ ] Create `cinema/cmd/examples/test_character_crew.py`
- [ ] Implement test case 1: Jack + Tommy interrogation
- [ ] Implement test case 2: Jack + Veronica confrontation
- [ ] Test with different max_iter values (10, 20, 50)
- [ ] Save outputs for comparison

**Acceptance Criteria**:
- Script runs successfully
- Generates realistic dialogue
- Characters stay in character
- Output quality measurable across iterations

### Task 7: CLI Integration (Optional)
**Priority**: P2
**Estimate**: 2 hours

**Requirements**:
- [ ] Add `krearts characters extract` command
- [ ] Add `krearts characters scenario` command
- [ ] Add `krearts characters list` command

**Acceptance Criteria**:
- CLI commands work as documented
- Integrates with existing workflow

## Notes

- Use `LLMThinkerIntent` (Gemini 2.5 Pro) for rich character interactions
- Consider using `LLMPlannerIntent` (GPT-4.1) for more structured scenarios
- Save all scenario outputs for analysis
- Track token usage per iteration
- Monitor for character drift over long iterations
