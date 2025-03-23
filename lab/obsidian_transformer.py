"""
Obsidian Transformer

A script to convert PubMed search results from JSON format to 
beautifully formatted Obsidian markdown files.
"""

import json
import os
import re
import textwrap
from datetime import datetime
from pathlib import Path
import argparse


class ObsidianTransformer:
    """Transform PubMed JSON results into Obsidian markdown format."""
    
    def __init__(self, output_dir=None):
        """Initialize the transformer with output directory."""
        self.output_dir = output_dir or Path.home() / "Documents" / "Obsidian" / "PubMed"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def transform(self, json_path):
        """Transform a JSON file to Obsidian markdown format."""
        # Load JSON data
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        # Prepare filename
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        query_slug = re.sub(r'[^\w\s-]', '', data['query'].lower())
        query_slug = re.sub(r'[\s-]+', '-', query_slug)
        filename = f"pubmed-{query_slug}-{timestamp}.md"
        outpath = self.output_dir / filename
        
        # Generate markdown content
        markdown = self._generate_markdown(data)
        
        # Write to file
        with open(outpath, 'w') as f:
            f.write(markdown)
        
        print(f"Created Obsidian markdown file: {outpath}")
        return outpath
    
    def _generate_markdown(self, data):
        """Generate the full markdown content."""
        # YAML frontmatter
        frontmatter = self._generate_frontmatter(data)
        
        # Title and introduction
        title = f"# PubMed Search: {data['query']}\n\n"
        intro = f"> Search performed on {self._format_date(data['timestamp'])} · {data['num_results']} results found\n\n"
        
        # Table of contents
        toc = self._generate_toc(data['articles'])
        
        # Articles content
        articles_content = self._generate_articles_content(data['articles'])
        
        # Combine everything
        return frontmatter + title + intro + toc + articles_content
    
    def _generate_frontmatter(self, data):
        """Generate YAML frontmatter for Obsidian."""
        frontmatter = [
            "---",
            f"title: PubMed - {data['query']}",
            f"date: {self._format_date(data['timestamp'])}",
            f"query: {data['query']}",
            f"results_count: {data['num_results']}",
            "tags:",
            "  - pubmed",
            "  - research"
        ]
        
        # Add additional tags based on query keywords
        query_words = re.findall(r'\w+', data['query'].lower())
        for word in query_words:
            if len(word) > 3:  # Only add significant words as tags
                frontmatter.append(f"  - {word}")
        
        frontmatter.append("---\n")
        return "\n".join(frontmatter)
    
    def _generate_toc(self, articles):
        """Generate a table of contents with links to each article."""
        toc = ["## Table of Contents\n"]
        
        for i, article in enumerate(articles, 1):
            # Create an anchor from the title
            anchor = re.sub(r'[^\w\s-]', '', article['title'].lower())
            anchor = re.sub(r'[\s-]+', '-', anchor)
            
            # Add TOC entry
            journal_year = f"({article['journal']}, {article['publication_date'].split()[-1]})"
            toc.append(f"{i}. [[#{anchor}|{article['title']}]] {journal_year}")
        
        toc.append("\n---\n")
        return "\n".join(toc)
    
    def _generate_articles_content(self, articles):
        """Generate formatted content for all articles."""
        content = []
        
        for i, article in enumerate(articles, 1):
            # Create article header with anchor for internal linking
            article_anchor = re.sub(r'[^\w\s-]', '', article['title'].lower())
            article_anchor = re.sub(r'[\s-]+', '-', article_anchor)
            
            content.append(f"## {i}. {article['title']} {{{article_anchor}}}\n")
            
            # Authors section
            authors = [article['first_author']] + article.get('co_authors', [])
            content.append("### Authors\n")
            content.append(", ".join(authors))
            content.append("\n")
            
            # Publication info
            content.append("### Publication\n")
            content.append(f"**Journal:** {article['journal']}  ")
            content.append(f"**Date:** {article['publication_date']}  ")
            content.append(f"**PMID:** [{article['pmid']}](https://pubmed.ncbi.nlm.nih.gov/{article['pmid']}/)  ")
            
            if article.get('doi'):
                content.append(f"**DOI:** [{article['doi']}](https://doi.org/{article['doi']})  ")
            
            if article.get('pmc_id'):
                pmc_id = article['pmc_id'].replace('PMC', '') if article['pmc_id'].startswith('PMC') else article['pmc_id']
                content.append(f"**PMC ID:** [PMC{pmc_id}](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc_id}/)  ")
            
            content.append("\n")
            
            # MeSH terms and Keywords
            if article.get('mesh_terms') or article.get('keywords'):
                content.append("### Terms\n")
                
                if article.get('mesh_terms'):
                    mesh_tags = [f"#mesh/{term.lower().replace(' ', '_')}" for term in article['mesh_terms']]
                    content.append(f"**MeSH Terms:** {' '.join(mesh_tags)}")
                    content.append("\n")
                
                if article.get('keywords'):
                    keyword_tags = [f"#keyword/{keyword.lower().replace(' ', '_')}" for keyword in article['keywords']]
                    content.append(f"**Keywords:** {' '.join(keyword_tags)}")
                    content.append("\n")
                
                content.append("\n")
            
            # Abstract - use the new formatting function
            if article.get('abstract'):
                content.append("### Abstract\n")
                
                # Use callout block for abstract to make it stand out
                content.append("> [!abstract]")
                
                # Format abstract with new function
                formatted_abstract = self._format_abstract(article['abstract'])
                for line in formatted_abstract:
                    # Add ">" prefix for each line to maintain the callout block
                    content.append(f"> {line}")
                
                content.append("\n")
            
            # Research Insight
            if article.get('research_insight'):
                content.append("### Research Insight\n")
                content.append("> [!insight] AI-Generated Research Insight")
                for line in article['research_insight'].split('\n'):
                    if line.strip():
                        content.append(f"> {line}")
                content.append("\n")
            
            # Links
            if article.get('full_text_links'):
                content.append("### Links\n")
                for i, link in enumerate(article['full_text_links'], 1):
                    content.append(f"{i}. [Full Text Link {i}]({link})")
                content.append("\n")
            
            # Separator between articles with clearer visual distinction
            content.append("\n<div style='page-break-after: always'></div>\n\n---\n")
        
        return "\n".join(content)
    
    def _format_abstract(self, abstract_text):
        """
        Format an abstract with beautiful formatting for better readability.
        
        Args:
            abstract_text: The raw abstract text
            
        Returns:
            List of formatted abstract lines
        """
        if not abstract_text or abstract_text == "Not available":
            return ["*No abstract available for this article.*"]
        
        # Common section headers in scientific abstracts
        section_headers = [
            "BACKGROUND:", "INTRODUCTION:", "OBJECTIVE:", "OBJECTIVES:", 
            "PURPOSE:", "AIM:", "AIMS:", "METHODS:", "METHODOLOGY:",
            "DESIGN:", "RESULTS:", "FINDINGS:", "CONCLUSION:", "CONCLUSIONS:",
            "DISCUSSION:", "SIGNIFICANCE:", "IMPLICATIONS:", "SUMMARY:"
        ]
        
        # Check if this is a structured abstract (has explicit section headers)
        is_structured = any(header in abstract_text for header in section_headers)
        
        formatted_lines = []
        
        if is_structured:
            # Handle structured abstract with clear sections
            # First clean up the text a bit
            abstract_text = re.sub(r'\s+', ' ', abstract_text).strip()
            
            # Split on section headers
            parts = []
            last_pos = 0
            
            # Find all section headers and their positions
            header_positions = []
            for header in section_headers:
                for match in re.finditer(r'\b' + re.escape(header), abstract_text):
                    header_positions.append((match.start(), header))
            
            # Sort by position
            header_positions.sort()
            
            # Split the text at header positions
            for pos, header in header_positions:
                if pos > last_pos:
                    parts.append(abstract_text[last_pos:pos])
                parts.append(header)
                last_pos = pos + len(header)
            
            # Add the final part
            if last_pos < len(abstract_text):
                parts.append(abstract_text[last_pos:])
            
            # Format each section
            current_section = None
            section_text = []
            
            for part in parts:
                if part in section_headers:
                    # Start a new section
                    if current_section and section_text:
                        # Format and add the previous section
                        formatted_lines.append(f"**{current_section}**")
                        formatted_lines.append("".join(section_text).strip())
                        formatted_lines.append("")  # Empty line for spacing
                    
                    current_section = part.strip(":")
                    section_text = []
                else:
                    section_text.append(part)
            
            # Add the last section
            if current_section and section_text:
                formatted_lines.append(f"**{current_section}**")
                formatted_lines.append("".join(section_text).strip())
        else:
            # Handle unstructured abstract
            # Break into sentences and then group into logical paragraphs
            sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z0-9])', abstract_text)
            
            current_paragraph = []
            current_length = 0
            max_paragraph_length = 600  # Characters per paragraph
            
            for sentence in sentences:
                if current_length + len(sentence) > max_paragraph_length and current_paragraph:
                    # Start a new paragraph if this one is getting too long
                    formatted_lines.append(" ".join(current_paragraph))
                    formatted_lines.append("")  # Empty line for spacing
                    current_paragraph = []
                    current_length = 0
                
                current_paragraph.append(sentence)
                current_length += len(sentence)
            
            # Add the final paragraph
            if current_paragraph:
                formatted_lines.append(" ".join(current_paragraph))
        
        # Remove any consecutive empty lines
        result = []
        for i, line in enumerate(formatted_lines):
            if not (i > 0 and line == "" and formatted_lines[i-1] == ""):
                result.append(line)
        
        return result

    def _format_date(self, timestamp):
        """Format timestamp into a readable date."""
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return dt.strftime("%Y-%m-%d")
        except (ValueError, AttributeError):
            return timestamp


def main():
    parser = argparse.ArgumentParser(description="Convert PubMed JSON results to Obsidian markdown format")
    parser.add_argument("json_file", help="Path to PubMed results JSON file")
    parser.add_argument("--output-dir", "-o", help="Output directory for markdown files")
    
    args = parser.parse_args()
    
    transformer = ObsidianTransformer(output_dir=args.output_dir)
    transformer.transform(args.json_file)


if __name__ == "__main__":
    main()