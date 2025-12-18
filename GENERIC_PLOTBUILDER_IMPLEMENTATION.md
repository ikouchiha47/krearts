# Generic PlotBuilder Implementation Plan

## Summary

Create a genre-agnostic plotbuilder that works like DetectivePlotBuilder but uses PlotGraphOutput as input.

---

## The Flow

```
PlotGraphFlow
    ↓
PlotGraphOutput (genres, characters, relationships, events, etc.)
    ↓
GenericPlotBuilderSchema (convert PlotGraph to dict)
    ↓
GenericPlotBuilder.bootstrap(genres)
    ↓ (bootstrap internally calls .format() to fill genre override placeholders)
Fills {genre_roles}, {genre_specific_content}, etc. from genre overrides
    ↓
kickoff_async(inputs=schema.model_dump())
    ↓
CrewAI fills {genres}, {characters}, {relationships}, etc. from schema
    ↓
LLM generates detailed storyline
```

---

## Step 1: Create GenericPlotBuilderSchema

```python
# In cinema/agents/bookwriter/crew.py

class GenericPlotBuilderSchema(BaseModel):
    """Input schema for GenericPlotBuilder - converts PlotGraphOutput to task inputs"""
    
    # From PlotGraphOutput
    genres: str  # JSON string: ["detective", "noir"]
    primary_genre: str
    characters: str  # JSON string: [{name, role, ...}, ...]
    relationships: str  # JSON string: [{source, target, type, ...}, ...]
    events: str  # JSON string: [{name, type, participants, ...}, ...]
    world_context: str  # JSON string: {era, setting, ...}
    genre_metadata: str  # JSON string: {detective: {...}, cyberpunk: {...}}
    
    # User inputs
    user_requirements: str = ""
    art_style: str = ""
    allowed_art_styles: str = ""
    selected_art_styles: str = ""
    
    # Feedback loop
    feedback: str = ""
    storyline: str = ""
    
    @classmethod
    def from_plotgraph(
        cls,
        plot_graph: PlotGraphOutput,
        user_requirements: str = "",
        art_style: str = "",
        allowed_art_styles: str = "",
        selected_art_styles: str = "",
    ) -> "GenericPlotBuilderSchema":
        """Convert PlotGraphOutput to schema"""
        import json
        
        return cls(
            genres=json.dumps(plot_graph.genres),
            primary_genre=plot_graph.primary_genre,
            characters=json.dumps(plot_graph.characters),
            relationships=json.dumps(plot_graph.relationships),
            events=json.dumps(plot_graph.events),
            world_context=json.dumps(plot_graph.world_context),
            genre_metadata=json.dumps(plot_graph.genre_metadata),
            user_requirements=user_requirements,
            art_style=art_style,
            allowed_art_styles=allowed_art_styles,
            selected_art_styles=selected_art_styles,
        )
```

---

## Step 2: Update tasks.yaml Generic Section

Add all schema fields as placeholders:

```yaml
plotbuilder:
  generic:
    expected_output: >
      A comprehensive storyline with character profiles, world context,
      and detailed narrative following genre conventions

    description: |
      Given a plot structure, expand it into a rich, detailed storyline.
      
      Your task is to:
      - Generate vivid character personas and backstories
      - Create narrative descriptions for relationships
      - Build a solid plotline that serves the characters and genre
      - Add atmospheric details and emotional depth
      
      You MAY add:
      - Vivid descriptions
      - Character personalities
      - Atmospheric details
      - Emotional depth
      
      IMPORTANT:
      - Text inside (), [] and <> are instructions or intent
      - **ALWAYS** use the GLOSSARY to get the correct file paths
      
      ---
      
      ## User Requirements (Optional Seed)
      
      {user_requirements}
      
      <logic>
      if user_requirements is provided:
        - Use these as creative constraints and inspiration
        - Incorporate themes, settings, character types mentioned
        - Respect any specific requests (era, location, tone, etc.)
        - Build the story around these requirements
      else:
        - Create story freely based on plot structure
      </logic>
      
      ---
      
      ## Input Structure
      
      **Genres:** {genres}
      **Primary Genre:** {primary_genre}
      
      ### Characters (from PlotGraph)
      {characters}
      
      ### Relationships (from PlotGraph)
      {relationships}
      
      ### Events (from PlotGraph)
      {events}
      
      ### World Context (from PlotGraph)
      {world_context}
      
      ### Genre-Specific Metadata (from PlotGraph)
      {genre_metadata}
      
      ---
      
      ## Knowledge Base
      
      Available in memory:
      - Glossary (GLOSSARY.md)
      - Narrative Structures (narrative-structures/index.md)
      - Art Styles (art-styles/index.md)
      - Character Guidelines (art-styles/character-guidelines.md)
      - Style Combinations (art-styles/combinations.md)
      
      ## Tool Usage
      - Use DirectoryReadTool to explore knowledge/narrative-structures
      - Use DirectoryReadTool to explore knowledge/art-styles
      - Use FileReadTool to read specific narrative structures
      - Use FileReadTool to read art style references
      - **ALWAYS use DirectoryReadTool before FileReadTool**
      
      ---
      
      ## Art Style Selection
      - Available art styles: {allowed_art_styles}
      - User selected art styles: {selected_art_styles}
      - If user selected styles, USE THEM (they can be combined)
      - If no styles selected, choose from available styles based on story tone
      - Art styles can be COMBINED (e.g., "noir + cyberpunk", "anime + pop-art")
      - See art-styles/combinations.md for proven combinations
      - Include selected art styles in storyline metadata
      
      ---
      
      ## Output Format
      
      Respond in markdown hierarchical format.
      **STRICTLY ADHERE TO THE BELOW FORMAT**
      
      ---
      
      ## World & Era Context
      
      - Era and Time Window: <e.g., 1950s Noir / Contemporary / Near-Future>
      - Geography and Setting: <city/region, urban/rural, climate>
      - Culture and Traditions: <norms impacting behavior/conflict>
      - Societal Constructs: <how society was defined during the era>
      - Geopolitics and Legal Context: <jurisdiction, legal constraints>
      - Technology Level: <tools available, limitations>
      - Media Environment: <press influence, public perception>
      - Thematic Constraints: <tone, taboos, social dynamics>
      
      {genre_world_additions}
      
      ---
      
      ## Characters
      
      ### Character N (index)
      
      **Name:** <full name>
      **Physical Traits:** <detailed physical description embodying character's beliefs>
      **Ethnicity:** <ethnicity>
      **Age:** <age>
      **Quirks:** <list of quirks>
      **Clothing:** <type of clothing preferred>
      
      #### Backstory
      (in details)
      <name> is a calculating individual with a dark secret.
      <name> was a wealthy and influential figure.
      (and how they met or knew or are related to other key characters)
      
      Describe the character's history, formative events, and how they relate to other characters.
      
      #### Role
      IMPORTANT: Use EXACTLY ONE of these role names:
      
      {genre_roles}
      
      #### Actions & Timeline
      A chronological breakdown of:
      - what the person did
      - where the person was
      - what role the person played
      - key moments
      
      {genre_actions_additions}
      
      #### Motivations
      The actions committed by the person, and the reasons for doing so.
      It must come from the backstory, their role, and their actions.
      
      #### World View and Cultural Context
      This is the individual character's:
      - Cultural, Emotional, and Philosophical beliefs
      - How the character feels in the world era and context
      - How they view the societal constructs
      
      #### Identity Anchors
      - Core beliefs and values
      - Behavioral Patterns
      - Vices, secrets, and ideologies that drive decisions
      
      These should be set with respect to the World context.
      
      #### Long-term Goals
      Career/personal goals and current constraints.
      
      #### Relationships Graph Notes
      Key allies, rivals, obligations; how ties influence choices.
      
      #### Triggers and Stress Responses
      What escalates them and how they react under pressure.
      Emotional conflicts and philosophical conflicts.
      
      #### Skills / Toolkit (Era-Appropriate)
      Practical skills and tools available given the era and context.
      
      #### Memory Hooks
      - Canonical facts to persist in the character node for future evolution
      - 3-6 bullet points, specific and verifiable from backstory/actions
      
      ---
      
      [Repeat for each character]
      
      All character definitions should be designed to serve the conflicts,
      tensions, and evolution in the detailed storyline.
      
      ---
      
      ## Storyline
      
      ### Metadata
      - Title: <title of the book (max. 1-3 words)>
      - Theme: <description>
      - Genres: <list of genres>
      - Primary Genre: <primary genre>
      - Adults Only: <boolean>
      - Narrative Structure: "<linear or non-linear>/<which_specific_structure>"
      - Art Style: <description>
      - Story Telling Style: <description>
      - Suited For: movie, shorts, microdrama, tv-show, novel, short-story, comic book
      - Colors: list of color names with hex codes (<color_name>(#<hex_code>)...)
      - Cover/Thumbnail Image Concept: <description>
      
      ### Detailed Storyline
      The entire storyline told using one of the narrative-styles in knowledgebase.
      
      {genre_storyline_additions}
      
      ---
      
      ## References
      - [Which parts of knowledgebase was used for understanding]
      - [Files were actually used for narrative-structures]
        This will be used in the next stage, for quick accessing files.
      
      ---
      
      ## Context
      {storyline}
      
      ---
      
      ## Improvement Feedback
      
      {feedback}
      
      <logic>
      if "IMPROVE" in feedback:
        Use the feedback to improve the storyline.
      
      if "REWRITE" in feedback:
        Use the feedback to rewrite the storyline.
      
      else:
        Ignore, and do nothing to influence the storyline.
      </logic>
      
      ---
      
      ## MANDATORY GUIDELINES
      
      - You MUST NOT change:
        - Who did what
        - Timeline order
        - Relationships
        - Logic structure
      - Use the knowledgebase to have a better understanding of how to write better storylines
      
      - **IMPORTANT**: Make sure to reflect on the storylines, and **make sure** it's **structurally sound** and passes **all mandatory** plausibility checks, like, **lives of people depend on it**.
      
      ---
      
      ## Genre-Specific Content
      
      {genre_specific_content}
      
      ---
      
      ## Validation Rules
      
      ### Universal Rules
      - Every alliance needs concrete stakes + mutual risk/benefit
      - Character motivations must be clear and consistent
      - Timeline must be logical and consistent
      - World rules must be established and followed
      
      ### Genre-Specific Rules
      
      {genre_validation_rules}
      
      ---
      
      ## Suspense and Pacing
      
      To invoke suspense and anticipation (Zeigarnik effect):
      - Build up to climactic events
      - Anchor the plot to a tangible central event
      - Create underlying current of momentum leading to it
      
      ---
      
      ## Examples
      {examples}
```

---

## Step 3: Usage in BookWorkflow

```python
# In cinema/workflow/book_workflow.py

async def init(self, **kwargs) -> Dict[str, Any]:
    genre = kwargs.get('genre', 'detective')
    
    if genre == 'detective':
        # OLD PATH: Static graph + DetectivePlotBuilder
        logger.info("Using detective-specific flow (static graph)")
        
        plotbuilder = DetectivePlotBuilder(ctx=self.ctx)
        critique = PlotCritique(ctx=self.ctx)
        
        # Build plot schema (old way)
        plot_schema = DetectivePlotBuilderSchema(
            characters=kwargs.get('characters'),
            relationships=kwargs.get('relationships'),
            killer=kwargs.get('killer'),
            victim=kwargs.get('victim'),
            # ... etc
        )
        
    else:
        # NEW PATH: PlotGraphFlow + GenericPlotBuilder
        logger.info(f"Using generic flow for genre: {genre}")
        
        # Step 1: Generate plot graph
        plotgraph_result = await self._generate_plotgraph(kwargs)
        self.state.plot_graph = plotgraph_result.plot_graph
        
        # Step 2: Convert to schema
        plot_schema = GenericPlotBuilderSchema.from_plotgraph(
            plot_graph=plotgraph_result.plot_graph,
            user_requirements=kwargs.get('user_requirements', ''),
            art_style=kwargs.get('art_style', ''),
            allowed_art_styles=", ".join(get_allowed_art_styles()),
            selected_art_styles=kwargs.get('selected_art_styles', ''),
        )
        
        # Step 3: Create generic crews
        plotbuilder = GenericPlotBuilder(ctx=self.ctx)
        critique = GenericPlotCritique(ctx=self.ctx)
    
    # Build StoryBuilder (same for both paths)
    flow = StoryBuilder.build(
        ctx=self.ctx,
        plotbuilder=plotbuilder,
        critique=critique,
        screenplay=screenplay,
        booker=booker,
        storyboard=storyboard,
    )
    
    # Set input (schema is different but interface is same)
    flow.state.input = StoryBuilderInput(
        plotbuilder=plot_schema,  # DetectivePlotBuilderSchema OR GenericPlotBuilderSchema
        # ... rest
    )
    
    # Run flow
    await flow.kickoff_async()
```

---

## Files to Create/Modify

### 1. ✅ `cinema/agents/bookwriter/crew.py`
- Add `GenericPlotBuilderSchema`
- `GenericPlotBuilder` already exists with bootstrap logic

### 2. ✅ `cinema/agents/bookwriter/plotbuilder/tasks.yaml`
- Update `plotbuilder.generic` section with all placeholders
- Already has genre overrides (detective, cyberpunk, shonen, horror, thriller)

### 3. ✅ `cinema/workflow/book_workflow.py`
- Add genre routing logic in `init()`
- Add `_generate_plotgraph()` method

### 4. ✅ `cinema/workflow/interface.py`
- Add `plot_graph` field to WorkflowState

### 5. ✅ `cinema/agents/bookwriter/plotgraph_flow.py`
- Implemented PlotGraphFlow with validation + retry loop

---

## Testing

```python
# Test 1: Detective (old way)
workflow = BookWorkflow(workflow_id="test1", ctx=ctx)
result = await workflow.init(
    genre="detective",
    characters="A, B, C",
    killer="A",
    victim="B",
)

# Test 2: Shonen (new way)
workflow = BookWorkflow(workflow_id="test2", ctx=ctx)
result = await workflow.init(
    genre="shonen",
    user_requirements="A young martial artist discovers special powers...",
    art_style="anime",
)
```

---

## Summary

The key insight: **GenericPlotBuilder works exactly like DetectivePlotBuilder**, just with different input schema and genre-aware task description.

1. PlotGraphFlow generates structured data
2. Convert to GenericPlotBuilderSchema (like DetectivePlotBuilderSchema)
3. Pass to GenericPlotBuilder.kickoff_async()
4. Task description has placeholders that get filled
5. LLM generates storyline

Same pattern, different data!


---

## Status Update

### ✅ Completed

1. **GenericPlotBuilderSchema** - Created in crew.py with all fields
2. **GenericPlotBuilder** - Already exists with bootstrap logic that handles genre overrides
3. **tasks.yaml generic section** - All placeholders present and verified
4. **Genre overrides** - detective, cyberpunk, shonen, horror, thriller all defined
5. **Genre alias system** - Maps anime→shonen, mystery→detective, etc.
6. **Removed unused placeholder** - `{genre_storyline_additions}` removed from tasks.yaml
7. **Fixed bootstrap method** - Changed from `.format()` to `str.replace()` to avoid KeyError
8. **Tests created** - `tests/test_generic_plotbuilder.py` verifies all functionality

### ✅ All Complete!

1. **BookWorkflow integration** - `_generate_plotgraph()` implemented, genre routing working
2. **StoryBuilder** - Updated to accept both DetectivePlotBuilderSchema and GenericPlotBuilderSchema
3. **PlotGraphFlow** - Implemented with validation + retry loop
4. **Tests** - Created test_plotgraph_flow.py (running successfully)

### 📝 Notes

- **WorkflowOrchestrator** manages jobs, **BookWorkflow** executes work
- **Type hints** use `Any` to avoid circular imports
- **Flow listeners** fixed to avoid name conflicts

---

## Key Insight: Bootstrap Uses str.replace()

The `bootstrap(genres)` method handles filling genre override placeholders:
- It finds matching genre overrides (using alias mapping)
- Concatenates all matching overrides for each placeholder
- Uses `str.replace()` to fill ONLY genre placeholders (not schema placeholders)
- Returns a Task with genre overrides filled, schema placeholders preserved

So when `kickoff_async(inputs=schema.model_dump())` is called:
- Genre placeholders (`{genre_roles}`, etc.) are already filled by bootstrap
- CrewAI only needs to fill schema placeholders (`{genres}`, `{characters}`, etc.)
- No additional `.format()` call needed!

**Flow:**
```python
# 1. Bootstrap fills genre overrides
plotbuilder = GenericPlotBuilder(ctx=ctx)
plotbuilder.bootstrap(genres=["shonen", "detective"])
# → description now has {genre_roles} filled with shonen + detective roles

# 2. Kickoff fills schema fields
schema = GenericPlotBuilderSchema.from_plotgraph(plot_graph, ...)
result = await plotbuilder.crew().kickoff_async(inputs=schema.model_dump())
# → CrewAI fills {genres}, {characters}, etc. from schema
```
