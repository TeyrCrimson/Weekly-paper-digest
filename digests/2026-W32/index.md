# Weekly paper digest

| Title | Score | Topics | One-liner |
|---|---|---|---|
| [ResKV: Reconstructing Omitted Attention Contributions for Fixed-Budget KV Cache Compression](2607.29591-reskv-reconstructing-omitted-attention-c.md) | 9 | LLM inference efficiency and long-context serving | KV cache compression using residual statistics to reconstruct omitted token contributions without perturbing retained values. |
| [WIDE: Boosting Adaptive LLM Inference via Token-level Dynamic Width Pruning](2607.28418-wide-boosting-adaptive-llm-inference-via.md) | 9 | LLM inference efficiency and long-context serving | Enables token-level dynamic width pruning in LLM inference achieving up to 1.98x prefill and 4.95x decode speedups. |
| [S-CEReBrO: Breaking the Memory Barrier in Continuous EEG Monitoring](2607.27913-s-cerebro-breaking-the-memory-barrier-in.md) | 9 | LLM inference efficiency and long-context serving | Windowed alternating attention mechanism guaranteeing constant KV cache memory during continuous EEG monitoring. |
| [A Sparse Glimpse of the Whole: Train-Free Self-Speculative Decoding](2607.27735-a-sparse-glimpse-of-the-whole-train-free.md) | 9 | LLM inference efficiency and long-context serving | Accelerates sparse attention via cached query-support reuse for long-context decoding. |
| [Recall Before You Rank: Similarity-Guided Top-$K$ Reuse for Efficient Long-Context Attention](2607.27692-recall-before-you-rank-similarity-guided.md) | 9 | LLM inference efficiency and long-context serving | Accelerates Top-K attention by reusing historical retrieval decisions for long-context decoding. |
| [InferScale: GPU-Native KV Injection for Personalized LLM Serving](2607.27090-inferscale-gpu-native-kv-injection-for-p.md) | 9 | LLM inference efficiency and long-context serving | GPU-native KV injection system that precomputes memory facts' KV representations to reduce TTFT and serve personalized LLMs efficiently. |
| [Beyond KV Reconstruction: Functional Reconstruction for MLA Draft Models in Speculative Decoding](2607.27269-beyond-kv-reconstruction-functional-reco.md) | 9 | LLM inference efficiency and long-context serving | Improves speculative decoding with MLA by optimizing functional reconstruction instead of cache compression. |
| [From Tokens to Watt-hours: Analytical Energy Estimation for LLM Inference on Modern GPUs](2607.26571-from-tokens-to-watt-hours-analytical-ene.md) | 9 | LLM inference efficiency and long-context serving | Develops analytical methodology for estimating LLM inference energy on modern GPUs. |
| [LLMET: Enabling Cross-Layer Evaluation of Emerging M3D Memories for Energy-Efficient LLM Serving](2607.26491-llmet-enabling-cross-layer-evaluation-of.md) | 9 | LLM inference efficiency and long-context serving | Studies impact of emerging M3D cache technologies on energy efficiency of LLM serving. |
| [AngelSpec: Towards Real-World High Performance Inference with Speculative Decoding](2607.25852-angelspec-towards-real-world-high-perfor.md) | 9 | LLM inference efficiency and long-context serving | Proposes AngelSpec framework with co-specialized speculative decoders and adaptive verification for efficient LLM inference. |
| [CoSA: Accelerating Long-Context Inference via Proxy-Kernel Co-Designed Sparse Attention](2607.25291-cosa-accelerating-long-context-inference.md) | 9 | LLM inference efficiency and long-context serving | Proxy-kernel co-designed sparse attention achieving 4.93× speedup for 128K context length inference. |
| [LOCKS: Page-Local Compact Key Summaries for Efficient Long-Context Decoding](2607.24555-locks-page-local-compact-key-summaries-f.md) | 9 | LLM inference efficiency and long-context serving | Page-local spectral summaries for efficient long-context decoding with selective attention. |

---

_Run: 2026-08-03 10:26 UTC · 21 LLM calls · 30810 in / 157267 out tokens · reported cost $5.0769 (subscription usage — should be $0 on API billing)_
