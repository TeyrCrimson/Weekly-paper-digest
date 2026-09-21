# Weekly paper digest

| Title | Score | Topics | One-liner |
|---|---|---|---|
| [On-Demand Attention: Language Models Know When to Recall](2609.20734-on-demand-attention-language-models-know.md) | 10 | LLM inference efficiency and long-context serving | Selective KV cache access using learned recall heads for efficient long-context inference. |
| [DeepSeek-V4.1-Flash: Pushing the Limits of KV Cache Compression](2609.19969-deepseek-v4-1-flash-pushing-the-limits-o.md) | 10 | LLM inference efficiency and long-context serving | Multimodal MoE model with extreme KV-cache compression via FP4 quantization and cross-layer reuse. |
| [LoopSpec: Pipelined Self-Speculative Decoding for Looped Transformers](2609.17184-loopspec-pipelined-self-speculative-deco.md) | 10 | LLM inference efficiency and long-context serving | Self-speculative decoding framework achieving 6.83× inference speedup for looped transformers. |
| [GrowMTP: Can RL Grow Its Own Draft Head?](2609.16648-growmtp-can-rl-grow-its-own-draft-head.md) | 10 | LLM inference efficiency and long-context serving | Online draft-head training within RL achieving 2.13× rollout speedup via speculative decoding. |
| [Watermarkable Multi-Draft Speculative Sampling via Poisson Processes](2609.21858-watermarkable-multi-draft-speculative-sa.md) | 9 | LLM inference efficiency and long-context serving | Develops multi-draft speculative sampling via Poisson processes maintaining both watermarking and sampling efficiency. |
| [RheoSampling: Resolving the One-Hot Dilemma in Stochastic Dynamic-Tree Speculative Decoding](2609.21827-rheosampling-resolving-the-one-hot-dilem.md) | 9 | LLM inference efficiency and long-context serving | Resolves stochastic sampling in dynamic-tree speculative decoding via probability decoupling and lossless equivalence classes. |
| [SpecQuant: Speculative Decoding with Multi-Parent Quantization for Adaptive LLM Inference](2609.21704-specquant-speculative-decoding-with-mult.md) | 9 | LLM inference efficiency and long-context serving | Combines speculative decoding with multi-parent quantization for adaptive efficient LLM inference. |
| [TierKV: Long-Context On-Device LLMs via Predictive Multi-Tier KV Caching](2609.21172-tierkv-long-context-on-device-llms-via-p.md) | 9 | LLM inference efficiency and long-context serving | Enables long-context inference on mobile devices through predictive multi-tier KV cache optimization. |
| [To Copy or Not to Copy: Controlling Speculative Decoding via Intrinsic Model Signals](2609.20186-to-copy-or-not-to-copy-controlling-specu.md) | 9 | LLM inference efficiency and long-context serving | Adaptive speculative decoding framework switching between neural drafting and copying based on model signals. |
| [D-Quant: Driftable Entropy Coding for KV Cache Quantization](2609.19880-d-quant-driftable-entropy-coding-for-kv.md) | 9 | LLM inference efficiency and long-context serving | Proposes D-Quant, an entropy-coding framework for KV cache quantization that uses drift mechanisms for efficient variable-length compression. |
| [PrefixBench-H100: Characterizing Prefix Reuse and Time-to-First-Token in H100 LLM Serving](2609.19657-prefixbench-h100-characterizing-prefix-r.md) | 9 | LLM inference efficiency and long-context serving | Presents PrefixBench-H100, a benchmark characterizing KV cache prefix reuse benefits and limitations on NVIDIA H100 for LLM serving. |
| [Elastic Threshold Attention: Learned Contextual Sparsity for Long-Context Decoding](2609.20888-elastic-threshold-attention-learned-cont.md) | 9 | LLM inference efficiency and long-context serving | Proposes Elastic Threshold Attention for learned contextual sparsity enabling 2.5× decode speedup on long sequences. |

---

_Run: 2026-09-21 13:00 UTC · 22 LLM calls · 31036 in / 169142 out tokens · reported cost $5.3697 (subscription usage — should be $0 on API billing)_
