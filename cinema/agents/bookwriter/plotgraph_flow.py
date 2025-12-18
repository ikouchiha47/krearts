"""
PlotGraph Flow - Validation + Retry Loop

Generates and validates plot graphs with automatic retry on validation failures.
"""

import logging
from typing import Optional

from crewai.flow.flow import Flow, listen, router, start, or_
from pydantic import BaseModel, Field

from cinema.agents.bookwriter.crew import PlotGraphBuilder, PlotGraphOutput
from cinema.agents.bookwriter.graph_validator import PlotValidationSystem, ValidationResult
from cinema.context import DirectorsContext

logger = logging.getLogger(__name__)


class PlotGraphFlowInput(BaseModel):
    """Input for PlotGraphFlow"""
    seed: str = Field(..., description="Story seed/requirements")
    art_style: Optional[str] = Field(None, description="Art style preference")
    max_retries: int = Field(default=3, description="Maximum retry attempts")


class PlotGraphFlowState(BaseModel):
    """State for PlotGraphFlow"""
    input: PlotGraphFlowInput = Field(default_factory=lambda: PlotGraphFlowInput(seed="", max_retries=3))
    
    # Iteration tracking
    current_iteration: int = 0
    max_iterations: int = 3
    current_state: str = "start"
    
    # Current attempt
    plot_graph: Optional[PlotGraphOutput] = None
    validation_result: Optional[ValidationResult] = None
    
    # History
    context: str = ""  # Previous iteration's output
    feedback: str = ""  # Validation feedback
    
    # Final output
    output: Optional["PlotGraphFlowOutput"] = None
    is_valid: bool = False


class PlotGraphFlowOutput(BaseModel):
    """Output from PlotGraphFlow"""
    plot_graph: PlotGraphOutput
    validation_result: ValidationResult
    iterations: int
    is_valid: bool


# Rebuild model to resolve forward references
PlotGraphFlowState.model_rebuild()


class PlotGraphFlow(Flow[PlotGraphFlowState]):
    """Flow for generating and validating plot graphs with retry logic"""
    
    def __init__(self, ctx: DirectorsContext):
        super().__init__()
        self.ctx = ctx
        self._plotgraph_crew = None
    
    @start()
    def resume(self):
        """Entry point - returns current state"""
        logger.info("Starting PlotGraph Flow")
        
        if self.state.output is None:
            self.state.output = PlotGraphFlowOutput(
                plot_graph=PlotGraphOutput(
                    genres=["generic"],
                    primary_genre="generic",
                    title="",
                    theme="",
                    narrative_structure="three-act",
                ),
                validation_result=ValidationResult(is_valid=False, violations=[], warnings=[]),
                iterations=0,
                is_valid=False,
            )
        
        return self.state.current_state
    
    @router(resume)
    def director(self):
        """Route to appropriate step based on current state"""
        
        if self.state.current_state == "start":
            self.state.current_state = "extract"
        
        logger.info(f"Directing to: {self.state.current_state}")
        return self.state.current_state
    
    @listen("extract")
    async def extract_graph(self):
        """Extract plot graph from seed"""
        
        logger.info(f"[Iteration {self.state.current_iteration + 1}/{self.state.max_iterations}] Extracting plot graph...")
        
        # Build input for PlotGraphBuilder
        inputs_dict = {
            "seed": self.state.input.seed,
            "art_style": self.state.input.art_style or "",
            "context": self.state.context,
            "feedback": self.state.feedback,
        }
        
        # Run PlotGraphBuilder
        if self._plotgraph_crew is None:
            self._plotgraph_crew = PlotGraphBuilder(ctx=self.ctx).crew()
        
        result = await self._plotgraph_crew.kickoff_async(inputs=inputs_dict)
        
        # Collect output
        plot_graph = PlotGraphBuilder.collect(result, output_model=PlotGraphOutput)
        
        if not plot_graph:
            raise ValueError("PlotGraphBuilder returned None")
        
        # Update state
        self.state.plot_graph = plot_graph
        self.state.current_iteration += 1
        self.state.current_state = "validate"
        
        logger.info(f"✓ Plot graph extracted ({len(plot_graph.characters)} characters, {len(plot_graph.events)} events)")
    
    @listen(extract_graph)
    def validate_graph(self):
        """Validate plot graph against genre rules"""
        
        if not self.state.plot_graph:
            raise ValueError("No plot graph to validate")
        
        logger.info("Validating plot graph...")
        
        # Run PIS validation (structure-based)
        from cinema.agents.bookwriter.plot_invariant_validator import validate_plot_structure
        
        plot_score = validate_plot_structure(self.state.plot_graph)
        
        # Convert to old ValidationResult format for compatibility
        from cinema.agents.bookwriter.graph_validator import ValidationResult, Violation, ViolationSeverity
        
        violations = []
        if not plot_score.is_valid:
            for feature, data in plot_score.breakdown.items():
                if data["raw"] == 0.0:
                    violations.append(Violation(
                        severity=ViolationSeverity.HIGH,
                        message=f"Plot missing {feature}: {self._get_feature_description(feature)}",
                        suggestion=self._get_feature_suggestion(feature)
                    ))
                elif data["raw"] == 0.5:
                    violations.append(Violation(
                        severity=ViolationSeverity.MEDIUM,
                        message=f"Plot has weak {feature}: {self._get_feature_description(feature)}",
                        suggestion=self._get_feature_suggestion(feature)
                    ))
        
        validation_result = ValidationResult(
            is_valid=plot_score.is_valid,
            violations=violations,
            warnings=[plot_score.interpretation]
        )
        
        # Update state
        self.state.validation_result = validation_result
        self.state.is_valid = validation_result.is_valid
        
        logger.info(f"Validation: {'✓ PASS' if validation_result.is_valid else '✗ FAIL'}")
        logger.info(f"  Violations: {len(validation_result.violations)}")
        logger.info(f"  Warnings: {len(validation_result.warnings)}")
    
    @router(validate_graph)
    def evaluate(self):
        """Decide whether to retry or finalize"""
        
        validation = self.state.validation_result
        
        if not validation:
            logger.error("No validation result available")
            return "finalize"
        
        # Check if valid
        if validation.is_valid:
            logger.info("✓ Plot graph is valid!")
            return "finalize"
        
        # Check if max retries reached
        if self.state.current_iteration >= self.state.max_iterations:
            logger.warning(f"✗ Max retries ({self.state.max_iterations}) reached")
            return "finalize"
        
        # Has critical or high violations - retry
        critical_or_high = [v for v in validation.violations 
                           if v.severity in ["critical", "high"]]
        
        if critical_or_high:
            logger.info(f"Retrying due to {len(critical_or_high)} critical/high violations")
            
            # Build feedback
            feedback_parts = []
            
            for v in critical_or_high:
                feedback_parts.append(f"[{v.severity.upper()}] {v.message}")
                if v.suggestion:
                    feedback_parts.append(f"  → {v.suggestion}")
            
            if validation.warnings:
                feedback_parts.append("\nIMPROVEMENTS:")
                for w in validation.warnings:
                    feedback_parts.append(f"  - {w}")
            
            # Update state for retry
            if self.state.plot_graph:
                self.state.context = self.state.plot_graph.model_dump_json(indent=2)
            self.state.feedback = "\n".join(feedback_parts)
            
            return "extract"  # Retry - this triggers @listen("extract")
        
        # Minor issues only - accept it
        logger.info("Minor issues only, accepting plot graph")
        return "finalize"
    
    @listen("finalize")
    def handle_finalize(self):
        """Finalize and prepare output"""
        
        logger.info("Finalizing plot graph flow")
        
        if not self.state.plot_graph or not self.state.validation_result:
            raise ValueError("Cannot finalize without plot_graph and validation_result")
        
        self.state.output = PlotGraphFlowOutput(
            plot_graph=self.state.plot_graph,
            validation_result=self.state.validation_result,
            iterations=self.state.current_iteration,
            is_valid=self.state.is_valid
        )
        
        logger.info(f"✓ Flow complete in {self.state.current_iteration} iterations")
    
    def _get_feature_description(self, feature: str) -> str:
        """Get description of PIS feature"""
        descriptions = {
            "agency": "At least one protagonist must participate in events",
            "intent": "Characters must have motivations/goals",
            "opposition": "There must be resistance/conflict",
            "causality": "Events must influence each other",
            "change": "Something must change (character/world/knowledge)",
            "escalation": "Stakes/pressure must increase",
            "irreversibility": "Some change must be permanent"
        }
        return descriptions.get(feature, "")
    
    def _get_feature_suggestion(self, feature: str) -> str:
        """Get suggestion for fixing PIS feature"""
        suggestions = {
            "agency": "Add events where protagonist takes action",
            "intent": "Add character motivations/goals",
            "opposition": "Add opposing relationships or obstacles",
            "causality": "Add outcomes to events that affect later events",
            "change": "Add character arcs or event outcomes",
            "escalation": "Make later events have higher stakes",
            "irreversibility": "Add permanent consequences (death, revelation, etc.)"
        }
        return suggestions.get(feature, "")
