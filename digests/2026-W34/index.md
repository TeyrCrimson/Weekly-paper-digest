# Weekly paper digest

| Title | Score | Topics | One-liner |
|---|---|---|---|
| [DeaMoE: Efficient MoE Structure for Fast Small-Batch Decoding](2608.14385-deamoe-efficient-moe-structure-for-fast.md) | 9 | LLM inference efficiency and long-context serving | Reduces expert weight loading bottleneck in MoE models through parameter sharing for fast small-batch decoding. |
| [KV Cache Compression Through the Lens of Transform Coding](2608.14191-kv-cache-compression-through-the-lens-of.md) | 9 | LLM inference efficiency and long-context serving | Applies transform coding and attention-aware distortion to achieve near-lossless KV cache compression. |
| [DARTree: Speculative Diffusion Decoding with Autoregressive Draft Trees](2608.13524-dartree-speculative-diffusion-decoding-w.md) | 9 | LLM inference efficiency and long-context serving | Accelerates LLM decoding via speculative diffusion drafting with autoregressive trees. |
| [TEMPO: Makespan-Aware Expert-Parallel Load Balancing Across Memory- and Compute-Bound Regimes](2608.13057-tempo-makespan-aware-expert-parallel-loa.md) | 9 | LLM inference efficiency and long-context serving | Makespan-aware dispatcher for expert-parallel MoE serving addressing compute and memory-bound regimes. |
| [Unifying Depth and Width Pruning for LLMs via Binary Knapsack Optimization](2608.12953-unifying-depth-and-width-pruning-for-llm.md) | 9 | LLM inference efficiency and long-context serving | Two-stage structured pruning framework achieving exact budget adherence for LLM compression. |
| [Decoupled Contrastive Decoding via Expert-Aligned Drafting](2608.12913-decoupled-contrastive-decoding-via-exper.md) | 9 | LLM inference efficiency and long-context serving | Expert-aligned speculative decoding for contrastive generation achieving 1.65-1.95x speedup. |
| [The Parser Already Knows: Lightweight Bias Correction in Constrained Decoding](2608.10137-the-parser-already-knows-lightweight-bia.md) | 9 | Pre-inference input sanitization for generation stability | Develops lightweight offline-trained logit correction for grammar-constrained decoding using parser state. |
| [Mismatch Matters: On-Policy Distillation Beyond Token Agreement](2608.09836-mismatch-matters-on-policy-distillation.md) | 9 | Post-inference detection and repair of degenerate output | Identifies and fixes degenerate agreement in on-policy distillation where students exploit repetitive loops to match teachers. |
| [FreeBalance: Pre-Routing Online Moe Load Balancing via Residual Workload Prediction](2608.14205-freebalance-pre-routing-online-moe-load.md) | 8 | LLM inference efficiency and long-context serving | Overlaps expert migration with preceding computation through residual workload prediction for MoE balancing. |
| [The Query Knows What to Forget: A Second Erase Direction for Linear Attention](2608.13668-the-query-knows-what-to-forget-a-second.md) | 8 | LLM inference efficiency and long-context serving | Improves linear attention for long context by adding query-derived erase directions. |
| [Reduced Matrix Multiplication: Input-Adaptive Matrix-Product Reduction for LLM Inference](2608.13426-reduced-matrix-multiplication-input-adap.md) | 8 | LLM inference efficiency and long-context serving | Reduces Transformer inference cost via input-adaptive matrix-product pruning. |
| [Self-Referential Induction Increases Response Instability Relative to Unresolvable and Verifiable Questions in Large Language Models](2608.13258-self-referential-induction-increases-res.md) | 8 | Post-inference detection and repair of degenerate output | Measures output instability in self-referential LLM prompts compared to philosophical and verifiable questions. |

---

_Run: 2026-08-17 07:35 UTC · 22 LLM calls · 31036 in / 161846 out tokens · reported cost $5.1148 (subscription usage — should be $0 on API billing)_
