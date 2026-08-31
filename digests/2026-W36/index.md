# Weekly paper digest

| Title | Score | Topics | One-liner |
|---|---|---|---|
| [FOCUS & RePAIR: Mitigating Text Degeneration via Token-Level Guidance for Pruned Large Language Models](2608.26676-focus-repair-mitigating-text-degeneratio.md) | 10 | Post-inference detection and repair of degenerate output | Token-level guidance methods (FOCUS & RePAIR) to mitigate repetition loops in pruned LLMs. |
| [Sliding-window beats linear attention](2608.28444-sliding-window-beats-linear-attention.md) | 9 | LLM inference efficiency and long-context serving | Sliding window attention with sinks outperforms post-trained linear attention for long-context LLMs. |
| [A Probabilistic Interpretation of KV Cache Eviction](2608.28293-a-probabilistic-interpretation-of-kv-cac.md) | 9 | LLM inference efficiency and long-context serving | Probabilistic framework for KV cache eviction with decode-time correction for efficient inference. |
| [H-Scale: Hessian-Guided Scale Refinement for NVFP4 Sub-Byte LLM Inference](2608.28113-h-scale-hessian-guided-scale-refinement.md) | 9 | LLM inference efficiency and long-context serving | H-Scale uses Hessian-guided refinement for NVFP4 sub-byte quantization of LLM inference. |
| [Beyond Parallel Blindness: Information Floors and Model Gaps in Block Drafting](2608.27339-beyond-parallel-blindness-information-fl.md) | 9 | LLM inference efficiency and long-context serving | Information floor analysis quantifies how much context is available for speculative decoding and identifies model capacity gaps. |
| [Prediction of Prediction (PoP): Inter-Layer Activation Fusion for Single-Pass Hallucination Detection in Large Language Models](2608.27165-prediction-of-prediction-pop-inter-layer.md) | 9 | Post-inference detection and repair of degenerate output | Detects factual errors in LLM outputs during decoding by analyzing inter-layer hidden-state transition dynamics. |
| [TwinKV: A Composable Repair Pass for KV Cache Eviction via Pairwise Key Redundancy](2608.27128-twinkv-a-composable-repair-pass-for-kv-c.md) | 9 | LLM inference efficiency and long-context serving | Improves KV cache efficiency by detecting token redundancy and selectively swapping evicted/retained tokens. |
| [ClusterAttention: A training-free speedup of bidirectional attention](2608.26965-clusterattention-a-training-free-speedup.md) | 9 | LLM inference efficiency and long-context serving | Accelerates attention layers via training-free adaptive clustering that runs at dense attention latency on GPUs. |
| [Trajectory-Level Speculative Decoding for Diffusion Language Models](2608.27514-trajectory-level-speculative-decoding-fo.md) | 9 | LLM inference efficiency and long-context serving | Enables parallel multi-token generation in diffusion models via trajectory-level speculative decoding. |
| [DAMP: Decay-Aware Mixed-Precision Recurrent-State Quantization](2608.27513-damp-decay-aware-mixed-precision-recurre.md) | 9 | LLM inference efficiency and long-context serving | Reduces memory and latency of recurrent-state quantization via decay-aware channel-wise precision allocation. |
| [Prefix Sliding for efficient test-time scaling](2608.26070-prefix-sliding-for-efficient-test-time-s.md) | 9 | LLM inference efficiency and long-context serving | Prefix Sliding discards intermediate tokens during reasoning while retaining instructions and recent context to cap memory for long-horizon scaling. |
| [AsymSpec: Context-Asymmetric Speculative Decoding for Agentic LLMs](2608.26004-asymspec-context-asymmetric-speculative.md) | 9 | LLM inference efficiency and long-context serving | Asymmetric speculative decoding uses full context in drafter and compressed context in verifier to achieve 1.3–1.7× throughput speedups. |

---

_Run: 2026-08-31 13:49 UTC · 22 LLM calls · 31036 in / 180975 out tokens · reported cost $5.2022 (subscription usage — should be $0 on API billing)_
