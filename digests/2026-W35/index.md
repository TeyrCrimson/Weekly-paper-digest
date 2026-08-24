# Weekly paper digest

| Title | Score | Topics | One-liner |
|---|---|---|---|
| [FlashPrefill V2: Block-Sparse Prefill Attention for Long-Context LLM Serving](2608.19758-flashprefill-v2-block-sparse-prefill-att.md) | 10 | LLM inference efficiency and long-context serving | Evolves FlashPrefill to production-ready block-sparse prefill attention with FP8 support and 47x speedups at 128K context. |
| [ReCache: Efficient KV Cache Reuse and Compression for Tool-Augmented LLM Agents](2608.19662-recache-efficient-kv-cache-reuse-and-com.md) | 10 | LLM inference efficiency and long-context serving | ReCache independently caches tool schemas with resource-wise attention and semantic pruning, reducing KV-tensor memory by 92.43%. |
| [Pallas: A Proactive KV Cache Migration Framework for LLM Inference in AI-RAN](2608.16477-pallas-a-proactive-kv-cache-migration-fr.md) | 10 | LLM inference efficiency and long-context serving | Proactive KV-cache migration framework for LLM serving during cellular handover to reduce service interruption. |
| [TreeWY: Speculative Verification for Gated DeltaNet Hybrids](2608.20961-treewy-speculative-verification-for-gate.md) | 9 | LLM inference efficiency and long-context serving | Proposes TreeWY for efficient speculative decoding in gated DeltaNet hybrid models. |
| [CacheRoute: Planned Prefix-Affinity Routing for Large-Scale LLM Serving](2608.19677-cacheroute-planned-prefix-affinity-routi.md) | 9 | LLM inference efficiency and long-context serving | CacheRoute resolves prefix-cache reuse tradeoffs via periodic routing plans, achieving 2.3x throughput on Llama-3.3-70B. |
| [BF1: A Causal Dyadic Sparse-Attention Retrofit for Efficient Long-Context Transformers](2608.20427-bf1-a-causal-dyadic-sparse-attention-ret.md) | 9 | LLM inference efficiency and long-context serving | BF1 block-aligned dyadic sparse attention achieves 10.91x prefill speedup at 32K tokens on RTX PRO Blackwell with retrofitted models. |
| [Off-Manifold Collapse in Guided Protein Language Models](2608.18597-off-manifold-collapse-in-guided-protein.md) | 9 | Post-inference detection and repair of degenerate output | Detects off-manifold collapse in guided protein generation and proposes post-hoc Mahalanobis filtering to recover plausible sequences. |
| [Mixture-of-Expert Blocks Contain Strong Hallucination Detection Signals](2608.17687-mixture-of-expert-blocks-contain-strong.md) | 9 | Post-inference detection and repair of degenerate output | MoE-specific routing signals enable per-token hallucination detection in LLMs. |
| [MoNe: Modular Neural Memory for Efficient Long Context Inference](2608.17616-mone-modular-neural-memory-for-efficient.md) | 9 | LLM inference efficiency and long-context serving | Modular neural memory enables efficient long-context inference with O(1) query cost. |
| [Proteus: Incremental Memory Activation for Long-Context Sequence Modeling](2608.16844-proteus-incremental-memory-activation-fo.md) | 9 | LLM inference efficiency and long-context serving | Progressive memory-capacity expansion during sequence generation reducing interference and improving long-context retention. |
| [HalluTracer: Hallucination Detection via Depth-Averaging Truth Signals](2608.16353-hallutracer-hallucination-detection-via.md) | 9 | Post-inference detection and repair of degenerate output | Detects hallucinations by aggregating truthfulness signals across forward-pass layers for white-box hallucination detection. |
| [Beyond Binary Priorities: Multi-Tier SLA Scheduling for Large Language Model Serving](2608.16336-beyond-binary-priorities-multi-tier-sla.md) | 9 | LLM inference efficiency and long-context serving | Multi-tier SLA scheduler for LLM serving extending Llumnix to arbitrary priority levels with workload differentiation. |

---

_Run: 2026-08-24 07:36 UTC · 20 LLM calls · 31016 in / 153805 out tokens · reported cost $4.6493 (subscription usage — should be $0 on API billing)_
