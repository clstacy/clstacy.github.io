---
title: "Introducing *Paralogs*: A New Dimension in Gene Expression Analysis"
excerpt: "An R Package for Visualizing Differential Paralog Expression in KEGG Gene Pathways 1<br/><img src='/images/paralogs_head_pic.png'>"
collection: portfolio
---


Thank you for scanning the QR code from my poster, or if you've found your way here through other means, welcome! I'm excited to share more about *paralogs*, an innovative R package I've developed that enhances the analysis of gene expression data by visualizing on paralog-specific responses in KEGG pathways. The original poster is accessible [here](https://github.com/clstacy/clstacy.github.io/blob/master/files/Stacy_Paralogs_Poster_2024.pdf) If you're interested in the technical details or want to try it out yourself, please visit the [GitHub repository](https://github.com/clstacy/Paralogs).

## Why Paralogs?

Traditional KEGG visualization often averages or takes the largest effect in the data from paralogous genes, which can mask the distinct roles these genes play in biological processes. *Paralogs* addresses this gap by providing tools to visualize differential expression of paralogs within their native KEGG pathways, allowing for a more nuanced understanding of gene function.

## Key Features of Paralogs

- **Gene-Level Precision**: "Paralogs" allows researchers to observe the expression of individual genes within paralog groups, providing insights that are lost when expression is averaged.
- **Integration with Established Tools**: The package integrates smoothly with popular R libraries like DESeq2, edgeR, and clusterProfiler, making it a versatile addition to any genomic researcher's toolkit.
- **Customizable Visualizations**: Tailor your analysis with our grammar of graphics (ggplot2) based approach, ensuring that you can highlight the specific data that matter most to your research.

## A Practical Example

Using *Paralogs* in a study on *Saccharomyces cerevisiae*, we could identify unique gene expression patterns under different stress conditions. This application demonstrated how our package can uncover crucial insights into metabolic pathways, such as glycolysis and the Krebs cycle, which are often overlooked by existing methods.

## Your Feedback and Contributions

I am continually striving to improve "Paralogs" and eagerly welcome feedback and contributions from the community. Whether you're a fellow researcher, a potential collaborator, or an employer, I value your insights and invite you to join me in enhancing this tool.

## Conclusion

"Paralogs" is more than just an R package—it's a new way of looking at genomic data. By providing detailed, paralog-specific expression analysis, it opens up new possibilities for understanding gene function and regulation. I'm thrilled to see how it will advance our knowledge in the field of genomics.

For further details, visit the [GitHub repository](https://github.com/clstacy/Paralogs) or reach out directly via [LinkedIn](https://www.linkedin.com/in/carson-stacy).

Thank you for your interest, and I look forward to your feedback and questions!

