# 候选肽预测摘要

- 生成时间：2026-11-26T06:23:40+00:00
- 输入候选肽：204 条
- 预测方式：['IEDB MHC-I processing (proteasome + TAP + MHC)', 'NetMHCpan-4.1 EL (IEDB recommended epitope)']
- 证据分层：{"C": 204}

## 排名前 10 的候选肽

| rank | peptide | length | gene | allele | percentile | tier | score |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | FLFLRNFSL | 9 | DEMO_GENE_6 | HLA-A*02:01 | 0.03 | C | 0.847 |
| 2 | GLIEKNIEL | 9 | DEMO_GENE_4 | HLA-A*02:01 | 0.01 | C | 0.8051 |
| 3 | DLMGYIPLV | 9 | DEMO_GENE_2 | HLA-A*02:01 | 0.12 | C | 0.7355 |
| 4 | FVFLRNFSL | 9 | DEMO_GENE_5 | HLA-A*02:01 | 0.27 | C | 0.6709 |
| 5 | GPDLMGYIPLV | 11 | DEMO_GENE_2 | HLA-A*02:01 | 0.32 | C | 0.5509 |
| 6 | FTEDPGPFV | 9 | DEMO_GENE_5 | HLA-A*02:01 | 0.55 | C | 0.4797 |
| 7 | FTEDPGPFL | 9 | DEMO_GENE_6 | HLA-A*02:01 | 0.62 | C | 0.4625 |
| 8 | GPGLIEKNIEL | 11 | DEMO_GENE_4 | HLA-A*02:01 | 0.14 | C | 0.4608 |
| 9 | FTEDPGPATL | 10 | DEMO_GENE_3 | HLA-A*02:01 | 0.43 | C | 0.4361 |
| 10 | FTEDPGPKL | 9 | DEMO_GENE_1 | HLA-A*02:01 | 0.77 | C | 0.3783 |

## 局限性

- 候选肽来自上游提供的 frame-correct 参考/异常 CDS；平台不从剪接坐标重建 ORF。
- MHC 结合预测不等于抗原呈递、不等于免疫原性、不等于临床有效性。
- IEDB 输出的是 percentile rank（百分位排名），不是实测亲和力 Kd。
- novelty 只在所提供的正常蛋白序列范围内成立，缺失不代表肿瘤特异。
- MHC-II 预测使用含侧翼序列的窗口，模型报告的是 9-mer core 的排名。
- 缺少 HLA 免疫肽组质谱与实验验证时，不能声称肽被呈递或具有免疫原性。
- 复现率与表达量仅作为排序权重，未设为硬门槛。

> 本表用于候选排序，不能证明抗原呈递、免疫原性或临床有效性。
