"""
Pipecleaner: Run-scoped global corpus deduplication for multi-agent systems.

V2.0: Global ClusterBank with dynamic batching barrier (5-10s) for cross-prompt deduplication.
- Run-scoped corpus: All prompts in a run share a global ClusterBank
- SimHash near-dup matching: Hamming distance ≤6 for 64-bit fingerprints
- Dynamic barrier: 5s min, +2s per arrival (cap 10s), maximizes dedupe by collecting bursts
- Canonical ownership: First prompt to use a cluster owns it, others drop duplicates
- Entity coverage: 95% threshold RUN-LEVEL (cumulative across all batches, not per-batch)

Algorithm:
1. Intercept prompt → split sentences → compute SimHash signatures
2. Match against ClusterBank (Hamming ≤6) → assign cluster_id or create new
3. Queue prompt into micro-batch, extend barrier (+2s per arrival, cap 10s)
4. On timer: cross-prompt dedupe (keep only canonical owners)
5. RUN-LEVEL entity coverage check (95% cumulative across entire run), re-add if needed
6. Emit cleaned prompts (original sentence order preserved)

Expected savings: 50-90% char reduction with 95%+ entity coverage across entire run.
Later batches are MORE aggressive (earlier batches already covered entities).
"""

import re
import hashlib
import threading
import time
from typing import List, Dict, Set, Tuple, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict
import numpy as np
import asyncio

# Type alias for return type
DeduplicationResult = Tuple[str, Dict]

# Lazy imports for performance (only load when needed)
_embedding_model = None
_spacy_nlp = None
_model_lock = threading.Lock()  # Thread-safe singleton access


def _vprint(message: str, verbose: bool = False, force: bool = False):
    """Helper function for verbose printing."""
    if force or verbose:
        print(message)


def _get_embedding_model():
    """
    Lazy load sentence transformer model (thread-safe singleton).
    Forces CPU to avoid meta tensor issues on Win + Py3.13 + Torch.
    """
    global _embedding_model
    
    # Double-checked locking pattern for performance
    if _embedding_model is None:
        with _model_lock:
            # Check again inside lock (another thread might have loaded it)
            if _embedding_model is None:
                try:
                    from sentence_transformers import SentenceTransformer
                    _vprint("[PIPECLEANER] Loading embedding model: all-MiniLM-L6-v2 (384-dim, ~80MB)...", True)
                    # Force CPU device to avoid meta tensor issues
                    _embedding_model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
                    _vprint("[PIPECLEANER] ✅ Embedding model loaded successfully (CPU)", True)
                except ImportError:
                    _vprint("[PIPECLEANER] ⚠️  sentence-transformers not installed. Install: pip install sentence-transformers", True)
                    raise
                except Exception as e:
                    _vprint(f"[PIPECLEANER] ⚠️  Failed to load embedding model: {e}", True)
                    raise
    
    return _embedding_model


def _get_spacy_model():
    """Lazy load spaCy model for entity extraction."""
    global _spacy_nlp
    if _spacy_nlp is None:
        try:
            import spacy
            _vprint("[PIPECLEANER] Loading spaCy model: en_core_web_sm...", True)
            _spacy_nlp = spacy.load("en_core_web_sm")
            _vprint("[PIPECLEANER] ✅ spaCy model loaded successfully", True)
        except ImportError:
            _vprint("[PIPECLEANER] ⚠️  spaCy not installed. Using regex fallback for entities.", True)
            _spacy_nlp = "fallback"
        except OSError:
            _vprint("[PIPECLEANER] ⚠️  spaCy model not found. Using regex fallback for entities.", True)
            _spacy_nlp = "fallback"
    return _spacy_nlp


# ============================================================================
# Run-Scoped Global Corpus System V2.0
# ============================================================================

@dataclass
class SentenceCluster:
    """Represents a cluster of similar sentences across the run."""
    cluster_id: str
    canonical_sentence: str
    owner_prompt_id: str  # First prompt to use this cluster
    simhash: int  # 64-bit SimHash fingerprint
    salience: float
    entities: Set[str]
    first_seen_seq: int
    length: int
    embedding: Optional[np.ndarray] = None  # Sentence embedding for cosine similarity
    
@dataclass
class PromptState:
    """State for a single prompt in the batch."""
    prompt_id: str
    sentences: List[str]
    cluster_ids: List[str]  # parallel to sentences
    original_order: List[int]  # track reordering
    entities: Set[str]
    arrived_at: float
    
@dataclass
class RunCorpusTelemetry:
    """Run-level statistics for the corpus."""
    prompts_total: int = 0
    sentences_total: int = 0
    clusters_total: int = 0
    cross_prompt_dups_removed: int = 0
    chars_in: int = 0
    chars_out: int = 0
    tokens_saved: int = 0
    entity_coverage_avg: float = 100.0
    batches_processed: int = 0
    avg_barrier_ms: float = 0.0
    max_barrier_ms: float = 0.0
    barrier_times: List[float] = field(default_factory=list)


def compute_simhash(text: str, hash_bits: int = 64) -> int:
    """
    Compute SimHash fingerprint for near-dup detection.
    
    Args:
        text: Input text
        hash_bits: Hash size (64-bit default)
    
    Returns:
        Integer hash value
    """
    # Tokenize and compute feature hashes
    tokens = re.findall(r'\b\w+\b', text.lower())
    if not tokens:
        return 0
    
    # Initialize bit vector
    v = [0] * hash_bits
    
    for token in tokens:
        # Hash each token
        h = int(hashlib.md5(token.encode()).hexdigest(), 16)
        
        # Update bit vector
        for i in range(hash_bits):
            if h & (1 << i):
                v[i] += 1
            else:
                v[i] -= 1
    
    # Generate final hash
    fingerprint = 0
    for i in range(hash_bits):
        if v[i] > 0:
            fingerprint |= (1 << i)
    
    return fingerprint


def hamming_distance(hash1: int, hash2: int) -> int:
    """Count differing bits between two hashes."""
    return bin(hash1 ^ hash2).count('1')


class RunScopedCorpus:
    """
    Global corpus for a single run, with dynamic batching barrier.
    All prompts in the run share this corpus for cross-prompt deduplication.
    
    CONCURRENCY MODEL:
    - All shared state (clusters, prompt_registry, run_entities, kept_entities, batch_queue)
      is protected by `self.batch_lock` (threading.Lock)
    - All reads iterate over snapshots (dict(...), list(...)) to avoid "dict changed size" errors
    - All writes are atomic under lock (copy-on-write when possible)
    - Re-entrancy guard in caller (DaseinCallbackHandler) prevents nested calls
    - Background timer thread (_process_batch) acquires lock before any mutations
    """
    
    def __init__(self, run_id: str, hamming_threshold: int = 6, entity_coverage_min: float = 0.95, verbose: bool = False):
        self.run_id = run_id
        self.hamming_threshold = hamming_threshold
        self.entity_coverage_min = entity_coverage_min
        self.verbose = verbose  # Gate debug logging
        
        # Core state
        self.clusters: Dict[str, SentenceCluster] = {}  # cluster_id → cluster
        self.simhash_index: Dict[int, List[str]] = defaultdict(list)  # simhash → [cluster_ids]
        self.prompt_registry: Dict[str, PromptState] = {}  # prompt_id → state
        self.entity_index: Dict[str, Set[str]] = defaultdict(set)  # entity → {cluster_ids}
        
        # Run-level entity tracking for global coverage
        self.run_entities: Set[str] = set()  # All entities seen across entire run
        self.kept_entities: Set[str] = set()  # All entities kept across all batches
        
        # Batching state
        self.batch_queue: List[str] = []  # [prompt_ids] waiting for barrier
        self.batch_lock = threading.Lock()  # Protects batch_queue, batch_timer, etc.
        self.processing_lock = threading.Lock()  # CRITICAL: Ensures only ONE batch processes at a time
        self.batch_timer: Optional[threading.Timer] = None
        self.batch_start_time: Optional[float] = None
        self.barrier_duration: float = 5.0  # Start at 5s (min wait)
        self.barrier_increment: float = 2.0  # Add 2s per new arrival
        self.barrier_cap: float = 10.0  # Max 10s
        self.batch_ready = threading.Event()  # Signal when batch is processed
        self.prompt_events: Dict[str, asyncio.Event] = {}  # Per-prompt events for ASYNC sequential release
        self.prompt_loops: Dict[str, asyncio.AbstractEventLoop] = {}  # Event loops for thread-safe signaling
        
        # Sequence tracking
        self.next_seq = 0
        self.next_cluster_id = 0
        
        # Telemetry
        self.telemetry = RunCorpusTelemetry()
        
        _vprint(f"[CORPUS] 🏗️  Created run-scoped corpus for run_id={run_id[:8]} (barrier: 5s min, +2s/arrival, 10s cap)", self.verbose)
    
    def _generate_cluster_id(self) -> str:
        """Generate unique cluster ID."""
        cluster_id = f"c{self.next_cluster_id:06d}"
        self.next_cluster_id += 1
        return cluster_id
    
    def find_matching_cluster(self, simhash: int, sentence: str, sentence_embedding=None) -> Optional[str]:
        """
        Find existing cluster that matches this sentence using cosine similarity.
        
        Args:
            simhash: SimHash of the sentence (for indexing, not matching)
            sentence: Original sentence text
            sentence_embedding: Pre-computed embedding for this sentence
        
        Returns:
            cluster_id if match found, None otherwise
        """
        if sentence_embedding is None:
            return None
        
        # Check all existing clusters for semantic similarity
        # Use cosine similarity ≥ 0.60 (catches cross-site paraphrases)
        best_match_id = None
        best_similarity = 0.60  # Threshold for considering duplicate (lowered to catch paraphrases)
        
        # Snapshot clusters to avoid "dict changed size" errors (thread-safe read)
        with self.batch_lock:
            clusters_snapshot = dict(self.clusters)
        
        for cluster_id, cluster in clusters_snapshot.items():
            if cluster.canonical_sentence == sentence:
                # Exact match
                return cluster_id
            
            # Hybrid similarity: semantic + lexical fallback for short sentences
            if hasattr(cluster, 'embedding') and cluster.embedding is not None:
                # Semantic similarity
                similarity = np.dot(sentence_embedding, cluster.embedding)
                
                # Lexical fallback for short sentences (boilerplate detection)
                max_len = max(len(sentence), len(cluster.canonical_sentence))
                if max_len <= 120 and similarity < 0.60:
                    lexical_sim = compute_char_3gram_jaccard(sentence, cluster.canonical_sentence)
                    if lexical_sim >= 0.82:
                        # Boost similarity to indicate match via lexical path
                        similarity = max(similarity, 0.82)
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match_id = cluster_id
        
        return best_match_id
    
    def add_sentence_to_corpus(self, sentence: str, prompt_id: str, salience: float, entities: Set[str]) -> str:
        """
        Add sentence to corpus or match to existing cluster.
        
        Args:
            sentence: Sentence text
            prompt_id: Owner prompt
            salience: Importance score
            entities: Extracted entities
        
        Returns:
            cluster_id (new or matched)
        """
        # Compute SimHash
        simhash = compute_simhash(sentence)
        
        # Try to match existing cluster
        existing_cluster_id = self.find_matching_cluster(simhash, sentence)
        
        if existing_cluster_id:
            # Matched existing cluster
            return existing_cluster_id
        
        # Create new cluster
        cluster_id = self._generate_cluster_id()
        cluster = SentenceCluster(
            cluster_id=cluster_id,
            canonical_sentence=sentence,
            owner_prompt_id=prompt_id,
            simhash=simhash,
            salience=salience,
            entities=entities,
            first_seen_seq=self.next_seq,
            length=len(sentence)
        )
        
        self.clusters[cluster_id] = cluster
        self.simhash_index[simhash].append(cluster_id)
        
        # Update entity index
        for entity in entities:
            self.entity_index[entity].add(cluster_id)
        
        self.next_seq += 1
        self.telemetry.clusters_total += 1
        
        return cluster_id
    
    async def enqueue_prompt(self, prompt_id: str, prompt_text: str) -> str:
        """
        Enqueue prompt for batched processing with dynamic barrier (ASYNC - allows parallel arrivals).
        
        Args:
            prompt_id: Unique prompt identifier
            prompt_text: Full prompt text
        
        Returns:
            Deduplicated prompt text (after barrier)
        """
        arrival_time = time.time()
        
        # Split into sentences
        sentences = split_into_sentences(prompt_text)
        
        if not sentences:
            return prompt_text
        
        self.telemetry.prompts_total += 1
        self.telemetry.sentences_total += len(sentences)
        self.telemetry.chars_in += len(prompt_text)
        
        # ⚡ CRITICAL: DO NOT compute embeddings here! It blocks async arrivals.
        # Store raw sentences and compute embeddings in batch during _process_batch
        all_entities = set()
        
        for sentence in sentences:
            # Extract entities (fast, non-blocking)
            entities, numbers = extract_entities_regex(sentence)
            all_entities.update(entities)
            all_entities.update(numbers)
        
        # Create prompt state (thread-safe mutation)
        # NOTE: cluster_ids will be computed during batch processing (after embeddings)
        with self.batch_lock:
            prompt_state = PromptState(
                prompt_id=prompt_id,
                sentences=sentences,
                cluster_ids=[],  # Will be filled during _process_batch
                original_order=list(range(len(sentences))),
                entities=all_entities,
                arrived_at=arrival_time
            )
            
            self.prompt_registry[prompt_id] = prompt_state
        
        # Add to batch queue and manage barrier
        # Create per-prompt ASYNC event for sequential release
        prompt_ready = asyncio.Event()
        loop = asyncio.get_running_loop()
        self.prompt_events[prompt_id] = prompt_ready
        self.prompt_loops[prompt_id] = loop
        
        with self.batch_lock:
            self.batch_queue.append(prompt_id)
            
            if self.batch_timer is None:
                # First prompt in batch, start timer at 5s
                self.batch_start_time = arrival_time
                self.barrier_duration = 5.0
                _vprint(f"[CORPUS] ⏱️  Starting batch barrier: 5.0s (first prompt, min wait)", self.verbose)
                self.batch_timer = threading.Timer(self.barrier_duration, self._process_batch)
                self.batch_timer.start()
            else:
                # Extend barrier by +2s per arrival (capped at 10s)
                elapsed = arrival_time - self.batch_start_time
                new_duration = min(elapsed + self.barrier_increment, self.barrier_cap)
                
                if new_duration > self.barrier_duration:
                    # Cancel old timer, start new one
                    self.batch_timer.cancel()
                    remaining = new_duration - elapsed
                    self.barrier_duration = new_duration
                    _vprint(f"[CORPUS] ⏱️  Extending barrier to {new_duration:.1f}s (+{remaining:.1f}s remaining, +{self.barrier_increment:.1f}s per arrival)", self.verbose)
                    self.batch_timer = threading.Timer(remaining, self._process_batch)
                    self.batch_timer.start()
        
        # ASYNC wait for THIS prompt's individual event (allows other async tasks to proceed)
        # Timeout must be generous to account for model loading on first batch
        try:
            await asyncio.wait_for(prompt_ready.wait(), timeout=30.0)  # 30s max wait (model load + processing)
            timed_out = False
        except asyncio.TimeoutError:
            timed_out = True
        
        if timed_out:
            # Fail open: return original text if batch processing hangs
            _vprint(f"[CORPUS] ⚠️  Timeout waiting for batch processing, returning original prompt", self.verbose)
            self.telemetry.chars_out += len(prompt_text)
            return prompt_text
        
        # Retrieve deduplicated result
        deduplicated_text = self._get_deduplicated_prompt(prompt_id)
        
        if not deduplicated_text:
            # Safety: if result is missing, return original
            _vprint(f"[CORPUS] ⚠️  Missing deduplicated result for prompt {prompt_id[:8]}, returning original", self.verbose)
            self.telemetry.chars_out += len(prompt_text)
            return prompt_text
        
        self.telemetry.chars_out += len(deduplicated_text)
        
        return deduplicated_text
    
    def _process_batch(self):
        """Process current batch: cross-prompt dedupe, entity coverage check, emit (synchronous)."""
        # CRITICAL: Acquire processing lock to prevent multiple batches from processing simultaneously
        with self.processing_lock:
            with self.batch_lock:
                if not self.batch_queue:
                    # No prompts to process, just return (shouldn't happen)
                    return
            
                batch_prompts = self.batch_queue.copy()
                self.batch_queue.clear()
                self.batch_timer = None
            
                batch_duration_ms = (time.time() - self.batch_start_time) * 1000
                self.telemetry.barrier_times.append(batch_duration_ms)
                self.telemetry.batches_processed += 1
            
                # Always show batch summary (key metric)
                _vprint(f"\n[CORPUS] 🔄 Processing batch: {len(batch_prompts)} prompts, barrier={batch_duration_ms:.0f}ms", self.verbose)
        
            # Step 0: Compute embeddings for NEW prompts in this batch (BATCHED operation!)
            # This is done ONCE for the entire batch, allowing parallel arrivals
            _vprint(f"[CORPUS] 🧮 Computing embeddings for {len(batch_prompts)} new prompts...", self.verbose)
            model = _get_embedding_model()
        
            for prompt_id in batch_prompts:
                prompt_state = self.prompt_registry[prompt_id]
            
                if not prompt_state.cluster_ids:  # Only process if not yet clustered
                    # Compute embeddings for all sentences in this prompt (batch operation)
                    sentence_embeddings = model.encode(prompt_state.sentences, show_progress_bar=False, normalize_embeddings=True)
                
                    # Match/create clusters for each sentence
                    cluster_ids = []
                    for i, sentence in enumerate(prompt_state.sentences):
                        # Compute salience
                        salience = len(sentence) / 100.0
                        salience += len(re.findall(r'\b[A-Z][a-z]+', sentence)) * 0.1
                    
                        # Extract entities
                        entities, numbers = extract_entities_regex(sentence)
                    
                        # Match against existing clusters
                        cluster_id = self.find_matching_cluster(0, sentence, sentence_embeddings[i])
                    
                        if cluster_id is None:
                            # Create new cluster
                            with self.batch_lock:
                                cluster_id = self._generate_cluster_id()
                                simhash = compute_simhash(sentence)
                            
                                cluster = SentenceCluster(
                                    cluster_id=cluster_id,
                                    canonical_sentence=sentence,
                                    owner_prompt_id=prompt_id,
                                    simhash=simhash,
                                    salience=salience,
                                    entities=entities | numbers,
                                    first_seen_seq=self.next_seq,
                                    length=len(sentence),
                                    embedding=sentence_embeddings[i]
                                )
                            
                                self.clusters[cluster_id] = cluster
                                self.next_seq += 1
                                self.telemetry.clusters_total += 1
                    
                        cluster_ids.append(cluster_id)
                
                    # Update prompt state with cluster_ids
                    prompt_state.cluster_ids = cluster_ids
        
            _vprint(f"[CORPUS] ✅ Embeddings computed and clusters assigned", self.verbose)
        
            # Step 1: Collect ALL sentences from THE ENTIRE RUN (not just current batch!)
            # This is critical for true run-scoped deduplication
            all_sentences = []
            sentence_to_prompt = {}  # Map sentence_id → (prompt_id, index)
            locked_sentences = set()  # Sentences from previous batches (already emitted, can't remove)
        
            # Iterate over ALL prompts in registry (including previous batches)
            for prompt_id, prompt_state in self.prompt_registry.items():
                is_previous_batch = prompt_id not in batch_prompts
            
                for idx, (sentence_text, cluster_id) in enumerate(zip(prompt_state.sentences, prompt_state.cluster_ids)):
                    cluster = self.clusters.get(cluster_id)
                    if not cluster:
                        continue
                
                    # Create Sentence object for greedy algorithm
                    sent_id = f"{prompt_id}_{idx}"
                    sent_obj = Sentence(
                        id=sent_id,
                        text=sentence_text,
                        embedding=cluster.embedding,
                        entities=cluster.entities,  # Keep ALL entities for accurate coverage tracking
                        numbers=set(),  # Already in entities
                        salience=cluster.salience,
                        position=cluster.first_seen_seq
                    )
                    all_sentences.append(sent_obj)
                    sentence_to_prompt[sent_id] = (prompt_id, idx)
                
                    # Lock sentences from previous batches (already emitted to user)
                    if is_previous_batch:
                        locked_sentences.add(sent_id)
        
            _vprint(f"[CORPUS] 🌐 Run-scoped MIS: {len(all_sentences)} total sentences ({len(locked_sentences)} locked from previous batches, {len(all_sentences)-len(locked_sentences)} new)", self.verbose)
            _vprint(f"[CORPUS] 🧮 Running greedy max-independent-set on {len(all_sentences)} sentences", self.verbose)
        
            # Step 2: Compute degree map (needed for isolates pass later)
            degree_map = {}
            for sent in all_sentences:
                degree = 0
                for other in all_sentences:
                    if sent.id != other.id:
                        if are_sentences_similar(sent, other, semantic_threshold=0.60):
                            degree += 1
                degree_map[sent.id] = degree
        
            # Sanity checks
            isolates_before = [s for s in all_sentences if degree_map[s.id] == 0]
            non_isolates = [s for s in all_sentences if degree_map[s.id] > 0]
            pct_isolates = len(isolates_before) / len(all_sentences) * 100 if all_sentences else 0
            avg_degree_non_iso = sum(degree_map[s.id] for s in non_isolates) / len(non_isolates) if non_isolates else 0
            _vprint(f"[CORPUS] 📊 Graph: isolates={pct_isolates:.1f}% (expect <20%), non-isolate avg degree={avg_degree_non_iso:.1f} (expect >3)", self.verbose)
        
            # Step 3: Run greedy maximum-independent-set selection
            # Start with LOCKED sentences (from previous batches, already emitted)
            # Then run MIS only on NEW sentences (current batch)
            selected_sentences = [s for s in all_sentences if s.id in locked_sentences]
            selected_ids = locked_sentences.copy()
        
            _vprint(f"[CORPUS] 🔒 Pre-seeded MIS with {len(locked_sentences)} locked sentences from previous batches", self.verbose)
        
            # Now run MIS on NEW sentences only (exclude locked)
            new_sentences = [s for s in all_sentences if s.id not in locked_sentences]
        
            if new_sentences:
                # Run MIS on new sentences, considering locked ones as neighbors
                new_selected = greedy_max_independent_set(
                    new_sentences,
                    similarity_threshold=0.60,
                    verbose=False,  # Set to True for debugging
                    precomputed_degree_map=degree_map  # Pass precomputed degrees
                )
            
                # Add newly selected sentences
                selected_sentences.extend(new_selected)
                selected_ids.update(s.id for s in new_selected)
        
            _vprint(f"[CORPUS] ✅ MIS complete: {len(selected_ids)} total kept ({len(locked_sentences)} locked + {len(selected_ids)-len(locked_sentences)} new)", self.verbose)
        
            # Step 3: Compute NODE COVERAGE (align universe for backfill)
            # covered_nodes = S ∪ N(S) (selected + their neighbors)
            covered_nodes = set(selected_ids)
            sentence_map = {s.id: s for s in all_sentences}
        
            for selected_id in selected_ids:
                selected_sent = sentence_map[selected_id]
                # Add all neighbors (similar nodes)
                for other in all_sentences:
                    if other.id != selected_id:
                        if are_sentences_similar(selected_sent, other, semantic_threshold=0.60):
                            covered_nodes.add(other.id)
        
            total_nodes = len(all_sentences)
            node_coverage_before = len(covered_nodes) / total_nodes if total_nodes > 0 else 0.0
        
            _vprint(f"[CORPUS] 📊 After MIS: nodes={len(selected_ids)}/{total_nodes} kept, coverage (S∪N(S))={len(covered_nodes)}/{total_nodes} ({node_coverage_before*100:.1f}%)", self.verbose)
        
            # Step 4: Backfill = GREEDY SET COVER over NODES (no independence constraint!)
            # Goal: Maximize node coverage (S ∪ N(S)) by re-adding removed nodes with highest gain
            # gain(u) = |({u} ∪ N(u)) \ covered_nodes|
            backfill_added = 0
            isolates_added = 0
            target_coverage = 0.90  # 90% node coverage target
        
            if node_coverage_before < target_coverage:
                uncovered_count = total_nodes - len(covered_nodes)
                _vprint(f"[CORPUS] 🔧 Backfill: {uncovered_count} uncovered nodes, targeting {target_coverage*100:.0f}% coverage", self.verbose)
            
                # Get ALL removed sentences (candidates for backfill)
                removed_sentences = [sent for sent in all_sentences if sent.id not in selected_ids]
            
                # Helper: compute node gain for a candidate
                def compute_node_gain(sent):
                    """Compute how many uncovered nodes this sentence + its neighbors would cover."""
                    candidate_coverage = {sent.id}
                    # Add neighbors
                    for other in all_sentences:
                        if other.id != sent.id:
                            if are_sentences_similar(sent, other, semantic_threshold=0.60):
                                candidate_coverage.add(other.id)
                    # Gain = new nodes not already covered
                    return len(candidate_coverage - covered_nodes)
            
                # Debug: Print top-5 candidates by gain (first iteration only)
                if removed_sentences:
                    gains = [(sent, compute_node_gain(sent)) for sent in removed_sentences[:20]]  # Sample first 20 for speed
                    gains.sort(key=lambda x: x[1], reverse=True)
                    _vprint(f"[CORPUS]   Top-5 backfill candidates by gain:", self.verbose)
                    for sent, gain in gains[:5]:
                        _vprint(f"     gain={gain}: '{sent.text[:60]}...'", self.verbose)
            
                # GREEDY SET COVER: repeatedly pick sentence with max gain
                iteration = 0
                while node_coverage_before < target_coverage and removed_sentences and iteration < 100:
                    # Find best candidate
                    best_sent = None
                    best_gain = 0
                
                    for sent in removed_sentences:
                        gain = compute_node_gain(sent)
                        if gain > best_gain:
                            best_gain = gain
                            best_sent = sent
                
                    if best_gain == 0:
                        _vprint(f"[CORPUS]   Backfill: all remaining candidates have gain=0, stopping", self.verbose)
                        break
                
                    # Add best sentence back
                    selected_ids.add(best_sent.id)
                    selected_sentences.append(best_sent)
                
                    # Update covered_nodes: add this node + its neighbors
                    covered_nodes.add(best_sent.id)
                    for other in all_sentences:
                        if other.id != best_sent.id:
                            if are_sentences_similar(best_sent, other, semantic_threshold=0.60):
                                covered_nodes.add(other.id)
                
                    removed_sentences.remove(best_sent)
                    backfill_added += 1
                
                    # Update coverage
                    node_coverage_before = len(covered_nodes) / total_nodes
                    iteration += 1
                
                    if backfill_added <= 5:
                        _vprint(f"[CORPUS]   ✅ Backfill +{best_gain} nodes: '{best_sent.text[:60]}...' (coverage now {node_coverage_before*100:.1f}%)", self.verbose)
            
                _vprint(f"[CORPUS] 📈 After backfill: +{backfill_added} sentences, node coverage {node_coverage_before*100:.1f}%)", self.verbose)
            
                # Step 5: ISOLATES PASS - add uncovered degree=0 nodes
                # These are unique nodes with no similar neighbors
                uncovered_isolates = [sent for sent in all_sentences 
                                      if sent.id not in covered_nodes and degree_map[sent.id] == 0]
            
                if uncovered_isolates:
                    _vprint(f"[CORPUS] 🔧 Isolates pass: {len(uncovered_isolates)} uncovered isolates (degree=0)", self.verbose)
                
                    for sent in uncovered_isolates:
                        if node_coverage_before >= target_coverage:
                            break
                        selected_ids.add(sent.id)
                        covered_nodes.add(sent.id)
                        isolates_added += 1
                        node_coverage_before = len(covered_nodes) / total_nodes
                    
                        if isolates_added <= 5:
                            _vprint(f"[CORPUS]   ✅ Isolate: '{sent.text[:60]}...'", self.verbose)
                
                    if isolates_added > 0:
                        _vprint(f"[CORPUS] 📈 After isolates: +{isolates_added} sentences, node coverage {node_coverage_before*100:.1f}%", self.verbose)
        
            # Final coverage stats (NODE universe)
            final_selected = len(selected_ids)
            final_covered_nodes = len(covered_nodes)
            final_node_coverage = final_covered_nodes / total_nodes if total_nodes > 0 else 0.0
        
            # Assert denominator is |V| (all nodes, no filtering)
            assert total_nodes == len(all_sentences), f"Denominator mismatch: {total_nodes} != {len(all_sentences)}"
        
            _vprint(f"[CORPUS] ✅ Final: kept={final_selected}/{total_nodes}, covered (S∪N(S))={final_covered_nodes}/{total_nodes} ({final_node_coverage*100:.1f}%)", self.verbose)
            _vprint(f"[CORPUS] 📊 Backfill={backfill_added}, Isolates={isolates_added}", self.verbose)
        
            # Step 6: Map results back to prompts
            results = {}
            for prompt_id in batch_prompts:
                prompt_state = self.prompt_registry[prompt_id]
                kept_sentences = []
                removed_count = 0
            
                for idx, sentence_text in enumerate(prompt_state.sentences):
                    sent_id = f"{prompt_id}_{idx}"
                    if sent_id in selected_ids:
                        kept_sentences.append(sentence_text)
                    else:
                        removed_count += 1
            
                results[prompt_id] = {
                    'kept': kept_sentences,
                    'removed': removed_count,
                    'original_count': len(prompt_state.sentences)
                }
        
            # Step 7: Store results and emit to prompts
            for prompt_id in batch_prompts:
                prompt_state = self.prompt_registry[prompt_id]
                result = results[prompt_id]
                prompt_state.sentences = result['kept']
            
                reduction_pct = (result['removed'] / result['original_count'] * 100) if result['original_count'] > 0 else 0
                _vprint(f"[CORPUS]   Prompt {prompt_id[:8]}: {result['original_count']} → {len(result['kept'])} sentences ({reduction_pct:.1f}% removed)", self.verbose)
        
            # Update telemetry
            self.telemetry.entity_coverage_avg = final_node_coverage * 100  # Now tracking NODE coverage
            # Always show final batch summary (key metric)
            _vprint(f"[CORPUS] ✅ Batch complete: Node coverage {final_node_coverage*100:.1f}%", self.verbose)
        
            # Update telemetry
            if self.telemetry.barrier_times:
                self.telemetry.avg_barrier_ms = sum(self.telemetry.barrier_times) / len(self.telemetry.barrier_times)
                self.telemetry.max_barrier_ms = max(self.telemetry.barrier_times)
        
            self.telemetry.tokens_saved = (self.telemetry.chars_in - self.telemetry.chars_out) // 4
        
            # Release prompts SEQUENTIALLY to avoid race condition in on_llm_start
            _vprint(f"[CORPUS] 🚦 Releasing {len(batch_prompts)} prompts sequentially...", self.verbose)
            for i, prompt_id in enumerate(batch_prompts):
                event = self.prompt_events.get(prompt_id)
                if event:
                    # Signal the asyncio.Event from the original loop thread-safely
                    loop = self.prompt_loops.get(prompt_id)
                    if loop:
                        loop.call_soon_threadsafe(event.set)
                    else:
                        event.set()
                    # Longer delay to ensure threads hit on_llm_start one at a time
                    if i < len(batch_prompts) - 1:  # Don't delay after the last one
                        time.sleep(0.5)  # 500ms stagger to be safe
        
            # Clean up events to prevent memory leak
            for prompt_id in batch_prompts:
                self.prompt_events.pop(prompt_id, None)
                self.prompt_loops.pop(prompt_id, None)
    
    def _get_deduplicated_prompt(self, prompt_id: str) -> str:
        """Get deduplicated prompt text."""
        prompt_state = self.prompt_registry.get(prompt_id)
        if not prompt_state:
            return ""
        
        return "\n".join(prompt_state.sentences)
    
    def get_telemetry_summary(self) -> str:
        """Generate human-readable telemetry summary."""
        t = self.telemetry
        reduction_pct = ((t.chars_in - t.chars_out) / t.chars_in * 100) if t.chars_in > 0 else 0
        
        summary = f"""
{'='*70}
[CORPUS] 📊 RUN-SCOPED TELEMETRY (run_id={self.run_id[:8]})
{'='*70}
Prompts processed:           {t.prompts_total}
Sentences total:             {t.sentences_total}
Clusters created:            {t.clusters_total}
Cross-prompt dups removed:   {t.cross_prompt_dups_removed}
{'='*70}
Chars in:                    {t.chars_in:,}
Chars out:                   {t.chars_out:,}
Reduction:                   {reduction_pct:.1f}%
Tokens saved (est):          {t.tokens_saved:,} tokens
{'='*70}
Node Coverage (S∪N(S)):      {t.entity_coverage_avg:.1f}%
Batches processed:           {t.batches_processed}
Avg barrier:                 {t.avg_barrier_ms:.0f}ms
Max barrier:                 {t.max_barrier_ms:.0f}ms
{'='*70}
"""
        return summary


# Global registry of run-scoped corpuses
_run_corpuses: Dict[str, RunScopedCorpus] = {}
_corpus_lock = threading.Lock()


def get_or_create_corpus(run_id: str, verbose: bool = False) -> RunScopedCorpus:
    """Get or create run-scoped corpus (thread-safe)."""
    with _corpus_lock:
        if run_id not in _run_corpuses:
            _run_corpuses[run_id] = RunScopedCorpus(run_id, verbose=verbose)
        return _run_corpuses[run_id]


def cleanup_corpus(run_id: str):
    """Cleanup corpus when run ends."""
    with _corpus_lock:
        if run_id in _run_corpuses:
            corpus = _run_corpuses[run_id]
            _vprint(corpus.get_telemetry_summary(), getattr(corpus, 'verbose', False))
            del _run_corpuses[run_id]
            _vprint(f"[CORPUS] 🗑️  Cleaned up corpus for run_id={run_id[:8]}", getattr(corpus, 'verbose', False))


# ============================================================================
# Legacy Per-Prompt Deduplication (V1.0 - Fallback)
# ============================================================================

@dataclass
class Sentence:
    """Represents a sentence with metadata for deduplication."""
    id: str
    text: str
    embedding: Optional[np.ndarray] = None
    entities: Set[str] = None
    numbers: Set[str] = None
    salience: float = 0.0
    position: int = 0
    
    def __post_init__(self):
        if self.entities is None:
            self.entities = set()
        if self.numbers is None:
            self.numbers = set()
    
    @property
    def protected_entities(self) -> Set[str]:
        """All entities that must be preserved."""
        return self.entities | self.numbers


def estimate_tokens(text: str) -> int:
    """Estimate token count (roughly chars/4 for English)."""
    return len(text) // 4


def adaptive_resize_sentences(sentences: List[str]) -> List[str]:
    """
    Adaptively resize sentences for optimal embedding similarity:
    - Long (>120 tokens): Split on commas, semicolons, conjunctions
    - Short (<40 tokens): Merge with next sentence
    - Mid (40-120 tokens): Keep as-is
    
    This improves cross-page similarity and reduces false uniqueness.
    """
    resized = []
    i = 0
    
    while i < len(sentences):
        sent = sentences[i]
        tokens = estimate_tokens(sent)
        
        if tokens > 120:
            # LONG: Split on commas, semicolons, and conjunctions
            # Split points: , ; : and, but, or, however, therefore (preceded by space/comma)
            split_pattern = r'(?:,\s+(?:and|but|or|however|therefore|while|although)\s+|[;:])\s+'
            chunks = re.split(split_pattern, sent)
            
            # Ensure each chunk is reasonable (not too tiny)
            for chunk in chunks:
                if chunk.strip() and estimate_tokens(chunk) >= 20:
                    resized.append(chunk.strip())
                elif resized:
                    # Merge tiny chunk with previous
                    resized[-1] += " " + chunk.strip()
            i += 1
            
        elif tokens < 40 and i + 1 < len(sentences):
            # SHORT: Merge with next sentence
            next_sent = sentences[i + 1]
            merged = sent + " " + next_sent
            merged_tokens = estimate_tokens(merged)
            
            # Only merge if result is ≤120 tokens (don't create overly long sentences)
            if merged_tokens <= 120:
                resized.append(merged)
                i += 2  # Skip next sentence (already merged)
            else:
                # Next sentence would make it too long, keep short one as-is
                resized.append(sent)
                i += 1
                
        else:
            # MID-RANGE (40-120) or last sentence: Keep as-is
            resized.append(sent)
            i += 1
    
    return resized


def split_into_sentences(text: str) -> List[str]:
    """
    Split text into sentences with special handling for markdown structures,
    then adaptively resize for optimal embedding similarity.
    
    Handles:
    - Standard sentences ending with .!?
    - Bullet points and numbered lists
    - Code blocks (preserve as single units)
    - Headers
    - Adaptive resizing: long sentences split, short ones merged
    """
    sentences = []
    
    # First, protect code blocks
    code_block_pattern = r'```[\s\S]*?```'
    code_blocks = {}
    for i, match in enumerate(re.finditer(code_block_pattern, text)):
        placeholder = f"__CODE_BLOCK_{i}__"
        code_blocks[placeholder] = match.group()
        text = text.replace(match.group(), placeholder)
    
    # Split on sentence boundaries
    # Handle: . ! ? followed by space/newline, or newlines with list markers
    patterns = [
        r'(?<=[.!?])\s+(?=[A-Z])',  # Standard sentences
        r'\n\s*[-*•]\s+',  # Bullet points
        r'\n\s*\d+\.\s+',  # Numbered lists
        r'\n#{1,6}\s+',  # Markdown headers
        r'\n\s*\n',  # Paragraph breaks
    ]
    
    # Use non-capturing groups so delimiters are discarded by re.split
    combined_pattern = '(?:' + '|'.join(patterns) + ')'
    parts = re.split(combined_pattern, text)
    
    # Collect non-empty segments as sentences
    sentences = [p.strip() for p in parts if p and p.strip()]
    
    # Restore code blocks
    restored = []
    for sent in sentences:
        for placeholder, code in code_blocks.items():
            sent = sent.replace(placeholder, code)
        if sent.strip():
            restored.append(sent.strip())
    
    # ADAPTIVE RESIZING: Split long sentences, merge short ones
    resized = adaptive_resize_sentences(restored)
    
    return resized


def extract_entities_regex(text: str) -> Tuple[Set[str], Set[str]]:
    """
    Fallback regex-based entity extraction.
    
    Returns:
        (entities, numbers) - Sets of extracted entities and numbers
    """
    entities = set()
    numbers = set()
    
    # Proper nouns: Capitalized words (basic heuristic) - at least 3 chars
    proper_nouns = re.findall(r'\b[A-Z][a-z]{2,}(?:\s+[A-Z][a-z]+)*\b', text)
    entities.update(proper_nouns)
    
    # Technical terms: CamelCase, snake_case, package names
    technical = re.findall(r'\b[A-Z][a-z]+[A-Z]\w+\b', text)  # CamelCase
    technical += re.findall(r'\b\w+_\w+\b', text)  # snake_case
    entities.update(technical)
    
    # Numbers: MEANINGFUL numbers only (exclude single digits 0-9)
    # Include: multi-digit numbers, floats, percentages, version numbers
    nums = re.findall(r'\b\d{2,}(?:\.\d+)?%?\b', text)  # 2+ digits
    nums += re.findall(r'\b\d+\.\d+\b', text)  # Floats like 14.4, 2.0
    numbers.update(nums)
    
    # Dates: YYYY-MM-DD, MM/DD/YYYY, etc.
    dates = re.findall(r'\b\d{4}[-/]\d{1,2}[-/]\d{1,4}\b', text)  # Full dates
    dates += re.findall(r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b', text)
    numbers.update(dates)
    
    # Filter out common non-informative words and malformed entities
    stopwords = {
        # Common words
        'The', 'This', 'That', 'These', 'Those', 'What', 'Where', 'When', 'Why', 'How', 'Who', 'Which',
        'Welcome', 'Search', 'Summary', 'Source', 'Url', 'Http', 'Https', 'One', 'Two', 'Three', 'Four', 'Five',
        'Key', 'Our', 'Its', 'It', 'For', 'With', 'And', 'But', 'Not', 'You', 'All', 'Can', 'Her', 'Was',
        'She', 'Has', 'Had', 'His', 'Him', 'Are', 'Were', 'Been', 'Being', 'Have', 'Does', 'Did', 'Will',
        # Markup/formatting artifacts
        'URL', 'Http', 'Https', 'PDF', 'CSV', 'JSON', 'XML', 'HTML',
    }
    
    # Filter entities
    filtered_entities = set()
    for e in entities:
        # Skip short entities
        if len(e) < 3:
            continue
        
        # Skip if contains newlines (malformed extraction)
        if '\n' in e:
            continue
        
        # Skip stopwords (case-insensitive)
        if e in stopwords or e.lower() in {s.lower() for s in stopwords}:
            continue
        
        # Skip if it's just a URL fragment
        if e.lower() in ['url', 'http', 'https', 'www']:
            continue
        
        # Skip if ends with common suffixes that indicate malformed extraction
        if e.endswith('---') or e.endswith('...') or e.endswith('--'):
            continue
        
        filtered_entities.add(e)
    
    # Filter numbers - remove single digits 0-9 (often SOURCE numbers)
    filtered_numbers = {n for n in numbers if len(n) >= 2 or '.' in n or '%' in n}
    
    return filtered_entities, filtered_numbers


def extract_entities_spacy(text: str, nlp) -> Tuple[Set[str], Set[str]]:
    """
    spaCy-based entity extraction (more accurate).
    
    Returns:
        (entities, numbers) - Sets of extracted entities and numbers
    """
    entities = set()
    numbers = set()
    
    doc = nlp(text)
    
    # Named entities
    for ent in doc.ents:
        if ent.label_ in ['PERSON', 'ORG', 'GPE', 'PRODUCT', 'EVENT', 'WORK_OF_ART', 'LAW']:
            entities.add(ent.text)
        elif ent.label_ in ['DATE', 'TIME', 'PERCENT', 'MONEY', 'QUANTITY', 'ORDINAL', 'CARDINAL']:
            numbers.add(ent.text)
    
    # Also grab technical terms (capitalized noun phrases)
    for chunk in doc.noun_chunks:
        if chunk.text[0].isupper():
            entities.add(chunk.text)
    
    # Apply SAME filtering as regex version
    stopwords = {
        'The', 'This', 'That', 'These', 'Those', 'What', 'Where', 'When', 'Why', 'How', 'Who', 'Which',
        'Welcome', 'Search', 'Summary', 'Source', 'Url', 'Http', 'Https', 'One', 'Two', 'Three', 'Four', 'Five',
        'Key', 'Our', 'Its', 'It', 'For', 'With', 'And', 'But', 'Not', 'You', 'All', 'Can', 'Her', 'Was',
        'She', 'Has', 'Had', 'His', 'Him', 'Are', 'Were', 'Been', 'Being', 'Have', 'Does', 'Did', 'Will',
        'URL', 'Http', 'Https', 'PDF', 'CSV', 'JSON', 'XML', 'HTML',
    }
    
    # Filter entities
    filtered_entities = set()
    for e in entities:
        # Skip short entities
        if len(e) < 3:
            continue
        
        # Skip if contains newlines (malformed)
        if '\n' in e:
            continue
        
        # Skip stopwords (case-insensitive)
        if e in stopwords or e.lower() in {s.lower() for s in stopwords}:
            continue
        
        # Skip URL fragments
        if e.lower() in ['url', 'http', 'https', 'www']:
            continue
        
        # Skip malformed endings
        if e.endswith('---') or e.endswith('...') or e.endswith('--') or e.endswith('---\\nURL'):
            continue
        
        filtered_entities.add(e)
    
    # Filter numbers - remove single digits 0-9
    filtered_numbers = {n for n in numbers if len(str(n).strip()) >= 2 or '.' in str(n) or '%' in str(n)}
    
    return filtered_entities, filtered_numbers


def extract_entities(text: str) -> Tuple[Set[str], Set[str]]:
    """
    Extract entities and numbers from text.
    
    Uses spaCy if available, falls back to regex.
    
    Returns:
        (entities, numbers) - Sets of protected entities and numbers
    """
    nlp = _get_spacy_model()
    
    if nlp == "fallback":
        return extract_entities_regex(text)
    else:
        return extract_entities_spacy(text, nlp)


def compute_salience(sentence: str, position: int, total_sentences: int) -> float:
    """
    Compute salience score for a sentence.
    
    Factors:
    - Position: Earlier sentences weighted higher (first paragraph effect)
    - Length: Moderate length preferred (too short = filler, too long = verbose)
    - Entity density: More entities = more information-dense
    - Numbers: Presence of numbers = factual content
    
    Returns:
        Salience score (0.0 to 1.0, higher = more important)
    """
    score = 0.0
    
    # Position-based (exponential decay)
    position_weight = np.exp(-position / (total_sentences * 0.3))
    score += position_weight * 0.3
    
    # Length-based (optimal ~50-150 chars)
    length = len(sentence)
    if 50 <= length <= 150:
        length_weight = 1.0
    elif length < 50:
        length_weight = length / 50
    else:
        length_weight = 150 / length
    score += length_weight * 0.2
    
    # Entity density (basic heuristic: count capitalized words)
    words = sentence.split()
    cap_words = sum(1 for w in words if w and w[0].isupper())
    entity_density = min(cap_words / max(len(words), 1), 1.0)
    score += entity_density * 0.3
    
    # Number presence
    has_numbers = bool(re.search(r'\d', sentence))
    score += 0.2 if has_numbers else 0.0
    
    return min(score, 1.0)


def compute_char_3gram_jaccard(text1: str, text2: str) -> float:
    """
    Compute character 3-gram Jaccard similarity.
    Captures boilerplate and tight phrasing that embeddings might miss.
    
    Returns:
        Jaccard similarity [0, 1]
    """
    def get_3grams(text):
        text = text.lower()
        return set(text[i:i+3] for i in range(len(text) - 2))
    
    grams1 = get_3grams(text1)
    grams2 = get_3grams(text2)
    
    if not grams1 or not grams2:
        return 0.0
    
    intersection = len(grams1 & grams2)
    union = len(grams1 | grams2)
    
    return intersection / union if union > 0 else 0.0


def compute_similarity(emb1: np.ndarray, emb2: np.ndarray) -> float:
    """
    Compute cosine similarity between two embeddings.
    Assumes embeddings are L2-normalized (unit vectors), so cosine = dot product.
    """
    return np.dot(emb1, emb2)


def are_sentences_similar(sent1: Sentence, sent2: Sentence, semantic_threshold: float = 0.60) -> bool:
    """
    Check if two sentences are similar using semantic + lexical signals.
    
    - Semantic: cosine similarity on embeddings
    - Lexical fallback: 3-gram Jaccard for short sentences (≤120 chars)
    
    Args:
        sent1, sent2: Sentence objects with embeddings
        semantic_threshold: Threshold for semantic similarity
    
    Returns:
        True if similar, False otherwise
    """
    # Primary: semantic similarity
    semantic_sim = compute_similarity(sent1.embedding, sent2.embedding)
    if semantic_sim >= semantic_threshold:
        return True
    
    # Fallback: lexical for short sentences (captures boilerplate)
    max_len = max(len(sent1.text), len(sent2.text))
    if max_len <= 120:  # ~30 tokens
        lexical_sim = compute_char_3gram_jaccard(sent1.text, sent2.text)
        if lexical_sim >= 0.82:  # High Jaccard = tight phrasing match
            return True
    
    return False


def build_sentence_objects(sentences_text: List[str], embeddings: np.ndarray) -> List[Sentence]:
    """
    Build Sentence objects with metadata.
    
    Args:
        sentences_text: List of sentence strings
        embeddings: Numpy array of embeddings (N x 384)
    
    Returns:
        List of Sentence objects with computed metadata
    """
    sentence_objects = []
    total = len(sentences_text)
    
    for i, text in enumerate(sentences_text):
        # Generate ID
        sent_id = hashlib.md5(text.encode()).hexdigest()[:8]
        
        # Extract entities
        entities, numbers = extract_entities(text)
        
        # Compute salience
        salience = compute_salience(text, i, total)
        
        sentence_objects.append(Sentence(
            id=sent_id,
            text=text,
            embedding=embeddings[i],
            entities=entities,
            numbers=numbers,
            salience=salience,
            position=i
        ))
    
    return sentence_objects


def greedy_max_independent_set(
    sentences: List[Sentence],
    similarity_threshold: float = 0.60,
    verbose: bool = True,
    precomputed_degree_map: Dict = None
) -> List[Sentence]:
    """
    Greedy maximum-independent-set selection with degree×length-aware ordering.
    
    Algorithm:
    1. Compute degree (# of similar neighbors) for each sentence
    2. Sort by (token_length × degree) DESCENDING → prioritizes ejecting long redundant sentences
    3. Pick highest degree×length sentence (most redundant, highest token savings)
    4. Remove all similar neighbors (similarity > threshold)
    5. Check removed sentences for unique entities
    6. If removed sentence has unique entities, re-add it (HARD GUARD)
    7. Repeat until all sentences processed
    
    This preserves coverage while ejecting long, low-value uniques → bigger trims without raising sim bar.
    
    Args:
        sentences: List of Sentence objects
        similarity_threshold: Similarity threshold for edge creation (0.75 = 75% similar)
        verbose: Print debug info
    
    Returns:
        List of selected Sentence objects (deduplicated)
    """
    if verbose:
        print(f"\n[PIPECLEANER] Starting degree×length-aware greedy max-independent-set")
        print(f"[PIPECLEANER] Input: {len(sentences)} sentences")
        print(f"[PIPECLEANER] Similarity threshold: {similarity_threshold}")
    
    # Step 1: Use precomputed degree map (or compute if not provided)
    if precomputed_degree_map is None:
        # Compute degree (# of connections) for each sentence
        # Use hybrid similarity: semantic (0.60) OR lexical (0.82 Jaccard for short spans)
        degree_map = {}
        for sent in sentences:
            degree = 0
            for other in sentences:
                if sent.id != other.id:
                    # Hybrid check: semantic OR lexical
                    if are_sentences_similar(sent, other, semantic_threshold=similarity_threshold):
                        degree += 1
            degree_map[sent.id] = degree
        
        # Sanity checks (as requested)
        isolates = [s for s in sentences if degree_map[s.id] == 0]
        non_isolates = [s for s in sentences if degree_map[s.id] > 0]
        pct_isolates = len(isolates) / len(sentences) * 100 if sentences else 0
        avg_degree_non_iso = sum(degree_map[s.id] for s in non_isolates) / len(non_isolates) if non_isolates else 0
        
        if verbose:
            avg_degree = sum(degree_map.values()) / len(degree_map) if degree_map else 0
            print(f"[PIPECLEANER] Degree stats: avg={avg_degree:.1f}, isolates={pct_isolates:.1f}%, non-isolate avg={avg_degree_non_iso:.1f}")
            print(f"[PIPECLEANER] Sanity: isolates {pct_isolates:.0f}% (expect <20%), non-isolate avg {avg_degree_non_iso:.1f} (expect >3)")
    else:
        # Use precomputed degree map (more efficient)
        degree_map = precomputed_degree_map
    
    # Step 2: Sort by (token_length × degree) ASCENDING
    # LOW degree×length = short + unique → keep first (high value)
    # HIGH degree×length = long + redundant → eject (low value)
    def sort_key(s):
        token_len = estimate_tokens(s.text)
        degree = degree_map[s.id]
        return token_len * degree
    
    # Sort ASCENDING - pick short unique sentences first
    sorted_sentences = sorted(sentences, key=sort_key, reverse=False)
    
    if verbose:
        top_5 = sorted_sentences[:5]
        print(f"[PIPECLEANER] Top 5 to keep (low degree×length = short + unique):")
        for i, s in enumerate(top_5, 1):
            score = sort_key(s)
            print(f"  {i}. {estimate_tokens(s.text)}tok × {degree_map[s.id]}deg = {score:.0f} | '{s.text[:60]}...'")

    
    selected = []
    remaining = sorted_sentences.copy()
    entity_coverage = set()
    iteration = 0
    
    while remaining:
        iteration += 1
        # Pick highest degree×length sentence (most redundant + expensive)
        best = remaining[0]
        
        if verbose and iteration <= 5:  # Print first 5 iterations
            score = sort_key(best)
            print(f"\n[PIPECLEANER] Iteration {iteration}:")
            print(f"  Selected: '{best.text[:80]}...'")
            print(f"  Degree×Length: {estimate_tokens(best.text)}tok × {degree_map[best.id]}deg = {score:.0f}")
            print(f"  Entities: {best.protected_entities}")
        
        # Add to selected
        selected.append(best)
        entity_coverage |= best.protected_entities
        
        # Remove from remaining
        remaining.remove(best)
        
        # Find similar neighbors to remove (using hybrid similarity)
        to_remove = []
        for candidate in remaining:
            if are_sentences_similar(best, candidate, semantic_threshold=similarity_threshold):
                # Get semantic sim for logging
                sem_sim = compute_similarity(best.embedding, candidate.embedding)
                to_remove.append((candidate, sem_sim))
        
        if verbose and iteration <= 5 and to_remove:
            print(f"  Removing {len(to_remove)} similar sentences (similarity >= {similarity_threshold})")
        
        # Remove similar sentences
        for candidate, sim in to_remove:
            remaining.remove(candidate)
        
        # HARD GUARD: Check removed sentences for unique entities
        # Only re-add if they have MULTIPLE (3+) meaningful unique entities
        # This prevents re-adding for trivial differences
        re_added = 0
        for candidate, sim in to_remove:
            unique_entities = candidate.protected_entities - entity_coverage
            
            # Require at least 3 unique entities OR at least 1 unique multi-word entity
            multi_word_entities = {e for e in unique_entities if ' ' in e or len(e) > 10}
            should_readd = len(unique_entities) >= 3 or len(multi_word_entities) >= 1
            
            if should_readd:
                if verbose and iteration <= 5:
                    print(f"  ⚠️  RE-ADDING sentence with {len(unique_entities)} unique entities: {unique_entities}")
                    print(f"     Text: '{candidate.text[:80]}...'")
                selected.append(candidate)
                entity_coverage |= candidate.protected_entities
                re_added += 1
        
        if verbose and iteration <= 5 and re_added:
            print(f"  Re-added {re_added} sentences to preserve entity coverage")
    
    if verbose:
        print(f"\n[PIPECLEANER] Selection complete:")
        print(f"  Input: {len(sentences)} sentences")
        print(f"  Output: {len(selected)} sentences")
        print(f"  Reduction: {(1 - len(selected)/len(sentences))*100:.1f}%")
        print(f"  Entities preserved: {len(entity_coverage)}")
    
    return selected


def deduplicate_search_results(
    text: str,
    similarity_threshold: float = 0.60,
    verbose: bool = True,
    cached_model=None
) -> Tuple[str, Dict, any]:
    """
    Main entry point: Deduplicate search results using graph-based approach.
    
    Args:
        text: Raw search results text
        similarity_threshold: Cosine similarity threshold (0.60 catches cross-site paraphrases at 0.55-0.68)
        verbose: Print debug info
        cached_model: Optional cached embedding model to reuse
    
    Returns:
        Tuple of (deduplicated_text, stats_dict, embedding_model)
        stats_dict contains: {
            'original_chars': int,
            'deduplicated_chars': int,
            'original_sentences': int,
            'deduplicated_sentences': int,
            'prune_pct': float,
            'original_tokens': int,
            'deduplicated_tokens': int,
            'tokens_saved': int,
            'entity_coverage_pct': float,
            'entities_total': int,
            'entities_preserved': int
        }
    """
    if verbose:
        print(f"\n{'='*70}")
        print(f"[PIPECLEANER] DEDUPLICATION STARTED")
        print(f"{'='*70}")
        print(f"[PIPECLEANER] Input text: {len(text)} chars, ~{len(text.split())} words")
    
    # Step 1: Split into sentences
    sentences_text = split_into_sentences(text)
    
    if verbose:
        print(f"[PIPECLEANER] Split into {len(sentences_text)} sentences")
    
    # Initialize stats
    stats = {
        'original_chars': len(text),
        'deduplicated_chars': len(text),
        'original_sentences': len(sentences_text),
        'deduplicated_sentences': len(sentences_text),
        'prune_pct': 0.0,
        'original_tokens': int(len(text) / 4),
        'deduplicated_tokens': int(len(text) / 4),
        'tokens_saved': 0,
        'entity_coverage_pct': 100.0,
        'entities_total': 0,
        'entities_preserved': 0
    }
    
    if len(sentences_text) == 0:
        if verbose:
            print(f"[PIPECLEANER] ⚠️  No sentences found, returning original text")
        return text, stats, cached_model
    
    if len(sentences_text) == 1:
        if verbose:
            print(f"[PIPECLEANER] Only 1 sentence, skipping deduplication")
        return text, stats, cached_model
    
    # Step 2: Compute embeddings
    # Always use the thread-safe singleton model
    model = _get_embedding_model()
    
    if verbose:
        print(f"[PIPECLEANER] Computing embeddings...")
    
    # L2 normalize embeddings so cosine similarity = dot product (faster)
    embeddings = model.encode(sentences_text, show_progress_bar=False, normalize_embeddings=True)
    
    if verbose:
        print(f"[PIPECLEANER] Embeddings computed: shape {embeddings.shape}")
    
    # Step 3: Build sentence objects with metadata
    sentences = build_sentence_objects(sentences_text, embeddings)
    
    # Calculate total entities across all sentences
    all_entities = set()
    for sent in sentences:
        all_entities |= sent.protected_entities
    
    # Step 4: Run greedy max-independent-set selection
    selected = greedy_max_independent_set(sentences, similarity_threshold, verbose)
    
    # Calculate preserved entities
    preserved_entities = set()
    for sent in selected:
        preserved_entities |= sent.protected_entities
    
    # Step 5: Reconstruct text preserving original order
    selected_by_position = sorted(selected, key=lambda s: s.position)
    deduplicated_text = '\n\n'.join(s.text for s in selected_by_position)
    
    # Calculate stats
    stats['deduplicated_chars'] = len(deduplicated_text)
    stats['deduplicated_sentences'] = len(selected)
    stats['prune_pct'] = (1 - len(selected) / len(sentences_text)) * 100 if len(sentences_text) > 0 else 0
    stats['deduplicated_tokens'] = int(len(deduplicated_text) / 4)
    stats['tokens_saved'] = stats['original_tokens'] - stats['deduplicated_tokens']
    stats['entities_total'] = len(all_entities)
    stats['entities_preserved'] = len(preserved_entities)
    stats['entity_coverage_pct'] = (len(preserved_entities) / len(all_entities) * 100) if len(all_entities) > 0 else 100.0
    
    if verbose:
        print(f"\n[PIPECLEANER] DEDUPLICATION COMPLETE")
        print(f"  Input: {len(text)} chars")
        print(f"  Output: {len(deduplicated_text)} chars")
        print(f"  Reduction: {(1 - len(deduplicated_text)/len(text))*100:.1f}%")
        print(f"  Sentences: {len(sentences_text)} → {len(selected)}")
        print(f"{'='*70}\n")
    
    return deduplicated_text, stats, model


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def estimate_tokens(text: str) -> int:
    """Rough estimate of token count (words / 0.75)."""
    return int(len(text.split()) / 0.75)


def should_deduplicate(text: str, min_length: int = 500) -> bool:
    """
    Check if text is worth deduplicating.
    
    Args:
        text: Input text
        min_length: Minimum character length to bother deduplicating
    
    Returns:
        True if text should be deduplicated
    """
    return len(text) >= min_length


def apply_pipecleaner_if_applicable(tool_name: str, output_str: str, selected_rules: list, cached_model=None) -> Tuple[str, any]:
    """
    High-level function to check for filter search rules and apply deduplication.
    
    This is called from capture.py's on_tool_end callback.
    
    Args:
        tool_name: Name of the tool that just finished
        output_str: Raw output from the tool
        selected_rules: List of rules selected for this run
        cached_model: Optional cached embedding model to reuse across searches
    
    Returns:
        Tuple of (deduplicated_output, embedding_model) for caching
        Returns (original_output, None) if no filter rule applies
    """
    try:
        # Find applicable filter search rules for this tool
        filter_rules = _find_filter_search_rules(tool_name, selected_rules)
        
        # If we found applicable filter rules, apply deduplication
        if filter_rules:
            print(f"\n{'='*70}")
            print(f"[PIPECLEANER] 🧹 FILTER SEARCH RULE DETECTED")
            print(f"{'='*70}")
            print(f"[PIPECLEANER] Tool: {tool_name}")
            print(f"[PIPECLEANER] Rules matched: {len(filter_rules)}")
            for rule in filter_rules:
                rule_id = getattr(rule, 'id', 'unknown')
                advice = getattr(rule, 'advice', '') or getattr(rule, 'advice_text', '')
                print(f"[PIPECLEANER]   - Rule {rule_id}: {advice[:80]}...")
            print(f"{'='*70}")
            
            # Apply deduplication with cached model
            deduplicated, stats, model = deduplicate_search_results(
                text=output_str,
                similarity_threshold=0.60,  # 0.60 catches cross-site paraphrases (0.55-0.68 typical)
                verbose=True,  # Show detailed deduplication stats
                cached_model=cached_model  # Reuse model if available
            )
            
            # Print comprehensive stats after every search
            print(f"\n{'='*70}")
            print(f"[PIPECLEANER] 📊 DEDUPLICATION RESULTS")
            print(f"{'='*70}")
            print(f"[PIPECLEANER] 🔢 Sentences:")
            print(f"[PIPECLEANER]   Original:       {stats['original_sentences']} sentences")
            print(f"[PIPECLEANER]   Deduplicated:   {stats['deduplicated_sentences']} sentences")
            print(f"[PIPECLEANER]   Prune %:        {stats['prune_pct']:.1f}% removed")
            print(f"[PIPECLEANER]")
            print(f"[PIPECLEANER] 🎯 Entity Coverage:")
            print(f"[PIPECLEANER]   Total entities:     {stats['entities_total']}")
            print(f"[PIPECLEANER]   Entities preserved: {stats['entities_preserved']}")
            print(f"[PIPECLEANER]   Coverage:           {stats['entity_coverage_pct']:.1f}%")
            print(f"[PIPECLEANER]")
            print(f"[PIPECLEANER] 💰 Token Savings (len/4):")
            print(f"[PIPECLEANER]   Original tokens:    {stats['original_tokens']:,} tokens")
            print(f"[PIPECLEANER]   Deduplicated:       {stats['deduplicated_tokens']:,} tokens")
            print(f"[PIPECLEANER]   Tokens saved:       {stats['tokens_saved']:,} tokens ({(stats['tokens_saved']/stats['original_tokens']*100 if stats['original_tokens'] > 0 else 0):.1f}%)")
            print(f"[PIPECLEANER]")
            print(f"[PIPECLEANER] ✅ SUCCESS: Pruned {stats['prune_pct']:.1f}% redundancy, preserved {stats['entity_coverage_pct']:.1f}% entities")
            print(f"{'='*70}\n")
            
            return deduplicated, model
        
        # No filter rules found, return original
        return output_str, None
        
    except ImportError as e:
        print(f"\n{'='*70}")
        print(f"[PIPECLEANER] ❌ IMPORT ERROR - FAILING OPEN")
        print(f"{'='*70}")
        print(f"[PIPECLEANER] Error: {e}")
        print(f"[PIPECLEANER] Install: pip install sentence-transformers")
        print(f"{'='*70}\n")
        return output_str, None
    except Exception as e:
        print(f"\n{'='*70}")
        print(f"[PIPECLEANER] ❌ EXCEPTION - FAILING OPEN")
        print(f"{'='*70}")
        print(f"[PIPECLEANER] Error type: {type(e).__name__}")
        print(f"[PIPECLEANER] Error message: {e}")
        import traceback
        print(f"[PIPECLEANER] Traceback:")
        traceback.print_exc()
        print(f"{'='*70}\n")
        return output_str, None


def _find_filter_search_rules(tool_name: str, selected_rules: list) -> list:
    """
    Find llm_start scoped rules with "filter search" keywords that apply to this tool.
    
    This is called from on_llm_start when a Summary tool's LLM is about to be called.
    Rule synthesis will generate rules scoped to llm_start when it detects search→summary patterns.
    
    Args:
        tool_name: Name of the tool whose LLM is starting (e.g., 'Summary')
        selected_rules: List of rules to search through
    
    Returns:
        List of applicable filter search rules
    """
    filter_rules = []
    
    for rule_meta in selected_rules:
        # Unwrap tuple if needed (rules come as (rule, metadata) from select_rules)
        if isinstance(rule_meta, tuple) and len(rule_meta) == 2:
            rule_obj, _metadata = rule_meta
        else:
            rule_obj = rule_meta
        
        # Check if this is an llm_start scoped rule
        target_step_type = getattr(rule_obj, 'target_step_type', None)
        
        # Must be scoped to llm_start (where we intercept Summary LLM calls)
        if target_step_type != 'llm_start':
            continue
        
        # Check if the rule contains "filter search" keywords
        # Try both field names that might be used
        advice = getattr(rule_obj, 'advice_text', None) or getattr(rule_obj, 'advice', None) or ''
        advice_lower = advice.lower() if advice else ''
        
        if not advice_lower or 'filter' not in advice_lower or 'search' not in advice_lower:
            continue
        
        # Check if the rule applies to this tool
        applies = _rule_applies_to_tool(rule_obj, tool_name, advice_lower)
        
        if applies:
            filter_rules.append(rule_obj)
    
    return filter_rules


def _rule_applies_to_tool(rule_obj, tool_name: str, advice_lower: str) -> bool:
    """
    Check if a rule applies to the given tool.
    
    Args:
        rule_obj: Rule object or dict to check
        tool_name: Name of the tool (case-insensitive)
        advice_lower: Lowercased advice text for fallback matching
    
    Returns:
        True if rule applies to this tool
    """
    # Wildcard matches everything (used for initial check)
    if tool_name == "*":
        return True
    
    tool_name_lower = tool_name.lower()
    
    # Extract references.tools from rule (handle both dict and object formats)
    if isinstance(rule_obj, dict):
        references = rule_obj.get('references', {})
        tools = references.get('tools', []) if isinstance(references, dict) else []
    else:
        references = getattr(rule_obj, 'references', None)
        if references:
            # Try both object attribute and dict access for tools
            if hasattr(references, 'tools'):
                tools = references.tools
            elif isinstance(references, dict):
                tools = references.get('tools', [])
            else:
                tools = []
        else:
            tools = []
    
    if tools:
        # Check if tool_name matches any tool in references.tools (case-insensitive exact match)
        for ref_tool in tools:
            ref_tool_lower = ref_tool.lower()
            if tool_name_lower == ref_tool_lower:
                return True
        # No match found in references.tools
        return False
    else:
        # Rule has no tools list - don't apply to anything (be conservative)
        return False


async def run_pipecleaner_enforcement(
    messages_or_prompts: tuple,
    callback_handler: any,
    patch_depth: any
) -> bool:
    """
    Main pipecleaner enforcement logic - parallel to run_microturn_enforcement.
    
    This intercepts ToolMessage objects and applies deduplication.
    
    Args:
        messages_or_prompts: Args tuple from _generate (first element is messages)
        callback_handler: DaseinCallbackHandler with rules
        patch_depth: Thread-local object with caching
        
    Returns:
        True if enforcement was applied, False if skipped
    """
    try:
        print(f"[PIPECLEANER] 🧹 run_pipecleaner_enforcement called")
        
        if not callback_handler or not hasattr(callback_handler, '_selected_rules'):
            return False
        
        rules = callback_handler._selected_rules
        print(f"[PIPECLEANER] Found {len(rules)} rules")
        
        filter_rules = _find_filter_search_rules("*", rules)
        if not filter_rules:
            return False
        
        print(f"[PIPECLEANER] 🎯 Found {len(filter_rules)} filter search rules!")
        
        # Extract messages from args
        if not messages_or_prompts or len(messages_or_prompts) == 0:
            return False
        
        messages = messages_or_prompts[0]
        if not isinstance(messages, list):
            return False
        
        # Find the most recent ToolMessage (tool result)
        tool_message = None
        for idx in range(len(messages) - 1, -1, -1):
            msg = messages[idx]
            msg_type = getattr(msg, 'type', None) or (msg.get('type') if isinstance(msg, dict) else None)
            if msg_type == 'tool':
                tool_message = msg
                break
        
        if not tool_message:
            return False
        
        # Extract tool name and content
        tool_name = getattr(tool_message, 'name', None) or tool_message.get('name', 'unknown')
        tool_content = str(getattr(tool_message, 'content', None) or tool_message.get('content', ''))
        
        print(f"[PIPECLEANER] Tool: {tool_name}, content: {len(tool_content)} chars")
        
        # Check if this tool matches our filter rules
        matching_rules = _find_filter_search_rules(tool_name, rules)
        if not matching_rules:
            print(f"[PIPECLEANER] Tool '{tool_name}' doesn't match filter rules, skipping")
            return False
        
        print(f"[PIPECLEANER] 🎯 Tool '{tool_name}' matches filter rules! Starting deduplication...")
        
        # Prevent infinite regression - check if we've already processed this exact message
        if not hasattr(patch_depth, 'processed_tool_messages'):
            patch_depth.processed_tool_messages = set()
        
        # Create signature from tool name + content hash
        msg_signature = f"{tool_name}_{hash(tool_content[:200])}"
        if msg_signature in patch_depth.processed_tool_messages:
            print(f"[PIPECLEANER] Already processed this ToolMessage, skipping")
            return False
        
        # Mark as processed
        patch_depth.processed_tool_messages.add(msg_signature)
        
        # Apply deduplication
        cached_model = getattr(callback_handler, '_pipecleaner_embedding_model', None)
        
        deduplicated, stats, model = deduplicate_search_results(
            text=tool_content,
            similarity_threshold=0.60,  # Lowered to catch paraphrases
            verbose=True,
            cached_model=cached_model
        )
        
        # Cache model
        callback_handler._pipecleaner_embedding_model = model
        
        # Modify ToolMessage content IN PLACE
        if hasattr(tool_message, 'content'):
            tool_message.content = deduplicated
        elif isinstance(tool_message, dict):
            tool_message['content'] = deduplicated
        
        # Cache result for potential reuse
        if not hasattr(patch_depth, 'tool_result_cache'):
            patch_depth.tool_result_cache = {}
        
        result_key = f"{tool_name}_{hash(tool_content[:100])}"
        patch_depth.tool_result_cache[result_key] = deduplicated
        
        print(f"[PIPECLEANER] ✅ Applied deduplication to {tool_name}")
        
        # Print stats
        print(f"\n{'='*70}")
        print(f"[PIPECLEANER] 📊 DEDUPLICATION RESULTS")
        print(f"{'='*70}")
        print(f"[PIPECLEANER] 🔢 Sentences:")
        print(f"[PIPECLEANER]   Original:       {stats['original_sentences']} sentences")
        print(f"[PIPECLEANER]   Deduplicated:   {stats['deduplicated_sentences']} sentences")
        print(f"[PIPECLEANER]   Prune %:        {stats['prune_pct']:.1f}% removed")
        print(f"[PIPECLEANER]")
        print(f"[PIPECLEANER] 🎯 Entity Coverage:")
        print(f"[PIPECLEANER]   Total entities:     {stats['entities_total']}")
        print(f"[PIPECLEANER]   Entities preserved: {stats['entities_preserved']}")
        print(f"[PIPECLEANER]   Coverage:           {stats['entity_coverage_pct']:.1f}%")
        print(f"[PIPECLEANER]")
        print(f"[PIPECLEANER] 💰 Token Savings (len/4):")
        print(f"[PIPECLEANER]   Original tokens:    {stats['original_tokens']:,} tokens")
        print(f"[PIPECLEANER]   Deduplicated:       {stats['deduplicated_tokens']:,} tokens")
        print(f"[PIPECLEANER]   Tokens saved:       {stats['tokens_saved']:,} tokens ({(stats['tokens_saved']/stats['original_tokens']*100 if stats['original_tokens'] > 0 else 0):.1f}%)")
        print(f"[PIPECLEANER]")
        print(f"[PIPECLEANER] ✅ SUCCESS: Pruned {stats['prune_pct']:.1f}% redundancy, preserved {stats['entity_coverage_pct']:.1f}% entities")
        print(f"{'='*70}\n")
        
        return True
        
    except Exception as e:
        print(f"[PIPECLEANER] ⚠️ Error during enforcement: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Simple test
    test_text = """
    LangChain is a framework for developing applications powered by language models.
    The LangChain framework enables developers to build LLM applications easily.
    LangChain provides many useful features for LLM apps.
    It supports multiple model providers including OpenAI and Anthropic.
    The framework was created in 2022 by Harrison Chase.
    LlamaIndex is another popular framework for LLM applications.
    LlamaIndex focuses on data indexing and retrieval.
    Both frameworks are open source and widely used.
    """
    
    print("Testing pipecleaner deduplication...")
    result, stats, model = deduplicate_search_results(test_text, verbose=True)
    
    print("\n" + "="*70)
    print("STATS:")
    print(f"  Prune %: {stats['prune_pct']:.1f}%")
    print(f"  Entity Coverage: {stats['entity_coverage_pct']:.1f}%")
    print(f"  Tokens saved: {stats['tokens_saved']:,} ({(stats['tokens_saved']/stats['original_tokens']*100 if stats['original_tokens'] > 0 else 0):.1f}%)")
    
    print("\n" + "="*70)
    print("ORIGINAL:")
    print(test_text)
    print("\n" + "="*70)
    print("DEDUPLICATED:")
    print(result)

