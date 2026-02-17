# Cinema Hybrid Model Strategy

## Current Pain Points
- **GPT-5 for novel generation**: Very expensive, rate limited
- **GPT-4.1 for planning**: Expensive for creative tasks
- **All tool calling through OpenAI**: Burning credits on simple orchestration

## Recommended Hybrid Architecture

### Phase 1: Strategic Model Routing

#### **Keep OpenAI For** (20% of tasks)
```python
# High-value, tool-calling heavy tasks
OPENAI_TASKS = {
    "workflow_orchestration": "gpt-4.1",      # Complex tool calling
    "quality_critique": "gpt-4.1",            # Critical validation  
    "plot_structure": "gpt-4.1",              # Complex reasoning
    "comic_adaptation": "gpt-4.1",            # JSON schema compliance
}
```

#### **Move to Local Models** (80% of tasks)
```python
# Creative, bulk content generation
LOCAL_TASKS = {
    "novel_writing": "gemma-2-ataraxy-9b",     # Creative prose
    "character_dialogue": "gemma-2-ataraxy-9b", # Character voices
    "scene_descriptions": "gemma-2-ataraxy-9b", # Visual narratives
    "character_backstories": "gemma-2-ataraxy-9b", # Creative development
}
```

### Phase 2: Implementation Strategy

#### **1. Create Model Router**
```python
# cinema/registry.py - Add hybrid configuration
HybridHerd = (
    GenerationHerd()
    # OpenAI for tool calling & critical reasoning
    .register_model("planner", ModelConfig(name="openai/gpt-4.1", ...))
    .register_model("critique", ModelConfig(name="openai/gpt-4.1", ...))
    .register_model("executor", ModelConfig(name="openai/gpt-4.1", ...))
    
    # Local models for creative tasks
    .register_model("creative_writer", ModelConfig(name="ollama/gemma-2-ataraxy-9b", ...))
    .register_model("dialogue_writer", ModelConfig(name="ollama/gemma-2-ataraxy-9b", ...))
    .register_model("scene_writer", ModelConfig(name="ollama/gemma-2-ataraxy-9b", ...))
)
```

#### **2. Task Classification System**
```python
class TaskRouter:
    def route_task(self, task_type: str, requires_tools: bool = False) -> str:
        if requires_tools or task_type in ["planning", "critique", "orchestration"]:
            return "openai"
        elif task_type in ["creative_writing", "dialogue", "descriptions"]:
            return "local"
        else:
            return "openai"  # Safe fallback
```

#### **3. Workflow Modifications**

**BookWorkflow Changes:**
- **init()**: Keep OpenAI (complex tool calling for plot structure)
- **generate_content()**: Split - OpenAI for structure, Local for prose
- **generate_chapters()**: OpenAI for JSON schema, Local for content
- **generate_pages()**: Keep OpenAI (complex tool calling)

### Phase 3: Specific Workflow Optimizations

#### **Story Generation Pipeline**
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   OpenAI GPT-4  │    │  Gemma-Ataraxy  │    │   OpenAI GPT-4  │
│                 │    │                  │    │                 │
│ 1. Plot Planning│───▶│ 2. Novel Writing │───▶│ 3. Comic Schema │
│ 4. Critique     │    │ 5. Dialogue Gen  │    │ 6. Orchestration│
│ 7. Validation   │    │ 8. Descriptions  │    │ 9. Tool Calling │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

#### **Cost Optimization Targets**
- **Novel Generation**: 90% cost reduction (GPT-5 → Local)
- **Dialogue/Descriptions**: 95% cost reduction (GPT-4 → Local)  
- **Character Development**: 95% cost reduction (GPT-4 → Local)
- **Overall Pipeline**: 60-70% cost reduction

### Phase 4: Quality Safeguards

#### **Validation Pipeline**
```python
# After local model generation, validate with OpenAI
async def validate_creative_output(content: str, task_type: str) -> bool:
    if len(content) < MIN_LENGTH[task_type]:
        return False
    
    # Use cheap OpenAI model for quality check
    critique = await openai_critique(content, task_type)
    return critique.quality_score > QUALITY_THRESHOLD
```

#### **Fallback Strategy**
```python
# If local model fails, fallback to OpenAI
async def generate_with_fallback(task_type: str, **kwargs):
    try:
        result = await local_model_generate(task_type, **kwargs)
        if validate_output(result):
            return result
    except Exception as e:
        logger.warning(f"Local model failed: {e}")
    
    # Fallback to OpenAI
    return await openai_generate(task_type, **kwargs)
```

## Implementation Priority

### **Week 1: Model Router**
- [ ] Create HybridHerd configuration
- [ ] Implement TaskRouter class
- [ ] Add local model support to registry

### **Week 2: Creative Tasks Migration**
- [ ] Move novel generation to local model
- [ ] Move dialogue generation to local model
- [ ] Add validation pipeline

### **Week 3: Testing & Optimization**
- [ ] A/B test quality vs OpenAI baseline
- [ ] Measure cost savings
- [ ] Fine-tune routing decisions

### **Week 4: Production Deployment**
- [ ] Deploy hybrid system
- [ ] Monitor quality metrics
- [ ] Optimize based on real usage

## Expected Results

### **Cost Savings**
- **Current**: ~$50-100 per story (all OpenAI)
- **Hybrid**: ~$15-30 per story (60-70% reduction)
- **ROI**: Break-even after ~20 stories

### **Performance**
- **Speed**: 2-3x faster (local models)
- **Quality**: 90-95% of OpenAI quality for creative tasks
- **Reliability**: Better (no rate limits on local)

### **Scalability**
- **Concurrent Stories**: 10x improvement
- **Rate Limits**: Eliminated for creative tasks
- **Infrastructure**: More predictable costs