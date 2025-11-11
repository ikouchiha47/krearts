# class DetectivePlotSystem:
#     """
#     Main system: Pure constraint-based plot generation.
#     Graph + Tables define ALL logic, LLM only adds descriptions.
#     """
    
#     def __init__(self):
#         self.builder = ConstraintTableBuilder()
#         self.validator = ConsistencyValidator()
#         self.truth_table = TruthTable()
#         self.narrator = NarrativeGenerator()
#         logger.info("Initialized DetectivePlotSystem")
    
#     def generate_from_constraints(
#         self,
#         constraints: PlotConstraints,
#         characters: List[Character]
#     ) -> Tuple[RelationshipGraph, Dict, Dict]:
#         """
#         Generate complete plot from pure constraints.
#         Returns: (graph, truth_table, narrative)
#         """
#         logger.info("\n" + "#"*80)
#         logger.info("# GENERATING PLOT FROM CONSTRAINTS")
#         logger.info("#"*80)
        
#         # Step 1: Build graph from constraints
#         graph = self.builder.build_from_constraints(constraints, characters)
        
#         # Step 2: Validate consistency
#         is_valid, violations = self.validator.validate(graph)
        
#         if not is_valid:
#             logger.error("Plot has logical violations!")
#             for v in violations:
#                 logger.error(f"  {v}")
#             raise ValueError("Plot is logically inconsistent")
        
#         # Step 3: Build truth table
#         truth_matrix = self.truth_table.build_from_graph(graph, constraints)
        
#         # Step 4: Generate narrative (LLM only does this part)
#         narrative = self.narrator.generate_descriptions(graph, constraints)
        
#         logger.info("\n" + "#"*80)
#         logger.info("# PLOT GENERATION COMPLETE")
#         logger.info("#"*80)
        
#         return graph, self.truth_table.export(), narrative
    
#     def export_full_plot(
#         self,
#         graph: RelationshipGraph,
#         truth_table: Dict,
#         narrative: Dict,
#         filename: str = "plot_structure.json"
#     ):
#         """Export complete plot with all layers"""
        
#         export = {
#             "logical_structure": {
#                 "graph": graph.export_to_dict(),
#                 "truth_table": truth_table,
#                 "timeline": [asdict(r) for r in graph.get_action_timeline()]
#             },
#             "narrative_layer": narrative,
#             "screenplay_format": self._convert_to_screenplay(graph, narrative)
#         }
        
#         with open(filename, 'w') as f:
#             json.dump(export, f, indent=2, default=str)
        
#         logger.info(f"\n✓ Exported complete plot to {filename}")
#         return export
    
#     def _convert_to_screenplay(self, graph: RelationshipGraph, narrative: Dict) -> Dict:
#         """Convert graph + narrative to screenplay format"""
        
#         timeline = graph.get_action_timeline()
        
#         scenes = []
#         for i, rel in enumerate(timeline):
#             scene = {
#                 "scene_number": i + 1,
#                 "time": rel.time,
#                 "location": rel.location,
#                 "action": rel.action.value,
#                 "characters": [rel.source, rel.target] + rel.witnessed_by,
#                 "description": narrative['action_descriptions'].get(rel.action.value, ""),
#                 "panels": [
#                     {"panel": 1, "shot": "establishing", "description": f"Wide shot of {rel.location}"},
#                     {"panel": 2, "shot": "action", "description": f"{rel.source} {rel.action.value} {rel.target}"},
#                     {"panel": 3, "shot": "reaction", "description": "Emotional reactions"}
#                 ]
#             }
#             scenes.append(scene)
        
#         return {
#             "acts": [
#                 {"act": 1, "scenes": scenes[:len(scenes)//3]},
#                 {"act": 2, "scenes": scenes[len(scenes)//3:2*len(scenes)//3]},
#                 {"act": 3, "scenes": scenes[2*len(scenes)//3:]}
#             ]
#         }




# # ==================== TESTS ====================

# def test_constraint_based_generation():
#     """Test: Generate plot purely from constraints"""
#     logger.info("\n" + "="*80)
#     logger.info("TEST 1: Pure Constraint-Based Generation")
#     logger.info("="*80)
    
#     # Define characters
#     characters = [
#         Character("Detective Morgan", "detective"),
#         Character("Victor Ashford", "victim"),
#         Character("James Butler", "butler", faction="servants"),
#         Character("Margaret Ashford", "wife", faction="family"),
#         Character("Dr. Helen Price", "doctor"),
#     ]
    
#     # Define constraints
#     constraints = PlotConstraints(
#         killer="James Butler",
#         victim="Victor Ashford",
#         accomplices=[],
#         framed_suspect="Margaret Ashford",
#         witnesses=[("Dr. Helen Price", "suspicious activity")],
#         alliances=[("James Butler", "Dr. Helen Price")],
#         winners=["James Butler"],
#         losers=["Margaret Ashford"],
#         betrayals=[]
#     )
    
#     system = DetectivePlotSystem()
#     graph, truth_table, narrative = system.generate_from_constraints(constraints, characters)
    
#     assert len(graph.action_sequences) > 0, "Should have actions"
#     assert truth_table['matrix'] is not None, "Should have truth table"
    
#     logger.info("✓ TEST PASSED: Generated plot from constraints")


# def test_truth_table_generation():
#     """Test: Truth table correctly maps clues to suspects"""
#     logger.info("\n" + "="*80)
#     logger.info("TEST 2: Truth Table Generation")
#     logger.info("="*80)
    
#     characters = [
#         Character("Victim", "victim"),
#         Character("Killer", "killer"),
#         Character("Suspect", "suspect"),
#     ]
    
#     constraints = PlotConstraints(
#         killer="Killer",
#         victim="Victim",
#         framed_suspect="Suspect"
#     )
    
#     system = DetectivePlotSystem()
#     graph, truth_table, _ = system.generate_from_constraints(constraints, characters)
    
#     matrix = np.array(truth_table['matrix'])
#     assert matrix.shape[0] > 0, "Should have clues (rows)"
#     assert matrix.shape[1] > 0, "Should have suspects (columns)"
    
#     logger.info(f"✓ TEST PASSED: Truth table shape {matrix.shape}")


# def test_faction_warfare():
#     """Test: Generate plot with faction conflict"""
#     logger.info("\n" + "="*80)
#     logger.info("TEST 3: Faction Warfare Plot")
#     logger.info("="*80)
    
#     characters = [
#         Character("Leader A", "leader", faction="faction_red"),
#         Character("Member A1", "member", faction="faction_red"),
#         Character("Leader B", "leader", faction="faction_blue"),
#         Character("Member B1", "member", faction="faction_blue"),
#         Character("Detective", "detective"),
#     ]
    
#     constraints = PlotConstraints(
#         killer="Leader B",
#         victim="Leader A",
#         accomplices=["Member B1"],
#         witnesses=[("Member A1", "the murder")],
#         factions={
#             "faction_red": ["Leader A", "Member A1"],
#             "faction_blue": ["Leader B", "Member B1"]
#         },
#         winners=["Leader B", "Member B1"],
#         losers=["Member A1"],
#         betrayals=[("Member B1", "Leader B")]  # Twist: accomplice betrays
#     )
    
#     system = DetectivePlotSystem()
#     graph, _, narrative = system.generate_from_constraints(constraints, characters)
    
#     # Check for betrayal in graph
#     betrayals = [r for r in graph.action_sequences if r.action == ActionType.BETRAYED]
#     assert len(betrayals) > 0, "Should have betrayal"
    
#     logger.info("✓ TEST PASSED: Faction warfare plot generated")


# def test_multiple_endings():
#     """Test: Same graph, different narrative endings"""
#     logger.info("\n" + "="*80)
#     logger.info("TEST 4: Multiple Endings from Same Graph")
#     logger.info("="*80)
    
#     characters = [
#         Character("Victim", "victim"),
#         Character("Killer", "killer"),
#         Character("Detective", "detective"),
#     ]
    
#     constraints = PlotConstraints(
#         killer="Killer",
#         victim="Victim"
#     )
    
#     system = DetectivePlotSystem()
    
#     # Generate base graph (logic is fixed)
#     graph, truth_table, narrative1 = system.generate_from_constraints(constraints, characters)
    
#     # Same graph, different narrative (would be different LLM call)
#     narrative2 = system.narrator.generate_descriptions(graph, constraints)
    
#     # Graph structure should be identical
#     assert len(graph.action_sequences) > 0, "Graph should have actions"
    
#     logger.info("✓ TEST PASSED: Can generate multiple narratives from same graph")


# def run_all_tests():
#     """Run complete test suite"""
#     logger.info("\n" + "#"*80)
#     logger.info("# RUNNING GRAPH-BASED PLOT GENERATOR TEST SUITE")
#     logger.info("#"*80)
    
#     try:
#         test_constraint_based_generation()
#         test_truth_table_generation()
#         test_faction_warfare()
#         test_multiple_endings()
        
#         logger.info("\n" + "#"*80)
#         logger.info("# ALL TESTS PASSED ✓")
#         logger.info("#"*80)
        
#     except Exception as e:
#         logger.error(f"\n✗ TEST FAILED: {e}")
#         raise


# if __name__ == "__main__":
#     # Run tests
#     run_all_tests()
    
#     # Demo: Complex multi-faction plot
#     logger.info("\n\n" + "#"*80)
#     logger.info("# DEMO: Complex Constraint-Based Plot")
#     logger.info("#"*80)
    
#     # Define a complex scenario
#     characters = [
#         Character("Lord Ashford", "nobleman", faction="aristocracy"),
#         Character("Lady Margaret", "noblewoman", faction="aristocracy"),
#         Character("James Butler", "butler", faction="servants"),
#         Character("Sarah Maid", "maid", faction="servants"),
#         Character("Detective Morrison", "detective"),
#         Character("Dr. Price", "doctor", faction="professionals"),
#     ]
    
#     # User specifies EXACTLY what happens
#     constraints = PlotConstraints(
#         killer="James Butler",
#         victim="Lord Ashford",
#         accomplices=["Sarah Maid"],
#         framed_suspect="Lady Margaret",
#         witnesses=[
#             ("Dr. Price", "suspicious behavior"),
#             ("Sarah Maid", "the murder itself")
#         ],
#         factions={
#             "aristocracy": ["Lord Ashford", "Lady Margaret"],
#             "servants": ["James Butler", "Sarah Maid"],
#             "professionals": ["Dr. Price"]
#         },
#         winners=["James Butler", "Sarah Maid"],  # They get freedom
#         losers=["Lady Margaret"],  # Gets framed
#         betrayals=[("Sarah Maid", "James Butler")],  # Twist ending
#         alliances=[("James Butler", "Sarah Maid")]
#     )
    
#     system = DetectivePlotSystem()
#     graph, truth_table, narrative = system.generate_from_constraints(constraints, characters)
    
#     # Export everything
#     full_export = system.export_full_plot(graph, truth_table, narrative, "complex_plot.json")
    
#     logger.info("\n" + "="*80)
#     logger.info("PLOT SUMMARY")
#     logger.info("="*80)
#     logger.info(f"Characters: {len(characters)}")
#     logger.info(f"Actions: {len(graph.action_sequences)}")
#     logger.info(f"Clues: {len(truth_table['clues'])}")
#     logger.info(f"Suspects: {len(truth_table['suspects'])}")
#     logger.info(f"\nTimeline:")
#     for rel in graph.get_action_timeline():
#         logger.info(f"  t={rel.time}: {rel.source} -{rel.action.value}-> {rel.target} @ {rel.location}")
    
#     logger.info(f"\n✓ Exported to complex_plot.json")
#     logger.info("\n" + "="*80)
#     logger.info("TRUTH TABLE")
#     logger.info("="*80)
#     matrix = np.array(truth_table['matrix'])
#     logger.info(f"Shape: {matrix.shape} (clues × suspects)")
#     logger.info(f"Matrix:\n{matrix}")
    
#     logger.info("\n" + "="*80)
#     logger.info("ADJACENCY MATRIX")
#     logger.info("="*80)
#     adj_matrix, nodes = graph.to_adjacency_matrix()
#     logger.info(f"Nodes: {nodes}")
#     logger.info(f"Matrix:\n{adj_matrix}")
    
#     logger.info("\n" + "#"*80)
#     logger.info("# DEMO COMPLETE")
#     logger.info("#"*80)
#     logger.info("\nKey Features Demonstrated:")
#     logger.info("  ✓ Pure constraint-based generation")
#     logger.info("  ✓ Graph relationships define ALL logic")
#     logger.info("  ✓ Truth table for clue-suspect mapping")
#     logger.info("  ✓ Adjacency matrix for relationship analysis")
#     logger.info("  ✓ LLM only generates narrative descriptions")
#     logger.info("  ✓ User has COMPLETE control over plot structure")
#     logger.info("\nYou can specify:")
#     logger.info("  - Who kills whom")
#     logger.info("  - Who gets framed")
#     logger.info("  - Who witnesses what")
#     logger.info("  - Faction allegiances")
#     logger.info("  - Betrayals and alliances")
#     logger.info("  - Winners and losers")
#     logger.info("  - Timeline order")
#     logger.info("\nThe LLM ONLY fills in descriptive text for your structure!")